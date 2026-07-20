from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, inspect, select

from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, EquipmentStatus
from app.modules.maintenance.models import (
    DiagnosisDraftStatus,
    FaultReport,
    FaultStatus,
    RepairStartMode,
    WorkOrderStatus,
)
from app.modules.maintenance.schemas import (
    FaultReportCreate,
    RepairResultRequest,
    StartRepairRequest,
)
from tests.modules.support import create_user_token, valid_equipment_body


def auth_headers(token: str, *, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def create_equipment(
    client: TestClient, *, status: str = "NORMAL"
) -> str:
    _, token = create_user_token(
        client,
        username=f"equipment-admin-{uuid4().hex[:8]}",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["equipment:write"],
    )
    body = valid_equipment_body(client, code=f"EQ-{uuid4().hex[:8]}")
    body["status"] = status
    response = client.post(
        "/api/equipment",
        headers=auth_headers(token, key=f"equipment-{uuid4()}"),
        json=body,
    )
    assert response.status_code == 201
    return response.json()["id"]


def fault_reporter(client: TestClient) -> tuple[str, str]:
    return create_user_token(
        client,
        username=f"fault-reporter-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=["fault:create"],
    )


def valid_fault_body(equipment_id: str) -> dict[str, object]:
    return {
        "equipment_id": equipment_id,
        "urgency": "HIGH",
        "symptom": "hydraulic pressure loss",
        "occurred_at": datetime.now(UTC).isoformat(),
        "possible_location": "main pump",
        "description": "pressure falls under load",
        "attachment_refs": [
            {
                "object_key": "faults/reference-1.jpg",
                "filename": "reference-1.jpg",
                "size_bytes": 1024,
                "content_type": "image/jpeg",
            }
        ],
    }


def test_maintenance_tables_exist(client: TestClient) -> None:
    names = set(inspect(client.app.state.engine).get_table_names())

    assert {
        "diagnosis_drafts",
        "fault_reports",
        "historical_repair_cases",
        "maintenance_records",
        "work_orders",
    } <= names


def test_maintenance_enum_values_are_frozen() -> None:
    assert [item.value for item in FaultStatus] == [
        "PENDING_ACCEPT",
        "IN_REPAIR",
        "PROCESSED",
    ]
    assert [item.value for item in WorkOrderStatus] == [
        "DRAFT",
        "PENDING_ACCEPT",
        "IN_REPAIR",
        "PENDING_INSPECTION",
        "COMPLETED",
    ]
    assert [item.value for item in RepairStartMode] == ["DIRECT", "ADOPTED"]
    assert [item.value for item in DiagnosisDraftStatus] == [
        "DRAFT",
        "DIAGNOSIS_READY",
    ]


def test_fault_report_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError) as captured:
        FaultReportCreate.model_validate(
            {
                "equipment_id": "equipment-id",
                "urgency": "HIGH",
                "symptom": "hydraulic pressure loss",
                "occurred_at": datetime.now(UTC),
                "binaryAttachment": "secret",
            }
        )

    assert captured.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("field", ["actual_cause", "actual_solution", "repair_result"])
def test_repair_result_requires_nonblank_final_fields(field: str) -> None:
    payload = {
        "actual_cause": "seal failure",
        "actual_solution": "replace seal",
        "repair_result": "pressure restored",
    }
    payload[field] = "   "

    with pytest.raises(ValidationError):
        RepairResultRequest.model_validate(payload)


def test_start_repair_mode_controls_diagnosis_reference() -> None:
    direct = StartRepairRequest.model_validate({"mode": "DIRECT"})
    assert direct.diagnosis_draft_id is None

    with pytest.raises(ValidationError):
        StartRepairRequest.model_validate(
            {"mode": "ADOPTED", "diagnosis_draft_id": None}
        )


def test_create_fault_is_idempotent_and_sets_equipment_fault(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    reporter_id, token = fault_reporter(client)
    body = valid_fault_body(equipment_id)
    headers = auth_headers(token, key="fault-create-1")

    first = client.post("/api/fault-reports", headers=headers, json=body)
    replay = client.post("/api/fault-reports", headers=headers, json=body)

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert first.json()["status"] == "PENDING_ACCEPT"
    assert first.json()["submitter_id"] == reporter_id
    assert first.json()["organization_snapshot"]["line"]["id"]
    assert first.json()["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 1
        equipment = db.get(Equipment, equipment_id)
        assert equipment is not None
        assert equipment.status is EquipmentStatus.FAULT
        assert db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "fault_report.create")
        ) == 1


def test_create_fault_rejects_future_occurrence_and_persists_failure_audit(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    body = valid_fault_body(equipment_id)
    body["occurred_at"] = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    response = client.post(
        "/api/fault-reports",
        headers=auth_headers(token, key="fault-future-1"),
        json=body,
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "FAULT_OCCURRENCE_IN_FUTURE"
    assert response.json()["detail"]["fields"] == {"occurred_at": "future"}
    assert response.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 0
        event = db.get(AuditEvent, response.json()["detail"]["audit_event_id"])
        assert event is not None
        assert event.result == "failure"
        assert event.action == "fault_report.create"


def test_create_fault_rejects_disabled_equipment(client: TestClient) -> None:
    equipment_id = create_equipment(client, status="DISABLED")
    _, token = fault_reporter(client)

    response = client.post(
        "/api/fault-reports",
        headers=auth_headers(token, key="fault-disabled-1"),
        json=valid_fault_body(equipment_id),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "FAULT_EQUIPMENT_DISABLED"
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 0
