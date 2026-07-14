# API 规格（候选版）

- 状态：等待 Stage 4 审批

| Method | Endpoint | Purpose | Authorization |
|---|---|---|---|
| GET | `/api/equipment` | list/filter equipment | menu + operation |
| POST | `/api/equipment` | create equipment | equipment manage |
| PATCH | `/api/equipment/{id}` | update/owner/status | equipment manage + guards |
| GET | `/api/equipment/{id}/health-score` | unified health result | equipment view |
| POST | `/api/fault-reports` | manual formal submit | fault create |
| POST | `/api/fault-reports/drafts` | create AI draft | fault create + Agent |
| POST | `/api/fault-reports/{id}/submit` | submit AI draft | submitter + fault create |
| GET | `/api/metrics/catalog` | fixed 40 metrics | metric view |
| POST | `/api/metrics/query` | query allowed metric | metric query |
| POST | `/api/knowledge/documents` | create/upload metadata | knowledge manage |
| GET | `/api/knowledge/documents/{id}` | processing status | knowledge view |
| POST | `/api/work-orders/{id}/confirm` | confirm/dispatch draft | equipment manage |
| POST | `/api/work-orders/{id}/repair-result` | submit repair result | repair execute |
| POST | `/api/agent/runs` | run controlled Agent | Agent permission |
| POST | `/api/agent/threads` | create user-bound LangGraph thread | authenticated user |
| POST | `/api/agent/threads/{thread_id}/messages` | stream Agent events over SSE | thread owner |
| POST | `/api/agent/threads/{thread_id}/resume` | resume interrupt or confirmation | thread owner |
| GET | `/api/agent/threads/{thread_id}` | read visible thread and citations | thread owner or system admin |

Knowledge adapter methods: `ingest_document`, `get_ingestion_status`, `retrieve_knowledge`, `delete_document`. Document states are `UPLOADING`, `PARSING`, `READY`, `FAILED`; only `READY` participates in retrieval.

All write requests require authenticated actor, idempotency key where repeatable, validation errors with field paths, and audit event IDs. SSE events are `token`, `tool_started`, `tool_finished`, `interrupt`, `completed`, `error`. Model/API inputs cannot override user identity, role, grants or confirmation state.
