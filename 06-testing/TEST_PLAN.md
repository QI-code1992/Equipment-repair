# Test Plan

- Status: Candidate / not executed for production
- Scope: Stage 1 AC, Stage 2 flows, Stage 3 states, Stage 4 contracts, production implementation and release risks.

Test layers: unit; API/schema; permission; health-score rule; Agent graph/checkpoint/SSE; RAG citation and document lifecycle; integration; browser E2E; security; performance; backup/restore. Each case must identify environment, fixture, exact Commit SHA, result and evidence. Production tests must verify missing model configuration fails clearly, unauthorized Agent equipment is rejected without detail leakage, non-catalog metrics are rejected, AI fault interrupts resume by the same thread, and secrets never appear in audit records.
