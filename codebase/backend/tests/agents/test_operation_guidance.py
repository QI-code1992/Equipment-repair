from app.modules.agents.operation_guidance import (
    GuidanceContext,
    GuidanceState,
    OperationGuidanceAgent,
)
from app.core.database import Base
from app.integrations.ragflow.adapter import KnowledgeCitation, RetrievalResult
from app.modules.agent_config.models import AgentConfigModel
from app.modules.knowledge.models import FileObject, FileScanStatus, KnowledgeDataset, KnowledgeDocument, KnowledgeDocumentStatus
from app.main import create_app
from tests.modules.support import create_user_token
from fastapi.testclient import TestClient
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


def _configure_guidance(client, dataset_ids: list[str]) -> None:
    with client.app.state.session_factory() as db:
        db.add(
            AgentConfigModel(
                agent_id="operation_guidance",
                enabled=True,
                model_binding_id=None,
                knowledge_dataset_ids=dataset_ids,
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


def test_operation_guidance_prioritizes_page_capability_and_limits_directional_retrievals():
    calls: list[str] = []

    def retrieve(query: str):
        calls.append(query)
        return [{"document_id": "doc-1", "chunk_id": f"case-{len(calls)}", "citation": f"case-{len(calls)}", "text": "verified guidance"}]

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
    assert len(calls) == 1
    assert session.question
    assert len(session.evidence) == 1


def test_operation_guidance_combines_context_into_one_directional_retrieval():
    calls: list[str] = []

    def retrieve(query: str):
        calls.append(query)
        return [{"document_id": "doc-1", "chunk_id": "chunk-1", "citation": "chunk-1", "text": "verified guidance"}]

    session = OperationGuidanceAgent(retrieve).start(
        GuidanceContext("eq-1", "X1", "pressure loss", "after warm-up")
    )

    assert calls == ["X1 pressure loss after warm-up"]
    assert session.retrieval_count == 1


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


def test_operation_guidance_empty_retrieval_states_no_citable_evidence():
    session = OperationGuidanceAgent(lambda _: []).start(
        GuidanceContext("eq-1", "X1", "pressure", "warm-up")
    )

    assert session.state is GuidanceState.NO_EVIDENCE
    assert session.evidence == ()
    assert session.manual_fallback is True
    assert session.question == "未检索到可引用依据，请补充工况或直接按人工流程处理。"


def test_operation_guidance_transient_retry_never_exceeds_two_total_retrievals():
    calls = 0

    def retrieve(_: str):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary")
        return [{"document_id": "doc-1", "chunk_id": "chunk", "citation": "chunk", "text": "retry succeeded"}]

    session = OperationGuidanceAgent(retrieve).start(
        GuidanceContext("eq-1", "X1", "pressure", "warm-up")
    )

    assert session.state is GuidanceState.QUESTIONING
    assert calls == 2
    assert session.retrieval_count == 2


def test_operation_guidance_api_uses_task005_retrieval_boundary(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    _configure_guidance(client, ["dataset-1"])
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
        {
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "citation": "chunk-1",
            "text": "inspect the pump",
        },
    ]


def test_operation_guidance_api_ignores_client_dataset_ids_and_uses_agent_config(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    _, token = create_user_token(
        client,
        username="guidance-config-user",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )
    with client.app.state.session_factory() as db:
        db.add(
            AgentConfigModel(
                agent_id="operation_guidance",
                enabled=True,
                model_binding_id=None,
                knowledge_dataset_ids=["server-dataset"],
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
    retrieval_calls: list[dict[str, object]] = []

    def retrieve(db, question, dataset_ids, adapter):
        retrieval_calls.append({"question": question, "dataset_ids": dataset_ids})
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
            "dataset_ids": ["client-controlled-dataset"],
        },
    )

    assert response.status_code == 200
    assert retrieval_calls[0]["dataset_ids"] == ["server-dataset"]


def test_operation_guidance_api_returns_no_citable_evidence_for_an_empty_retrieval(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    _configure_guidance(client, ["dataset-1"])
    _, token = create_user_token(
        client,
        username="guidance-empty-user",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )
    monkeypatch.setattr(
        "app.modules.agents.router.knowledge_service.retrieve_knowledge",
        lambda *args, **kwargs: RetrievalResult(citations=[]),
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
    assert response.json()["state"] == "NO_EVIDENCE"
    assert response.json()["evidence"] == []
    assert response.json()["question"] == "未检索到可引用依据，请补充工况或直接按人工流程处理。"


def test_operation_guidance_api_uses_app_factory_ragflow_adapter(monkeypatch):
    requests: list[dict[str, object]] = []

    class RagflowHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append({"path": self.path, "body": body})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "code": 0,
                        "data": {
                            "chunks": [
                                {
                                    "id": "chunk-1",
                                    "document_id": "remote-ready",
                                    "content": "inspect the pump filter",
                                    "similarity": 0.93,
                                }
                            ]
                        },
                    }
                ).encode()
            )

        def log_message(self, *args: object) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), RagflowHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("RAGFLOW_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("RAGFLOW_API_KEY", "test-key")
    try:
        app = create_app(
            postgres_dsn="sqlite+pysqlite:///:memory:",
            redis_url="redis://redis:6379/0",
        )
        Base.metadata.create_all(app.state.engine)
        client = TestClient(app)
        user_id, token = create_user_token(
            client,
            username="guidance-factory-user",
            role_code="LINE_OPERATOR",
            permission_codes=["intelligence:agent"],
        )
        with app.state.session_factory() as db:
            dataset = KnowledgeDataset(name="factory manuals", ragflow_dataset_id="remote-dataset")
            db.add(dataset)
            db.flush()
            file_object = FileObject(
                object_key="knowledge/manual.txt",
                filename="manual.txt",
                content_type="text/plain",
                size_bytes=12,
                sha256="0" * 64,
                scan_status=FileScanStatus.CLEAN,
                created_by=user_id,
            )
            db.add(file_object)
            db.flush()
            document = KnowledgeDocument(
                dataset_id=dataset.id,
                object_storage_file_id=file_object.id,
                ragflow_document_id="remote-ready",
                filename="manual.txt",
                content_type="text/plain",
                size_bytes=12,
                status=KnowledgeDocumentStatus.READY,
                created_by=user_id,
            )
            db.add(document)
            db.add(
                AgentConfigModel(
                    agent_id="operation_guidance",
                    enabled=True,
                    model_binding_id=None,
                    knowledge_dataset_ids=[dataset.id],
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
            dataset_id = dataset.id

        response = client.post(
            "/api/agent/operation-guidance",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "equipment_id": "equipment-1",
                "equipment_model": "MODEL-1",
                "symptom": "pressure loss",
                "description": "drops under load",
                "dataset_ids": [dataset_id],
            },
        )

        assert response.status_code == 200
        assert response.json()["state"] == "QUESTIONING"
        assert response.json()["evidence"][0] == {
            "document_id": document.id,
            "chunk_id": "chunk-1",
            "citation": "chunk-1",
            "text": "inspect the pump filter",
        }
        assert requests[0]["path"] == "/api/v1/retrieval"
        assert requests[0]["body"]["dataset_ids"] == ["remote-dataset"]
        assert requests[0]["body"]["document_ids"] == ["remote-ready"]
    finally:
        server.shutdown()
