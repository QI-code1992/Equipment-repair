import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.audit.service import sanitize_audit_metadata
from app.modules.equipment import router as equipment_router
from app.modules.equipment.models import Equipment
from app.modules.identity.models import RoleCode
from tests.modules.support import create_user_token, valid_equipment_body


def test_sensitive_key_variants_and_attachment_payload_are_redacted() -> None:
    value = sanitize_audit_metadata(
        {
            "password_confirmation": "secret-one",
            "password2": "secret-two",
            "cookies": "session=secret",
            "attachment_payload": {
                "filename": "manual.pdf",
                "content": "sensitive-body",
            },
        }
    )

    assert value == {
        "password_confirmation": "[REDACTED]",
        "password2": "[REDACTED]",
        "cookies": "[REDACTED]",
        "attachment_payload": {
            "filename": "manual.pdf",
            "content": "[REDACTED]",
        },
    }


def test_password_semantic_segments_and_attachment_payload_aliases_are_redacted() -> None:
    value = sanitize_audit_metadata(
        {
            "newPasswordConfirmation": "new-password-secret",
            "current_password_confirmation": "current-password-secret",
            "payload": [
                {
                    "attachment_payload": {
                        "filename": "manual.pdf",
                        "raw_content": "attachment-secret",
                        "nested": [{"binary_payload": "nested-attachment-secret"}],
                    }
                }
            ],
        }
    )

    assert value == {
        "newPasswordConfirmation": "[REDACTED]",
        "current_password_confirmation": "[REDACTED]",
        "payload": [
            {
                "attachment_payload": {
                    "filename": "manual.pdf",
                    "raw_content": "[REDACTED]",
                    "nested": "[REDACTED]",
                }
            }
        ],
    }


def failure_events(client: TestClient) -> list[AuditEvent]:
    with client.app.state.session_factory() as db:
        return list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.action == "equipment.create",
                    AuditEvent.result == "failure",
                )
            )
        )


def equipment_writer(client: TestClient) -> tuple[str, dict[str, object]]:
    _, token = create_user_token(
        client,
        username="exception-writer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["equipment:write"],
    )
    return token, valid_equipment_body(client, code="EQ-EXCEPTION")


def request_headers(token: str, key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key,
    }


def test_success_audit_sql_error_rolls_back_and_writes_independent_failure_audit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token, body = equipment_writer(client)

    def fail_success_audit(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise SQLAlchemyError("secret database detail")

    monkeypatch.setattr(equipment_router, "write_audit_event", fail_success_audit)
    response = client.post(
        "/api/equipment",
        headers=request_headers(token, "audit-sql-error"),
        json=body,
    )

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["detail"]["audit_event_id"]
    assert "secret database detail" not in response.text
    events = failure_events(client)
    assert len(events) == 1
    with client.app.state.session_factory() as db:
        assert db.scalar(select(Equipment).where(Equipment.code == body["code"])) is None


def test_business_commit_sql_error_uses_same_failure_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token, body = equipment_writer(client)
    real_commit = Session.commit
    commit_calls = 0

    def fail_first_commit(session: Session) -> None:
        nonlocal commit_calls
        commit_calls += 1
        if commit_calls == 1:
            raise SQLAlchemyError("secret commit detail")
        real_commit(session)

    monkeypatch.setattr(Session, "commit", fail_first_commit)
    response = client.post(
        "/api/equipment",
        headers=request_headers(token, "business-commit-error"),
        json=body,
    )

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["detail"]["audit_event_id"]
    assert "secret commit detail" not in response.text
    assert len(failure_events(client)) == 1


def test_unexpected_runtime_error_is_safely_audited(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token, body = equipment_writer(client)

    def fail_create(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("Bearer secret-runtime-detail")

    monkeypatch.setattr(equipment_router.service, "create_equipment", fail_create)
    safe_client = TestClient(client.app, raise_server_exceptions=False)
    response = safe_client.post(
        "/api/equipment",
        headers=request_headers(token, "runtime-error"),
        json=body,
    )

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["detail"]["audit_event_id"]
    assert "secret-runtime-detail" not in response.text
    assert len(failure_events(client)) == 1
