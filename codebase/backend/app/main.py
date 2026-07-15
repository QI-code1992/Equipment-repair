from fastapi import FastAPI
from fastapi import Response

from app.core.config import Settings
from app.core.database import create_database_engine, session_factory
from app.modules.equipment.router import router as equipment_router
from app.modules.identity.router import router as identity_router


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
    if settings.postgres_dsn:
        app.state.engine = create_database_engine(settings.postgres_dsn)
        app.state.session_factory = session_factory(app.state.engine)
    app.include_router(identity_router)
    app.include_router(equipment_router)

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

        return {"status": "ok", "service": settings.service_name}

    return app


app = create_app()
