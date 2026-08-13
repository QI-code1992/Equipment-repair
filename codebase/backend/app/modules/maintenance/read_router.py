from datetime import UTC, datetime, timedelta

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.audit.models import AuditEvent
from app.modules.agent_runtime.models import AgentRun, AgentThread
from app.modules.equipment.models import Equipment, Organization
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.identity.service import permission_codes_for_user
from app.modules.knowledge.models import KnowledgeDocument
from app.modules.maintenance.models import FaultReport, HistoricalRepairCase, MaintenanceRecord, WorkOrder


router = APIRouter(tags=["task-012-read-models"])


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _page(items: list[dict[str, object]], page: int, page_size: int) -> dict[str, object]:
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "count": len(items), "page": page, "page_size": page_size}


def _record_body(record: MaintenanceRecord, order: WorkOrder, fault: FaultReport, *, include_detail: bool, linked_work_order_ids: set[str] | None = None) -> dict[str, object]:
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
        "knowledge_status": "LINKED" if linked_work_order_ids is not None and order.id in linked_work_order_ids else "NOT_LINKED",
    }
    if include_detail:
        body.update({
            "start_mode": record.start_mode.value,
            "parts_replacement_notes": record.parts_replacement_notes,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        })
    return body


def _linked_work_order_ids(db: Session, work_order_ids: list[str]) -> set[str]:
    if not work_order_ids:
        return set()
    return set(db.scalars(select(HistoricalRepairCase.source_work_order_id).where(HistoricalRepairCase.source_work_order_id.in_(work_order_ids))).all())

@router.get("/api/bi/dashboard", response_model=None)
def bi_dashboard(
    organization_id: str | None = None,
    period: Literal["day", "week", "month"] = Query(default="week"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("bi:view")),
) -> dict[str, object]:
    if organization_id is not None and db.get(Organization, organization_id) is None:
        raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})
    equipment_filter = select(Equipment.id)
    if organization_id is not None:
        equipment_filter = equipment_filter.where(Equipment.organization_id == organization_id)
    fault_statement = select(FaultReport).where(FaultReport.equipment_id.in_(equipment_filter))
    faults = db.scalars(fault_statement).all()
    orders = db.scalars(select(WorkOrder).where(WorkOrder.equipment_id.in_(equipment_filter))).all()
    now = datetime.now(UTC)
    window_days = {"day": 1, "week": 7, "month": 30}[period]
    current_window_start = now - timedelta(days=window_days)
    previous_window_start = now - timedelta(days=window_days * 2)
    current_faults = [item for item in faults if _utc(item.submitted_at) >= current_window_start]
    current_completed = [item for item in orders if item.completed_at is not None and _utc(item.completed_at) >= current_window_start]
    current_orders = [item for item in orders if _utc(item.created_at) >= current_window_start or (item.completed_at is not None and _utc(item.completed_at) >= current_window_start)]
    ranking_statement = (
        select(Organization.id, Organization.name, func.count(FaultReport.id))
        .select_from(Organization)
        .join(Equipment, Equipment.organization_id == Organization.id)
        .outerjoin(FaultReport, and_(FaultReport.equipment_id == Equipment.id, FaultReport.submitted_at >= current_window_start))
        .group_by(Organization.id, Organization.name)
        .order_by(func.count(FaultReport.id).desc(), Organization.id.asc())
        .limit(20)
    )
    if organization_id is not None:
        ranking_statement = ranking_statement.where(Organization.id == organization_id)
    by_org = db.execute(ranking_statement).all()
    completed_durations = [
        (_utc(item.completed_at) - _utc(item.started_at)).total_seconds() / 3600
        for item in current_completed
        if item.started_at is not None and _utc(item.completed_at) >= _utc(item.started_at)
    ]
    trend = []
    for offset in range(window_days - 1, -1, -1):
        day = (now - timedelta(days=offset)).date().isoformat()
        trend.append({"date": day, "fault_count": sum(_utc(item.submitted_at).date().isoformat() == day for item in faults), "completed_work_order_count": sum(item.completed_at is not None and _utc(item.completed_at).date().isoformat() == day for item in orders)})
    return {
        "summary": {"fault_count": len(current_faults), "active_fault_count": sum(item.status.value != "PROCESSED" for item in current_faults), "completed_work_order_count": len(current_completed), "completion_rate": round(len(current_completed) / len(current_orders), 4) if current_orders else 0.0},
        "trend": trend,
        "efficiency": {
            "completed_work_order_count": len(current_completed),
            "average_completion_hours": round(sum(completed_durations) / len(completed_durations), 2) if completed_durations else None,
        },
        "organization_ranking": [{"organization_id": item[0], "organization_name": item[1], "fault_count": int(item[2])} for item in by_org],
        "history_comparison": {
            "current_fault_count": sum(_utc(item.submitted_at) >= current_window_start for item in faults),
            "previous_fault_count": sum(previous_window_start <= _utc(item.submitted_at) < current_window_start for item in faults),
        },
        "period": period,
    }


@router.get("/api/maintenance-history/equipment/{equipment_id}", response_model=None)
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
    linked_work_order_ids = _linked_work_order_ids(db, [row[1].id for row in rows])
    items = [_record_body(*row, include_detail=False, linked_work_order_ids=linked_work_order_ids) for row in rows]
    return {**_page(items, page, page_size), "trend": _history_trend(rows)}


def _history_trend(rows: list[tuple[MaintenanceRecord, WorkOrder, FaultReport]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for _, order, _ in rows:
        if order.completed_at is None:
            continue
        day = _utc(order.completed_at).date().isoformat()
        counts[day] = counts.get(day, 0) + 1
    return [{"date": day, "completed_count": counts[day]} for day in sorted(counts)]


@router.get("/api/maintenance-records", response_model=None)
def maintenance_records(
    equipment_id: str | None = None,
    knowledge_status: Literal["LINKED", "NOT_LINKED"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("maintenance:view")),
) -> dict[str, object]:
    statement = select(MaintenanceRecord, WorkOrder, FaultReport).join(WorkOrder, MaintenanceRecord.work_order_id == WorkOrder.id).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id)
    if equipment_id is not None:
        statement = statement.where(WorkOrder.equipment_id == equipment_id)
    rows = db.execute(statement.order_by(WorkOrder.completed_at.desc(), WorkOrder.id.asc())).all()
    linked_work_order_ids = _linked_work_order_ids(db, [row[1].id for row in rows])
    items = [_record_body(*row, include_detail=False, linked_work_order_ids=linked_work_order_ids) for row in rows]
    if knowledge_status is not None:
        items = [item for item in items if item["knowledge_status"] == knowledge_status]
    return _page(items, page, page_size)


@router.get("/api/maintenance-records/{record_id}", response_model=None)
def maintenance_record_detail(
    record_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("maintenance:detail")),
) -> dict[str, object]:
    row = db.execute(select(MaintenanceRecord, WorkOrder, FaultReport).join(WorkOrder, MaintenanceRecord.work_order_id == WorkOrder.id).join(FaultReport, WorkOrder.fault_report_id == FaultReport.id).where(MaintenanceRecord.id == record_id)).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "MAINTENANCE_RECORD_NOT_FOUND"})
    linked_work_order_ids = _linked_work_order_ids(db, [row[1].id])
    return _record_body(*row, include_detail=True, linked_work_order_ids=linked_work_order_ids)


@router.get("/api/work-orders", response_model=None)
def work_orders(
    status: Literal["DRAFT", "PENDING_ACCEPT", "IN_REPAIR", "PENDING_INSPECTION", "COMPLETED"] | None = None,
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
    resource_type: str | None = None,
    result: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("system:audit")),
) -> dict[str, object]:
    statement = select(AuditEvent)
    if action is not None:
        statement = statement.where(AuditEvent.action == action)
    if resource_type is not None:
        statement = statement.where(AuditEvent.resource_type == resource_type)
    if result is not None:
        statement = statement.where(AuditEvent.result == result)
    records = db.scalars(statement.order_by(AuditEvent.created_at.desc(), AuditEvent.id.asc())).all()
    users = {item.id: item for item in db.scalars(select(User).where(User.id.in_([event.actor_user_id for event in records if event.actor_user_id is not None])))}
    items = [{"id": item.id, "occurred_at": item.created_at.isoformat(), "actor_user_id": item.actor_user_id, "actor_display_name": users[item.actor_user_id].display_name or users[item.actor_user_id].username if item.actor_user_id in users else None, "module": item.resource_type, "action": item.action, "target_type": item.resource_type, "target_id": item.resource_id, "target_display_name": item.resource_id, "result": item.result, "summary": item.action} for item in records]
    return _page(items, page, page_size)


@router.get("/api/login-events", response_model=None)
def login_events(
    username: str | None = None,
    result: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("system:audit")),
) -> dict[str, object]:
    records = db.scalars(select(AuditEvent).where(AuditEvent.action == "login").order_by(AuditEvent.created_at.desc(), AuditEvent.id.asc())).all()
    users = {item.id: item for item in db.scalars(select(User))}
    items = []
    for item in records:
        login_name = str(item.metadata_json.get("username", ""))
        if username is not None and login_name != username:
            continue
        if result is not None and item.result != result:
            continue
        user = users.get(item.actor_user_id) if item.actor_user_id else None
        items.append({"id": item.id, "username": login_name, "display_name": user.display_name if user else None, "logged_at": item.created_at.isoformat(), "source_ip": None, "client_summary": None, "result": item.result, "reason": None if item.result == "success" else "INVALID_CREDENTIALS"})
    return _page(items, page, page_size)


@router.get("/api/intelligence/usage", response_model=None)
def intelligence_usage(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("intelligence:audit")),
) -> dict[str, object]:
    cutoff = datetime.now(UTC) - timedelta(days=30)
    rows = db.execute(
        select(
            AgentThread.agent_id,
            AgentRun.status,
            func.count(AgentRun.id),
            func.coalesce(func.sum(AgentRun.config_snapshot_json["max_reply_tokens"].as_integer()), 0),
        )
        .join(AgentThread, AgentRun.thread_id == AgentThread.id)
        .where((AgentRun.started_at.is_(None)) | (AgentRun.started_at >= cutoff))
        .group_by(AgentThread.agent_id, AgentRun.status)
        .order_by(AgentThread.agent_id.asc(), AgentRun.status.asc())
    ).all()
    items = [
        {
            "agent_id": agent_id,
            "status": status,
            "run_count": int(run_count),
            "configured_max_reply_tokens": int(token_budget),
        }
        for agent_id, status, run_count, token_budget in rows
    ]
    return {
        "items": items,
        "count": len(items),
        "retention_days": 30,
        "token_measurement": "configured_max_reply_tokens_not_actual_usage",
    }


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
