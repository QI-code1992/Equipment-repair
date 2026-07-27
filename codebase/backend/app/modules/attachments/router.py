from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
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


def _invalid_attachment() -> HTTPException:
    return HTTPException(status_code=422, detail={"code": "ATTACHMENT_INVALID"})


@router.post("/api/attachments", status_code=201)
async def upload_attachment(
    file: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
    storage: ObjectStorage = Depends(get_storage),
    scanner: FileScanner = Depends(get_scanner),
) -> dict[str, object]:
    content = await file.read(MAX_ATTACHMENT_SIZE + 1)
    content_type = file.content_type or ""
    filename = file.filename or ""
    if not content or len(content) > MAX_ATTACHMENT_SIZE or content_type not in ALLOWED_CONTENT_TYPES:
        raise _invalid_attachment()

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(prefix="equipment-attachment-", delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        try:
            safe = scanner.is_safe(content)
        except ScannerUnavailable:
            raise HTTPException(status_code=503, detail={"code": "ATTACHMENT_SCAN_UNAVAILABLE"}) from None
        if not safe:
            raise HTTPException(status_code=422, detail={"code": "ATTACHMENT_INFECTED"})
        try:
            object_key = storage.put(
                filename=filename, content=content, content_type=content_type
            )
        except Exception:
            raise HTTPException(status_code=503, detail={"code": "ATTACHMENT_STORAGE_UNAVAILABLE"}) from None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    write_audit_event(
        db,
        actor_user_id=actor.id,
        action="attachment.upload",
        resource_type="attachment",
        resource_id=object_key,
        result="success",
        metadata={
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(content),
            "object_key": object_key,
        },
    )
    db.commit()
    return {
        "object_key": object_key,
        "filename": filename,
        "size_bytes": len(content),
        "content_type": content_type,
    }
