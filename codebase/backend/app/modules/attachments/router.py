from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated
from hashlib import sha256
import logging

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.integrations.file_scanning import ScannerUnavailable
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.knowledge.router import FileScanner, ObjectStorage, get_scanner, get_storage


MAX_ATTACHMENT_SIZE = 100 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

router = APIRouter(tags=["attachments"])
logger = logging.getLogger(__name__)


def _invalid_attachment() -> HTTPException:
    return HTTPException(status_code=422, detail={"code": "ATTACHMENT_INVALID"})


@router.post("/api/attachments", status_code=201, response_model=None)
async def upload_attachment(
    file: Annotated[UploadFile, File()],
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
    storage: ObjectStorage = Depends(get_storage),
    scanner: FileScanner = Depends(get_scanner),
) -> dict[str, object] | JSONResponse:
    content_type = file.content_type or ""
    filename = file.filename or ""
    size_bytes = 0
    digest = sha256()
    temporary_path: Path | None = None
    with NamedTemporaryFile(prefix="equipment-attachment-", delete=False) as temporary:
        temporary_path = Path(temporary.name)
        while chunk := await file.read(64 * 1024):
            size_bytes += len(chunk)
            if size_bytes > MAX_ATTACHMENT_SIZE:
                break
            digest.update(chunk)
            temporary.write(chunk)
    request_body = {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "sha256": digest.hexdigest(),
    }
    try:
        replay = find_idempotent_response(
            db,
            user_id=actor.id,
            method="POST",
            path="/api/attachments",
            key=idempotency_key,
            request_body=request_body,
        )
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    if replay is not None:
        temporary_path.unlink(missing_ok=True)
        return JSONResponse(status_code=replay[0], content=replay[1])
    try:
        if not size_bytes or size_bytes > MAX_ATTACHMENT_SIZE or content_type not in ALLOWED_CONTENT_TYPES:
            raise _invalid_attachment()
        try:
            safe = scanner.is_safe_file(temporary_path)
        except ScannerUnavailable:
            raise HTTPException(status_code=503, detail={"code": "ATTACHMENT_SCAN_UNAVAILABLE"}) from None
        if not safe:
            raise HTTPException(status_code=422, detail={"code": "ATTACHMENT_INFECTED"})
        try:
            object_key = storage.put_file(
                filename=filename,
                path=temporary_path,
                size_bytes=size_bytes,
                content_type=content_type,
            )
        except Exception:
            raise HTTPException(status_code=503, detail={"code": "ATTACHMENT_STORAGE_UNAVAILABLE"}) from None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    response_body = {
        "object_key": object_key,
        "filename": filename,
        "size_bytes": size_bytes,
        "content_type": content_type,
    }
    try:
        write_audit_event(
            db,
            actor_user_id=actor.id,
            action="attachment.upload",
            resource_type="attachment",
            resource_id=object_key,
            result="success",
            metadata=response_body,
        )
        save_idempotent_response(
            db,
            user_id=actor.id,
            method="POST",
            path="/api/attachments",
            key=idempotency_key,
            request_body=request_body,
            status=201,
            body=response_body,
        )
        db.commit()
    except Exception:
        db.rollback()
        try:
            storage.delete(object_key)
        except Exception:
            logger.exception("attachment object compensation failed")
        raise
    return response_body
