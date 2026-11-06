import hashlib, secrets
from datetime import datetime, timedelta
from typing import Any, Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from .models import (
    ApiSession,
    AuditEvent,
    FileObject,
    Invitation,
    Organization,
    PlatformProfile,
    PlatformRecord,
    Position,
    WorkspaceState,
)
from .cache import (
    invalidate_workspace,
    invalidate_records,
    invalidate_users,
    invalidate_attendance,
    invalidate_files,
    invalidate_system_stats,
)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def user_payload(user: User) -> dict:
    profile = getattr(user, "platform_profile", None)
    return {
        "id": profile.platform_user_id if profile else str(user.pk),
        "orgId": (profile.organization_id or "") if profile else "",
        "name": user.get_full_name() or user.username,
        "email": user.email or user.username,
        "systemRole": (profile.system_role or "standard_user") if profile else "standard_user",
        "positionId": (profile.position_id or "") if profile else "",
        "status": profile.status if profile else ("Active" if user.is_active else "Inactive"),
        "mustReset": profile.must_reset if profile else False,
        "profile": profile.profile_data if profile else {},
    }

@transaction.atomic
def issue_api_session(user: User, user_agent="", ip_address=None) -> str:
    raw = secrets.token_urlsafe(48)
    ApiSession.objects.create(
        user=user,
        token_hash=hash_token(raw),
        expires_at=timezone.now() + timedelta(hours=12),
        user_agent=user_agent[:2000],
        ip_address=ip_address,
    )
    return raw

def sanitize_state(state: dict) -> dict:
    state = dict(state or {})
    users = []
    for item in state.get("users", []) if isinstance(state.get("users", []), list) else []:
        x = dict(item)
        x.pop("password", None)
        x.pop("passwordHash", None)
        users.append(x)
    state["users"] = users
    reqs = []
    for item in state.get("requests", []) if isinstance(state.get("requests", []), list) else []:
        x = dict(item)
        x.pop("pin", None)
        reqs.append(x)
    state["requests"] = reqs
    return state

@transaction.atomic
def sync_identity_from_state(raw_state: dict):
    for o in raw_state.get("organizations", []) if isinstance(raw_state.get("organizations", []), list) else []:
        Organization.objects.update_or_create(
            id=str(o.get("id", ""))[:120],
            defaults={
                "name": o.get("name") or o.get("id") or "Organization",
                "organization_type": o.get("type") or "organization",
                "country": o.get("country") or "",
                "parent_id": o.get("parentId") or "",
                "status": o.get("status") or "Active",
                "contact": o.get("contact") or {},
                "metadata": o,
            },
        )
    for u in raw_state.get("users", []) if isinstance(raw_state.get("users", []), list) else []:
        email = (u.get("email") or "").strip().lower()
        if not email:
            continue
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.is_active = u.get("status") != "Inactive"
        parts = (u.get("name") or "").strip().split(" ", 1)
        user.first_name = parts[0] if parts else ""
        user.last_name = parts[1] if len(parts) > 1 else ""
        if u.get("password"):
            user.set_password(u["password"])
        user.save()
        org = Organization.objects.filter(pk=u.get("orgId")).first()
        pos = Position.objects.filter(pk=u.get("positionId")).first() if u.get("positionId") else None
        PlatformProfile.objects.update_or_create(
            user=user,
            defaults={
                "platform_user_id": u.get("id") or f"user-{user.pk}",
                "organization": org,
                "position": pos,
                "system_role": u.get("systemRole") or "standard_user",
                "status": u.get("status") or "Active",
                "must_reset": bool(u.get("mustReset", False)),
                "profile_data": u.get("profile") or {},
            },
        )

@transaction.atomic
def save_workspace_state(state: dict, user: User) -> WorkspaceState:
    """Atomically synchronizes the entire workspace state, updates models, and invalidates cache."""
    sync_identity_from_state(state)
    safe = sanitize_state(state)
    ws, _ = WorkspaceState.objects.select_for_update().get_or_create(
        key="t4f-global",
        defaults={"state": safe, "revision": 1, "last_saved_by": user},
    )
    if ws.pk and ws.state != safe:
        ws.state = safe
        ws.revision = (ws.revision or 0) + 1
        ws.last_saved_by = user
        ws.save()

    arrays = {k: v for k, v in safe.items() if isinstance(v, list)}
    for record_type, rows in arrays.items():
        live_ids = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("id") or "")[:180]
            if not rid:
                continue
            live_ids.append(rid)
            PlatformRecord.objects.update_or_create(
                workspace_key="t4f-global",
                record_type=record_type,
                record_id=rid,
                defaults={
                    "organization_id": str(row.get("orgId") or row.get("organizationId") or "")[:120],
                    "country": str(row.get("country") or "")[:120],
                    "user_ref": str(row.get("userId") or row.get("ownerUserId") or "")[:160],
                    "status": str(row.get("status") or row.get("workflowStatus") or "")[:80],
                    "data": row,
                },
            )
        stale = PlatformRecord.objects.filter(workspace_key="t4f-global", record_type=record_type)
        if live_ids:
            stale = stale.exclude(record_id__in=live_ids)
        stale.delete()

    AuditEvent.objects.create(
        actor=user,
        organization_id=getattr(user.platform_profile, "organization_id", "") if hasattr(user, "platform_profile") else "",
        action="workspace.sync",
        entity_type="workspace",
        entity_id="t4f-global",
        detail={"revision": ws.revision},
    )

    invalidate_workspace("t4f-global")
    invalidate_users()
    return ws

@transaction.atomic
def save_platform_record(
    workspace_key: str,
    record_type: str,
    record_id: str,
    org_id: str,
    country: str,
    user_ref: str,
    status: str,
    data: dict,
    actor: Optional[User] = None,
) -> dict:
    """Atomically create or update a single PlatformRecord, logging audit and invalidating cache."""
    data = dict(data)
    data.setdefault("id", record_id)
    obj, _ = PlatformRecord.objects.select_for_update().update_or_create(
        workspace_key=workspace_key,
        record_type=record_type,
        record_id=record_id,
        defaults={
            "organization_id": org_id,
            "country": country,
            "user_ref": user_ref,
            "status": status or data.get("workflowStatus", "") or data.get("status", ""),
            "data": data,
        },
    )
    AuditEvent.objects.create(
        actor=actor,
        organization_id=org_id,
        action="record.save",
        entity_type=record_type,
        entity_id=record_id,
        detail={"status": status},
    )
    invalidate_records(record_type, workspace_key)
    return obj.data

@transaction.atomic
def delete_platform_record(
    workspace_key: str,
    record_type: str,
    record_id: str,
    actor: Optional[User] = None,
) -> bool:
    """Atomically delete a PlatformRecord, logging audit and invalidating cache."""
    obj = PlatformRecord.objects.select_for_update().filter(
        workspace_key=workspace_key,
        record_type=record_type,
        record_id=record_id,
    ).first()
    if not obj:
        return False
    org_id = obj.organization_id
    obj.delete()
    AuditEvent.objects.create(
        actor=actor,
        organization_id=org_id,
        action="record.delete",
        entity_type=record_type,
        entity_id=record_id,
        detail={},
    )
    invalidate_records(record_type, workspace_key)
    return True

@transaction.atomic
def create_attendance_event_record(
    user: User,
    profile: Optional[PlatformProfile],
    event_type: str,
    occurred_at: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    accuracy_m: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Atomically log an attendance punch event, create audit trail, and invalidate cache."""
    when = timezone.now() if not occurred_at else datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    p_id = profile.platform_user_id if profile else str(user.pk)
    org_id = profile.organization_id if profile else ""
    rid = f"{p_id}-{int(when.timestamp() * 1000)}-{event_type}"
    data = {
        "id": rid,
        "userId": p_id,
        "orgId": org_id,
        "eventType": event_type,
        "time": when.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy_m,
        "metadata": metadata or {},
    }
    PlatformRecord.objects.create(
        workspace_key="t4f-global",
        record_type="attendanceEvents",
        record_id=rid,
        organization_id=org_id,
        user_ref=p_id,
        status=event_type,
        data=data,
    )
    AuditEvent.objects.create(
        actor=user,
        organization_id=org_id,
        action="attendance.event",
        entity_type="attendanceEvents",
        entity_id=rid,
        detail={"eventType": event_type},
    )
    invalidate_attendance()
    return data

@transaction.atomic
def provision_invited_user(
    invited_by: User,
    organization_id: str,
    name: str,
    email: str,
    position_id: str = "",
    system_role: str = "standard_user",
) -> tuple[dict, str]:
    """Atomically provision invited user, issue temporary credentials, and create Invitation record."""
    clean_email = str(email).strip().lower()
    org = Organization.objects.filter(pk=organization_id).first()
    if not org:
        raise ValueError("Organization not found")

    user, _ = User.objects.get_or_create(username=clean_email, defaults={"email": clean_email})
    user.email = clean_email
    user.is_active = True
    temp = secrets.token_hex(4)
    user.set_password(temp)
    parts = name.strip().split(" ", 1)
    user.first_name = parts[0] if parts else ""
    user.last_name = parts[1] if len(parts) > 1 else ""
    user.save()

    pos = Position.objects.filter(pk=position_id).first() if position_id else None
    profile, _ = PlatformProfile.objects.update_or_create(
        user=user,
        defaults={
            "platform_user_id": f"user-{user.pk}",
            "organization": org,
            "position": pos,
            "system_role": system_role,
            "status": "Invited",
            "must_reset": True,
            "invited_at": timezone.now(),
        },
    )
    raw = secrets.token_urlsafe(32)
    Invitation.objects.create(
        email=clean_email,
        organization=org,
        invited_by=invited_by,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        expires_at=timezone.now() + timedelta(days=7),
        metadata={"platform_user_id": profile.platform_user_id},
    )
    AuditEvent.objects.create(
        actor=invited_by,
        organization_id=organization_id,
        action="user.invite",
        entity_type="user",
        entity_id=profile.platform_user_id,
        detail={"email": clean_email, "role": system_role},
    )
    invalidate_users(organization_id)
    return user_payload(user), temp

@transaction.atomic
def change_user_password(user: User, current_password: str, new_password: str) -> dict:
    """Atomically validate and update user password."""
    if len(new_password) < 8:
        raise ValueError("The password must be at least 8 characters long.")
    profile = getattr(user, "platform_profile", None)
    if not (profile and profile.must_reset):
        if not current_password or not user.check_password(current_password):
            raise ValueError("Current password is incorrect")
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        raise ValueError(" ".join(e.messages))

    user.set_password(new_password)
    user.save(update_fields=["password"])
    if profile:
        profile.must_reset = False
        profile.status = "Active"
        profile.save(update_fields=["must_reset", "status", "updated_at"])

    AuditEvent.objects.create(
        actor=user,
        organization_id=getattr(profile, "organization_id", ""),
        action="user.change_password",
        entity_type="user",
        entity_id=str(user.pk),
        detail={},
    )
    invalidate_users(getattr(profile, "organization_id", ""))
    return {"ok": True}

@transaction.atomic
def save_uploaded_file(
    owner: User,
    organization_id: str,
    category: str,
    filename: str,
    mime_type: str,
    content: bytes,
    classification: str = "Internal",
) -> FileObject:
    """Atomically save uploaded file object and metadata."""
    digest = hashlib.sha256(content).hexdigest()
    obj = FileObject(
        owner=owner,
        organization_id=organization_id,
        category=category,
        original_name=filename,
        mime_type=mime_type,
        size_bytes=len(content),
        sha256=digest,
        classification=classification,
    )
    obj.stored_file.save(filename or f"{digest}.bin", ContentFile(content), save=True)
    AuditEvent.objects.create(
        actor=owner,
        organization_id=organization_id,
        action="file.upload",
        entity_type="file",
        entity_id=str(obj.id),
        detail={"size": len(content), "category": category},
    )
    invalidate_files(organization_id)
    return obj
