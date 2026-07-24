from app.modules.agents.operation_guidance import (
    GuidanceContext,
    GuidanceState,
    OperationGuidanceAgent,
)
from app.integrations.ragflow.adapter import KnowledgeCitation, RetrievalResult
from tests.modules.support import create_user_token


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


def test_operation_guidance_api_uses_task005_retrieval_boundary(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    _, token = create_user_token(
        client,
        username="guidance-api-user",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )

    def retrieve(*args, **kwargs):
        return RetrievalResult(
            citations=[KnowledgeCitation("doc-1", "chunk-1", "inspect the pump", 0.9)]
        )

    monkeypatch.setattr(
        "app.modules.agents.router.knowledge_service.retrieve_knowledge", retrieve
    )
    response = client.post(
        "/api/agent/operation-guidance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "equipment_id": "equipment-1",
            "equipment_model": "MODEL-1",
            "symptom": "pressure loss",
            "description": "drops under load",
            "dataset_ids": ["dataset-1"],
        },
    )

    assert response.status_code == 200
    assert response.json()["evidence"] == [
        {"citation": "chunk-1", "text": "inspect the pump"},
        {"citation": "chunk-1", "text": "inspect the pump"},
    ]
