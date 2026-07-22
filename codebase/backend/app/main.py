from fastapi import FastAPI
from fastapi import Response

from app.core.config import Settings
from app.core.database import create_database_engine, session_factory
from app.integrations.file_scanning import ClamAvScanner
from app.integrations.object_storage import build_minio_storage
from app.modules.audit.http import register_audit_exception_handlers
from app.modules.equipment.router import router as equipment_router
from app.modules.equipment.organization_router import router as organization_router
from app.modules.identity.router import router as identity_router
from app.modules.identity.admin_router import router as identity_admin_router
from app.modules.maintenance.router import router as maintenance_router
from app.modules.knowledge.router import router as knowledge_router


def create_app(
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    service_name: str | None = "equipment-operations-platform",
    knowledge_storage: object | None = None,
    knowledge_scanner: object | None = None,
) -> FastAPI:
    environment = Settings.from_environment()
    settings = Settings(
        postgres_dsn=postgres_dsn if postgres_dsn is not None else environment.postgres_dsn,
        redis_url=redis_url if redis_url is not None else environment.redis_url,
        service_name=service_name,
        minio_endpoint=environment.minio_endpoint,
        minio_access_key=environment.minio_access_key,
        minio_secret_key=environment.minio_secret_key,
        minio_bucket=environment.minio_bucket,
        minio_secure=environment.minio_secure,
        clamav_host=environment.clamav_host,
        clamav_port=environment.clamav_port,
        file_scan_timeout_seconds=environment.file_scan_timeout_seconds,
    )
    app = FastAPI(title=settings.service_name or "unconfigured-application")
    if knowledge_storage is None and all(
        (
            settings.minio_endpoint,
            settings.minio_access_key,
            settings.minio_secret_key,
            settings.minio_bucket,
        )
    ):
        knowledge_storage = build_minio_storage(
            endpoint=str(settings.minio_endpoint),
            access_key=str(settings.minio_access_key),
            secret_key=str(settings.minio_secret_key),
            bucket_name=str(settings.minio_bucket),
            secure=settings.minio_secure,
        )
    if knowledge_scanner is None and settings.clamav_host:
        knowledge_scanner = ClamAvScanner(
            host=settings.clamav_host,
            port=settings.clamav_port,
            timeout_seconds=settings.file_scan_timeout_seconds,
        )
    app.state.knowledge_storage = knowledge_storage
    app.state.knowledge_scanner = knowledge_scanner
    if settings.postgres_dsn:
        app.state.engine = create_database_engine(settings.postgres_dsn)
        app.state.session_factory = session_factory(app.state.engine)
    app.include_router(identity_router)
    app.include_router(identity_admin_router)
    app.include_router(equipment_router)
    app.include_router(organization_router)
    app.include_router(maintenance_router)
    app.include_router(knowledge_router)
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
