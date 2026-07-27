from fastapi.testclient import TestClient

from app.core.database import Base
from app.integrations.file_scanning import ScannerUnavailable
from app.main import create_app
from tests.modules.support import create_user_token


class FakeStorage:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.unavailable = unavailable

    def put(self, **kwargs: object) -> str:
        if self.unavailable:
            raise RuntimeError("storage unavailable")
        self.put_calls.append(kwargs)
        return "knowledge/attachment.png"


class SafeScanner:
    def __init__(self, *, safe: bool = True, unavailable: bool = False) -> None:
        self.safe = safe
        self.unavailable = unavailable

    def is_safe(self, content: bytes) -> bool:
        if self.unavailable:
            raise ScannerUnavailable("scanner unavailable")
        return self.safe and content == b"image-bytes"


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
        headers={"Authorization": f"Bearer {token}"},
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
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence.zip", b"image-bytes", "application/zip")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_INVALID"
    assert storage.put_calls == []


def test_attachment_upload_rejects_infected_content_without_storing() -> None:
    client, token, storage = build_client(scanner=SafeScanner(safe=False))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ATTACHMENT_INFECTED"
    assert storage.put_calls == []


def test_attachment_upload_fails_closed_when_scanner_is_unavailable() -> None:
    client, token, storage = build_client(scanner=SafeScanner(unavailable=True))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ATTACHMENT_SCAN_UNAVAILABLE"
    assert storage.put_calls == []


def test_attachment_upload_reports_storage_failure_without_reference() -> None:
    client, token, _ = build_client(storage=FakeStorage(unavailable=True))

    response = client.post(
        "/api/attachments",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evidence.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ATTACHMENT_STORAGE_UNAVAILABLE"
