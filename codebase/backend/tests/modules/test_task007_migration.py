from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


BACKEND_DIR = Path(__file__).parents[2]


def test_task007_upgrade_creates_runtime_and_checkpoint_tables(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'task007.sqlite3').as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    engine = create_engine(database_url)
    config.attributes["connection"] = engine.connect()
    try:
        command.upgrade(config, "0005_task007")
        tables = set(inspect(engine).get_table_names())
        assert {
            "agent_threads",
            "agent_runs",
            "agent_tool_calls",
            "agent_confirmations",
        } <= tables
        assert {column["name"] for column in inspect(engine).get_columns("agent_runs")} >= {
            "config_snapshot_json", "state_json", "thread_id"
        }
        assert "checkpoint_ref" in {
            column["name"] for column in inspect(engine).get_columns("agent_threads")
        }
    finally:
        config.attributes["connection"].close()
