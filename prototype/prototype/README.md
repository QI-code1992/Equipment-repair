# 新能源装载机智能运维平台｜完整开发交接包

> **开发前先读：** `docs/开发交付入口.md`。它明确当前有效依据、必须开发项、明确不开发项与历史材料边界；不得直接以旧 PDF、旧计划或页面静态演示数据实现业务规则。

生成日期：2026-07-13

这是面向开发、联调和测试的完整交接包。历史“智能配置专项开发交接文档”已融合为当前有效 PRD、开发交付入口和 AI 技术 SPEC；不得再寻找或引用已拆分的旧文件。

## 先读什么

1. `docs/开发交付入口.md`：当前有效依据、必须开发项、明确不开发项和历史材料边界。
2. `docs/PRD-当前有效版.md`：当前业务规则，包含健康评分、统一健康分服务与智能问数约束。
3. `docs/engineering/AI_RAGFLOW_LANGGRAPH_SPEC.md`：RAGFlow、LangGraph、模型网关、接口、状态、审计、部署与验收要求。
4. `docs/superpowers/specs/2026-07-13-health-score-and-permission-prototype-sync-design.md`：原型同步实现约束。

## 最重要的开发门禁

智能问数首期固定使用 40 个内置指标和其允许维度；模型不得计算或猜测指标数值。具体清单以当前有效 PRD 和指标管理原型为准。

## 原型启动

在 `prototype/prototype` 目录中运行：

```powershell
node local-server-4209.js
```

访问：`http://127.0.0.1:4209/pages/intelligent-config.html`

如果 4209 已被占用，可修改 `local-server-4209.js` 中的端口后再启动。

## 原型检查

在交接包根目录运行：

```powershell
Get-ChildItem .\tests -Filter '*.test.js' | Sort-Object Name | ForEach-Object { node $_.FullName }
```

这些检查验证原型关键规则，不等于真实后端服务验收。正式开发仍需补充单元测试、接口测试、权限测试和端到端测试。

## 交付边界

- `prototype` 目录包含完整本地原型，其他业务页面用于理解既有业务上下文。
- 智能配置专项不修改其他同事已完成的业务流程；只在原型合并后按实际接口完成对接。
- 本包不包含真实 API Key、密码、供应商密钥或生产配置。
