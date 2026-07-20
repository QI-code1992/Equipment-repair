from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.maintenance import service
from app.modules.maintenance.models import (
    FaultReport,
    HistoricalRepairCase,
    MaintenanceRecord,
    WorkOrder,
)
from app.modules.maintenance.schemas import (
    FaultReportCreate,
    RepairResultRequest,
    StartRepairRequest,
)


router = APIRouter(tags=["maintenance"])


def fault_report_body(item: FaultReport) -> dict[str, object]:
    return {
        "id": item.id,
        "number": item.number,
        "equipment_id": item.equipment_id,
        "organization_snapshot": item.organization_snapshot,
        "urgency": item.urgency,
        "symptom": item.symptom,
        "occurred_at": item.occurred_at.isoformat(),
        "possible_location": item.possible_location,
        "description": item.description,
        "attachment_refs": item.attachment_refs,
        "status": item.status.value,
        "submitter_id": item.submitter_id,
        "submitted_at": item.submitted_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def repair_start_body(
    fault: FaultReport,
    work_order: WorkOrder,
    record: MaintenanceRecord,
) -> dict[str, object]:
    return {
        "fault_report_id": fault.id,
        "work_order_id": work_order.id,
        "maintenance_record_id": record.id,
        "equipment_id": fault.equipment_id,
        "fault_status": fault.status.value,
        "work_order_status": work_order.status.value,
        "start_mode": record.start_mode.value,
        "diagnosis_draft_id": record.diagnosis_draft_id,
    }


def repair_result_body(
    order: WorkOrder,
    fault: FaultReport,
    record: MaintenanceRecord,
    case: HistoricalRepairCase,
) -> dict[str, object]:
    return {
        "work_order_id": order.id,
        "fault_report_id": fault.id,
        "maintenance_record_id": record.id,
        "historical_case_id": case.id,
        "work_order_status": order.status.value,
        "fault_status": fault.status.value,
        "actual_cause": record.actual_cause,
        "actual_solution": record.actual_solution,
        "repair_result": record.repair_result,
        "parts_replacement_notes": record.parts_replacement_notes,
    }


@router.post(
    "/api/fault-reports",
    status_code=201,
    response_model=None,
    name="fault_report.create",
)
def create_fault_report(
    payload: FaultReportCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
) -> dict[str, object] | JSONResponse:
    path = "/api/fault-reports"
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db,
        user_id=actor.id,
        method="POST",
        path=path,
        key=idempotency_key,
        request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])

    item = service.create_fault_report(db, payload, submitter_id=actor.id)
    event = write_audit_event(
        db,
        actor_user_id=actor.id,
        action="fault_report.create",
        resource_type="fault_report",
        resource_id=item.id,
        result="success",
        metadata=request_body,
    )
    body = {**fault_report_body(item), "audit_event_id": event.id}
    save_idempotent_response(
        db,
        user_id=actor.id,
        method="POST",
        path=path,
        key=idempotency_key,
        request_body=request_body,
        status=201,
        body=body,
    )
    db.commit()
    return body


@router.post(
    "/api/fault-reports/{fault_id}/start-repair",
    status_code=200,
    response_model=None,
    name="repair.start",
)
def start_repair(
    fault_id: str,
    payload: StartRepairRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:repair")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/fault-reports/{fault_id}/start-repair"
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])

    fault, work_order, record = service.start_repair(
        db, fault_id, payload, repairer_id=actor.id
    )
    event = write_audit_event(
        db, actor_user_id=actor.id, action="repair.start",
        resource_type="work_order", resource_id=work_order.id,
        result="success", metadata=request_body,
    )
    body = {**repair_start_body(fault, work_order, record), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=body,
    )
    db.commit()
    return body


@router.post(
    "/api/work-orders/{work_order_id}/repair-result",
    status_code=200,
    response_model=None,
    name="repair.complete",
)
def complete_repair(
    work_order_id: str,
    payload: RepairResultRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:close")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/work-orders/{work_order_id}/repair-result"
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])

    order, fault, record, case = service.complete_repair(
        db, work_order_id, payload
    )
    event = write_audit_event(
        db, actor_user_id=actor.id, action="repair.complete",
        resource_type="work_order", resource_id=order.id,
        result="success", metadata=request_body,
    )
    body = {**repair_result_body(order, fault, record, case), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=body,
    )
    db.commit()
    return body
