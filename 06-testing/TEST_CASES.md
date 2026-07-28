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

详细可执行用例需等待 Stage 4 API/数据契约获批后编写。

| ID | 静态审查用例 | 通过条件 | 证据 |
|---|---|---|---|
| TC-STATIC-001 | CodeQL 全仓扫描 | 无未处置 Critical/High | SARIF、人工分类 |
| TC-STATIC-002 | Semgrep 安全规则与项目边界复核 | 无未处置 Critical/High；误报有理由 | JSON/SARIF、分类表 |
| TC-STATIC-003 | Gitleaks 历史与工作树 | 无真实密钥；疑似项脱敏分类 | JSON、提交范围 |
| TC-STATIC-004 | Trivy 依赖/密钥/误配置 | 无未处置 Critical/High | JSON、SBOM/锁文件范围 |
