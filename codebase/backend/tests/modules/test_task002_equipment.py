import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.modules.equipment.router as equipment_router
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from app.modules.equipment.models import Equipment, OrganizationType
from app.modules.identity.bootstrap import bootstrap_admin
from app.modules.identity.models import Role, RoleCode


VALID_EQUIPMENT = {
    "code": "EQ-001",
    "name": "电驱装载机",
    "model": "ZL956EV",
    "type": "新能源装载机",
    "manufacturer": "示例制造商",
    "manufactured_at": "2026-01-10",
    "commissioned_at": "2026-02-01",
    "operating_hours": 128.5,
    "status": "NORMAL",
    "organization_id": "replace-with-line-id",
    "owner_user_id": "replace-with-user-id",
    "image_refs": [
        {"object_key": "equipment/EQ-001/front.jpg", "filename": "front.jpg"}
    ],
}


def test_equipment_model_storage_matches_write_contract() -> None:
    assert Equipment.__table__.c.model.type.length == 200


def _headers(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def _role_id(client: TestClient, code: RoleCode) -> str:
    with client.app.state.session_factory() as db:
        role = db.scalar(select(Role).where(Role.code == code.value))
        assert role is not None
        return role.id


def _create_organization(
    client: TestClient,
    token: str,
    *,
    parent_id: str,
    organization_type: str,
    code: str,
    enabled: bool = True,
) -> dict[str, object]:
    response = client.post(
        "/api/organizations",
        headers=_headers(token, f"create-{code}"),
        json={
            "type": organization_type,
            "code": code,
            "name": code,
            "parent_id": parent_id,
            "sort_order": 0,
            "enabled": enabled,
            "remark": "",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def valid_equipment_payload(
    client: TestClient,
) -> tuple[dict[str, object], dict[str, str]]:
    with client.app.state.session_factory() as db:
        bootstrap_admin(db, "equipment-admin", "equipment-password")
    login = client.post(
        "/api/auth/login",
        json={"username": "equipment-admin", "password": "equipment-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    owner = client.post(
        "/api/users",
        headers=_headers(token, "create-equipment-owner"),
        json={
            "username": "equipment-owner",
            "password": "equipment-owner-password",
            "role_ids": [_role_id(client, RoleCode.LINE_OPERATOR)],
        },
    )
    assert owner.status_code == 201, owner.text
    root = next(
        item
        for item in client.get("/api/organizations", headers=_headers(token)).json()
        if item["type"] == OrganizationType.ROOT.value
    )
    factory = _create_organization(
        client, token, parent_id=root["id"], organization_type="FACTORY", code="FAC-EQ"
    )
    workshop = _create_organization(
        client,
        token,
        parent_id=factory["id"],
        organization_type="WORKSHOP",
        code="WS-EQ",
    )
    line = _create_organization(
        client,
        token,
        parent_id=workshop["id"],
        organization_type="LINE",
        code="LINE-EQ",
    )
    payload = {
        **VALID_EQUIPMENT,
        "organization_id": line["id"],
        "owner_user_id": owner.json()["id"],
    }
    return payload, _headers(token)


def invalid_equipment_facts(
    client: TestClient,
) -> tuple[dict[str, object], dict[str, str], str, str, str]:
    payload, headers = valid_equipment_payload(client)
    token = headers["Authorization"].removeprefix("Bearer ")
    organizations = client.get("/api/organizations", headers=headers).json()
    factory_id = next(item["id"] for item in organizations if item["type"] == "FACTORY")
    workshop_id = next(item["id"] for item in organizations if item["type"] == "WORKSHOP")
    disabled_line = _create_organization(
        client,
        token,
        parent_id=workshop_id,
        organization_type="LINE",
        code="LINE-DISABLED",
        enabled=False,
    )
    disabled_owner = client.post(
        "/api/users",
        headers=_headers(token, "create-disabled-owner"),
        json={
            "username": "disabled-owner",
            "password": "disabled-owner-password",
            "role_ids": [_role_id(client, RoleCode.LINE_OPERATOR)],
        },
    )
    assert disabled_owner.status_code == 201
    disabled = client.patch(
        f"/api/users/{disabled_owner.json()['id']}",
        headers=_headers(token, "disable-owner"),
        json={
            "enabled": False,
            "role_ids": [_role_id(client, RoleCode.LINE_OPERATOR)],
        },
    )
    assert disabled.status_code == 200
    return payload, headers, factory_id, disabled_line["id"], disabled_owner.json()["id"]


def test_equipment_create_read_update_uses_full_contract(client: TestClient) -> None:
    payload, headers = valid_equipment_payload(client)
    created = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "create-equipment"},
        json=payload,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert {key: body[key] for key in payload} == payload
    assert {"id", "created_at", "updated_at", "audit_event_id"} <= body.keys()

    detail = client.get(f"/api/equipment/{body['id']}", headers=headers)
    listed = client.get("/api/equipment", headers=headers)
    assert detail.status_code == listed.status_code == 200
    assert detail.json()["code"] == payload["code"]
    assert listed.json() == [detail.json()]

    changed = {
        **payload,
        "code": "EQ-002",
        "name": "更新后的设备",
        "operating_hours": 256.75,
        "status": "REPAIRING",
        "image_refs": [],
    }
    updated = client.patch(
        f"/api/equipment/{body['id']}",
        headers={**headers, "Idempotency-Key": "update-equipment"},
        json=changed,
    )
    assert updated.status_code == 200, updated.text
    assert {key: updated.json()[key] for key in changed} == changed
    assert "audit_event_id" in updated.json()


@pytest.mark.parametrize(
    ("change", "code", "status"),
    [
        ({"organization_id": "factory"}, "EQUIPMENT_ORGANIZATION_NOT_LINE", 409),
        ({"organization_id": "disabled_line"}, "EQUIPMENT_ORGANIZATION_DISABLED", 409),
        ({"organization_id": "missing"}, "EQUIPMENT_ORGANIZATION_NOT_FOUND", 404),
        ({"owner_user_id": "disabled_owner"}, "EQUIPMENT_OWNER_DISABLED", 409),
        ({"owner_user_id": "missing"}, "EQUIPMENT_OWNER_NOT_FOUND", 404),
        ({"operating_hours": -0.01}, "VALIDATION_ERROR", 422),
    ],
)
def test_equipment_rejects_invalid_domain_facts(
    client: TestClient, change: dict[str, object], code: str, status: int
) -> None:
    payload, headers, factory_id, disabled_line_id, disabled_user_id = (
        invalid_equipment_facts(client)
    )
    replacements = {
        "factory": factory_id,
        "disabled_line": disabled_line_id,
        "disabled_owner": disabled_user_id,
        "missing": "missing-id",
    }
    case = {
        key: replacements.get(value, value) if isinstance(value, str) else value
        for key, value in ({**payload, **change}).items()
    }
    response = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": f"invalid-{code}"},
        json=case,
    )
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert "audit_event_id" in response.json()["detail"]


def test_equipment_write_schemas_forbid_unknown_and_attachment_content(
    client: TestClient,
) -> None:
    payload, headers = valid_equipment_payload(client)
    cases = [
        {**payload, "enabled": True},
        {
            **payload,
            "image_refs": [
                {
                    "object_key": "equipment/EQ-001/front.jpg",
                    "filename": "front.jpg",
                    "content": "base64-secret-body",
                }
            ],
        },
    ]
    for index, case in enumerate(cases):
        response = client.post(
            "/api/equipment",
            headers={**headers, "Idempotency-Key": f"forbid-extra-{index}"},
            json=case,
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "VALIDATION_ERROR"
        assert "audit_event_id" in response.json()["detail"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(Equipment)) is None
        failure_events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.action == "equipment.create",
                    AuditEvent.result == "failure",
                )
            )
        )
    assert "base64-secret-body" not in str(
        [event.metadata_json for event in failure_events]
    )


def test_equipment_code_is_unique_on_create_and_update(client: TestClient) -> None:
    payload, headers = valid_equipment_payload(client)
    first = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "unique-first"},
        json=payload,
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "unique-create"},
        json={**payload, "name": "重复设备"},
    )
    second = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "unique-second"},
        json={**payload, "code": "EQ-SECOND"},
    )
    update_duplicate = client.patch(
        f"/api/equipment/{second.json()['id']}",
        headers={**headers, "Idempotency-Key": "unique-update"},
        json=payload,
    )
    for response in (duplicate, update_duplicate):
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"
        assert "audit_event_id" in response.json()["detail"]


@pytest.mark.parametrize("method", ["POST", "PATCH"])
def test_equipment_database_unique_race_maps_to_stable_conflict(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    payload, headers = valid_equipment_payload(client)
    equipment_id = "new"
    if method == "PATCH":
        created = client.post(
            "/api/equipment",
            headers={**headers, "Idempotency-Key": "race-seed"},
            json=payload,
        )
        assert created.status_code == 201
        equipment_id = created.json()["id"]
        payload = {**payload, "code": "EQ-RACE"}

    original_flush = Session.flush

    def conflicting_flush(session: Session, *args, **kwargs) -> None:
        if any(isinstance(item, Equipment) for item in session.new | session.dirty):
            raise IntegrityError(
                "equipment write",
                {},
                sqlite3.IntegrityError("UNIQUE constraint failed: equipment.code"),
            )
        original_flush(session, *args, **kwargs)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    monkeypatch.setattr(
        equipment_router,
        "equipment_code_exists",
        lambda *args, **kwargs: False,
        raising=False,
    )
    response = (
        client.post(
            "/api/equipment",
            headers={**headers, "Idempotency-Key": "race-create"},
            json=payload,
        )
        if method == "POST"
        else client.patch(
            f"/api/equipment/{equipment_id}",
            headers={**headers, "Idempotency-Key": "race-update"},
            json=payload,
        )
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"
    assert "audit_event_id" in response.json()["detail"]


def test_equipment_unknown_database_conflict_is_not_mislabeled_as_duplicate_code(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, headers = valid_equipment_payload(client)

    original_flush = Session.flush

    def conflicting_flush(session: Session, *args, **kwargs) -> None:
        if any(isinstance(item, Equipment) for item in session.new):
            raise IntegrityError(
                "equipment write",
                {},
                sqlite3.IntegrityError("FOREIGN KEY constraint failed"),
            )
        original_flush(session, *args, **kwargs)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "unknown-conflict"},
        json=payload,
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EQUIPMENT_CONFLICT"
    assert "audit_event_id" in response.json()["detail"]


def test_equipment_success_is_idempotent_and_audited_once(client: TestClient) -> None:
    payload, headers = valid_equipment_payload(client)
    request_headers = {**headers, "Idempotency-Key": "same-equipment-create"}
    first = client.post("/api/equipment", headers=request_headers, json=payload)
    replay = client.post("/api/equipment", headers=request_headers, json=payload)
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    with client.app.state.session_factory() as db:
        events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.action == "equipment.create",
                    AuditEvent.result == "success",
                )
            )
        )
        records = list(db.scalars(select(IdempotencyRecord)))
        item = db.scalar(select(Equipment).where(Equipment.code == payload["code"]))
    assert len(events) == 1
    assert any(record.idempotency_key == "same-equipment-create" for record in records)
    assert item is not None and item.image_refs == payload["image_refs"]


def test_equipment_has_no_physical_delete_endpoint(client: TestClient) -> None:
    payload, headers = valid_equipment_payload(client)
    created = client.post(
        "/api/equipment",
        headers={**headers, "Idempotency-Key": "no-delete-create"},
        json=payload,
    )
    response = client.delete(f"/api/equipment/{created.json()['id']}", headers=headers)
    assert response.status_code == 405
