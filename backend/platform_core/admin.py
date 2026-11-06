import uuid
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Organization,
    Position,
    PlatformProfile,
    ApiSession,
    WorkspaceState,
    PlatformRecord,
    AuditEvent,
    FileObject,
    Invitation,
)

# ==============================================================================
# Platform Profile Inline for User Admin
# ==============================================================================
class PlatformProfileInline(admin.StackedInline):
    model = PlatformProfile
    can_delete = False
    verbose_name = "Platform Hierarchy & Organization Profile"
    verbose_name_plural = "Platform Hierarchy & Organization Profile"
    fields = (
        "organization",
        "position",
        "system_role",
        "status",
        "must_reset",
        "platform_user_id",
    )
    readonly_fields = ("platform_user_id",)
    extra = 0

# ==============================================================================
# Custom User Admin with Profile Integration
# ==============================================================================
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = [PlatformProfileInline]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_organization",
        "get_system_role",
        "get_profile_status",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "platform_profile__organization",
        "platform_profile__system_role",
        "platform_profile__status",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "platform_profile__platform_user_id",
    )
    ordering = ("username",)

    @admin.display(description="Organization", ordering="platform_profile__organization")
    def get_organization(self, obj):
        profile = getattr(obj, "platform_profile", None)
        return profile.organization.name if profile and profile.organization else "—"

    @admin.display(description="System Role", ordering="platform_profile__system_role")
    def get_system_role(self, obj):
        profile = getattr(obj, "platform_profile", None)
        return profile.system_role.replace("_", " ").title() if profile else "—"

    @admin.display(description="Portal Status", ordering="platform_profile__status")
    def get_profile_status(self, obj):
        profile = getattr(obj, "platform_profile", None)
        return profile.status if profile else "Active"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure a platform profile exists for every user
        if not hasattr(obj, "platform_profile"):
            hq = Organization.objects.filter(pk="t4f-hq").first()
            PlatformProfile.objects.create(
                user=obj,
                platform_user_id=str(uuid.uuid4()),
                organization=hq,
                system_role="platform_super_admin" if obj.is_superuser else "standard_user",
                status="Active",
                must_reset=False,
            )

# ==============================================================================
# Model Admins for Platform Core
# ==============================================================================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization_type", "country", "status", "updated_at")
    list_filter = ("organization_type", "status", "country")
    search_fields = ("id", "name", "country")
    ordering = ("name",)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "family", "group", "reports_to")
    list_filter = ("family", "group")
    search_fields = ("id", "title", "role_purpose")
    ordering = ("title",)

@admin.register(PlatformProfile)
class PlatformProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "position", "system_role", "status", "must_reset", "last_seen_at")
    list_filter = ("organization", "system_role", "status", "must_reset")
    search_fields = ("user__username", "user__email", "platform_user_id")
    raw_id_fields = ("user",)

@admin.register(PlatformRecord)
class PlatformRecordAdmin(admin.ModelAdmin):
    list_display = ("record_id", "record_type", "organization_id", "country", "status", "created_at")
    list_filter = ("record_type", "status", "country")
    search_fields = ("record_id", "record_type", "organization_id")
    ordering = ("-created_at",)

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "actor", "action", "entity_type", "entity_id", "organization_id")
    list_filter = ("action", "entity_type", "occurred_at")
    search_fields = ("action", "entity_id", "organization_id")
    readonly_fields = ("id", "occurred_at", "actor", "action", "entity_type", "entity_id", "organization_id", "detail")
    ordering = ("-occurred_at",)

@admin.register(ApiSession)
class ApiSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "expires_at", "revoked_at", "created_at")
    list_filter = ("revoked_at", "expires_at")
    search_fields = ("user__username", "user__email", "ip_address")
    readonly_fields = ("id", "user", "token_hash", "created_at", "expires_at", "user_agent", "ip_address")
    ordering = ("-created_at",)

@admin.register(FileObject)
class FileObjectAdmin(admin.ModelAdmin):
    list_display = ("original_name", "category", "classification", "size_bytes", "owner", "created_at")
    list_filter = ("category", "classification")
    search_fields = ("original_name", "sha256")
    ordering = ("-created_at",)

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "invited_by", "expires_at", "accepted_at", "created_at")
    list_filter = ("organization", "accepted_at")
    search_fields = ("email",)
    ordering = ("-created_at",)

@admin.register(WorkspaceState)
class WorkspaceStateAdmin(admin.ModelAdmin):
    list_display = ("key", "revision", "last_saved_by", "updated_at")
    readonly_fields = ("key", "revision", "updated_at", "created_at")
