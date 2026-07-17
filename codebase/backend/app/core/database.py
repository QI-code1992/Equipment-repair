from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def create_database_engine(database_url: str) -> Engine:
    normalized_url = normalize_database_url(database_url)
    options: dict[str, object] = {"pool_pre_ping": True}
    if normalized_url == "sqlite+pysqlite:///:memory:":
        options.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(normalized_url, **options)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
