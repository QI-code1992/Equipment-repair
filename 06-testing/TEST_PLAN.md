# 测试计划

- 状态：Stage 6 未获准；静态全局审查与 PR #61 合并后的核心运行态验证已执行。性能边界、最终独立质量结论及 Stage 7 验收仍未执行或获批。
- 范围：Stage 1 验收标准、Stage 2 流程、Stage 3 状态、Stage 4 契约、生产实现和发布风险。

Test layers: unit; API/schema; permission; health-score rule; Agent graph/checkpoint/SSE; RAG citation and document lifecycle; integration; browser E2E; security; performance; backup/restore. Each case must identify environment, fixture, exact Commit SHA, result and evidence. Production tests must verify missing model configuration fails clearly, unauthorized Agent equipment is rejected without detail leakage, non-catalog metrics are rejected, AI fault interrupts resume by the same thread, and secrets never appear in audit records.

## Stage 6 静态全局审查

静态审查基线为 `codex/stage-05-integration` 的精确提交；每次代码、依赖或部署配置变化后必须重跑，旧结果不能替代当前集成树证据。

- CodeQL：分别建立 Python 与 JavaScript/TypeScript 数据库，运行安全查询套件；归档 SARIF、扫描文件数和告警分类。
- Semgrep：运行社区规则集，重点复核 Bearer/SSE、附件/临时文件、RAGFlow URL、审计脱敏、Nginx 和 Dockerfile 告警的真实可达性。
- Gitleaks：扫描当前工作树及完整 Git 历史；历史命中必须确认是否为真实秘密，报告不得复制秘密值。
- Trivy：扫描依赖、秘密和基础设施错误配置；依赖告警需有可验证修复或项目负责人签署的适用性/风险处置。
- 静态用例：执行 `06-testing/tests/*.test.js`，其中 React Router 风险边界用例必须保持通过。

本层不启动 Docker、RAGFlow、数据库、浏览器或外部模型；这些活动属于后续 Stage 6 运行态验证，不能由静态结果替代。

## Stage 6 动态性能与恢复验证

- 基线：每份动态结果必须记录 SUT SHA、harness SHA、隔离 Compose 环境、夹具和执行时间；Agent 成功路径还必须记录并逐条校验 fixture 的 `document_id`、`chunk_id` 与 marker。结果仅在对应精确 SUT 上有效。当前 Agent 成功证据的 SUT/harness 为 `a07b3b4bcc20439c786e8ad6a5dc7204dc390a3e`，首次归档记录为 `a3189e590897ca4dd7c3de90075c3a678be9469e`。
- 性能场景：认证 `GET /api/auth/me`、附件 `POST /api/attachments`、真实 RAGFlow `POST /api/agent/operation-guidance` 成功路径、RAGFlow 不可用降级路径；每个场景总计 300 秒，按 1/2/5/10 并发执行。认证和附件 P95 不超过 1 秒，两个 Agent 场景 P95 不超过 15 秒。
- 恢复场景：在受控 API 附件备份和随机隔离恢复期间，对 `/api/auth/me` 运行固定 10 并发只读负载 60 秒；恢复不超过 180 秒，只读 P95 不超过 2 秒。结果 JSON 必须记录备份对象、恢复项目和只读端点 fixture。
- 复现：使用 `python 06-testing/performance/stage6_performance.py --scenario <auth|attachment|agent-success|agent-unavailable> --base-url <isolated-url> --token <ephemeral-token> --duration-seconds 300 --concurrency-levels 1,2,5,10 --p95-limit-ms <limit> --sut-commit <sha> --harness-commit <sha> --environment <isolated-compose-id> --fixture <fixture-id> --output <result.json>`；成功路径额外提供 `--agent-payload-json`、`--expected-reference-text`、`--expected-document-id` 和 `--expected-chunk-id`。本机自签名测试环境才允许 `--insecure-tls`。
- 证据：认证、附件、Agent 成功、Agent 降级和恢复只读结果分别归档在 `06-testing/performance/results-*-v2.json` 与 `results-backup-restore-readonly.json`；成功路径结果必须由当前 document/chunk 身份契约重新生成后才可作为通过证据。若单个并发层独立重试，主结果必须记录该层来源，并保留独立重试 JSON。
