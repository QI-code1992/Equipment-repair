import os

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect


POSTGRES_DSN = os.getenv("TASK005_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN or os.getenv("TASK005_ALLOW_DESTRUCTIVE_TESTS") != "1",
    reason="dedicated DSN and TASK005_ALLOW_DESTRUCTIVE_TESTS=1 are required",
)


def test_task005_postgres_upgrade_downgrade_upgrade() -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", POSTGRES_DSN)
    engine = create_engine(POSTGRES_DSN)
    config.attributes["connection"] = engine.connect()
    try:
        command.upgrade(config, "0006_task005")
        assert {"file_objects", "knowledge_datasets", "knowledge_documents", "knowledge_citations"} <= set(inspect(engine).get_table_names())
        command.downgrade(config, "0005_task007")
        assert "knowledge_documents" not in set(inspect(engine).get_table_names())
        command.upgrade(config, "0006_task005")
        assert "knowledge_documents" in set(inspect(engine).get_table_names())
    finally:
        config.attributes["connection"].close()
