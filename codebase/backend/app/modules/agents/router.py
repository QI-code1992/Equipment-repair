from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.modules.agents.metric_query import (
    InvalidMetricQueryError,
    METRIC_CATALOG,
    MetricQuery,
    MetricQueryService,
    ServiceUnavailableError,
)
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(tags=["agents"])


def _default_metric_service() -> MetricQueryService:
    def unavailable(_: MetricQuery) -> list[dict[str, Any]]:
        raise ServiceUnavailableError("metrics service unavailable")

    return MetricQueryService(unavailable)


@router.get("/api/metrics/catalog")
def metric_catalog(_: User = Depends(require_permission("equipment:read"))) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in METRIC_CATALOG]


@router.post("/api/metrics/query-batch", response_model=None)
def query_metrics(
    payload: MetricQuery,
    request: Request,
    _: User = Depends(require_permission("equipment:read")),
) -> dict[str, Any] | JSONResponse:
    service = getattr(request.app.state, "metric_query_service", None) or _default_metric_service()
    try:
        result = service.query(payload)
    except InvalidMetricQueryError as error:
        raise HTTPException(status_code=422, detail={"code": "INVALID_METRIC_QUERY", "message": str(error)}) from error
    if result["status"] == "UNAVAILABLE":
        return JSONResponse(status_code=503, content=result)
    return result
