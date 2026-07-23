from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class FaultDraft(BaseModel):
    """受控的 AI 故障草稿；正式业务写入仍由业务 API 完成。"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    equipment_id: str = Field(min_length=1, max_length=36)
    urgency: str = Field(min_length=1, max_length=30)
    symptom: str = Field(min_length=1, max_length=4000)
    occurred_at: AwareDatetime | None = None
    duration_minutes: int | None = Field(default=None, ge=0, le=10 * 365 * 24 * 60)
    possible_location: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    attachment_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_multiple_equipment(self) -> "FaultDraft":
        if not isinstance(self.equipment_id, str):
            raise ValueError("exactly one equipment_id is required")
        if self.occurred_at is not None:
            occurred_at = self.occurred_at
            if occurred_at > datetime.now(UTC):
                raise ValueError("occurred_at cannot be in the future")
        return self


class FaultPreview(BaseModel):
    model_config = ConfigDict(frozen=True)

    draft: FaultDraft
    missing_fields: tuple[str, ...] = ()


class MissingFaultFieldsError(ValueError):
    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__(f"missing required fault fields: {', '.join(fields)}")


class SubmissionNotConfirmedError(ValueError):
    pass


class FaultReportingAgent:
    """实现收集、只读预览和人工确认门禁，不自行写数据库。"""

    def __init__(self, submitter: Callable[[FaultDraft], str] | None = None) -> None:
        self._submitter = submitter

    def preview(self, draft: FaultDraft) -> FaultPreview:
        missing = [
            name
            for name, value in (
                ("occurred_at", draft.occurred_at),
                ("duration_minutes", draft.duration_minutes),
            )
            if value is None
        ]
        if missing:
            raise MissingFaultFieldsError(missing)
        return FaultPreview(draft=draft)

    def submit(self, preview: FaultPreview, *, confirmed: bool) -> dict[str, Any]:
        if not confirmed:
            raise SubmissionNotConfirmedError("human confirmation is required")
        if self._submitter is None:
            raise RuntimeError("fault business API is unavailable")
        fault_id = self._submitter(preview.draft)
        return {"fault_report_id": fault_id, "status": "AI_DRAFT"}
