# 原型交互覆盖

| 范围 | 源码是否覆盖 | Stage 3 审批前必须验证 |
|---|---|---|
| Navigation/sidebar | yes | all authorized/forbidden combinations |
| Agent open/close/tab history | yes | reload, clear-current-tab, cross-page persistence |
| AI fault collection/preview | partial | required/optional fields, one-equipment guard, permission denial |
| Intelligent query | partial | fixed metric catalog, disallowed metric/dimension, API failure |
| Health displays | partial | same service result on five surfaces and explicit failure |
| Equipment forms | yes visual | duplicate, future date, deactivation guard, save failure |
| Work-order/repair | yes visual | state transitions, closure validation, human confirmation |
| Start-repair diagnosis Agent | yes | loading, stream, dynamic question plan, alarm-code required, evidence-insufficient, unavailable, adopted/direct-start and end-summary boundary |
| Empty/loading/error/disabled | partial | capture evidence for every P0 page |
