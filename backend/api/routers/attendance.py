from fastapi import APIRouter, Depends, Query
from asgiref.sync import sync_to_async
from platform_core.models import PlatformRecord
from platform_core.services import create_attendance_event_record
from platform_core.cache import (
    get_or_set_cache,
    get_namespace_version,
    attendance_namespace,
)
from platform_core.pagination import paginate_sequence
from api.deps import CurrentUser, current_user
from api.schemas import AttendanceAction, AttendancePage

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/event")
async def event(body: AttendanceAction, cu: CurrentUser = Depends(current_user)):
    """
    Record an attendance check-in/out event atomically with audit trail and cache invalidation.
    """
    def record():
        return create_attendance_event_record(
            user=cu.user,
            profile=cu.profile,
            event_type=body.event_type,
            occurred_at=body.occurred_at,
            latitude=body.latitude,
            longitude=body.longitude,
            accuracy_m=body.accuracy_m,
            metadata=body.metadata,
        )

    data = await sync_to_async(record, thread_sensitive=True)()
    return {"ok": True, "event": data}

@router.get("/events", response_model=AttendancePage)
async def list_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: str = "",
    cu: CurrentUser = Depends(current_user),
):
    """
    List paginated attendance events with role scoping and caching.
    """
    org_id = ""
    is_admin = cu.profile and cu.profile.system_role in {"platform_super_admin", "high_super_admin"}
    if cu.profile and not is_admin:
        org_id = cu.profile.organization_id or ""

    def get_data():
        version = get_namespace_version(attendance_namespace())
        cache_key = f"attendance:v{version}:{org_id}:{user_id}:{limit}:{offset}"

        def query():
            qs = PlatformRecord.objects.filter(
                workspace_key="t4f-global",
                record_type="attendanceEvents",
            ).order_by("-updated_at")
            if org_id:
                qs = qs.filter(organization_id=org_id)
            if user_id:
                qs = qs.filter(user_ref=user_id)
            elif not is_admin:
                # Standard users only see their own attendance events unless country admin
                is_org_admin = cu.profile and cu.profile.system_role in {"country_super_admin", "country_it_admin"}
                if not is_org_admin:
                    my_user_id = cu.profile.platform_user_id if cu.profile else str(cu.user.pk)
                    qs = qs.filter(user_ref=my_user_id)

            total = qs.count()
            rows = list(qs[offset : offset + limit].values_list("data", flat=True))
            return paginate_sequence(rows, total=total, limit=limit, offset=offset)

        return get_or_set_cache(cache_key, query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()
