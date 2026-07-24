from app.modules.agents.fault_diagnosis import (
    DiagnosisContext,
    DiagnosisState,
    FaultDiagnosisAgent,
)


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
