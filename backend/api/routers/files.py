import hashlib
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from asgiref.sync import sync_to_async
from platform_core.models import FileObject
from platform_core.services import save_uploaded_file
from platform_core.cache import (
    get_or_set_cache,
    get_namespace_version,
    files_namespace,
)
from platform_core.pagination import paginate_sequence
from api.deps import CurrentUser, current_user
from api.schemas import FileItem, FilePage

router = APIRouter(prefix="/files", tags=["files"])
MAX_FILE_BYTES = 100 * 1024 * 1024

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("general"),
    organization_id: str = Form(""),
    classification: str = Form("Internal"),
    cu: CurrentUser = Depends(current_user),
):
    """
    Atomically upload and store a file with SHA256 checksum and cache invalidation.
    """
    if (
        cu.profile
        and cu.profile.system_role not in {"platform_super_admin", "high_super_admin"}
        and organization_id
        and organization_id != cu.profile.organization_id
    ):
        raise HTTPException(status_code=403, detail="Organization scope denied")

    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 100 MB limit")

    target_org = organization_id or (cu.profile.organization_id if cu.profile else "")

    def save():
        return save_uploaded_file(
            owner=cu.user,
            organization_id=target_org,
            category=category,
            filename=file.filename or "upload",
            mime_type=file.content_type or "",
            content=content,
            classification=classification,
        )

    obj = await sync_to_async(save, thread_sensitive=True)()
    return {
        "id": str(obj.id),
        "name": obj.original_name,
        "size": obj.size_bytes,
        "sha256": obj.sha256,
        "download_url": f"/api/v1/files/{obj.id}",
    }

@router.get("", response_model=FilePage)
async def list_files(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str = "",
    cu: CurrentUser = Depends(current_user),
):
    """
    List uploaded files with pagination, org scoping, and caching.
    """
    org_id = ""
    if cu.profile and cu.profile.system_role not in {"platform_super_admin", "high_super_admin"}:
        org_id = cu.profile.organization_id or ""

    def get_data():
        version = get_namespace_version(files_namespace(org_id))
        cache_key = f"files:v{version}:{org_id}:{category}:{limit}:{offset}"

        def query():
            qs = FileObject.objects.all().order_by("-created_at")
            if org_id:
                qs = qs.filter(organization_id=org_id)
            if category:
                qs = qs.filter(category=category)
            total = qs.count()
            rows = [
                FileItem(
                    id=str(f.id),
                    owner_id=f.owner_id,
                    organization_id=f.organization_id,
                    category=f.category,
                    original_name=f.original_name,
                    mime_type=f.mime_type,
                    size_bytes=f.size_bytes,
                    sha256=f.sha256,
                    classification=f.classification,
                    download_url=f"/api/v1/files/{f.id}",
                    created_at=f.created_at.isoformat(),
                )
                for f in qs[offset : offset + limit]
            ]
            return paginate_sequence(rows, total=total, limit=limit, offset=offset)

        return get_or_set_cache(cache_key, query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()

@router.get("/{file_id}")
async def download_file(file_id: str, cu: CurrentUser = Depends(current_user)):
    def get():
        return FileObject.objects.filter(pk=file_id).first()

    obj = await sync_to_async(get, thread_sensitive=True)()
    if not obj:
        raise HTTPException(status_code=404, detail="File not found")
    if (
        cu.profile
        and cu.profile.system_role not in {"platform_super_admin", "high_super_admin"}
        and obj.organization_id
        and obj.organization_id != cu.profile.organization_id
    ):
        raise HTTPException(status_code=403, detail="Organization scope denied")
    return FileResponse(
        obj.stored_file.path,
        filename=obj.original_name,
        media_type=obj.mime_type or "application/octet-stream",
    )
