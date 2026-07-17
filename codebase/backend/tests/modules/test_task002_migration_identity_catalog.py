import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.modules.identity.bootstrap import PERMISSION_CODES
from app.modules.identity.models import RoleCode


BACKEND_DIR = Path(__file__).parents[2]


@pytest.fixture
def catalog_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Config, Engine]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'catalog.sqlite3').as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    return config, create_engine(database_url)


def seed_legacy_administrator(config: Config, engine: Engine) -> None:
    command.upgrade(config, "0001")
    with engine.begin() as db:
        db.execute(text("INSERT INTO roles (id, name) VALUES ('role-admin', 'system-administrator')"))
        db.execute(
            text(
                "INSERT INTO users "
                "(id, username, password_hash, enabled, created_at, updated_at) VALUES "
                "('user-admin', 'admin', 'hash', 1, '2026-01-01', '2026-01-01')"
            )
        )
        db.execute(text("INSERT INTO permissions (id, code) VALUES ('permission-read', 'identity:read')"))
        db.execute(text("INSERT INTO user_roles (user_id, role_id) VALUES ('user-admin', 'role-admin')"))
        db.execute(
            text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "VALUES ('role-admin', 'permission-read')"
            )
        )


def test_upgrade_builds_exact_identity_catalog_and_full_system_admin_grant(
    catalog_database: tuple[Config, Engine],
) -> None:
    config, engine = catalog_database
    seed_legacy_administrator(config, engine)

    command.upgrade(config, "0002")

    with engine.connect() as db:
        roles = set(db.execute(text("SELECT code, name, built_in FROM roles")))
        assert roles == {(code.value, code.value, 1) for code in RoleCode}
        permissions = set(db.execute(text("SELECT code FROM permissions")).scalars())
        assert permissions == set(PERMISSION_CODES)
        system_permissions = set(
            db.execute(
                text(
                    "SELECT permissions.code FROM permissions "
                    "JOIN role_permissions ON role_permissions.permission_id = permissions.id "
                    "JOIN roles ON roles.id = role_permissions.role_id "
                    "WHERE roles.code = 'SYSTEM_ADMIN'"
                )
            ).scalars()
        )
        assert system_permissions == set(PERMISSION_CODES)


def test_upgrade_rejects_unmappable_custom_legacy_role(
    catalog_database: tuple[Config, Engine],
) -> None:
    config, engine = catalog_database
    command.upgrade(config, "0001")
    with engine.begin() as db:
        db.execute(text("INSERT INTO roles (id, name) VALUES ('custom-role', 'planner')"))

    with pytest.raises(RuntimeError, match="custom legacy roles"):
        command.upgrade(config, "0002")


def test_upgrade_rejects_permission_outside_fixed_catalog(
    catalog_database: tuple[Config, Engine],
) -> None:
    config, engine = catalog_database
    command.upgrade(config, "0001")
    with engine.begin() as db:
        db.execute(
            text("INSERT INTO permissions (id, code) VALUES ('custom', 'custom:grant')")
        )

    with pytest.raises(RuntimeError, match="custom legacy permissions"):
        command.upgrade(config, "0002")


def test_programmatic_migration_preserves_existing_logging_configuration(
    catalog_database: tuple[Config, Engine],
) -> None:
    config, _ = catalog_database
    root_logger = logging.getLogger()
    audit_logger = logging.getLogger("app.modules.audit.http")
    original_handlers = tuple(root_logger.handlers)
    original_disabled = audit_logger.disabled
    audit_logger.disabled = False

    try:
        command.upgrade(config, "0001")
        assert tuple(root_logger.handlers) == original_handlers
        assert audit_logger.disabled is False
    finally:
        root_logger.handlers[:] = original_handlers
        audit_logger.disabled = original_disabled
