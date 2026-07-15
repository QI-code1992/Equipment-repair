# 原型基线

- 基线：已批准 v1.0
- 状态：Stage 3 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-004
- 来源：`03-ui-prototype/prototype/`
- 导入源码 Commit：`c544c2d`（原始快照）；迁移 Commit：`32d1b7b`

## 包含内容

Login, workbench, BI, factory model, equipment ledger/add/edit/detail, fault report, Agent report, maintenance records, repair execution, system management and intelligent configuration. The prototype is static HTML/CSS/JavaScript and includes a local Node server and static rule checks.

## 约束

- It is design/reference evidence, not a production service.
- Static numbers, old labels and historical data-import navigation must not override Stage 1.
- `assets/health-score-service.js` is an adapter shape only; production health calculation belongs to the backend service.
- P0 state coverage still needs verification for loading, empty, error, disabled, permission and boundary cases.

## 候选增量 v1.1：维修接单前诊断 Agent

当前 `fault-report.html` 包含开始维修双栏独立滚动、3 秒检索加载、配置驱动的流式对话、动态问题计划、报警码必填、证据不足保护、采纳/直接开始边界、结束维修预填与 AI 摘要展示。该增量仍是 Stage 3 候选原型，不构成生产模型/RAG 集成承诺。

## 恢复

```bash
git restore --source snapshot/legacy-import-20260714 -- prototype/prototype
git restore --source 32d1b7b -- 03-ui-prototype/prototype
```
