# 测试计划

- 状态：候选版 / 尚未执行生产测试
- 范围：Stage 1 验收标准、Stage 2 流程、Stage 3 状态、Stage 4 契约、生产实现和发布风险。

Test layers: unit; API/schema; permission; health-score rule; Agent graph/checkpoint/SSE; RAG citation and document lifecycle; integration; browser E2E; security; performance; backup/restore. Each case must identify environment, fixture, exact Commit SHA, result and evidence. Production tests must verify missing model configuration fails clearly, unauthorized Agent equipment is rejected without detail leakage, non-catalog metrics are rejected, AI fault interrupts resume by the same thread, and secrets never appear in audit records.

## Stage 6 静态全局审查

基线为获批应用候选 `8a5e6ced473ea6219666d858ce5b751e61362871`。所有报告记录工具版本、完整命令、规则/数据库版本、扫描范围、排除路径、精确 SHA、原始 SARIF/JSON 路径、发现数量、人工分类、修复 PR 与复扫结果。

| 工具 | 范围与命令 | 阈值 |
|---|---|---|
| CodeQL | Python、TypeScript/JavaScript、Docker/配置；本地数据库分析或 GitHub Code Scanning SARIF | Critical/High 必须关闭或按项目负责人接受风险 |
| Semgrep | `semgrep scan --config auto codebase`；认证、上传、RAGFlow、审计和 Nginx 自定义审查 | Critical/High 必须关闭；其余须人工分类 |
| Gitleaks | `gitleaks git` 加当前工作树扫描 | 任何真实密钥阻断；环境变量引用须人工分类 |
| Trivy | `trivy fs --scanners vuln,secret,misconfig`，含依赖与 Dockerfile/Compose/Nginx | Critical/High 必须关闭或接受风险 |
