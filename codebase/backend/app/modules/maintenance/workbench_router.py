from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.equipment.models import Equipment
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.identity.service import permission_codes_for_user
from app.modules.maintenance.models import FaultReport, FaultStatus


router = APIRouter(tags=["workbench"])

ACTIVE_STATUSES = (FaultStatus.PENDING_ACCEPT, FaultStatus.IN_REPAIR)
TodoStatus = Literal["PENDING_ACCEPT", "IN_REPAIR"]


def todo_body(fault: FaultReport, equipment: Equipment) -> dict[str, object]:
    return {
        "id": fault.id,
        "number": fault.number,
        "equipment_id": equipment.id,
        "equipment_code": equipment.code,
        "equipment_name": equipment.name,
        "urgency": fault.urgency,
        "symptom": fault.symptom,
        "occurred_at": fault.occurred_at.isoformat(),
        "submitted_at": fault.submitted_at.isoformat(),
        "status": fault.status.value,
    }


@router.get("/api/workbench/todos", response_model=None)
def workbench_todos(
    status: TodoStatus | None = Query(default=None),
    urgency: str | None = Query(default=None, min_length=1, max_length=30),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("workbench:view")),
) -> dict[str, object]:
    statement = (
        select(FaultReport, Equipment)
        .join(Equipment, FaultReport.equipment_id == Equipment.id)
        .where(FaultReport.status.in_(ACTIVE_STATUSES))
        .order_by(FaultReport.submitted_at.desc(), FaultReport.id.asc())
        .limit(limit)
    )
    if status is not None:
        statement = statement.where(FaultReport.status == FaultStatus(status))
    if urgency is not None:
        statement = statement.where(FaultReport.urgency == urgency)
    rows = db.execute(statement).all()
    return {"items": [todo_body(fault, equipment) for fault, equipment in rows], "count": len(rows)}


@router.get("/api/workbench/alert-summary", response_model=None)
def workbench_alert_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("workbench:view")),
) -> dict[str, object]:
    base = select(FaultReport).where(FaultReport.status.in_(ACTIVE_STATUSES)).subquery()
    status_rows = db.execute(
        select(base.c.status, func.count()).group_by(base.c.status)
    ).all()
    urgency_rows = db.execute(
        select(base.c.urgency, func.count()).group_by(base.c.urgency)
    ).all()
    status_counts = sorted(
        ({"status": status.value if isinstance(status, FaultStatus) else status, "count": count}
         for status, count in status_rows),
        key=lambda item: (-int(item["count"]), str(item["status"])),
    )
    urgency_counts = sorted(
        ({"urgency": urgency, "count": count} for urgency, count in urgency_rows),
        key=lambda item: (-int(item["count"]), str(item["urgency"])),
    )
    return {
        "active_fault_count": sum(int(item["count"]) for item in status_counts),
        "status_counts": status_counts,
        "urgency_counts": urgency_counts,
    }


@router.get("/api/workbench/shortcuts", response_model=None)
def workbench_shortcuts(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("workbench:view")),
) -> dict[str, object]:
    permissions = permission_codes_for_user(db, actor.id)
    items = []
    if "fault:create" in permissions:
        items.append({"id": "fault_report", "label": "故障上报", "path": "/fault-report"})
    return {"items": items}
