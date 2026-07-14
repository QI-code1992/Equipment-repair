# Implementation Plan Candidate

1. Confirm Stage 1–4 baselines and unresolved decisions.
2. Establish service repository, environment contract, migrations and seed roles/permissions.
3. Implement auth, menu/operation permissions, audit and equipment aggregates.
4. Implement fault, work-order, maintenance and knowledge metadata APIs.
5. Implement health-score service and snapshot persistence.
6. Implement RAGFlow adapter and citation contract.
7. Implement LangGraph fault-report, metric-query and diagnosis/advice graphs with allowlisted tools.
8. Replace prototype adapters with API clients and preserve approved interaction states.
9. Add unit, API, permission, contract, integration, security and end-to-end tests.
10. Execute Stage 6, obtain exact Commit SHA approval, then acceptance and release handoff.

Each task becomes a development checkpoint only after its tests and relevant regression checks pass. No production task is authorized before Stage 4 approval.
