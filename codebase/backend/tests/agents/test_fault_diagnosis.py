from app.modules.agents.fault_diagnosis import (
    DiagnosisContext,
    DiagnosisState,
    FaultDiagnosisAgent,
)
from app.integrations.ragflow.adapter import KnowledgeCitation, RetrievalResult
from tests.modules.maintenance_support import auth_headers, create_equipment, create_fault, repairer
from tests.modules.support import create_user_token
from app.core.database import Base
from app.modules.agent_config.models import AgentConfigModel
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from app.modules.equipment.models import Organization, OrganizationType
from app.modules.knowledge.models import FileObject, FileScanStatus, KnowledgeDataset, KnowledgeDocument, KnowledgeDocumentStatus
from app.modules.maintenance.models import DiagnosisDraft
from app.main import create_app
from fastapi.testclient import TestClient
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from sqlalchemy import func, select
import json
import threading


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


def test_fault_diagnosis_api_uses_app_factory_ragflow_adapter(monkeypatch):
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
                                    "content": "inspect the relief valve",
                                    "similarity": 0.91,
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
        with app.state.session_factory() as db:
            db.add(
                Organization(
                    type=OrganizationType.ROOT,
                    code="ROOT",
                    name="根节点",
                    parent_id=None,
                    sort_order=0,
                    enabled=True,
                    remark="",
                )
            )
            db.commit()
        client = TestClient(app)
        user_id, token = create_user_token(
            client,
            username="diagnosis-factory-user",
            role_code="REPAIR_WORKER",
            permission_codes=["intelligence:agent", "fault:repair"],
        )
        equipment_id = create_equipment(client, model="SERVER-MODEL")
        fault_id = create_fault(client, equipment_id, symptom="server pressure loss")
        with app.state.session_factory() as db:
            dataset = KnowledgeDataset(name="diagnosis manuals", ragflow_dataset_id="remote-dataset")
            db.add(dataset)
            db.flush()
            db.add(
                AgentConfigModel(
                    agent_id="fault_diagnosis",
                    enabled=True,
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
            file_object = FileObject(
                object_key="knowledge/diagnosis.txt",
                filename="diagnosis.txt",
                content_type="text/plain",
                size_bytes=12,
                sha256="0" * 64,
                scan_status=FileScanStatus.CLEAN,
                created_by=user_id,
            )
            db.add(file_object)
            db.flush()
            db.add(
                KnowledgeDocument(
                    dataset_id=dataset.id,
                    object_storage_file_id=file_object.id,
                    ragflow_document_id="remote-ready",
                    filename="diagnosis.txt",
                    content_type="text/plain",
                    size_bytes=12,
                    status=KnowledgeDocumentStatus.READY,
                    created_by=user_id,
                )
            )
            db.commit()

        response = client.post(
            "/api/agent/fault-diagnosis",
            headers=auth_headers(token, key="diagnosis-factory-start"),
            json={"action": "start", "fault_report_id": fault_id},
        )

        assert response.status_code == 200
        assert response.json()["state"] == "QUESTIONING"
        assert response.json()["diagnosis_draft_id"]
        assert requests[0]["path"] == "/api/v1/retrieval"
        assert requests[0]["body"]["dataset_ids"] == ["remote-dataset"]
        assert requests[0]["body"]["document_ids"] == ["remote-ready"]
    finally:
        server.shutdown()


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
        return RetrievalResult(citations=[KnowledgeCitation("doc-1", "chunk-1", "inspect the relief valve", 0.91)])

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


def test_fault_diagnosis_does_not_generate_a_ready_summary_without_retrieved_sources(client, monkeypatch):
    client.app.state.knowledge_adapter = object()
    configure_fault_diagnosis_dataset(client)
    equipment_id = create_equipment(client, model="NO-SOURCE-MODEL")
    fault_id = create_fault(client, equipment_id, symptom="pressure drops")
    _, token = create_user_token(
        client, username="diagnosis-no-source", role_code="REPAIR_WORKER", permission_codes=["intelligence:agent", "fault:repair"]
    )
    monkeypatch.setattr(
        "app.modules.agents.router.knowledge_service.retrieve_knowledge",
        lambda db, question, dataset_ids, adapter: RetrievalResult(),
    )
    headers = {"Authorization": f"Bearer {token}"}
    started = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "no-source-start"},
        json={"action": "start", "fault_report_id": fault_id},
    )
    draft_id = started.json()["diagnosis_draft_id"]
    client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "no-source-reproduction"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "reproduction", "detail": "drops under load"},
    )
    response = client.post(
        "/api/agent/fault-diagnosis",
        headers={**headers, "Idempotency-Key": "no-source-measurement"},
        json={"action": "evidence", "diagnosis_draft_id": draft_id, "category": "measurement", "detail": "12 bar"},
    )
    assert response.status_code == 200
    assert response.json()["state"] == "EVIDENCE_PENDING"
    assert response.json()["prefill"] is None
    assert response.json()["summary"] is None
