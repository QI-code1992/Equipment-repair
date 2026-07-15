from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_settings_expose_stable_service_identity() -> None:
    settings = Settings()

    assert settings.service_name == "equipment-operations-platform"


def test_healthz_reports_application_status_without_dependencies() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "equipment-operations-platform",
    }
