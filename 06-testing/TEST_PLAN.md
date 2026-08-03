# 测试计划

- 状态：此前 Stage 6 结论与 Stage 6 → Stage 7 Gate 仅保留历史。TASK-012 已在新的集成基线 `75276cbf5291dd19932595aadc6daa6a3f782bc6` 完成 Stage 5 合并后治理；本计划新增的重测范围尚待项目负责人确认，未执行 Stage 6 重测、Stage 7 验收或 Stage 8 发布。
- 范围：Stage 1 验收标准、Stage 2 流程、Stage 3 状态、Stage 4 契约、生产实现和发布风险。

Test layers: unit; API/schema; permission; health-score rule; Agent graph/checkpoint/SSE; RAG citation and document lifecycle; integration; browser E2E; security; performance; backup/restore. Each case must identify environment, fixture, exact Commit SHA, result and evidence. Production tests must verify missing model configuration fails clearly, unauthorized Agent equipment is rejected without detail leakage, non-catalog metrics are rejected, AI fault interrupts resume by the same thread, and secrets never appear in audit records.

## TASK-012 后 Stage 6 独立重测（候选计划）

- 基线：仅测试 `codex/stage-05-integration` 的精确提交 `75276cbf5291dd19932595aadc6daa6a3f782bc6`。此前 PR #63、PR #61 或 PR #75 候选的结果只保留历史追溯，不能证明该新集成树通过。
- 独立性：由独立测试角色执行和签发结论；不继承 Stage 5 的开发者互审、单 Draft PR 或非作者 Merge 规则。任何业务代码、测试代码、数据库、基础设施、部署或运行配置缺陷均须登记并回流 Stage 5。
- 静态与回归：重新执行 CodeQL（Python、JavaScript/TypeScript）、Semgrep、Gitleaks（工作树与完整历史）、Trivy、15 项 Node 静态回归、后端全量回归、前端全量测试与生产构建。所有扫描工件须存入以本次 SUT SHA 命名的目录；HIGH/CRITICAL 仅可通过可验证修复或项目负责人已签署且仍适用的风险处置关闭。
- 隔离运行态：使用专用 PostgreSQL、Redis、MinIO、ClamAV、RAGFlow 数据集、临时账号和本地 HTTPS；不得使用生产数据、凭据、卷或公网暴露。验证 Compose、迁移、`/healthz`、Worker 文档生命周期、真实 RAGFlow 成功、`UNAVAILABLE` 降级、`NO_EVIDENCE`、附件扫描、API 重启恢复、HTTPS 与 JS/CSS MIME。
- 浏览器 E2E：在受信任的临时 HTTPS 配置下，验证未认证重定向、登录、Workbench、`/intelligent-config`、`/fault-report`、权限受限写操作和退出跳转 `/login`；记录浏览器版本、临时夹具与 SUT SHA，不记录账号口令或 Token。
- 性能与恢复：按本计划既有 1/2/5/10 并发与 P95 阈值重跑认证、附件、真实 RAGFlow 成功和不可用降级；重新执行受控附件备份、随机隔离恢复及恢复期间 10 并发只读验证。每份动态 JSON 的 `sut_commit`、`harness_commit` 与 `evidence_subject_commit` 必须为本次基线，或明确说明为何 harness 不同及其不可变关联。
- 退出条件：所有适用测试用例有 `PASS` 或经项目负责人接受的残余风险；无未处置 Critical/Important；测试报告绑定本次精确 SHA 并给出独立结论。仅在项目负责人明确批准该结论和精确候选后，方可重新进入 Stage 7。

## Stage 6 静态全局审查

静态审查基线为 `codex/stage-05-integration` 的精确提交；每次代码、依赖或部署配置变化后必须重跑，旧结果不能替代当前集成树证据。

- CodeQL：分别建立 Python 与 JavaScript/TypeScript 数据库，运行安全查询套件；归档 SARIF、扫描文件数和告警分类。
- Semgrep：运行社区规则集，重点复核 Bearer/SSE、附件/临时文件、RAGFlow URL、审计脱敏、Nginx 和 Dockerfile 告警的真实可达性。
- Gitleaks：扫描当前工作树及完整 Git 历史；历史命中必须确认是否为真实秘密，报告不得复制秘密值。
- Trivy：扫描依赖、秘密和基础设施错误配置；依赖告警需有可验证修复或项目负责人签署的适用性/风险处置。
- 静态用例：执行 `06-testing/tests/*.test.js`，其中 React Router 风险边界用例必须保持通过。

本层不启动 Docker、RAGFlow、数据库、浏览器或外部模型；这些活动属于后续 Stage 6 运行态验证，不能由静态结果替代。

## Stage 6 动态性能与恢复验证

- 基线：每份动态结果必须记录 SUT SHA、harness SHA、隔离 Compose 环境、夹具、执行时间与 evidence subject SHA；Agent 成功路径还必须记录并逐条校验 fixture 的 `document_id`、`chunk_id` 与 marker。结果仅在对应精确 SUT 上有效。当前认证、附件与两个 Agent 场景证据的 SUT/harness/evidence subject 均为 `ed0250cad87c8d814a5a2cc5cca8fb5217783064`；恢复只读结果须在其自身 JSON 中声明独立 SUT/harness，不得推断为当前候选结果。
- 性能场景：认证 `GET /api/auth/me`、附件 `POST /api/attachments`、真实 RAGFlow `POST /api/agent/operation-guidance` 成功路径、RAGFlow 不可用降级路径；每个场景总计 300 秒，按 1/2/5/10 并发执行。认证和附件 P95 不超过 1 秒，两个 Agent 场景 P95 不超过 15 秒。
- 恢复场景：在受控 API 附件备份和随机隔离恢复期间，对 `/api/auth/me` 运行固定 10 并发只读负载 60 秒；恢复不超过 180 秒，只读 P95 不超过 2 秒。结果 JSON 必须记录备份对象、恢复项目和只读端点 fixture。
- 复现：使用 `python 06-testing/performance/stage6_performance.py --scenario <auth|attachment|agent-success|agent-unavailable> --base-url <isolated-url> --token <ephemeral-token> --duration-seconds 300 --concurrency-levels 1,2,5,10 --p95-limit-ms <limit> --sut-commit <sha> --harness-commit <sha> --evidence-subject-commit <sha> --environment <isolated-compose-id> --fixture <fixture-id> --output <result.json>`；成功路径额外提供 `--agent-payload-json`、`--expected-reference-text`、`--expected-document-id` 和 `--expected-chunk-id`。本机自签名测试环境才允许 `--insecure-tls`。
- 证据：认证、附件、Agent 成功、Agent 降级和恢复只读结果分别归档在 `06-testing/performance/results-*-v2.json` 与 `results-backup-restore-readonly.json`；成功路径结果必须由当前 document/chunk 身份契约重新生成后才可作为通过证据。若单个并发层独立重试，主结果必须记录该层来源，并保留独立重试 JSON。
