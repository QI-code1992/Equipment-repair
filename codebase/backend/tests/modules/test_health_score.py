from app.modules.agents.metric_query import HealthScoreReader, ServiceUnavailableError


def test_health_score_reader_preserves_controlled_service_result() -> None:
    reader = HealthScoreReader(
        lambda equipment_id: {
            "equipment_id": equipment_id,
            "score": 87,
            "grade": "B",
            "components": [{"name": "availability", "value": 0.9}],
        }
    )

    assert reader.read("equipment-1") == {
        "status": "OK",
        "equipment_id": "equipment-1",
        "score": 87,
        "grade": "B",
        "components": [{"name": "availability", "value": 0.9}],
    }


def test_health_score_reader_does_not_fallback_to_cached_or_zero_score() -> None:
    reader = HealthScoreReader(
        lambda _: (_ for _ in ()).throw(ServiceUnavailableError("down"))
    )

    assert reader.read("equipment-1") == {
        "status": "UNAVAILABLE",
        "score": None,
        "grade": None,
        "components": [],
    }
