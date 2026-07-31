# 测试用例

| ID 范围 | 覆盖内容 | 来源 |
|---|---|---|
| TC-EQ-* | equipment CRUD, duplicate, owner, deactivation | AC-006–008 |
| TC-KB-* | document lifecycle, failed retrieval, citations | AC-009 |
| TC-FR-* | manual and AI fault validation/status | AC-010–015 |
| TC-MET-* | 40 metrics, dimensions, query failures | AC-016–019 |
| TC-HS-* | unified health, launch baseline, snapshots/failure | AC-020–023 |
| TC-DIAG-* | diagnosis evidence and safety review | AC-024–025 |
| TC-WO-* | draft confirmation, repair closure, sedimentation | AC-026–028 |
| TC-SEC-* | login, permission, audit, secrets | AC-001–005 |
| TC-RES-* | outage fallback, repeated submit, UI states | AC-029–031 |

## TASK-012 统一开发候选回归（2026-07-31）

| ID | 用例与通过条件 | 当前证据 |
|---|---|---|
| TC-T012-READ-001 | BI 日/周/月窗口、组织不存在、设备历史趋势、维修记录知识状态、工单状态和审计筛选均调用正式 API；不拼接业务聚合。 | `tests/modules/test_task012_read_apis.py`；前端 `PortalPages.test.tsx`。 |
| TC-T012-AGENT-001 | 线程历史只返回当前用户摘要；详情、resume 布尔契约、SSE 状态可用；原始用户消息和思维链不渲染。 | `test_agent_runtime.py`；`App.test.tsx`、`api.test.ts`。 |
| TC-T012-ATTACH-001 | 故障上报和 AI 故障上报只接受附件上传 API 返回的安全引用；上传中/失败时不能写入附件引用。 | `FaultReportPage.test.tsx`、`IntelligentConfigPage.test.tsx`。 |
| TC-T012-UI-001 | 全部正式 P0 路由拥有加载、空、错误、禁用或权限状态；数据导入明确排除。 | `FRONTEND_PROTOTYPE_DIFFERENCE_MATRIX.md` 与页面测试。 |

动态、浏览器与 live-stack 可执行用例在相应 Stage 6 验证启动前补齐并绑定精确集成提交；不得将下列静态用例替代其运行态证据。

## Stage 6 静态全局审查用例

| ID | 用例与通过条件 | 证据 |
|---|---|---|
| TC-STATIC-001 | CodeQL Python 与 JavaScript/TypeScript 安全查询完成；生产 `codebase/` 中无未分类 Critical/Important 安全结果。 | 两份 SARIF、扫描文件数、人工分类。 |
| TC-STATIC-002 | Semgrep 覆盖 Git 跟踪源文件；所有生产路径命中均有可达性结论，不将固定上游、受控配置或公开 API 路由误标为 SSRF。 | JSON 结果、Nginx/RAGFlow 配置核查。 |
| TC-STATIC-003 | Gitleaks 当前工作树及完整历史均扫描；无当前秘密，历史命中只保留脱敏分类说明。 | 两份脱敏 JSON 报告。 |
| TC-STATIC-004 | Trivy 覆盖依赖、秘密、Dockerfile 与 Compose；HIGH/CRITICAL 必须关闭或有项目负责人明确风险处置；React Router 边界回归通过。 | Trivy JSON、风险处置、`react-router-rsc-risk.test.js`。 |
| TC-PERF-001 | 认证和附件在 1/2/5/10 并发、每场景 300 秒下零意外错误，P95 不超过 1 秒。 | `results-auth-v2.json`、`results-attachment-v2.json`，含 SUT/harness/环境/夹具。 |
| TC-PERF-002 | 真实 RAGFlow 成功路径在 1/2/5/10 并发下为 `QUESTIONING`；每条 evidence 的 marker、`document_id`、`chunk_id` 均绑定本次 fixture，P95 不超过 15 秒。 | `results-agent-success-final-v2.json`，含 SUT/harness、预期身份对、每层绑定统计和逐层来源；独立重试保留为 `results-agent-success-10-concurrency-retry.json`。 |
| TC-PERF-003 | 受控 RAGFlow 不可用路径在 1/2/5/10 并发下均为 `UNAVAILABLE`、零引用、零意外错误，P95 不超过 15 秒。 | `results-agent-unavailable-v2.json`，含 SUT/harness/环境/夹具。 |
| TC-AGENT-EMPTY-001 | RAGFlow 正常返回但无 citation 时，响应为 `NO_EVIDENCE`、空 evidence，并给出无可引用依据的人工处理提示；不得返回 `QUESTIONING`。维修执行页面必须呈现该提示，不能显示为空白。 | `tests/agents/test_operation_guidance.py` 单元/API 回归及 `RepairExecutionPage.test.tsx` 交互回归。 |
| TC-RESTORE-001 | 受控附件备份和随机隔离恢复不超过 180 秒；恢复期间 `/api/auth/me` 固定 10 并发只读 60 秒，零意外错误且 P95 不超过 2 秒。 | `results-backup-restore-readonly.json`，含 SUT/harness/恢复环境/受控附件与恢复项目 fixture。 |
