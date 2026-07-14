# System Architecture

- Baseline: Candidate v1.0
- Status: Awaiting Stage 4 approval

## Context

```text
Web UI ──HTTPS──> Business API ──> Database / Audit / File metadata
  │                       ├──> Unified health-score service
  │                       └──> LangGraph Agent ──> allowlisted business tools
  │                                                   └──> RAGFlow (parse/retrieve/rerank/cite)
  └──> Agent drawer
```

## Boundaries

- Business API is the only writer of business facts and permissions.
- Health-score service owns score calculation and snapshots.
- LangGraph owns controlled stateful orchestration and human-confirmation pauses.
- RAGFlow owns document processing and retrieval evidence; it does not own business truth.
- LLM produces language from tool results; it does not calculate or infer missing facts.

## Trust boundaries

Browser input, uploaded files, external LLM/RAGFlow calls and Agent tool calls are untrusted boundaries. Authenticate at the business API, authorize every operation server-side, validate file type/size, redact secrets, and audit permission denials and writes.

## Deployment candidate

Windows demonstration environment; business service, database, RAGFlow and LangGraph may be separate processes. Tailscale Funnel is temporary external access. Backup at 00:10 with 10-day retention. Exact production topology remains a Stage 4 decision.
