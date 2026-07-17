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
SENSITIVE_SEMANTIC_SEGMENTS = {
    "authorization",
    "cookie",
    "cookies",
    "passwd",
    "password",
    "pwd",
    "secret",
    "token",
}
COMPACT_SENSITIVE_PREFIXES = (
    "authorization",
    "cookie",
    "cookies",
    "passwd",
    "password",
    "pwd",
    "secret",
)
COMPACT_SENSITIVE_PREFIX_SUFFIXES = ("confirmation", "hash", "value")
COMPACT_SENSITIVE_SUFFIXES = (
    "authorization",
    "cookie",
    "cookies",
    "passwd",
    "password",
    "pwd",
    "secret",
)
TOKEN_METRIC_KEYS = {"token_count", "token_usage"}
ATTACHMENT_CONTEXT_SEGMENTS = {
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
ATTACHMENT_METADATA_KEYS = {
    "attachment_id",
    "checksum",
    "content_type",
    "extension",
    "file_id",
    "file_name",
    "filename",
    "length",
    "mime_type",
    "name",
    "sha1",
    "sha256",
    "size",
}


def normalize_key(key: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key).lower().replace("-", "_")


def key_segments(key: str) -> tuple[str, ...]:
    return tuple(segment for segment in normalize_key(key).split("_") if segment)


def has_compact_sensitive_form(normalized: str) -> bool:
    return normalized.endswith(COMPACT_SENSITIVE_SUFFIXES) or any(
        normalized == f"{prefix}{suffix}"
        for prefix in COMPACT_SENSITIVE_PREFIXES
        for suffix in COMPACT_SENSITIVE_PREFIX_SUFFIXES
    )


def is_sensitive_key(key: str) -> bool:
    normalized = normalize_key(key)
    segments = key_segments(key)
    return (
        normalized in SENSITIVE_KEYS
        or normalized == "cookies"
        or normalized not in TOKEN_METRIC_KEYS
        and any(segment in SENSITIVE_SEMANTIC_SEGMENTS for segment in segments)
        or normalized.startswith("authorization_")
        or normalized.endswith(SENSITIVE_KEY_SUFFIXES)
        or has_compact_sensitive_form(normalized)
        or normalized.startswith(("password_", "passwd_", "pwd_", "cookie_", "cookies_"))
        or re.fullmatch(r"(?:password|passwd|pwd)\d+", normalized) is not None
    )


def is_attachment_context(key: str) -> bool:
    return any(segment in ATTACHMENT_CONTEXT_SEGMENTS for segment in key_segments(key))


def has_attachment_context(context: tuple[str, ...]) -> bool:
    return any(is_attachment_context(part) for part in context)


def sanitize_audit_metadata(
    value: object, *, context: tuple[str, ...] = ()
) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        attachment_context = has_attachment_context(context)
        for key, item in value.items():
            normalized = normalize_key(key)
            redact = (
                is_sensitive_key(key)
                or normalized in DIRECT_ATTACHMENT_CONTENT_KEYS
                or (attachment_context and normalized in ATTACHMENT_CONTENT_KEYS)
                or (
                    attachment_context
                    and normalized not in ATTACHMENT_METADATA_KEYS
                )
            )
            result[key] = (
                "[REDACTED]"
                if redact
                else sanitize_audit_metadata(item, context=(*context, normalized))
            )
        return result
    if isinstance(value, list):
        if has_attachment_context(context) and all(
            not isinstance(item, dict) for item in value
        ):
            return "[REDACTED]"
        return [sanitize_audit_metadata(item, context=context) for item in value]
    if has_attachment_context(context) and (
        not context or context[-1] not in ATTACHMENT_METADATA_KEYS
    ):
        return "[REDACTED]"
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
