import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url

import app.modules.maintenance.router as maintenance_router
from app.main import create_app
from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, EquipmentStatus
from app.modules.maintenance.models import FaultReport, WorkOrder
from tests.modules.maintenance_support import auth_headers, valid_fault_body
from tests.modules.support import create_user_token, valid_equipment_body


POSTGRES_DSN = os.getenv("TASK003_POSTGRES_DSN")
ALLOW_DESTRUCTIVE_TESTS = os.getenv("TASK003_ALLOW_DESTRUCTIVE_TESTS") == "1"
BACKEND_DIR = Path(__file__).parents[2]
TASK003_TABLES = {
    "diagnosis_drafts",
    "fault_reports",
    "historical_repair_cases",
    "maintenance_records",
    "work_orders",
}
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN or not ALLOW_DESTRUCTIVE_TESTS,
    reason="dedicated DSN and TASK003_ALLOW_DESTRUCTIVE_TESTS=1 are required",
)


def _require_dedicated_database() -> None:
    url = make_url(POSTGRES_DSN)
    if not str(url.database).startswith("equipment_task3_validation"):
        raise RuntimeError("TASK-003 tests require a dedicated validation database")
    if url.host not in {"127.0.0.1", "localhost", "postgres"}:
        raise RuntimeError("TASK-003 validation database host is not approved")


@pytest.fixture(scope="module")
def app() -> Iterator[FastAPI]:
    _require_dedicated_database()
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    previous_dsn = os.environ.get("POSTGRES_DSN")
    os.environ["POSTGRES_DSN"] = POSTGRES_DSN
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "0002")
        engine = create_app(
            postgres_dsn=POSTGRES_DSN,
            redis_url="redis://redis:6379/0",
        ).state.engine
        with engine.connect() as connection:
            assert connection.dialect.server_version_info[0] == 17
        assert not (TASK003_TABLES & set(inspect(engine).get_table_names()))
        command.upgrade(config, "0003_task003")
        inspector = inspect(engine)
        assert TASK003_TABLES <= set(inspector.get_table_names())
        assert {
            item["name"] for item in inspector.get_check_constraints("fault_reports")
        } == {"ck_fault_reports_status"}
        assert {
            item["name"] for item in inspector.get_unique_constraints("work_orders")
        } == {"uq_work_orders_fault_report_id", "uq_work_orders_number"}
        command.downgrade(config, "0002")
        assert not (TASK003_TABLES & set(inspect(engine).get_table_names()))
        command.upgrade(config, "head")
        assert TASK003_TABLES <= set(inspect(engine).get_table_names())
        application = create_app(
            postgres_dsn=POSTGRES_DSN,
            redis_url="redis://redis:6379/0",
        )
        yield application
        application.state.engine.dispose()
        engine.dispose()
    finally:
        if previous_dsn is None:
            os.environ.pop("POSTGRES_DSN", None)
        else:
            os.environ["POSTGRES_DSN"] = previous_dsn


def _reset_validation_data(app: FastAPI) -> None:
    with app.state.engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE historical_repair_cases, maintenance_records, "
                "work_orders, diagnosis_drafts, fault_reports, idempotency_records, "
                "audit_events, login_sessions, user_roles, users, equipment CASCADE"
            )
        )
        connection.execute(text("DELETE FROM organizations WHERE type <> 'ROOT'"))


@pytest.fixture(autouse=True)
def clean_validation_data(app: FastAPI) -> Iterator[None]:
    _reset_validation_data(app)
    yield
    _reset_validation_data(app)


def _new_user(
    client: TestClient, prefix: str, role: str, permissions: list[str]
) -> tuple[str, str]:
    return create_user_token(
        client,
        username=f"{prefix}-{uuid4().hex[:10]}",
        role_code=role,
        permission_codes=permissions,
    )


def _create_equipment(client: TestClient) -> str:
    _, token = _new_user(
        client, "pg-equipment-admin", "EQUIPMENT_ADMIN", ["equipment:write"]
    )
    response = client.post(
        "/api/equipment",
        headers=auth_headers(token, key=f"equipment-{uuid4()}"),
        json=valid_equipment_body(client, code=f"PG-EQ-{uuid4().hex[:10]}"),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _fault_payload(equipment_id: str) -> dict[str, object]:
    return {
        **valid_fault_body(equipment_id),
        "occurred_at": datetime.now(UTC).isoformat(),
    }


def _post_fault(
    app: FastAPI,
    barrier: Barrier,
    token: str,
    key: str,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    barrier.wait()
    with TestClient(app) as client:
        response = client.post(
            "/api/fault-reports",
            headers=auth_headers(token, key=key),
            json=payload,
        )
        return response.status_code, response.json()


def _start_repair(
    app: FastAPI, barrier: Barrier, token: str, fault_id: str, key: str
) -> tuple[int, dict[str, object]]:
    barrier.wait()
    with TestClient(app) as client:
        response = client.post(
            f"/api/fault-reports/{fault_id}/start-repair",
            headers=auth_headers(token, key=key),
            json={"mode": "DIRECT"},
        )
        return response.status_code, response.json()


def _disable_equipment(
    app: FastAPI,
    barrier: Barrier,
    token: str,
    equipment_id: str,
    payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    barrier.wait()
    with TestClient(app) as client:
        response = client.patch(
            f"/api/equipment/{equipment_id}",
            headers=auth_headers(token, key=f"disable-{uuid4()}"),
            json={**payload, "status": "DISABLED"},
        )
        return response.status_code, response.json()


def test_failed_fault_write_rolls_back_business_state_and_persists_failure_audit(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        equipment_id = _create_equipment(client)
        _, token = _new_user(
            client, "pg-reporter", "LINE_OPERATOR", ["fault:create"]
        )

        def fail_success_audit(*args: object, **kwargs: object) -> None:
            del args, kwargs
            raise RuntimeError("injected success audit failure")

        monkeypatch.setattr(maintenance_router, "write_audit_event", fail_success_audit)
        response = client.post(
            "/api/fault-reports",
            headers=auth_headers(token, key="rollback-fault"),
            json=_fault_payload(equipment_id),
        )

    assert response.status_code == 500
    audit_event_id = response.json()["detail"]["audit_event_id"]
    with app.state.session_factory() as db:
        equipment = db.get(Equipment, equipment_id)
        event = db.get(AuditEvent, audit_event_id)
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 0
        assert equipment is not None and equipment.status is EquipmentStatus.NORMAL
        assert event is not None and event.result == "failure"
        assert event.action == "fault_report.create"


def test_same_key_concurrent_fault_creation_replays_one_write(app: FastAPI) -> None:
    with TestClient(app) as client:
        equipment_id = _create_equipment(client)
        _, token = _new_user(
            client, "pg-reporter", "LINE_OPERATOR", ["fault:create"]
        )
    payload = _fault_payload(equipment_id)
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _post_fault, app, barrier, token, "same-fault-key", payload
            )
            for _ in range(2)
        ]
        responses = [future.result() for future in futures]

    assert [status for status, _ in responses] == [201, 201]
    assert responses[0][1] == responses[1][1]
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 1


def test_concurrent_repair_start_creates_one_work_order(app: FastAPI) -> None:
    with TestClient(app) as client:
        equipment_id = _create_equipment(client)
        _, reporter_token = _new_user(
            client, "pg-reporter", "LINE_OPERATOR", ["fault:create"]
        )
        fault = client.post(
            "/api/fault-reports",
            headers=auth_headers(reporter_token, key="fault-for-start-race"),
            json=_fault_payload(equipment_id),
        )
        assert fault.status_code == 201
        _, repair_token = _new_user(
            client, "pg-repairer", "REPAIR_WORKER", ["fault:repair"]
        )
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _start_repair,
                app,
                barrier,
                repair_token,
                fault.json()["id"],
                f"start-race-{index}",
            )
            for index in range(2)
        ]
        responses = [future.result() for future in futures]

    assert sorted(status for status, _ in responses) == [200, 409]
    with app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(WorkOrder)) == 1


def test_fault_creation_and_disable_race_has_only_valid_final_states(
    app: FastAPI,
) -> None:
    with TestClient(app) as client:
        equipment_id = _create_equipment(client)
        _, reporter_token = _new_user(
            client, "pg-reporter", "LINE_OPERATOR", ["fault:create"]
        )
        _, writer_token = _new_user(
            client,
            "pg-equipment-writer",
            "EQUIPMENT_ADMIN",
            ["equipment:read", "equipment:write"],
        )
        detail = client.get(
            f"/api/equipment/{equipment_id}", headers=auth_headers(writer_token)
        )
        assert detail.status_code == 200
        equipment_payload = {
            key: value
            for key, value in detail.json().items()
            if key not in {"id", "created_at", "updated_at"}
        }
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        fault_future = executor.submit(
            _post_fault,
            app,
            barrier,
            reporter_token,
            "fault-disable-race",
            _fault_payload(equipment_id),
        )
        disable_future = executor.submit(
            _disable_equipment,
            app,
            barrier,
            writer_token,
            equipment_id,
            equipment_payload,
        )
        fault_response = fault_future.result()
        disable_response = disable_future.result()

    assert (fault_response[0], disable_response[0]) in {(201, 409), (409, 200)}
    with app.state.session_factory() as db:
        equipment = db.get(Equipment, equipment_id)
        fault_count = db.scalar(
            select(func.count())
            .select_from(FaultReport)
            .where(FaultReport.equipment_id == equipment_id)
        )
        assert equipment is not None
        assert (equipment.status, fault_count) in {
            (EquipmentStatus.DISABLED, 0),
            (EquipmentStatus.FAULT, 1),
        }
