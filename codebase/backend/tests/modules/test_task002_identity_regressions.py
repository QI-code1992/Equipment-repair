import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.modules.identity.service as identity_service
from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment
from app.modules.identity.bootstrap import (
    PERMISSION_CODES,
    BootstrapAlreadyInitialized,
    bootstrap_admin,
    ensure_identity_catalog,
)
from app.modules.identity.models import RoleCode, User
from tests.modules.support import valid_equipment_body
from tests.modules.test_identity_permissions import (
    client,
    create_user_token,
    organization_payload,
    root_id,
    writer_headers,
)


def test_bootstrap_creates_only_first_administrator(client: TestClient) -> None:
    with client.app.state.session_factory() as session:
        administrator = bootstrap_admin(session, "first-admin", "bootstrap-password")
        permission_codes = {
            permission.code
            for role in administrator.roles
            for permission in role.permissions
        }
        assert permission_codes >= {
            "identity:write",
            "equipment:read",
            "organization:write",
        }
        with pytest.raises(BootstrapAlreadyInitialized):
            bootstrap_admin(session, "second-admin", "another-password")
        events = session.scalars(
            select(AuditEvent).where(AuditEvent.action == "user.bootstrap")
        ).all()
        assert len(events) == 1
        assert events[0].actor_user_id is None
        assert events[0].resource_id == administrator.id

    response = client.post(
        "/api/auth/login",
        json={"username": "first-admin", "password": "bootstrap-password"},
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("username", "password"),
    [("", "bootstrap-password"), ("first-admin", "")],
)
def test_bootstrap_rejects_blank_credentials(
    client: TestClient, username: str, password: str
) -> None:
    with client.app.state.session_factory() as session:
        with pytest.raises(ValueError, match="must not be blank"):
            bootstrap_admin(session, username, password)


def test_identity_reader_can_query_permissions_and_roles(client: TestClient) -> None:
    token = create_user_token(client, ["identity:read"])
    with client.app.state.session_factory() as session:
        ensure_identity_catalog(session)
        session.commit()
    headers = {"Authorization": f"Bearer {token}"}

    permissions = client.get("/api/permissions", headers=headers)
    roles = client.get("/api/roles", headers=headers)

    assert permissions.status_code == 200
    assert {item["code"] for item in permissions.json()} == set(PERMISSION_CODES)
    assert roles.status_code == 200
    assert {item["code"] for item in roles.json()} == {code.value for code in RoleCode}


def test_equipment_and_organization_can_be_updated(client: TestClient) -> None:
    headers = writer_headers(client, "create-org-for-update")
    organization = client.post(
        "/api/organizations",
        json=organization_payload(
            "FACTORY", "FAC-UPDATE", "Original Plant", root_id(client)
        ),
        headers=headers,
    ).json()
    create_headers = {**headers, "Idempotency-Key": "create-equipment-for-update"}
    payload = valid_equipment_body(client, code="EQ-UPDATE", name="Old Name")
    equipment = client.post(
        "/api/equipment", json=payload, headers=create_headers
    ).json()
    assert equipment["status"] == "NORMAL"

    updated_organization = client.patch(
        f"/api/organizations/{organization['id']}",
        json={
            "code": organization["code"],
            "name": "Updated Plant",
            "sort_order": organization["sort_order"],
            "enabled": organization["enabled"],
            "remark": organization["remark"],
        },
        headers={**headers, "Idempotency-Key": "update-org"},
    )
    updated_equipment = client.patch(
        f"/api/equipment/{equipment['id']}",
        json={**payload, "name": "New Name", "status": "REPAIRING"},
        headers={**headers, "Idempotency-Key": "update-equipment"},
    )

    assert updated_organization.status_code == 200
    assert updated_organization.json()["name"] == "Updated Plant"
    assert "audit_event_id" in updated_organization.json()
    assert updated_equipment.status_code == 200
    assert updated_equipment.json()["status"] == "REPAIRING"
    assert "audit_event_id" in updated_equipment.json()


def test_login_failure_and_permission_denial_are_audited(client: TestClient) -> None:
    token = create_user_token(client, [])
    invalid = client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
    )
    denied = client.get("/api/equipment", headers={"Authorization": f"Bearer {token}"})

    with client.app.state.session_factory() as session:
        events = session.scalars(
            select(AuditEvent).order_by(AuditEvent.created_at)
        ).all()

    assert invalid.status_code == 401
    assert denied.status_code == 403
    assert [(event.action, event.result) for event in events] == [
        ("login", "success"),
        ("login", "failed"),
        ("permission.denied", "denied"),
    ]


def test_unknown_user_still_runs_password_verification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    real_verify = identity_service.verify_password

    def counting_verify(password: str, encoded: str) -> bool:
        nonlocal calls
        calls += 1
        return real_verify(password, encoded)

    monkeypatch.setattr(identity_service, "verify_password", counting_verify)
    response = client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert calls == 1


def test_idempotency_key_cannot_be_reused_for_another_target(
    client: TestClient,
) -> None:
    headers = writer_headers(client, "global-key")
    organization = client.post(
        "/api/organizations",
        json=organization_payload("FACTORY", "FAC-GLOBAL", "Plant", root_id(client)),
        headers=headers,
    )
    equipment = client.post(
        "/api/equipment",
        json=valid_equipment_body(client, code="EQ-GLOBAL"),
        headers=headers,
    )

    assert organization.status_code == 201
    assert equipment.status_code == 409
    assert equipment.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_idempotency_key_rejects_changed_request_body(client: TestClient) -> None:
    headers = writer_headers(client, "body-key")
    first = client.post(
        "/api/equipment",
        json=valid_equipment_body(client, code="EQ-BODY-A", name="A"),
        headers=headers,
    )
    second = client.post(
        "/api/equipment",
        json=valid_equipment_body(client, code="EQ-BODY-B", name="B"),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_equipment_unique_conflict_is_mapped_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = writer_headers(client, "database-conflict")
    real_flush = Session.flush

    def conflicting_flush(session: Session, objects: object = None) -> None:
        if any(isinstance(item, Equipment) for item in session.new):
            raise IntegrityError(
                "insert", {}, RuntimeError("UNIQUE constraint failed: equipment.code")
            )
        real_flush(session, objects)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.post(
        "/api/equipment",
        json=valid_equipment_body(client, code="EQ-RACE"),
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"


def test_identity_user_unique_conflict_is_mapped_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = create_user_token(client, ["identity:write"])
    with client.app.state.session_factory() as session:
        role = ensure_identity_catalog(session)[RoleCode.EQUIPMENT_ADMIN]
        session.commit()
        role_id = role.id

    real_flush = Session.flush

    def conflicting_flush(session: Session, objects: object = None) -> None:
        if any(isinstance(item, User) for item in session.new):
            raise IntegrityError("insert", {}, RuntimeError("unique conflict"))
        real_flush(session, objects)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.post(
        "/api/users",
        json={"username": "new-user", "password": "password", "role_ids": [role_id]},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "conflict-user",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "USERNAME_EXISTS"


def test_timestamp_columns_keep_utc_and_update_semantics() -> None:
    assert AuditEvent.__table__.c.created_at.type.timezone is True
    assert User.__table__.c.updated_at.onupdate is not None
