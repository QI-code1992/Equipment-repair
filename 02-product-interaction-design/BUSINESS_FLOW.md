# Business Flow

- Baseline: Candidate v1.0
- Status: Awaiting Stage 2 approval

## Fault-to-knowledge loop

`发现异常 → 选择一台设备 → 人工表单或 AI 对话收集 → 校验必填项 → 生成/提交故障单 → 待接单 → 维修中 → 已处理 → 维修记录 → 历史案例/待审核知识 → 健康分服务重算`。

## AI diagnosis loop

`故障正式提交 → LangGraph 读取上下文 → 权限检查 → RAGFlow 检索带引用片段 → 读取业务事实 → 诊断与维修建议 → 低置信度/安全风险人工复核 → 草稿工单 → 管理员确认派发`。

## Exclusions

数据导入不在当前菜单、权限、接口或开发流程中；其历史页面只存在于原始 Git 快照。
