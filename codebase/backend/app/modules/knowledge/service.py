from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ragflow.adapter import (
    DocumentStatus,
    KnowledgeDocumentRef,
    RetrievalResult,
)
from app.modules.knowledge.models import (
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeDocumentStatus,
)


class KnowledgeAdapter(Protocol):
    def upload_and_parse(self, **kwargs: object) -> str: ...

    def get_document_status(
        self, dataset_id: str, document_id: str
    ) -> DocumentStatus: ...

    def retrieve(self, **kwargs: object) -> RetrievalResult: ...

    def delete_document(self, dataset_id: str, document_id: str) -> None: ...


def register_document(
    db: Session,
    *,
    dataset_id: str,
    object_storage_file_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    created_by: str,
) -> KnowledgeDocument:
    if db.get(KnowledgeDataset, dataset_id) is None:
        raise ValueError("knowledge dataset does not exist")
    if size_bytes > 100 * 1024 * 1024:
        raise ValueError("knowledge document exceeds the 100 MB limit")
    if not object_storage_file_id or not filename or not content_type or size_bytes < 0:
        raise ValueError("valid knowledge document metadata is required")
    document = KnowledgeDocument(
        dataset_id=dataset_id,
        object_storage_file_id=object_storage_file_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        created_by=created_by,
    )
    db.add(document)
    db.flush()
    return document


def sync_uploaded_document(
    db: Session,
    document_id: str,
    content: bytes,
    adapter: KnowledgeAdapter,
) -> KnowledgeDocument:
    document, dataset = _document_and_dataset(db, document_id)
    if document.status is not KnowledgeDocumentStatus.UPLOADING:
        raise ValueError("document is not awaiting upload")
    if len(content) != document.size_bytes:
        raise ValueError("object content size does not match document metadata")
    document.status = KnowledgeDocumentStatus.SCANNING
    try:
        remote_id = adapter.upload_and_parse(
            dataset_id=dataset.ragflow_dataset_id,
            filename=document.filename,
            content=content,
            content_type=document.content_type,
        )
    except Exception:
        document.status = KnowledgeDocumentStatus.FAILED
        document.failure_reason = "RAGFlow document upload failed"
        db.flush()
        return document
    document.ragflow_document_id = remote_id
    document.status = KnowledgeDocumentStatus.PARSING
    document.failure_reason = None
    db.flush()
    return document


def refresh_document_status(
    db: Session,
    document_id: str,
    adapter: KnowledgeAdapter,
) -> KnowledgeDocument:
    document, dataset = _document_and_dataset(db, document_id)
    if document.ragflow_document_id is None:
        raise ValueError("document has no RAGFlow mapping")
    remote = adapter.get_document_status(
        dataset.ragflow_dataset_id, document.ragflow_document_id
    )
    document.status = KnowledgeDocumentStatus(remote.status)
    document.failure_reason = remote.failure_reason
    db.flush()
    return document


def retrieve_knowledge(
    db: Session,
    question: str,
    dataset_ids: list[str],
    adapter: KnowledgeAdapter,
) -> RetrievalResult:
    datasets = list(
        db.scalars(select(KnowledgeDataset).where(KnowledgeDataset.id.in_(dataset_ids)))
    )
    documents = list(
        db.scalars(
            select(KnowledgeDocument).where(
                KnowledgeDocument.dataset_id.in_(dataset_ids),
                KnowledgeDocument.status == KnowledgeDocumentStatus.READY,
                KnowledgeDocument.ragflow_document_id.is_not(None),
            )
        )
    )
    references = [
        KnowledgeDocumentRef(item.id, str(item.ragflow_document_id), item.status.value)
        for item in documents
    ]
    return adapter.retrieve(
        question=question,
        dataset_ids=[item.ragflow_dataset_id for item in datasets],
        documents=references,
    )


def delete_document(
    db: Session, document_id: str, adapter: KnowledgeAdapter
) -> None:
    document, dataset = _document_and_dataset(db, document_id)
    if document.ragflow_document_id is not None:
        adapter.delete_document(
            dataset.ragflow_dataset_id, document.ragflow_document_id
        )
    db.delete(document)
    db.flush()


def _document_and_dataset(
    db: Session, document_id: str
) -> tuple[KnowledgeDocument, KnowledgeDataset]:
    document = db.get(KnowledgeDocument, document_id)
    if document is None:
        raise ValueError("knowledge document does not exist")
    dataset = db.get(KnowledgeDataset, document.dataset_id)
    if dataset is None:
        raise ValueError("knowledge dataset does not exist")
    return document, dataset
