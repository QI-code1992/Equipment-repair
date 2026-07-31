from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, Organization
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.identity.service import permission_codes_for_user
from app.modules.knowledge.models import KnowledgeDocument
from app.modules.maintenance.models import FaultReport, HistoricalRepairCase, MaintenanceRecord, WorkOrder


router = APIRouter(tags=["task-012-read-models"])


def _page(items: list[dict[str, object]], page: int, page_size: int) -> dict[str, object]:
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "count": len(items), "page": page, "page_size": page_size}


def _record_body(record: MaintenanceRecord, order: WorkOrder, fault: FaultReport, *, include_detail: bool) -> dict[str, object]:
    body: dict[str, object] = {
        "maintenance_record_id": record.id,
        "work_order_id": order.id,
        "fault_report_id": fault.id,
        "equipment_id": order.equipment_id,
        "work_order_number": order.number,
        "status": order.status.value,
        "symptom": fault.symptom,
        "actual_cause": record.actual_cause,
        "actual_solution": record.actual_solution,
        "repair_result": record.repair_result,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "knowledge_status": "NOT_LINKED",
    }
    if include_detail:
        body.update({
            "start_mode": record.start_mode.value,
            "parts_replacement_notes": record.parts_replacement_notes,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        })
    return body


@router.get("/api/bi/dashboard", response_model=None)
def bi_dashboard(
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("bi:view")),
) -> dict[str, object]:
    equipment_filter = select(Equipment.id)
    if organization_id is not None:
        equipment_filter = equipment_filter.where(Equipment.organization_id == organization_id)
    fault_statement = select(FaultReport).where(FaultReport.equipment_id.in_(equipment_filter))
    faults = db.scalars(fault_statement).all()
    orders = db.scalars(select(WorkOrder).where(WorkOrder.equipment_id.in_(equipment_filter))).all()
    by_org = db.execute(
        select(Organization.id, Organization.name, func.count(FaultReport.id))
        .select_from(Organization)
        .join(Equipment, Equipment.organization_id == Organization.id)
        .outerjoin(FaultReport, FaultReport.equipment_id == Equipment.id)
        .group_by(Organization.id, Organization.name)
        .order_by(func.count(FaultReport.id).desc(), Organization.id.asc())
        .limit(20)
    ).all()
    completed = [item for item in orders if item.completed_at is not None]
    now = datetime.now(UTC)
    trend = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date().isoformat()
        trend.append({"date": day, "fault_count": sum(item.submitted_at.date().isoformat() == day for item in faults), "completed_work_order_count": sum(item.completed_at is not None and item.completed_at.date().isoformat() == day for item in orders)})
    return {
        "summary": {"fault_count": len(faults), "active_fault_count": sum(item.status.value != "PROCESSED" for item in faults), "completed_work_order_count": len(completed), "completion_rate": round(len(completed) / len(orders), 4) if orders else 0.0},
        "trend": trend,
        "efficiency": {"completed_work_order_count": len(completed), "average_completion_hours": 0.0},
        "organization_ranking": [{"organization_id": item[0], "organization_name": item[1], "fault_count": int(item[2])} for item in by_org],
        "history_comparison": {"current_fault_count": len(faults), "previous_fault_count": 0},
    }


@router.get("/api/equipment/{equipment_id}/maintenance-history", response_model=None)
def equipment_maintenance_history(
    equipment_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("equipment:read")),
) -> dict[str, object]:
    if db.get(Equipment, equipment_id) is None:
        raise HTTPException(status_code=404, detail={"code": "EQUIPMENT_NOT_FOUND"})
    rows = db.execute(
        select(MaintenanceRecord, WorkOrder, FaultReport)
        .join(WorkOrder, MaintenanceRecord.work_order_id == WorkOrder.id)
        .join(FaultReport, WorkOrder.fault_report_id == FaultReport.id)
        .where(WorkOrder.equipment_id == equipment_id)
        .order_by(WorkOrder.completed_at.desc(), WorkOrder.id.asc())
    ).all()
    return _page([_record_body(*row, include_detail=False) for row in rows], page, page_size)


@router.get("/api/maintenance-records", response_model=None)
def maintenance_records(
    equipment_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("maintenance:view")),
) -> dict[str, object]:
    statement = select(MaintenanceRecord, WorkOrder, FaultReport).join(WorkOrder, MaintenanceRecord.work_order_id == WorkOrder.id).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id)
    if equipment_id is not None:
        statement = statement.where(WorkOrder.equipment_id == equipment_id)
    rows = db.execute(statement.order_by(WorkOrder.completed_at.desc(), WorkOrder.id.asc())).all()
    return _page([_record_body(*row, include_detail=False) for row in rows], page, page_size)


@router.get("/api/maintenance-records/{record_id}", response_model=None)
def maintenance_record_detail(
    record_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("maintenance:detail")),
) -> dict[str, object]:
    row = db.execute(select(MaintenanceRecord, WorkOrder, FaultReport).join(WorkOrder, MaintenanceRecord.work_order_id == WorkOrder.id).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id).where(MaintenanceRecord.id == record_id)).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "MAINTENANCE_RECORD_NOT_FOUND"})
    return _record_body(*row, include_detail=True)


@router.get("/api/work-orders", response_model=None)
def work_orders(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("maintenance:view")),
) -> dict[str, object]:
    permissions = permission_codes_for_user(db, actor.id)
    statement = select(WorkOrder, FaultReport).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id)
    if "maintenance:detail" not in permissions:
        statement = statement.where(WorkOrder.repairer_user_id == actor.id)
    if status is not None:
        statement = statement.where(WorkOrder.status == status)
    rows = db.execute(statement.order_by(WorkOrder.created_at.desc(), WorkOrder.id.asc())).all()
    items = [{"id": order.id, "number": order.number, "fault_report_id": order.fault_report_id, "equipment_id": order.equipment_id, "status": order.status.value, "repairer_user_id": order.repairer_user_id, "started_at": order.started_at.isoformat() if order.started_at else None, "completed_at": order.completed_at.isoformat() if order.completed_at else None, "symptom": fault.symptom} for order, fault in rows]
    return _page(items, page, page_size)


@router.get("/api/work-orders/{work_order_id}", response_model=None)
def work_order_detail(
    work_order_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("maintenance:view")),
) -> dict[str, object]:
    row = db.execute(select(WorkOrder, FaultReport).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id).where(WorkOrder.id == work_order_id)).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "WORK_ORDER_NOT_FOUND"})
    order, fault = row
    if "maintenance:detail" not in permission_codes_for_user(db, actor.id) and order.repairer_user_id != actor.id:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
    return {"id": order.id, "number": order.number, "fault_report_id": order.fault_report_id, "equipment_id": order.equipment_id, "status": order.status.value, "repairer_user_id": order.repairer_user_id, "started_at": order.started_at.isoformat() if order.started_at else None, "pending_inspection_at": order.pending_inspection_at.isoformat() if order.pending_inspection_at else None, "completed_at": order.completed_at.isoformat() if order.completed_at else None, "symptom": fault.symptom}


@router.get("/api/audit-events", response_model=None)
def audit_events(
    action: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("system:audit")),
) -> dict[str, object]:
    statement = select(AuditEvent)
    if action is not None:
        statement = statement.where(AuditEvent.action == action)
    records = db.scalars(statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.asc())).all()
    items = [{"id": item.id, "actor_user_id": item.actor_user_id, "action": item.action, "resource_type": item.resource_type, "resource_id": item.resource_id, "result": item.result, "created_at": item.created_at.isoformat()} for item in records]
    return _page(items, page, page_size)


@router.get("/api/intelligence/usage", response_model=None)
def intelligence_usage(
    _: User = Depends(require_permission("intelligence:audit")),
) -> dict[str, object]:
    return {"items": [], "count": 0, "retention_days": 30}


@router.get("/api/intelligence/knowledge-documents", response_model=None)
def intelligence_knowledge_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("intelligence:audit")),
) -> dict[str, object]:
    documents = db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc(), KnowledgeDocument.id.asc())).all()
    items = [{"id": item.id, "dataset_id": item.dataset_id, "filename": item.filename, "status": item.status.value, "failure_reason": item.failure_reason, "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat(), "retry_available": item.status.value == "FAILED"} for item in documents]
    return _page(items, page, page_size)
