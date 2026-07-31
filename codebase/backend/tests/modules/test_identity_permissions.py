from datetime import UTC, datetime, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
import json
import app.modules.equipment.organization_router as organization_router
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import (
    Equipment,
    EquipmentStatus,
    Organization,
    OrganizationType,
)
from app.modules.identity.models import LoginSession, Permission, Role, RoleCode, User
from app.modules.identity.bootstrap import ensure_identity_catalog
from app.modules.identity.security import hash_password
from app.main import create_app
from tests.modules.support import valid_equipment_body


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
    db_session.add(
        Organization(
            id="line-unique",
            type=OrganizationType.LINE,
            code="LINE-UNIQUE",
            name="Unique Test Line",
            sort_order=0,
            enabled=True,
        )
    )
    db_session.add_all(
        [
            Equipment(
                code="EQ-001",
                name="A",
                model="MODEL-A",
                type="TYPE-A",
                manufacturer="MANUFACTURER-A",
                operating_hours=Decimal("0"),
                status=EquipmentStatus.NORMAL,
                organization_id="line-unique",
                image_refs=[],
            ),
            Equipment(
                code="EQ-001",
                name="B",
                model="MODEL-B",
                type="TYPE-B",
                manufacturer="MANUFACTURER-B",
                operating_hours=Decimal("0"),
                status=EquipmentStatus.NORMAL,
                organization_id="line-unique",
                image_refs=[],
            ),
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
    with app.state.session_factory() as session:
        session.add(
            Organization(
                type=OrganizationType.ROOT,
                code="ROOT",
                name="根节点",
                parent_id=None,
                sort_order=0,
                enabled=True,
                remark="",
            )
        )
        session.commit()
    return TestClient(app)


def root_id(client: TestClient) -> str:
    with client.app.state.session_factory() as session:
        return session.scalar(
            select(Organization.id).where(Organization.type == OrganizationType.ROOT)
        )


def organization_payload(
    organization_type: str, code: str, name: str, parent_id: str
) -> dict[str, object]:
    return {
        "type": organization_type,
        "code": code,
        "name": name,
        "parent_id": parent_id,
        "sort_order": 0,
        "enabled": True,
        "remark": "",
    }


def create_user_token(client: TestClient, permission_codes: list[str]) -> str:
    with client.app.state.session_factory() as session:
        role_name = RoleCode.EQUIPMENT_ADMIN.value
        role = Role(code=role_name, name=role_name, built_in=True)
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


def test_current_user_returns_only_its_effective_permission_codes(client: TestClient) -> None:
    token = create_user_token(client, ["equipment:read", "fault:create"])

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["permission_codes"] == ["equipment:read", "fault:create"]
    assert set(response.json()) == {"id", "username", "enabled", "permission_codes"}


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
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "logout-once"}

    logout = client.delete("/api/auth/session", headers=headers)
    assert logout.status_code == 200
    assert "audit_event_id" in logout.json()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_replays_after_session_is_revoked(client: TestClient) -> None:
    token = create_user_token(client, [])
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "logout-replay"}

    first = client.delete("/api/auth/session", headers=headers)
    second = client.delete("/api/auth/session", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


@pytest.mark.parametrize("invalid_state", ["expired", "disabled"])
def test_logout_rejects_invalid_session(
    client: TestClient, invalid_state: str
) -> None:
    token = create_user_token(client, [])
    with client.app.state.session_factory() as session:
        login_session = session.scalar(select(LoginSession))
        assert login_session is not None
        if invalid_state == "expired":
            login_session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        else:
            user = session.get(User, login_session.user_id)
            assert user is not None
            user.enabled = False
        session.commit()

    response = client.delete(
        "/api/auth/session",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": f"logout-{invalid_state}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHENTICATED"


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
    payload = valid_equipment_body(client, code="EQ-101")
    headers = writer_headers(client, "first")
    first = client.post("/api/equipment", json=payload, headers=headers)

    second_headers = dict(headers)
    second_headers["Idempotency-Key"] = "second"
    second = client.post("/api/equipment", json=payload, headers=second_headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"


def test_same_idempotency_key_replays_response(client: TestClient) -> None:
    payload = valid_equipment_body(client, code="EQ-102")
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
        json=valid_equipment_body(client, code="EQ-103"),
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
        metadata={
            "password": "plain",
            "access_token": "token-value",
            "password_hash": "hash-value",
            "note": "Bearer embedded-value",
            "nested": {"authorization": "Bearer secret"},
            "token_count": 42,
            "max_reply_tokens": 512,
            "token_usage": {"input": 12, "output": 8},
            "accessToken": "camel-access",
            "refreshToken": "camel-refresh",
            "apiKey": "camel-key",
            "newPassword": "camel-password",
        },
    )
    db_session.commit()

    rendered = json.dumps(event.metadata_json)
    assert "plain" not in rendered
    assert "Bearer secret" not in rendered
    assert "token-value" not in rendered
    assert "hash-value" not in rendered
    assert "embedded-value" not in rendered
    assert "camel-access" not in rendered
    assert "camel-refresh" not in rendered
    assert "camel-key" not in rendered
    assert "camel-password" not in rendered
    assert rendered.count("[REDACTED]") == 9
    assert event.metadata_json["token_count"] == 42
    assert event.metadata_json["max_reply_tokens"] == 512
    assert event.metadata_json["token_usage"] == {"input": 12, "output": 8}


def test_organization_tree_can_be_created(client: TestClient) -> None:
    headers = writer_headers(client, "root-org")
    root = client.post(
        "/api/organizations",
        json=organization_payload("FACTORY", "FAC-TREE", "Plant A", root_id(client)),
        headers=headers,
    )
    child_headers = dict(headers)
    child_headers["Idempotency-Key"] = "child-org"
    child = client.post(
        "/api/organizations",
        json=organization_payload("WORKSHOP", "WS-TREE", "Workshop", root.json()["id"]),
        headers=child_headers,
    )

    assert root.status_code == 201
    assert child.status_code == 201
    assert child.json()["parent_id"] == root.json()["id"]


def test_organization_parent_cannot_be_changed(client: TestClient) -> None:
    headers = writer_headers(client, "cycle-root")
    root = client.post(
        "/api/organizations",
        json=organization_payload("FACTORY", "FAC-FIXED", "Factory", root_id(client)),
        headers=headers,
    ).json()

    response = client.patch(
        f"/api/organizations/{root['id']}",
        json={
            "code": root["code"],
            "name": root["name"],
            "sort_order": root["sort_order"],
            "enabled": root["enabled"],
            "remark": root["remark"],
            "parent_id": root_id(client),
        },
        headers={**headers, "Idempotency-Key": "cycle-update"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_organization_tree_writes_use_one_postgresql_lock() -> None:
    executed: list[tuple[object, object]] = []

    class PostgreSQLBind:
        class dialect:
            name = "postgresql"

    class RecordingSession:
        def get_bind(self) -> PostgreSQLBind:
            return PostgreSQLBind()

        def execute(self, statement: object, parameters: object = None) -> None:
            executed.append((statement, parameters))

    organization_router.acquire_organization_tree_lock(RecordingSession())

    assert "pg_advisory_xact_lock" in str(executed[0][0])
    assert executed[0][1] == {"lock_id": organization_router.ORGANIZATION_TREE_LOCK_ID}


@pytest.mark.parametrize("method", ["post", "patch"])
def test_equipment_rejects_unknown_organization(
    client: TestClient, method: str
) -> None:
    headers = writer_headers(client, f"unknown-org-{method}")
    valid_payload = valid_equipment_body(client, code="EQ-NO-ORG")
    payload = valid_payload | {
        "organization_id": "missing"
    }
    if method == "post":
        response = client.post(
            "/api/equipment",
            json=payload,
            headers=headers,
        )
    else:
        with client.app.state.session_factory() as session:
            equipment = Equipment(
                code="EQ-EXISTING",
                name="Loader",
                model="MODEL-EXISTING",
                type="TYPE-EXISTING",
                manufacturer="MANUFACTURER-EXISTING",
                operating_hours=Decimal("0"),
                status=EquipmentStatus.NORMAL,
                organization_id=valid_payload["organization_id"],
                image_refs=[],
            )
            session.add(equipment)
            session.commit()
            equipment_id = equipment.id
        response = client.patch(
            f"/api/equipment/{equipment_id}",
            json=payload,
            headers=headers,
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EQUIPMENT_ORGANIZATION_NOT_FOUND"


def test_identity_admin_can_create_user_with_fixed_role(client: TestClient) -> None:
    admin_token = create_user_token(
        client,
        ["identity:read", "identity:write", "equipment:read"],
    )
    base_headers = {"Authorization": f"Bearer {admin_token}"}
    with client.app.state.session_factory() as session:
        fixed_roles = ensure_identity_catalog(session)
        session.commit()
        equipment_admin_id = fixed_roles[RoleCode.EQUIPMENT_ADMIN].id
    user_response = client.post(
        "/api/users",
        json={
            "username": "reader",
            "password": "reader-password",
            "role_ids": [equipment_admin_id],
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
