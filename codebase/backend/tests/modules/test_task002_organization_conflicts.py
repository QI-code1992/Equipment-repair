import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.modules.equipment.organization_router as organization_router
from app.modules.equipment.models import Organization
from tests.modules.test_task002_organizations import (
    create_organization,
    organization_tree,
    organization_writer_headers,
    root_organization,
    update_payload,
)


@pytest.mark.parametrize(
    ("message", "field", "value", "expected_code"),
    [
        (
            "UNIQUE constraint failed: organizations.code",
            "code",
            "RACE-CODE",
            "ORGANIZATION_CODE_EXISTS",
        ),
        (
            "UNIQUE constraint failed: organizations.parent_id, organizations.name",
            "name",
            "竞态名称",
            "ORGANIZATION_SIBLING_NAME_EXISTS",
        ),
        (
            "UNIQUE constraint failed: organizations.unexpected",
            "name",
            "未知竞态",
            "ORGANIZATION_CONFLICT",
        ),
    ],
)
def test_update_flush_conflicts_are_stable_and_audited(
    client: TestClient,
    monkeypatch,
    message: str,
    field: str,
    value: str,
    expected_code: str,
) -> None:
    factory, _, _, headers = organization_tree(client)
    original_flush = Session.flush

    def conflicting_flush(session: Session, *args, **kwargs) -> None:
        if any(isinstance(item, Organization) for item in session.dirty):
            raise IntegrityError("UPDATE organizations", {}, sqlite3.IntegrityError(message))
        original_flush(session, *args, **kwargs)

    monkeypatch.setattr(
        organization_router.organization_service,
        "_validate_unique",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": f"flush-{expected_code}"},
        json=update_payload(factory, enabled=True) | {field: value},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == expected_code
    assert "audit_event_id" in response.json()["detail"]


def test_delete_flush_foreign_key_conflict_is_stable_and_audited(
    client: TestClient, monkeypatch
) -> None:
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    factory = create_organization(
        client, headers, root["id"], "FACTORY", "FAC-DELETE-RACE", "删除竞态"
    )
    original_flush = Session.flush

    def conflicting_flush(session: Session, *args, **kwargs) -> None:
        if any(isinstance(item, Organization) for item in session.deleted):
            raise IntegrityError(
                "DELETE FROM organizations",
                {},
                sqlite3.IntegrityError("FOREIGN KEY constraint failed"),
            )
        original_flush(session, *args, **kwargs)

    monkeypatch.setattr(Session, "flush", conflicting_flush)
    response = client.delete(f"/api/organizations/{factory['id']}", headers=headers)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ORGANIZATION_HAS_EQUIPMENT"
    assert "audit_event_id" in response.json()["detail"]


@pytest.mark.parametrize("cycle_kind", ["self", "three-node"])
def test_disabling_invalid_sqlite_cycle_terminates_and_is_audited(
    client: TestClient, monkeypatch, cycle_kind: str
) -> None:
    factory, _, line, headers = organization_tree(client)
    with client.app.state.session_factory() as db:
        target = db.get(Organization, factory["id"])
        target.parent_id = target.id if cycle_kind == "self" else line["id"]
        db.commit()

    original_scalars = Session.scalars
    descendant_queries = 0

    def limited_scalars(session: Session, *args, **kwargs):
        nonlocal descendant_queries
        descendant_queries += 1
        if descendant_queries > 6:
            raise AssertionError("organization traversal did not terminate")
        return original_scalars(session, *args, **kwargs)

    monkeypatch.setattr(Session, "scalars", limited_scalars)
    response = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": f"invalid-cycle-{cycle_kind}"},
        json=update_payload(factory, enabled=False),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "ORGANIZATION_TREE_INVALID"
    assert "audit_event_id" in response.json()["detail"]
    assert descendant_queries <= 6
