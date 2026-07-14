# 新能源装载机设备智能运维平台

当前仓库按 `formal-software-delivery-workflow` 管理，所有阶段资料以编号目录为准。

## 当前状态

- 工作流状态：`PRODUCT_CLARIFICATION_REQUIRED`
- Stage 0–8：候选资料已整理，尚无阶段审批
- 生产实现：尚未开始
- 原始资产恢复点：`snapshot/legacy-import-20260714`
- 当前交接版本候选：`handoff/candidate-v20260714-01`

## 阅读顺序

1. `workflow/state.json`
2. `workflow/PROJECT_ASSET_BASELINE.md`
3. `workflow/EXTERNAL_BASELINE_INPUTS.md`
4. `01-requirements/PRD.md`
5. `01-requirements/SPEC.md`
6. `01-requirements/ACCEPTANCE_CRITERIA.md`
7. `01-requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md`
8. `04-architecture-plan/AI_RAGFLOW_LANGGRAPH_SPEC.md`
9. 各阶段目录中的候选资料

## 原型运行

```bash
node 03-ui-prototype/prototype/local-server-4209.js
```

访问 `http://127.0.0.1:4209/pages/intelligent-config.html`。

## 静态检查

```bash
for f in 06-testing/tests/*.test.js; do node "$f"; done
```

这些检查只证明静态原型规则，不等同于生产接口、权限、安全或验收测试。

## 版本管理

- `main`：正式仓库基线
- `agent/formal-stage-gate-migration`：本次正式化资料整理分支
- `snapshot/legacy-import-20260714`：接管前完整资产恢复点
- `handoff/candidate-v20260714-01`：2026-07-14 项目文档与静态原型候选交接快照
- 阶段审批通过后才创建 `baseline/stage-XX-...` 标签
