# 缺陷记录

### DEF-STAGE7-001：正式前端未实现批准原型的全部 P0 页面

- 严重程度：Stage 7 验收阻断 / 实现偏离。
- 状态：已确认；回流 Stage 5 修复设计中。
- 发现时间：2026-07-30。
- 发现基线：`a334afd1b8cb4eeb139d78b7f5f1b5617bb2cd32`；关联验收候选 `89fbd2129169fb6ece42094b17907885637f3c48`。
- 现象：正式 React 前端仅有工作台、智能配置、故障上报和维修执行四个业务路由；工作台只呈现设备 ID 健康分查询。已批准原型包含完整 P0 信息架构和页面布局，包括 BI、工厂建模、设备台账及新增/编辑/详情、Agent 上报、维修记录、系统管理、全局 Agent 等。
- 根因：Stage 5 的“禁止复制或运行原型源码”边界被错误收缩为最小前端壳实现，未完成任务书要求的原型差异审查、页面矩阵覆盖和正式 UI 迁移。
- 影响：项目负责人无法依据当前界面进行已批准 P0 页面和交互的产品验收；受影响 Stage 7 验收项阻断。
- 处置：按 `CR-047` 和 `05-development/STAGE7_P0_FRONTEND_REMEDIATION_DESIGN.md` 回流 Stage 5，逐页以正式 React 组件实现已批准原型的视觉/交互，并接入真实 API、权限、加载、空态和错误状态；缺失后端契约不得以 mock 替代。
- 关闭条件：全部 P0 页面完成差异矩阵、任务书审核/集成、自动化与浏览器对照证据，并基于新的精确候选重新执行受影响的 Stage 6 和 Stage 7 验收。

### DEF-STAGE6-002：操作指引正常空检索未明确无可引用依据

- 严重程度：Stage 6 P1（知识引用契约）。
- 状态：已修复，待 DEV-002 复核。
- 发现时间：2026-07-29。
- 根因：`OperationGuidanceAgent.start()` 将成功但零引用的检索结果与有引用的成功路径一并返回 `QUESTIONING`，造成调用方无法区分“可继续追问”与“无可引用依据”。
- 修复：新增 `NO_EVIDENCE` 状态；正常空检索返回空 `evidence`、明确提示和人工兜底，不伪造引用。公开 API 规格及前端响应类型同步该状态与每条引用的业务文档/切片标识。
- 回归：Agent 单元和 API 回归断言空检索返回 `NO_EVIDENCE`、空引用和固定提示；有引用成功与不可用降级路径保持原有契约。
- Gate 边界：此修复不构成 Stage 6 总体通过、Merge 或 Stage 7 授权。

### DEF-STAGE6-001：备份恢复性能与受控负载干扰证据未满足门槛

- 严重程度：Stage 6 阻断（测试/交付证据）；当前不是已确认的生产代码缺陷。
- 状态：已解决，待 DEV-002 复核。
- 发现时间：2026-07-28。
- 证据：在隔离 Compose 项目中，备份后向随机恢复项目执行恢复脚本的功能性命令退出码为 0，但包含附件压测对象的恢复耗时约 194.7 秒，超过已约定的 180 秒；同时尚未完成恢复过程中维持 10 个只读请求、并验证 P95 不超过 2 秒的组合试验。
- 边界：该结果来自一次包含大量测试附件对象的隔离环境，不能外推为生产容量结论，也不得删改结果以规避门槛。
- 处置与复验：建立新的隔离 Compose 项目，仅由 API 写入 1 个受控附件对象；备份耗时 3.578 秒，随机恢复耗时 10.584 秒。恢复期间执行 60 秒、10 并发认证只读负载，12,443 次请求零错误、P95 76.64 ms。两个门槛均通过，详见 `TEST_REPORT.md` 与 `06-testing/performance/results-backup-restore-readonly.json`。
- 结论限制：15,525 个小对象恢复约 194.7 秒仍是容量边界信息，不得外推为生产容量结论；Stage 6 Gate 仍由 DEV-002 单独决定。

### DEF-STAGE6-003：TASK-012 新集成基线的真实知识生命周期未在时限内完成

- 严重程度：Stage 6 P1 测试阻断。
- 状态：Open / 根因调查中；回流 Stage 5 的范围尚未确认。
- 发现基线：`6fbb9e5be6267851482fda425c704acdada92c50`。
- 证据：Windows 隔离环境中 `tests/integration/test_task005_live_stack.py` 在专用数据库初始化和 MinIO bucket 初始化后仍在 180 秒执行上限内未产生终态结果。不得将此前候选或容器健康结果替代为本基线的生命周期通过证据。
- 当前已知事实：Compose、迁移、PostgreSQL、Redis、MinIO、ClamAV、API、Worker、Validator、Nginx 和 RAGFlow 认证探针均已通过；超时边界在文档上传后等待知识文档 `READY`、检索或清理链路中的哪一段尚未由带时间戳的分段日志确认。
- 关闭条件：在隔离环境追加不含秘密的分段时序证据，定位唯一阻塞组件；如需代码、Worker、RAGFlow、基础设施或运行时配置修复，按 Stage 5 任务书建立修复任务、测试、审核和集成，再以新的精确集成 SHA 重跑。

### DEF-STAGE6-004：浏览器 E2E 的临时本地 HTTPS 信任链未建立

- 严重程度：Stage 6 P1 测试阻断。
- 状态：Open / 测试环境配置待修复。
- 发现基线：`6fbb9e5be6267851482fda425c704acdada92c50`。
- 证据：隔离环境浏览器拒绝已清理的临时证书，返回 `ERR_CERT_AUTHORITY_INVALID`；命令行 HTTPS 200 与 MIME 结果不能替代浏览器 E2E。
- 关闭条件：使用仅隔离测试环境的临时信任根或受浏览器信任的本地证书，完成并归档未认证跳转、登录、Workbench、智能配置、故障上报、权限受限写操作和退出跳转；不得使用生产证书、生产域名或公网暴露。

### DEF-STAGE6-005：性能、备份恢复与恢复期只读负载未在当前 SUT 重跑

- 严重程度：Stage 6 P1 测试阻断。
- 状态：Open / 证据缺失。
- 发现基线：`6fbb9e5be6267851482fda425c704acdada92c50`。
- 缺口：认证、附件、真实 RAGFlow 成功、`UNAVAILABLE` 降级的 1/2/5/10 并发结果，以及受控附件备份、随机隔离恢复和恢复期间 10 并发只读负载均未在本基线完成。
- 关闭条件：每项结果均绑定本次 SUT、harness、evidence subject、隔离环境、夹具与 UTC 时间，并满足测试计划阈值；旧候选的 JSON 只能保留历史追溯。

### DEF-STAGE6-006：后端生产容器未声明非 root 运行用户

- 严重程度：Stage 6 P2 静态扫描待核验项；尚未确认代码缺陷或 Stage 5 回流。
- 状态：Open / 等待容器 UID 运行证据。
- 发现基线：`6fbb9e5be6267851482fda425c704acdada92c50`。
- 根因调查：Semgrep 未识别 Docker 多阶段构建的最终 `production` stage。该 stage 继承 `runtime` 后创建 `appuser` 并声明 `USER appuser`；Compose 未指定 build target，按 Docker 语义会构建最终 stage。因此“当前 Dockerfile 未设置最终 USER”的结论不成立。
- 关闭条件：在 Windows 隔离 Compose 中对 `api` 和 `worker` 执行不含敏感信息的 `id -u`，确认均非 `0`；若实际为 root，才以最小 Dockerfile/挂载权限修复回流 Stage 5。

### DEF-STAGE6-007：性能 harness 的不校验证书分支缺少受控边界验证

- 严重程度：Stage 6 P2 安全/测试治理问题。
- 状态：Open / 待边界复核。
- 发现基线：`6fbb9e5be6267851482fda425c704acdada92c50`。
- 证据：Semgrep `python.lang.security.unverified-ssl-context.unverified-ssl-context` 命中 `06-testing/performance/stage6_performance.py` 的 `--insecure-tls` 分支。该开关仅应允许显式隔离自签名测试，绝不可成为默认或生产路径。
- 关闭条件：增加失败用例证明无显式隔离标识时拒绝不校验证书；记录临时证书环境边界。若修改测试代码，按 Stage 5 修复范围处理。

### TASK-002 合并后治理台账修正（2026-07-17）

- 严重程度：交付治理 Important；不构成新的 `codebase/` 实现缺陷。
- 状态：已由 PR #25 Merge Commit `028da42eb9ab4b55ef981ac462e09993a31e8813` 集成；TASK-002 下游前置已解除。
- 发现：R10 指出任务摘要过期、TASK-005/006 依赖状态错误，以及 PR #20 缺少 DEV-001 手动合并记录。
- 处理：以 PR #20 的实际 Merge Commit `904886f48061e27c775f6ee2f8ddae99f5571ead`、执行人 DEV-001（`ll979053897-arch`）和已归档技术证据统一更新任务书、评审、自测、检查点与交接台账。
- 残余风险：审计脱敏的字段语义规则关闭已知别名漏洞，不宣称能识别攻击者以任意未知字段名承载的秘密；该风险不在本纯治理 PR 中扩大实现范围。

### DEF-001: Legacy metric static test conflicted with current requirement

- 严重程度：重大基线不一致
- 状态：候选验证已解决；生产行为仍未验证
- 证据：导入的 `06-testing/tests/intelligent-config-metric-inline.test.js`
- 当前预期行为：固定指标目录为只读。
- 处理：测试现在检查可见的只读指标弹窗，完整静态套件通过；生产指标 API 尚未实现。

### DEF-002: Prototype runbook paths were stale before migration

- 严重程度：中等文档缺陷
- 状态：候选迁移修复
- 证据：原 README 和运行说明引用了缺失文件/根目录服务器路径。
- 必要动作：更新根入口并验证迁移后的服务器路径。

### DEF-003：后端健康检查基线存在重复定义冲突

- 严重程度：阻断后端测试收集
- 状态：已解决 / TASK-001 已验证
- 发现时间：2026-07-15
- 复现命令：`python -m pytest codebase/backend/tests/test_health.py -q`
- 实际结果：导入 `codebase/backend/app/main.py` 时调用 `Settings()`，因缺少 `postgres_dsn` 和 `redis_url` 触发 `TypeError`，测试在收集阶段中止。
- 初步证据：`codebase/backend/app/main.py` 和 `codebase/backend/app/core/config.py` 均包含重复定义；该内容在本次目录迁移前已存在，CR-032 只执行 Git 路径重命名，没有修改业务代码。
- 处理：删除 `main.py` 中第二套无参数应用工厂及 `config.py` 中重复字段；保留四条已批准的应用、PostgreSQL、Redis 缺失与完整配置健康检查契约。Python 3.13.14 下结果为 `4 passed, 1 warning`。

### DEF-004：Compose 基线存在重复服务和网络定义

- 严重程度：阻断 Compose 配置验证
- 状态：已解决 / TASK-001 已验证
- 发现时间：2026-07-15
- 静态证据：`codebase/infra/docker-compose.yml` 重复定义 `postgres`、`redis` 和顶层 `networks`，且网络结构互相矛盾。
- 处理：删除重复 `postgres`、`redis` 与顶层 `networks` 定义，保留唯一 `platform` 内部网络。`docker compose ... config --quiet` 通过；独立 `equipment-task1` 项目中 PostgreSQL、Redis 均为 `healthy`，API 实际健康检查返回 200。

## TASK-002 / CR-036 缺陷复核（2026-07-16）

- DEV-002 对 PR #15 提出的 Standards 与 Spec 阻断统一由 CR-036 管理，不另行拆成重复 DEF。
- R6/R7 已修复公开契约、失败审计、完整设备字段、组织层级、固定角色/用户权限、附件引用脱敏和迁移问题。
- DEV-001 最终独立复审为 Critical 0、Important 0；未发现需要保持 Open 的新缺陷。
- 唯一非阻断提醒：Alembic `0002` 接近规模上限，后续数据库变化必须新增 revision；第三方 TestClient/httpx 弃用警告留待依赖维护任务处理。
- TASK-002 仍待 DEV-002 复审；若正式审核发现新阻断项，应在本台账新增 DEF 或重新打开 CR-036，不得改写本次历史结果。

## TASK-002 / CR-036 R8 缺陷复核（2026-07-17）

- DEV-002 最新 4 个 Important 均属于既有 CR-036 范围，不重复创建 DEF；代码候选为 `73030f83638b3b063db483029591720bf65aac21`。
- 固定目录、用户范围、脱敏变体和未知异常失败审计已由新增回归测试及真实 PostgreSQL 验证关闭。
- DEV-001 三轮复核为 Critical 0、Important 0；未发现新的 Open 产品/代码缺陷。
- 历史 `merge(task-002)` 类型与不可变 `0001` 职责说明为非阻断治理处置，详见 `CODE_REVIEW.md`；不得通过 force-push 或改写已发布 migration 处理。
- 既有 TestClient/httpx 弃用警告仍为非阻断依赖维护项；本次未升级或新增生产依赖。
- TASK-002 仍待 DEV-002 正式复审和后继 PR 集成，不得据本内部结论解锁依赖。

## TASK-002 / CR-036 R9 复审发现（2026-07-17）

- DEV-002 新发现为 CR-036 的剩余 Important，不另建重复 DEF：密码确认驼峰/中缀变体和附件未知正文别名可绕过失败审计脱敏。
- 根因和修复见 `CODE_REVIEW.md` R9；代码候选为 `ac6947a642f00ba48aebcb80064f87fcc4c01ea8`，新增数据库持久化断言。
- 当前状态：独立 `test` 镜像已补齐 pytest/httpx 并完成 PostgreSQL 17 `5 passed`；仍等待 DEV-002 复审，不得据内部证据提前关闭外部审核门禁。

## TASK-002 / CR-036 R10 复审发现（2026-07-17）

- DEV-002 补充发现属于既有 CR-036 的同一审计脱敏 Important，不新增重复 DEF：附件上下文标量、标量列表及紧凑密码键会绕过 R9 的字典白名单规则。
- 根因和修复见 `CODE_REVIEW.md` R10；代码候选 `b4d451009d1deb9dbe3286f5bff4db9414ef4aee`，新增直接脱敏和数据库持久化两层回归。
- 当前状态：DEV-001 内部复核未见 Critical/Important；真实 PostgreSQL 17、Compose 与 `/healthz` 已复测。外部审核仍未通过，TASK-002 不得视为完成或解除依赖。

## TASK-002 / CR-036 R11 复审发现（2026-07-17）

- DEV-002 的 R10 Important 属于既有 CR-036，不新增重复 DEF：附件/文件语义仅识别键首，Cookie 和紧凑密码规则不完整，导致失败审计可含明文。
- 根因和修复见 `CODE_REVIEW.md` R11；代码候选 `ea4338bad15f16048226a329801d3144b367909e`，新增直接和落库反例测试。
- 残余风险：无敏感语义的未知字段默认脱敏未实施，须作为独立安全强化项评估；不得把 R11 结论表述为可识别任意秘密。
- 当前状态：DEV-001 内部复核未见 Critical/Important；真实 PostgreSQL 17、Compose 与 `/healthz` 已复测。外部审核仍未通过，TASK-002 不得视为完成或解除依赖。
-
## TASK-012 consolidated defect inventory (DEV-001 review, 2026-07-31)

Review record only. No business-code fix is included in this governance branch. DEV-002 must address these findings in the single TASK-012 development PR and submit a new exact HEAD.

### Previously reported findings

- DEF-TASK012-001 (P1): `/api/auth/me` failure leaves the protected shell mounted; permission loading is not fail-closed (`codebase/frontend/src/App.tsx`).
- DEF-TASK012-002 (P1): Pages check one permission while their API calls require combinations, causing predictable 403 responses (`App.tsx`, `PortalPages.tsx`, `api.ts`).
- DEF-TASK012-003 (P1): Logout omits the required `Idempotency-Key` (`codebase/frontend/src/api.ts`).
- DEF-TASK012-004 (P1): Operation guidance trusts client `dataset_ids`, while the normal page does not provide required dataset context.
- DEF-TASK012-005 (P1): Fault diagnosis does not validate enabled Agent configuration and model binding.
- DEF-TASK012-006 (P1): Diagnosis can emit a fixed root cause/recommendation without real case or knowledge evidence.
- DEF-TASK012-007 (P1): Diagnosis form cannot submit alarm-code and second-evidence fields needed for `DIAGNOSIS_READY`.
- DEF-TASK012-008 (P1): Diagnosis rejected promises are not consistently handled, leaving stale UI and unhandled errors.
- DEF-TASK012-009 (P1): Diagnosis questions remain a fixed template instead of using the dynamic contract.
- DEF-TASK012-010 (P1): Repair execution context is client-controlled instead of bound to formal work order, fault and equipment facts.
- DEF-TASK012-011 (P1): Maintenance records show fixed `NOT_LINKED`, and invalid filter values are not surfaced as 422.
- DEF-TASK012-012 (P1): Manual fault submission and AI draft generation remain available while attachment scanning is pending.
- DEF-TASK012-013 (P1): AI confirmation submits the old preview and ignores edits made after preview generation.
- DEF-TASK012-014 (P1): AI reporting always sends `duration_minutes: 0` instead of collecting actual duration.
- DEF-TASK012-015 (P1): Agent reporting starts Runtime but does not consume thread, SSE, result state or missing-field flow.

### Additional findings from the complete candidate

- DEF-TASK012-016 (P1): BI `period` changes trend length only; summary, efficiency and organization ranking still use all history (`PortalPages.tsx`, `api.ts`).
- DEF-TASK012-017 (P1): Equipment edit sends `manufactured_at: null`, `commissioned_at: null` and `image_refs: []`, silently clearing existing fields.
- DEF-TASK012-018 (P1): Equipment page is gated by `equipment:read`, but create/edit require `equipment:write`; read-only users see unusable actions.
- DEF-TASK012-019 (P1): Factory modeling is gated by `organization:read`, but create/edit/enable/delete require `organization:write` and are not disabled.
- DEF-TASK012-020 (P1): Maintenance list requires `maintenance:view`, while detail requires `maintenance:detail`; the detail link predictably fails for ordinary viewers.
- DEF-TASK012-021 (P1): Repair execution is gated by `fault:repair`, while loading work orders needs `maintenance:view` and submitting results needs `fault:close`.
- DEF-TASK012-022 (P1): Fault report page is gated by `fault:create`, but AI pre-diagnosis needs `intelligence:agent`; the AI button is not permission-aware.
- DEF-TASK012-023 (P1): Agent report page is gated by `intelligence:agent`, but final submission also requires `fault:create`.
- DEF-TASK012-024 (P1): System management is gated by `identity:read`, while user and role writes require `identity:write`.
- DEF-TASK012-025 (P1): Global Agent drawer is visible to every authenticated user although Runtime endpoints require `intelligence:agent`.
- DEF-TASK012-026 (P1): Intelligent configuration route checks `intelligence:model`, but `/api/agent-configs` requires `intelligence:agent`.
- DEF-TASK012-027 (P1): Root workbench route has no `workbench:view` gate and exposes requests that fail for users without it.
- DEF-TASK012-028 (P1): Equipment edit has no date or image controls, compounding the field-clearing payload defect.
- DEF-TASK012-029 (P1): BI page provides list-only output and omits the approved chart-switching interaction.
- DEF-TASK012-030 (P1): Workbench health score requires manually typing an equipment ID instead of selecting from the formal equipment list.
- DEF-TASK012-031 (P2): Successful writes often show only “refresh to confirm” and do not reconcile local data, leaving stale UI and repeat-submit risk.
- DEF-TASK012-032 (P2): Organization, equipment, user and role writes lack consistent post-write refresh or state reconciliation.
- DEF-TASK012-033 (P1): Create/submit controls lack consistent in-flight guards; repeated clicks can create duplicate Runtime runs and records.
- DEF-TASK012-034 (P1): Root pytest has two real failures because `06-testing/performance/*.py` opens JSON through a working-directory-relative path.
- DEF-TASK012-035 (P1): PR #75 claims the backend suite passed, but the reproducible root run is `339 passed, 13 skipped, 2 failed, 2 warnings`; evidence boundary is inaccurate.
- DEF-TASK012-036 (P1): Knowledge retry tests do not click/assert the dual-permission request; the path is unverified (`PortalPages.test.tsx`).
- DEF-TASK012-037 (P1): The existing retry test blockage remains unresolved while candidate evidence reports green.
- DEF-TASK012-038 (P1): Equipment add/edit is gated only by `equipment:read`, but the form also loads `/api/organizations` and `/api/users`; users with equipment permission but without organization/identity read receive a blank/error form before they can save. Evidence: `App.tsx`, `PortalPages.tsx`, P0 API availability matrix.
- DEF-TASK012-039 (P1): After an AI preview is generated, the ordinary “提交故障” action remains enabled; a user can create a manual fault and then confirm the preview, producing two contradictory records from one report flow. Evidence: `FaultReportPage.tsx` preview branch and submit button.
- DEF-TASK012-040 (P1): `readRunEvents()` awaits `response.text()` and parses only after the SSE response closes; Runtime status is not consumed incrementally, so the required live `run_started`/tool/status experience is not delivered. Evidence: `codebase/frontend/src/api.ts`, `App.tsx`, `RepairExecutionPage.tsx`, Runtime SSE contract.

### Third-pass findings against PR #75 HEAD 989e23481f071a46ee164c9595434d703d8a3a1f

- DEF-TASK012-041 (P1): `POST /api/agent/operation-guidance` performs external retrieval and writes a success audit but has no `Idempotency-Key` contract or replay storage; browser retry or double-click can repeat retrieval/audit with no stable response. Evidence: `codebase/backend/app/modules/agents/router.py`, `codebase/frontend/src/api.ts`, TASK-010 protected-write convention.
- DEF-TASK012-042 (P1): Global Agent creation is a non-atomic thread-create then message-create sequence, each with a new idempotency key; message failure or retry leaves orphan threads, and the submit control has no in-flight disabled state. Evidence: `codebase/frontend/src/api.ts`, `codebase/frontend/src/App.tsx`.
- DEF-TASK012-043 (P1): Repair execution enables manual fault-id fallback whenever assigned-order loading is `null`, including request failure; this permits bypassing formal work-order context during 403/network errors instead of only when an authoritative empty list is returned. Evidence: `codebase/frontend/src/RepairExecutionPage.tsx`.
- DEF-TASK012-044 (P1): Page-level permission gates require write permissions for factory modeling, system management, intelligent configuration and repair execution, blocking read-only users from approved read views instead of rendering read data with write controls disabled. Evidence: `codebase/frontend/src/App.tsx`, page API contracts and P0 permission matrix.
- DEF-TASK012-045 (P2): SSE parser accepts only one single-line `data:` field and silently drops `event:error`, multi-line data, or blocks separated by CRLF; the live Runtime contract is not robustly consumed despite the incremental reader. Evidence: `codebase/frontend/src/api.ts`.
- DEF-TASK012-046 (P1): Required runtime integration evidence is still absent on HEAD 989e234: Docker Compose/container health, PostgreSQL, RAGFlow, ClamAV/MinIO, HTTPS and browser E2E were not rerun; frontend mocks/static checks cannot establish production readiness.
- DEF-TASK012-047 (P1): Exact-HEAD live validation now reaches authenticated RAGFlow and the production `operation-guidance` route, but the live lifecycle returns `UNAVAILABLE` instead of the required `QUESTIONING` because the validation fixture creates a local knowledge dataset without creating/binding an `operation_guidance` Agent configuration. The client-supplied `dataset_ids` are correctly ignored by the server, so the test cannot prove the production route until the approved Agent config is provisioned. Evidence: `codebase/backend/tests/integration/test_task005_live_stack.py`, `codebase/backend/app/modules/agents/router.py`.

### DEF-TASK012-046 status update (2026-08-03)

- Exact HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8` completed the disposable live-stack run: PostgreSQL, Redis, MinIO, ClamAV, API, Worker, Validator and Nginx started; authenticated RAGFlow retrieval, temporary Agent binding, operation-guidance success/degradation, attachment scanning and cleanup passed (`2 passed, 5 warnings`).
- Remaining scope is limited to application HTTPS ingress and authenticated browser E2E on this exact candidate. Existing RAGFlow HTTPS or unauthenticated/container-local checks do not satisfy this requirement.
- DEF-TASK012-046 remains open until those two checks are executed and recorded.

### DEF-TASK012-047 status update (2026-08-03)

- Closed on exact HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8`. The live fixture now creates and binds a temporary `operation_guidance` Agent configuration to the disposable dataset, then removes it during cleanup. The authenticated production route and unavailable degradation path were exercised; client-supplied `dataset_ids` remained ignored.

### Historical gate (superseded by final review and integration)

DEF-TASK012-001..045 remain subject to final exact-HEAD review; DEF-TASK012-047 is closed. PR #75 must remain unmerged and Stage 6/7/8 locked while DEF-TASK012-046 remains open. DEV-001 must execute application HTTPS and authenticated browser E2E, then perform the final whole-candidate review and integration check.
- DEF-TASK012-046 (P1, closed 2026-08-03): Exact HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8` now has reproducible Compose, PostgreSQL, RAGFlow, ClamAV/MinIO, application HTTPS, static MIME and authenticated browser E2E evidence. The browser run verified login, workbench load, `/intelligent-config`, `/fault-report`, and logout redirect to `/login`.

### Final resolution (2026-08-03)

- DEV-001 final review `4840904555` approved exact HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8`; this closes DEF-TASK012-001 through DEF-TASK012-045 after the consolidated remediation and final regression review.
- DEF-TASK012-046 and DEF-TASK012-047 are closed by the recorded isolated live-stack, HTTPS and authenticated-browser evidence on the same HEAD.
- PR #75 was merged as `9c8a787ba2ba51f4362bf6186b1c7d54cbe3e15c`; PR #76 merged the post-merge governance record as `477cb16e8a1e68d9d9325705d9d7db685fba9d86`.
- No TASK-012 defect remains open. This closes the Stage 5 remediation task only; Stage 6 independent testing must be rerun against the new integration baseline before Stage 7 can be reconsidered.
