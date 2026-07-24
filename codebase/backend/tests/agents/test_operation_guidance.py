from app.modules.agents.operation_guidance import (
    GuidanceContext,
    GuidanceState,
    OperationGuidanceAgent,
)


def test_operation_guidance_prioritizes_page_capability_and_limits_directional_retrievals():
    calls: list[str] = []

    def retrieve(query: str):
        calls.append(query)
        return [{"citation": f"case-{len(calls)}", "text": "verified guidance"}]

    agent = OperationGuidanceAgent(retrieve)
    session = agent.start(
        GuidanceContext(
            equipment_id="eq-1",
            equipment_model="X1",
            symptom="hydraulic pressure drops",
            description="pressure drops after warm-up",
        )
    )

    assert session.state is GuidanceState.QUESTIONING
    assert len(calls) == 2
    assert session.question
    assert len(session.evidence) == 2


def test_operation_guidance_failure_keeps_manual_path_available():
    def unavailable(_: str):
        raise TimeoutError("retrieval timeout")

    session = OperationGuidanceAgent(unavailable).start(
        GuidanceContext(
            equipment_id="eq-1",
            equipment_model="X1",
            symptom="unknown",
            description="unknown",
        )
    )

    assert session.state is GuidanceState.UNAVAILABLE
    assert session.manual_fallback is True
    assert session.evidence == ()
