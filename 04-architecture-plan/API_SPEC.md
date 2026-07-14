# API Specification Candidate

- Status: Awaiting Stage 4 approval

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

All write requests require authenticated actor, idempotency key where repeatable, validation errors with field paths, and audit event IDs. Exact schemas and auth mechanism are open Stage 4 decisions.
