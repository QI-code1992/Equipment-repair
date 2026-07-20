from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import String, create_engine, inspect
from sqlalchemy.engine import Engine


BACKEND_DIR = Path(__file__).parents[2]


@pytest.fixture
def migration_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Config, Engine]:
    database_path = tmp_path / "task006.sqlite3"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    return config, create_engine(database_url)


def _column_names(engine: Engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def _column(engine: Engine, table_name: str, name: str) -> dict[str, object]:
    return next(
        column for column in inspect(engine).get_columns(table_name) if column["name"] == name
    )


def _foreign_key(engine: Engine, table_name: str, column_name: str) -> dict[str, object]:
    return next(
        foreign_key
        for foreign_key in inspect(engine).get_foreign_keys(table_name)
        if foreign_key["constrained_columns"] == [column_name]
    )


def test_task006_upgrade_creates_catalog_and_config_constraints(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0002")
    command.upgrade(config, "0003")

    inspector = inspect(engine)
    assert {"model_providers", "model_bindings", "agent_configs"} <= set(
        inspector.get_table_names()
    )

    for table_name in ("model_providers", "model_bindings", "agent_configs"):
        identifier = _column(engine, table_name, "id")
        assert isinstance(identifier["type"], String)
        assert identifier["type"].length == 36

    provider_columns = _column_names(engine, "model_providers")
    assert provider_columns >= {"id", "name", "secret_ref", "enabled"}
    assert _column(engine, "model_providers", "secret_ref")["type"].length == 500
    assert {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("model_providers")
    } >= {("name",)}

    binding_columns = _column_names(engine, "model_bindings")
    assert binding_columns >= {
        "id",
        "provider_id",
        "name",
        "model_name",
        "supports_reasoning",
        "enabled",
    }
    assert {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("model_bindings")
    } >= {("provider_id", "name")}
    provider_foreign_key = _foreign_key(engine, "model_bindings", "provider_id")
    assert provider_foreign_key["referred_table"] == "model_providers"
    assert provider_foreign_key["options"].get("ondelete") == "RESTRICT"

    config_columns = _column_names(engine, "agent_configs")
    assert config_columns >= {
        "id",
        "agent_id",
        "enabled",
        "model_binding_id",
        "knowledge_dataset_ids",
        "streaming_enabled",
        "suggestions_enabled",
        "sources_enabled",
        "context_turns",
        "retrieval_limit",
        "similarity_threshold",
        "deep_thinking_enabled",
        "deep_thinking_level",
        "max_reply_tokens",
        "created_at",
        "updated_at",
        "updated_by",
    }
    assert {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("agent_configs")
    } >= {("agent_id",)}
    assert _column(engine, "agent_configs", "updated_by")["nullable"] is True
    model_binding_foreign_key = _foreign_key(engine, "agent_configs", "model_binding_id")
    assert model_binding_foreign_key["referred_table"] == "model_bindings"
    assert model_binding_foreign_key["options"].get("ondelete") == "RESTRICT"
    updated_by_foreign_key = _foreign_key(engine, "agent_configs", "updated_by")
    assert updated_by_foreign_key["referred_table"] == "users"


def test_task006_downgrade_removes_only_task006_tables(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0003")

    command.downgrade(config, "0002")

    table_names = set(inspect(engine).get_table_names())
    assert {"model_providers", "model_bindings", "agent_configs"}.isdisjoint(table_names)
    assert {"users", "roles", "permissions", "organizations", "equipment"} <= table_names
