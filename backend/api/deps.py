from dataclasses import dataclass
from hashlib import sha256
from fastapi import Header, HTTPException, Request, status
from asgiref.sync import sync_to_async
from django.utils import timezone
from platform_core.models import ApiSession

@dataclass
class CurrentUser:
    user: object
    profile: object | None

async def current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token=authorization.split(" ",1)[1].strip()
    token_hash=sha256(token.encode("utf-8")).hexdigest()
    def lookup():
        s=(ApiSession.objects.select_related("user","user__platform_profile")
           .filter(token_hash=token_hash,revoked_at__isnull=True,expires_at__gt=timezone.now()).first())
        if not s or not s.user.is_active: return None
        return CurrentUser(s.user,getattr(s.user,"platform_profile",None))
    found=await sync_to_async(lookup,thread_sensitive=True)()
    if not found: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Session expired or invalid")
    return found

def require_roles(*roles):
    async def dep(cu: CurrentUser = None):
        # FastAPI won't inject nested default like this, wrapper defined in routers instead.
        return cu
    return dep

def client_ip(request: Request):
    forwarded=request.headers.get("x-forwarded-for","").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else None)
