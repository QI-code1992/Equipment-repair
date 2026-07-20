from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, inspect, select

from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, EquipmentStatus
from app.modules.maintenance.models import (
    DiagnosisDraft,
    DiagnosisDraftStatus,
    FaultReport,
    FaultStatus,
    MaintenanceRecord,
    RepairStartMode,
    WorkOrder,
    WorkOrderStatus,
)
from app.modules.maintenance.schemas import (
    FaultReportCreate,
    RepairResultRequest,
    StartRepairRequest,
)
from tests.modules.maintenance_support import (
    auth_headers,
    create_diagnosis_draft,
    create_equipment,
    create_fault,
    fault_reporter,
    repairer,
    valid_fault_body,
)
from tests.modules.support import create_user_token


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


def test_fault_report_schema_requires_timezone_aware_occurrence() -> None:
    with pytest.raises(ValidationError) as captured:
        FaultReportCreate.model_validate(
            {
                "equipment_id": "equipment-id",
                "urgency": "HIGH",
                "symptom": "hydraulic pressure loss",
                "occurred_at": "2026-07-20T08:00:00",
            }
        )

    assert captured.value.errors()[0]["type"] == "timezone_aware"


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

    with pytest.raises(ValidationError):
        StartRepairRequest.model_validate(
            {"mode": "DIRECT", "diagnosis_draft_id": str(uuid4())}
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


def test_create_fault_rejects_same_key_with_changed_request(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    body = valid_fault_body(equipment_id)
    headers = auth_headers(token, key="fault-changed-body")

    first = client.post("/api/fault-reports", headers=headers, json=body)
    changed = client.post(
        "/api/fault-reports",
        headers=headers,
        json={**body, "symptom": "changed symptom"},
    )

    assert first.status_code == 201
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert changed.json()["detail"]["fields"] == {
        "idempotency_key": "conflict"
    }
    assert changed.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 1
        assert db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.action == "fault_report.create",
                AuditEvent.result == "failure",
            )
        ) == 1


def test_maintenance_write_endpoints_require_their_permissions(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username=f"maintenance-denied-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=["equipment:read"],
    )
    denied_requests = [
        client.post(
            "/api/fault-reports",
            headers=auth_headers(token, key="denied-fault"),
            json=valid_fault_body(str(uuid4())),
        ),
        client.post(
            f"/api/fault-reports/{uuid4()}/start-repair",
            headers=auth_headers(token, key="denied-start"),
            json={"mode": "DIRECT"},
        ),
        client.post(
            f"/api/work-orders/{uuid4()}/repair-result",
            headers=auth_headers(token, key="denied-complete"),
            json={
                "actual_cause": "cause",
                "actual_solution": "solution",
                "repair_result": "result",
            },
        ),
    ]

    assert [response.status_code for response in denied_requests] == [403, 403, 403]
    assert all(
        response.json()["detail"]["code"] == "PERMISSION_DENIED"
        for response in denied_requests
    )


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


def test_start_repair_direct_is_idempotent_and_creates_one_work_order(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    repairer_id, token = repairer(client)
    path = f"/api/fault-reports/{fault_id}/start-repair"
    headers = auth_headers(token, key="direct-start-1")

    first = client.post(path, headers=headers, json={"mode": "DIRECT"})
    replay = client.post(path, headers=headers, json={"mode": "DIRECT"})

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert first.json()["fault_status"] == "IN_REPAIR"
    assert first.json()["work_order_status"] == "IN_REPAIR"
    assert first.json()["start_mode"] == "DIRECT"
    assert first.json()["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(WorkOrder)) == 1
        assert db.scalar(select(func.count()).select_from(MaintenanceRecord)) == 1
        fault = db.get(FaultReport, fault_id)
        equipment = db.get(Equipment, equipment_id)
        work_order = db.scalar(
            select(WorkOrder).where(WorkOrder.fault_report_id == fault_id)
        )
        assert fault is not None and fault.status is FaultStatus.IN_REPAIR
        assert equipment is not None and equipment.status is EquipmentStatus.REPAIRING
        assert work_order is not None
        assert work_order.status is WorkOrderStatus.IN_REPAIR
        assert work_order.repairer_user_id == repairer_id
        record = db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.work_order_id == work_order.id
            )
        )
        assert record is not None
        assert record.start_mode is RepairStartMode.DIRECT
        assert record.diagnosis_draft_id is None
        assert record.diagnosis_prefill is None
        assert record.ai_summary is None
        assert db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "repair.start")
        ) == 1


def test_start_repair_direct_rejects_missing_fault_and_repeated_transition(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    _, token = repairer(client)

    missing = client.post(
        f"/api/fault-reports/{uuid4()}/start-repair",
        headers=auth_headers(token, key="direct-missing-1"),
        json={"mode": "DIRECT"},
    )
    first = client.post(
        f"/api/fault-reports/{fault_id}/start-repair",
        headers=auth_headers(token, key="direct-start-2"),
        json={"mode": "DIRECT"},
    )
    repeated = client.post(
        f"/api/fault-reports/{fault_id}/start-repair",
        headers=auth_headers(token, key="direct-start-new-key"),
        json={"mode": "DIRECT"},
    )

    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "FAULT_REPORT_NOT_FOUND"
    assert missing.json()["detail"]["audit_event_id"]
    assert first.status_code == 200
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "FAULT_STATE_CONFLICT"
    assert repeated.json()["detail"]["fields"] == {"status": "IN_REPAIR"}
    assert repeated.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(WorkOrder)) == 1
        assert db.scalar(select(func.count()).select_from(MaintenanceRecord)) == 1


def test_start_repair_adopted_copies_only_approved_fields_once(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    draft_id = create_diagnosis_draft(client, fault_id)
    _, token = repairer(client)
    path = f"/api/fault-reports/{fault_id}/start-repair"
    body = {"mode": "ADOPTED", "diagnosis_draft_id": draft_id}

    response = client.post(
        path,
        headers=auth_headers(token, key="adopted-start-1"),
        json=body,
    )
    replay = client.post(
        path,
        headers=auth_headers(token, key="adopted-start-1"),
        json=body,
    )

    assert response.status_code == 200
    assert replay.json() == response.json()
    assert response.json()["start_mode"] == "ADOPTED"
    assert response.json()["diagnosis_draft_id"] == draft_id
    with client.app.state.session_factory() as db:
        draft = db.get(DiagnosisDraft, draft_id)
        record = db.scalar(select(MaintenanceRecord))
        assert draft is not None and draft.adopted_at is not None
        assert record is not None
        assert record.diagnosis_prefill == {
            "fault_type": "hydraulic",
            "actual_cause": "suspected seal wear",
            "actual_solution": "inspect and replace seal",
            "parts_replacement_notes": "prepare seal kit",
        }
        assert record.ai_summary == {
            "symptom": "pressure loss",
            "key_evidence": ["pressure drops under load"],
            "verification_results": ["leak observed"],
            "root_cause": "seal wear",
            "recommendations": ["replace seal", "retest pressure"],
        }
        serialized = f"{record.diagnosis_prefill!r}{record.ai_summary!r}"
        assert "secret" not in serialized
        assert "raw_chain_of_thought" not in serialized
        assert "attachment_content" not in serialized


def test_start_repair_adopted_rejects_invalid_draft_state_and_ownership(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    other_fault_id = create_fault(client, equipment_id)
    draft_not_ready = create_diagnosis_draft(
        client, fault_id, status=DiagnosisDraftStatus.DRAFT
    )
    wrong_fault_draft = create_diagnosis_draft(client, other_fault_id)
    adopted_draft = create_diagnosis_draft(client, fault_id, adopted=True)
    _, token = repairer(client)
    path = f"/api/fault-reports/{fault_id}/start-repair"

    cases = [
        (str(uuid4()), "DIAGNOSIS_DRAFT_NOT_FOUND"),
        (wrong_fault_draft, "DIAGNOSIS_DRAFT_FAULT_MISMATCH"),
        (draft_not_ready, "DIAGNOSIS_DRAFT_NOT_READY"),
        (adopted_draft, "DIAGNOSIS_DRAFT_ALREADY_ADOPTED"),
    ]
    for index, (draft_id, code) in enumerate(cases):
        response = client.post(
            path,
            headers=auth_headers(token, key=f"invalid-adopt-{index}"),
            json={"mode": "ADOPTED", "diagnosis_draft_id": draft_id},
        )
        assert response.status_code in {404, 409}
        assert response.json()["detail"]["code"] == code
        assert response.json()["detail"]["audit_event_id"]

    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(WorkOrder)) == 0
        assert db.scalar(select(func.count()).select_from(MaintenanceRecord)) == 0


def test_start_repair_adopted_drops_untyped_nested_values(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    draft_id = create_diagnosis_draft(client, fault_id)
    with client.app.state.session_factory() as db:
        draft = db.get(DiagnosisDraft, draft_id)
        assert draft is not None
        draft.allowed_prefill = {
            "actual_cause": {"password": "prefill-secret"},
            "actual_solution": "replace seal",
        }
        draft.read_only_summary = {
            "symptom": "pressure loss",
            "key_evidence": [
                "pressure drop",
                {"token": "summary-secret"},
            ],
            "root_cause": {"secret": "nested-secret"},
        }
        db.commit()

    _, token = repairer(client)
    response = client.post(
        f"/api/fault-reports/{fault_id}/start-repair",
        headers=auth_headers(token, key="adopted-untyped-values"),
        json={"mode": "ADOPTED", "diagnosis_draft_id": draft_id},
    )

    assert response.status_code == 200
    with client.app.state.session_factory() as db:
        record = db.scalar(select(MaintenanceRecord))
        assert record is not None
        assert record.diagnosis_prefill == {"actual_solution": "replace seal"}
        assert record.ai_summary == {
            "symptom": "pressure loss",
            "key_evidence": ["pressure drop"],
        }
        assert "secret" not in f"{record.diagnosis_prefill!r}{record.ai_summary!r}"
