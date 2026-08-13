from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.equipment.models import Organization, OrganizationType
from app.modules.identity.models import Role, User


def headers(token: str, key: str = "key") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key}


def admin_token(client: TestClient) -> str:
    with client.app.state.session_factory() as db:
        bootstrap_admin(db, "admin", "admin-password")
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin-password"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_custom_role_lifecycle_is_idempotent_and_protected(client: TestClient) -> None:
    token = admin_token(client)
    body = {
        "code": "QUALITY_INSPECTOR",
        "name": "Quality inspector",
        "description": "Inspects repairs",
        "enabled": True,
        "permission_codes": ["identity:read"],
    }
    created = client.post("/api/roles", headers=headers(token, "create-role"), json=body)
    replay = client.post("/api/roles", headers=headers(token, "create-role"), json=body)
    assert created.status_code == replay.status_code == 201
    role_id = created.json()["id"]
    assert created.json()["description"] == "Inspects repairs"
    assert created.json()["user_count"] == 0
    updated = client.patch(f"/api/roles/{role_id}", headers=headers(token, "update-role"), json={**body, "name": "Quality lead", "enabled": False})
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    deleted = client.delete(f"/api/roles/{role_id}", headers=headers(token, "delete-role"))
    assert deleted.status_code == 200
    assert role_id not in {item["id"] for item in client.get("/api/roles", headers=headers(token)).json()}
    with client.app.state.session_factory() as db:
        assert db.scalar(select(Role).where(Role.id == role_id)) is None


def test_user_profile_reset_and_log_read_models(client: TestClient) -> None:
    token = admin_token(client)
    with client.app.state.session_factory() as db:
        root = db.scalar(select(Organization).where(Organization.type == OrganizationType.ROOT))
        assert root is not None
        organization = Organization(type=OrganizationType.FACTORY, code="FACTORY-ONE", name="Factory One", parent_id=root.id)
        db.add(organization)
        db.commit()
        organization_id = organization.id
    created = client.post("/api/users", headers=headers(token, "create-user"), json={
        "username": "operator", "password": "operator-password", "role_ids": [],
        "display_name": "Operator One", "gender": "MALE", "email": "operator@example.com",
        "phone": "+8613800000000", "remark": "night shift", "organization_id": organization_id,
    })
    assert created.status_code == 201
    user_id = created.json()["id"]
    assert created.json()["display_name"] == "Operator One"
    assert client.get(f"/api/users?organization_id={organization_id}", headers=headers(token)).json()[0]["id"] == user_id
    reset = client.post(f"/api/users/{user_id}/password-reset", headers=headers(token, "reset-password"), json={"new_password": "new-operator-password"})
    assert reset.status_code == 200
    assert client.post("/api/auth/login", json={"username": "operator", "password": "operator-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "operator", "password": "new-operator-password"}).status_code == 200
    login_events = client.get("/api/login-events?username=operator", headers=headers(token))
    audits = client.get("/api/audit-events?resource_type=user&page=1&page_size=20", headers=headers(token))
    assert login_events.status_code == audits.status_code == 200
    assert {"username", "display_name", "logged_at", "result", "reason"} <= set(login_events.json()["items"][0])
    assert {"occurred_at", "actor_display_name", "module", "target_display_name", "summary"} <= set(audits.json()["items"][0])
    with client.app.state.session_factory() as db:
        assert db.scalar(select(User).where(User.id == user_id)) is not None
        assert db.scalar(select(AuditEvent).where(AuditEvent.action == "user.password_reset")) is not None
