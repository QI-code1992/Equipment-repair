from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.integrations.ragflow.adapter import DocumentStatus, RetrievalResult
from app.modules.knowledge import service
from app.modules.knowledge.models import (
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeDocumentStatus,
)
import pytest


class FakeRagflow:
    def __init__(self) -> None:
        self.upload_result: str | Exception = "remote-doc"
        self.status_result = DocumentStatus(status="READY")
        self.retrieval_result = RetrievalResult(no_citation_reason="NO_RETRIEVABLE_EVIDENCE")
        self.retrieval_documents = []
        self.deleted: tuple[str, str] | None = None

    def upload_and_parse(self, **kwargs: object) -> str:
        if isinstance(self.upload_result, Exception):
            raise self.upload_result
        return self.upload_result

    def get_document_status(self, dataset_id: str, document_id: str) -> DocumentStatus:
        return self.status_result

    def retrieve(self, **kwargs: object) -> RetrievalResult:
        self.retrieval_documents = list(kwargs["documents"])
        return self.retrieval_result

    def delete_document(self, dataset_id: str, document_id: str) -> None:
        self.deleted = (dataset_id, document_id)


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def create_dataset(db: Session) -> KnowledgeDataset:
    dataset = KnowledgeDataset(name="maintenance manuals", ragflow_dataset_id="remote-dataset")
    db.add(dataset)
    db.flush()
    return dataset


def test_register_document_keeps_business_and_object_storage_references() -> None:
    with build_session() as db:
        dataset = create_dataset(db)

        document = service.register_document(
            db,
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            filename="loader-manual.pdf",
            content_type="application/pdf",
            size_bytes=2048,
            created_by="operator-1",
        )

        assert document.status is KnowledgeDocumentStatus.UPLOADING
        assert document.object_storage_file_id == "object-123"
        assert document.ragflow_document_id is None
        assert document.failure_reason is None


def test_register_document_rejects_file_larger_than_100_mb() -> None:
    with build_session() as db:
        dataset = create_dataset(db)

        with pytest.raises(ValueError, match="100 MB"):
            service.register_document(
                db,
                dataset_id=dataset.id,
                object_storage_file_id="object-large",
                filename="large.pdf",
                content_type="application/pdf",
                size_bytes=100 * 1024 * 1024 + 1,
                created_by="operator-1",
            )


def test_worker_uploads_scanned_content_and_records_remote_mapping() -> None:
    adapter = FakeRagflow()
    with build_session() as db:
        dataset = create_dataset(db)
        document = service.register_document(
            db,
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            filename="manual.txt",
            content_type="text/plain",
            size_bytes=8,
            created_by="operator-1",
        )

        service.sync_uploaded_document(db, document.id, b"guidance", adapter)

        assert document.status is KnowledgeDocumentStatus.PARSING
        assert document.ragflow_document_id == "remote-doc"


def test_worker_rejects_content_that_does_not_match_object_metadata() -> None:
    adapter = FakeRagflow()
    with build_session() as db:
        dataset = create_dataset(db)
        document = service.register_document(
            db,
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            filename="manual.txt",
            content_type="text/plain",
            size_bytes=8,
            created_by="operator-1",
        )

        with pytest.raises(ValueError, match="size does not match"):
            service.sync_uploaded_document(db, document.id, b"short", adapter)

        assert document.status is KnowledgeDocumentStatus.UPLOADING


def test_worker_persists_safe_failure_without_remote_identifier() -> None:
    adapter = FakeRagflow()
    adapter.upload_result = RuntimeError("Authorization: Bearer secret-value")
    with build_session() as db:
        dataset = create_dataset(db)
        document = service.register_document(
            db,
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            filename="manual.txt",
            content_type="text/plain",
            size_bytes=8,
            created_by="operator-1",
        )

        service.sync_uploaded_document(db, document.id, b"guidance", adapter)

        assert document.status is KnowledgeDocumentStatus.FAILED
        assert document.failure_reason == "RAGFlow document upload failed"
        assert "secret-value" not in document.failure_reason


def test_status_refresh_persists_ready_and_failed_states() -> None:
    adapter = FakeRagflow()
    with build_session() as db:
        dataset = create_dataset(db)
        document = KnowledgeDocument(
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            ragflow_document_id="remote-doc",
            filename="manual.txt",
            content_type="text/plain",
            size_bytes=8,
            status=KnowledgeDocumentStatus.PARSING,
            created_by="operator-1",
        )
        db.add(document)
        db.flush()

        service.refresh_document_status(db, document.id, adapter)
        assert document.status is KnowledgeDocumentStatus.READY

        adapter.status_result = DocumentStatus(status="FAILED", failure_reason="parse failed")
        service.refresh_document_status(db, document.id, adapter)
        assert document.status is KnowledgeDocumentStatus.FAILED
        assert document.failure_reason == "parse failed"


def test_retrieval_passes_only_ready_documents_to_adapter() -> None:
    adapter = FakeRagflow()
    with build_session() as db:
        dataset = create_dataset(db)
        db.add_all(
            [
                KnowledgeDocument(
                    dataset_id=dataset.id,
                    object_storage_file_id="object-ready",
                    ragflow_document_id="remote-ready",
                    filename="ready.txt",
                    content_type="text/plain",
                    size_bytes=5,
                    status=KnowledgeDocumentStatus.READY,
                    created_by="operator-1",
                ),
                KnowledgeDocument(
                    dataset_id=dataset.id,
                    object_storage_file_id="object-failed",
                    ragflow_document_id="remote-failed",
                    filename="failed.txt",
                    content_type="text/plain",
                    size_bytes=6,
                    status=KnowledgeDocumentStatus.FAILED,
                    failure_reason="parse failed",
                    created_by="operator-1",
                ),
            ]
        )
        db.flush()

        service.retrieve_knowledge(db, "inspection", [dataset.id], adapter)

        assert [item.business_document_id for item in adapter.retrieval_documents] == [
            db.scalar(
                select(KnowledgeDocument.id).where(KnowledgeDocument.filename == "ready.txt")
            )
        ]


def test_delete_removes_remote_document_before_business_metadata() -> None:
    adapter = FakeRagflow()
    with build_session() as db:
        dataset = create_dataset(db)
        document = KnowledgeDocument(
            dataset_id=dataset.id,
            object_storage_file_id="object-123",
            ragflow_document_id="remote-doc",
            filename="manual.txt",
            content_type="text/plain",
            size_bytes=8,
            status=KnowledgeDocumentStatus.READY,
            created_by="operator-1",
        )
        db.add(document)
        db.flush()
        document_id = document.id

        service.delete_document(db, document_id, adapter)

        assert adapter.deleted == ("remote-dataset", "remote-doc")
        assert db.get(KnowledgeDocument, document_id) is None
