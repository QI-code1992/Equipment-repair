from fastapi.testclient import TestClient

from app.main import create_app


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
