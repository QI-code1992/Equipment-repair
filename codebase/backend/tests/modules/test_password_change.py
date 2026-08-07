from sqlalchemy import select
from fastapi.testclient import TestClient

from app.modules.audit.models import AuditEvent
from app.modules.identity.models import LoginSession
from tests.modules.support import build_client, create_user_token


def test_password_change_updates_hash_revokes_all_sessions_and_requires_new_login() -> None:
    client = build_client()
    user_id, token = create_user_token(client, username="password-owner", role_code="REPAIR_WORKER", permission_codes=[])
    second_login = client.post("/api/auth/login", json={"username": "password-owner", "password": "correct-password"})
    assert second_login.status_code == 200
    response = client.patch(
        "/api/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "correct-password", "new_password": "new-password-123", "confirm_password": "new-password-123"},
    )
    assert response.status_code == 200
    assert response.json()["audit_event_id"]
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "password-owner", "password": "correct-password"}).status_code == 401
    new_login = client.post("/api/auth/login", json={"username": "password-owner", "password": "new-password-123"})
    assert new_login.status_code == 200
    with client.app.state.session_factory() as db:
        sessions = db.scalars(select(LoginSession).where(LoginSession.user_id == user_id)).all()
        assert sum(session.revoked_at is not None for session in sessions) >= 2
        event = db.scalar(select(AuditEvent).where(AuditEvent.action == "password_change", AuditEvent.result == "success"))
        assert event is not None
        assert "password" not in str(event.metadata_json).lower()


def test_password_change_rejects_wrong_current_password_and_mismatched_confirmation() -> None:
    client = build_client()
    _, token = create_user_token(client, username="password-errors", role_code="REPAIR_WORKER", permission_codes=[])
    headers = {"Authorization": f"Bearer {token}"}
    wrong = client.patch("/api/auth/password", headers=headers, json={"current_password": "wrong-password", "new_password": "new-password-123", "confirm_password": "new-password-123"})
    assert wrong.status_code == 422
    assert wrong.json()["detail"]["code"] == "CURRENT_PASSWORD_INVALID"
    mismatch = client.patch("/api/auth/password", headers=headers, json={"current_password": "correct-password", "new_password": "new-password-123", "confirm_password": "different-password"})
    assert mismatch.status_code == 422
    assert mismatch.json()["detail"]["code"] == "PASSWORD_CONFIRMATION_MISMATCH"
