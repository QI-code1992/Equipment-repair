# 需求追踪矩阵

- 基线：已批准 v1.1
- 状态：Stage 1 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-002

| 需求 | SPEC 章节 | 验收标准 | 原型证据 | 测试包 | 状态 |
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
| NFR-006 AI runtime/configuration | 10, SPEC Agent runtime contract | AC-032, 035 | `04-architecture-plan/AI_RAGFLOW_LANGGRAPH_SPEC.md` | TC-AI-CONFIG-* | Candidate |
| NFR-007 Citation and tool boundary | 1, 7, 8 | AC-033, 036 | RAGFlow/LangGraph architecture candidate | TC-AI-BOUNDARY-* | Candidate |
| NFR-008 Thread and authorization detail isolation | 2, 7, 8 | AC-034, 037 | Agent permission boundary; CR-043 excludes `EquipmentGrant` / equipment row-level filtering | TC-AI-PERM-* | Candidate updated by CR-043 |
| NFR-009 Audit redaction | 10 | AC-038 | audit contract candidate | TC-SEC-AI-* | Candidate |
| FR-010 Logout navigation | 2, 9 | AC-039 | global user menu | TC-AUTH-LOGOUT-* | Candidate |
| FR-RA-001 动态诊断追问与建议 | PRD 12、SPEC 12.3 | AC-040 | `fault-report.html` | `fault-report-repair-agent.test.js` | Candidate v1.1 |
| FR-RA-002 报警码必填与否定证据 | PRD 12、SPEC 12.2 | AC-041、AC-042 | `fault-report.html` | `fault-report-repair-agent.test.js` | Candidate v1.1 |
| FR-RA-003 采纳/直接开始与摘要边界 | PRD 12、SPEC 12.2 | AC-043 | `fault-report.html` | `fault-report-repair-agent.test.js` | Candidate v1.1 |
| FR-RA-004 Agent 降级 | PRD 12、SPEC 12.1 | AC-044 | `fault-report.html` | `fault-report-repair-agent.test.js` | Candidate v1.1 |

## 覆盖规则

- 每个 `FR-*` 和 `NFR-*` 至少映射一个 `AC-*`。
- 每个 `AC-*` 必须在 Stage 6 获得一个或多个 `TC-*` 测试用例。
- 原型证据仅用于设计和参考，不能替代生产验证。
- 任何基线变更都必须原地更新本矩阵，并在 `workflow/CHANGE_REQUESTS.md` 记录变更。
