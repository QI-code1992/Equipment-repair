from sqlalchemy import func, select
from fastapi.testclient import TestClient

from app.core.database import Base
from app.modules.audit.models import AuditEvent
from app.modules.attachments import router as attachment_router
from app.integrations.file_scanning import ScannerUnavailable
from app.main import create_app
from tests.modules.support import create_user_token


class FakeStorage:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.delete_calls: list[str] = []
        self.unavailable = unavailable

    def put(self, **kwargs: object) -> str:
        if self.unavailable:
            raise RuntimeError("storage unavailable")
        self.put_calls.append(kwargs)
        return "knowledge/attachment.png"

    def delete(self, object_key: str) -> None:
        self.delete_calls.append(object_key)


class SafeScanner:
    def __init__(self, *, safe: bool = True, unavailable: bool = False) -> None:
        self.safe = safe
        self.unavailable = unavailable

    def is_safe(self, content: bytes) -> bool:
        if self.unavailable:
            raise ScannerUnavailable("scanner unavailable")
        return self.safe


def build_client(
    *, storage: FakeStorage | None = None, scanner: SafeScanner | None = None
) -> tuple[TestClient, str, FakeStorage]:
    storage = storage or FakeStorage()
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
        knowledge_storage=storage,
        knowledge_scanner=scanner or SafeScanner(),
    )
    Base.metadata.create_all(app.state.engine)
    client = TestClient(app, raise_server_exceptions=False)
    _, token = create_user_token(
        client,
        username="attachment-uploader",
        role_code="LINE_OPERATOR",
        permission_codes=["fault:create"],
    )
    return client, token, storage


def test_attachment_upload_scans_and_returns_reference() -> None:
    client, token, storage = build_client()

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "upload-once"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "object_key": "knowledge/attachment.png",
        "filename": "evidence.png",
        "size_bytes": 11,
        "content_type": "image/png",
    }
    assert storage.put_calls == [
        {
            "filename": "evidence.png",
            "content": b"image-bytes",
            "content_type": "image/png",
        }
    ]


def test_attachment_upload_rejects_disallowed_mime_without_storing() -> None:
    client, token, storage = build_client()

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "bad-mime"},
        files={"file": ("evidence.zip", b"image-bytes", "application/zip")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_INVALID"
    assert storage.put_calls == []


def test_attachment_upload_rejects_infected_content_without_storing() -> None:
    client, token, storage = build_client(scanner=SafeScanner(safe=False))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "infected"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_INFECTED"
    assert storage.put_calls == []


def test_attachment_upload_fails_closed_when_scanner_is_unavailable() -> None:
    client, token, storage = build_client(scanner=SafeScanner(unavailable=True))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "scanner-down"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ATTACHMENT_SCAN_UNAVAILABLE"
    assert storage.put_calls == []


def test_attachment_upload_reports_storage_failure_without_reference() -> None:
    client, token, _ = build_client(storage=FakeStorage(unavailable=True))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "storage-down"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ATTACHMENT_STORAGE_UNAVAILABLE"


def test_attachment_upload_requires_idempotency_key() -> None:
    client, token, storage = build_client()

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 422
    assert storage.put_calls == []


def test_attachment_upload_requires_authenticated_fault_create_permission() -> None:
    client, _, storage = build_client()

    response = client.post(
        "/api/attachments",
        headers={"Idempotency-Key": "unauthenticated"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 401
    assert storage.put_calls == []


def test_attachment_upload_rejects_file_over_configured_size_without_storing(monkeypatch) -> None:
    client, token, storage = build_client()
    monkeypatch.setattr(attachment_router, "MAX_ATTACHMENT_SIZE", 3)

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "too-large"},
        files={"file": ("evidence.png", b"four", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_INVALID"
    assert storage.put_calls == []


def test_attachment_upload_replays_same_key_without_second_object_or_audit() -> None:
    client, token, storage = build_client()
    request = {
        "headers": {"Authorization": f"Bearer {token}", "Idempotency-Key": "replay-upload"},
        "files": {"file": ("evidence.png", b"image-bytes", "image/png")},
    }

    first = client.post("/api/attachments", **request)
    second = client.post("/api/attachments", **request)

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert len(storage.put_calls) == 1
    with client.app.state.session_factory() as db:
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "attachment.upload", AuditEvent.result == "success"
            )
        ) == 1


def test_attachment_upload_rejects_idempotency_key_with_changed_file() -> None:
    client, token, storage = build_client()
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "conflict-upload"}

    first = client.post(
        "/api/attachments", headers=headers,
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )
    second = client.post(
        "/api/attachments", headers=headers,
        files={"file": ("evidence.png", b"different", "image/png")},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert len(storage.put_calls) == 1


def test_attachment_upload_deletes_object_when_success_audit_fails(monkeypatch) -> None:
    client, token, storage = build_client()

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(attachment_router, "write_audit_event", fail_audit)
    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "audit-failure"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert storage.delete_calls == ["knowledge/attachment.png"]
    with client.app.state.session_factory() as db:
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "attachment.upload", AuditEvent.result == "success"
            )
        ) == 0
