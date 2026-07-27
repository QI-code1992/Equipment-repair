from hashlib import sha256
from pathlib import Path
from typing import Annotated, Protocol, cast

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.integrations.file_scanning import ScannerUnavailable
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.knowledge import service
from app.modules.knowledge.models import FileObject, FileScanStatus, KnowledgeDataset, KnowledgeDocument


MAX_FILE_SIZE = 100 * 1024 * 1024
router = APIRouter(tags=["knowledge"])


class ObjectStorage(Protocol):
    def put(self, **kwargs: object) -> str: ...

    def put_file(self, **kwargs: object) -> str: ...

    def delete(self, object_key: str) -> None: ...


class FileScanner(Protocol):
    def is_safe(self, content: bytes) -> bool: ...

    def is_safe_file(self, path: Path) -> bool: ...


def _dependency(request: Request, name: str, error_code: str) -> object:
    dependency = getattr(request.app.state, name, None)
    if dependency is None:
        raise HTTPException(status_code=503, detail={"code": error_code})
    return dependency


def get_storage(request: Request) -> ObjectStorage:
    return cast(
        ObjectStorage,
        _dependency(request, "knowledge_storage", "KNOWLEDGE_STORAGE_UNAVAILABLE"),
    )


def get_scanner(request: Request) -> FileScanner:
    return cast(
        FileScanner,
        _dependency(request, "knowledge_scanner", "KNOWLEDGE_SCANNER_UNAVAILABLE"),
    )


def document_body(document: KnowledgeDocument) -> dict[str, object]:
    return {
        "id": document.id,
        "dataset_id": document.dataset_id,
        "file_id": document.object_storage_file_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "status": document.status.value,
        "failure_reason": document.failure_reason,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


@router.post(
    "/api/knowledge/documents",
    status_code=201,
    response_model=None,
    name="knowledge_document.create",
)
async def create_document(
    dataset_id: Annotated[str, Form(min_length=1, max_length=36)],
    file: Annotated[UploadFile, File()],
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:knowledge")),
    storage: ObjectStorage = Depends(get_storage),
    scanner: FileScanner = Depends(get_scanner),
) -> dict[str, object] | JSONResponse:
    content = await file.read(MAX_FILE_SIZE + 1)
    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=422, detail={"code": "KNOWLEDGE_FILE_SIZE_INVALID"}
        )
    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"
    request_body = {
        "dataset_id": dataset_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }
    replay = find_idempotent_response(
        db, user_id=actor.id, method="POST", path="/api/knowledge/documents",
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])
    if db.get(KnowledgeDataset, dataset_id) is None:
        raise HTTPException(status_code=404, detail={"code": "KNOWLEDGE_DATASET_NOT_FOUND"})
    try:
        safe = scanner.is_safe(content)
    except ScannerUnavailable:
        raise HTTPException(
            status_code=503, detail={"code": "KNOWLEDGE_SCANNER_UNAVAILABLE"}
        ) from None
    if not safe:
        raise HTTPException(status_code=422, detail={"code": "KNOWLEDGE_FILE_UNSAFE"})

    object_key = storage.put(
        filename=filename, content=content, content_type=content_type
    )
    try:
        file_object = FileObject(
            object_key=object_key,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            sha256=request_body["sha256"],
            scan_status=FileScanStatus.CLEAN,
            created_by=actor.id,
        )
        db.add(file_object)
        db.flush()
        document = service.register_document(
            db, dataset_id=dataset_id, object_storage_file_id=file_object.id,
            filename=filename, content_type=content_type, size_bytes=len(content),
            created_by=actor.id,
        )
        event = write_audit_event(
            db, actor_user_id=actor.id, action="knowledge_document.create",
            resource_type="knowledge_document", resource_id=document.id,
            result="success", metadata=request_body,
        )
        body = {**document_body(document), "audit_event_id": event.id}
        save_idempotent_response(
            db, user_id=actor.id, method="POST", path="/api/knowledge/documents",
            key=idempotency_key, request_body=request_body, status=201, body=body,
        )
        db.commit()
        return body
    except Exception:
        db.rollback()
        storage.delete(object_key)
        raise


@router.get(
    "/api/knowledge/documents/{document_id}",
    response_model=None,
    name="knowledge_document.get",
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:knowledge")),
) -> dict[str, object]:
    del actor
    document = db.get(KnowledgeDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail={"code": "KNOWLEDGE_DOCUMENT_NOT_FOUND"})
    return document_body(document)
