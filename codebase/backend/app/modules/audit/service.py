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
ATTACHMENT_CONTEXT_KEYS = {
    "attachment",
    "attachments",
    "file",
    "files",
    "upload",
    "document",
    "image",
    "image_refs",
}
ATTACHMENT_CONTENT_KEYS = {"body", "content", "data", "bytes", "text", "base64"}
DIRECT_ATTACHMENT_CONTENT_KEYS = {
    "attachment_content",
    "file_content",
    "file_bytes",
    "content_base64",
}


def normalize_key(key: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key).lower().replace("-", "_")


def is_sensitive_key(key: str) -> bool:
    normalized = normalize_key(key)
    return (
        normalized in SENSITIVE_KEYS
        or normalized == "cookies"
        or normalized.startswith("authorization_")
        or normalized.endswith(SENSITIVE_KEY_SUFFIXES)
        or normalized.startswith(("password_", "passwd_", "pwd_", "cookie_", "cookies_"))
        or re.fullmatch(r"(?:password|passwd|pwd)\d+", normalized) is not None
    )


def is_attachment_context(key: str) -> bool:
    normalized = normalize_key(key)
    return normalized in ATTACHMENT_CONTEXT_KEYS or any(
        normalized.startswith(f"{prefix}_") for prefix in ATTACHMENT_CONTEXT_KEYS
    )


def sanitize_audit_metadata(
    value: object, *, context: tuple[str, ...] = ()
) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        attachment_context = any(is_attachment_context(part) for part in context)
        for key, item in value.items():
            normalized = normalize_key(key)
            redact = (
                is_sensitive_key(key)
                or normalized in DIRECT_ATTACHMENT_CONTENT_KEYS
                or (attachment_context and normalized in ATTACHMENT_CONTENT_KEYS)
            )
            result[key] = (
                "[REDACTED]"
                if redact
                else sanitize_audit_metadata(item, context=(*context, normalized))
            )
        return result
    if isinstance(value, list):
        return [sanitize_audit_metadata(item, context=context) for item in value]
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
