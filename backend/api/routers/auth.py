from hashlib import sha256
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from platform_core.models import ApiSession, PlatformProfile
from platform_core.services import issue_api_session, user_payload, change_user_password
from api.deps import CurrentUser, client_ip, current_user
from api.schemas import LoginRequest, LoginResponse, PasswordChangeRequest

router=APIRouter(prefix="/auth",tags=["auth"])

@router.post("/login",response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    identifier = str(body.email).strip().lower()

    def find_and_auth():
        from django.contrib.auth.models import User
        # Try direct username authentication
        u = authenticate(username=identifier, password=body.password)
        if not u:
            # Try matching by email
            matched = User.objects.filter(email__iexact=identifier).first()
            if matched:
                u = authenticate(username=matched.username, password=body.password)
        return u

    user = await sync_to_async(find_and_auth, thread_sensitive=True)()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid organization, email, or password")

    def verify_org():
        import uuid
        from platform_core.models import Organization, PlatformProfile
        p = getattr(user, "platform_profile", None)
        if not p:
            hq = Organization.objects.filter(pk="t4f-hq").first()
            p = PlatformProfile.objects.create(
                user=user,
                platform_user_id=str(uuid.uuid4()),
                organization=hq,
                system_role="platform_super_admin" if user.is_superuser else "standard_user",
                status="Active",
                must_reset=False,
            )
        if p.status == "Inactive":
            return False
        # Platform superusers can log into t4f-hq or their assigned org
        if user.is_superuser and (not p.organization_id or body.organization_id == "t4f-hq" or p.organization_id == body.organization_id):
            if not p.organization_id:
                hq = Organization.objects.filter(pk="t4f-hq").first()
                p.organization = hq
                p.save(update_fields=["organization", "updated_at"])
            return True
        return p.organization_id == body.organization_id

    if not await sync_to_async(verify_org, thread_sensitive=True)():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid organization, email, or password")

    token=await sync_to_async(issue_api_session,thread_sensitive=True)(user,request.headers.get("user-agent",""),client_ip(request))
    def touch():
        p=user.platform_profile; p.last_seen_at=timezone.now(); p.save(update_fields=["last_seen_at","updated_at"]); return user_payload(user)
    payload=await sync_to_async(touch,thread_sensitive=True)()
    return LoginResponse(token=token,user=payload)

@router.get("/me")
async def me(cu: CurrentUser = Depends(current_user)):
    return await sync_to_async(user_payload,thread_sensitive=True)(cu.user)


@router.post("/change-password")
async def change_password(body: PasswordChangeRequest, cu: CurrentUser = Depends(current_user)):
    try:
        return await sync_to_async(change_user_password, thread_sensitive=True)(
            user=cu.user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout(authorization: str | None = Header(default=None), cu: CurrentUser = Depends(current_user)):
    if authorization and authorization.lower().startswith("bearer "):
        token=authorization.split(" ",1)[1].strip()
        token_hash=sha256(token.encode("utf-8")).hexdigest()
        await sync_to_async(ApiSession.objects.filter(token_hash=token_hash).update,thread_sensitive=True)(revoked_at=timezone.now())
    return {"ok":True}
