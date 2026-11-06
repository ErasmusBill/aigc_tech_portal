from fastapi import APIRouter, Depends
from asgiref.sync import sync_to_async
from django.db import connection
from platform_core.models import Organization, PlatformRecord, WorkspaceState
from platform_core.cache import get_or_set_cache
from api.deps import CurrentUser, current_user

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
async def health():
    def check():
        with connection.cursor() as c:
            c.execute("SELECT 1")
            c.fetchone()
        return {"ok": True, "database": True, "backend": "django+fastapi", "version": "13.0"}

    return await sync_to_async(check, thread_sensitive=True)()

@router.get("/stats")
async def stats(cu: CurrentUser = Depends(current_user)):
    def get():
        def compute_stats():
            return {
                "organizations": Organization.objects.count(),
                "records": PlatformRecord.objects.count(),
                "workspace_revision": WorkspaceState.objects.filter(pk="t4f-global").values_list("revision", flat=True).first() or 0,
            }
        return get_or_set_cache("system:stats", compute_stats, timeout=60)

    return await sync_to_async(get, thread_sensitive=True)()
