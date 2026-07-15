import hashlib
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.audit.models import IdempotencyRecord


class IdempotencyKeyReused(RuntimeError):
    pass


def request_digest(body: object) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def advisory_lock_id(user_id: str, key: str) -> int:
    digest = hashlib.blake2b(f"{user_id}:{key}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=True)


def acquire_idempotency_lock(db: Session, user_id: str, key: str) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": advisory_lock_id(user_id, key)},
        )


def find_idempotent_response(
    db: Session,
    *,
    user_id: str,
    method: str,
    path: str,
    key: str,
    request_body: object,
) -> tuple[int, dict[str, object]] | None:
    acquire_idempotency_lock(db, user_id, key)
    record = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.idempotency_key == key,
        )
    )
    if record is None:
        return None
    if (
        record.method != method
        or record.path != path
        or record.request_hash != request_digest(request_body)
    ):
        raise IdempotencyKeyReused(key)
    return record.response_status, record.response_body


def save_idempotent_response(
    db: Session,
    *,
    user_id: str,
    method: str,
    path: str,
    key: str,
    request_body: object,
    status: int,
    body: dict[str, object],
) -> None:
    db.add(
        IdempotencyRecord(
            user_id=user_id,
            method=method,
            path=path,
            idempotency_key=key,
            request_hash=request_digest(request_body),
            response_status=status,
            response_body=body,
        )
    )
