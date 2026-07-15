import pytest
from fastapi.testclient import TestClient
import json
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import Equipment
from app.modules.identity.models import LoginSession, Permission, Role, User
from app.modules.identity.security import hash_password
from app.main import create_app


pytestmark = pytest.mark.filterwarnings("error:datetime.datetime.utcnow")


@pytest.fixture
def engine() -> Engine:
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database_engine)
    return database_engine


@pytest.fixture
def db_session(engine: Engine) -> Session:
    factory = session_factory(engine)
    with factory() as session:
        yield session


def test_equipment_code_is_unique(db_session: Session) -> None:
    db_session.add_all(
        [
            Equipment(code="EQ-001", name="A", organization_id=None),
            Equipment(code="EQ-001", name="B", organization_id=None),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_schema_has_no_equipment_grant_table(engine: Engine) -> None:
    assert "equipment_grant" not in inspect(engine).get_table_names()


@pytest.fixture
def client() -> TestClient:
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
    )
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def create_user_token(client: TestClient, permission_codes: list[str]) -> str:
    with client.app.state.session_factory() as session:
        role = Role(name=f"role-{len(permission_codes)}-{'-'.join(permission_codes)}")
        role.permissions = [Permission(code=code) for code in permission_codes]
        user = User(username=f"user-{len(permission_codes)}", password_hash=hash_password("correct-password"))
        user.roles = [role]
        session.add(user)
        session.commit()

    response = client.post(
        "/api/auth/login",
        json={"username": user.username, "password": "correct-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_protected_request_requires_login(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_user_without_operation_permission_is_forbidden(client: TestClient) -> None:
    token = create_user_token(client, [])

    response = client.get("/api/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_authorized_user_can_read_equipment(client: TestClient) -> None:
    token = create_user_token(client, ["equipment:read"])

    response = client.get("/api/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_login_stores_only_token_digest(client: TestClient) -> None:
    token = create_user_token(client, [])

    with client.app.state.session_factory() as session:
        stored_session = session.scalar(select(LoginSession))

    assert stored_session is not None
    assert stored_session.token_hash != token
    assert len(stored_session.token_hash) == 64


def test_logout_revokes_session(client: TestClient) -> None:
    token = create_user_token(client, [])
    headers = {"Authorization": f"Bearer {token}"}

    assert client.delete("/api/auth/session", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def writer_headers(client: TestClient, idempotency_key: str) -> dict[str, str]:
    token = create_user_token(
        client,
        ["equipment:read", "equipment:write", "organization:read", "organization:write"],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
    }


def test_duplicate_equipment_code_is_rejected(client: TestClient) -> None:
    payload = {"code": "EQ-101", "name": "Loader", "organization_id": None}
    headers = writer_headers(client, "first")
    first = client.post("/api/equipment", json=payload, headers=headers)

    second_headers = dict(headers)
    second_headers["Idempotency-Key"] = "second"
    second = client.post("/api/equipment", json=payload, headers=second_headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"


def test_same_idempotency_key_replays_response(client: TestClient) -> None:
    payload = {"code": "EQ-102", "name": "Loader", "organization_id": None}
    headers = writer_headers(client, "same-request")

    first = client.post("/api/equipment", json=payload, headers=headers)
    second = client.post("/api/equipment", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == first.status_code
    assert second.json() == first.json()


def test_protected_write_requires_idempotency_key(client: TestClient) -> None:
    token = create_user_token(client, ["equipment:write"])

    response = client.post(
        "/api/equipment",
        json={"code": "EQ-103", "name": "Loader", "organization_id": None},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_audit_metadata_excludes_credentials(db_session: Session) -> None:
    event = write_audit_event(
        db_session,
        actor_user_id=None,
        action="security.test",
        resource_type="test",
        resource_id=None,
        result="success",
        metadata={"password": "plain", "nested": {"authorization": "Bearer secret"}},
    )
    db_session.commit()

    rendered = json.dumps(event.metadata_json)
    assert "plain" not in rendered
    assert "Bearer secret" not in rendered
    assert rendered.count("[REDACTED]") == 2


def test_organization_tree_can_be_created(client: TestClient) -> None:
    headers = writer_headers(client, "root-org")
    root = client.post("/api/organizations", json={"name": "Plant A", "parent_id": None}, headers=headers)
    child_headers = dict(headers)
    child_headers["Idempotency-Key"] = "child-org"
    child = client.post(
        "/api/organizations",
        json={"name": "Workshop", "parent_id": root.json()["id"]},
        headers=child_headers,
    )

    assert root.status_code == 201
    assert child.status_code == 201
    assert child.json()["parent_id"] == root.json()["id"]


def test_identity_admin_can_create_role_and_user(client: TestClient) -> None:
    admin_token = create_user_token(
        client,
        ["identity:read", "identity:write", "equipment:read"],
    )
    base_headers = {"Authorization": f"Bearer {admin_token}"}
    role_response = client.post(
        "/api/roles",
        json={"name": "equipment-reader", "permission_codes": ["equipment:read"]},
        headers={**base_headers, "Idempotency-Key": "create-reader-role"},
    )
    assert role_response.status_code == 201
    user_response = client.post(
        "/api/users",
        json={
            "username": "reader",
            "password": "reader-password",
            "role_ids": [role_response.json()["id"]],
        },
        headers={**base_headers, "Idempotency-Key": "create-reader-user"},
    )
    assert user_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": "reader", "password": "reader-password"},
    )
    reader_token = login_response.json()["access_token"]

    assert login_response.status_code == 200
    assert client.get(
        "/api/equipment",
        headers={"Authorization": f"Bearer {reader_token}"},
    ).status_code == 200
