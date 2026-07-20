import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.modules.audit.http import response_detail


def test_http_detail_uses_safe_recursive_whitelist(client: TestClient) -> None:
    @client.app.post("/api/test-sensitive-detail", name="test.fail")
    def fail_with_sensitive_detail() -> None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TEST_FAILED",
                "message": "Safe message",
                "password": "plain-password",
                "authorization": "Bearer response-token",
                "sql": "SELECT password FROM users",
                "fields": [
                    {
                        "field": "password",
                        "type": "invalid",
                        "authorization": "Bearer nested-token",
                    }
                ],
            },
        )

    response = client.post("/api/test-sensitive-detail", json={})

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert set(detail) == {"code", "message", "fields", "audit_event_id"}
    assert detail["fields"] == {"password": "invalid"}
    rendered = json.dumps(detail)
    assert "plain-password" not in rendered
    assert "response-token" not in rendered
    assert "nested-token" not in rendered
    assert "SELECT password" not in rendered


def test_non_dict_http_detail_uses_complete_safe_shape(client: TestClient) -> None:
    @client.app.post("/api/test-string-detail", name="test.fail")
    def fail_with_string_detail() -> None:
        raise HTTPException(status_code=400, detail="SELECT secret-password")

    response = client.post("/api/test-string-detail", json={})

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert set(detail) == {"code", "message", "fields", "audit_event_id"}
    assert detail == {
        "code": "REQUEST_FAILED",
        "message": "REQUEST_FAILED",
        "fields": {},
        "audit_event_id": detail["audit_event_id"],
    }
    assert "secret-password" not in response.text


@pytest.mark.parametrize(
    ("code", "fields"),
    [
        ("IDEMPOTENCY_KEY_REUSED", {"idempotency_key": "conflict"}),
        ("USERNAME_EXISTS", {"username": "duplicate"}),
        ("ORGANIZATION_CODE_EXISTS", {"code": "duplicate"}),
        ("ORGANIZATION_SIBLING_NAME_EXISTS", {"name": "duplicate"}),
        ("EQUIPMENT_CODE_EXISTS", {"code": "duplicate"}),
    ],
)
def test_stable_error_codes_supply_contract_fields(
    code: str, fields: dict[str, str],
) -> None:
    assert response_detail({"code": code}, None)["fields"] == fields
