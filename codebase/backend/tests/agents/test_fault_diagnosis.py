from app.modules.agents.fault_diagnosis import (
    DiagnosisContext,
    DiagnosisState,
    FaultDiagnosisAgent,
)
from app.integrations.ragflow.adapter import RetrievalResult
from tests.modules.maintenance_support import auth_headers, create_equipment, create_fault
from tests.modules.support import create_user_token


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


def test_fault_diagnosis_api_creates_existing_business_diagnosis_draft(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    _, token = create_user_token(
        client,
        username="diagnosis-api-user",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    monkeypatch.setattr(
        "app.modules.agents.router.knowledge_service.retrieve_knowledge",
        lambda *args, **kwargs: RetrievalResult(),
    )
    headers = {"Authorization": f"Bearer {token}"}
    start = client.post(
        "/api/agent/fault-diagnosis",
        headers=headers,
        json={
            "action": "start",
            "fault_report_id": fault_id,
            "equipment_model": "MODEL-1",
            "symptom": "pressure loss",
            "description": "drops under load",
            "dataset_ids": ["dataset-1"],
        },
    )
    assert start.status_code == 200
    session = start.json()["session"]
    first = client.post(
        "/api/agent/fault-diagnosis",
        headers=headers,
        json={"action": "evidence", "session": session, "category": "reproduction", "detail": "drops under load"},
    )
    second = client.post(
        "/api/agent/fault-diagnosis",
        headers=headers,
        json={"action": "evidence", "session": first.json()["session"], "category": "measurement", "detail": "pressure 12 bar"},
    )

    assert second.status_code == 200
    body = second.json()
    assert body["state"] == "DIAGNOSIS_READY"
    assert body["diagnosis_draft_id"]
