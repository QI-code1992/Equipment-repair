import json

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.modules.audit.http as audit_http
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import sanitize_audit_metadata
from app.modules.equipment.organization_router import router as organization_router
from app.modules.equipment.router import router as equipment_router
from app.modules.identity.admin_router import router as identity_admin_router
from app.modules.identity.models import RoleCode
from app.modules.identity.router import router as identity_router
from tests.modules.support import create_user_token, valid_equipment_body


def event_from_response(client: TestClient, response: Response) -> AuditEvent:
    event_id = response.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        event = db.get(AuditEvent, event_id)
    assert event is not None
    return event


def failure_events(
    client: TestClient, *, actor_user_id: str, action: str
) -> list[AuditEvent]:
    with client.app.state.session_factory() as db:
        return list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_user_id == actor_user_id,
                    AuditEvent.action == action,
                    AuditEvent.result == "failure",
                )
            )
        )


def test_protected_write_routes_use_resource_action_names() -> None:
    route_names = {
        (route.path, method): route.name
        for router in (
            identity_router,
            identity_admin_router,
            organization_router,
            equipment_router,
        )
        for route in router.routes
        for method in getattr(route, "methods", set())
    }

    assert route_names[("/api/auth/session", "DELETE")] == "session.logout"
    assert route_names[("/api/users", "POST")] == "user.create"
    assert route_names[("/api/users/{user_id}", "PATCH")] == "user.update"
    assert route_names[("/api/roles/{role_id}/permissions", "PATCH")] == (
        "role.permissions.update"
    )
    assert route_names[("/api/organizations", "POST")] == "organization.create"
    assert route_names[("/api/organizations/{organization_id}", "PATCH")] == (
        "organization.update"
    )
    assert route_names[("/api/organizations/{organization_id}", "DELETE")] == (
        "organization.delete"
    )
    assert route_names[("/api/equipment", "POST")] == "equipment.create"
    assert route_names[("/api/equipment/{equipment_id}", "PATCH")] == (
        "equipment.update"
    )


def test_attachment_content_is_redacted_without_removing_metadata() -> None:
    value = sanitize_audit_metadata(
        {
            "attachment": {"filename": "manual.pdf", "content": "secret-body"},
            "content": "ordinary-business-content",
            "content_base64": "c2VjcmV0",
        }
    )

    assert value["attachment"] == {
        "filename": "manual.pdf",
        "content": "[REDACTED]",
    }
    assert value["content"] == "ordinary-business-content"
    assert value["content_base64"] == "[REDACTED]"


def test_attachment_redaction_handles_arrays_and_normalized_keys() -> None:
    value = sanitize_audit_metadata(
        {
            "Files": [
                {
                    "filename": "one.txt",
                    "Content": "first-secret",
                    "authorization": "Bearer file-token",
                },
                {"filename": "two.txt", "base64": "second-secret"},
            ],
            "file-content": "direct-secret",
            "content": "ordinary-content",
        }
    )

    assert value == {
        "Files": [
            {
                "filename": "one.txt",
                "Content": "[REDACTED]",
                "authorization": "[REDACTED]",
            },
            {"filename": "two.txt", "base64": "[REDACTED]"},
        ],
        "file-content": "[REDACTED]",
        "content": "ordinary-content",
    }


def test_validation_failure_returns_one_persisted_audit_id(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="validation-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "invalid-equipment",
        },
        json={
            "code": "EQ-X",
            "attachment": {"filename": "manual.pdf", "content": "secret-body"},
            "password": "plain-password",
            "authorization": "Bearer request-token",
            "content": "ordinary-business-content",
        },
    )

    assert response.status_code == 422
    fields = response.json()["detail"]["fields"]
    assert set(fields) == {
        "name", "model", "type", "manufacturer", "operating_hours", "status",
        "organization_id", "attachment", "password", "authorization", "content",
    }
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "equipment.create"
    assert event.result == "failure"
    assert event.metadata_json["request"] == {
        "code": "EQ-X",
        "attachment": {"filename": "manual.pdf", "content": "[REDACTED]"},
        "password": "[REDACTED]",
        "authorization": "[REDACTED]",
        "content": "ordinary-business-content",
    }
    assert [
        item.id
        for item in failure_events(
            client, actor_user_id=user_id, action="equipment.create"
        )
    ] == [event.id]


def test_validation_failure_redacts_password_and_attachment_aliases_in_database(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username="audit-alias-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    secrets = [
        "new-password-secret",
        "current-password-secret",
        "attachment-secret",
        "nested-attachment-secret",
    ]

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "invalid-equipment-audit-aliases",
        },
        json={
            "code": "EQ-AUDIT-ALIASES",
            "newPasswordConfirmation": secrets[0],
            "current_password_confirmation": secrets[1],
            "attachment_payload": {
                "filename": "manual.pdf",
                "raw_content": secrets[2],
                "nested": [{"binary_payload": secrets[3]}],
            },
        },
    )

    assert response.status_code == 422
    event = event_from_response(client, response)
    rendered = json.dumps(event.metadata_json)
    for secret in secrets:
        assert secret not in rendered
    assert event.metadata_json["request"]["newPasswordConfirmation"] == "[REDACTED]"
    assert event.metadata_json["request"]["current_password_confirmation"] == "[REDACTED]"
    assert event.metadata_json["request"]["attachment_payload"] == {
        "filename": "manual.pdf",
        "raw_content": "[REDACTED]",
        "nested": "[REDACTED]",
    }


def test_validation_failure_redacts_attachment_scalars_and_compact_passwords_in_database(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username="audit-scalar-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    secrets = [
        "password-secret",
        "user-password-secret",
        "scalar-secret",
        "list-secret",
        "upload-secret",
        "nested-secret",
        "mixed-list-secret",
    ]

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "invalid-equipment-audit-scalars",
        },
        json={
            "code": "EQ-AUDIT-SCALARS",
            "newpassword": secrets[0],
            "userpassword": secrets[1],
            "attachment_payload": secrets[2],
            "attachments": [secrets[3]],
            "uploadData": secrets[4],
            "attachment_payload_mixed": [
                {"filename": "manual.pdf", "raw_content": secrets[5]},
                secrets[6],
            ],
        },
    )

    assert response.status_code == 422
    event = event_from_response(client, response)
    rendered = json.dumps(event.metadata_json)
    for secret in secrets:
        assert secret not in rendered
    assert event.metadata_json["request"] == {
        "code": "EQ-AUDIT-SCALARS",
        "newpassword": "[REDACTED]",
        "userpassword": "[REDACTED]",
        "attachment_payload": "[REDACTED]",
        "attachments": "[REDACTED]",
        "uploadData": "[REDACTED]",
        "attachment_payload_mixed": [
            {"filename": "manual.pdf", "raw_content": "[REDACTED]"},
            "[REDACTED]",
        ],
    }


def test_logout_validation_failure_recovers_actor_from_bearer(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="logout-validation-user",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=[],
    )

    revoked = client.delete(
        "/api/auth/session",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "revoke-before-validation",
        },
    )
    response = client.delete(
        "/api/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert revoked.status_code == 200
    assert response.status_code == 422
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "session.logout"


def test_invalid_json_body_is_not_stored_in_failure_audit(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username="invalid-json-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "invalid-json",
            "Content-Type": "application/json",
        },
        content='{"password":"raw-secret"',
    )

    assert response.status_code == 422
    event = event_from_response(client, response)
    assert "request" not in event.metadata_json
    assert "raw-secret" not in json.dumps(event.metadata_json)


def test_logout_idempotency_failure_recovers_actor_from_bearer(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="logout-idempotency-user",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "cross-route-key",
    }
    created = client.post(
        "/api/equipment",
        headers=headers,
        json=valid_equipment_body(client, code="EQ-LOGOUT", name="Logout"),
    )

    response = client.delete("/api/auth/session", headers=headers)

    assert created.status_code == 201
    assert response.status_code == 409
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "session.logout"


def test_http_failure_returns_one_persisted_audit_id(client: TestClient) -> None:
    user_id, token = create_user_token(
        client,
        username="http-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )

    response = client.patch(
        "/api/equipment/missing-equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "missing-equipment",
        },
        json=valid_equipment_body(client, code="EQ-MISSING", name="Missing"),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EQUIPMENT_NOT_FOUND"
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "equipment.update"
    assert event.result == "failure"
    assert event.metadata_json["request"]["code"] == "EQ-MISSING"
    assert event.metadata_json["request"]["name"] == "Missing"
    assert [
        item.id
        for item in failure_events(
            client, actor_user_id=user_id, action="equipment.update"
        )
    ] == [event.id]


def test_idempotency_failure_returns_one_persisted_audit_id(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="idempotency-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "reused-key",
    }
    first = client.post(
        "/api/equipment",
        headers=headers,
        json=valid_equipment_body(client, code="EQ-FIRST", name="First"),
    )

    response = client.post(
        "/api/equipment",
        headers=headers,
        json=valid_equipment_body(client, code="EQ-SECOND", name="Second"),
    )

    assert first.status_code == 201
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "equipment.create"
    assert event.result == "failure"
    assert [
        item.id
        for item in failure_events(
            client, actor_user_id=user_id, action="equipment.create"
        )
    ] == [event.id]


def test_permission_denial_reuses_its_existing_audit_event(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="denied-writer",
        role_code=RoleCode.REPAIR_WORKER.value,
        permission_codes=[],
    )

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "denied-equipment",
        },
        json={"code": "EQ-DENIED", "name": "Denied"},
    )

    assert response.status_code == 403
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "permission.denied"
    assert event.result == "denied"
    with client.app.state.session_factory() as db:
        events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.actor_user_id == user_id,
                AuditEvent.action.in_(["permission.denied", "equipment.create"]),
            )
        ).all()
    assert [item.id for item in events] == [event.id]


@pytest.mark.parametrize("failure_point", ["flush", "commit"])
def test_audit_persistence_error_rolls_back_and_returns_safe_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure_point: str,
) -> None:
    _, token = create_user_token(
        client,
        username=f"audit-failure-{failure_point}",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    rollback_calls = 0
    real_rollback = Session.rollback

    def recording_rollback(session: Session) -> None:
        nonlocal rollback_calls
        rollback_calls += 1
        real_rollback(session)

    def fail_write(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise SQLAlchemyError("SELECT password FROM credentials")

    def fail_commit(session: Session) -> None:
        del session
        raise SQLAlchemyError("SELECT password FROM credentials")

    monkeypatch.setattr(Session, "rollback", recording_rollback)
    if failure_point == "flush":
        monkeypatch.setattr(audit_http, "write_audit_event", fail_write)
    else:
        monkeypatch.setattr(Session, "commit", fail_commit)

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": f"audit-failure-{failure_point}",
        },
        json={"code": "EQ-AUDIT-FAILURE"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "AUDIT_PERSIST_FAILED",
            "message": "AUDIT_PERSIST_FAILED",
            "fields": {},
        }
    }
    assert rollback_calls == 2
    assert caplog.messages == ["Failed to persist audit event"]
    assert "SELECT" not in caplog.text
    assert "password" not in caplog.text


def test_audit_rollback_error_is_logged_without_sensitive_detail(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _, token = create_user_token(
        client,
        username="audit-rollback-failure",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )

    def fail_write(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise SQLAlchemyError("SELECT password FROM credentials")

    def fail_rollback(session: Session) -> None:
        del session
        raise SQLAlchemyError("Bearer rollback-secret")

    monkeypatch.setattr(audit_http, "write_audit_event", fail_write)
    monkeypatch.setattr(Session, "rollback", fail_rollback)

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "audit-rollback-failure",
        },
        json={"code": "EQ-AUDIT-ROLLBACK"},
    )

    assert response.status_code == 503
    assert caplog.messages == [
        "Unhandled database request failure",
        "Failed to roll back audit transaction",
        "Failed to persist audit event",
    ]
    assert "rollback-secret" not in caplog.text
