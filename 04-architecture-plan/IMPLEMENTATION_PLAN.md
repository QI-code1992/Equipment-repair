# 实施计划（候选版）

1. Confirm Stage 1–4 baselines, external development baseline and unresolved decisions; no production implementation before Stage 4 approval.
2. Establish Python 3.13/FastAPI service repository, environment contract, PostgreSQL migrations, MinIO/S3 and Redis dependencies, and seed roles/permissions.
3. Implement auth, menu/operation permissions, audit and equipment aggregates.
4. Implement fault, work-order, maintenance and knowledge metadata APIs.
5. Implement health-score service and snapshot persistence.
6. Implement independent RAGFlow adapter, document lifecycle and citation contract.
7. Implement LangGraph threads/checkpoints, SSE events, fault-report, metric-query and diagnosis/advice graphs with closed allowlisted tools.
8. Replace prototype adapters with API clients and preserve approved interaction states.
9. Add unit, API, permission, contract, Agent/RAG citation, integration, security, performance, backup/restore and end-to-end tests.
10. Execute Stage 6, obtain exact Commit SHA approval, then acceptance and release handoff.

每项任务只有在测试和相关回归检查通过后，才能形成开发检查点。Stage 4 审批前不得执行生产开发任务。
