from collections.abc import Callable
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    formula: str
    period: str
    allowed_dimensions: tuple[str, ...] = (
        "equipment_id",
        "equipment_type",
        "organization_id",
    )
    examples: tuple[str, ...] = ()


_METRIC_NAMES = (
    "fault_count", "fault_rate", "critical_fault_count", "repair_count",
    "repair_completion_rate", "mean_time_to_repair", "mean_time_between_failures",
    "pending_fault_count", "in_repair_count", "completed_repair_count",
    "downtime_hours", "availability_rate", "utilization_rate", "operating_hours",
    "maintenance_cost", "parts_cost", "labor_cost", "repeat_fault_rate",
    "first_time_fix_rate", "overdue_work_order_count", "work_order_count",
    "work_order_completion_rate", "inspection_pass_rate", "safety_incident_count",
    "attachment_failure_count", "agent_fault_draft_count", "agent_submit_rate",
    "health_score_average", "health_score_minimum", "health_score_change",
    "health_grade_a_count", "health_grade_b_count", "health_grade_c_count",
    "health_grade_d_count", "health_grade_e_count", "alert_count",
    "alarm_code_count", "hydraulic_fault_count", "electrical_fault_count",
    "drive_fault_count",
)

METRIC_CATALOG = tuple(
    MetricDefinition(
        id=name,
        name=name.replace("_", " ").title(),
        formula=f"controlled service formula for {name}",
        period="日/周/月",
        examples=(f"按 equipment_id 查询 {name}",),
    )
    for name in _METRIC_NAMES
)


class MetricQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_ids: list[str] = Field(min_length=1, max_length=5)
    dimensions: dict[str, str] = Field(default_factory=dict)
    period_start: date
    period_end: date

    @model_validator(mode="after")
    def validate_period(self) -> "MetricQuery":
        if self.period_end < self.period_start:
            raise ValueError("period_end must not precede period_start")
        return self


class InvalidMetricQueryError(ValueError):
    pass


class ServiceUnavailableError(RuntimeError):
    pass


class MetricQueryService:
    def __init__(
        self,
        query_backend: Callable[[MetricQuery], list[dict[str, Any]]],
        catalog: tuple[MetricDefinition, ...] = METRIC_CATALOG,
    ) -> None:
        self._backend = query_backend
        self._catalog = {item.id: item for item in catalog}

    def query(self, request: MetricQuery) -> dict[str, Any]:
        unknown = [item for item in request.metric_ids if item not in self._catalog]
        if unknown:
            raise InvalidMetricQueryError(f"unknown metric: {', '.join(unknown)}")
        allowed = set().union(*(set(item.allowed_dimensions) for item in self._catalog.values()))
        invalid_dimensions = sorted(set(request.dimensions) - allowed)
        if invalid_dimensions:
            raise InvalidMetricQueryError(
                f"invalid dimensions: {', '.join(invalid_dimensions)}"
            )
        try:
            items = self._backend(request)
        except (ServiceUnavailableError, TimeoutError) as error:
            return {"status": "UNAVAILABLE", "items": [], "error": str(error)}
        return {
            "status": "OK",
            "items": items,
            "period_start": request.period_start.isoformat(),
            "period_end": request.period_end.isoformat(),
        }


class HealthScoreReader:
    def __init__(self, reader: Callable[[str], dict[str, Any]]) -> None:
        self._reader = reader

    def read(self, equipment_id: str) -> dict[str, Any]:
        try:
            value = self._reader(equipment_id)
        except (ServiceUnavailableError, TimeoutError):
            return {"status": "UNAVAILABLE", "score": None, "grade": None, "components": []}
        return {"status": "OK", **value}
