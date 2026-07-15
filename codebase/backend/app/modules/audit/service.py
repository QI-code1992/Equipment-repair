from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


SENSITIVE_KEYS = {"password", "token", "authorization", "cookie", "secret", "api_key"}


def sanitize_audit_metadata(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower() in SENSITIVE_KEYS
            else sanitize_audit_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_audit_metadata(item) for item in value]
    return value


def write_audit_event(
    db: Session,
    *,
    actor_user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    metadata: dict[str, object],
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        metadata_json=sanitize_audit_metadata(metadata),
    )
    db.add(event)
    db.flush()
    return event
