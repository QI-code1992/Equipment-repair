# 交互规格

- 基线：已批准 v1.0
- 状态：Stage 2 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-003

## 通用规则

- Navigation is permission-driven; unauthorized routes show a forbidden state.
- Save operations show validating, saving, success and failure states.
- Empty states explain why there is no data and offer only allowed next actions.
- Backend errors never become invented values; retry and fallback are explicit.
- Destructive actions require permission and preserve audit evidence.

## Agent 状态

| 状态 | 进入条件 | 退出条件 |
|---|---|---|
| Closed | page loaded with Agent permission | click floating entry |
| Open | click entry | close or switch page |
| Collecting | AI fault tab missing required data | required data complete or permission denied |
| Preview | required data complete | confirm, continue dialogue, cancel |
| Querying | valid metric/dimension request | result, empty, error |
| Guidance | current page context available | answer, clarify, permission explanation |

History is independent per tab; clear only affects current tab; closing preserves all history.

## 故障状态

`AI_DRAFT → PENDING_ACCEPT → IN_REPAIR → PROCESSED`. No reopen operation exists in this release.

## 异常流程

- Missing required field: identify field and continue collection.
- Multiple equipment: request exactly one.
- Attachment failure: retain text, expose retry.
- Agent/RAGFlow outage: preserve manual flow and explain service unavailability.
- Permission denial: explain reason, log event, do not simulate success.

## 开始维修：故障诊断 Agent

1. 用户点击开始维修，左侧维修接单信息与右侧 Agent 独立滚动，弹窗页头与页脚固定。
2. 右侧先以约 3 秒的分阶段动态效果展示“理解故障—检索同类维修—检索知识库—形成首问”；该阶段不可输入。
3. 加载完成后，Agent 以单条对话消息提出当前证据缺口；历史案例和知识库引用只挂在首条检索完成消息下，可折叠展开。
4. Agent 根据设备/故障计划动态追问。选择“有报警码”后，输入区切换为报警码必填模式；必须填写具体报码或明确选择“暂无报码/未读取”。
5. 缺失或否定信息只作为缺失证据，Agent 继续索取测量值、日志、图片或复现条件。证据不足时不显示采纳按钮。
6. 满足诊断条件后，Agent 以可折叠对话详情展示根因、检查清单、维修方案和备件/安全建议；方案只读，不强制选择。
7. 底部始终保留直接开始维修。仅采纳 AI 建议时，才预填结束维修字段和生成只读 AI 对话摘要；直接开始维修不保存 AI 临时数据。
8. 结束维修页和故障详情页仅对已采纳 AI 建议的工单显示摘要，摘要包含故障现象与关键诊断证据，不显示原始消息和思维过程。
