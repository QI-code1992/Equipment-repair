# 交互规格

- 基线：候选版 v1.0
- 状态：等待 Stage 2 审批

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
