from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge import service
from app.modules.knowledge.models import KnowledgeDocument, KnowledgeDocumentStatus


class ObjectStorage(Protocol):
    def get(self, object_key: str) -> bytes: ...


class KnowledgeAdapter(service.KnowledgeAdapter, Protocol):
    pass


@dataclass(frozen=True)
class WorkerResult:
    uploaded: int
    refreshed: int
    failed: int


def sync_pending_documents(
    db: Session,
    storage: ObjectStorage,
    adapter: KnowledgeAdapter,
    *,
    limit: int = 50,
) -> WorkerResult:
    if limit < 1 or limit > 500:
        raise ValueError("worker limit must be between 1 and 500")
    documents = list(
        db.scalars(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.status.in_(
                    (
                        KnowledgeDocumentStatus.UPLOADING,
                        KnowledgeDocumentStatus.PARSING,
                    )
                )
            )
            .order_by(KnowledgeDocument.created_at, KnowledgeDocument.id)
            .limit(limit)
        )
    )
    uploaded = refreshed = failed = 0
    for document in documents:
        try:
            if document.status is KnowledgeDocumentStatus.UPLOADING:
                try:
                    file_content = storage.get(
                        _object_key(db, document.object_storage_file_id)
                    )
                except Exception:
                    document.status = KnowledgeDocumentStatus.FAILED
                    document.failure_reason = "object storage read failed"
                    db.flush()
                    failed += 1
                    continue
                service.sync_uploaded_document(db, document.id, file_content, adapter)
                if document.status is KnowledgeDocumentStatus.PARSING:
                    uploaded += 1
                else:
                    failed += 1
            else:
                service.refresh_document_status(db, document.id, adapter)
                if document.status is KnowledgeDocumentStatus.FAILED:
                    failed += 1
                else:
                    refreshed += 1
        except Exception:
            document.status = KnowledgeDocumentStatus.FAILED
            document.failure_reason = "knowledge synchronization failed"
            db.flush()
            failed += 1
    return WorkerResult(uploaded=uploaded, refreshed=refreshed, failed=failed)


def _object_key(db: Session, file_object_id: str) -> str:
    from app.modules.knowledge.models import FileObject

    file_object = db.get(FileObject, file_object_id)
    if file_object is None or file_object.scan_status.value != "CLEAN":
        raise ValueError("scanned object is unavailable")
    return file_object.object_key
