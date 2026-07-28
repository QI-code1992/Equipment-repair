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

动态、浏览器与 live-stack 可执行用例在相应 Stage 6 验证启动前补齐并绑定精确集成提交；不得将下列静态用例替代其运行态证据。

## Stage 6 静态全局审查用例

| ID | 用例与通过条件 | 证据 |
|---|---|---|
| TC-STATIC-001 | CodeQL Python 与 JavaScript/TypeScript 安全查询完成；生产 `codebase/` 中无未分类 Critical/Important 安全结果。 | 两份 SARIF、扫描文件数、人工分类。 |
| TC-STATIC-002 | Semgrep 覆盖 Git 跟踪源文件；所有生产路径命中均有可达性结论，不将固定上游、受控配置或公开 API 路由误标为 SSRF。 | JSON 结果、Nginx/RAGFlow 配置核查。 |
| TC-STATIC-003 | Gitleaks 当前工作树及完整历史均扫描；无当前秘密，历史命中只保留脱敏分类说明。 | 两份脱敏 JSON 报告。 |
| TC-STATIC-004 | Trivy 覆盖依赖、秘密、Dockerfile 与 Compose；HIGH/CRITICAL 必须关闭或有项目负责人明确风险处置；React Router 边界回归通过。 | Trivy JSON、风险处置、`react-router-rsc-risk.test.js`。 |
