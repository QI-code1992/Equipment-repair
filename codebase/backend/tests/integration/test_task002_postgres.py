import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url

import app.modules.equipment.router as equipment_router
import app.modules.equipment.service as equipment_service
from app.main import create_app
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from app.modules.equipment.models import Equipment, Organization, OrganizationType
from app.modules.identity.models import Role, RoleCode, User
from app.modules.identity.security import hash_password
from tests.modules.support import create_user_token, valid_equipment_body


POSTGRES_DSN = os.getenv("TASK002_POSTGRES_DSN")
ALLOW_DESTRUCTIVE_TESTS = os.getenv("TASK002_ALLOW_DESTRUCTIVE_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN or not ALLOW_DESTRUCTIVE_TESTS,
    reason="dedicated DSN and TASK002_ALLOW_DESTRUCTIVE_TESTS=1 are required",
)


@pytest.fixture(scope="module")
def app() -> FastAPI:
    url = make_url(POSTGRES_DSN)
    if url.host != "postgres" or not str(url.database).startswith(
        "equipment_task2_validation"
    ):
        raise RuntimeError("TASK-002 PostgreSQL tests require the dedicated validation DB")
    return create_app(
        postgres_dsn=POSTGRES_DSN,
        redis_url="redis://redis:6379/0",
    )


def _reset_validation_data(app: FastAPI) -> None:
    with app.state.engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE idempotency_records, audit_events, login_sessions, "
                "user_roles, role_permissions, permissions, users, equipment CASCADE"
            )
        )
        connection.execute(
            text("DELETE FROM organizations WHERE type <> 'ROOT'")
        )
        connection.execute(
            text(
                "DELETE FROM roles WHERE code NOT IN "
                "('SYSTEM_ADMIN','EQUIPMENT_ADMIN','REPAIR_WORKER','LINE_OPERATOR')"
            )
        )


@pytest.fixture(scope="module", autouse=True)
def clean_validation_data(app: FastAPI) -> Iterator[None]:
    _reset_validation_data(app)
    yield
    _reset_validation_data(app)


def _headers(token: str, key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": key,
    }


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def _create_organization(
    client: TestClient,
    token: str,
    *,
    organization_type: str,
    code_prefix: str,
    name: str,
    parent_id: str,
    sort_order: int = 0,
) -> dict[str, object]:
    response = client.post(
        "/api/organizations",
        headers=_headers(token, _unique(code_prefix)),
        json={
            "type": organization_type,
            "code": _unique(code_prefix),
            "name": name,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "enabled": True,
            "remark": "",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_concurrent_line(
    app: FastAPI,
    barrier: Barrier,
    token: str,
    workshop_id: str,
    sibling_name: str,
    index: int,
) -> int:
    barrier.wait()
    with TestClient(app) as client:
        response = client.post(
            "/api/organizations",
            headers=_headers(token, _unique(f"line-{index}")),
            json={
                "type": "LINE",
                "code": _unique(f"PG-LINE-{index}"),
                "name": sibling_name,
                "parent_id": workshop_id,
                "sort_order": index,
                "enabled": True,
                "remark": "",
            },
        )
        return response.status_code


def _post_equipment(
    app: FastAPI,
    barrier: Barrier,
    token: str,
    key: str,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    barrier.wait()
    with TestClient(app) as client:
        response = client.post(
            "/api/equipment",
            headers=_headers(token, key),
            json=payload,
        )
        return response.status_code, response.json()


def _disable_admin(
    app: FastAPI,
    barrier: Barrier,
    actor_token: str,
    target_id: str,
    role_id: str,
) -> int:
    barrier.wait()
    with TestClient(app) as client:
        response = client.patch(
            f"/api/users/{target_id}",
            headers=_headers(actor_token, _unique("disable-admin")),
            json={"enabled": False, "role_ids": [role_id]},
        )
        return response.status_code


def test_failed_equipment_write_rolls_back_and_commits_one_failure_audit(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(app) as client:
        actor_id, token = create_user_token(
            client,
            username=_unique("pg-equipment-writer"),
            role_code=RoleCode.EQUIPMENT_ADMIN.value,
            permission_codes=["equipment:write"],
        )
        code = _unique("PG-EQ")
        payload = valid_equipment_body(client, code=code)
    monkeypatch.setattr(
        equipment_router, "acquire_organization_tree_lock", lambda db: None
    )
    monkeypatch.setattr(
        equipment_service, "equipment_code_exists", lambda *args, **kwargs: False
    )
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        args = (app, barrier, token)
        first = executor.submit(_post_equipment, *args, _unique("race-a"), payload)
        second = executor.submit(_post_equipment, *args, _unique("race-b"), payload)
        responses = [first.result(), second.result()]

    assert sorted(status for status, _ in responses) == [201, 409]
    failure_body = next(body for status, body in responses if status == 409)
    assert failure_body["detail"]["fields"] == {"code": "duplicate"}
    event_id = failure_body["detail"]["audit_event_id"]
    with app.state.session_factory() as db:
        assert db.scalar(
            select(func.count()).select_from(Equipment).where(Equipment.code == code)
        ) == 1
        events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_user_id == actor_id,
                    AuditEvent.action == "equipment.create",
                )
            )
        )
        related = [
            event
            for event in events
            if event.metadata_json.get("code") == code
            or (
                isinstance(event.metadata_json.get("request"), dict)
                and event.metadata_json["request"].get("code") == code
            )
        ]
        assert sorted(event.result for event in related) == ["failure", "success"]
        assert next(event.id for event in related if event.result == "failure") == event_id


def test_concurrent_same_idempotency_key_and_body_replays_one_write(
    app: FastAPI,
) -> None:
    with TestClient(app) as client:
        actor_id, token = create_user_token(
            client,
            username=_unique("pg-idempotency-replay"),
            role_code=RoleCode.EQUIPMENT_ADMIN.value,
            permission_codes=["equipment:write"],
        )
        payload = valid_equipment_body(client, code=_unique("PG-IDEM-SAME"))
    key = _unique("pg-idem-same")
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        args = (app, barrier, token, key, payload)
        responses = [
            executor.submit(_post_equipment, *args),
            executor.submit(_post_equipment, *args),
        ]
        results = [response.result() for response in responses]

    assert [status for status, _ in results] == [201, 201]
    assert results[0][1] == results[1][1]
    with app.state.session_factory() as db:
        assert db.scalar(
            select(func.count())
            .select_from(Equipment)
            .where(Equipment.code == payload["code"])
        ) == 1
        assert db.scalar(
            select(func.count())
            .select_from(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == actor_id,
                IdempotencyRecord.idempotency_key == key,
            )
        ) == 1
        assert db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.actor_user_id == actor_id,
                AuditEvent.action == "equipment.create",
                AuditEvent.result == "success",
            )
        ) == 1


def test_concurrent_same_idempotency_key_with_changed_body_rejects_reuse(
    app: FastAPI,
) -> None:
    with TestClient(app) as client:
        actor_id, token = create_user_token(
            client,
            username=_unique("pg-idempotency-conflict"),
            role_code=RoleCode.EQUIPMENT_ADMIN.value,
            permission_codes=["equipment:write"],
        )
        first_payload = valid_equipment_body(client, code=_unique("PG-IDEM-A"))
    second_payload = {
        **first_payload,
        "code": _unique("PG-IDEM-B"),
        "name": _unique("PG Idempotency B"),
    }
    key = _unique("pg-idem-conflict")
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            _post_equipment, app, barrier, token, key, first_payload
        )
        second = executor.submit(
            _post_equipment, app, barrier, token, key, second_payload
        )
        results = [first.result(), second.result()]

    assert sorted(status for status, _ in results) == [201, 409]
    failure = next(body for status, body in results if status == 409)["detail"]
    assert failure["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert failure["fields"] == {"idempotency_key": "conflict"}
    with app.state.session_factory() as db:
        assert db.scalar(
            select(func.count())
            .select_from(Equipment)
            .where(Equipment.code.in_([first_payload["code"], second_payload["code"]]))
        ) == 1
        assert db.scalar(
            select(func.count())
            .select_from(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == actor_id,
                IdempotencyRecord.idempotency_key == key,
            )
        ) == 1
        events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.actor_user_id == actor_id,
                    AuditEvent.action == "equipment.create",
                )
            )
        )
        assert sorted(event.result for event in events) == ["failure", "success"]
        assert next(event.id for event in events if event.result == "failure") == (
            failure["audit_event_id"]
        )


def test_concurrent_system_admin_updates_keep_one_enabled_admin(
    app: FastAPI,
) -> None:
    with TestClient(app) as client:
        _, actor_token = create_user_token(
            client,
            username=_unique("pg-identity-writer"),
            role_code=RoleCode.EQUIPMENT_ADMIN.value,
            permission_codes=["identity:write"],
        )
        with app.state.session_factory() as db:
            system_role = db.scalar(
                select(Role).where(Role.code == RoleCode.SYSTEM_ADMIN.value)
            )
            assert system_role is not None
            role_id = system_role.id
            first = User(
                username=_unique("pg-system-admin-a"),
                password_hash=hash_password("correct-password"),
                roles=[system_role],
            )
            second = User(
                username=_unique("pg-system-admin-b"),
                password_hash=hash_password("correct-password"),
                roles=[system_role],
            )
            db.add_all([first, second])
            db.commit()
            first_id, second_id = first.id, second.id
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        args = (app, barrier, actor_token)
        first = executor.submit(_disable_admin, *args, first_id, role_id)
        second = executor.submit(_disable_admin, *args, second_id, role_id)
        statuses = sorted((first.result(), second.result()))

    assert statuses == [200, 409]
    with app.state.session_factory() as db:
        enabled_admins = db.scalar(
            select(func.count())
            .select_from(User)
            .join(User.roles)
            .where(Role.code == RoleCode.SYSTEM_ADMIN.value, User.enabled.is_(True))
        )
        assert enabled_admins == 1


def test_concurrent_sibling_creation_keeps_one_name(
    app: FastAPI,
) -> None:
    with TestClient(app) as client:
        _, token = create_user_token(
            client,
            username=_unique("pg-organization-writer"),
            role_code=RoleCode.EQUIPMENT_ADMIN.value,
            permission_codes=["organization:write"],
        )
        with app.state.session_factory() as db:
            root = db.scalar(
                select(Organization).where(Organization.type == OrganizationType.ROOT)
            )
            assert root is not None
            root_id = root.id

        factory = _create_organization(
            client,
            token,
            organization_type="FACTORY",
            code_prefix="PG-FAC",
            name=_unique("PG Factory"),
            parent_id=root_id,
        )
        workshop = _create_organization(
            client,
            token,
            organization_type="WORKSHOP",
            code_prefix="PG-WS",
            name=_unique("PG Workshop"),
            parent_id=str(factory["id"]),
        )

    sibling_name = _unique("PG Shared Line")
    barrier = Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as executor:
        args = (app, barrier, token, str(workshop["id"]), sibling_name)
        first = executor.submit(_create_concurrent_line, *args, 1)
        second = executor.submit(_create_concurrent_line, *args, 2)
        statuses = sorted((first.result(), second.result()))

    assert statuses == [201, 409]
    with app.state.session_factory() as db:
        assert db.scalar(
            select(func.count())
            .select_from(Organization)
            .where(
                Organization.parent_id == workshop["id"],
                Organization.name == sibling_name,
            )
        ) == 1
