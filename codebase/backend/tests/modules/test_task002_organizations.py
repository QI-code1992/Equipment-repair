from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.equipment.models import Equipment, OrganizationType
from tests.modules.support import create_user_token


def organization_writer_headers(client: TestClient) -> dict[str, str]:
    _, token = create_user_token(
        client,
        username="organization-writer",
        role_code="organization-writer",
        permission_codes=["organization:read", "organization:write"],
    )
    return {"Authorization": f"Bearer {token}"}


def root_organization(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    roots = [
        item
        for item in client.get("/api/organizations", headers=headers).json()
        if item["type"] == OrganizationType.ROOT.value
    ]
    assert len(roots) == 1
    return roots[0]


def organization_payload(
    *,
    organization_type: str,
    code: str,
    name: str,
    parent_id: str,
    enabled: bool = True,
) -> dict[str, object]:
    return {
        "type": organization_type,
        "code": code,
        "name": name,
        "parent_id": parent_id,
        "sort_order": 0,
        "enabled": enabled,
        "remark": "",
    }


def create_organization_response(
    client: TestClient,
    headers: dict[str, str],
    parent_id: str,
    organization_type: str,
    code: str,
    name: str,
    *,
    key: str,
):
    return client.post(
        "/api/organizations",
        headers={**headers, "Idempotency-Key": key},
        json=organization_payload(
            organization_type=organization_type,
            code=code,
            name=name,
            parent_id=parent_id,
        ),
    )


def create_organization(
    client: TestClient,
    headers: dict[str, str],
    parent_id: str,
    organization_type: str,
    code: str,
    name: str,
) -> dict[str, object]:
    response = create_organization_response(
        client,
        headers,
        parent_id,
        organization_type,
        code,
        name,
        key=f"create-{code}",
    )
    assert response.status_code == 201, response.text
    return response.json()


def organization_tree(client: TestClient):
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    factory = create_organization(client, headers, root["id"], "FACTORY", "FAC-001", "一厂")
    workshop = create_organization(client, headers, factory["id"], "WORKSHOP", "WS-001", "总装")
    line = create_organization(client, headers, workshop["id"], "LINE", "LINE-001", "一线")
    return factory, workshop, line, headers


def update_payload(node: dict[str, object], *, enabled: bool) -> dict[str, object]:
    return {
        "code": node["code"],
        "name": node["name"],
        "sort_order": node["sort_order"],
        "enabled": enabled,
        "remark": node["remark"],
    }


def test_organization_hierarchy_and_uniqueness_rules(client: TestClient) -> None:
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    factory = create_organization(client, headers, root["id"], "FACTORY", "FAC-001", "一厂")
    workshop = create_organization(client, headers, factory["id"], "WORKSHOP", "WS-001", "总装")
    create_organization(client, headers, workshop["id"], "LINE", "LINE-001", "一线")

    invalid = create_organization_response(
        client, headers, workshop["id"], "FACTORY", "FAC-002", "二厂", key="invalid-level"
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "ORGANIZATION_LEVEL_INVALID"

    duplicate_code = create_organization_response(
        client, headers, root["id"], "FACTORY", "FAC-001", "二厂", key="duplicate-code"
    )
    assert duplicate_code.status_code == 409
    assert duplicate_code.json()["detail"]["code"] == "ORGANIZATION_CODE_EXISTS"

    duplicate_name = create_organization_response(
        client, headers, workshop["id"], "LINE", "LINE-002", "一线", key="duplicate-name"
    )
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["detail"]["code"] == "ORGANIZATION_SIBLING_NAME_EXISTS"


def test_create_requires_enabled_parent(client: TestClient) -> None:
    factory, workshop, _, headers = organization_tree(client)
    response = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": "disable-parent"},
        json=update_payload(factory, enabled=False),
    )
    assert response.status_code == 200

    blocked = create_organization_response(
        client, headers, workshop["id"], "LINE", "LINE-002", "二线", key="disabled-parent"
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "ORGANIZATION_PARENT_DISABLED"


def test_update_enforces_code_and_sibling_name_uniqueness(client: TestClient) -> None:
    factory, workshop, line, headers = organization_tree(client)
    root = root_organization(client, headers)
    other_factory = create_organization(
        client, headers, root["id"], "FACTORY", "FAC-002", "二厂"
    )
    other_line = create_organization(
        client, headers, workshop["id"], "LINE", "LINE-002", "二线"
    )

    duplicate_code = client.patch(
        f"/api/organizations/{other_factory['id']}",
        headers={**headers, "Idempotency-Key": "update-duplicate-code"},
        json=update_payload(other_factory, enabled=True) | {"code": factory["code"]},
    )
    duplicate_name = client.patch(
        f"/api/organizations/{other_line['id']}",
        headers={**headers, "Idempotency-Key": "update-duplicate-name"},
        json=update_payload(other_line, enabled=True) | {"name": line["name"]},
    )
    assert duplicate_code.status_code == 409
    assert duplicate_code.json()["detail"]["code"] == "ORGANIZATION_CODE_EXISTS"
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["detail"]["code"] == "ORGANIZATION_SIBLING_NAME_EXISTS"


def test_disabling_cascades_and_enabling_does_not_enable_descendants(client: TestClient) -> None:
    factory, workshop, line, headers = organization_tree(client)
    disabled = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": "disable-factory"},
        json=update_payload(factory, enabled=False),
    )
    assert disabled.status_code == 200
    nodes = {item["id"]: item for item in client.get("/api/organizations", headers=headers).json()}
    assert not nodes[factory["id"]]["enabled"]
    assert not nodes[workshop["id"]]["enabled"]
    assert not nodes[line["id"]]["enabled"]

    enabled = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": "enable-factory"},
        json=update_payload(factory, enabled=True),
    )
    assert enabled.status_code == 200
    nodes = {item["id"]: item for item in client.get("/api/organizations", headers=headers).json()}
    assert nodes[factory["id"]]["enabled"]
    assert not nodes[workshop["id"]]["enabled"]
    assert not nodes[line["id"]]["enabled"]


def test_root_cannot_be_updated_disabled_or_deleted(client: TestClient) -> None:
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    updated = client.patch(
        f"/api/organizations/{root['id']}",
        headers={**headers, "Idempotency-Key": "update-root"},
        json=update_payload(root, enabled=True) | {"name": "另一个根"},
    )
    disabled = client.patch(
        f"/api/organizations/{root['id']}",
        headers={**headers, "Idempotency-Key": "disable-root"},
        json=update_payload(root, enabled=False),
    )
    deleted = client.delete(f"/api/organizations/{root['id']}", headers=headers)

    for response in (updated, disabled, deleted):
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "ORGANIZATION_ROOT_PROTECTED"


def test_update_rejects_type_and_parent_id(client: TestClient) -> None:
    factory, _, _, headers = organization_tree(client)
    for field, value in (("type", "WORKSHOP"), ("parent_id", factory["id"])):
        response = client.patch(
            f"/api/organizations/{factory['id']}",
            headers={**headers, "Idempotency-Key": f"immutable-{field}"},
            json=update_payload(factory, enabled=True) | {field: value},
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "VALIDATION_ERROR"
        assert {item["field"] for item in response.json()["detail"]["fields"]} == {field}
        assert "audit_event_id" in response.json()["detail"]


def test_delete_is_protected_by_children_and_equipment(client: TestClient) -> None:
    factory, workshop, line, headers = organization_tree(client)
    with client.app.state.session_factory() as db:
        db.add(Equipment(code="EQ-ORG-REF", name="引用设备", organization_id=line["id"]))
        db.commit()

    has_children = client.delete(f"/api/organizations/{factory['id']}", headers=headers)
    has_equipment = client.delete(f"/api/organizations/{line['id']}", headers=headers)
    assert has_children.status_code == 409
    assert has_children.json()["detail"]["code"] == "ORGANIZATION_HAS_CHILDREN"
    assert has_equipment.status_code == 409
    assert has_equipment.json()["detail"]["code"] == "ORGANIZATION_HAS_EQUIPMENT"

    with client.app.state.session_factory() as db:
        equipment = db.query(Equipment).filter_by(code="EQ-ORG-REF").one()
        db.delete(equipment)
        db.commit()
    deleted = client.delete(f"/api/organizations/{line['id']}", headers=headers)
    assert deleted.status_code == 200
    with client.app.state.session_factory() as db:
        success = db.get(AuditEvent, deleted.json()["audit_event_id"])
        failure = db.get(AuditEvent, has_children.json()["detail"]["audit_event_id"])
        assert (success.action, success.result) == ("organization.delete", "success")
        assert (failure.action, failure.result) == ("organization.delete", "failure")


def test_create_idempotency_replays_one_success_audit(client: TestClient) -> None:
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    first = create_organization_response(
        client, headers, root["id"], "FACTORY", "FAC-IDEM", "幂等工厂", key="same-create"
    )
    replay = create_organization_response(
        client, headers, root["id"], "FACTORY", "FAC-IDEM", "幂等工厂", key="same-create"
    )
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    with client.app.state.session_factory() as db:
        events = list(
            db.scalars(
                select(AuditEvent).where(
                    AuditEvent.action == "organization.create",
                    AuditEvent.result == "success",
                )
            )
        )
        assert len(events) == 1
