from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.maintenance.models import (
    DiagnosisDraft,
    DiagnosisDraftStatus,
)
from tests.modules.support import create_user_token, valid_equipment_body


def auth_headers(token: str, *, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def create_equipment(
    client: TestClient,
    *,
    status: str = "NORMAL",
    equipment_type: str = "LOADER",
    model: str = "MODEL-1",
) -> str:
    _, token = create_user_token(
        client,
        username=f"equipment-admin-{uuid4().hex[:8]}",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["equipment:write"],
    )
    body = valid_equipment_body(client, code=f"EQ-{uuid4().hex[:8]}")
    body["status"] = status
    body["type"] = equipment_type
    body["model"] = model
    response = client.post(
        "/api/equipment",
        headers=auth_headers(token, key=f"equipment-{uuid4()}"),
        json=body,
    )
    assert response.status_code == 201
    return response.json()["id"]


def fault_reporter(client: TestClient) -> tuple[str, str]:
    return create_user_token(
        client,
        username=f"fault-reporter-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=["fault:create"],
    )


def repairer(client: TestClient) -> tuple[str, str]:
    return create_user_token(
        client,
        username=f"repairer-{uuid4().hex[:8]}",
        role_code="REPAIR_WORKER",
        permission_codes=["fault:repair", "fault:close", "maintenance:view"],
    )


def valid_fault_body(
    equipment_id: str,
    *,
    symptom: str = "hydraulic pressure loss",
) -> dict[str, object]:
    return {
        "equipment_id": equipment_id,
        "urgency": "HIGH",
        "symptom": symptom,
        "occurred_at": datetime.now(UTC).isoformat(),
        "possible_location": "main pump",
        "description": "pressure falls under load",
        "attachment_refs": [
            {
                "object_key": "faults/reference-1.jpg",
                "filename": "reference-1.jpg",
                "size_bytes": 1024,
                "content_type": "image/jpeg",
            }
        ],
    }


def create_fault(
    client: TestClient,
    equipment_id: str,
    *,
    symptom: str = "hydraulic pressure loss",
) -> str:
    _, token = fault_reporter(client)
    response = client.post(
        "/api/fault-reports",
        headers=auth_headers(token, key=f"fault-{uuid4()}"),
        json=valid_fault_body(equipment_id, symptom=symptom),
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_diagnosis_draft(
    client: TestClient,
    fault_id: str,
    *,
    status: DiagnosisDraftStatus = DiagnosisDraftStatus.DIAGNOSIS_READY,
    adopted: bool = False,
) -> str:
    with client.app.state.session_factory() as db:
        draft = DiagnosisDraft(
            fault_report_id=fault_id,
            status=status,
            allowed_prefill={
                "fault_type": "hydraulic",
                "actual_cause": "suspected seal wear",
                "actual_solution": "inspect and replace seal",
                "parts_replacement_notes": "prepare seal kit",
                "unknown_field": "must not copy",
                "password": "prefill-secret",
            },
            read_only_summary={
                "symptom": "pressure loss",
                "key_evidence": ["pressure drops under load"],
                "verification_results": ["leak observed"],
                "root_cause": "seal wear",
                "recommendations": ["replace seal", "retest pressure"],
                "raw_chain_of_thought": "must not copy",
                "attachment_content": "binary-secret",
                "token": "summary-secret",
            },
            adopted_at=datetime.now(UTC) if adopted else None,
        )
        db.add(draft)
        db.commit()
        return draft.id


def start_repair(
    client: TestClient,
    fault_id: str,
    *,
    token: str | None = None,
    mode: str = "DIRECT",
    diagnosis_draft_id: str | None = None,
) -> tuple[str, str]:
    if token is None:
        _, token = repairer(client)
    body: dict[str, object] = {"mode": mode}
    if diagnosis_draft_id is not None:
        body["diagnosis_draft_id"] = diagnosis_draft_id
    response = client.post(
        f"/api/fault-reports/{fault_id}/start-repair",
        headers=auth_headers(token, key=f"start-{uuid4()}"),
        json=body,
    )
    assert response.status_code == 200
    return response.json()["work_order_id"], token
