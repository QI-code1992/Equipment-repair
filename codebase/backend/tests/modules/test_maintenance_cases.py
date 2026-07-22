from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.maintenance.models import HistoricalRepairCase
from tests.modules.maintenance_support import (
    auth_headers,
    create_equipment,
    create_fault,
    repairer,
    start_repair,
)
from tests.modules.support import create_user_token


def create_case(
    client: TestClient,
    *,
    equipment_type: str,
    model: str,
    symptom: str,
    completed_at: datetime,
) -> str:
    equipment_id = create_equipment(
        client, equipment_type=equipment_type, model=model
    )
    fault_id = create_fault(client, equipment_id, symptom=symptom)
    work_order_id, token = start_repair(client, fault_id)
    response = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key=f"complete-{uuid4()}"),
        json={
            "actual_cause": f"cause for {symptom}",
            "actual_solution": "replace affected component",
            "repair_result": "verified normal operation",
        },
    )
    assert response.status_code == 200
    case_id = response.json()["historical_case_id"]
    with client.app.state.session_factory() as db:
        case = db.get(HistoricalRepairCase, case_id)
        assert case is not None
        case.completed_at = completed_at
        db.commit()
    return case_id


def test_similar_cases_rank_exact_fields_then_symptom_and_recency(
    client: TestClient,
    monkeypatch,
) -> None:
    now = datetime.now(UTC)
    older_exact = create_case(
        client,
        equipment_type="LOADER",
        model="MODEL-1",
        symptom="hydraulic pressure loss",
        completed_at=now - timedelta(days=2),
    )
    newer_exact = create_case(
        client,
        equipment_type="LOADER",
        model="MODEL-1",
        symptom="hydraulic hose leak",
        completed_at=now - timedelta(days=1),
    )
    type_only = create_case(
        client,
        equipment_type="LOADER",
        model="MODEL-2",
        symptom="hydraulic valve noise",
        completed_at=now,
    )
    symptom_only = create_case(
        client,
        equipment_type="EXCAVATOR",
        model="EX-9",
        symptom="hydraulic pressure oscillation",
        completed_at=now + timedelta(hours=1),
    )
    _, token = repairer(client)
    monkeypatch.setattr(
        "socket.create_connection",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("similar-case query attempted network access")
        ),
    )

    response = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(token),
        params={
            "equipment_type": "LOADER",
            "equipment_model": "MODEL-1",
            "symptom": "hydraulic",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [
        newer_exact,
        older_exact,
        type_only,
        symptom_only,
    ]
    assert response.json()["count"] == 4
    assert all("citation" not in item for item in response.json()["items"])


def test_similar_cases_require_filter_enforce_limit_and_return_empty(
    client: TestClient,
) -> None:
    _, token = repairer(client)

    missing = client.get(
        "/api/repair-cases/similar", headers=auth_headers(token)
    )
    too_large = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(token),
        params={"equipment_type": "LOADER", "limit": 101},
    )
    empty = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(token),
        params={"equipment_model": "NO-SUCH-MODEL"},
    )

    assert missing.status_code == 422
    assert too_large.status_code == 422
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "count": 0}


def test_similar_cases_treats_sql_wildcards_as_literal_text(
    client: TestClient,
) -> None:
    create_case(
        client,
        equipment_type="LOADER",
        model="MODEL-1",
        symptom="hydraulic pressure loss",
        completed_at=datetime.now(UTC),
    )
    _, token = repairer(client)

    response = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(token),
        params={"symptom": "%_"},
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0}


def test_similar_cases_require_permission_and_do_not_write_success_audit(
    client: TestClient,
) -> None:
    _, viewer_token = repairer(client)
    _, denied_token = create_user_token(
        client,
        username=f"case-denied-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=["fault:create"],
    )
    with client.app.state.session_factory() as db:
        before = list(db.scalars(select(AuditEvent.id)))

    denied = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(denied_token),
        params={"equipment_type": "LOADER"},
    )
    allowed = client.get(
        "/api/repair-cases/similar",
        headers=auth_headers(viewer_token),
        params={"equipment_type": "LOADER"},
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    with client.app.state.session_factory() as db:
        after = list(db.scalars(select(AuditEvent.id)))
    assert len(after) == len(before) + 1
