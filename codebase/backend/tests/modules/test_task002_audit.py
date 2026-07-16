from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.audit.service import sanitize_audit_metadata
from app.modules.equipment.organization_router import router as organization_router
from app.modules.equipment.router import router as equipment_router
from app.modules.identity.admin_router import router as identity_admin_router
from app.modules.identity.router import router as identity_router
from tests.modules.support import create_user_token


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
    assert route_names[("/api/roles", "POST")] == "role.create"
    assert route_names[("/api/users", "POST")] == "user.create"
    assert route_names[("/api/organizations", "POST")] == "organization.create"
    assert route_names[("/api/organizations/{organization_id}", "PATCH")] == (
        "organization.update"
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


def test_validation_failure_returns_one_persisted_audit_id(
    client: TestClient,
) -> None:
    user_id, token = create_user_token(
        client,
        username="validation-writer",
        role_code="VALIDATION_WRITER",
        permission_codes=["equipment:write"],
    )

    response = client.post(
        "/api/equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "invalid-equipment",
        },
        json={"code": "EQ-X"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["fields"] == [
        {"field": "name", "type": "missing"}
    ]
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


def test_http_failure_returns_one_persisted_audit_id(client: TestClient) -> None:
    user_id, token = create_user_token(
        client,
        username="http-writer",
        role_code="HTTP_WRITER",
        permission_codes=["equipment:write"],
    )

    response = client.patch(
        "/api/equipment/missing-equipment",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "missing-equipment",
        },
        json={"name": "Missing", "organization_id": None, "status": "NORMAL"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EQUIPMENT_NOT_FOUND"
    event = event_from_response(client, response)
    assert event.actor_user_id == user_id
    assert event.action == "equipment.update"
    assert event.result == "failure"
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
        role_code="IDEMPOTENCY_WRITER",
        permission_codes=["equipment:write"],
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "reused-key",
    }
    first = client.post(
        "/api/equipment",
        headers=headers,
        json={"code": "EQ-FIRST", "name": "First"},
    )

    response = client.post(
        "/api/equipment",
        headers=headers,
        json={"code": "EQ-SECOND", "name": "Second"},
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
        role_code="DENIED_WRITER",
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
