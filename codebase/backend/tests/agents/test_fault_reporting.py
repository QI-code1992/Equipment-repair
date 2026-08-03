from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.modules.agents.fault_reporting import (
    FaultDraft,
    FaultReportingAgent,
    MissingFaultFieldsError,
    SubmissionNotConfirmedError,
)
from tests.modules.maintenance_support import auth_headers, create_equipment, fault_reporter
from app.modules.audit.models import AuditEvent
from app.modules.maintenance.models import FaultReport


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


def test_confirmed_fault_submission_uses_existing_business_api(client) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    response = client.post(
        "/api/agent/fault-reports/submit",
        headers=auth_headers(token, key="agent-fault-submit-1"),
        json={
            "draft": valid_draft(equipment_id=equipment_id).model_dump(mode="json"),
            "confirmed": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING_ACCEPT"
    assert response.json()["audit_event_id"]


def test_fault_submission_without_confirmation_returns_reviewable_preview_without_writing_business_record(client) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    response = client.post(
        "/api/agent/fault-reports/submit",
        headers=auth_headers(token, key="agent-fault-submit-2"),
        json={
            "draft": valid_draft(equipment_id=equipment_id).model_dump(mode="json"),
            "confirmed": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "agent_status": "PREVIEW",
        "draft": valid_draft(equipment_id=equipment_id).model_dump(mode="json"),
        "missing_fields": [],
    }
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 0
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_report.submit"
            )
        ) == 0


def test_fault_submission_replays_and_rejects_idempotency_conflict_without_duplicates(client) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    headers = auth_headers(token, key="agent-fault-submit-replay")
    body = {
        "draft": valid_draft(equipment_id=equipment_id).model_dump(mode="json"),
        "confirmed": True,
    }
    first = client.post("/api/agent/fault-reports/submit", headers=headers, json=body)
    assert first.status_code == 201
    with client.app.state.session_factory() as db:
        faults_before = db.scalar(select(func.count()).select_from(FaultReport))
        audits_before = db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_report.submit"
            )
        )

    replay = client.post("/api/agent/fault-reports/submit", headers=headers, json=body)
    assert replay.status_code == 201
    assert replay.json() == first.json()
    conflict_body = {
        **body,
        "draft": valid_draft(equipment_id=equipment_id, symptom="不同故障").model_dump(mode="json"),
    }
    conflict = client.post(
        "/api/agent/fault-reports/submit", headers=headers, json=conflict_body
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == faults_before
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_report.submit"
            )
        ) == audits_before


def test_incomplete_confirmed_draft_returns_422_without_writes_or_success_idempotency(client) -> None:
    equipment_id = create_equipment(client)
    _, token = fault_reporter(client)
    headers = auth_headers(token, key="agent-fault-incomplete")
    incomplete = {
        "draft": valid_draft(
            equipment_id=equipment_id,
            occurred_at=None,
            duration_minutes=None,
        ).model_dump(mode="json"),
        "confirmed": True,
    }
    failed = client.post("/api/agent/fault-reports/submit", headers=headers, json=incomplete)

    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail["code"] == "FAULT_DRAFT_INCOMPLETE"
    assert detail["fields"] == {"occurred_at": "required", "duration_minutes": "required"}
    assert detail["audit_event_id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(FaultReport)) == 0
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_report.submit"
            )
        ) == 0

    corrected = {
        "draft": valid_draft(equipment_id=equipment_id).model_dump(mode="json"),
        "confirmed": True,
    }
    succeeded = client.post("/api/agent/fault-reports/submit", headers=headers, json=corrected)
    assert succeeded.status_code == 201
