# 新能源装载机设备智能运维平台 SPEC

- Baseline: Candidate v1.0
- Status: Awaiting Stage 1 user approval
- Related PRD: `01-requirements/PRD.md`

## 1. System boundary

| Component | Responsibilities | Prohibited |
|---|---|---|
| Business system | Auth, menus, permissions, devices, faults, work orders, maintenance, health service, audit, UI | Treat static demo data as business fact |
| LangGraph Agent | Intent, permission gate, missing-field collection, controlled tool calls, human confirmation, response | Direct database writes, health-score calculation, bypassing business API |
| RAGFlow | Parse, chunk, embed, index, retrieve, rerank and cite documents | Store business facts, calculate metrics, create work orders |
| LLM | Understand language, summarize API/RAG results | Guess numbers, diagnosis facts, sources or permissions |

## 2. Roles and permission matrix

| Capability | Admin | Equipment admin | Repair worker | Line operator |
|---|---:|---:|---:|---:|
| User/role/menu/operation management | Manage | View | None | None |
| User management scope (`user_management.view_all`) | All users | Granted scope | Self only | Self only |
| Equipment list/detail | Manage | Manage | View | View assigned context |
| Equipment knowledge | Manage | Manage | View | None |
| Manual fault report | Create/view | Create/view | Create/view | Create/view |
| AI floating Agent | Use/manage | Use | Use | Use |
| AI fault-report creation | Create | Create | Create | Create |
| AI diagnosis review | View | Review/confirm | View | View related |
| Draft work order | Manage | Confirm/dispatch | View | View related |
| Repair execution | View | View/accept | Execute/submit | View progress |
| Health score/BI | View | View | View | View related |

Server-side authorization is mandatory. Device grants constrain Agent equipment lookup/reporting only and do not become general data filtering.

`user_management.view_all` controls user-management visibility; it does not expand Agent device grants or create general data permissions.

## 3. Page and route contract

| Page | Route candidate | Required states |
|---|---|---|
| Login | `/login` | default, invalid, disabled, loading |
| Workbench | `/workbench` | default, empty, error, permission |
| BI dashboard | `/bi-dashboard` | default, empty, error, filter |
| Equipment ledger | `/equipment` | list, empty, loading, error, permission |
| Factory modeling | `/factory-modeling` | tree, detail, add/edit, disable cascade, delete blocked |
| Equipment add/edit/detail | `/equipment/new`, `/equipment/:id/edit`, `/equipment/:id` | validation, saving, error, forbidden |
| Equipment knowledge/config | `/intelligent-config` | tab, upload states, failed index, readonly metrics |
| Fault report | `/fault-report` | draft, validation, AI pending, submitted |
| Agent report | `/agent-report` | permission identified, missing fields, handoff, submit gate |
| Maintenance records | `/maintenance-records` | list, detail, empty, error |
| Repair execution | `/repair-execution` | assigned, editing, submitted, forbidden |
| System management | `/system-management` | user/role/menu/audit tabs, readonly/permission |
| Global Agent | drawer on authorized pages | closed, open, tab history, collecting, preview, error |

The historical data-import page is not a current route/menu/permission/API requirement.

## 4. Data contracts

### Equipment

`id`, `code` unique, `name`, `model`, `type`, `manufacturer`, `manufacturedAt`, `commissionedAt`, `operatingHours >= 0`, `status`, `ownerUserId`, `imageRefs`, timestamps.

### Fault report

`id`, `equipmentId`, `submitterId`, `urgency`, `symptom`, `occurredAt <= now`, `duration`, `possibleLocation`, `description`, `attachmentRefs`, `status`, `submittedAt`, `auditRefs`. AI 上报正式提交前 `occurredAt` 与 `duration` 必填。Status: `AI_DRAFT -> PENDING_ACCEPT -> IN_REPAIR -> PROCESSED`.

### Work order

`id`, `faultId`, `assigneeId`, `diagnosisRef`, `repairAdviceRef`, `status`, `actualCause`, `actualSolution`, `repairResult`, `inspectionResult`, timestamps. Status: `DRAFT -> PENDING_ACCEPT -> IN_REPAIR -> PENDING_INSPECTION -> COMPLETED`, with reject/repair exception paths.

### Health score

`equipmentId`, `score`, `grade`, `calculatedAt`, `periodStart`, `periodEnd`, `components`, `serviceStatus`. Snapshot: before/after score, trigger, deductions/recoveries, fault/order refs, calculation time.

### Knowledge document

`id`, `datasetId`, `ragDocumentId`, `name`, `mimeType`, `size <= 100MB`, `status`, `failureReason`, `sourceRefs`, timestamps. Only `READY` documents are retrievable.

## 5. Health service contract

`GET /api/equipment/{equipmentId}/health-score` returns score, grade, component breakdown, current period, snapshot summary and `serviceStatus`. On failure it returns an error status; clients must not substitute cached, zero or empty values. Workbench, BI, ledger, detail and metric-query adapters call this service.

## 6. Metric query contract

`GET /api/metrics/catalog` returns the fixed 40 metric definitions, allowed dimensions, formula, period and examples. `POST /api/metrics/query` accepts only a catalog metric ID, allowed dimension values, and a date range. Agent tool `get_metric` may call only these endpoints. The LLM receives results and may summarize them but cannot create values.

## 7. Agent tool allowlist

`get_metric`, `get_health_score`, `get_granted_equipment`, `retrieve_knowledge`, `create_fault_draft`, `submit_fault_report`, `get_fault_progress`. Every write tool requires a permission check and, where specified, human confirmation. RAG citations must include document and chunk identifiers.

The allowlist is closed: no direct database, arbitrary SQL, health-score write, maintenance-record write, permission/user mutation or filesystem-execution tool may be registered.

## 8. Agent state machines

### AI fault report

`load_context -> check_permission -> collect_equipment -> collect_urgency -> collect_symptom -> collect_optional_context -> preview -> human_confirm -> create_fault_draft -> final_response`.

Missing required fields loop back to collection. Permission denial ends in an explanatory response. Attachment failure preserves text context and reports retry.

### Intelligent query

`load_context -> detect_intent -> match_metric -> validate_dimensions -> ask_missing_or_query -> summarize -> final_response`.

Unknown metrics, disallowed dimensions, and backend errors are explicit failures; no guessed values.

### Diagnosis/advice

`load_context -> check_permission -> retrieve_knowledge -> load_business_data -> generate_diagnosis -> generate_repair_advice -> human_review -> draft_work_order -> final_response`.

Low confidence, high-voltage, brake, or safety-critical cases require human review and safety instructions.

### Agent runtime contract

- `POST /api/agent/threads` creates a user-bound thread.
- `POST /api/agent/threads/{thread_id}/messages` streams `token`, `tool_started`, `tool_finished`, `interrupt`, `completed`, and `error` events through SSE.
- `POST /api/agent/threads/{thread_id}/resume` resumes a LangGraph interrupt using the same `thread_id`.
- `GET /api/agent/threads/{thread_id}` is visible only to the creator or system administrator.
- Shared state includes `thread_id`, `user_id`, `role`, `page_context`, `messages`, `tool_results`, `citations`, `pending_confirmation`, and `audit_id`.

## 9. Validation and exception rules

- Equipment code duplicate blocks save.
- Equipment deactivation is blocked by pending/repairing faults.
- Fault requires one equipment, urgency and symptom; occurrence cannot be future.
- AI preview is readonly; edits happen through dialogue or fault-report page.
- AI draft cannot become a formal pending fault until user submits.
- Work order cannot close without actual cause, solution and repair result.
- RAGFlow parse/index failure excludes a document from retrieval.
- Agent unavailable does not block manual fault and work-order flows.
- Permission failures are audit events.
- AI fault reporting pauses on missing `occurredAt` or `duration` and resumes after user input; formal submission always requires explicit user confirmation.
- RAGFlow empty retrieval returns an explicit no-citation result; it must not be converted into a fabricated citation or answer.
- Work-order UI labels map to API states: `待派单`=`DRAFT/PENDING_ACCEPT`, `维修中`=`IN_REPAIR`, `待验收`=`PENDING_INSPECTION`, `已关闭`=`COMPLETED`.

## 10. Non-functional traceability

| NFR | Specification |
|---|---|
| NFR-001 Security | server-side auth, audit events, secrets out of Git |
| NFR-002 Explainability | citation IDs, confidence, score components |
| NFR-003 Availability | manual fallback when Agent/RAGFlow unavailable |
| NFR-004 Traceability | exact Commit SHA, stage ledgers, change IDs |
| NFR-005 Operations | Windows demo, 00:10 backup, 10-day retention, Tailscale Funnel |

## 11. Open engineering decisions

Confirm before Stage 4 approval: first equipment models, supported document MIME types, RAGFlow deployment, embedding/rerank models, LLM deployment/data boundary, metadata schema, database choice, API authentication, and backup storage.
