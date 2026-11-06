import uuid
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
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
# Helper Formatting Utilities
# ==============================================================================
def format_file_size(size_bytes):
    try:
        b = float(size_bytes or 0)
        if b < 1024:
            return f"{int(b)} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        return f"{b / (1024 * 1024 * 1024):.2f} GB"
    except (ValueError, TypeError):
        return "—"


# ==============================================================================
# Platform Profile Inline for User Admin (Change View)
# ==============================================================================
class PlatformProfileInline(admin.StackedInline):
    model = PlatformProfile
    can_delete = False
    verbose_name = "Platform Hierarchy & Organization Profile"
    verbose_name_plural = "Platform Hierarchy & Organization Profile"
    fields = (
        ("organization", "position"),
        ("system_role", "status", "must_reset"),
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
        help_text="Required for portal login and system notifications.",
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label="Assigned Organization",
        help_text="Select Headquarters or one of the 16 West Africa Country Portals.",
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
        "get_full_name_display",
        "get_organization_badge",
        "get_system_role_badge",
        "get_profile_status_badge",
        "get_staff_badge",
        "date_joined",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "platform_profile__organization",
        "platform_profile__system_role",
        "platform_profile__status",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "platform_profile__organization__name",
        "platform_profile__platform_user_id",
    )
    ordering = ("username",)
    actions = ["activate_users", "deactivate_users", "require_password_reset"]

    add_fieldsets = (
        (
            "Account Credentials",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    ("first_name", "last_name"),
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Platform Hierarchy & Organization Assignment",
            {
                "classes": ("wide",),
                "description": "Select the organization, position, and role for this user account.",
                "fields": (
                    ("organization", "position"),
                    ("system_role", "status"),
                    "must_reset",
                ),
            },
        ),
    )

    fieldsets = (
        (
            "Account Credentials",
            {
                "fields": ("username", "password"),
                "description": "Primary login identifier and password authentication.",
            },
        ),
        (
            "Personal Information",
            {
                "fields": (("first_name", "last_name"), "email"),
            },
        ),
        (
            "Portal Permissions & Status",
            {
                "fields": (
                    ("is_active", "is_staff"),
                    "is_superuser",
                ),
                "description": "Active users can log into the portal. Staff users have access to this administration console.",
            },
        ),
        (
            "Advanced Django ORM Permissions",
            {
                "classes": ("collapse",),
                "fields": ("groups", "user_permissions"),
                "description": "Granular database permissions (portal roles are managed under Platform Profile below).",
            },
        ),
        (
            "Important Audit Dates",
            {
                "classes": ("collapse",),
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        return self.inlines

    @admin.display(description="Full Name")
    def get_full_name_display(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else "—"

    @admin.display(description="Organization", ordering="platform_profile__organization")
    def get_organization_badge(self, obj):
        profile = getattr(obj, "platform_profile", None)
        if profile and profile.organization:
            url = reverse("admin:platform_core_organization_change", args=[profile.organization.id])
            return format_html(
                '<a href="{}" class="font-weight-bold text-dark"><i class="fas fa-building text-primary mr-1"></i>{}</a>',
                url,
                profile.organization.name,
            )
        return mark_safe('<span class="text-muted font-italic">Unassigned</span>')

    @admin.display(description="System Role", ordering="platform_profile__system_role")
    def get_system_role_badge(self, obj):
        profile = getattr(obj, "platform_profile", None)
        role = profile.system_role if profile else ("platform_super_admin" if obj.is_superuser else "standard_user")
        role_map = {
            "platform_super_admin": ("badge-primary bg-primary", "fas fa-shield-alt", "Platform Super Admin"),
            "high_super_admin": ("badge-purple", "fas fa-crown", "High Super Admin"),
            "country_super_admin": ("badge-info bg-info", "fas fa-globe-africa", "Country Super Admin"),
            "country_it_admin": ("badge-teal", "fas fa-user-cog", "Country IT Admin"),
            "standard_user": ("badge-secondary bg-secondary", "fas fa-user", "Standard User"),
        }
        badge_class, icon, label = role_map.get(role, ("badge-secondary bg-secondary", "fas fa-user", role.replace("_", " ").title()))
        return format_html('<span class="badge {}"><i class="{} mr-1"></i>{}</span>', badge_class, icon, label)

    @admin.display(description="Status", ordering="platform_profile__status")
    def get_profile_status_badge(self, obj):
        profile = getattr(obj, "platform_profile", None)
        status = profile.status if profile else ("Active" if obj.is_active else "Inactive")
        if status == "Active":
            return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-check-circle mr-1"></i>Active</span>')
        elif status == "Suspended":
            return mark_safe('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-pause-circle mr-1"></i>Suspended</span>')
        return mark_safe('<span class="badge badge-danger bg-danger"><i class="fas fa-times-circle mr-1"></i>Inactive</span>')

    @admin.display(description="Access Tier")
    def get_staff_badge(self, obj):
        if obj.is_superuser:
            return mark_safe('<span class="badge badge-danger bg-danger"><i class="fas fa-user-shield mr-1"></i>Superuser</span>')
        elif obj.is_staff:
            return mark_safe('<span class="badge badge-primary bg-primary"><i class="fas fa-user-tie mr-1"></i>Staff Admin</span>')
        return mark_safe('<span class="badge badge-light bg-light text-dark border"><i class="fas fa-user mr-1"></i>Portal User</span>')

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        PlatformProfile.objects.filter(user__in=queryset).update(status="Active")
        self.message_user(request, f"Successfully activated {count} user(s).")

    @admin.action(description="Deactivate / Suspend selected users")
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        PlatformProfile.objects.filter(user__in=queryset).update(status="Inactive")
        self.message_user(request, f"Successfully deactivated {count} user(s).")

    @admin.action(description="Require password reset on next login")
    def require_password_reset(self, request, queryset):
        count = PlatformProfile.objects.filter(user__in=queryset).update(must_reset=True)
        self.message_user(request, f"Set password reset requirement on {count} user(s).")

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
    list_display = ("name", "id", "get_type_badge", "country", "get_status_badge", "get_user_count", "updated_at")
    list_filter = ("organization_type", "status", "country")
    search_fields = ("id", "name", "country", "parent_id")
    ordering = ("name",)
    fieldsets = (
        (
            "Organization Profile",
            {
                "fields": (("name", "id"), ("organization_type", "country"), ("status", "parent_id")),
            },
        ),
        (
            "Contact & Operational Metadata",
            {
                "classes": ("collapse",),
                "fields": ("contact", "metadata"),
            },
        ),
    )

    @admin.display(description="Type", ordering="organization_type")
    def get_type_badge(self, obj):
        t = obj.organization_type or "general"
        if t == "global_hq":
            return mark_safe('<span class="badge badge-primary bg-primary"><i class="fas fa-landmark mr-1"></i>Global HQ</span>')
        elif t == "country_office":
            return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-globe-africa mr-1"></i>Country Office</span>')
        elif t == "external_partner":
            return mark_safe('<span class="badge badge-info bg-info"><i class="fas fa-handshake mr-1"></i>Partner</span>')
        elif t == "fiscal_sponsor":
            return mark_safe('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-donate mr-1"></i>Fiscal Sponsor</span>')
        return format_html('<span class="badge badge-secondary bg-secondary">{}</span>', t.replace("_", " ").title())

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        if obj.status == "Active":
            return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-check-circle mr-1"></i>Active</span>')
        return mark_safe('<span class="badge badge-danger bg-danger"><i class="fas fa-times-circle mr-1"></i>Inactive</span>')

    @admin.display(description="Assigned Staff")
    def get_user_count(self, obj):
        count = obj.profiles.count()
        return format_html('<span class="badge badge-light bg-light text-dark border font-weight-bold"><i class="fas fa-users mr-1"></i>{} staff</span>', count)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "id", "get_family_badge", "group", "reports_to", "get_holders_count")
    list_filter = ("family", "group")
    search_fields = ("id", "title", "family", "group", "role_purpose")
    ordering = ("title",)
    fieldsets = (
        (
            "Position Hierarchy",
            {
                "fields": (("title", "id"), ("family", "group"), "reports_to"),
            },
        ),
        (
            "Terms of Reference (TOR)",
            {
                "fields": ("role_purpose", "metadata"),
            },
        ),
    )

    @admin.display(description="Family", ordering="family")
    def get_family_badge(self, obj):
        fam = obj.family or "general"
        fam_colors = {
            "global_management": "badge-primary bg-primary",
            "country_leadership": "badge-success bg-success",
            "global_employee": "badge-info bg-info",
            "volunteer": "badge-warning bg-warning text-dark",
        }
        color = fam_colors.get(fam, "badge-secondary bg-secondary")
        return format_html('<span class="badge {}">{}</span>', color, fam.replace("_", " ").title())

    @admin.display(description="Holders")
    def get_holders_count(self, obj):
        count = obj.profiles.count()
        return format_html('<span class="badge badge-light bg-light text-dark border font-weight-bold"><i class="fas fa-user-check mr-1"></i>{}</span>', count)


@admin.register(PlatformProfile)
class PlatformProfileAdmin(admin.ModelAdmin):
    list_display = ("get_user_link", "get_org_link", "position", "get_role_badge", "get_status_badge", "must_reset", "last_seen_at")
    list_filter = ("organization", "system_role", "status", "must_reset")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "platform_user_id")
    raw_id_fields = ("user",)
    readonly_fields = ("platform_user_id", "last_seen_at")

    @admin.display(description="User Account", ordering="user__username")
    def get_user_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}" class="font-weight-bold"><i class="fas fa-user text-primary mr-1"></i>{}</a>', url, obj.user.username)

    @admin.display(description="Organization", ordering="organization__name")
    def get_org_link(self, obj):
        if obj.organization:
            url = reverse("admin:platform_core_organization_change", args=[obj.organization.id])
            return format_html('<a href="{}" class="font-weight-bold text-dark"><i class="fas fa-building text-success mr-1"></i>{}</a>', url, obj.organization.name)
        return "—"

    @admin.display(description="Role", ordering="system_role")
    def get_role_badge(self, obj):
        role_map = {
            "platform_super_admin": ("badge-primary bg-primary", "Platform Super Admin"),
            "high_super_admin": ("badge-purple", "High Super Admin"),
            "country_super_admin": ("badge-info bg-info", "Country Super Admin"),
            "country_it_admin": ("badge-teal", "Country IT Admin"),
            "standard_user": ("badge-secondary bg-secondary", "Standard User"),
        }
        badge_class, label = role_map.get(obj.system_role, ("badge-secondary bg-secondary", obj.system_role.replace("_", " ").title()))
        return format_html('<span class="badge {}">{}</span>', badge_class, label)

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        if obj.status == "Active":
            return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-check-circle mr-1"></i>Active</span>')
        elif obj.status == "Suspended":
            return mark_safe('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-pause-circle mr-1"></i>Suspended</span>')
        return mark_safe('<span class="badge badge-danger bg-danger"><i class="fas fa-times-circle mr-1"></i>Inactive</span>')


@admin.register(PlatformRecord)
class PlatformRecordAdmin(admin.ModelAdmin):
    list_display = ("record_id", "get_type_badge", "organization_id", "country", "get_status_badge", "created_at")
    list_filter = ("record_type", "status", "country")
    search_fields = ("record_id", "record_type", "organization_id", "country", "user_ref")
    ordering = ("-created_at",)

    @admin.display(description="Record Type", ordering="record_type")
    def get_type_badge(self, obj):
        t = obj.record_type or "general"
        type_colors = {
            "projects": "badge-primary bg-primary",
            "reports": "badge-success bg-success",
            "finance": "badge-info bg-info",
            "documents": "badge-purple",
            "grants": "badge-teal",
        }
        color = type_colors.get(t, "badge-secondary bg-secondary")
        return format_html('<span class="badge {}">{}</span>', color, t.title())

    @admin.display(description="Status", ordering="status")
    def get_status_badge(self, obj):
        s = obj.status or "Active"
        if s.lower() in {"active", "approved", "published"}:
            return format_html('<span class="badge badge-success bg-success"><i class="fas fa-check-circle mr-1"></i>{}</span>', s)
        elif s.lower() in {"draft", "pending", "submitted"}:
            return format_html('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-edit mr-1"></i>{}</span>', s)
        return format_html('<span class="badge badge-secondary bg-secondary">{}</span>', s)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "actor", "get_action_badge", "entity_type", "entity_id", "organization_id")
    list_filter = ("action", "entity_type", "organization_id")
    search_fields = ("actor", "action", "entity_id", "organization_id", "entity_type")
    readonly_fields = ("id", "occurred_at", "actor", "action", "entity_type", "entity_id", "organization_id", "detail")
    date_hierarchy = "occurred_at"
    ordering = ("-occurred_at",)

    @admin.display(description="Action", ordering="action")
    def get_action_badge(self, obj):
        act = obj.action or ""
        if "sign" in act.lower() or "login" in act.lower():
            return format_html('<span class="badge badge-info bg-info"><i class="fas fa-sign-in-alt mr-1"></i>{}</span>', act)
        elif "create" in act.lower() or "init" in act.lower() or "add" in act.lower():
            return format_html('<span class="badge badge-success bg-success"><i class="fas fa-plus-circle mr-1"></i>{}</span>', act)
        elif "update" in act.lower() or "change" in act.lower():
            return format_html('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-edit mr-1"></i>{}</span>', act)
        elif "delete" in act.lower() or "remove" in act.lower():
            return format_html('<span class="badge badge-danger bg-danger"><i class="fas fa-trash mr-1"></i>{}</span>', act)
        return format_html('<span class="badge badge-secondary bg-secondary">{}</span>', act)


@admin.register(ApiSession)
class ApiSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "get_session_status", "expires_at", "created_at")
    list_filter = ("revoked_at", "expires_at")
    search_fields = ("user__username", "user__email", "ip_address")
    readonly_fields = ("id", "user", "token_hash", "created_at", "expires_at", "user_agent", "ip_address")
    ordering = ("-created_at",)
    actions = ["revoke_sessions"]

    @admin.display(description="Status")
    def get_session_status(self, obj):
        if obj.revoked_at:
            return mark_safe('<span class="badge badge-danger bg-danger"><i class="fas fa-ban mr-1"></i>Revoked</span>')
        elif obj.expires_at and obj.expires_at < timezone.now():
            return mark_safe('<span class="badge badge-secondary bg-secondary"><i class="fas fa-history mr-1"></i>Expired</span>')
        return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-key mr-1"></i>Active</span>')

    @admin.action(description="Revoke selected API sessions immediately")
    def revoke_sessions(self, request, queryset):
        count = queryset.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
        self.message_user(request, f"Revoked {count} active API session(s).")


@admin.register(FileObject)
class FileObjectAdmin(admin.ModelAdmin):
    list_display = ("original_name", "get_category_badge", "classification", "get_formatted_size", "owner", "created_at")
    list_filter = ("category", "classification")
    search_fields = ("original_name", "sha256")
    ordering = ("-created_at",)

    @admin.display(description="Category", ordering="category")
    def get_category_badge(self, obj):
        return format_html('<span class="badge badge-info bg-info"><i class="fas fa-file mr-1"></i>{}</span>', (obj.category or "file").title())

    @admin.display(description="Size", ordering="size_bytes")
    def get_formatted_size(self, obj):
        return format_file_size(obj.size_bytes)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "get_status_badge", "invited_by", "expires_at", "created_at")
    list_filter = ("organization", "accepted_at")
    search_fields = ("email", "organization__name")
    ordering = ("-created_at",)

    @admin.display(description="Status")
    def get_status_badge(self, obj):
        if obj.accepted_at:
            return mark_safe('<span class="badge badge-success bg-success"><i class="fas fa-check-circle mr-1"></i>Accepted</span>')
        elif obj.expires_at and obj.expires_at < timezone.now():
            return mark_safe('<span class="badge badge-secondary bg-secondary"><i class="fas fa-clock mr-1"></i>Expired</span>')
        return mark_safe('<span class="badge badge-warning bg-warning text-dark"><i class="fas fa-envelope mr-1"></i>Pending</span>')


@admin.register(WorkspaceState)
class WorkspaceStateAdmin(admin.ModelAdmin):
    list_display = ("key", "get_revision_badge", "last_saved_by", "updated_at")
    readonly_fields = ("key", "revision", "updated_at", "created_at")

    @admin.display(description="Revision", ordering="revision")
    def get_revision_badge(self, obj):
        return format_html('<span class="badge badge-primary bg-primary font-weight-bold">v{}</span>', obj.revision)
