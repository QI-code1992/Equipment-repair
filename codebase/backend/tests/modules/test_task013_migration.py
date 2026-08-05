from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


BACKEND_DIR = Path(__file__).parents[2]


def test_task013_upgrade_and_downgrade_notification_schema(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'task013.sqlite3').as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    engine = create_engine(database_url)
    config.attributes["connection"] = engine.connect()
    try:
        command.upgrade(config, "0007_task013_notifications")
        inspector = inspect(engine)
        assert {"notifications", "notification_reads"} <= set(inspector.get_table_names())
        assert {
            "id", "type", "title", "body", "level", "action_url", "created_at"
        } <= {column["name"] for column in inspector.get_columns("notifications")}
        assert {
            "id", "notification_id", "user_id", "read_at"
        } <= {column["name"] for column in inspector.get_columns("notification_reads")}
        assert {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints("notification_reads")
        } >= {("notification_id", "user_id")}

        command.downgrade(config, "0006_task005")
        remaining = set(inspect(engine).get_table_names())
        assert {"notifications", "notification_reads"}.isdisjoint(remaining)
    finally:
        config.attributes["connection"].close()
