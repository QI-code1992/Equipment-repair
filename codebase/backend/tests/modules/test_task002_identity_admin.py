from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.identity.models import Role, RoleCode


def seeded_system_admin(client: TestClient) -> tuple[str, str]:
    with client.app.state.session_factory() as db:
        user = bootstrap_admin(db, "system-admin", "system-password")
        user_id = user.id
    response = client.post(
        "/api/auth/login",
        json={"username": "system-admin", "password": "system-password"},
    )
    assert response.status_code == 200
    return user_id, response.json()["access_token"]


def admin_headers(token: str, key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key,
    }


def role_id(client: TestClient, code: RoleCode) -> str:
    with client.app.state.session_factory() as db:
        role = db.scalar(select(Role).where(Role.code == code.value))
        assert role is not None
        return role.id


def test_role_catalog_is_fixed_and_non_admin_permissions_are_editable(
    client: TestClient,
) -> None:
    _, token = seeded_system_admin(client)
    headers = admin_headers(token, "role-update")

    assert client.post(
        "/api/roles",
        headers=headers,
        json={"name": "custom", "permission_codes": []},
    ).status_code == 405
    roles = client.get("/api/roles", headers=headers).json()
    assert {role["code"] for role in roles} == {code.value for code in RoleCode}
    target = next(role for role in roles if role["code"] == RoleCode.EQUIPMENT_ADMIN)
    response = client.patch(
        f"/api/roles/{target['id']}/permissions",
        headers=headers,
        json={"permission_codes": ["equipment:read", "equipment:write"]},
    )

    assert response.status_code == 200
    assert response.json()["permission_codes"] == ["equipment:read", "equipment:write"]
    assert "audit_event_id" in response.json()


def test_system_admin_permissions_cannot_be_changed(client: TestClient) -> None:
    _, token = seeded_system_admin(client)

    response = client.patch(
        f"/api/roles/{role_id(client, RoleCode.SYSTEM_ADMIN)}/permissions",
        headers=admin_headers(token, "weaken-system-admin"),
        json={"permission_codes": ["identity:read"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SYSTEM_ADMIN_PERMISSIONS_FIXED"
    assert "audit_event_id" in response.json()["detail"]


def test_user_list_detail_create_and_update_hide_passwords(client: TestClient) -> None:
    admin_id, token = seeded_system_admin(client)
    equipment_admin_id = role_id(client, RoleCode.EQUIPMENT_ADMIN)
    created = client.post(
        "/api/users",
        headers=admin_headers(token, "create-user"),
        json={
            "username": "operator-admin",
            "password": "operator-password",
            "role_ids": [equipment_admin_id],
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    listed = client.get("/api/users", headers=admin_headers(token, "unused"))
    detailed = client.get(f"/api/users/{user_id}", headers=admin_headers(token, "unused"))
    updated = client.patch(
        f"/api/users/{user_id}",
        headers=admin_headers(token, "update-user"),
        json={"enabled": False, "role_ids": [equipment_admin_id]},
    )

    assert listed.status_code == detailed.status_code == updated.status_code == 200
    assert {item["id"] for item in listed.json()} == {admin_id, user_id}
    assert detailed.json()["username"] == "operator-admin"
    assert updated.json()["enabled"] is False
    assert updated.json()["role_ids"] == [equipment_admin_id]
    assert "audit_event_id" in created.json() and "audit_event_id" in updated.json()
    assert all("password" not in response.text for response in (created, listed, detailed, updated))

    with client.app.state.session_factory() as db:
        events = db.scalars(
            select(AuditEvent).where(AuditEvent.action.in_(["user.create", "user.update"]))
        ).all()
    assert len(events) == 2
    assert "operator-password" not in str([event.metadata_json for event in events])


def test_user_cannot_disable_self_or_last_system_admin(client: TestClient) -> None:
    user_id, token = seeded_system_admin(client)
    response = client.patch(
        f"/api/users/{user_id}",
        headers=admin_headers(token, "disable-self"),
        json={"enabled": False, "role_ids": [role_id(client, RoleCode.SYSTEM_ADMIN)]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "USER_SELF_DISABLE_FORBIDDEN"
    assert "audit_event_id" in response.json()["detail"]


def test_last_enabled_system_admin_role_cannot_be_removed(client: TestClient) -> None:
    admin_id, token = seeded_system_admin(client)

    response = client.patch(
        f"/api/users/{admin_id}",
        headers=admin_headers(token, "remove-last-admin"),
        json={
            "enabled": True,
            "role_ids": [role_id(client, RoleCode.EQUIPMENT_ADMIN)],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "LAST_SYSTEM_ADMIN_REQUIRED"


def test_unknown_roles_permissions_and_users_are_rejected(client: TestClient) -> None:
    _, token = seeded_system_admin(client)
    missing_role = client.post(
        "/api/users",
        headers=admin_headers(token, "missing-role"),
        json={"username": "new-user", "password": "new-password", "role_ids": ["missing"]},
    )
    missing_permission = client.patch(
        f"/api/roles/{role_id(client, RoleCode.EQUIPMENT_ADMIN)}/permissions",
        headers=admin_headers(token, "missing-permission"),
        json={"permission_codes": ["missing:permission"]},
    )
    missing_user = client.get(
        "/api/users/missing",
        headers=admin_headers(token, "unused"),
    )

    assert missing_role.status_code == 422
    assert missing_role.json()["detail"]["code"] == "ROLE_NOT_FOUND"
    assert missing_permission.status_code == 422
    assert missing_permission.json()["detail"]["code"] == "PERMISSION_NOT_FOUND"
    assert missing_user.status_code == 404
    assert missing_user.json()["detail"]["code"] == "USER_NOT_FOUND"


def test_unknown_write_field_is_audited_once(client: TestClient) -> None:
    admin_id, token = seeded_system_admin(client)
    response = client.patch(
        f"/api/users/{admin_id}",
        headers=admin_headers(token, "unknown-field"),
        json={
            "enabled": True,
            "role_ids": [role_id(client, RoleCode.SYSTEM_ADMIN)],
            "unexpected": "value",
        },
    )

    assert response.status_code == 422
    event_id = response.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "user.update",
                AuditEvent.result == "failure",
            )
        ).all()
    assert [event.id for event in events] == [event_id]
