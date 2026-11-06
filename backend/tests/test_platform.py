import os
os.environ.setdefault("DB_ENGINE","sqlite")
import pytest
from django.contrib.auth.models import User
from platform_core.models import Organization, PlatformProfile, Position, WorkspaceState
from platform_core.services import save_workspace_state

@pytest.mark.django_db
def test_workspace_state_roundtrip():
    org=Organization.objects.create(id="t4f-hq",name="HQ",organization_type="global_hq")
    pos=Position.objects.create(id="admin",title="Admin",family="global_management")
    user=User.objects.create_user("admin@example.org",password="A-strong-test-password-123!")
    PlatformProfile.objects.create(user=user,platform_user_id="u1",organization=org,position=pos,system_role="platform_super_admin")
    state={"organizations":[{"id":"t4f-hq","name":"HQ","type":"global_hq"}],"users":[{"id":"u1","orgId":"t4f-hq","name":"Admin","email":"admin@example.org","password":"Temporary-Password-123!","systemRole":"platform_super_admin","positionId":"admin","status":"Active"}],"reports":[]}
    ws=save_workspace_state(state,user)
    assert ws.revision >= 1
    assert "password" not in ws.state["users"][0]
    assert User.objects.get(username="admin@example.org").check_password("Temporary-Password-123!")

@pytest.mark.django_db
def test_custom_user_admin_and_profile_integration():
    from django.contrib.admin.sites import AdminSite
    from platform_core.admin import CustomUserAdmin
    org = Organization.objects.create(id="t4f-hq", name="Tech4Future Headquarters", organization_type="global_hq")
    admin_site = AdminSite()
    user_admin = CustomUserAdmin(User, admin_site)
    
    # Create a user through admin save_model
    new_user = User(username="newadmin", email="newadmin@t4f-global.org", is_superuser=True)
    new_user.set_password("SecurePassword2027!")
    user_admin.save_model(None, new_user, None, False)
    
    # Verify profile automatically provisioned
    assert hasattr(new_user, "platform_profile")
    assert new_user.platform_profile.organization == org
    assert new_user.platform_profile.system_role == "platform_super_admin"
    assert "Tech4Future Headquarters" in str(user_admin.get_organization_badge(new_user))
    assert "Platform Super Admin" in str(user_admin.get_system_role_badge(new_user))
