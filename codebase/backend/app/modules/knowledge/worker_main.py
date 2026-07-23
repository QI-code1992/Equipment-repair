import argparse
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
import json
import os

from sqlalchemy.orm import Session

from app.core.database import create_database_engine, session_factory
from app.integrations.object_storage import MinioObjectStorage, build_minio_storage
from app.integrations.ragflow import RagflowAdapter, UrllibRagflowTransport
from app.modules.knowledge import worker


_REQUIRED_SETTINGS = (
    "POSTGRES_DSN",
    "MINIO_ENDPOINT",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "MINIO_BUCKET",
    "RAGFLOW_BASE_URL",
    "RAGFLOW_API_KEY",
)


@contextmanager
def worker_runtime() -> Iterator[tuple[Session, MinioObjectStorage, RagflowAdapter]]:
    missing = [name for name in _REQUIRED_SETTINGS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"missing worker settings: {', '.join(missing)}")

    postgres_dsn = os.environ["POSTGRES_DSN"]
    endpoint = os.environ["MINIO_ENDPOINT"]
    access_key = os.environ["MINIO_ACCESS_KEY"]
    secret_key = os.environ["MINIO_SECRET_KEY"]
    bucket = os.environ["MINIO_BUCKET"]
    base_url = os.environ["RAGFLOW_BASE_URL"]
    api_key = os.environ["RAGFLOW_API_KEY"]
    timeout = float(os.getenv("RAGFLOW_TIMEOUT_SECONDS", "30"))
    if timeout <= 0:
        raise RuntimeError("RAGFLOW_TIMEOUT_SECONDS must be positive")

    engine = create_database_engine(postgres_dsn)
    storage = build_minio_storage(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket,
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )
    transport = UrllibRagflowTransport(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
    )
    adapter = RagflowAdapter(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
        transport=transport,
    )
    try:
        with session_factory(engine)() as db:
            yield db, storage, adapter
    finally:
        engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronize pending knowledge documents")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    with worker_runtime() as (db, storage, adapter):
        result = worker.sync_pending_documents(db, storage, adapter, limit=args.limit)
        db.commit()
    print(json.dumps(result.__dict__, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
