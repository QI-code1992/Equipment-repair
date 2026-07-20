from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from app.modules.equipment.models import Equipment, EquipmentStatus, Organization
from app.modules.maintenance.models import (
    DiagnosisDraft,
    DiagnosisDraftStatus,
    FaultReport,
    FaultStatus,
    HistoricalRepairCase,
    MaintenanceRecord,
    RepairStartMode,
    WorkOrder,
    WorkOrderStatus,
)
from app.modules.maintenance.schemas import (
    FaultReportCreate,
    RepairResultRequest,
    SimilarCaseQuery,
    StartRepairRequest,
)


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


def _locked_work_order(db: Session, work_order_id: str) -> WorkOrder:
    statement = select(WorkOrder).where(WorkOrder.id == work_order_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if order is None:
        raise _error(404, "WORK_ORDER_NOT_FOUND")
    return order


def _maintenance_record(db: Session, work_order_id: str) -> MaintenanceRecord:
    statement = select(MaintenanceRecord).where(
        MaintenanceRecord.work_order_id == work_order_id
    )
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    record = db.scalar(statement)
    if record is None:
        raise _error(409, "MAINTENANCE_RECORD_NOT_FOUND")
    return record


def _historical_case(
    fault: FaultReport,
    order: WorkOrder,
    equipment: Equipment,
    record: MaintenanceRecord,
    completed_at: datetime,
) -> HistoricalRepairCase:
    assert record.actual_cause is not None
    assert record.actual_solution is not None
    assert record.repair_result is not None
    return HistoricalRepairCase(
        source_work_order_id=order.id,
        source_fault_report_id=fault.id,
        equipment_id=equipment.id,
        equipment_type=equipment.type,
        equipment_model=equipment.model,
        symptom=fault.symptom,
        actual_cause=record.actual_cause,
        actual_solution=record.actual_solution,
        repair_result=record.repair_result,
        completed_at=completed_at,
    )


def complete_repair(
    db: Session,
    work_order_id: str,
    payload: RepairResultRequest,
) -> tuple[WorkOrder, FaultReport, MaintenanceRecord, HistoricalRepairCase]:
    order = _locked_work_order(db, work_order_id)
    if order.status is not WorkOrderStatus.IN_REPAIR:
        raise _error(
            409, "WORK_ORDER_STATE_CONFLICT", fields={"status": order.status.value}
        )
    fault = _locked_fault_report(db, order.fault_report_id)
    equipment = _locked_equipment(db, order.equipment_id)
    record = _maintenance_record(db, order.id)
    completed_at = datetime.now(UTC)
    record.actual_cause = payload.actual_cause
    record.actual_solution = payload.actual_solution
    record.repair_result = payload.repair_result
    record.parts_replacement_notes = payload.parts_replacement_notes
    order.status = WorkOrderStatus.PENDING_INSPECTION
    order.pending_inspection_at = completed_at
    case = _historical_case(fault, order, equipment, record, completed_at)
    db.add(case)
    order.status = WorkOrderStatus.COMPLETED
    order.completed_at = completed_at
    fault.status = FaultStatus.PROCESSED
    active = db.scalar(
        select(FaultReport.id).where(
            FaultReport.equipment_id == equipment.id,
            FaultReport.status.in_([FaultStatus.PENDING_ACCEPT, FaultStatus.IN_REPAIR]),
        ).limit(1)
    )
    equipment.status = EquipmentStatus.FAULT if active else EquipmentStatus.NORMAL
    db.flush()
    return order, fault, record, case


def find_similar_cases(
    db: Session, query: SimilarCaseQuery
) -> list[HistoricalRepairCase]:
    matches = []
    priorities = []
    if query.equipment_type and query.equipment_model:
        priorities.append(
            (
                and_(
                    HistoricalRepairCase.equipment_type == query.equipment_type,
                    HistoricalRepairCase.equipment_model == query.equipment_model,
                ),
                3,
            )
        )
    if query.equipment_type:
        condition = HistoricalRepairCase.equipment_type == query.equipment_type
        matches.append(condition)
        priorities.append((condition, 2))
    if query.equipment_model:
        condition = HistoricalRepairCase.equipment_model == query.equipment_model
        matches.append(condition)
        priorities.append((condition, 2))
    if query.symptom:
        condition = HistoricalRepairCase.symptom.ilike(f"%{query.symptom}%")
        matches.append(condition)
        priorities.append((condition, 1))
    score = case(*priorities, else_=0)
    statement = (
        select(HistoricalRepairCase)
        .where(or_(*matches))
        .order_by(
            score.desc(),
            HistoricalRepairCase.completed_at.desc(),
            HistoricalRepairCase.id.asc(),
        )
        .limit(query.limit)
    )
    return list(db.scalars(statement))
