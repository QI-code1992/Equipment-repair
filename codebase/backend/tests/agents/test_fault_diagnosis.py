from app.modules.agents.fault_diagnosis import (
    DiagnosisContext,
    DiagnosisState,
    FaultDiagnosisAgent,
)
from app.integrations.ragflow.adapter import RetrievalResult
from tests.modules.maintenance_support import auth_headers, create_equipment, create_fault, repairer
from tests.modules.support import create_user_token
from app.modules.agent_config.models import AgentConfigModel
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from app.modules.maintenance.models import DiagnosisDraft
from sqlalchemy import func, select


def test_diagnosis_requires_concrete_alarm_code_or_negative_evidence():
    agent = FaultDiagnosisAgent(lambda _: (), lambda _: ())
    session = agent.start(
        DiagnosisContext(
            fault_report_id="fault-1",
            equipment_model="X1",
            symptom="drive overheats",
            description="torque drops under load",
            alarm_code_present=True,
        )
    )

    assert session.state is DiagnosisState.EVIDENCE_PENDING
    assert "报警码" in session.question
    session = agent.answer(session, "暂无报码")
    assert session.state is DiagnosisState.QUESTIONING
    assert session.evidence[-1].category == "alarm_code_negative"


def test_diagnosis_needs_reproduction_and_two_evidence_categories_before_adoption():
    agent = FaultDiagnosisAgent(lambda _: (), lambda _: ())
    session = agent.start(
        DiagnosisContext(
            fault_report_id="fault-1",
            equipment_model="X1",
            symptom="hydraulic pressure drops",
            description="pressure drops after warm-up",
        )
    )
    session = agent.add_evidence(session, "reproduction", "drops after warm-up")
    session = agent.add_evidence(session, "measurement", "pressure 12 bar")
    assert session.state is DiagnosisState.DIAGNOSIS_READY
    adopted = agent.adopt(session)
    assert adopted.state is DiagnosisState.ADOPTED
    assert adopted.prefill["actual_cause"]
    assert adopted.summary["key_evidence"]


def test_direct_start_discards_temporary_diagnosis_summary():
    agent = FaultDiagnosisAgent(lambda _: (), lambda _: ())
    session = agent.start(
        DiagnosisContext(
            fault_report_id="fault-1",
            equipment_model="X1",
            symptom="electrical fault",
            description="intermittent restart",
        )
    )
    direct = agent.direct_start(session)
    assert direct.state is DiagnosisState.DIRECT_START
    assert direct.prefill is None
    assert direct.summary is None


def test_diagnosis_caps_evidence_at_four_items_and_steps_at_eight():
    agent = FaultDiagnosisAgent(lambda _: (), lambda _: ())
    session = agent.start(
        DiagnosisContext(
            fault_report_id="fault-1",
            equipment_model="X1",
            symptom="electrical fault",
            description="intermittent restart",
        )
    )
    for index in range(6):
        session = agent.add_evidence(session, "reproduction", f"detail-{index}")
    assert len(session.evidence) == 4
    assert session.steps <= 8


def configure_fault_diagnosis_dataset(client, dataset_id: str = "server-dataset") -> None:
    with client.app.state.session_factory() as db:
        db.add(
            AgentConfigModel(
                agent_id="fault_diagnosis",
                enabled=True,
                model_binding_id=None,
                knowledge_dataset_ids=[dataset_id],
                streaming_enabled=True,
                suggestions_enabled=True,
                sources_enabled=True,
                context_turns=3,
                retrieval_limit=6,
                similarity_threshold=0.62,
                deep_thinking_enabled=False,
                deep_thinking_level="medium",
                max_reply_tokens=4096,
            )
        )
        db.commit()


def test_fault_diagnosis_api_creates_existing_business_diagnosis_draft(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    configure_fault_diagnosis_dataset(client)
    equipment_id = create_equipment(client, model="SERVER-MODEL")
    fault_id = create_fault(client, equipment_id, symptom="server pressure loss")
    _, agent_only_token = create_user_token(
        client,
        username="diagnosis-agent-only",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )
    _, token = create_user_token(
        client,
        username="diagnosis-api-user",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent", "fault:repair"],
    )
    retrieval_calls = []

    denied = client.post(
        "/api/agent/fault-diagnosis",
        headers={"Authorization": f"Bearer {agent_only_token}", "Idempotency-Key": "diagnosis-agent-only"},
        json={
            "action": "start",
            "fault_report_id": fault_id,
            "equipment_model": "SERVER-MODEL",
            "symptom": "server pressure loss",
            "description": "pressure falls under load",
        },
    )
    assert denied.status_code == 403
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(DiagnosisDraft)) == 0

    forged_context = client.post(
        "/api/agent/fault-diagnosis",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "diagnosis-forged-context"},
        json={
            "action": "start",
            "fault_report_id": fault_id,
            "equipment_model": "CLIENT-MODEL",
            "symptom": "client symptom",
            "description": "client description",
            "dataset_ids": ["client-dataset"],
        },
    )
    assert forged_context.status_code == 422

    def retrieve(db, question, dataset_ids, adapter):
        retrieval_calls.append({"question": question, "dataset_ids": dataset_ids})
        return RetrievalResult()

    monkeypatch.setattr(
        "app.modules.agents.router.knowledge_service.retrieve_knowledge",
        retrieve,
    )
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "diagnosis-start"}
    start = client.post(
        "/api/agent/fault-diagnosis",
        headers=headers,
        json={
            "action": "start",
            "fault_report_id": fault_id,
        },
    )
    assert start.status_code == 200
    assert retrieval_calls[0] == {
        "question": "SERVER-MODEL server pressure loss pressure falls under load",
        "dataset_ids": ["server-dataset"],
    }
    draft_id = start.json()["diagnosis_draft_id"]
    first = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-evidence-1"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "reproduction", "detail": "drops under load"},
    )
    second = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-evidence-2"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "pressure 12 bar"},
    )

    assert second.status_code == 200
    body = second.json()
    assert body["state"] == "DIAGNOSIS_READY"
    assert body["diagnosis_draft_id"]
    with client.app.state.session_factory() as db:
        ready_audits = db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_diagnosis.ready"
            )
        )
        draft_count = db.scalar(select(func.count()).select_from(DiagnosisDraft))
        idempotency_count = db.scalar(
            select(func.count()).select_from(IdempotencyRecord).where(
                IdempotencyRecord.path == "/api/agent/fault-diagnosis"
            )
        )

    replay = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-evidence-2"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "pressure 12 bar"},
    )
    assert replay.status_code == 200
    assert replay.json() == body
    conflict = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-evidence-2"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "pressure 13 bar"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    completed_again = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-after-ready"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "late replay"},
    )
    assert completed_again.status_code == 200
    assert completed_again.json() == body

    forged = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "diagnosis-forged"},
        json={
            "action": "evidence",
            "diagnosis_draft_id": draft_id,
            "session": {"state": "DIAGNOSIS_READY", "prefill": {"actual_cause": "forged"}},
            "category": "measurement",
            "detail": "forged",
        },
    )
    assert forged.status_code == 422

    _, other_token = create_user_token(
        client,
        username="diagnosis-api-other-user",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    denied = client.post(
        "/api/agent/fault-diagnosis",
        headers={"Authorization": f"Bearer {other_token}", "Idempotency-Key": "diagnosis-other"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "other"},
    )
    assert denied.status_code == 403

    _, repair_token = repairer(client)
    adopted = client.post(
        f"/api/fault-reports/{fault_id}/start-repair",
        headers=auth_headers(repair_token, key="diagnosis-adopt"),
        json={"mode": "ADOPTED", "diagnosis_draft_id": draft_id},
    )
    assert adopted.status_code == 200
    assert adopted.json()["start_mode"] == "ADOPTED"
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(DiagnosisDraft)) == 1
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.action == "agent.fault_diagnosis.ready"
            )
        ) == ready_audits
        assert db.scalar(
            select(func.count()).select_from(IdempotencyRecord).where(
                IdempotencyRecord.path == "/api/agent/fault-diagnosis"
            )
        ) == idempotency_count + 1
