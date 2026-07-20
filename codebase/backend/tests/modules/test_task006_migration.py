from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import Boolean, DateTime, JSON, String, create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError


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
    engine = create_engine(database_url)
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    return config, engine


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


def _assert_not_nullable(engine: Engine, table_name: str, column_names: tuple[str, ...]) -> None:
    for column_name in column_names:
        assert _column(engine, table_name, column_name)["nullable"] is False


def test_task006_upgrade_creates_model_catalog_schema(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0002")
    command.upgrade(config, "0003")

    inspector = inspect(engine)
    assert {"model_providers", "model_bindings", "agent_configs"} <= set(
        inspector.get_table_names()
    )

    for table_name in ("model_providers", "model_bindings"):
        identifier = _column(engine, table_name, "id")
        assert isinstance(identifier["type"], String)
        assert identifier["type"].length == 36

    assert _column_names(engine, "model_providers") >= {"id", "name", "secret_ref", "enabled"}
    assert _column(engine, "model_providers", "name")["type"].length == 100
    assert _column(engine, "model_providers", "secret_ref")["type"].length == 500
    assert isinstance(_column(engine, "model_providers", "enabled")["type"], Boolean)
    assert _column(engine, "model_providers", "enabled")["default"] == "1"
    _assert_not_nullable(engine, "model_providers", ("id", "name", "secret_ref", "enabled"))
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
    assert _column(engine, "model_bindings", "name")["type"].length == 100
    assert _column(engine, "model_bindings", "model_name")["type"].length == 200
    assert _column(engine, "model_bindings", "supports_reasoning")["default"] == "0"
    assert _column(engine, "model_bindings", "enabled")["default"] == "1"
    _assert_not_nullable(
        engine,
        "model_bindings",
        ("id", "provider_id", "name", "model_name", "supports_reasoning", "enabled"),
    )
    assert {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("model_bindings")
    } >= {("provider_id", "name")}
    provider_foreign_key = _foreign_key(engine, "model_bindings", "provider_id")
    assert provider_foreign_key["referred_table"] == "model_providers"
    assert provider_foreign_key["options"].get("ondelete") == "RESTRICT"


def test_task006_upgrade_creates_agent_config_schema(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0003")

    inspector = inspect(engine)
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
    assert _column(engine, "agent_configs", "id")["type"].length == 36
    assert _column(engine, "agent_configs", "agent_id")["type"].length == 36
    assert isinstance(_column(engine, "agent_configs", "knowledge_dataset_ids")["type"], JSON)
    for timestamp in ("created_at", "updated_at"):
        assert isinstance(_column(engine, "agent_configs", timestamp)["type"], DateTime)
    assert _column(engine, "agent_configs", "deep_thinking_level")["type"].length == 20
    _assert_not_nullable(
        engine,
        "agent_configs",
        (
            "id", "agent_id", "enabled", "knowledge_dataset_ids", "streaming_enabled",
            "suggestions_enabled", "sources_enabled", "context_turns", "retrieval_limit",
            "similarity_threshold", "deep_thinking_enabled", "deep_thinking_level",
            "max_reply_tokens", "created_at", "updated_at",
        ),
    )
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


def test_task006_restricts_deleting_referenced_model_catalog_rows(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0003")
    with engine.begin() as db:
        assert db.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        db.execute(
            text(
                "INSERT INTO model_providers (id, name, secret_ref, enabled) VALUES "
                "('provider-1', 'Provider', 'secret://provider', 1)"
            )
        )
        db.execute(
            text(
                "INSERT INTO model_bindings "
                "(id, provider_id, name, model_name, supports_reasoning, enabled) VALUES "
                "('binding-1', 'provider-1', 'Binding', 'model', 0, 1)"
            )
        )
        db.execute(
            text(
                "INSERT INTO agent_configs "
                "(id, agent_id, enabled, model_binding_id, knowledge_dataset_ids, "
                "streaming_enabled, suggestions_enabled, sources_enabled, context_turns, "
                "retrieval_limit, similarity_threshold, deep_thinking_enabled, "
                "deep_thinking_level, max_reply_tokens, created_at, updated_at) VALUES "
                "('config-1', 'fault_reporting', 1, 'binding-1', '[]', 1, 1, 1, 3, 6, "
                "0.62, 0, 'medium', 4096, '2026-01-01', '2026-01-01')"
            )
        )
        with pytest.raises(IntegrityError):
            db.execute(text("DELETE FROM model_providers WHERE id = 'provider-1'"))
        with pytest.raises(IntegrityError):
            db.execute(text("DELETE FROM model_bindings WHERE id = 'binding-1'"))


def test_task006_round_trip_preserves_task002_baseline_data(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0002")
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO users (id, username, password_hash, enabled, created_at, updated_at) "
                "VALUES ('user-1', 'baseline-user', 'hash', 1, '2026-01-01', '2026-01-01')"
            )
        )

    command.upgrade(config, "0003")
    command.downgrade(config, "0002")

    with engine.connect() as db:
        assert db.execute(
            text("SELECT username, password_hash, enabled FROM users WHERE id = 'user-1'")
        ).one() == ("baseline-user", "hash", 1)


def test_task006_downgrade_removes_only_task006_tables(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0003")

    command.downgrade(config, "0002")

    table_names = set(inspect(engine).get_table_names())
    assert {"model_providers", "model_bindings", "agent_configs"}.isdisjoint(table_names)
    assert {"users", "roles", "permissions", "organizations", "equipment"} <= table_names
