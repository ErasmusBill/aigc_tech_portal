import uuid
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
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
    SYSTEM_ROLE_CHOICES,
    STATUS_CHOICES,
)

# ==============================================================================
# Platform Profile Inline for User Admin (Change View)
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
# Custom User Creation Form (Add View with Organization & Position)
# ==============================================================================
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False, label="First Name")
    last_name = forms.CharField(max_length=150, required=False, label="Last Name")
    email = forms.EmailField(
        required=True,
        label="Email Address",
        help_text="Required for portal login and communications.",
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label="Organization",
        help_text="Assign user to Headquarters or one of the 16 West Africa Country Portals.",
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        label="Hierarchy Position",
        help_text="Select their standardized operational position / job title.",
    )
    system_role = forms.ChoiceField(
        choices=SYSTEM_ROLE_CHOICES,
        initial="standard_user",
        label="System Access Role",
        help_text="Controls operational permissions and security tier.",
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial="Active",
        label="Portal Status",
    )
    must_reset = forms.BooleanField(
        required=False,
        initial=False,
        label="Must Reset Password",
        help_text="Prompt user to change temporary password upon first login.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "organization",
            "position",
            "system_role",
            "status",
            "must_reset",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user

# ==============================================================================
# Custom User Admin with Profile Integration
# ==============================================================================
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
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

    add_fieldsets = (
        (
            "Account Credentials",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Platform Hierarchy & Organization Assignment",
            {
                "classes": ("wide",),
                "description": "Assign this user to an Organization and operational Position immediately upon creation.",
                "fields": (
                    "organization",
                    "position",
                    "system_role",
                    "status",
                    "must_reset",
                ),
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        return self.inlines

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
        if not change and hasattr(form, "cleaned_data"):
            hq = Organization.objects.filter(pk="t4f-hq").first()
            org = form.cleaned_data.get("organization") or hq
            pos = form.cleaned_data.get("position")
            role = form.cleaned_data.get("system_role") or ("platform_super_admin" if obj.is_superuser else "standard_user")
            status_val = form.cleaned_data.get("status") or "Active"
            must_reset_val = form.cleaned_data.get("must_reset", False)
            PlatformProfile.objects.update_or_create(
                user=obj,
                defaults={
                    "platform_user_id": str(uuid.uuid4()),
                    "organization": org,
                    "position": pos,
                    "system_role": role,
                    "status": status_val,
                    "must_reset": must_reset_val,
                },
            )
        elif not hasattr(obj, "platform_profile"):
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
