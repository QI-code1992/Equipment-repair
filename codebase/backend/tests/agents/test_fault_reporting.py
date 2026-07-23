from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.modules.agents.fault_reporting import (
    FaultDraft,
    FaultReportingAgent,
    MissingFaultFieldsError,
    SubmissionNotConfirmedError,
)


def valid_draft(**overrides: object) -> FaultDraft:
    values: dict[str, object] = {
        "equipment_id": "equipment-1",
        "urgency": "HIGH",
        "symptom": "液压压力异常",
        "occurred_at": datetime(2026, 7, 23, 1, 0, tzinfo=UTC),
        "duration_minutes": 15,
    }
    values.update(overrides)
    return FaultDraft.model_validate(values)


def test_fault_preview_reports_required_time_and_duration_before_submit() -> None:
    agent = FaultReportingAgent()
    with pytest.raises(MissingFaultFieldsError) as error:
        agent.preview(valid_draft(occurred_at=None, duration_minutes=None))

    assert error.value.fields == ["occurred_at", "duration_minutes"]


def test_fault_submission_requires_human_confirmation_and_calls_business_writer_once() -> None:
    calls: list[dict[str, object]] = []
    agent = FaultReportingAgent(lambda draft: calls.append(draft.model_dump(mode="json")) or "fault-1")
    draft = valid_draft()

    preview = agent.preview(draft)
    with pytest.raises(SubmissionNotConfirmedError):
        agent.submit(preview, confirmed=False)
    assert calls == []

    result = agent.submit(preview, confirmed=True)
    assert result == {"fault_report_id": "fault-1", "status": "AI_DRAFT"}
    assert len(calls) == 1


def test_fault_draft_rejects_multiple_equipment_selection() -> None:
    with pytest.raises(ValidationError):
        FaultDraft(
            equipment_id=["equipment-1", "equipment-2"],
            urgency="LOW",
            symptom="异响",
        )


def test_fault_draft_rejects_future_occurrence_time() -> None:
    with pytest.raises(ValidationError):
        valid_draft(occurred_at=datetime(2099, 1, 1, tzinfo=UTC))
