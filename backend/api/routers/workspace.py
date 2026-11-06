from fastapi import APIRouter, Depends, HTTPException, Query
from asgiref.sync import sync_to_async
from django.db.models import Q
from platform_core.models import PlatformRecord, WorkspaceState
from platform_core.services import save_workspace_state
from platform_core.cache import (
    get_or_set_cache,
    get_namespace_version,
    record_namespace,
)
from platform_core.pagination import paginate_sequence
from api.deps import CurrentUser, current_user
from api.schemas import WorkspaceStateIn, WorkspaceStateOut, RecordPage

router = APIRouter(prefix="/workspace", tags=["workspace"])

@router.get("/state")
async def get_state(cu: CurrentUser = Depends(current_user)):
    """
    Get the synchronized global workspace state.
    Cached for fast repeated loads; invalidated on any workspace sync or mutation.
    """
    def query():
        ws = WorkspaceState.objects.filter(pk="t4f-global").first()
        return {"revision": ws.revision if ws else 0, "state": ws.state if ws else {}}

    def get_data():
        return get_or_set_cache("workspace:state:t4f-global", query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()

@router.put("/state")
async def put_state(body: WorkspaceStateIn, cu: CurrentUser = Depends(current_user)):
    """
    Atomically synchronize the workspace state, update database records, and invalidate caches.
    """
    ws = await sync_to_async(save_workspace_state, thread_sensitive=True)(body.state, cu.user)
    return {"ok": True, "revision": ws.revision}

@router.get("/records/{record_type}", response_model=RecordPage)
async def records(
    record_type: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    org_id: str = "",
    cu: CurrentUser = Depends(current_user),
):
    """
    Fetch paginated records for a specific record type with role scoping and caching.
    """
    effective_org = org_id
    p = cu.profile
    global_roles = {"platform_super_admin", "high_super_admin"}
    if p and p.system_role not in global_roles and p.organization_id:
        effective_org = p.organization_id

    def get_data():
        version = get_namespace_version(record_namespace("t4f-global", record_type))
        cache_key = f"workspace_records:v{version}:t4f-global:{record_type}:{effective_org}:{limit}:{offset}"

        def query():
            qs = PlatformRecord.objects.filter(workspace_key="t4f-global", record_type=record_type).order_by("-updated_at")
            if p and p.system_role not in global_roles and p.organization_id:
                qs = qs.filter(Q(organization_id=p.organization_id) | Q(organization_id=""))
            elif org_id:
                qs = qs.filter(organization_id=org_id)
            total = qs.count()
            rows = list(qs[offset : offset + limit].values_list("data", flat=True))
            return paginate_sequence(rows, total=total, limit=limit, offset=offset)

        return get_or_set_cache(cache_key, query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()
