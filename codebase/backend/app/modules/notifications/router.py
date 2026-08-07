from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

from .models import Notification, NotificationRead


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _read_exists(user_id: str):
    return exists().where(
        NotificationRead.notification_id == Notification.id,
        NotificationRead.user_id == user_id,
    )


def _notification_body(notification: Notification, *, is_read: bool) -> dict[str, object]:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "body": notification.body,
        "level": notification.level,
        "action_url": notification.action_url,
        "related_object_id": notification.related_object_id,
        "created_at": notification.created_at.isoformat(),
        "is_read": is_read,
    }


@router.get("", response_model=None)
def list_notifications(
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    read_exists = _read_exists(user.id)
    unread_statement = select(func.count()).select_from(Notification).where(~read_exists)
    statement = select(Notification, read_exists.label("is_read"))
    if unread_only:
        statement = statement.where(~read_exists)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(
        statement.order_by(Notification.created_at.desc(), Notification.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_notification_body(notification, is_read=bool(is_read)) for notification, is_read in rows],
        "total": total,
        "unread_count": db.scalar(unread_statement) or 0,
    }


@router.get("/unread-count", response_model=None)
def unread_count(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict[str, int]:
    return {
        "unread_count": db.scalar(
            select(func.count()).select_from(Notification).where(~_read_exists(user.id))
        )
        or 0
    }


@router.patch("/{notification_id}/read", response_model=None)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    if db.get(Notification, notification_id) is None:
        raise HTTPException(status_code=404, detail={"code": "NOTIFICATION_NOT_FOUND"})
    read = db.scalar(
        select(NotificationRead).where(
            NotificationRead.notification_id == notification_id,
            NotificationRead.user_id == user.id,
        )
    )
    if read is None:
        db.add(NotificationRead(notification_id=notification_id, user_id=user.id))
        write_audit_event(
            db,
            actor_user_id=user.id,
            action="notification.read",
            resource_type="notification",
            resource_id=notification_id,
            result="success",
            metadata={},
        )
        db.commit()
    return {"notification_id": notification_id, "is_read": True}


@router.post("/read-all", response_model=None)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    unread_ids = db.scalars(
        select(Notification.id).where(~_read_exists(user.id))
    ).all()
    for notification_id in unread_ids:
        db.add(NotificationRead(notification_id=notification_id, user_id=user.id))
    if unread_ids:
        write_audit_event(
            db,
            actor_user_id=user.id,
            action="notification.read_all",
            resource_type="notification",
            resource_id=None,
            result="success",
            metadata={"count": len(unread_ids)},
        )
        db.commit()
    return {"marked_read_count": len(unread_ids)}
