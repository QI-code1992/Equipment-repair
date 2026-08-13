from fastapi.testclient import TestClient

from app.modules.identity.models import RoleCode
from tests.modules.support import create_user_token


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_user_management_without_view_all_is_limited_to_self(
    client: TestClient,
) -> None:
    actor_id, actor_token = create_user_token(
        client,
        username="limited-user",
        role_code=RoleCode.REPAIR_WORKER.value,
        permission_codes=[],
    )
    other_id, _ = create_user_token(
        client,
        username="other-user",
        role_code=RoleCode.LINE_OPERATOR.value,
        permission_codes=[],
    )

    response = client.get("/api/users", headers=authorization(actor_token))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [actor_id]

    own_detail = client.get(f"/api/users/{actor_id}", headers=authorization(actor_token))
    assert own_detail.status_code == 200
    denied = client.get(f"/api/users/{other_id}", headers=authorization(actor_token))
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "PERMISSION_DENIED"


def test_user_management_view_all_returns_every_user(client: TestClient) -> None:
    _, viewer_token = create_user_token(
        client,
        username="global-viewer",
        role_code=RoleCode.EQUIPMENT_ADMIN.value,
        permission_codes=["user_management.view_all"],
    )
    other_id, _ = create_user_token(
        client,
        username="visible-user",
        role_code=RoleCode.LINE_OPERATOR.value,
        permission_codes=[],
    )

    response = client.get("/api/users", headers=authorization(viewer_token))
    assert response.status_code == 200
    assert {item["username"] for item in response.json()} == {
        "global-viewer", "visible-user"
    }
    detail = client.get(f"/api/users/{other_id}", headers=authorization(viewer_token))
    assert detail.status_code == 200
    assert detail.json()["id"] == other_id


def test_enabled_custom_role_can_grant_view_all(client: TestClient) -> None:
    actor_id, actor_token = create_user_token(
        client,
        username="legacy-viewer",
        role_code="LEGACY_CUSTOM_ROLE",
        permission_codes=["user_management.view_all"],
    )
    hidden_user_id, _ = create_user_token(
        client,
        username="hidden-user",
        role_code=RoleCode.LINE_OPERATOR.value,
        permission_codes=[],
    )

    response = client.get("/api/users", headers=authorization(actor_token))
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {actor_id, hidden_user_id}
