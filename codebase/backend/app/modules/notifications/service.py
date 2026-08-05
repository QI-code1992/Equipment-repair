from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Notification


def add_notification(
    db: Session,
    *,
    notification_type: str,
    title: str,
    body: str,
    level: str,
    related_object_id: str | None,
    action_url: str | None,
) -> Notification:
    notification = Notification(
        type=notification_type,
        title=title,
        body=body,
        level=level,
        related_object_id=related_object_id,
        action_url=action_url,
    )
    db.add(notification)
    db.flush()
    return notification


def add_health_notification_if_band_changed(
    db: Session, *, equipment_id: str, score: int | float
) -> Notification | None:
    numeric_score = max(0, min(100, int(score)))
    if numeric_score == 100:
        label, level = "正常", "NORMAL"
    elif numeric_score >= 80:
        label, level = "低风险", "LOW"
    elif numeric_score >= 60:
        label, level = "中风险", "MEDIUM"
    elif numeric_score >= 40:
        label, level = "高风险", "HIGH"
    else:
        label, level = "严重风险", "SEVERE"
    previous = db.scalar(
        select(Notification)
        .where(
            Notification.type == "HEALTH_RISK",
            Notification.related_object_id == equipment_id,
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    if previous is not None and previous.level == level:
        return None
    return add_notification(
        db,
        notification_type="HEALTH_RISK",
        title="设备健康分恢复正常" if level == "NORMAL" else f"设备健康分进入{label}",
        body=f"设备 {equipment_id} 当前健康分为 {numeric_score}，风险等级为{label}。",
        level=level,
        related_object_id=equipment_id,
        action_url=f"/equipment/{equipment_id}",
    )
