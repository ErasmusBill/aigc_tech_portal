import uuid
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Organization(TimestampedModel):
    id = models.CharField(primary_key=True, max_length=120)
    name = models.CharField(max_length=255)
    organization_type = models.CharField(max_length=80, db_index=True)
    country = models.CharField(max_length=120, blank=True, db_index=True)
    parent_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=40, default="Active", db_index=True)
    contact = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    def __str__(self): return self.name

class Position(TimestampedModel):
    id = models.CharField(primary_key=True, max_length=150)
    title = models.CharField(max_length=255)
    family = models.CharField(max_length=80, db_index=True)
    group = models.CharField(max_length=180, blank=True)
    reports_to = models.CharField(max_length=255, blank=True)
    role_purpose = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    def __str__(self): return self.title

class PlatformProfile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="platform_profile")
    platform_user_id = models.CharField(max_length=160, unique=True, db_index=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="profiles")
    position = models.ForeignKey(Position, null=True, blank=True, on_delete=models.SET_NULL, related_name="profiles")
    system_role = models.CharField(max_length=80, default="standard_user", db_index=True)
    status = models.CharField(max_length=40, default="Active", db_index=True)
    must_reset = models.BooleanField(default=True)
    profile_data = models.JSONField(default=dict, blank=True)
    invited_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

class ApiSession(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_sessions")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

class WorkspaceState(TimestampedModel):
    key = models.CharField(primary_key=True, max_length=100, default="t4f-global")
    revision = models.BigIntegerField(default=1)
    state = models.JSONField(default=dict)
    last_saved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

class PlatformRecord(TimestampedModel):
    workspace_key = models.CharField(max_length=100, default="t4f-global", db_index=True)
    record_type = models.CharField(max_length=80, db_index=True)
    record_id = models.CharField(max_length=180)
    organization_id = models.CharField(max_length=120, blank=True, db_index=True)
    country = models.CharField(max_length=120, blank=True, db_index=True)
    user_ref = models.CharField(max_length=160, blank=True, db_index=True)
    status = models.CharField(max_length=80, blank=True, db_index=True)
    data = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace_key","record_type","record_id"], name="uniq_platform_record")]
        indexes = [models.Index(fields=["record_type","organization_id"]), models.Index(fields=["record_type","status"])]

class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    organization_id = models.CharField(max_length=120, blank=True, db_index=True)
    action = models.CharField(max_length=180, db_index=True)
    entity_type = models.CharField(max_length=100, blank=True, db_index=True)
    entity_id = models.CharField(max_length=180, blank=True, db_index=True)
    detail = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

class FileObject(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    organization_id = models.CharField(max_length=120, blank=True, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    original_name = models.CharField(max_length=255)
    stored_file = models.FileField(upload_to="platform/%Y/%m/%d/")
    mime_type = models.CharField(max_length=160, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    classification = models.CharField(max_length=80, default="Internal")
    metadata = models.JSONField(default=dict, blank=True)

class Invitation(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    invited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_invitations")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
