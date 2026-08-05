from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.notifications.models import Notification
from tests.modules.maintenance_support import auth_headers
from tests.modules.support import build_client, create_user_token


def _user(client: TestClient, prefix: str) -> tuple[str, str]:
    return create_user_token(
        client,
        username=f"{prefix}-{uuid4().hex[:8]}",
        role_code="LINE_OPERATOR",
        permission_codes=[],
    )


def _seed_notifications(client: TestClient) -> list[str]:
    with client.app.state.session_factory() as db:
        records = [
            Notification(type="WORK_ORDER", title="工单待处理", body="请处理工单", level="warning", action_url="/work-orders/1"),
            Notification(type="SYSTEM", title="系统通知", body="系统维护完成", level="info", action_url=None),
            Notification(type="FAULT", title="故障已上报", body="新的故障报告", level="critical", action_url="/fault-reports/1"),
        ]
        db.add_all(records)
        db.commit()
        return [record.id for record in records]


def test_notifications_require_authentication() -> None:
    client = build_client()

    response = client.get("/api/notifications")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHENTICATED"


def test_authenticated_user_can_read_empty_notification_list_and_count() -> None:
    client = build_client()
    _, token = _user(client, "notification-reader")
    headers = auth_headers(token)

    response = client.get("/api/notifications", headers=headers)
    count = client.get("/api/notifications/unread-count", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "unread_count": 0}
    assert count.status_code == 200
    assert count.json() == {"unread_count": 0}


def test_notification_list_reports_unread_state_and_supports_filtering() -> None:
    client = build_client()
    notification_ids = _seed_notifications(client)
    _, token = _user(client, "notification-list")
    headers = auth_headers(token)

    marked = client.patch(f"/api/notifications/{notification_ids[0]}/read", headers=headers)
    response = client.get("/api/notifications?page=1&page_size=2", headers=headers)
    unread = client.get("/api/notifications?unread_only=true", headers=headers)

    assert marked.status_code == 200
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["unread_count"] == 2
    assert len(response.json()["items"]) == 2
    all_items = client.get("/api/notifications?page_size=100", headers=headers).json()["items"]
    assert next(item for item in all_items if item["id"] == notification_ids[0])["is_read"] is True
    assert unread.status_code == 200
    assert unread.json()["total"] == 2
    assert all(item["is_read"] is False for item in unread.json()["items"])


def test_mark_read_is_idempotent_and_read_all_is_scoped_to_current_user() -> None:
    client = build_client()
    notification_ids = _seed_notifications(client)
    _, first_token = _user(client, "notification-first")
    _, second_token = _user(client, "notification-second")

    first_headers = auth_headers(first_token)
    second_headers = auth_headers(second_token)
    first = client.patch(f"/api/notifications/{notification_ids[0]}/read", headers=first_headers)
    repeated = client.patch(f"/api/notifications/{notification_ids[0]}/read", headers=first_headers)
    assert first.status_code == 200
    assert repeated.status_code == 200
    assert client.get("/api/notifications/unread-count", headers=first_headers).json() == {"unread_count": 2}
    assert client.get("/api/notifications/unread-count", headers=second_headers).json() == {"unread_count": 3}

    all_read = client.post("/api/notifications/read-all", headers=first_headers)
    assert all_read.status_code == 200
    assert all_read.json() == {"marked_read_count": 2}
    assert client.get("/api/notifications/unread-count", headers=first_headers).json() == {"unread_count": 0}
    assert client.get("/api/notifications/unread-count", headers=second_headers).json() == {"unread_count": 3}


def test_marking_unknown_notification_returns_not_found() -> None:
    client = build_client()
    _, token = _user(client, "notification-missing")

    response = client.patch("/api/notifications/missing/read", headers=auth_headers(token))

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NOTIFICATION_NOT_FOUND"
