# 数据模型

- 基线：候选版 v2.1
- 状态：等待 Stage 4 文档包评审

## 核心聚合

| 聚合 | 关键字段/关系 | 约束 |
|---|---|---|
| `User`、`Role`、`Permission`、`Session` | 用户、角色、菜单/操作权限、登录会话 | 不包含工厂或设备授权关系。 |
| `Organization`、`Equipment` | 组织树与设备主数据 | `equipment.code` 唯一；有待处理或维修中故障时不得停用设备。 |
| `FaultReport`、`WorkOrder`、`MaintenanceRecord` | 故障—工单—维修闭环 | 业务状态迁移由业务 API 控制；维修人员最终提交字段是业务事实。 |
| `HistoricalRepairCase` | 从已完成维修沉淀的结构化案例 | 仅 PostgreSQL 查询，不写入 RAGFlow 作为案例事实源。 |
| `KnowledgeDataset`、`KnowledgeDocument`、`KnowledgeCitation` | 知识文档业务元数据、RAGFlow 映射与引用 | 只有 `READY` 文档可检索；RAGFlow ID、对象存储文件 ID 和失败原因必须保留。 |
| `ModelProvider`、`ModelBinding`、`AgentConfig` | 模型能力、密钥引用、每 Agent 当前有效配置 | `AgentConfig.agent_id` 唯一；推理开启时绑定模型必须具备 `supports_reasoning=true`。 |
| `AgentThread`、`AgentRun`、`ToolCall`、`AgentConfirmation` | 会话、运行、工具审计、人工确认 | 线程绑定创建者；`AgentRun.config_snapshot` 不可变，只作审计，不作为版本管理。 |
| `HealthScoreSnapshot`、`MetricDefinition`、`MetricQueryResult` | 健康快照、固定指标、查询结果 | 快照追加式；指标目录只读；模型不能生成或写入指标数值。 |
| `FileObject`、`AuditEvent`、`IdempotencyKey`、`JobRun` | 附件、审计、重复写防护、异步任务 | 审计不得保存密钥、令牌、Cookie、原始思维链或敏感附件原文。 |

## Agent 配置与运行模型

```text
AgentConfig(agent_id, enabled, model_binding_id, knowledge_dataset_ids,
            streaming_enabled, suggestions_enabled, sources_enabled,
            context_turns, retrieval_limit, similarity_threshold,
            deep_thinking_enabled, deep_thinking_level, max_reply_tokens,
            updated_at, updated_by)

AgentThread(thread_id, agent_id, creator_user_id, business_context_json,
            checkpoint_ref, status, created_at)

AgentRun(run_id, thread_id, config_snapshot_json, state_json,
         model_binding_id, status, started_at, completed_at, error_code)
```

- 首次初始化只在某个 `agent_id` 没有记录时插入该 Agent 自己的默认值；不使用共享默认对象批量覆盖。
- `config_snapshot_json` 必须包含该轮实际使用的模型、流式、建议、引用、上下文和深度思考参数，支持审计与复现。
- `state_json` 只保存结构化工作状态、已确认字段、工具结果摘要、待补证据与安全状态；不保存模型原始思维链。

## 故障诊断补充关系

```text
FaultReport -> DiagnosisDraft -> AgentThread -> AgentRun
AgentRun -> ToolCall / KnowledgeCitation / AgentConfirmation
MaintenanceRecord -> HistoricalRepairCase
```

`DiagnosisDraft` 是可丢弃的 AI 草稿。只有用户点击“采纳 AI 建议并开始维修”才将允许预填的内容与只读对话摘要关联到维修记录；直接开始维修不保留 AI 摘要。结束维修页面显示的摘要放在“备件更换说明”之后，且包含故障现象、关键故障码/现场证据、验证结果、根因与建议，不包含操作过程流水账或思维链。
