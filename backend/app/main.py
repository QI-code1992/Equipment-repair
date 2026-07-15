from fastapi import FastAPI, Response
from fastapi import FastAPI

from app.core.config import Settings


def create_app(
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    service_name: str | None = "equipment-operations-platform",
) -> FastAPI:
    environment = Settings.from_environment()
    settings = Settings(
        postgres_dsn=postgres_dsn if postgres_dsn is not None else environment.postgres_dsn,
        redis_url=redis_url if redis_url is not None else environment.redis_url,
        service_name=service_name,
    )
    app = FastAPI(title=settings.service_name or "unconfigured-application")

    @app.get("/healthz")
    def healthz(response: Response) -> dict[str, object]:
        missing = [
            name
            for name, value in (
                ("application", settings.service_name),
                ("postgres", settings.postgres_dsn),
                ("redis", settings.redis_url),
            )
            if not value
        ]
        if missing:
            response.status_code = 503
            return {"status": "unavailable", "missing": missing}
def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.service_name)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
