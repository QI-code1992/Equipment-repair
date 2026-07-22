from fastapi.testclient import TestClient

from app.core.database import Base
from app.integrations.file_scanning import ScannerUnavailable
from app.main import create_app
from app.modules.knowledge.models import KnowledgeDataset, KnowledgeDocument
from tests.modules.support import create_user_token


class FakeStorage:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.deleted: list[str] = []

    def put(self, **kwargs: object) -> str:
        self.put_calls.append(kwargs)
        return "knowledge/stored.txt"

    def delete(self, object_key: str) -> None:
        self.deleted.append(object_key)


class FakeScanner:
    def __init__(self, safe: bool = True, unavailable: bool = False) -> None:
        self.safe = safe
        self.unavailable = unavailable
        self.scanned: list[bytes] = []

    def is_safe(self, content: bytes) -> bool:
        self.scanned.append(content)
        if self.unavailable:
            raise ScannerUnavailable("scanner address is secret")
        return self.safe


def build_knowledge_client(
    *, storage: FakeStorage | None = None, scanner: FakeScanner | None = None
) -> tuple[TestClient, str, FakeStorage, FakeScanner]:
    storage = storage or FakeStorage()
    scanner = scanner or FakeScanner()
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
        knowledge_storage=storage,
        knowledge_scanner=scanner,
    )
    Base.metadata.create_all(app.state.engine)
    client = TestClient(app)
    _, token = create_user_token(
        client,
        username="knowledge-admin",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )
    with app.state.session_factory() as db:
        dataset = KnowledgeDataset(
            name="maintenance manuals", ragflow_dataset_id="remote-dataset"
        )
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id
    return client, dataset_id, storage, scanner


def test_upload_creates_scanned_file_metadata_and_document() -> None:
    client, dataset_id, storage, scanner = build_knowledge_client()

    response = client.post(
        "/api/knowledge/documents",
        headers={"Authorization": "Bearer " + client.post(
            "/api/auth/login",
            json={"username": "knowledge-admin", "password": "correct-password"},
        ).json()["access_token"], "Idempotency-Key": "upload-1"},
        data={"dataset_id": dataset_id},
        files={"file": ("manual.txt", b"guidance", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "UPLOADING"
    assert body["filename"] == "manual.txt"
    assert body["size_bytes"] == 8
    assert body["failure_reason"] is None
    assert scanner.scanned == [b"guidance"]
    assert storage.put_calls[0]["content"] == b"guidance"
    with client.app.state.session_factory() as db:
        document = db.get(KnowledgeDocument, body["id"])
        assert document is not None
        assert document.object_storage_file_id == body["file_id"]


def test_upload_is_idempotent_without_duplicate_storage_write() -> None:
    client, dataset_id, storage, _ = build_knowledge_client()
    _, token = create_user_token(
        client,
        username="knowledge-admin-2",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )
    request = {
        "headers": {"Authorization": f"Bearer {token}", "Idempotency-Key": "same-upload"},
        "data": {"dataset_id": dataset_id},
        "files": {"file": ("manual.txt", b"guidance", "text/plain")},
    }

    first = client.post("/api/knowledge/documents", **request)
    second = client.post("/api/knowledge/documents", **request)

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert len(storage.put_calls) == 1


def test_upload_rejects_unsafe_file_without_storing_it() -> None:
    storage, scanner = FakeStorage(), FakeScanner(safe=False)
    client, dataset_id, _, _ = build_knowledge_client(storage=storage, scanner=scanner)
    _, token = create_user_token(
        client,
        username="unsafe-uploader",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )

    response = client.post(
        "/api/knowledge/documents",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "unsafe-1"},
        data={"dataset_id": dataset_id},
        files={"file": ("manual.txt", b"malware!", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "KNOWLEDGE_FILE_UNSAFE"
    assert storage.put_calls == []


def test_upload_requires_configured_scanner() -> None:
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
        knowledge_storage=FakeStorage(),
    )
    Base.metadata.create_all(app.state.engine)
    client = TestClient(app, raise_server_exceptions=False)
    _, token = create_user_token(
        client,
        username="no-scanner",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )

    response = client.post(
        "/api/knowledge/documents",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "no-scan"},
        data={"dataset_id": "missing"},
        files={"file": ("manual.txt", b"guidance", "text/plain")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "KNOWLEDGE_SCANNER_UNAVAILABLE"


def test_upload_fails_closed_when_scanner_cannot_respond() -> None:
    client, dataset_id, storage, _ = build_knowledge_client(
        scanner=FakeScanner(unavailable=True)
    )
    _, token = create_user_token(
        client,
        username="scanner-down",
        role_code="SYSTEM_ADMIN",
        permission_codes=["intelligence:knowledge"],
    )

    response = client.post(
        "/api/knowledge/documents",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "scan-down"},
        data={"dataset_id": dataset_id},
        files={"file": ("manual.txt", b"guidance", "text/plain")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "KNOWLEDGE_SCANNER_UNAVAILABLE"
    assert "secret" not in response.text
    assert storage.put_calls == []
