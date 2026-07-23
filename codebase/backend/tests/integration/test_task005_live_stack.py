"""Opt-in TASK-005 validation against PostgreSQL, MinIO, ClamAV and RAGFlow.

DEV-001 supplies a dedicated database and disposable RAGFlow dataset. Ordinary
test runs skip this module, and no credentials are stored in the repository.
"""

import os
import time
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect

from app.core.database import create_database_engine, session_factory
from app.integrations.file_scanning import ClamAvScanner
from app.integrations.object_storage import build_minio_storage
from app.integrations.ragflow import RagflowAdapter, UrllibRagflowTransport
from app.main import create_app
from app.modules.knowledge import service, worker
from app.modules.knowledge.models import FileObject, KnowledgeDataset, KnowledgeDocument
from tests.modules.support import create_user_token


REQUIRED_ENV = (
    "TASK005_POSTGRES_DSN",
    "TASK005_MINIO_ENDPOINT",
    "TASK005_MINIO_ACCESS_KEY",
    "TASK005_MINIO_SECRET_KEY",
    "TASK005_MINIO_BUCKET",
    "TASK005_CLAMAV_HOST",
    "TASK005_RAGFLOW_BASE_URL",
    "TASK005_RAGFLOW_API_KEY",
    "TASK005_RAGFLOW_DATASET_ID",
)
MISSING_ENV = [name for name in REQUIRED_ENV if not os.getenv(name)]
pytestmark = pytest.mark.skipif(
    os.getenv("TASK005_ALLOW_LIVE_TESTS") != "1" or bool(MISSING_ENV),
    reason="TASK005_ALLOW_LIVE_TESTS=1 and dedicated live-stack settings are required",
)


def _setting(name: str) -> str:
    return os.environ[name]


def _require_dedicated_database() -> str:
    dsn = _setting("TASK005_POSTGRES_DSN")
    database = dsn.rsplit("/", 1)[-1].split("?", 1)[0]
    if not database.startswith("equipment_task5_validation"):
        raise RuntimeError("TASK-005 requires a dedicated validation database")
    return dsn


def _ragflow_adapter() -> RagflowAdapter:
    base_url = _setting("TASK005_RAGFLOW_BASE_URL")
    api_key = _setting("TASK005_RAGFLOW_API_KEY")
    timeout = float(os.getenv("TASK005_RAGFLOW_TIMEOUT_SECONDS", "30"))
    transport = UrllibRagflowTransport(
        base_url=base_url, api_key=api_key, timeout_seconds=timeout
    )
    return RagflowAdapter(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
        transport=transport,
    )


def test_task005_live_document_lifecycle() -> None:
    dsn = _require_dedicated_database()
    engine = create_database_engine(dsn)
    required_tables = {
        "knowledge_datasets",
        "knowledge_documents",
        "knowledge_citations",
    }
    assert required_tables <= set(inspect(engine).get_table_names())

    storage = build_minio_storage(
        endpoint=_setting("TASK005_MINIO_ENDPOINT"),
        access_key=_setting("TASK005_MINIO_ACCESS_KEY"),
        secret_key=_setting("TASK005_MINIO_SECRET_KEY"),
        bucket_name=_setting("TASK005_MINIO_BUCKET"),
        secure=os.getenv("TASK005_MINIO_SECURE", "false").lower() == "true",
    )
    scanner = ClamAvScanner(
        host=_setting("TASK005_CLAMAV_HOST"),
        port=int(os.getenv("TASK005_CLAMAV_PORT", "3310")),
        timeout_seconds=float(os.getenv("TASK005_CLAMAV_TIMEOUT_SECONDS", "10")),
    )
    adapter = _ragflow_adapter()
    app = create_app(
        postgres_dsn=dsn,
        redis_url=os.getenv("TASK005_REDIS_URL", "redis://redis:6379/0"),
        knowledge_storage=storage,
        knowledge_scanner=scanner,
    )
    client = TestClient(app)
    suffix = uuid4().hex
    dataset = KnowledgeDataset(
        name=f"task005-live-{suffix}",
        ragflow_dataset_id=_setting("TASK005_RAGFLOW_DATASET_ID"),
    )
    with app.state.session_factory() as db:
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id
    _, token = create_user_token(
        client,
        username=f"task005-live-{suffix}",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )
    headers = {"Authorization": f"Bearer {token}"}
    document_id = file_id = object_key = remote_id = None
    try:
        unsafe = client.post(
            "/api/knowledge/documents",
            headers={**headers, "Idempotency-Key": f"unsafe-{suffix}"},
            data={"dataset_id": dataset_id},
            files={
                "file": (
                    "eicar.txt",
                    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
                    "text/plain",
                )
            },
        )
        assert unsafe.status_code == 422
        assert unsafe.json()["detail"]["code"] == "KNOWLEDGE_FILE_UNSAFE"

        marker = f"TASK005 hydraulic pressure guidance {suffix}"
        upload = client.post(
            "/api/knowledge/documents",
            headers={**headers, "Idempotency-Key": f"upload-{suffix}"},
            data={"dataset_id": dataset_id},
            files={"file": ("manual.txt", marker.encode(), "text/plain")},
        )
        assert upload.status_code == 201
        document_id = str(upload.json()["id"])
        file_id = str(upload.json()["file_id"])

        factory = session_factory(engine)
        deadline = time.monotonic() + float(os.getenv("TASK005_READY_TIMEOUT_SECONDS", "180"))
        status = "UPLOADING"
        while time.monotonic() < deadline and status != "READY":
            with factory() as db:
                worker.sync_pending_documents(db, storage, adapter, limit=1)
                db.commit()
                document = db.get(KnowledgeDocument, document_id)
                assert document is not None
                status = document.status.value
                remote_id = document.ragflow_document_id
                file_object = db.get(FileObject, file_id)
                assert file_object is not None
                object_key = file_object.object_key
            if status != "READY":
                time.sleep(2)
        assert status == "READY"

        with factory() as db:
            result = service.retrieve_knowledge(db, marker, [dataset_id], adapter)
        assert result.unavailable is False
        assert result.citations
        assert all(item.business_document_id == document_id for item in result.citations)
        assert all(item.chunk_id for item in result.citations)
    finally:
        with session_factory(engine)() as db:
            document = db.get(KnowledgeDocument, document_id) if document_id else None
            if document is not None:
                db.delete(document)
            file_object = db.get(FileObject, file_id) if file_id else None
            if file_object is not None:
                db.delete(file_object)
            stored_dataset = db.get(KnowledgeDataset, dataset_id)
            if stored_dataset is not None:
                db.delete(stored_dataset)
            db.commit()
        if remote_id:
            adapter.delete_document(_setting("TASK005_RAGFLOW_DATASET_ID"), remote_id)
        if object_key:
            storage.delete(object_key)
        client.close()
        app.state.engine.dispose()
        engine.dispose()
