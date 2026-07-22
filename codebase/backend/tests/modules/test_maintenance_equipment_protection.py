from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment
from tests.modules.maintenance_support import (
    auth_headers,
    create_equipment,
    create_fault,
    start_repair,
)
from tests.modules.support import create_user_token


def _equipment_writer(client: TestClient) -> str:
    _, token = create_user_token(
        client,
        username=f"equipment-writer-{uuid4().hex[:8]}",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["equipment:read", "equipment:write"],
    )
    return token


def _equipment_write_body(
    client: TestClient, equipment_id: str, token: str
) -> dict[str, object]:
    response = client.get(
        f"/api/equipment/{equipment_id}", headers=auth_headers(token)
    )
    assert response.status_code == 200
    return {
        key: value
        for key, value in response.json().items()
        if key not in {"id", "created_at", "updated_at"}
    }


@pytest.mark.parametrize("start_active_repair", [False, True])
def test_active_fault_blocks_equipment_disable_but_not_other_updates(
    client: TestClient, start_active_repair: bool
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    if start_active_repair:
        start_repair(client, fault_id)
    token = _equipment_writer(client)
    payload = _equipment_write_body(client, equipment_id, token)
    prior_status = "REPAIRING" if start_active_repair else "FAULT"

    disabled = client.patch(
        f"/api/equipment/{equipment_id}",
        headers=auth_headers(token, key=f"disable-active-{start_active_repair}"),
        json={**payload, "status": "DISABLED"},
    )

    assert disabled.status_code == 409
    assert disabled.json()["detail"]["code"] == "EQUIPMENT_ACTIVE_FAULT"
    assert disabled.json()["detail"]["fields"] == {"status": "active_fault"}
    audit_event_id = disabled.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        equipment = db.get(Equipment, equipment_id)
        event = db.get(AuditEvent, audit_event_id)
        assert equipment is not None and equipment.status.value == prior_status
        assert event is not None and event.result == "failure"
        assert event.action == "equipment.update"

    allowed = client.patch(
        f"/api/equipment/{equipment_id}",
        headers=auth_headers(token, key=f"update-active-{start_active_repair}"),
        json={**payload, "name": "Updated while active", "status": prior_status},
    )

    assert allowed.status_code == 200
    assert allowed.json()["name"] == "Updated while active"
    assert allowed.json()["status"] == prior_status


def test_equipment_disable_is_allowed_after_all_faults_are_processed(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    work_order_id, repair_token = start_repair(client, fault_id)
    completed = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(repair_token, key="complete-before-disable"),
        json={
            "actual_cause": "seal failure",
            "actual_solution": "replace seal",
            "repair_result": "pressure restored",
            "parts_replacement_notes": "seal kit installed",
        },
    )
    assert completed.status_code == 200
    token = _equipment_writer(client)
    payload = _equipment_write_body(client, equipment_id, token)

    disabled = client.patch(
        f"/api/equipment/{equipment_id}",
        headers=auth_headers(token, key="disable-after-processed"),
        json={**payload, "status": "DISABLED"},
    )

    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"
