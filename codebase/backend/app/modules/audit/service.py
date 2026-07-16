import re

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "cookie",
    "password",
    "password_hash",
    "secret",
    "token",
}
SENSITIVE_KEY_SUFFIXES = ("_api_key", "_cookie", "_password", "_secret", "_token")


def is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key).lower().replace("-", "_")
    return (
        normalized in SENSITIVE_KEYS
        or normalized.startswith("authorization_")
        or normalized.endswith(SENSITIVE_KEY_SUFFIXES)
    )


def sanitize_audit_metadata(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if is_sensitive_key(key)
            else sanitize_audit_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_audit_metadata(item) for item in value]
    if isinstance(value, str) and "bearer " in value.lower():
        return "[REDACTED]"
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
