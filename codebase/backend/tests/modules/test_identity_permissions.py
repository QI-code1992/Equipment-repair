import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
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
