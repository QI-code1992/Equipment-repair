from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.modules.audit.models import AuditEvent
from app.modules.knowledge.models import KnowledgeDataset, KnowledgeDocument, KnowledgeDocumentStatus
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
        f"/api/equipment/{equipment_id}/maintenance-history", headers=auth_headers(token)
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
    assert detail.status_code == 200
    assert detail.json()["knowledge_status"] == "NOT_LINKED"
    assert orders.status_code == 200
    assert order.status_code == 200
    assert order.json()["id"] == work_order_id
    assert "diagnosis_prefill" not in detail.json()


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
    assert usage.json() == {"items": [], "count": 0, "retention_days": 30}
    assert documents.status_code == 200
    assert documents.json() == {"items": [], "count": 0, "page": 1, "page_size": 20}
