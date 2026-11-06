from fastapi import APIRouter, Depends, HTTPException, Query
from asgiref.sync import sync_to_async
from platform_core.models import PlatformRecord
from platform_core.services import save_platform_record, delete_platform_record
from platform_core.cache import (
    get_or_set_cache,
    get_namespace_version,
    record_namespace,
)
from platform_core.pagination import paginate_sequence
from api.deps import CurrentUser, current_user
from api.schemas import RecordIn, RecordPage

router = APIRouter(prefix="/records", tags=["records"])

def can_write(cu: CurrentUser, org_id: str) -> bool:
    p = cu.profile
    if not p:
        return False
    if p.system_role in {"platform_super_admin", "high_super_admin"}:
        return True
    return not org_id or org_id == p.organization_id

@router.get("/{record_type}", response_model=RecordPage)
async def list_records(
    record_type: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    cu: CurrentUser = Depends(current_user),
):
    """
    List records with pagination, caching, and role/org scoping.
    Cached queries automatically invalidate upon create/update/delete.
    """
    org_id = ""
    if cu.profile and cu.profile.system_role not in {"platform_super_admin", "high_super_admin"} and cu.profile.organization_id:
        org_id = cu.profile.organization_id

    def get_data():
        version = get_namespace_version(record_namespace("t4f-global", record_type))
        cache_key = f"records:v{version}:t4f-global:{record_type}:{org_id}:{limit}:{offset}"

        def query():
            qs = PlatformRecord.objects.filter(workspace_key="t4f-global", record_type=record_type).order_by("-updated_at")
            if org_id:
                qs = qs.filter(organization_id__in=["", org_id])
            total = qs.count()
            items = list(qs[offset : offset + limit].values_list("data", flat=True))
            return paginate_sequence(items, total=total, limit=limit, offset=offset)

        return get_or_set_cache(cache_key, query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()

@router.put("/{record_type}/{record_id}")
async def put_record(
    record_type: str,
    record_id: str,
    body: RecordIn,
    cu: CurrentUser = Depends(current_user),
):
    """
    Atomically create or update a record with transaction safety and cache invalidation.
    """
    org_id = body.orgId or body.data.get("orgId", "")
    if not can_write(cu, org_id):
        raise HTTPException(status_code=403, detail="Organization scope denied")

    def save():
        return save_platform_record(
            workspace_key="t4f-global",
            record_type=record_type,
            record_id=record_id,
            org_id=org_id,
            country=body.country,
            user_ref=body.userId,
            status=body.status,
            data=body.data,
            actor=cu.user,
        )

    return await sync_to_async(save, thread_sensitive=True)()

@router.delete("/{record_type}/{record_id}")
async def delete_record(
    record_type: str,
    record_id: str,
    cu: CurrentUser = Depends(current_user),
):
    """
    Atomically delete a record with transaction safety and cache invalidation.
    """
    def remove():
        obj = PlatformRecord.objects.filter(workspace_key="t4f-global", record_type=record_type, record_id=record_id).first()
        if not obj:
            return False
        if not can_write(cu, obj.organization_id):
            raise PermissionError
        return delete_platform_record(
            workspace_key="t4f-global",
            record_type=record_type,
            record_id=record_id,
            actor=cu.user,
        )

    try:
        ok = await sync_to_async(remove, thread_sensitive=True)()
    except PermissionError:
        raise HTTPException(status_code=403, detail="Organization scope denied")

    return {"ok": ok}
