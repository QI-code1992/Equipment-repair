from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


BACKEND_DIR = Path(__file__).parents[2]


def test_task005_upgrade_creates_knowledge_lifecycle_tables(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'task005.sqlite3').as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    engine = create_engine(database_url)
    config.attributes["connection"] = engine.connect()
    try:
        command.upgrade(config, "0006_task005")
        inspector = inspect(engine)
        assert {
            "file_objects",
            "knowledge_datasets",
            "knowledge_documents",
            "knowledge_citations",
        } <= set(inspector.get_table_names())
        assert "ix_knowledge_documents_dataset_id" in {
            index["name"] for index in inspector.get_indexes("knowledge_documents")
        }
        assert "ix_knowledge_citations_document_id" in {
            index["name"] for index in inspector.get_indexes("knowledge_citations")
        }
    finally:
        config.attributes["connection"].close()
