# 测试计划

- 状态：Stage 6 已获准；静态全局审查已执行，运行态测试尚未执行
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
