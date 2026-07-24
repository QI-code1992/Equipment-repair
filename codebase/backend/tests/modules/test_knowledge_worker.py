from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.integrations.ragflow.adapter import DocumentStatus
from app.modules.knowledge import worker
from app.modules.knowledge.models import (
    FileObject,
    FileScanStatus,
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeDocumentStatus,
)


class FakeStorage:
    def __init__(self, content: bytes = b"guidance") -> None:
        self.content = content
        self.keys: list[str] = []

    def get(self, object_key: str) -> bytes:
        self.keys.append(object_key)
        return self.content


class FakeAdapter:
    def __init__(self) -> None:
        self.uploads: list[dict[str, object]] = []
        self.status = DocumentStatus(status="READY")

    def upload_and_parse(self, **kwargs: object) -> str:
        self.uploads.append(kwargs)
        return "remote-doc"

    def get_document_status(self, dataset_id: str, document_id: str) -> DocumentStatus:
        return self.status


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def create_document(db: Session, status: KnowledgeDocumentStatus) -> KnowledgeDocument:
    dataset = KnowledgeDataset(name="manuals", ragflow_dataset_id="remote-dataset")
    db.add(dataset)
    db.flush()
    file_object = FileObject(
        object_key="knowledge/file.txt",
        filename="file.txt",
        content_type="text/plain",
        size_bytes=8,
        sha256="a" * 64,
        scan_status=FileScanStatus.CLEAN,
        created_by="operator",
    )
    db.add(file_object)
    db.flush()
    document = KnowledgeDocument(
        dataset_id=dataset.id,
        object_storage_file_id=file_object.id,
        ragflow_document_id=None if status is KnowledgeDocumentStatus.UPLOADING else "remote-doc",
        filename="file.txt",
        content_type="text/plain",
        size_bytes=8,
        status=status,
        created_by="operator",
    )
    db.add(document)
    db.flush()
    return document


def test_worker_uploads_pending_clean_document() -> None:
    storage, adapter = FakeStorage(), FakeAdapter()
    with build_session() as db:
        document = create_document(db, KnowledgeDocumentStatus.UPLOADING)

        result = worker.sync_pending_documents(db, storage, adapter)

        assert result == worker.WorkerResult(uploaded=1, refreshed=0, failed=0)
        assert document.status is KnowledgeDocumentStatus.PARSING
        assert storage.keys == ["knowledge/file.txt"]
        assert adapter.uploads[0]["content"] == b"guidance"


def test_worker_refreshes_parsing_document_to_ready() -> None:
    storage, adapter = FakeStorage(), FakeAdapter()
    with build_session() as db:
        document = create_document(db, KnowledgeDocumentStatus.PARSING)

        result = worker.sync_pending_documents(db, storage, adapter)

        assert result == worker.WorkerResult(uploaded=0, refreshed=1, failed=0)
        assert document.status is KnowledgeDocumentStatus.READY


def test_worker_records_safe_failure_when_object_storage_is_unavailable() -> None:
    class BrokenStorage(FakeStorage):
        def get(self, object_key: str) -> bytes:
            raise OSError("secret storage endpoint")

    with build_session() as db:
        document = create_document(db, KnowledgeDocumentStatus.UPLOADING)

        result = worker.sync_pending_documents(db, BrokenStorage(), FakeAdapter())

        assert result == worker.WorkerResult(uploaded=0, refreshed=0, failed=1)
        assert document.status is KnowledgeDocumentStatus.FAILED
        assert document.failure_reason == "object storage read failed"
