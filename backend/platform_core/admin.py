from django.contrib import admin
from .models import Organization, Position, PlatformProfile, ApiSession, WorkspaceState, PlatformRecord, AuditEvent, FileObject, Invitation
for model in [Organization, Position, PlatformProfile, ApiSession, WorkspaceState, PlatformRecord, AuditEvent, FileObject, Invitation]:
    admin.site.register(model)
