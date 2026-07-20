from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.equipment.models import Equipment, EquipmentStatus, Organization
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
from app.modules.maintenance.schemas import FaultReportCreate, StartRepairRequest


def _error(
    status_code: int,
    code: str,
    *,
    fields: dict[str, str] | None = None,
) -> HTTPException:
    detail: dict[str, object] = {"code": code}
    if fields:
        detail["fields"] = fields
    return HTTPException(status_code=status_code, detail=detail)


def _locked_equipment(db: Session, equipment_id: str) -> Equipment:
    statement = select(Equipment).where(Equipment.id == equipment_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    equipment = db.scalar(statement)
    if equipment is None:
        raise _error(404, "FAULT_EQUIPMENT_NOT_FOUND")
    return equipment


def _organization_snapshot(db: Session, line_id: str) -> dict[str, object]:
    line = db.get(Organization, line_id)
    if line is None:
        raise _error(409, "FAULT_ORGANIZATION_NOT_FOUND")
    workshop = None if line.parent_id is None else db.get(Organization, line.parent_id)
    factory = (
        None
        if workshop is None or workshop.parent_id is None
        else db.get(Organization, workshop.parent_id)
    )

    def item(organization: Organization | None) -> dict[str, str] | None:
        if organization is None:
            return None
        return {
            "id": organization.id,
            "code": organization.code,
            "name": organization.name,
        }

    return {"factory": item(factory), "workshop": item(workshop), "line": item(line)}


def create_fault_report(
    db: Session,
    payload: FaultReportCreate,
    *,
    submitter_id: str,
) -> FaultReport:
    equipment = _locked_equipment(db, payload.equipment_id)
    if equipment.status is EquipmentStatus.DISABLED:
        raise _error(409, "FAULT_EQUIPMENT_DISABLED")
    if payload.occurred_at > datetime.now(UTC):
        raise _error(
            422,
            "FAULT_OCCURRENCE_IN_FUTURE",
            fields={"occurred_at": "future"},
        )

    item = FaultReport(
        number=f"FR-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:12].upper()}",
        equipment_id=equipment.id,
        organization_snapshot=_organization_snapshot(db, equipment.organization_id),
        urgency=payload.urgency,
        symptom=payload.symptom,
        occurred_at=payload.occurred_at,
        possible_location=payload.possible_location,
        description=payload.description,
        attachment_refs=[reference.model_dump() for reference in payload.attachment_refs],
        submitter_id=submitter_id,
    )
    if equipment.status is EquipmentStatus.NORMAL:
        equipment.status = EquipmentStatus.FAULT
    db.add(item)
    db.flush()
    return item


def _locked_fault_report(db: Session, fault_id: str) -> FaultReport:
    statement = select(FaultReport).where(FaultReport.id == fault_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    fault = db.scalar(statement)
    if fault is None:
        raise _error(404, "FAULT_REPORT_NOT_FOUND")
    return fault


def _locked_diagnosis_draft(db: Session, draft_id: str) -> DiagnosisDraft:
    statement = select(DiagnosisDraft).where(DiagnosisDraft.id == draft_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    draft = db.scalar(statement)
    if draft is None:
        raise _error(404, "DIAGNOSIS_DRAFT_NOT_FOUND")
    return draft


def _adopted_diagnosis(
    db: Session, draft_id: str, fault_id: str
) -> tuple[DiagnosisDraft, dict[str, object], dict[str, object]]:
    draft = _locked_diagnosis_draft(db, draft_id)
    if draft.fault_report_id != fault_id:
        raise _error(409, "DIAGNOSIS_DRAFT_FAULT_MISMATCH")
    if draft.status is not DiagnosisDraftStatus.DIAGNOSIS_READY:
        raise _error(
            409, "DIAGNOSIS_DRAFT_NOT_READY", fields={"status": draft.status.value}
        )
    if draft.adopted_at is not None:
        raise _error(409, "DIAGNOSIS_DRAFT_ALREADY_ADOPTED")
    prefill_fields = {
        "fault_type",
        "actual_cause",
        "actual_solution",
        "parts_replacement_notes",
    }
    summary_fields = {
        "symptom",
        "key_evidence",
        "verification_results",
        "root_cause",
        "recommendations",
    }
    prefill = {
        key: value
        for key, value in (draft.allowed_prefill or {}).items()
        if key in prefill_fields
    }
    summary = {
        key: value
        for key, value in (draft.read_only_summary or {}).items()
        if key in summary_fields
    }
    return draft, prefill, summary


def _new_work_order(
    db: Session,
    fault: FaultReport,
    *,
    repairer_id: str,
    started_at: datetime,
) -> WorkOrder:
    work_order = WorkOrder(
        number=f"WO-{started_at:%Y%m%d}-{uuid4().hex[:12].upper()}",
        fault_report_id=fault.id,
        equipment_id=fault.equipment_id,
        status=WorkOrderStatus.IN_REPAIR,
        repairer_user_id=repairer_id,
        started_at=started_at,
    )
    db.add(work_order)
    db.flush()
    return work_order


def start_repair(
    db: Session,
    fault_id: str,
    payload: StartRepairRequest,
    *,
    repairer_id: str,
) -> tuple[FaultReport, WorkOrder, MaintenanceRecord]:
    fault = _locked_fault_report(db, fault_id)
    if fault.status is not FaultStatus.PENDING_ACCEPT:
        raise _error(
            409,
            "FAULT_STATE_CONFLICT",
            fields={"status": fault.status.value},
        )
    equipment = _locked_equipment(db, fault.equipment_id)
    now = datetime.now(UTC)
    draft = None
    diagnosis_prefill = None
    ai_summary = None
    if payload.mode is RepairStartMode.ADOPTED:
        assert payload.diagnosis_draft_id is not None
        draft, diagnosis_prefill, ai_summary = _adopted_diagnosis(
            db, payload.diagnosis_draft_id, fault.id
        )
    work_order = _new_work_order(
        db, fault, repairer_id=repairer_id, started_at=now
    )
    record = MaintenanceRecord(
        work_order_id=work_order.id,
        start_mode=payload.mode,
        diagnosis_draft_id=None if draft is None else draft.id,
        diagnosis_prefill=diagnosis_prefill,
        ai_summary=ai_summary,
    )
    if draft is not None:
        draft.adopted_at = now
    fault.status = FaultStatus.IN_REPAIR
    equipment.status = EquipmentStatus.REPAIRING
    db.add(record)
    db.flush()
    return fault, work_order, record
