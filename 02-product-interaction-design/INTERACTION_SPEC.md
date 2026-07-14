# Interaction Specification

- Baseline: Candidate v1.0
- Status: Awaiting Stage 2 approval

## Shared rules

- Navigation is permission-driven; unauthorized routes show a forbidden state.
- Save operations show validating, saving, success and failure states.
- Empty states explain why there is no data and offer only allowed next actions.
- Backend errors never become invented values; retry and fallback are explicit.
- Destructive actions require permission and preserve audit evidence.

## Agent states

| State | Entry | Exit |
|---|---|---|
| Closed | page loaded with Agent permission | click floating entry |
| Open | click entry | close or switch page |
| Collecting | AI fault tab missing required data | required data complete or permission denied |
| Preview | required data complete | confirm, continue dialogue, cancel |
| Querying | valid metric/dimension request | result, empty, error |
| Guidance | current page context available | answer, clarify, permission explanation |

History is independent per tab; clear only affects current tab; closing preserves all history.

## Fault status

`AI_DRAFT → PENDING_ACCEPT → IN_REPAIR → PROCESSED`. No reopen operation exists in this release.

## Exception flows

- Missing required field: identify field and continue collection.
- Multiple equipment: request exactly one.
- Attachment failure: retain text, expose retry.
- Agent/RAGFlow outage: preserve manual flow and explain service unavailability.
- Permission denial: explain reason, log event, do not simulate success.
