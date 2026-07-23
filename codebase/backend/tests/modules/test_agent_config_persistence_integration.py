from pathlib import Path
import subprocess
import sys
import textwrap

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import Base, create_database_engine


def test_database_engine_factory_preserves_sqlite_and_postgresql_contracts(tmp_path) -> None:
    sqlite_engine = create_database_engine(
        f"sqlite+pysqlite:///{tmp_path / 'foreign-keys.db'}"
    )
    Base.metadata.create_all(sqlite_engine)
    try:
        with (
            sqlite_engine.connect() as first_connection,
            sqlite_engine.connect() as second_connection,
        ):
            assert first_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert second_connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        with sqlite_engine.begin() as connection:
            with pytest.raises(IntegrityError):
                connection.execute(
                    text(
                        "INSERT INTO model_bindings "
                        "(id, provider_id, name, model_name) VALUES "
                        "('binding-1', 'missing-provider', 'Binding', 'model-v1')"
                    )
                )
    finally:
        Base.metadata.drop_all(sqlite_engine)
        sqlite_engine.dispose()

    postgresql_engine = create_database_engine(
        "postgresql+psycopg://task006@db.example.test:5433/equipment"
        "?application_name=task006&connect_timeout=4&sslmode=require"
    )
    try:
        assert postgresql_engine.dialect.name == "postgresql"
        assert postgresql_engine.url.drivername == "postgresql+psycopg"
        assert postgresql_engine.url.host == "db.example.test"
        assert postgresql_engine.url.port == 5433
        assert postgresql_engine.url.database == "equipment"
        assert dict(postgresql_engine.url.query) == {
            "application_name": "task006",
            "connect_timeout": "4",
            "sslmode": "require",
        }
        assert postgresql_engine.pool._pre_ping is True
        assert all(
            "PRAGMA foreign_keys=ON"
            not in getattr(getattr(listener, "__code__", None), "co_consts", ())
            for listener in postgresql_engine.pool.dispatch.connect.listeners
        )
    finally:
        postgresql_engine.dispose()


def test_alembic_env_import_registers_agent_config_tables_in_target_metadata() -> None:
    env_path = Path(__file__).parents[2] / "alembic" / "env.py"
    script = textwrap.dedent(
        f"""
        import importlib.util
        import sys
        from contextlib import nullcontext
        from types import SimpleNamespace

        import alembic

        class Config:
            config_file_name = None

            def get_main_option(self, name):
                return "sqlite+pysqlite:///:memory:"

            def set_main_option(self, name, value):
                pass

        context = SimpleNamespace(
            config=Config(),
            configure=lambda **kwargs: None,
            begin_transaction=nullcontext,
            is_offline_mode=lambda: True,
            run_migrations=lambda: None,
        )
        alembic.context = context
        sys.modules["alembic.context"] = context

        spec = importlib.util.spec_from_file_location("task006_alembic_env", {str(env_path)!r})
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        from app.core.database import Base

        assert {{"model_providers", "model_bindings", "agent_configs"}} <= set(Base.metadata.tables)
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=env_path.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
