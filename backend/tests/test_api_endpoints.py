import pytest
from fastapi.testclient import TestClient
from django.contrib.auth.models import User
from platform_core.models import Organization, PlatformProfile, Position, PlatformRecord
from platform_core.services import issue_api_session
from api.main import api_app

client = TestClient(api_app)

@pytest.fixture
def auth_headers(db):
    org = Organization.objects.create(id="org-test-api", name="Test Org", organization_type="global_hq")
    user = User.objects.create_user("superadmin@example.org", password="AStrongPassword123!")
    profile = PlatformProfile.objects.create(
        user=user,
        platform_user_id="user-superadmin",
        organization=org,
        system_role="platform_super_admin",
    )
    token = issue_api_session(user)
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.django_db(transaction=True)
def test_api_records_pagination_caching_and_atomic_crud(auth_headers):
    # 1. Insert 5 test records
    for i in range(5):
        res = client.put(
            f"/records/testItems/item-{i}",
            json={
                "id": f"item-{i}",
                "orgId": "org-test-api",
                "status": "Active",
                "data": {"id": f"item-{i}", "num": i, "orgId": "org-test-api"},
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

    # 2. Query paginated records: page 1 with limit=2
    res_p1 = client.get("/records/testItems?limit=2&offset=0", headers=auth_headers)
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total"] == 5
    assert len(data_p1["rows"]) == 2
    assert data_p1["page"] == 1
    assert data_p1["pages"] == 3
    assert data_p1["has_next"] is True
    assert data_p1["has_prev"] is False
    assert data_p1["next_offset"] == 2

    # 3. Query paginated records: page 2 with limit=2, offset=2
    res_p2 = client.get("/records/testItems?limit=2&offset=2", headers=auth_headers)
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2["rows"]) == 2
    assert data_p2["page"] == 2
    assert data_p2["has_next"] is True
    assert data_p2["has_prev"] is True

    # 4. Atomic Delete
    res_del = client.delete("/records/testItems/item-0", headers=auth_headers)
    assert res_del.status_code == 200
    assert res_del.json()["ok"] is True

    # 5. Verify cache invalidation occurred and total decreased to 4
    res_after = client.get("/records/testItems?limit=10&offset=0", headers=auth_headers)
    assert res_after.status_code == 200
    assert res_after.json()["total"] == 4

@pytest.mark.django_db(transaction=True)
def test_api_users_pagination_and_atomic_invite(auth_headers):
    # 1. Query users
    res_users = client.get("/users?limit=10&offset=0", headers=auth_headers)
    assert res_users.status_code == 200
    data = res_users.json()
    assert "rows" in data
    assert "total" in data
    initial_total = data["total"]

    # 2. Invite a new user
    res_invite = client.post(
        "/users/invite",
        json={
            "organization_id": "org-test-api",
            "name": "Jane Doe",
            "email": "jane.doe@example.org",
            "system_role": "standard_user",
        },
        headers=auth_headers,
    )
    assert res_invite.status_code == 200
    assert "temporary_password" in res_invite.json()

    # 3. Verify user list cache invalidation reflects new total
    res_after = client.get("/users?limit=10&offset=0", headers=auth_headers)
    assert res_after.status_code == 200
    assert res_after.json()["total"] == initial_total + 1

@pytest.mark.django_db(transaction=True)
def test_api_attendance_event_atomic_and_pagination(auth_headers):
    # 1. Clock in
    res_punch = client.post(
        "/attendance/event",
        json={"event_type": "CHECK_IN", "latitude": 41.8781, "longitude": -87.6298},
        headers=auth_headers,
    )
    assert res_punch.status_code == 200
    assert res_punch.json()["ok"] is True

    # 2. List attendance events with pagination
    res_events = client.get("/attendance/events?limit=10&offset=0", headers=auth_headers)
    assert res_events.status_code == 200
    body = res_events.json()
    assert body["total"] >= 1
    assert len(body["rows"]) >= 1
    assert body["rows"][0]["eventType"] == "CHECK_IN"
