from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import IdempotencyRecord


def find_idempotent_response(
    db: Session,
    *,
    user_id: str,
    method: str,
    path: str,
    key: str,
) -> tuple[int, dict[str, object]] | None:
    record = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.method == method,
            IdempotencyRecord.path == path,
            IdempotencyRecord.idempotency_key == key,
        )
    )
    if record is None:
        return None
    return record.response_status, record.response_body


def save_idempotent_response(
    db: Session,
    *,
    user_id: str,
    method: str,
    path: str,
    key: str,
    status: int,
    body: dict[str, object],
) -> None:
    db.add(
        IdempotencyRecord(
            user_id=user_id,
            method=method,
            path=path,
            idempotency_key=key,
            response_status=status,
            response_body=body,
        )
    )
