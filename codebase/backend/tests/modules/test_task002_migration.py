from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


BACKEND_DIR = Path(__file__).parents[2]


@pytest.fixture
def migration_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Config, Engine]:
    database_path = tmp_path / "task002.sqlite3"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("POSTGRES_DSN", database_url)
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    return config, create_engine(database_url)


def insert_legacy_organization_tree(engine: Engine) -> None:
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO organizations (id, name, parent_id) VALUES "
                "('org-1', 'Factory', NULL), "
                "('org-2', 'Workshop', 'org-1'), "
                "('org-3', 'Line', 'org-2')"
            )
        )
        db.execute(
            text(
                "INSERT INTO equipment (id, code, name, organization_id, enabled) "
                "VALUES ('equipment-1', 'EQ-1', 'Legacy', 'org-3', 0), "
                "('equipment-2', 'EQ-2', 'Unassigned', NULL, 1), "
                "('equipment-3', 'EQ-3', 'Wrong Level', 'org-1', 1)"
            )
        )


def assert_upgraded_legacy_contract(engine: Engine) -> None:
    with engine.connect() as db:
        fixed_roles = set(db.execute(text("SELECT code FROM roles")).scalars())
        assert fixed_roles == {
            "SYSTEM_ADMIN", "EQUIPMENT_ADMIN", "REPAIR_WORKER", "LINE_OPERATOR"
        }
        organizations = {
            row.id: row
            for row in db.execute(text("SELECT id, type, code, parent_id FROM organizations"))
        }
        roots = [row for row in organizations.values() if row.type == "ROOT"]
        assert len(roots) == 1
        assert organizations["org-1"].type == "FACTORY"
        assert organizations["org-1"].parent_id == roots[0].id
        assert organizations["org-2"].type == "WORKSHOP"
        assert organizations["org-3"].type == "LINE"
        equipment = db.execute(
            text(
                "SELECT model, type, manufacturer, organization_id, status, "
                "operating_hours, image_refs FROM equipment WHERE id = 'equipment-1'"
            )
        ).one()
        assert equipment.model == "LEGACY-EQ-1"
        assert equipment.type == "LEGACY_UNSPECIFIED"
        assert equipment.manufacturer == "LEGACY_UNSPECIFIED"
        assert equipment.organization_id == "org-3"
        assert equipment.status == "DISABLED"
        assert equipment.operating_hours == 0
        assert equipment.image_refs == "[]"
        unassigned = db.execute(
            text(
                "SELECT equipment.model, organizations.type AS organization_type "
                "FROM equipment JOIN organizations "
                "ON equipment.organization_id = organizations.id "
                "WHERE equipment.id = 'equipment-2'"
            )
        ).one()
        assert unassigned.model == "LEGACY-EQ-2"
        assert unassigned.organization_type == "LINE"
        columns = {
            column["name"]: column for column in inspect(engine).get_columns("equipment")
        }
        assert "enabled" not in columns
        for column_name in ("model", "type", "manufacturer", "organization_id"):
            assert columns[column_name]["nullable"] is False


def assert_downgraded_legacy_contract(engine: Engine) -> None:
    with engine.connect() as db:
        equipment = db.execute(
            text("SELECT enabled, organization_id FROM equipment WHERE id = 'equipment-1'")
        ).one()
        assert equipment.enabled == 0
        assert equipment.organization_id == "org-3"
        invalid_legacy_organizations = dict(
            db.execute(
                text(
                    "SELECT id, organization_id FROM equipment "
                    "WHERE id IN ('equipment-2', 'equipment-3')"
                )
            ).all()
        )
        assert invalid_legacy_organizations == {
            "equipment-2": None,
            "equipment-3": None,
        }
        assert {
            "users", "roles", "permissions", "organizations", "equipment"
        } <= set(inspect(engine).get_table_names())


def test_upgrade_and_downgrade_backfill_full_legacy_contract(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0001")
    insert_legacy_organization_tree(engine)

    command.upgrade(config, "0002")
    assert_upgraded_legacy_contract(engine)

    command.downgrade(config, "0001")
    assert_downgraded_legacy_contract(engine)


def test_upgrade_merges_duplicate_system_roles_without_losing_relationships(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0001")
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO roles (id, name) VALUES "
                "('role-legacy', 'system-administrator'), "
                "('role-code-name', 'SYSTEM_ADMIN')"
            )
        )
        db.execute(
            text(
                "INSERT INTO users "
                "(id, username, password_hash, enabled, created_at, updated_at) VALUES "
                "('user-1', 'admin', 'hash', 1, '2026-01-01', '2026-01-01')"
            )
        )
        db.execute(
            text(
                "INSERT INTO permissions (id, code) VALUES "
                "('permission-1', 'identity:read'), "
                "('permission-2', 'identity:write')"
            )
        )
        db.execute(
            text(
                "INSERT INTO user_roles (user_id, role_id) VALUES "
                "('user-1', 'role-legacy'), ('user-1', 'role-code-name')"
            )
        )
        db.execute(
            text(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES "
                "('role-legacy', 'permission-1'), ('role-code-name', 'permission-2')"
            )
        )

    command.upgrade(config, "0002")

    with engine.connect() as db:
        system_roles = db.execute(
            text("SELECT id FROM roles WHERE code = 'SYSTEM_ADMIN'")
        ).scalars().all()
        assert system_roles == ["role-legacy"]
        assert db.execute(text("SELECT role_id FROM user_roles")).scalars().all() == [
            "role-legacy"
        ]
        permission_codes = set(
            db.execute(
                text(
                    "SELECT permissions.code FROM permissions "
                    "JOIN role_permissions ON permissions.id = role_permissions.permission_id "
                    "WHERE role_permissions.role_id = 'role-legacy'"
                )
            ).scalars()
        )
        assert permission_codes == {"identity:read", "identity:write"}


@pytest.mark.parametrize("invalid_tree", ["depth", "cycle"])
def test_upgrade_rejects_invalid_legacy_organization_tree(
    migration_database: tuple[Config, Engine], invalid_tree: str
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0001")
    with engine.begin() as db:
        if invalid_tree == "depth":
            db.execute(
                text(
                    "INSERT INTO organizations (id, name, parent_id) VALUES "
                    "('org-1', 'One', NULL), ('org-2', 'Two', 'org-1'), "
                    "('org-3', 'Three', 'org-2'), ('org-4', 'Four', 'org-3')"
                )
            )
        else:
            db.execute(
                text(
                    "INSERT INTO organizations (id, name, parent_id) VALUES "
                    "('org-1', 'One', 'org-2'), ('org-2', 'Two', 'org-1')"
                )
            )

    expected = "depth greater than 3" if invalid_tree == "depth" else "contains a cycle"
    with pytest.raises(RuntimeError, match=expected):
        command.upgrade(config, "0002")


def test_downgrade_detaches_equipment_from_generated_root(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0001")
    insert_legacy_organization_tree(engine)
    command.upgrade(config, "0002")
    with engine.begin() as db:
        root_id = db.execute(
            text("SELECT id FROM organizations WHERE type = 'ROOT'")
        ).scalar_one()
        db.execute(
            text("UPDATE equipment SET organization_id = :root_id"), {"root_id": root_id}
        )

    command.downgrade(config, "0001")

    with engine.connect() as db:
        assert db.execute(
            text("SELECT organization_id FROM equipment WHERE id = 'equipment-1'")
        ).scalar_one_or_none() is None
        assert db.execute(
            text("SELECT count(*) FROM organizations WHERE id = :root_id"), {"root_id": root_id}
        ).scalar_one() == 0


def test_upgrade_avoids_fallback_name_collision(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, "0001")
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO organizations (id, name, parent_id) "
                "VALUES ('legacy-factory', 'Legacy Equipment Factory', NULL)"
            )
        )
        db.execute(
            text(
                "INSERT INTO equipment (id, code, name, organization_id, enabled) "
                "VALUES ('equipment-unassigned', 'EQ-U', 'Unassigned', NULL, 1)"
            )
        )

    command.upgrade(config, "0002")

    with engine.connect() as db:
        root_id = db.execute(
            text("SELECT id FROM organizations WHERE type = 'ROOT'")
        ).scalar_one()
        factory_names = db.execute(
            text(
                "SELECT name FROM organizations "
                "WHERE parent_id = :root_id AND type = 'FACTORY'"
            ),
            {"root_id": root_id},
        ).scalars().all()
        assert len(factory_names) == len(set(factory_names)) == 2
