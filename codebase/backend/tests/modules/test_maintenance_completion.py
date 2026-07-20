from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, EquipmentStatus
from app.modules.maintenance.models import (
    FaultReport,
    FaultStatus,
    HistoricalRepairCase,
    MaintenanceRecord,
    WorkOrder,
    WorkOrderStatus,
)
from tests.modules.maintenance_support import (
    auth_headers,
    create_diagnosis_draft,
    create_equipment,
    create_fault,
    repairer,
    start_repair,
)


def repair_result_body() -> dict[str, str]:
    return {
        "actual_cause": "confirmed pump seal failure",
        "actual_solution": "replaced pump seal and flushed circuit",
        "repair_result": "pressure restored under load",
        "parts_replacement_notes": "seal kit SK-42 installed",
    }


def test_repair_result_is_idempotent_and_creates_one_structured_case(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    work_order_id, token = start_repair(client, fault_id)
    path = f"/api/work-orders/{work_order_id}/repair-result"
    headers = auth_headers(token, key="repair-result-1")

    first = client.post(path, headers=headers, json=repair_result_body())
    replay = client.post(path, headers=headers, json=repair_result_body())

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert first.json()["work_order_status"] == "COMPLETED"
    assert first.json()["fault_status"] == "PROCESSED"
    assert first.json()["historical_case_id"]
    assert first.json()["audit_event_id"]
    with client.app.state.session_factory() as db:
        order = db.get(WorkOrder, work_order_id)
        fault = db.get(FaultReport, fault_id)
        equipment = db.get(Equipment, equipment_id)
        record = db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.work_order_id == work_order_id
            )
        )
        case = db.scalar(select(HistoricalRepairCase))
        assert order is not None and order.status is WorkOrderStatus.COMPLETED
        assert fault is not None and fault.status is FaultStatus.PROCESSED
        assert equipment is not None and equipment.status is EquipmentStatus.NORMAL
        assert record is not None and case is not None
        assert record.actual_cause == repair_result_body()["actual_cause"]
        assert record.actual_solution == repair_result_body()["actual_solution"]
        assert record.repair_result == repair_result_body()["repair_result"]
        assert case.actual_cause == repair_result_body()["actual_cause"]
        assert db.scalar(select(func.count()).select_from(HistoricalRepairCase)) == 1
        assert db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "repair.complete")
        ) == 1


def test_repair_result_overrides_adopted_prefill_and_keeps_other_fault_active(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    other_fault_id = create_fault(client, equipment_id)
    draft_id = create_diagnosis_draft(client, fault_id)
    _, token = repairer(client)
    work_order_id, _ = start_repair(
        client,
        fault_id,
        token=token,
        mode="ADOPTED",
        diagnosis_draft_id=draft_id,
    )

    response = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key="repair-result-adopted"),
        json=repair_result_body(),
    )

    assert response.status_code == 200
    with client.app.state.session_factory() as db:
        record = db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.work_order_id == work_order_id
            )
        )
        equipment = db.get(Equipment, equipment_id)
        other_fault = db.get(FaultReport, other_fault_id)
        assert record is not None
        assert record.actual_cause == repair_result_body()["actual_cause"]
        assert record.actual_cause != record.diagnosis_prefill["actual_cause"]
        assert equipment is not None and equipment.status is EquipmentStatus.FAULT
        assert other_fault is not None
        assert other_fault.status is FaultStatus.PENDING_ACCEPT


def test_repair_result_rejects_missing_and_completed_work_order(
    client: TestClient,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    work_order_id, token = start_repair(client, fault_id)

    missing = client.post(
        f"/api/work-orders/{uuid4()}/repair-result",
        headers=auth_headers(token, key="repair-result-missing"),
        json=repair_result_body(),
    )
    first = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key="repair-result-first"),
        json=repair_result_body(),
    )
    repeated = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key="repair-result-new-key"),
        json=repair_result_body(),
    )

    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "WORK_ORDER_NOT_FOUND"
    assert missing.json()["detail"]["audit_event_id"]
    assert first.status_code == 200
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "WORK_ORDER_STATE_CONFLICT"
    assert repeated.json()["detail"]["fields"] == {"status": "COMPLETED"}
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(HistoricalRepairCase)) == 1


def test_repair_result_rolls_back_business_changes_when_audit_fails(
    client: TestClient,
    monkeypatch,
) -> None:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    work_order_id, token = start_repair(client, fault_id)

    def fail_audit(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(
        "app.modules.maintenance.router.write_audit_event", fail_audit
    )
    safe_client = TestClient(client.app, raise_server_exceptions=False)
    response = safe_client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key="repair-result-rollback"),
        json=repair_result_body(),
    )

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTERNAL_SERVER_ERROR"
    assert response.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        order = db.get(WorkOrder, work_order_id)
        fault = db.get(FaultReport, fault_id)
        equipment = db.get(Equipment, equipment_id)
        record = db.scalar(
            select(MaintenanceRecord).where(
                MaintenanceRecord.work_order_id == work_order_id
            )
        )
        assert order is not None and order.status is WorkOrderStatus.IN_REPAIR
        assert fault is not None and fault.status is FaultStatus.IN_REPAIR
        assert equipment is not None
        assert equipment.status is EquipmentStatus.REPAIRING
        assert record is not None and record.actual_cause is None
        assert db.scalar(select(func.count()).select_from(HistoricalRepairCase)) == 0
        failure = db.get(AuditEvent, response.json()["detail"]["audit_event_id"])
        assert failure is not None and failure.action == "repair.complete"
