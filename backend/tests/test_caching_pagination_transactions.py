import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from platform_core.models import Organization, PlatformProfile, Position, PlatformRecord, WorkspaceState, FileObject
from platform_core.services import (
    save_workspace_state,
    save_platform_record,
    delete_platform_record,
    create_attendance_event_record,
    provision_invited_user,
    change_user_password,
    save_uploaded_file,
)
from platform_core.cache import (
    invalidate_workspace,
    invalidate_records,
    invalidate_users,
    get_namespace_version,
    record_namespace,
    user_namespace,
)
from platform_core.pagination import paginate_sequence

@pytest.mark.django_db
def test_atomic_record_create_update_delete():
    user = User.objects.create_user("actor@example.org", password="ValidPassword123!")
    org = Organization.objects.create(id="org-atomic", name="Atomic Org", organization_type="country_office")

    # 1. Create record atomically
    data = save_platform_record(
        workspace_key="t4f-global",
        record_type="projects",
        record_id="proj-1",
        org_id="org-atomic",
        country="USA",
        user_ref="actor@example.org",
        status="Active",
        data={"id": "proj-1", "title": "Project One"},
        actor=user,
    )
    assert data["title"] == "Project One"
    rec = PlatformRecord.objects.get(record_type="projects", record_id="proj-1")
    assert rec.status == "Active"

    # 2. Update record atomically
    data_up = save_platform_record(
        workspace_key="t4f-global",
        record_type="projects",
        record_id="proj-1",
        org_id="org-atomic",
        country="USA",
        user_ref="actor@example.org",
        status="Completed",
        data={"id": "proj-1", "title": "Project One Updated"},
        actor=user,
    )
    assert data_up["title"] == "Project One Updated"
    rec.refresh_from_db()
    assert rec.status == "Completed"

    # 3. Delete record atomically
    deleted = delete_platform_record("t4f-global", "projects", "proj-1", actor=user)
    assert deleted is True
    assert not PlatformRecord.objects.filter(record_type="projects", record_id="proj-1").exists()

@pytest.mark.django_db
def test_atomic_transaction_rollback():
    """Ensure that if an exception occurs inside a transaction block, changes roll back."""
    user = User.objects.create_user("rollback@example.org", password="ValidPassword123!")
    
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            PlatformRecord.objects.create(
                workspace_key="t4f-global",
                record_type="projects",
                record_id="proj-fail",
                data={"name": "Will rollback"},
            )
            raise RuntimeError("Forced transaction failure")

    assert not PlatformRecord.objects.filter(record_id="proj-fail").exists()

@pytest.mark.django_db
def test_cache_invalidation_on_mutation():
    user = User.objects.create_user("cache_tester@example.org", password="ValidPassword123!")
    
    # Check version before creation
    ns = record_namespace("t4f-global", "tasks")
    v1 = get_namespace_version(ns)

    # Creating a record invalidates records cache
    save_platform_record(
        workspace_key="t4f-global",
        record_type="tasks",
        record_id="task-1",
        org_id="org-cache",
        country="",
        user_ref="",
        status="Pending",
        data={"id": "task-1", "title": "Task 1"},
        actor=user,
    )
    v2 = get_namespace_version(ns)
    assert v2 > v1

    # Deleting a record invalidates records cache again
    delete_platform_record("t4f-global", "tasks", "task-1", actor=user)
    v3 = get_namespace_version(ns)
    assert v3 > v2

@pytest.mark.django_db
def test_pagination_helper_and_calculations():
    items = list(range(100))
    
    # Page 1 (limit 20, offset 0)
    p1 = paginate_sequence(items[0:20], total=100, limit=20, offset=0)
    assert p1["page"] == 1
    assert p1["pages"] == 5
    assert p1["total"] == 100
    assert p1["has_next"] is True
    assert p1["has_prev"] is False
    assert p1["next_offset"] == 20
    assert p1["prev_offset"] is None
    assert len(p1["rows"]) == 20

    # Middle Page (limit 20, offset 40 -> page 3)
    p3 = paginate_sequence(items[40:60], total=100, limit=20, offset=40)
    assert p3["page"] == 3
    assert p3["pages"] == 5
    assert p3["has_next"] is True
    assert p3["has_prev"] is True
    assert p3["next_offset"] == 60
    assert p3["prev_offset"] == 20

    # Last Page (limit 20, offset 80 -> page 5)
    p5 = paginate_sequence(items[80:100], total=100, limit=20, offset=80)
    assert p5["page"] == 5
    assert p5["has_next"] is False
    assert p5["has_prev"] is True
    assert p5["next_offset"] is None
    assert p5["prev_offset"] == 60

@pytest.mark.django_db
def test_user_provisioning_and_password_change_atomic():
    admin = User.objects.create_user("super@example.org", password="ValidPassword123!")
    org = Organization.objects.create(id="hq-test", name="HQ Test", organization_type="global_hq")

    # Atomic invite
    u_dict, temp = provision_invited_user(
        invited_by=admin,
        organization_id="hq-test",
        name="John Doe",
        email="john.doe@example.org",
        position_id="",
        system_role="standard_user",
    )
    assert u_dict["email"] == "john.doe@example.org"
    user_obj = User.objects.get(username="john.doe@example.org")
    assert user_obj.check_password(temp)
    assert user_obj.platform_profile.must_reset is True

    # Attempting to change to non-8-character password fails
    with pytest.raises(ValueError) as exc:
        change_user_password(user_obj, current_password="", new_password="TooLongPassword123!")
    assert "8 characters long" in str(exc.value)

    # Atomic change password with exactly 8 characters succeeds
    res = change_user_password(user_obj, current_password="", new_password="T4F@2026")
    assert res["ok"] is True
    user_obj.refresh_from_db()
    assert user_obj.check_password("T4F@2026")
    assert user_obj.platform_profile.must_reset is False
