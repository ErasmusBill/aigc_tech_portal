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
def test_deleted_records_are_removed():
    org=Organization.objects.create(id="t4f-hq",name="HQ",organization_type="global_hq")
    user=User.objects.create_user("admin2@example.org",password="A-strong-test-password-123!")
    PlatformProfile.objects.create(user=user,platform_user_id="u2",organization=org,system_role="platform_super_admin")
    save_workspace_state({"organizations":[{"id":"t4f-hq","name":"HQ","type":"global_hq"}],"users":[],"reports":[{"id":"r1","orgId":"t4f-hq","title":"R"}]},user)
    save_workspace_state({"organizations":[{"id":"t4f-hq","name":"HQ","type":"global_hq"}],"users":[],"reports":[]},user)
    from platform_core.models import PlatformRecord
    assert not PlatformRecord.objects.filter(record_type="reports",record_id="r1").exists()
