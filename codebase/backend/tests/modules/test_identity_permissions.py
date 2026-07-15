from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
import json
import app.modules.identity.service as identity_service
import app.modules.equipment.organization_router as organization_router
from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import Equipment
from app.modules.identity.models import LoginSession, Permission, Role, User
from app.modules.identity.bootstrap import BootstrapAlreadyInitialized, bootstrap_admin
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


def test_organization_parent_cannot_create_cycle(client: TestClient) -> None:
    headers = writer_headers(client, "cycle-root")
    root = client.post(
        "/api/organizations",
        json={"name": "Root", "parent_id": None},
        headers=headers,
    ).json()
    child = client.post(
        "/api/organizations",
        json={"name": "Child", "parent_id": root["id"]},
        headers={**headers, "Idempotency-Key": "cycle-child"},
    ).json()

    response = client.patch(
        f"/api/organizations/{root['id']}",
        json={"name": "Root", "parent_id": child["id"]},
        headers={**headers, "Idempotency-Key": "cycle-update"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ORGANIZATION_PARENT_INVALID"


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
    if method == "post":
        response = client.post(
            "/api/equipment",
            json={"code": "EQ-NO-ORG", "name": "Loader", "organization_id": "missing"},
            headers=headers,
        )
    else:
        with client.app.state.session_factory() as session:
            equipment = Equipment(code="EQ-EXISTING", name="Loader")
            session.add(equipment)
            session.commit()
            equipment_id = equipment.id
        response = client.patch(
            f"/api/equipment/{equipment_id}",
            json={"name": "Loader", "organization_id": "missing", "enabled": True},
            headers=headers,
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ORGANIZATION_NOT_FOUND"


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


def test_bootstrap_creates_only_first_administrator(client: TestClient) -> None:
    with client.app.state.session_factory() as session:
        administrator = bootstrap_admin(session, "first-admin", "bootstrap-password")
        assert {permission.code for role in administrator.roles for permission in role.permissions} >= {
            "identity:write",
            "equipment:read",
            "organization:write",
        }
        with pytest.raises(BootstrapAlreadyInitialized):
            bootstrap_admin(session, "second-admin", "another-password")
        events = session.scalars(select(AuditEvent).where(AuditEvent.action == "user.bootstrap")).all()
        assert len(events) == 1
        assert events[0].actor_user_id is None
        assert events[0].resource_id == administrator.id

    response = client.post(
        "/api/auth/login",
        json={"username": "first-admin", "password": "bootstrap-password"},
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("username", "password"),
    [("", "bootstrap-password"), ("first-admin", "")],
)
def test_bootstrap_rejects_blank_credentials(
    client: TestClient, username: str, password: str
) -> None:
    with client.app.state.session_factory() as session:
        with pytest.raises(ValueError, match="must not be blank"):
            bootstrap_admin(session, username, password)


def test_identity_reader_can_query_permissions_and_roles(client: TestClient) -> None:
    token = create_user_token(client, ["identity:read"])
    headers = {"Authorization": f"Bearer {token}"}

    permissions = client.get("/api/permissions", headers=headers)
    roles = client.get("/api/roles", headers=headers)

    assert permissions.status_code == 200
    assert permissions.json() == [{"code": "identity:read"}]
    assert roles.status_code == 200
    assert roles.json()[0]["permission_codes"] == ["identity:read"]


def test_equipment_and_organization_can_be_updated(client: TestClient) -> None:
    headers = writer_headers(client, "create-org-for-update")
    organization = client.post(
        "/api/organizations",
        json={"name": "Original Plant", "parent_id": None},
        headers=headers,
    ).json()
    create_equipment_headers = dict(headers)
    create_equipment_headers["Idempotency-Key"] = "create-equipment-for-update"
    equipment = client.post(
        "/api/equipment",
        json={"code": "EQ-UPDATE", "name": "Old Name", "organization_id": organization["id"]},
        headers=create_equipment_headers,
    ).json()

    update_org_headers = dict(headers)
    update_org_headers["Idempotency-Key"] = "update-org"
    updated_organization = client.patch(
        f"/api/organizations/{organization['id']}",
        json={"name": "Updated Plant", "parent_id": None},
        headers=update_org_headers,
    )
    update_equipment_headers = dict(headers)
    update_equipment_headers["Idempotency-Key"] = "update-equipment"
    updated_equipment = client.patch(
        f"/api/equipment/{equipment['id']}",
        json={"name": "New Name", "organization_id": organization["id"], "enabled": False},
        headers=update_equipment_headers,
    )

    assert updated_organization.status_code == 200
    assert updated_organization.json()["name"] == "Updated Plant"
    assert "audit_event_id" in updated_organization.json()
    assert updated_equipment.status_code == 200
    assert updated_equipment.json()["enabled"] is False
    assert "audit_event_id" in updated_equipment.json()


def test_login_failure_and_permission_denial_are_audited(client: TestClient) -> None:
    token = create_user_token(client, [])
    invalid = client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
    )
    denied = client.get("/api/equipment", headers={"Authorization": f"Bearer {token}"})

    with client.app.state.session_factory() as session:
        events = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at)).all()

    assert invalid.status_code == 401
    assert denied.status_code == 403
    assert [(event.action, event.result) for event in events] == [
        ("login", "success"),
        ("login", "failed"),
        ("permission.denied", "denied"),
    ]


def test_unknown_user_still_runs_password_verification(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    real_verify = identity_service.verify_password

    def counting_verify(password: str, encoded: str) -> bool:
        nonlocal calls
        calls += 1
        return real_verify(password, encoded)

    monkeypatch.setattr(identity_service, "verify_password", counting_verify)

    response = client.post(
        "/api/auth/login",
        json={"username": "missing-user", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert calls == 1


def test_idempotency_key_cannot_be_reused_for_another_target(client: TestClient) -> None:
    headers = writer_headers(client, "global-key")
    organization = client.post(
        "/api/organizations",
        json={"name": "Plant", "parent_id": None},
        headers=headers,
    )

    equipment = client.post(
        "/api/equipment",
        json={"code": "EQ-GLOBAL", "name": "Loader", "organization_id": None},
        headers=headers,
    )

    assert organization.status_code == 201
    assert equipment.status_code == 409
    assert equipment.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_idempotency_key_rejects_changed_request_body(client: TestClient) -> None:
    headers = writer_headers(client, "body-key")
    first = client.post(
        "/api/equipment",
        json={"code": "EQ-BODY-A", "name": "A", "organization_id": None},
        headers=headers,
    )
    second = client.post(
        "/api/equipment",
        json={"code": "EQ-BODY-B", "name": "B", "organization_id": None},
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_equipment_unique_conflict_is_mapped_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = writer_headers(client, "database-conflict")
    real_flush = Session.flush

    def conflicting_flush(session: Session, objects: object = None) -> None:
        if any(isinstance(item, Equipment) for item in session.new):
            raise IntegrityError("insert", {}, RuntimeError("unique conflict"))
        real_flush(session, objects)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.post(
        "/api/equipment",
        json={"code": "EQ-RACE", "name": "Loader", "organization_id": None},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"


@pytest.mark.parametrize("resource", ["role", "user"])
def test_identity_unique_conflict_is_mapped_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, resource: str
) -> None:
    token = create_user_token(client, ["identity:write"])
    with client.app.state.session_factory() as session:
        role = Role(name="existing-role")
        session.add(role)
        session.commit()
        role_id = role.id

    real_flush = Session.flush
    conflict_type = Role if resource == "role" else User

    def conflicting_flush(session: Session, objects: object = None) -> None:
        if any(isinstance(item, conflict_type) for item in session.new):
            raise IntegrityError("insert", {}, RuntimeError("unique conflict"))
        real_flush(session, objects)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": f"conflict-{resource}"}
    if resource == "role":
        response = client.post(
            "/api/roles",
            json={"name": "new-role", "permission_codes": []},
            headers=headers,
        )
        expected_code = "ROLE_NAME_EXISTS"
    else:
        response = client.post(
            "/api/users",
            json={"username": "new-user", "password": "password", "role_ids": [role_id]},
            headers=headers,
        )
        expected_code = "USERNAME_EXISTS"

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == expected_code


def test_timestamp_columns_keep_utc_and_update_semantics() -> None:
    assert AuditEvent.__table__.c.created_at.type.timezone is True
    assert User.__table__.c.updated_at.onupdate is not None
