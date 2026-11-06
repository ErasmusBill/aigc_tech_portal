from fastapi import APIRouter, Depends, HTTPException, Query, status
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.mail import send_mail
from platform_core.services import user_payload, provision_invited_user
from platform_core.cache import (
    get_or_set_cache,
    get_namespace_version,
    user_namespace,
)
from platform_core.pagination import paginate_sequence
from api.deps import CurrentUser, current_user
from api.schemas import InviteRequest, UserPage

router = APIRouter(prefix="/users", tags=["users"])

def can_provision(profile, org_id: str) -> bool:
    if not profile:
        return False
    if profile.system_role in {"platform_super_admin", "high_super_admin"}:
        return True
    return profile.organization_id == org_id and (
        profile.system_role in {"country_super_admin", "country_it_admin"}
        or profile.position_id in {
            "country-it-support-specialist",
            "country-technology-infrastructure-manager",
        }
    )

@router.get("", response_model=UserPage)
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    cu: CurrentUser = Depends(current_user),
):
    """
    List platform users with pagination and organization scoping.
    Cached queries automatically invalidate when users are invited or modified.
    """
    org_id = ""
    if cu.profile and cu.profile.system_role not in {"platform_super_admin", "high_super_admin"}:
        org_id = cu.profile.organization_id or ""

    def get_data():
        version = get_namespace_version(user_namespace(org_id))
        cache_key = f"users:v{version}:{org_id}:{limit}:{offset}"

        def query():
            qs = User.objects.select_related("platform_profile", "platform_profile__organization", "platform_profile__position").order_by("id")
            if org_id:
                qs = qs.filter(platform_profile__organization_id=org_id)
            total = qs.count()
            users = [user_payload(u) for u in qs[offset : offset + limit]]
            return paginate_sequence(users, total=total, limit=limit, offset=offset)

        return get_or_set_cache(cache_key, query, timeout=300)

    return await sync_to_async(get_data, thread_sensitive=True)()

@router.post("/invite")
async def invite(body: InviteRequest, cu: CurrentUser = Depends(current_user)):
    """
    Atomically provision an invited user, issue credentials, and invalidate user cache.
    """
    if not can_provision(cu.profile, body.organization_id):
        raise HTTPException(status_code=403, detail="Insufficient account provisioning rights")

    def perform_invite():
        user_dict, temp = provision_invited_user(
            invited_by=cu.user,
            organization_id=body.organization_id,
            name=body.name,
            email=str(body.email),
            position_id=body.position_id,
            system_role=body.system_role,
        )
        send_mail(
            "Tech4Future-Global Management Platform Invitation",
            f"Hello {body.name},\n\nYour account is ready.\nUsername: {body.email}\nTemporary password: {temp}\n\nPlease change the password at first sign-in.",
            None,
            [str(body.email)],
            fail_silently=True,
        )
        return {"user": user_dict, "temporary_password": temp}

    try:
        return await sync_to_async(perform_invite, thread_sensitive=True)()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
