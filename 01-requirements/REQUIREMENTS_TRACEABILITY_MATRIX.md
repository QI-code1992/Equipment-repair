# Requirements Traceability Matrix

- Baseline: Candidate v1.0
- Status: Awaiting Stage 1 user approval

| Requirement | SPEC section | AC | Prototype evidence | Test package | Status |
|---|---|---|---|---|---|
| FR-001 Equipment ledger | 3, 4 | AC-006–008 | `03-ui-prototype/prototype/pages/equipment-ledger.html`, detail/add/edit | TC-EQ-* | Candidate |
| FR-002 Knowledge config | 1, 7, 9 | AC-009 | `03-ui-prototype/prototype/pages/intelligent-config.html` | TC-KB-* | Candidate |
| FR-003 Manual fault | 3, 9 | AC-010 | `03-ui-prototype/prototype/pages/fault-report.html` | TC-FR-* | Candidate |
| FR-004 AI fault | 7, 8, 9 | AC-011–015 | global Agent in prototype and fault page | TC-AI-FR-* | Candidate |
| FR-005 Global Agent | 2, 7, 8 | AC-003–005, 029 | shared Agent UI | TC-AG-* | Candidate |
| FR-006 Intelligent query | 6, 8 | AC-016–019 | intelligent-config metric view and Agent | TC-MET-* | Candidate; one legacy static test conflicts |
| FR-007 Diagnosis/advice | 1, 7, 8 | AC-024–025 | agent-report/detail prototype | TC-DIAG-* | Candidate |
| FR-008 Work order/repair | 3, 9 | AC-026–028 | repair-execution/maintenance-records prototype | TC-WO-* | Candidate |
| FR-009 Health score | 4, 5, 6 | AC-020–023 | workbench/BI/equipment detail + health service adapter | TC-HS-* | Candidate |
| FR-010 Admin/audit | 2, 9 | AC-001–005 | system-management prototype | TC-PERM-* | Candidate |
| NFR-001 Security | 10 | AC-003–005 | permission states | TC-SEC-* | Candidate |
| NFR-002 Explainability | 1, 7 | AC-009, 024–025 | citation/diagnosis cards | TC-EXP-* | Candidate |
| NFR-003 Availability | 8 | AC-029 | manual fallback pages | TC-RES-* | Candidate |
| NFR-004 Traceability | workflow | all AC | workflow ledgers and Git | TC-GOV-* | Candidate |
| NFR-005 Operations | 10 | release criteria | prototype run notes | TC-OPS-* | Candidate |

## Coverage rules

- Every `FR-*` and `NFR-*` maps to at least one `AC-*`.
- Every `AC-*` must receive one or more `TC-*` cases in Stage 6.
- Prototype evidence is design/reference evidence only; it cannot replace production verification.
- Any baseline change updates this matrix in place and records movement in `workflow/CHANGE_REQUESTS.md`.
