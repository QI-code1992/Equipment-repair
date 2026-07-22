from fastapi import FastAPI
from fastapi import Response

from app.core.config import Settings
from app.core.database import create_database_engine, session_factory
from app.modules.audit.http import register_audit_exception_handlers
from app.modules.equipment.router import router as equipment_router
from app.modules.equipment.organization_router import router as organization_router
from app.modules.identity.router import router as identity_router
from app.modules.identity.admin_router import router as identity_admin_router
from app.modules.agent_config.router import router as agent_config_router
from app.modules.maintenance.router import router as maintenance_router


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
    app.include_router(identity_admin_router)
    app.include_router(agent_config_router)
    app.include_router(equipment_router)
    app.include_router(organization_router)
    app.include_router(maintenance_router)
    register_audit_exception_handlers(app)

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
