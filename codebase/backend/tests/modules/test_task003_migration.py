from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine


BACKEND_DIR = Path(__file__).parents[2]
TASK003_TABLES = {
    "diagnosis_drafts",
    "fault_reports",
    "historical_repair_cases",
    "maintenance_records",
    "work_orders",
}


@pytest.fixture
def migration_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Config, Engine]:
    database_path = tmp_path / "task003.sqlite3"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    return config, create_engine(database_url)


def _assert_task003_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    assert TASK003_TABLES <= set(inspector.get_table_names())
    assert {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("work_orders")
    } == {"uq_work_orders_fault_report_id", "uq_work_orders_number"}
    assert {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("maintenance_records")
    } == {
        "uq_maintenance_records_diagnosis_draft_id",
        "uq_maintenance_records_work_order_id",
    }
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("fault_reports")
    } == {"ck_fault_reports_status"}
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("work_orders")
    } == {"ck_work_orders_status"}
    assert {
        index["name"] for index in inspector.get_indexes("fault_reports")
    } == {"ix_fault_reports_equipment_id", "ix_fault_reports_status"}
    assert {
        foreign_key["referred_table"]
        for table in TASK003_TABLES
        for foreign_key in inspector.get_foreign_keys(table)
    } >= {"equipment", "fault_reports", "users", "work_orders"}


def test_empty_database_upgrades_to_single_task003_head_and_is_reversible(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database

    command.upgrade(config, "head")

    script = ScriptDirectory.from_config(config)
    assert [revision.revision for revision in script.get_revisions("heads")] == [
        "0007_task013_notifications"
    ]
    _assert_task003_schema(engine)

    command.downgrade(config, "0002")
    tables = set(inspect(engine).get_table_names())
    assert not (TASK003_TABLES & tables)
    assert {"users", "roles", "permissions", "organizations", "equipment"} <= tables

    command.upgrade(config, "0003_task003")
    _assert_task003_schema(engine)


def test_existing_0002_database_upgrades_to_task003(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0002")
    assert not (TASK003_TABLES & set(inspect(engine).get_table_names()))

    command.upgrade(config, "0003_task003")

    _assert_task003_schema(engine)
