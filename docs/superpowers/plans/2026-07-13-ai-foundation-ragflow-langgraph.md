# AI Foundation: RAGFlow and LangGraph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the first-phase AI foundation in which RAGFlow provides cited knowledge retrieval and LangGraph orchestrates only controlled agent workflows through business APIs.

**Architecture:** The product backend is a Python/FastAPI service. It owns authentication, menu permissions, the existing Agent-only device-grant boundary, business facts, health-score reads, audit records, and every business write. It calls RAGFlow through an adapter for document ingestion and retrieval, and runs LangGraph in-process for durable agent workflows. The model gateway uses OpenAI-compatible configuration so deployment can point to a local or remote provider without changing application code.

**Tech Stack:** Python 3.13, FastAPI, LangGraph, PostgreSQL, Redis, MinIO/S3-compatible object storage, RAGFlow Docker Compose, Docker Desktop/WSL2 on Windows, OpenAI-compatible LLM/embedding/reranker endpoints.

## Global Constraints

- RAGFlow is mandatory for knowledge parsing, retrieval, reranking, and citations; it is not the business source of truth.
- LangGraph is mandatory for intelligent query, AI fault reporting, operations guidance, and diagnostic/repair suggestions.
- Agents may read through allowlisted tools only. For every device-specific request, Agents must enforce the existing device-grant boundary using a server-side lookup; that scope does not create general data permissions for non-Agent modules. Agents never write health scores and never persist faults, repairs, or other business records except by calling the corresponding validated business API.
- Intelligent query can use only the 40 built-in metrics and their allowed dimensions. The metric service calculates values; the LLM only understands, validates, and summarizes.
- The Windows demonstration server supports no more than 10 concurrent users and approximately 100 managed devices. Application data is backed up daily at 00:10 and retained for 10 days.
- `pages/data-import.html` is legacy-only. No menu, permission, route, or implementation task may restore it.
- All secrets are injected through environment variables. No token, password, model key, or connection string may be committed.

---

### Task 1: Establish the AI architecture and configuration contract

**Files:**
- Create: `docs/engineering/AI_RAGFLOW_LANGGRAPH_SPEC.md`
- Create: `deploy/.env.example`
- Create: `deploy/docker-compose.ai.yml`
- Test: `tests/ai-config-contract.test.js`

**Interfaces:**
- Consumes: current PRD, `docs/开发交付入口.md`, and the system username/password authentication requirement.
- Produces: a documented configuration contract and an AI container topology that later tasks can run without private machine state.

- [ ] **Step 1: Write the failing configuration contract test**

```javascript
assert.match(envExample, /^RAGFLOW_BASE_URL=/m);
assert.match(envExample, /^RAGFLOW_API_KEY=/m);
assert.match(envExample, /^MODEL_BASE_URL=/m);
assert.match(envExample, /^MODEL_API_KEY=/m);
assert.match(envExample, /^MODEL_CHAT_NAME=/m);
assert.match(envExample, /^MODEL_EMBEDDING_NAME=/m);
assert.match(envExample, /^MODEL_RERANK_NAME=/m);
assert.match(compose, /ragflow/i);
assert.doesNotMatch(envExample, /1234qwer/);
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node tests/ai-config-contract.test.js`

Expected: failure because the deployment configuration does not exist.

- [ ] **Step 3: Create the minimal deployment contract**

```dotenv
RAGFLOW_BASE_URL=http://ragflow:9380
RAGFLOW_API_KEY=
MODEL_BASE_URL=
MODEL_API_KEY=
MODEL_CHAT_NAME=
MODEL_EMBEDDING_NAME=
MODEL_RERANK_NAME=
POSTGRES_DSN=postgresql://app:change-me@postgres:5432/equipment_ops
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=change-me
S3_SECRET_KEY=change-me
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node tests/ai-config-contract.test.js`

Expected: `ai-config-contract: passed`.

- [ ] **Step 5: Commit**

```powershell
git add docs/engineering/AI_RAGFLOW_LANGGRAPH_SPEC.md deploy/.env.example deploy/docker-compose.ai.yml tests/ai-config-contract.test.js
git commit -m "docs: define RAGFlow and LangGraph foundation"
```

### Task 2: Build the RAGFlow integration boundary

**Files:**
- Create: `backend/app/integrations/ragflow_client.py`
- Create: `backend/app/services/knowledge_service.py`
- Create: `backend/app/schemas/knowledge.py`
- Test: `backend/tests/test_ragflow_client.py`
- Test: `backend/tests/test_knowledge_service.py`

**Interfaces:**
- Consumes: `RAGFLOW_BASE_URL`, `RAGFLOW_API_KEY`, a local `knowledge_document` record, and an allowlisted RAGFlow dataset identifier.
- Produces: `ingest_document(...) -> KnowledgeDocument`, `get_ingestion_status(...) -> IngestionStatus`, and `retrieve(...) -> list[KnowledgeCitation]`.

- [ ] **Step 1: Write failing retrieval and ingestion tests**

```python
def test_retrieve_returns_only_cited_chunks(fake_ragflow):
    result = service.retrieve(dataset_id="maintenance", query="驱动电机过温")
    assert result[0].citation.document_id == "doc-17"
    assert result[0].citation.chunk_id
    assert result[0].citation.text

def test_ingestion_persists_ragflow_ids(fake_ragflow):
    document = service.ingest_document(file_id="file-1", dataset_id="maintenance")
    assert document.ragflow_document_id == "rag-doc-1"
    assert document.status == "PARSING"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest backend/tests/test_ragflow_client.py backend/tests/test_knowledge_service.py -q`

Expected: collection failure because the client and service are not implemented.

- [ ] **Step 3: Implement a typed RAGFlow adapter**

```python
class RagflowClient(Protocol):
    def upload_document(self, dataset_id: str, file_path: str) -> str: ...
    def document_status(self, dataset_id: str, document_id: str) -> str: ...
    def retrieve(self, dataset_id: str, query: str, top_k: int) -> list[dict]: ...

class KnowledgeService:
    def retrieve(self, dataset_id: str, query: str) -> list[KnowledgeCitation]:
        chunks = self._ragflow.retrieve(dataset_id, query, top_k=5)
        return [KnowledgeCitation.from_ragflow(chunk) for chunk in chunks if chunk.get("document_id") and chunk.get("content")]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest backend/tests/test_ragflow_client.py backend/tests/test_knowledge_service.py -q`

Expected: `2 passed` or more, with every returned retrieval result containing a citation.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/integrations/ragflow_client.py backend/app/services/knowledge_service.py backend/app/schemas/knowledge.py backend/tests/test_ragflow_client.py backend/tests/test_knowledge_service.py
git commit -m "feat: add cited RAGFlow retrieval adapter"
```

### Task 3: Build the metric-query LangGraph workflow

**Files:**
- Create: `backend/app/agents/metric_query_graph.py`
- Create: `backend/app/agents/state.py`
- Create: `backend/app/tools/metric_tool.py`
- Create: `backend/app/api/agent_query.py`
- Test: `backend/tests/test_metric_query_graph.py`

**Interfaces:**
- Consumes: `AgentRequest(user_id, thread_id, message, page_context)`, authenticated menu permissions, server-side device grants, the 40-item metric catalog, and the health-score service.
- Produces: `AgentResponse(answer, metric_results, citations, follow_up_question, audit_id)`.

- [ ] **Step 1: Write failing graph tests**

```python
def test_unknown_metric_is_refused(graph):
    response = graph.invoke(request("查一下报警次数"))
    assert response["status"] == "REFUSED"
    assert "内置指标" in response["answer"]

def test_health_score_is_read_only_from_health_service(graph):
    response = graph.invoke(request("EL-2024-019 的健康分"))
    assert response["metric_results"][0]["source"] == "health-score-service"
    assert response["metric_results"][0]["value"] == 61

def test_metric_query_refuses_ungranted_device(graph):
    response = graph.invoke(request("查询 EL-2024-099 的健康分", user_id="u-1"))
    assert response["status"] == "REFUSED"
    assert "EL-2024-099" not in response["metric_results"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest backend/tests/test_metric_query_graph.py -q`

Expected: collection failure because the graph and metric tool do not exist.

- [ ] **Step 3: Implement the controlled graph**

```python
builder.add_node("understand", understand_metric_request)
builder.add_node("validate", validate_builtin_metric_and_dimensions)
builder.add_node("query_metric", query_metric_service)
builder.add_node("summarize", summarize_without_changing_values)
builder.add_edge(START, "understand")
builder.add_edge("understand", "validate")
builder.add_conditional_edges("validate", route_valid_metric, {"valid": "query_metric", "invalid": END})
builder.add_edge("query_metric", "summarize")
builder.add_edge("summarize", END)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest backend/tests/test_metric_query_graph.py -q`

Expected: `2 passed` or more. No test may allow an LLM-supplied numeric value to replace a metric-service value.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/agents backend/app/tools/metric_tool.py backend/app/api/agent_query.py backend/tests/test_metric_query_graph.py
git commit -m "feat: add controlled intelligent query graph"
```

### Task 4: Build the fault-report and maintenance-advice LangGraph workflows

**Files:**
- Create: `backend/app/agents/fault_report_graph.py`
- Create: `backend/app/agents/maintenance_guidance_graph.py`
- Create: `backend/app/tools/fault_tool.py`
- Create: `backend/app/tools/knowledge_tool.py`
- Test: `backend/tests/test_fault_report_graph.py`
- Test: `backend/tests/test_maintenance_guidance_graph.py`

**Interfaces:**
- Consumes: authenticated user identity, page context, the server-side granted equipment list, user-entered fault text, attachment IDs, and cited RAGFlow results.
- Produces: a structured draft or cited advice. Only `submit_fault_report_draft(...)` may create a fault record after required fields and user confirmation pass.

- [ ] **Step 1: Write failing workflow safety tests**

```python
def test_fault_report_pauses_for_required_fields(graph):
    result = graph.invoke(request("电机过温"), config=thread("fault-1"))
    assert result["status"] == "WAITING_FOR_INPUT"
    assert set(result["missing_fields"]) == {"occurred_at", "duration"}

def test_guidance_never_writes_a_repair_record(graph):
    result = graph.invoke(request("给出液压压力波动排查建议"))
    assert result["write_operations"] == []
    assert result["citations"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest backend/tests/test_fault_report_graph.py backend/tests/test_maintenance_guidance_graph.py -q`

Expected: collection failure because the workflows and allowlisted tools do not exist.

- [ ] **Step 3: Implement human-confirmed writes and cited guidance**

```python
if missing_required_fields(state):
    return interrupt({"type": "required_fields", "fields": missing_required_fields(state)})
if not state["user_confirmed"]:
    return interrupt({"type": "submit_confirmation", "draft": state["fault_draft"]})
return fault_api.submit_fault_report_draft(state["fault_draft"], actor_id=state["user_id"])
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest backend/tests/test_fault_report_graph.py backend/tests/test_maintenance_guidance_graph.py -q`

Expected: `2 passed` or more. Every persisted fault is confirmed by the user and every knowledge-backed answer contains a citation.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/agents backend/app/tools backend/tests/test_fault_report_graph.py backend/tests/test_maintenance_guidance_graph.py
git commit -m "feat: add controlled fault and guidance agents"
```

### Task 5: Add durable state, audit, and end-to-end acceptance checks

**Files:**
- Create: `backend/app/persistence/langgraph_checkpoint.py`
- Create: `backend/app/services/agent_audit_service.py`
- Create: `backend/tests/test_agent_checkpoint.py`
- Create: `backend/tests/test_agent_audit.py`
- Create: `tests/ai-e2e-acceptance.md`

**Interfaces:**
- Consumes: a stable `thread_id`, authenticated `user_id`, graph node events, tool calls, model usage metadata, and errors.
- Produces: resumable graph state and immutable audit events without storing model secrets.

- [ ] **Step 1: Write failing persistence and audit tests**

```python
def test_resume_uses_same_thread_state(checkpointed_graph):
    first = checkpointed_graph.invoke(request("电机过温"), config=thread("t-1"))
    resumed = checkpointed_graph.invoke(Command(resume={"occurred_at": "2026-07-13 10:00", "duration": "20分钟"}), config=thread("t-1"))
    assert resumed["fault_draft"]["occurred_at"] == "2026-07-13 10:00"

def test_audit_record_has_no_secret(audit_service):
    record = audit_service.record_tool_call("metric_query", {"metric": "故障数量"})
    assert "api_key" not in record.payload
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest backend/tests/test_agent_checkpoint.py backend/tests/test_agent_audit.py -q`

Expected: collection failure because persistent checkpoints and audits do not exist.

- [ ] **Step 3: Implement PostgreSQL-backed checkpoints and audit events**

```python
checkpointer = PostgresSaver.from_conn_string(settings.postgres_dsn)
graph = builder.compile(checkpointer=checkpointer)

audit_service.record(
    user_id=user_id,
    thread_id=thread_id,
    graph_name=graph_name,
    node_name=node_name,
    event_type=event_type,
    safe_payload=redact_secrets(payload),
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest backend/tests/test_agent_checkpoint.py backend/tests/test_agent_audit.py -q`

Expected: `2 passed` or more, including a resumed human-in-the-loop session.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/persistence backend/app/services/agent_audit_service.py backend/tests/test_agent_checkpoint.py backend/tests/test_agent_audit.py tests/ai-e2e-acceptance.md
git commit -m "feat: persist and audit agent workflows"
```

## Self-review

- RAGFlow is isolated behind a typed adapter and every returned knowledge answer carries a citation.
- LangGraph is the required orchestrator, but it can reach business data only through allowlisted tools.
- Intelligent query receives numeric values only from metric services and health scores only from the unified health-score service.
- AI fault reports pause for required inputs and final user confirmation.
- State, audit, Windows deployment, 100MB upload scope, legacy exclusions, backup policy, and secret handling are included.
- Before execution, select an actual OpenAI-compatible model endpoint and provide its non-committed deployment credentials. This is an environment prerequisite, not a reason to alter the architecture.
