from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import Base
from app.main import create_app
from app.modules.identity.bootstrap import ensure_identity_catalog
from app.modules.identity.models import Role, RoleCode, User
from app.modules.identity.security import hash_password


def build_client() -> TestClient:
    app = create_app(postgres_dsn="sqlite+pysqlite:///:memory:", redis_url="redis://redis:6379/0")
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as db:
        ensure_identity_catalog(db)
        admin_role = db.scalar(select(Role).where(Role.code == RoleCode.SYSTEM_ADMIN.value))
        assert admin_role is not None
        db.add(User(username="admin", password_hash=hash_password("correct-password"), roles=[admin_role]))
        db.commit()
    return TestClient(app)


def headers(client: TestClient, key: str = "role-test-key") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"username": "admin", "password": "correct-password"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}", "Idempotency-Key": key}


def role_payload(name: str) -> dict[str, object]:
    return {"name": name, "description": "用于测试的自定义角色", "enabled": True, "permission_codes": ["equipment:read"]}


def test_role_management_creates_and_lists_custom_roles() -> None:
    client = build_client()
    response = client.post("/api/roles", json=role_payload("质量管理员"), headers=headers(client))

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "质量管理员"
    assert created["built_in"] is False
    assert created["enabled"] is True
    assert created["user_count"] == 0
    listed = client.get("/api/roles", headers=headers(client)).json()
    assert any(role["id"] == created["id"] for role in listed)


def test_system_administrator_cannot_be_changed_or_deleted() -> None:
    client = build_client()
    role = next(item for item in client.get("/api/roles", headers=headers(client)).json() if item["code"] == "SYSTEM_ADMIN")

    update = client.patch(f"/api/roles/{role['id']}", json={**role_payload("不应保存"), "enabled": False}, headers=headers(client))
    remove = client.delete(f"/api/roles/{role['id']}", headers=headers(client))

    assert update.status_code == 409
    assert update.json()["detail"]["code"] == "SYSTEM_ADMIN_ROLE_FIXED"
    assert remove.status_code == 409
    assert remove.json()["detail"]["code"] == "SYSTEM_ADMIN_ROLE_FIXED"


def test_bound_role_cannot_be_disabled_or_deleted() -> None:
    client = build_client()
    create = client.post("/api/roles", json=role_payload("临时角色"), headers=headers(client, "create-bound")).json()
    with client.app.state.session_factory() as db:
        role = db.get(Role, create["id"])
        assert role is not None
        db.add(User(username="bound-user", password_hash=hash_password("password"), roles=[role]))
        db.commit()

    disable = client.patch(f"/api/roles/{create['id']}", json={**role_payload("临时角色"), "enabled": False}, headers=headers(client, "disable-bound"))
    remove = client.delete(f"/api/roles/{create['id']}", headers=headers(client, "delete-bound"))

    assert disable.status_code == 409
    assert disable.json()["detail"]["code"] == "ROLE_BOUND_TO_USERS"
    assert remove.status_code == 409
    assert remove.json()["detail"]["code"] == "ROLE_BOUND_TO_USERS"


def test_unbound_role_is_soft_deleted() -> None:
    client = build_client()
    create = client.post("/api/roles", json=role_payload("待删除角色"), headers=headers(client, "create-delete")).json()

    deleted = client.delete(f"/api/roles/{create['id']}", headers=headers(client, "delete-unbound"))

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert all(item["id"] != create["id"] for item in client.get("/api/roles", headers=headers(client)).json())
