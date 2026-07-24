from pathlib import Path

from fastapi.testclient import TestClient

from app.integrations.ragflow.adapter import RagflowAdapter
from app.main import create_app


def test_api_image_includes_database_migrations() -> None:
    dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text()

    assert "COPY alembic.ini ./" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile


def test_healthz_reports_unavailable_when_application_is_not_configured() -> None:
    response = TestClient(
        create_app(
            service_name=None,
            postgres_dsn="postgresql://postgres/app",
            redis_url="redis://redis:6379/0",
        )
    ).get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "missing": ["application"]}


def test_healthz_reports_unavailable_when_postgres_is_not_configured() -> None:
    response = TestClient(create_app(postgres_dsn=None, redis_url="redis://redis:6379/0")).get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "missing": ["postgres"]}


def test_healthz_reports_unavailable_when_redis_is_not_configured() -> None:
    response = TestClient(create_app(postgres_dsn="postgresql://postgres/app", redis_url=None)).get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "missing": ["redis"]}


def test_healthz_reports_ok_when_application_dependencies_are_configured() -> None:
    response = TestClient(
        create_app(postgres_dsn="postgresql://postgres/app", redis_url="redis://redis:6379/0")
    ).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "equipment-operations-platform"}


def test_app_factory_builds_ragflow_adapter_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("RAGFLOW_BASE_URL", "http://ragflow:9380")
    monkeypatch.setenv("RAGFLOW_API_KEY", "test-key")
    monkeypatch.setenv("RAGFLOW_TIMEOUT_SECONDS", "7.5")

    app = create_app(
        postgres_dsn="postgresql://postgres/app",
        redis_url="redis://redis:6379/0",
    )

    assert isinstance(app.state.knowledge_adapter, RagflowAdapter)
    assert app.state.knowledge_adapter.base_url == "http://ragflow:9380"
    assert app.state.knowledge_adapter.timeout_seconds == 7.5
