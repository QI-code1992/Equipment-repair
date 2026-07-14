# 系统架构

- 基线：候选版 v1.0
- 状态：等待 Stage 4 审批

## 上下文

```text
Web UI ──HTTPS──> Business API ──> Database / Audit / File metadata
  │                       ├──> Unified health-score service
  │                       └──> LangGraph Agent ──> allowlisted business tools
  │                                                   └──> RAGFlow (parse/retrieve/rerank/cite)
  └──> Agent drawer
```

## 边界

- Business API is the only writer of business facts and permissions.
- Health-score service owns score calculation and snapshots.
- LangGraph owns controlled stateful orchestration and human-confirmation pauses.
- RAGFlow owns document processing and retrieval evidence; it does not own business truth.
- LLM produces language from tool results; it does not calculate or infer missing facts.

## 信任边界

Browser input, uploaded files, external LLM/RAGFlow calls and Agent tool calls are untrusted boundaries. Authenticate at the business API, authorize every operation server-side, validate file type/size, redact secrets, and audit permission denials and writes.

## 候选部署方案

Windows demonstration environment; business service, database, RAGFlow and LangGraph may be separate processes. Tailscale Funnel is temporary external access. Backup at 00:10 with 10-day retention. Exact production topology remains a Stage 4 decision.

## Stage 4 技术基线

- Runtime: Python 3.13 + FastAPI.
- Business persistence: PostgreSQL; business attachments: MinIO/S3-compatible object storage; Redis for short-lived cache and rate limiting.
- RAGFlow runs in an independent Docker Compose dependency stack and must not share PostgreSQL, Redis, MinIO instances or accounts with the business system.
- Model access uses an OpenAI-compatible gateway with separately configured chat, Embedding and Rerank names, endpoints and secrets. Missing configuration is a health-check failure, never a pseudo-result.
- Windows host uses Docker Desktop with WSL2 Linux containers. Funnel exposes only the front-end/API HTTPS entry; databases, object storage, Redis, RAGFlow and dependencies stay on the internal Docker network.

## Agent 与知识边界

LangGraph checkpoints use PostgreSQL so an interrupted workflow can resume after refresh or service restart. Each thread is bound to its creating user. RAGFlow documents move through `UPLOADING -> PARSING -> READY|FAILED`; only `READY` documents are retrievable and every citation carries document and chunk identifiers. Agent tools are closed-world allowlisted and all calls are audited without secrets.
