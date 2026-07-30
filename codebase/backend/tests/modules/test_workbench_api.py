from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.maintenance.models import FaultReport
from tests.modules.maintenance_support import (
    auth_headers,
    create_equipment,
    create_fault,
    repairer,
    start_repair,
)
from tests.modules.support import create_user_token


def _create_fault_with_urgency(
    client: TestClient, equipment_id: str, urgency: str
) -> str:
    fault_id = create_fault(client, equipment_id)
    with client.app.state.session_factory() as db:
        fault = db.get(FaultReport, fault_id)
        assert fault is not None
        fault.urgency = urgency
        db.commit()
    return fault_id


def _set_submitted_at(
    client: TestClient, fault_id: str, submitted_at: datetime
) -> None:
    with client.app.state.session_factory() as db:
        fault = db.get(FaultReport, fault_id)
        assert fault is not None
        fault.submitted_at = submitted_at
        db.commit()


def _workbench_token(client: TestClient, *permissions: str) -> str:
    _, token = create_user_token(
        client,
        username=f"workbench-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=list(permissions),
    )
    return token


def test_workbench_todos_returns_only_active_faults_with_server_filters(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    first = _create_fault_with_urgency(client, equipment_id, "LOW")
    second = _create_fault_with_urgency(client, equipment_id, "HIGH")
    repair_fault = _create_fault_with_urgency(client, equipment_id, "HIGH")
    work_order_id, repairer_token = start_repair(
        client, repair_fault, token=repairer(client)[1]
    )
    base = datetime(2026, 7, 30, tzinfo=UTC)
    _set_submitted_at(client, first, base)
    _set_submitted_at(client, second, base + timedelta(minutes=1))
    tied = _create_fault_with_urgency(client, equipment_id, "LOW")
    _set_submitted_at(client, tied, base)
    token = _workbench_token(client, "workbench:view")

    response = client.get(
        "/api/workbench/todos?status=PENDING_ACCEPT&limit=2",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [item["id"] for item in body["items"]] == [second, min(first, tied)]
    assert set(body["items"][0]) == {
        "id", "number", "equipment_id", "equipment_code", "equipment_name",
        "urgency", "symptom", "occurred_at", "submitted_at", "status",
    }
    assert "description" not in body["items"][0]

    filtered = client.get(
        "/api/workbench/todos?urgency=HIGH",
        headers=auth_headers(token),
    )
    assert filtered.status_code == 200
    assert filtered.json()["count"] == 2
    assert {item["status"] for item in filtered.json()["items"]} == {
        "PENDING_ACCEPT", "IN_REPAIR"
    }

    tied_items = client.get(
        "/api/workbench/todos?status=PENDING_ACCEPT&urgency=LOW",
        headers=auth_headers(token),
    ).json()["items"]
    assert [item["id"] for item in tied_items] == sorted([first, tied])

    completion = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(repairer_token, key="complete-workbench-active-boundary"),
        json={
            "actual_cause": "cause",
            "actual_solution": "solution",
            "repair_result": "completed",
        },
    )
    assert completion.status_code == 200
    active_high = client.get(
        "/api/workbench/todos?urgency=HIGH", headers=auth_headers(token)
    )
    assert active_high.status_code == 200
    assert active_high.json()["count"] == 1
    assert active_high.json()["items"][0]["id"] == second


def test_workbench_summary_empty_state_shortcuts_and_permission_boundary(
    client: TestClient,
) -> None:
    viewer_token = _workbench_token(client, "workbench:view")

    empty_todos = client.get("/api/workbench/todos", headers=auth_headers(viewer_token))
    empty_summary = client.get(
        "/api/workbench/alert-summary", headers=auth_headers(viewer_token)
    )
    no_shortcuts = client.get(
        "/api/workbench/shortcuts", headers=auth_headers(viewer_token)
    )

    assert empty_todos.status_code == 200
    assert empty_todos.json() == {"items": [], "count": 0}
    assert empty_summary.status_code == 200
    assert empty_summary.json() == {
        "active_fault_count": 0, "status_counts": [], "urgency_counts": []
    }
    assert no_shortcuts.status_code == 200
    assert no_shortcuts.json() == {"items": []}

    unauthenticated = client.get("/api/workbench/todos")
    invalid_status = client.get(
        "/api/workbench/todos?status=PROCESSED", headers=auth_headers(viewer_token)
    )
    invalid_limit = client.get(
        "/api/workbench/todos?limit=101", headers=auth_headers(viewer_token)
    )
    assert unauthenticated.status_code == 401
    assert invalid_status.status_code == 422
    assert invalid_limit.status_code == 422
    assert invalid_status.json()["detail"]["code"] == "VALIDATION_ERROR"
    assert invalid_limit.json()["detail"]["code"] == "VALIDATION_ERROR"

    reporter_token = _workbench_token(client, "workbench:view", "fault:create")
    reporter_shortcuts = client.get(
        "/api/workbench/shortcuts", headers=auth_headers(reporter_token)
    )
    assert reporter_shortcuts.status_code == 200
    assert reporter_shortcuts.json() == {
        "items": [{"id": "fault_report", "label": "故障上报", "path": "/fault-report"}]
    }

    denied_token = _workbench_token(client, "equipment:read")
    denied = client.get("/api/workbench/todos", headers=auth_headers(denied_token))
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "PERMISSION_DENIED"


def test_workbench_summary_uses_only_live_active_fault_facts(client: TestClient) -> None:
    equipment_id = create_equipment(client)
    _create_fault_with_urgency(client, equipment_id, "LOW")
    high_fault = _create_fault_with_urgency(client, equipment_id, "HIGH")
    start_repair(client, high_fault, token=repairer(client)[1])
    token = _workbench_token(client, "workbench:view")

    response = client.get(
        "/api/workbench/alert-summary", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "active_fault_count": 2,
        "status_counts": [
            {"status": "IN_REPAIR", "count": 1},
            {"status": "PENDING_ACCEPT", "count": 1},
        ],
        "urgency_counts": [
            {"urgency": "HIGH", "count": 1},
            {"urgency": "LOW", "count": 1},
        ],
    }
