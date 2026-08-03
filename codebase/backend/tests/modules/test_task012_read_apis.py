from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.audit.models import AuditEvent
from app.modules.agent_runtime.models import AgentRun, AgentThread
from app.modules.equipment.models import Equipment
from app.modules.knowledge.models import FileObject, FileScanStatus, KnowledgeDataset, KnowledgeDocument, KnowledgeDocumentStatus
from app.modules.maintenance.models import FaultReport, HistoricalRepairCase, MaintenanceRecord, WorkOrder
from tests.modules.maintenance_support import auth_headers, create_equipment, create_fault, repairer, start_repair
from tests.modules.support import create_user_token


def _token(client: TestClient, *permissions: str) -> str:
    _, token = create_user_token(
        client,
        username=f"task012-reader-{uuid4().hex[:8]}",
        role_code="SYSTEM_ADMIN",
        permission_codes=list(permissions),
    )
    return token


def _completed_work(client: TestClient) -> tuple[str, str, str]:
    equipment_id = create_equipment(client)
    fault_id = create_fault(client, equipment_id)
    work_order_id, token = start_repair(client, fault_id, token=repairer(client)[1])
    completion = client.post(
        f"/api/work-orders/{work_order_id}/repair-result",
        headers=auth_headers(token, key=f"complete-{uuid4()}"),
        json={"actual_cause": "wear", "actual_solution": "replace", "repair_result": "passed"},
    )
    assert completion.status_code == 200
    return equipment_id, fault_id, work_order_id


def test_bi_and_equipment_history_are_server_aggregated_and_permissioned(client: TestClient) -> None:
    equipment_id, _, _ = _completed_work(client)
    token = _token(client, "bi:view", "equipment:read")

    dashboard = client.get("/api/bi/dashboard", headers=auth_headers(token))
    history = client.get(
        f"/api/maintenance-history/equipment/{equipment_id}", headers=auth_headers(token)
    )

    assert dashboard.status_code == 200
    assert dashboard.json()["summary"]["completed_work_order_count"] == 1
    assert dashboard.json()["organization_ranking"]
    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert {
        "work_order_id", "maintenance_record_id", "fault_report_id", "status",
        "symptom", "actual_cause", "actual_solution", "repair_result", "completed_at",
    }.issubset(history.json()["items"][0])
    denied = client.get("/api/bi/dashboard", headers=auth_headers(_token(client, "equipment:read")))
    assert denied.status_code == 403


def test_bi_filter_scopes_ranking_and_calculates_completed_duration(client: TestClient) -> None:
    equipment_id, _, work_order_id = _completed_work(client)
    other_equipment_id, _, _ = _completed_work(client)
    with client.app.state.session_factory() as db:
        first = db.get(WorkOrder, work_order_id)
        assert first is not None
        first.started_at = first.completed_at - timedelta(hours=3)
        first.created_at = first.started_at
        old_fault = db.scalar(select(FaultReport).where(FaultReport.equipment_id == equipment_id))
        assert old_fault is not None
        old_fault.submitted_at = datetime.now(UTC) - timedelta(days=8)
        db.commit()
        first_equipment = db.get(Equipment, equipment_id)
        other_equipment = db.get(Equipment, other_equipment_id)
        assert first_equipment is not None and other_equipment is not None
        organization_id = first_equipment.organization_id
        other_organization_id = other_equipment.organization_id

    token = _token(client, "bi:view")
    response = client.get(f"/api/bi/dashboard?organization_id={organization_id}", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["fault_count"] == 0
    assert body["summary"]["completed_work_order_count"] == 1
    assert body["efficiency"]["average_completion_hours"] == 3.0
    assert body["organization_ranking"] == [{"organization_id": organization_id, "organization_name": body["organization_ranking"][0]["organization_name"], "fault_count": 0}]
    assert body["history_comparison"] == {"current_fault_count": 0, "previous_fault_count": 1}
    assert other_organization_id != organization_id


def test_bi_supports_explicit_periods_and_rejects_unknown_organization(client: TestClient) -> None:
    token = _token(client, "bi:view")
    response = client.get("/api/bi/dashboard?period=day", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["period"] == "day"
    assert len(response.json()["trend"]) == 1
    missing = client.get("/api/bi/dashboard?organization_id=missing", headers=auth_headers(token))
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "ORGANIZATION_NOT_FOUND"


def test_maintenance_and_assigned_work_orders_have_controlled_read_models(client: TestClient) -> None:
    equipment_id, _, work_order_id = _completed_work(client)
    token = _token(client, "maintenance:view", "maintenance:detail", "equipment:read")

    records = client.get("/api/maintenance-records", headers=auth_headers(token))
    record_id = records.json()["items"][0]["maintenance_record_id"]
    detail = client.get(f"/api/maintenance-records/{record_id}", headers=auth_headers(token))
    orders = client.get("/api/work-orders", headers=auth_headers(token))
    order = client.get(f"/api/work-orders/{work_order_id}", headers=auth_headers(token))

    assert records.status_code == 200
    assert records.json()["items"][0]["equipment_id"] == equipment_id
    assert records.json()["items"][0]["knowledge_status"] == "LINKED"
    assert detail.status_code == 200
    assert detail.json()["knowledge_status"] == "LINKED"
    assert orders.status_code == 200
    assert order.status_code == 200
    assert order.json()["id"] == work_order_id
    assert "diagnosis_prefill" not in detail.json()
    linked = client.get("/api/maintenance-records?knowledge_status=LINKED", headers=auth_headers(token))
    assert linked.status_code == 200
    assert linked.json()["count"] == 1
    invalid_knowledge_status = client.get("/api/maintenance-records?knowledge_status=UNKNOWN", headers=auth_headers(token))
    assert invalid_knowledge_status.status_code == 422
    invalid_status = client.get("/api/work-orders?status=UNKNOWN", headers=auth_headers(token))
    assert invalid_status.status_code == 422


def test_audit_and_intelligence_read_models_are_whitelisted_and_empty_safe(client: TestClient) -> None:
    with client.app.state.session_factory() as db:
        db.add(AuditEvent(action="test.action", resource_type="test", resource_id="x", result="success", metadata_json={"token": "never-return"}))
        dataset = KnowledgeDataset(name="Task 012", ragflow_dataset_id=f"rag-{uuid4()}")
        db.add(dataset)
        db.flush()
        db.add(KnowledgeDocument(dataset_id=dataset.id, object_storage_file_id="missing-file", filename="manual.pdf", content_type="application/pdf", size_bytes=10, status=KnowledgeDocumentStatus.FAILED, failure_reason="retryable", created_by="missing-user"))
        db.rollback()

    token = _token(client, "system:audit", "intelligence:audit")
    audit = client.get("/api/audit-events", headers=auth_headers(token))
    usage = client.get("/api/intelligence/usage", headers=auth_headers(token))
    documents = client.get("/api/intelligence/knowledge-documents", headers=auth_headers(token))

    assert audit.status_code == 200
    assert audit.json()["items"]
    assert set(audit.json()["items"][0]) == {"id", "actor_user_id", "action", "resource_type", "resource_id", "result", "created_at"}
    assert "metadata_json" not in audit.json()["items"][0]
    assert usage.status_code == 200
    assert usage.json() == {
        "items": [], "count": 0, "retention_days": 30,
        "token_measurement": "configured_max_reply_tokens_not_actual_usage",
    }
    assert documents.status_code == 200
    assert documents.json() == {"items": [], "count": 0, "page": 1, "page_size": 20}


def test_failed_knowledge_document_can_be_retried_once_with_authorized_idempotency(client: TestClient) -> None:
    user_id, token = create_user_token(
        client, username=f"knowledge-retry-{uuid4().hex[:8]}", role_code="SYSTEM_ADMIN", permission_codes=["intelligence:knowledge"]
    )
    with client.app.state.session_factory() as db:
        dataset = KnowledgeDataset(name="Task 012", ragflow_dataset_id=f"rag-{uuid4()}")
        db.add(dataset)
        db.flush()
        file_object = FileObject(object_key=f"test/{uuid4()}", filename="manual.pdf", content_type="application/pdf", size_bytes=10, sha256="0" * 64, scan_status=FileScanStatus.CLEAN, created_by=user_id)
        db.add(file_object)
        db.flush()
        document = KnowledgeDocument(dataset_id=dataset.id, object_storage_file_id=file_object.id, filename="manual.pdf", content_type="application/pdf", size_bytes=10, status=KnowledgeDocumentStatus.FAILED, failure_reason="retryable", created_by=user_id)
        db.add(document)
        db.commit()
        document_id = document.id

    response = client.post(f"/api/knowledge/documents/{document_id}/retry", headers=auth_headers(token, key="retry-document"))
    replay = client.post(f"/api/knowledge/documents/{document_id}/retry", headers=auth_headers(token, key="retry-document"))

    assert response.status_code == 200
    assert response.json()["status"] == "UPLOADING"
    assert replay.status_code == 200


def test_intelligence_usage_aggregates_persisted_runs_without_claiming_actual_tokens(client: TestClient) -> None:
    user_id, token = create_user_token(
        client, username=f"intelligence-audit-{uuid4().hex[:8]}", role_code="SYSTEM_ADMIN", permission_codes=["intelligence:audit"]
    )
    with client.app.state.session_factory() as db:
        thread = AgentThread(agent_id="operation_guidance", creator_user_id=user_id)
        db.add(thread)
        db.flush()
        db.add_all([
            AgentRun(thread_id=thread.id, config_snapshot_json={"max_reply_tokens": 256}, state_json={}, status="RUNNING"),
            AgentRun(thread_id=thread.id, config_snapshot_json={"max_reply_tokens": 256}, state_json={}, status="RUNNING"),
        ])
        db.commit()

    response = client.get("/api/intelligence/usage", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["items"] == [{
        "agent_id": "operation_guidance",
        "status": "RUNNING",
        "run_count": 2,
        "configured_max_reply_tokens": 512,
    }]
    assert response.json()["token_measurement"] == "configured_max_reply_tokens_not_actual_usage"
