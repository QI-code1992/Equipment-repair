from datetime import date

import pytest

from app.modules.agents.metric_query import (
    HealthScoreReader,
    InvalidMetricQueryError,
    MetricQuery,
    MetricQueryService,
    METRIC_CATALOG,
    ServiceUnavailableError,
)
from tests.modules.support import create_user_token


def test_catalog_is_fixed_and_contains_forty_metrics() -> None:
    assert len(METRIC_CATALOG) == 40
    assert all(item.id and item.name and item.formula for item in METRIC_CATALOG)


def test_metric_query_rejects_more_than_five_metrics_and_unknown_dimensions() -> None:
    with pytest.raises(ValueError):
        MetricQuery(
            metric_ids=[item.id for item in METRIC_CATALOG[:6]],
            dimensions={},
            period_start=date(2026, 1, 1),
            period_end=date(2026, 7, 1),
        )

    with pytest.raises(InvalidMetricQueryError):
        MetricQueryService(lambda _: []).query(
            MetricQuery(
                metric_ids=[METRIC_CATALOG[0].id],
                dimensions={"not_allowed": "x"},
                period_start=date(2026, 1, 1),
                period_end=date(2026, 7, 1),
            )
        )


def test_metric_query_does_not_fabricate_values_when_service_fails() -> None:
    query = MetricQuery(
        metric_ids=[METRIC_CATALOG[0].id],
        dimensions={},
        period_start=date(2026, 1, 1),
        period_end=date(2026, 7, 1),
    )

    def failing_service(_: MetricQuery) -> list[dict[str, object]]:
        raise ServiceUnavailableError("metrics backend unavailable")

    result = MetricQueryService(failing_service).query(query)
    assert result == {"status": "UNAVAILABLE", "items": []}


def test_health_score_reader_returns_controlled_failure_without_score() -> None:
    reader = HealthScoreReader(lambda _: (_ for _ in ()).throw(ServiceUnavailableError("health unavailable")))

    result = reader.read("equipment-1")

    assert result == {"status": "UNAVAILABLE", "score": None, "grade": None, "components": []}


def test_metric_catalog_api_is_read_only_and_returns_fixed_catalog(client) -> None:
    _, token = create_user_token(
        client,
        username="metric-reader",
        role_code="LINE_OPERATOR",
        permission_codes=["equipment:read"],
    )

    response = client.get(
        "/api/metrics/catalog", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 40
    assert all("create" not in item and "delete" not in item for item in response.json())


def test_metric_query_api_returns_unavailable_without_fabricated_value(client) -> None:
    _, token = create_user_token(
        client,
        username="metric-reader-2",
        role_code="REPAIR_WORKER",
        permission_codes=["equipment:read"],
    )

    response = client.post(
        "/api/metrics/query-batch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "metric_ids": [METRIC_CATALOG[0].id],
            "dimensions": {},
            "period_start": "2026-01-01",
            "period_end": "2026-07-01",
        },
    )

    assert response.status_code == 503
    assert response.json()["status"] == "UNAVAILABLE"
    assert response.json()["items"] == []


def test_health_score_agent_boundary_returns_controlled_unavailable_status(client) -> None:
    _, token = create_user_token(
        client,
        username="health-reader",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )

    response = client.get(
        "/api/agent/health-score/equipment-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "UNAVAILABLE",
        "score": None,
        "grade": None,
        "components": [],
    }


def test_health_score_agent_boundary_reads_only_from_injected_service(client) -> None:
    from app.modules.agents.metric_query import HealthScoreReader

    client.app.state.health_score_reader = HealthScoreReader(
        lambda equipment_id: {
            "equipment_id": equipment_id,
            "score": 91,
            "grade": "A",
            "components": [],
        }
    )
    _, token = create_user_token(
        client,
        username="health-reader-2",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )

    response = client.get(
        "/api/agent/health-score/equipment-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["score"] == 91
