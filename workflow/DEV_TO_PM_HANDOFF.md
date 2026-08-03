# 开发到产品交接

## TASK-012 P1 权限修复复审交接（2026-07-31）

- PR：#75；最新精确 HEAD：`77a54a1587544374ed876e902bc132d58cf8ed9b`；目标 `codex/stage-05-integration`；PR 继续保持 Ready，未申请 Merge 授权。
- 根因：仅 `intelligence:audit` 用户可见知识重试按钮，但后端写入接口要求 `intelligence:knowledge`，点击必然 403。
- 修复：`IntelligentAuditPage` 接收当前会话权限；无知识写权限时禁用“重新同步”并显示明确提示；审计+知识双权限仍可执行重试。
- 验证：修复前审计-only 回归失败；修复后定向 17 passed，前端全量 55 passed，生产构建、15 项 Node 静态回归和 diff-check 通过。
- 下一步：请 DEV-001 基于新精确 HEAD 重新进行 TASK-012 完整整体审核；不申请合并授权、不合并，Stage 6/7/8 继续锁定。

## TASK-012 整体开发候选交接（2026-07-31）

- 开发分支：`codex/task-012-p0-frontend-remediation`；最新精确提交：`08e1576`；PR 继续保持 Draft。
- 已完成：API-002—007 正式读接口、全部除 Data import 外的 P0 页面、Bearer/权限/状态、附件安全引用、Agent 线程历史/详情/resume/SSE、前后端回归和测试治理材料。
- 本地证据：前端 `53 passed`、生产构建通过；后端 `328 passed, 13 skipped, 2 warnings`；compileall、15 项 Node 静态回归、JSON、diff-check 通过。
- 未完成证据：DEV-001 对完整候选的一次性审核；Windows Docker Desktop/WSL2 live-stack；真实 ClamAV/MinIO/RAGFlow、HTTPS、浏览器逐页 E2E、重启/备份恢复和最终 Stage 6/7 门禁。
- 请求动作：由 DEV-001 基于该精确 HEAD 进行整体审核；在审核、集成检查和项目负责人授权前，不转 Ready、不申请 Merge、不合并、不进入 Stage 6/7/8。

## TASK-012-API-001 合并后治理收尾候选（2026-07-30）

- 集成：PR #71 的获批 HEAD `c1273fd01e5ec91b2de3af59aab371844d228cd6` 已由 DEV-002 在项目负责人授权后以 Merge Commit `274673b72d5201986ffee77b038f516022cd174d` 合入 `codex/stage-05-integration`；双亲和结果树已核验。
- 合并后证据：Python 3.13 定向 `3 passed, 2 warnings`、后端全量 `319 passed, 13 skipped, 2 warnings`、compileall、Compose config、workflow JSON 与 diff-check 均通过。
- 依赖结论：API-001 已集成；API-002—007 尚未关闭，TASK-012 前端和 Stage 6/7/8 继续锁定。本候选只请求项目负责人确认治理记录，不请求启动任何下游任务。

## Stage 7 P0 正式前端回流规划已集成（2026-07-30）

- 背景：验收发现正式 React 前端只有四个业务路由，且工作台只提供设备 ID 健康分查询，不能覆盖批准原型的全部 P0 页面。`DEF-STAGE7-001` 与 `CR-047` 已登记。
- 已集成范围：PR #69 的获批 HEAD `9b89adb9d32dc067a9ea9b1cb4aa8c5f9c6d1fd8` 已由 DEV-001 以 Merge Commit `be9de719c7a1a14f7bf98aab792a2b73bf0278d5` 合入 `codex/stage-05-integration`。该 PR 不含 `codebase/`、测试代码、迁移、基础设施、部署或运行配置修改。
- 关键结论：现有正式 API 可覆盖登录、组织/设备 CRUD、部分工作台与 BI 指标、故障/诊断、Agent Runtime、附件、相似案例、维修结果、用户/角色/权限和模型/Agent/知识配置。`API-GAP-001`—`007` 仍缺正式读取或聚合契约，明确阻断其对应原型功能，未使用 mock 或静态样例。
- 后续动作：TASK-012 仍不能创建代码 PR。先逐项取得 `TASK-012-API-001`—`007` 的项目负责人公开 API 范围确认，并完成各自的开发 PR、审核和集成；Stage 6 重测、Stage 7 恢复验收和 Stage 8 均不在本次合入授权范围内。

## Stage 6 → Stage 7 验收交接（2026-07-29）

## TASK-012-API-001 开发候选复审交接（2026-07-30）

- PR #71 分支 `codex/task-012-api-001-workbench` 已补齐 API-001 的边界回归，最新测试证据提交为 `44992b5b34f6a2c77378383a363bfb2a3f86fd25`。
- 验证：定向 `3 passed, 2 warnings`；后端全量 `319 passed, 13 skipped, 2 warnings`；Python 3.13 compileall、Compose config 和 diff-check 通过。
- 当前门禁：等待 DEV-002 对 PR #71 最新精确 HEAD 正式审核；未申请 Merge 授权、未合并、未解锁 TASK-012 前端或 Stage 6/7/8。新 HEAD 必须重新绑定审核结论。

## Stage 6 → Stage 7 验收交接（2026-07-29）

- Gate：项目负责人已批准 `89fbd2129169fb6ece42094b17907885637f3c48` 进入 Stage 7 独立产品验收。
- 前置结论：Stage 6 独立测试总体结论已签发，绑定 PR #63 approved HEAD `46bd5b7f6579016d9ce9bb3f0d1d7226ccd503d1` 与 Merge Commit `a5e4f6abec98f0df4c04f18a0cbf849e423624be`；后续治理合并未改变业务或运行时内容。
- 验收边界：基于 PRD、SPEC、AC、批准原型和当前精确候选逐项独立判定；既有 React Router 风险处置与 Stage 3 原型 P2 发现必须如实纳入验收报告。
- 禁止事项：不得把本交接解释为验收通过、Stage 8 发布、生产操作或 `main` 合并授权。

## Stage 6 PR #63 合并后治理同步（2026-07-29）

- 合并事实：DEV-002 已按单独授权以手动 Merge Commit `a5e4f6abec98f0df4c04f18a0cbf849e423624be` 将 PR #63 合入 `codex/stage-05-integration`；双亲为目标分支基线 `d4fa5eefaa9ebfb9ed768f199ca5df2b0e2d397b` 与获批候选 `46bd5b7f6579016d9ce9bb3f0d1d7226ccd503d1`。合并结果树与第二父候选一致，PR 状态和目标分支指针已核验。
- 合并后验证：前端 `27 passed`、生产构建、Python 3.13 性能单元 `13 passed`、15 项 Node 静态回归、证据 JSON/SARIF 解析，以及相对两个父提交的差异检查均通过。
- 未重跑边界：本次合并未改变已归档运行态证据，因此未重跑 Docker live-stack 或完整后端 pytest；该事实不将其替换为新的运行态结论。
- 残余风险与回滚：既有 React Router 风险处置和 Stage 3 原型 P2 仍未关闭。若发现回归，先在隔离环境验证 `git revert -m 1 a5e4f6abec98f0df4c04f18a0cbf849e423624be`，经授权后再执行；不得删除卷或覆盖数据。
- 当前门禁与下一动作：Stage 6 独立测试总体结论已签发，并精确绑定获批 PR #63 HEAD `46bd5b7f6579016d9ce9bb3f0d1d7226ccd503d1` 与 Merge Commit `a5e4f6abec98f0df4c04f18a0cbf849e423624be`。治理 PR #64 已由 DEV-002 按授权合入 `1b43565d750eea8b85e5e66fab6b9f9ae1fdccaa`；本记录不构成 Stage 7 验收或生产发布授权。Stage 7 仍锁定，必须由项目负责人另行批准启动。

## Stage 6 PR #61 合并后验证与治理交接（2026-07-28）

- 合并事实：DEV-002 已按授权以手动 Merge Commit `144ad1ac5802dcbe53a55a426f46ce9bef8eba0f` 合入 PR #61；双亲为 `e32478e20c0f27558356d4f0e7d5a6d4c8eba477` 与获授权 HEAD `b73311cfd3beebe048c5ef64320886ccdea363e0`。
- DEV-001 合并后验证：在该 Merge Commit 的独立工作树中，前端 `26 passed`、生产构建、15 项静态回归、Nginx 契约和合并差异检查均通过；完整 readiness 验证真实 HTTPS MIME、PostgreSQL、RAGFlow 成功/降级、API 重启和隔离备份恢复通过；真实浏览器登录与两个受保护路由通过。
- 残余风险与边界：依赖审计的既有 React Router 风险处置及 Stage 3 原型 P2 风险未因本轮关闭；性能/负载边界、Stage 6 最终独立质量结论、Stage 7 验收和生产发布均未获批准。
- 下一动作：以本治理记录创建仅文档 PR，请项目负责人确认治理内容与精确 HEAD；确认、集成检查和逐 PR 授权完成前，不得将 Stage 6 标记为通过或启动 Stage 7。

## Stage 6 PR #61：Nginx 静态资源 MIME 修复交接（2026-07-28）

- 范围与验证基线：PR #61 的实际运行验证候选为 HEAD `2875c1ff3a244398183a5c5a9be0a76ca016c24d`，目标 `codex/stage-05-integration`。该候选包含 Nginx MIME 修复、静态配置契约和真实 HTTPS 响应头回归；本次后续提交只补充本段证据，不改运行代码或测试逻辑。整个 PR 只修改 `codebase/infra/nginx/default.conf`、`codebase/infra/tests/verify-nginx-contract.ps1`、`codebase/infra/scripts/verify-platform-readiness.ps1` 与本交接文件；不修改业务 API、身份认证、数据迁移、依赖、RAGFlow 配置或运行数据。
- 根因与风险：Nginx `http` 块未加载 `/etc/nginx/mime.types`，导致生产构建的 `.js` 与 `.css` 经 HTTPS 返回 `text/plain`。浏览器会拒绝模块脚本，造成前端空白；因此该项为 Stage 6 P1，未修复前不得给出 Stage 6 通过结论。
- 修复与回归：加载官方 MIME 类型表；静态配置契约要求该指令；platform-readiness 在真实 HTTPS 入口中解析构建 `index.html` 的哈希资源，并分别断言 JavaScript 为 `application/javascript`、CSS 为 `text/css`。
- 实际执行结果与边界：在 HEAD `2875c1f…` 上，前端 `26 passed`、生产构建、Nginx 契约和 `git diff --check` 通过；完整 `verify-platform-readiness.ps1` 通过，覆盖真实 HTTPS `.js/.css` MIME 响应、PostgreSQL 迁移 `1 passed, 3 warnings`、真实 Agent/RAGFlow `1 passed, 2 warnings`、HTTPS E2E `1 passed`、API 重启恢复及隔离备份恢复 `equipment-task011-restore-12f7edcc6dd7`。真实浏览器同时验证未认证跳转 `/login`、登录后会话令牌写入和 `/intelligent-config`、`/fault-report` 受保护路由访问。临时浏览器用户、专用 RAGFlow 数据集、Docker 项目与备份目录均不得进入仓库；此记录不构成 Merge 授权或 Stage 6 最终通过结论。
- 回退：若该修复引起静态资源交付异常，回退 PR #61 的 MIME 配置提交即可恢复合入前配置；随后仍须以真实 HTTPS 响应头复现并重新处置，不能以健康检查或配置文本替代。
- 请求动作：DEV-002 需针对 PR #61 新完整 HEAD 复审；在批准、DEV-001 最终集成检查及项目负责人绑定授权前，PR 保持 Draft，不申请 Merge 授权、不合并，Stage 6 仍不得出具最终通过结论。

## Stage 5 最终集成 Gate 请求（2026-07-27）

- 执行者：DEV-001。
- 集成候选：`codex/stage-05-integration@8a5e6ced473ea6219666d858ce5b751e61362871`（PR #56 Merge Commit）。
- 汇总：TASK-001—TASK-011（含 TASK-006-FE）的正式集成、FCP 和合并后治理证据已在任务书、检查点、测试报告和 `workflow/state.json` 中交叉记录；TASK-011 已为 `CLOSED_POST_MERGE_GOVERNANCE_COMPLETED`。
- 验证：后端 `309 passed, 13 skipped, 2 warnings`；前端 `26 passed`、生产构建通过；静态回归、`compileall`、JSON 与 diff 检查通过。真实 live-stack 覆盖 RAGFlow 成功/降级、HTTPS、重启、备份和隔离恢复，详见 `06-testing/TEST_REPORT.md`。
- 残余风险与回滚：RAGFlow 存在已观测到的间歇性外部可用性风险；前端依赖审计有 2 项既有 high-severity 发现。若后续发现阻断，按受影响 Merge Commit 做受控 `git revert -m 1` 并先在隔离环境验证；禁止覆盖数据库或删除卷。
- 请求项目负责人：仅对以上精确 HEAD 明确批准或拒绝 Stage 5 -> Stage 6 Gate。未获批准前，DEV-001、DEV-002 均不得创建或执行 Stage 6 正式测试、Stage 7 验收或生产发布。

## TASK-011 合并后治理收尾（2026-07-27）

- 交付结论：TASK-011 的开发 PR #52、后续 MinIO 初始化 PR #53 与备份输出修复 PR #54 已按授权合入；当前治理候选仅记录已完成的证据，不包含运行代码或配置。
- 精确事实：最终合并提交 `b1e4ea6c409946667e22e4bff427c4dccaa86f22`，双亲 `22f619f…` 与 `f3150a2…`；开发者 DEV-001，审核与合并执行者 DEV-002。
- 验证：合并后后端 `309 passed, 13 skipped, 2 warnings`，前端 `26 passed` 与生产构建通过；真实 Agent/RAGFlow、HTTPS、重启、备份和隔离恢复证据已完成，临时数据集已清理。
- 风险与门禁：外部 RAGFlow live-stack 曾有间歇性不可用，最终重跑已通过；生产发布、Stage 6 独立测试和 Stage 7 产品验收未执行。此治理 PR 合入后仅关闭 TASK-011，不构成任何下一阶段批准。
- 收尾事实：PR #55 已由 DEV-002 按授权手动 Merge Commit 合入 `53bdf90ec8ab743165d0542099a15d3c9de598b3`；TASK-011 正式关闭。
- 下一步：Stage 6 仍须项目负责人单独批准。DEV-001 不得因 TASK-011 关闭自行宣布 Stage 6 开始。

## TASK-006-FE 正式集成后的治理收尾候选（2026-07-22）

- 正式审核与集成：DEV-001 已批准精确 HEAD `a9c4fc0a2f651ed7465d8d2003342cb94d6f1629`；PR [#33](https://github.com/QI-code1992/Equipment-repair/pull/33) 由 DEV-001（`ll979053897-arch`）手动 Merge Commit 合入 `codex/stage-05-integration`，合并提交为 `25737f52a7e113224606cef6dbd3de49dbf7e4f4`。
- 交付：唯一正式 TypeScript 前端工程，React + Vite + TypeScript，应用壳、非业务路由页面骨架、基础样式、构建/测试脚本与非业务 `fetch` JSON 边界。
- 运行基线：`package.json` 声明 Node `^20.19.0 || >=22.12.0`、npm `>=10.0.0`；本轮验证使用 Node `v26.5.0`、npm `11.17.0`，并执行 `npm ci`。
- 验证：`npm ci` 成功且 0 vulnerabilities；前端 2 项测试通过；生产构建通过；14 项原型静态检查通过；`git diff --check`、合并树检查与原型运行时引用扫描通过。
- 范围：仅复用原型的共享视觉语言，未复制原型源码，也未实现 Agent 配置、保存、对话、SSE、引用、故障/维修流程、认证或业务 API。
- 当前门禁：本治理收尾候选不是 Stage 6 放行。合入前，TASK-006 智能配置前端子范围和 TASK-007 共享前端对话子范围继续锁定；合入后两者可按各自任务书、PR、审核和授权门禁继续，TASK-010 仍等待 TASK-003、TASK-008、TASK-009。
- 风险/回退：浏览器人工视觉回归尚未执行；可选择性回退任务合并提交，不涉及数据删除、生产操作或兼容层。

## TASK-002 正式集成后的治理收尾（2026-07-17）

- 正式审核与集成：DEV-002 已批准精确 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15`；PR #20 由集成负责人 DEV-001（`ll979053897-arch`）手动合入 `codex/stage-05-integration`，Merge Commit 为 `904886f48061e27c775f6ee2f8ddae99f5571ead`。
- 技术证据：Python 3.13 `142 passed, 5 skipped, 1 warning`；PostgreSQL 17 专项 `5 passed, 1 warning`；Compose 健康与容器内 `/healthz` HTTP 200。
- 本 PR 的交付修正：关闭 R10 的三个 Important——过期任务摘要、TASK-005/006 错误依赖状态、缺失的 DEV-001 手动合并记录。
- 治理合并：PR #25 的获批 HEAD `92ec18ec17f08d1d2226b0d98f59eeb2eba78d2f` 已由 DEV-002（`QI-code1992`）手动 Merge Commit 合入，合并提交为 `028da42eb9ab4b55ef981ac462e09993a31e8813`。
- 当前门禁：TASK-002 治理收尾完成，不是 Stage 6 放行。TASK-003/004 可启动，TASK-005 仍等待 TASK-004，TASK-006 已解除 TASK-002 前置；所有后续任务仍须遵循自身 PR、审核和授权门禁。

## CR-041 前端工程初始化前置（2026-07-22）

- 项目负责人决定：采用方案 2，新增可提前执行的正式前端工程初始化与共享基础任务，不把 TASK-006 的智能配置模块移入 TASK-010。
- 候选范围：新增 TASK-006-FE；只建立 `codebase/frontend/` TypeScript 工程、构建/测试脚本、应用壳、非业务共享基础与测试基础设施。禁止提前实现智能配置、对话、SSE、引用、采纳/直接开始或其他业务页面，也不得复制或改写 Stage 3 原型。
- 依赖修正：TASK-006 后端/迁移可继续；其智能配置前端子范围、TASK-007 的共享前端对话子范围均等待 TASK-006-FE 正式集成。TASK-010 改为在该工程基础上完成完整页面/API 集成，仍等待 TASK-003、TASK-008、TASK-009。
- 合并：PR #28 的最终授权 HEAD `ee3383bf56aa2eb1b0dc90d1b253fbf9666dbce5` 已由 DEV-001（`ll979053897-arch`）以 Merge Commit `7a44401bacbdc48d58f697a6b252449ecf44bb29` 合入 `codex/stage-05-integration`；源分支保留。
- 当前状态：TASK-006-FE 可按任务书创建独立 Draft PR 并启动；不得改变 TASK-006 PR #14 的作者/单 PR 边界，不代表任何任务完成或进入 Stage 6。

## TASK-001 正式交接（2026-07-15）

- 已批准输入基线：`25e15709a3f1d92f661d37acdb8aa3e1e0e41346`（`baseline/stage-04-development-v1.1`）。
- 修复范围：清除 `codebase/` 中后端应用工厂、配置字段、Compose 服务和网络的重复定义；不改变 PRD、SPEC、原型或公开业务 API。
- 远端提交：修复 `87538b04a168cb3c11c2e65dfb976d3a206d8218`，验证证据 `45725ac083c98ea999492b709e9792082c3db284`，分支 `codex/task-001-runtime-baseline`。
- 验证：Python 3.13.14 下健康检查测试 4 passed（仅一个第三方弃用警告）；Compose 配置通过；PostgreSQL、Redis healthy；API 容器内 `/healthz` 返回 `200` 与 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。
- 缺陷：`DEF-003`、`DEF-004` 已解决并更新台账；独立 Review 通过，无阻断、重要或次要问题。

## DEV-002 启动边界

- 可启动：TASK-006 全部已定义范围；TASK-002 前置已解除。
- 当前进度：非数据库切片已完成并保留 `FCP-006-NDB`；数据库迁移、数据库集成、共享数据模型和正式路由仍待实现。
- 仍阻塞：TASK-005 必须等待 TASK-004；其他任务继续严格遵循任务书依赖矩阵。
- 容器责任：DEV-002 不得自行宣称 Docker、Compose 或 RAGFlow 验证通过；相关真实环境验证仍由 DEV-001 提供。

## TASK-002 开发交接（2026-07-15）

- 分支与恢复点：`codex/task-002-identity-equipment`，远端实现 Commit `0b0d9cf0dc066143c0a57d4683567fadb4714c12`，交接证据 Commit `9f162b421f4fefae4cdd69a001891c7e83d4bc13`，PR 目标为 `codex/stage-05-integration`。
- PR：[#15](https://github.com/QI-code1992/Equipment-repair/pull/15) 已 Ready for review，待 Review 与集成。
- 交付契约：会话认证、操作权限依赖、角色/权限查询、登录/登出/拒绝审计、全局请求指纹幂等、组织树、设备主数据和 Alembic `0001`。
- 验证：Python 3.13.14 下 38 tests passed；Compose 配置、API 镜像构建、PostgreSQL downgrade/upgrade/current、`/healthz` 200、真实并发幂等/唯一冲突/组织树竞争均通过。
- Review：最终独立复审 Critical 0、Important 0、Minor 0。
- DEV-002 消费边界：可基于冻结的认证上下文继续 TASK-006 非数据库实现；只有 TASK-002 合入集成分支后，才可开始 TASK-006 数据库迁移/集成以及其他依赖 TASK-002 的数据库工作。
- DEV-001 下一步：提交并完成 TASK-002 PR/集成；合入后按依赖矩阵启动 TASK-003，并通知 DEV-002 数据库边界已解锁。

## TASK-002 交接状态更正（2026-07-16）

- 原因：DEV-002 对 PR #15 候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 提交 `Changes requested`；上节“Ready for review”不再代表当前有效交接状态。
- 当前状态：TASK-002 / CR-036 `In Development`；本地整改代码和契约草稿保持原状。任务书 v1.2 已通过 PR #18 合入 `codex/stage-05-integration`，CR-037 收尾记录合入后可恢复 R6/R7。
- 旧证据边界：`0b0d9cf`、`9f162b4` 和 PR #15 历史继续保留，但不得作为 TASK-002 完成、FCP、正式 PR 或集成依据。
- 协作分工：DEV-001 为任务开发者和集成负责人；DEV-002 为指定审核者及后继正式 PR 创建者。DEV-001 只能推送任务分支并发送书面审核请求。
- PR #15：保留为被拒绝候选的审核历史和本轮 Review Request 载体；DEV-002 审核新候选通过后创建后继正式 PR。
- 依赖边界：TASK-003、TASK-004、TASK-005 及 DEV-002 的数据库集成继续按任务书阻塞；TASK-006 仅保留已允许的非数据库范围。
- 下一次有效交接条件：任务书 v1.2 与本审批记录已通过治理 PR 合入集成分支；CR-036 R6/R7 完成；PostgreSQL/Compose 和完整回归通过；正式证据提交并推送；DEV-002 复审通过。
- PR #16 更正：历史 PR #16 错误指向 `main`，且当前远端 `main` 不包含获批任务书 v1.2；该 PR 不构成 CR-037 完成或 Stage 5 协作基线。必须重新创建目标为 `codex/stage-05-integration` 的治理 PR。
- CR-037 正确 PR：[PR #18](https://github.com/QI-code1992/Equipment-repair/pull/18)，已合入 `codex/stage-05-integration`；Merged Head 为 `e6b571d16192fb4462b7c118ef977df8f6ce186a`，Merge Commit 为 `18485653a94cd033cfc82e8d6c7e40c35fcfbe33`。合并树、Python 3.13、`compileall`、Compose 配置和治理一致性验证通过。
- CR-037 收尾边界：本收尾 PR 仅把合并结果写回治理台账；合入后 DEV-001 可恢复 TASK-002 / CR-036 R6/R7。TASK-002 仍未完成，TASK-003、TASK-004、TASK-005 及依赖 TASK-002 的数据库集成继续阻塞。

## CR-038 治理补救交接（2026-07-16）

- 事件：PR #15 在审核结论仍为 `Changes requested` 时被合入 `codex/stage-05-integration`，合并提交为 `e328cec64f1aa9c7cdc383579af042692dce5679`。
- 批准：项目负责人批准保留开发成果并通过独立 PR 非破坏性回滚该集成结果。
- 补救分支：`codex/cr-038-revert-pr-15-gate-violation`。
- 授权记录：`6650f615e48d88b9a54179c27a7f03d1bf48f391`。
- 回滚候选：`5d91e83679acefa5486a25bf5b921e9c12fd52d6`。
- 补救 PR：[PR #17](https://github.com/QI-code1992/Equipment-repair/pull/17)，已合入 `codex/stage-05-integration`。
- 合并批准：项目负责人于 2026-07-16T15:00:35+08:00 明确批准审查候选 `3f02ac1021ffb2f189ee53120d4b3523415bff60` 转为 Ready 并手动合入；批准后的治理文档提交不得修改代码或回滚边界。
- Merge Commit：`d37698c6e51df1701bbdfcf12ec6fa329241e0bd`。
- 验证：Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 构建、PostgreSQL/Redis/API 健康和容器内 `/healthz` 通过。
- 当前边界：CR-038 已完成；TASK-002 仍为 `Changes requested`；CR-037、TASK-002 R6/R7、TASK-003、TASK-004 和依赖 TASK-002 的数据库集成继续暂停。
- 下一步：完成 CR-037 治理 PR；合入后恢复 TASK-002 R6/R7 和 DEV-002 复审。

## TASK-002 / CR-036 新候选审核请求（2026-07-16）

- 任务开发者：DEV-001。
- 指定审核者与正式 PR 创建者：DEV-002。
- 任务分支：`codex/task-002-identity-equipment`。
- 目标分支：`codex/stage-05-integration`。
- 实现提交：R6 `35119954ba1d9ca475f03d1faa026bf6a474b18f`；R7 `11dbb226e9b77ff5185fed5fa1434b0de6749206`。
- 正式证据：本轮 `docs(task-002): record review remediation handoff` 提交后，以推送后的任务分支精确 HEAD 作为审核对象，并在 GitHub 审核请求中补记。
- 需求/AC：FR-001、FR-010、FR-011、NFR-001、NFR-009；AC-001—008、AC-038、AC-039；不改写 PRD/SPEC/AC。
- 修改范围：身份、固定角色和权限目录、失败审计与脱敏、组织层级、完整设备主数据、Alembic `0002`、API/Data Model 契约和相关测试。
- 验证：Python 3.13.14 全套 `125 passed, 5 skipped`；专用 PostgreSQL 17 集成 `5 passed`；迁移 `0002 -> 0001 -> 0002`；Compose、PostgreSQL/Redis 健康、API `/healthz`、compileall 和 diff check 通过。
- Review：DEV-001 内部独立复审 Critical 0、Important 0；Minor 为未来迁移 revision/测试函数可读性提醒，不阻塞本候选。
- 未验证：DEV-002 尚未批准；后继正式 PR 尚未创建；任务尚未正式集成。
- 依赖：无新增生产依赖；TASK-003/TASK-004 未实施；TASK-003、TASK-004、TASK-005 和依赖 TASK-002 的数据库工作继续阻塞。
- 兼容与抽象：未新增兼容分支；仅保留任务所需领域 service/schema 与测试职责拆分，无通用框架。
- 风险：Alembic `0002` downgrade 会丢弃完整合同新增字段，只允许在已备份或专用验证环境执行；PostgreSQL 集成测试有专用库名、主机和显式开关三重保护。
- 回退：应用与契约按独立任务 Commit 选择性 revert；数据库按已验证 downgrade 或前向修复策略处理，不对生产数据执行未授权删除。
- 请求动作：请 DEV-002 对推送后的精确 HEAD 复审；若通过，由 DEV-002 创建后继正式 PR。PR #15 仅保留被拒绝和违规合并/回滚历史，不得再次作为正式集成触发源。

### 集成基线同步更正

- 被取代审核 HEAD：`ab67bcdff42d64ba739571515df4e6faed158d32`；原因是该分支相对当前集成分支分叉，模拟正式合并存在冲突。
- 当前集成基线：`ac767c83128cb89ceea8e28c518be0adfbe1984c`。
- 同步 Merge Commit：`0aac415d18aee256c237adb508d2ab24314a7486`。
- 修正结果：当前集成基线已成为任务分支祖先；模拟合并无冲突；CR-037/CR-038 与 `STAGE_APPROVALS.md` 保持集成分支版本。
- 复验结果：Python 3.13.14 `125 passed, 5 skipped`；PostgreSQL 17 集成 `5 passed`；迁移、Compose 实际状态、容器健康和 `/healthz` 通过。
- 同步验证候选：`4c111d0243d947a32d555bd48b1b72cab552bac4`，已推送并完成第二次自查。
- 新请求动作：首轮 PR #15 评论中的 `ab67bcd...` 请求已被取代；本治理记录提交并推送后，以新的远端分支 HEAD 重新请求 DEV-002 审核。该最终 HEAD 包含的新增内容仅为本节台账回填，不改变 `4c111d0...` 的代码、测试或运行证据。

## TASK-002 / CR-036 R8 复审交接（2026-07-17）

- 开发者：DEV-001；指定审核者与后继正式 PR 创建者：DEV-002。
- 分支/目标：`codex/task-002-identity-equipment` → `codex/stage-05-integration`。
- 被取代审核 HEAD：`60c71dd5ab7588006ee16d794b03bef493fb3c72`；R8 代码候选：`73030f83638b3b063db483029591720bf65aac21`。
- 修复：精确固定角色/权限目录和系统管理员全授权；非固定角色不得授权；用户管理执行 `user_management.view_all`；敏感字段变体和附件正文脱敏；数据库/未知异常回滚与独立失败审计。
- 验证：本机 Python 3.13 `136 passed, 5 skipped`；专用 PostgreSQL 17 `5 passed`；迁移往返和最终目录计数通过；Compose、PostgreSQL/Redis 健康、API Up、`/healthz` HTTP 200。
- Review：DEV-001 三轮复审 Critical 0、Important 0；两个历史 Minor 已按不可改写历史约束形成书面处置。
- 交付边界：无生产依赖、兼容层、通用抽象、TASK-003 或 TASK-004 修改；未创建正式 PR。
- 请求动作：正式台账提交推送后，以远端最终 HEAD 在 PR #15 请求 DEV-002 复审。若审核通过，由 DEV-002 创建后继正式 PR；在合入前 TASK-002、TASK-003、TASK-004、TASK-005 和相关数据库依赖状态不变。

## TASK-002 / CR-036 R9 复审交接（2026-07-17）

- 开发者/审核者：DEV-001 / DEV-002；任务分支仍为 `codex/task-002-identity-equipment`，目标为 `codex/stage-05-integration`。
- 代码候选：`ac6947a642f00ba48aebcb80064f87fcc4c01ea8`，关闭 R8 复审剩余的审计脱敏 Important。
- 修复与证据：密码语义段识别；附件上下文元数据白名单；驼峰、下划线、嵌套/list 和真实失败审计表 `metadata_json` 回归。RED `2 failed`，定向 `19 passed`，Python 3.13 全量 `138 passed, 5 skipped`。
- PostgreSQL 证据：新增 `41591e7` Docker `test` 目标，在构建阶段安装 dev 依赖、运行时接入内部网络；专用 PostgreSQL 17 集成 `5 passed, 1 warning`。默认生产镜像不含 pytest/httpx。
- 请求动作：推送台账 HEAD 后，请 DEV-002 复审；TASK-002 仍未验收、未集成，依赖不解锁，DEV-002 通过后才创建后继正式 PR。

## TASK-002 / CR-036 R10 复审交接（2026-07-17）

- 开发者/审核者：DEV-001 / DEV-002；任务分支 `codex/task-002-identity-equipment`，目标 `codex/stage-05-integration`。
- 代码候选：`b4d451009d1deb9dbe3286f5bff4db9414ef4aee`，修复 R9 补充审核的一个 Important。
- 修复：附件 context 的标量和纯标量列表默认脱敏；混合 list/dict 只保留字典元数据白名单；紧凑密码键 `newpassword`、`userpassword` 脱敏。
- 证据：RED `2 failed`；定向 `21 passed`；Python 3.13 全量 `140 passed, 5 skipped`；失败请求已从 `AuditEvent.metadata_json` 读取验证无明文。独立 PostgreSQL 17 `5 passed, 1 warning`；Compose/健康检查 `/healthz` HTTP 200。
- 请求动作：推送本台账 HEAD 后，请 DEV-002 对该精确远端 HEAD 复审。TASK-002 仍未验收、未集成，DEV-002 批准后才可创建后继正式 PR；依赖不解锁。

## TASK-002 / CR-036 R11 复审交接（2026-07-17）

- 开发者/审核者：DEV-001 / DEV-002；任务分支 `codex/task-002-identity-equipment`，目标 `codex/stage-05-integration`。
- 代码候选：`ea4338bad15f16048226a329801d3144b367909e`，修复 R10 的敏感键语义识别 Important。
- 修复：完整分段识别附件/文件与敏感语义；有限紧凑规则覆盖 `passwordvalue`、`userpassword`；保留 `profile`、`token_count`、`token_usage` 等反例；附件容器继续使用元数据白名单。
- 证据：RED `2 failed`；定向 `23 passed`；Python 3.13 全量 `142 passed, 5 skipped`；失败审计 `AuditEvent.metadata_json` 无测试秘密。PostgreSQL 17 `5 passed, 1 warning`；Compose/`/healthz` HTTP 200。
- 已知残余风险：任意未知字段默认脱敏不在本 CR，当前结论仅关闭已知敏感语义别名漏洞。
- 请求动作：推送本台账 HEAD 后，请 DEV-002 对精确远端 HEAD 复审；TASK-002 仍未验收、未集成，依赖不解锁，DEV-002 批准后才可创建后继正式 PR。

## CR-040 协作治理候选交接（2026-07-17）

- 项目负责人决定：采用“任务开发者创建并维护同一 Draft PR、另一名开发者批准、DEV-001 集成检查、项目负责人逐 PR 授权、非任务开发者获批后 Merge”的开发任务流程。
- 角色：Stage 5 只有 DEV-001、DEV-002 两名开发者。DEV-001 负责 DEV-002 开发任务审核、全部 PR 集成检查、授权请求、合并 DEV-002 的获批 PR 和合并后回归；DEV-002 负责自身开发任务、DEV-001 开发任务审核及合并 DEV-001 的获批 PR。“Agent”是执行方式，不是另设角色。
- 治理边界：只修改流程、任务书、AGENTS 或工作流台账且不含业务代码、测试代码、数据库、基础设施或部署配置的纯治理文档 PR，不要求两名开发者交叉代码审核；由项目负责人确认治理内容和精确 HEAD，DEV-001 执行集成核查和请求授权，非 PR 作者的开发者获批后合并。
- Merge 授权请求必须包含：TASK/CR、PR 链接、源/目标分支、精确 HEAD、适用的开发审核或治理确认结论、Critical/Important/Minor 或治理检查结果、测试与 Docker 证据（如适用）、依赖、冲突、共享契约、风险、回滚和合并后验证计划。
- 安全边界：未获项目负责人明确授权不得 Merge；授权后 HEAD 或条件变化则失效；禁止 auto-merge、merge queue、直接 push 集成分支、普通 Stage 5 PR 指向 `main`。
- 历史边界：不追溯改写 TASK-001、TASK-002 或 CR-037—CR-039 的已发生 GitHub 操作。生效时仍 Open 的 TASK-006 Draft PR #14 应继续作为同一 PR，不再创建后继 PR。
- 当前候选分支：`codex/cr-040-agent-merge-approval`；目标：`codex/stage-05-integration`。本治理候选不修改 `codebase/`，不解锁 TASK 依赖，也不批准进入 Stage 6。

## TASK-004 独立 RAGFlow 基础设施审核交接（2026-07-20）

- 开发者/审核者：DEV-001 / DEV-002；同一 Draft PR [#27](https://github.com/QI-code1992/Equipment-repair/pull/27)；分支 `codex/task-004-ragflow-infra` → `codex/stage-05-integration`。
- 基线/功能候选：`b29c69d13c3d1c81f01023152eabf0c0f2d02741` / `ac8c007730d8e947c5687380e4583e8b23d2cce1`；正式审核对象为本证据提交推送后的 PR #27 完整精确 HEAD。
- 交付：独立五服务 Compose、固定版本与摘要、内部/访问双网络、仅回环 Web/API、五个命名卷、脱敏环境模板、健康/隔离/重启持久化脚本、唯一运行手册和 TASK-005 API 接入契约。
- 验证：Python 3.13 `5 passed, 1 warning`；平台/RAGFlow Compose 和静态契约通过；5 容器 healthy、Web HTTP 200、Elasticsearch 8.11.3；依赖无宿主端口；MySQL/Redis/MinIO/Elasticsearch 重启后探针一致且容器未重建。
- Review：DEV-001 已完成 Standards、Spec/失败路径、完整 diff 三轮复审，Critical 0、Important 0、Minor 0；DEV-002 尚未对最终精确 HEAD 提交正式审核结论。
- 边界：未修改业务 API、数据库迁移、前端、原型或 TASK-005；未新增生产依赖、兼容代码、通用抽象层或无关修改。真实文档上传/解析/混合检索/引用属于 TASK-005，不在本任务实现。
- 风险/回退：镜像首次拉取受外部 Registry 可用性影响；本机端口可通过本地环境覆盖；完整备份恢复演练延后 TASK-011。回退只停止/移除项目容器并选择性 revert；删除命名卷必须另行授权。
- 请求动作：推送证据提交并确认 PR #27 精确 HEAD 后转 Ready，请 DEV-002 审核。TASK-005 在 PR #27 获批、逐 PR Merge 授权、由 DEV-002 合并且 DEV-001 完成合并后复验前继续锁定；Stage 6 禁止进入。

## TASK-004 PR #27 R1 审核修正交接（2026-07-20）

- 审核/修正：DEV-002 对 `8b628fcfbf80fb6490d8d3dd5257feafba9d1595` 给出 `Changes requested`（Critical 0、Important 3、Minor 0）；DEV-001 在同一分支和同一 PR 内完成修正，功能提交为 `f87a0c309c322f9accedcaea4a80aed84483b0e7`。
- 三项关闭证据：9380 稳定版本 API 在有限启动重试内为 HTTP 200 且返回 v0.25.6 契约；MinIO 经 S3 API 创建随机 bucket/object、整栈重启后回读并清理；5 个固定镜像逐一匹配获批 SHA-256，错误摘要突变测试被拒绝。完成前矩阵发现并修复了容器 healthy 后 API 短暂未就绪的时序缺陷，追加功能提交为 `ba7e13f2b585f872ca811e98b50c09e25020fba5`。
- 验证：Python 3.13 `5 passed, 1 warning`；平台/RAGFlow Compose config、静态契约、真实健康/API、网络隔离、四存储重启持久化及 `git diff --check` 全部通过。
- 交付边界：无业务 API、数据库迁移、TASK-005、生产依赖、兼容代码、通用抽象或无关修改；真实文档上传/解析/混合检索/引用仍属于 TASK-005。
- 请求动作：将本正式台账提交推送到同一 PR #27，以新的完整精确 HEAD 重新请求 DEV-002 审核。旧审核随 HEAD 变化失效；复审通过前不得请求 Merge 授权，TASK-005 继续锁定，Stage 6 禁止进入。

## TASK-004 PR #27 R2 审核修正交接（2026-07-20）

- 审核/修正：DEV-002 对 `6c6fda004f806f8b72eddaad64aac419b78a7a6f` 给出 `Changes requested`（Critical 0、Important 4、Minor 2）；DEV-001 继续在同一分支和 PR #27 内修正。
- 关闭证据：验证脚本绑定展开 Compose 镜像、获批 digest、固定标签与运行容器镜像 ID；Runbook 显式传入忽略的本地 `EnvFile`；Web/API 均有限超时；当前执行窗口日志依赖错误与秘密值扫描为 0；证据包含时间、命令退出码和脱敏摘要；失败验证保留四类持久化探针；PR 标题按任务书格式修正。
- 真实验证：Python 3.13 `5 passed, 1 warning`；平台/RAGFlow Compose config、静态契约、5 容器 healthy、Web/API 200、Elasticsearch 8.11.3、网络隔离、四存储 restart、错误镜像/摘要拒绝及失败探针保留全部通过。未输出或提交秘密值。
- 交付边界：无业务 API、迁移、TASK-005、生产依赖、兼容代码、通用抽象或无关修改；TASK-005 真实文档能力和 TASK-011 灾备仍不属于本轮。
- 请求动作：推送本轮功能和正式台账提交，确认 PR #27 完整精确 HEAD，并重新请求 DEV-002 审核。复审通过前不得请求 Merge 授权；TASK-005 继续锁定，Stage 6 禁止进入。

## TASK-004 PR #27 R3 审核修正交接（2026-07-20）

- 审核/修正：DEV-002 对 `601d54d2427302999c7bc10ac5beec3ac0565501` 给出 `Changes requested`（Critical 0、Important 2、Minor 0）；DEV-001 在同一分支和 PR #27 内完成最小修正，功能提交 `dc909fff1c8260f2f8a50670192761572cdfb76b`。
- 关闭证据：Runbook 不再向无该参数的隔离脚本传 `-EnvFile`，回归通过 PowerShell AST 核对真实参数签名；持久化脚本严格检查 MySQL、Redis、MinIO、Elasticsearch 及临时资源清理退出码，所有清理完成后才输出 PASS。
- 真实验证：5 容器 healthy，Web/API 200，RAGFlow v0.25.6，Elasticsearch 8.11.3；依赖错误/秘密值命中均为 0；网络隔离和四存储 restart 通过，容器未重建，四类探针清理完成；PowerShell 语法、两个静态契约、Compose config 和 diff check 通过。
- 交付边界：仅 TASK-004 Runbook、验证脚本、回归测试和正式证据；无业务 API、迁移、TASK-005、生产依赖、兼容代码、通用抽象或无关修改。
- 请求动作：推送正式台账提交后，以 PR #27 新完整 HEAD 重新请求 DEV-002 审核。新审核通过前不得请求 Merge 授权；TASK-005 继续锁定，Stage 6 禁止进入。

## TASK-004 PR #27 R4 审核修正交接（2026-07-20）

- 审核/修正：DEV-002 对 `6cd29f158b2c03f61c5b21a7e9bf99d30ec17a34` 给出 `Changes requested`（Critical 0、Important 2、Minor 0）；DEV-001 在同一分支和 PR #27 内完成最小修正，功能提交 `29180e285767cbffb9d694cd1834f04514d2cc18`。
- 关闭证据：设计、计划与 Runbook 统一真实运行使用 `.env.local`，静态 Compose config 才允许 `.env.example`；四类清理通过子进程执行固定非零假命令，均返回非零且不输出 PASS，避免只依赖源码正则判断。
- 真实验证：Python 3.13 `5 passed, 1 warning`；Compose/审核/清理行为契约、PowerShell 语法、5 容器健康、Web/API 200、网络隔离、四存储 restart 和严格清理通过；未输出或提交真实秘密。
- 交付边界：无业务 API、迁移、TASK-005、生产依赖、兼容代码或无关修改；新增一个仅检查外部 Compose 命令退出码的最小模块。
- 请求动作：推送本正式台账提交后，以 PR #27 新完整 HEAD 重新请求 DEV-002 审核。新审核通过前不得请求 Merge 授权；TASK-005 继续锁定，Stage 6 禁止进入。

## TASK-004 PR #27 R5 审核修正交接（2026-07-22）

- 审核/修正：DEV-002 对 `a5ac8490bf678ea03efc702052f7f1edecff182b` 给出 `Changes requested`（Critical 0、Important 1、Minor 0）；DEV-001 在同一分支和 PR #27 内完成最小修正，功能提交 `314b46d3efdc7af0d13c671fadd41be7bb3900d1`。
- 关闭证据：任务书 Markdown 列表中的真实运行命令现在进入环境契约；`.env.example` 运行变异返回非零，静态 config 和明确禁用示例不误报；独立累计复审 Critical 0、Important 0、Minor 0。
- 验证：Windows PowerShell 语法、审核契约、四类清理失败行为、Compose 静态契约和 diff check 通过。本轮未改运行配置且未重跑 Docker；Python 3.13 历史虚拟环境入口当前不可创建进程，未虚报新结果。
- 交付边界：仅 TASK-004 审核测试与正式证据；无业务 API、迁移、TASK-005、生产依赖、兼容代码、抽象层或无关修改。
- 请求动作：推送本证据提交后，以 PR #27 新完整 HEAD 重新请求 DEV-002 审核。新审核通过前不得请求 Merge 授权；TASK-005 继续锁定，Stage 6 禁止进入。
## TASK-004 PR #27 R6 复审交接（2026-07-22）

- 审核/修正：DEV-002 对 `80b40182efa49033ee561f34fd6e078b3469a733` 给出 Changes requested（Critical 0、Important 1、Minor 0）；DEV-001 在同一分支和 PR #27 内完成最小修正，功能提交为 `78e3132d907870f17980ade7142f7c9a7ae7562e`。
- 关闭证据：两个真实验证脚本默认使用 Git 忽略的 `.env.local`；文件缺失时在 Docker 调用前非零退出并给出明确错误；`.env.example` 仅保留给静态 Compose 配置检查。
- 验证：Python 3.13 `5 passed, 1 warning`；PowerShell/Compose/失败行为契约通过；5 容器 healthy，Web/API 200，网络隔离及四存储重启恢复/清理通过。
- 边界：无业务 API、迁移、TASK-005、生产依赖、兼容代码、抽象层或无关修改。
- 请求动作：推送证据提交后，以 PR #27 新完整精确 HEAD 重新请求 DEV-002 审核；批准前不得请求 Merge 授权，TASK-005 继续锁定，Stage 6 禁止进入。

## CR-042：PR #29 并发目标分支竞态追认（2026-07-22）

- 事件：PR #29 授权时目标分支为 `7a44401bacbdc48d58f697a6b252449ecf44bb29`，随后 TASK-004 合入 `87e8e3c0aab62ee9105bf3807b23fcf44ac15137`；PR #29 最终以第一父提交为 `87e8e3c...` 的 Merge Commit `960c64ffc64c20edfb5bd73a2721678c9b9972c8` 合入。
- 处置：项目负责人明确追认该实际目标上的治理合并结果，不授权回滚。该追认只处理该已发生竞态，不改变 TASK-006-FE 的任务范围或免除后续 PR 的目标分支变化重核查要求。
- 预防：目标分支、HEAD、依赖或 checks 在授权后发生变化时，DEV-001 必须停止 Merge、重新集成检查并重新申请绑定精确条件的授权；GitHub `MERGEABLE/CLEAN` 不构成例外。

## TASK-004 PR #27 合并后治理收尾（2026-07-22）

- 开发者/审核者/Merge 执行者：DEV-001 / DEV-002 / DEV-002。
- PR/版本：PR #27；获批源 HEAD `76732606412d71239d302e4e9e5a0da6b364fd70`；Merge Commit `87e8e3c0aab62ee9105bf3807b23fcf44ac15137`。
- 授权与审核：DEV-002 Approved 同一 HEAD；项目负责人授权同一 PR/HEAD；DEV-002 按职责分离执行 Merge Commit。
- 合并后验证：Python 3.13 `5 passed, 1 warning`；PowerShell 三类契约和 RAGFlow Compose 通过；5 容器 healthy、Web/API 200、固定镜像/日志扫描、网络隔离、四存储重启恢复及清理通过。
- 交付边界：独立 RAGFlow 基础设施正式集成；无业务 API、数据库迁移、TASK-005 实现、生产依赖、兼容代码或通用抽象层。
- 风险/回退：外部镜像 Registry 可用性仍是运行风险；完整备份恢复属于 TASK-011。应用回退可评估 `git revert -m 1 87e8e3c0aab62ee9105bf3807b23fcf44ac15137`；删除命名卷必须另行授权。
- 依赖：本治理 PR 合并后 TASK-004 正式闭环，TASK-005 的 TASK-004 阻塞解除；Stage 6 仍未获准。
- 请求动作：项目负责人确认本纯治理 PR 的内容和精确 HEAD；DEV-001 完成集成核查与授权请求后，由非 PR 作者 DEV-002 合并。

## TASK-005 PR #37 真实联调与重新审核交接（2026-07-23）

- 开发者/审核者/Merge 执行者：DEV-002 / DEV-001 / DEV-001；同一 Draft PR [#37](https://github.com/QI-code1992/Equipment-repair/pull/37)，目标 `codex/stage-05-integration`。
- DEV-001 实测对象：`9375d12853248ceb39068f509a8dbd95bf717ce5`。上传、ClamAV 恶意附件拒绝、RAGFlow 解析、`READY`、混合检索与引用回传通过，`1 passed`；临时数据集、容器、网络和卷已清理，共享 RAGFlow 五服务仍 healthy。
- 回归证据：Python 3.13 后端 `217 passed, 11 skipped`；`compileall`、验证脚本契约和 `git diff --check` 通过；三轮复核 Critical 0、Important 0、Minor 0。
- 集成同步：PR 分支已吸收当前 `codex/stage-05-integration`，解决 `app/main.py`、`pyproject.toml`、SELF_TEST 与 CHECKPOINTS 冲突；同时保留 TASK-005 路由/MinIO 依赖与已集成 Agent Runtime/LangGraph 内容。
- 同步后回归：Python 3.13.14 全量后端 `259 passed, 10 skipped, 2 warnings`；`pip check`、`compileall` 与暂存 diff check 通过。
- 请求动作：推送证据与同步提交后，以 PR #37 新完整精确 HEAD 请求 DEV-001 正式审核。新 HEAD 使旧审核失效；审核前不得申请 Merge 授权、合并、解锁 TASK-009/011 或进入 Stage 6。

## TASK-007 开发交接（2026-07-22）

- 开发者/指定审核者：DEV-002 / DEV-001；分支 `codex/task-007-agent-runtime`，目标 `codex/stage-05-integration`。
- 候选功能提交：`7c3cf64fe7537ca8f7e05c66e4d5a71ff3383e61`。
- 交付范围：Runtime 持久化模型、线程访问隔离、配置快照、checkpoint、SSE 状态事件、恢复接口和推理参数映射；Alembic `0005_task007`。
- 验证证据：Python 3.13 全量后端 `224 passed, 9 skipped, 1 warning`；TASK-007 `2 passed`；迁移检查、`compileall`、`git diff --check` 通过。
- 未验证项：当前环境未执行 Docker/PostgreSQL 真实 checkpoint 联调，未连接外部 LLM；需 DEV-001 具备环境后验证。
- 风险/回退：`0005_task007` downgrade 会删除 Runtime 四表，生产数据回退须另行授权并先备份；应用可回退功能提交。
- 请求动作：请 DEV-002 在同一任务分支创建/更新 Draft PR，完成 Ready 前自测后请求 DEV-001 审核精确 HEAD；未完成 Review、集成检查和项目负责人逐 PR/HEAD 授权前，不得合并或解锁下游任务。

## TASK-007 Changes requested 修订交接（2026-07-23）

- 原审核 HEAD：`24421bc49d45823fa9e2946124940a26de684545`；DEV-001 对 PR #40 提出 3 项 P1、1 项 P2，旧审核失效。
- 本轮修订：消息幂等重放/409 冲突、线程/运行/resume 脱敏审计、递归上下文/附件/状态脱敏、allowlist ToolCall 审计、管理员/SSE/checkpoint/嵌套敏感测试和可选 PostgreSQL 集成测试。
- 验证：Python 3.13 全量 `226 passed, 10 skipped, 1 warning`；Runtime `4 passed`；`compileall` 和 `git diff --check` 通过。
- 阻断：真实 LangGraph checkpoint 尚未实现；新增 LangGraph 生产依赖需项目负责人先确认，当前不申请 Ready、Merge 或下游解锁。

## TASK-007 LangGraph 依赖授权后修订交接（2026-07-23）

- 授权：项目负责人确认允许新增 LangGraph 生产依赖。
- 新增：`langgraph>=0.6,<0.7`、`langgraph-checkpoint-postgres>=2.0,<3.0`。
- 实现：LangGraph `StateGraph`、PostgreSQL `PostgresSaver` checkpoint、同一 `thread_id` resume；SQLite 测试使用内存 saver。
- 验证：全量后端 `226 passed, 10 skipped, 2 warnings`；Runtime `4 passed`；`compileall` 和 `git diff --check` 通过。
- 未验证：当前无 Docker/PostgreSQL 专用环境；需 DEV-001 执行真实 PostgreSQL checkpoint 集成测试后再提交 Ready 审核请求。

## TASK-007 第二轮 Changes requested 修订交接（2026-07-23）

- 原审核 HEAD：`71b7d3c1993beb6abd94a22bacd0b9d392347d7d`；阻断为 resume 幂等、PostgresSaver 真实恢复和历史 checkpoint 不得被调用方 state 覆盖。
- 修订：resume 幂等重放/409 与 confirmation/audit 唯一性测试；`run_checkpoint` 通过同一 `thread_id` 先读取 saver 历史 state，再合并白名单恢复输入；可选专用 PostgreSQL 测试覆盖真实首存/恢复。
- 验证：全量 `227 passed, 10 skipped, 2 warnings`；Runtime/集成定向 `5 passed, 1 skipped`；compileall/diff-check 通过。
- 未验证：当前无专用 PostgreSQL DSN，真实 PostgresSaver 集成测试跳过；请 DEV-001 提供环境执行并将结果绑定新精确 HEAD。

## TASK-007 第三轮 DSN 修订交接（2026-07-23）

- 审核对象：HEAD `d315d11c67e3886aad7feae9b0699d12e64b1336`。
- 修订：专用 PostgreSQL 测试改用项目 `create_database_engine()`（psycopg v3）；LangGraph PostgresSaver 接收前统一转换为 libpq `postgresql://`；新增 URL 转换回归测试。
- 验证：全量 `228 passed, 10 skipped, 2 warnings`；Runtime/集成定向 `6 passed, 1 skipped`；compileall/diff-check 通过。
- 未验证/请求：当前无专用 PostgreSQL DSN；请 DEV-001 在 PostgreSQL 17 真实环境运行 `TASK007_POSTGRES_DSN=... TASK007_ALLOW_DESTRUCTIVE_TESTS=1 python -m pytest tests/integration/test_task007_postgres.py -q`，并将结果绑定下一次精确 HEAD 审核。

## TASK-007 PR #40 合并后治理收尾候选（2026-07-23）

- 代码集成事实：PR [#40](https://github.com/QI-code1992/Equipment-repair/pull/40) 的源 HEAD `fcd643ab0b0e33a585e3be6ec0b0036a611059c4` 已合入 `codex/stage-05-integration`，Merge Commit `bf842626987148575173c6cf3f34970fc496ad7c`；第一父 `fdec916fad943acb8ad62a1cf5bc3ce8f770cc8d`，第二父为源 HEAD。
- 审核与集成：DEV-001 已批准该精确 HEAD 并完成最终集成技术检查；这两项是代码审核/集成事实，不等同于项目负责人 Merge 授权。项目负责人已正式追认 PR #40、源 HEAD、Merge Commit 及合并结果；PR #41 已完成治理收尾并合入。
- 合并后证据：后端 `228 passed, 10 skipped, 2 warnings`；PostgreSQL 17 真实 PostgresSaver checkpoint/restart `1 passed, 1 warning`；compileall、Compose 配置、API 生产镜像构建、PostgreSQL/Redis healthy、容器内 `/healthz` HTTP 200、merge-tree 与 `git diff --check` 通过。
- 治理范围：本收尾候选只更新 `workflow/`、`05-development/`、任务书和本交接台账，不修改 `codebase/`、测试实现、迁移、基础设施、部署或运行配置。
- 当前门禁：TASK-007 治理闭环已完成；依赖矩阵允许的下游可继续。该闭环不构成 Stage 6 批准，Stage 6 仍须单独门禁。

## TASK-003 本地开发候选交接（2026-07-22）

- 开发者/审核者：DEV-001 / DEV-002；分支 `codex/task-003-maintenance-lifecycle`，目标 `codex/stage-05-integration`。
- 候选：本地实现与验证候选 `053e69039e86c12d4ddb96ee768074bf76ee6497`；吸收最新集成基线 `f135997a6ecc009de75735b673499b475615a717` 的同步 Merge Commit 为 `4877dcdc301b97d884a43883a5584fdee1d28c41`。
- 交付：故障、工单、维修、人工最终字段、结构化案例查询、活跃故障设备停用保护和可逆 Alembic `0003_task003`。
- 验证：Python 3.13.14 模块 `168 passed, 1 warning`；专用 PostgreSQL 17 `4 passed, 1 warning`；`compileall`、单一迁移 head、平台/RAGFlow Compose 和差异检查通过。
- 边界：不调用 RAGFlow、Agent 或外部网络；无新增生产依赖、兼容层、通用抽象、前端或其他正式任务实现。
- 风险/回退：`0003_task003` downgrade 会删除 TASK-003 五表，只允许专用验证库或已备份环境；应用按独立 TASK-003 Commit 选择性 revert，任何生产数据回退另行授权。
- 当前门禁：候选尚未推送、Draft PR 尚未创建或更新、DEV-002 尚未审核、未申请 Merge 授权、未集成；不解锁 TASK-009/010/011，Stage 6 仍未获准。
- 下一动作：提交本地正式台账；获得 DEV-001 明确推送指令后推送同一任务分支并创建/更新唯一 Draft PR，绑定完整精确 HEAD 请求 DEV-002 审核。

## TASK-003 PR #32 合并后治理收尾（2026-07-22）

- 开发者/审核者/Merge 执行者：DEV-001 / DEV-002 / DEV-002。
- PR/版本：PR #32；获批源 HEAD `8960b5d8ab1e7073036c6151744233e26c15c9e9`；Merge Commit `51337db767eb94051f78a5c537a3ff48d428a742`。
- 审核与授权：DEV-002 Approved 同一 HEAD；项目负责人授权同一 PR/HEAD；DEV-002 按职责分离执行 Merge Commit。
- 合并后验证：Python 3.13.14 `173 passed, 9 skipped, 1 warning`；专用 PostgreSQL 17 `4 passed, 1 warning`；Alembic 单一 head、平台/RAGFlow Compose、compileall 和差异检查通过。
- 交付边界：TASK-003 后端维修事实闭环正式集成；无 RAGFlow/Agent/向量/正式前端、新生产依赖、兼容代码、通用抽象或范围外修改。
- 风险/回退：`0003_task003` downgrade 会删除五张业务表；生产回退优先前向修复，数据回退必须备份并另行授权；应用可评估选择性 revert Merge Commit。
- 依赖：本治理 PR 合入后 TASK-003 正式闭环；TASK-009/010/011 仍等待各自其余依赖，Stage 6 仍未获准。
- 请求动作：项目负责人确认本纯治理 PR 的内容和精确 HEAD；DEV-001 完成集成核查与授权请求后，由非 PR 作者 DEV-002 合并。

## TASK-005 PR #37 Changes requested 整改交接（2026-07-23）

- 开发者/审核者/Merge 执行者：DEV-002 / DEV-001 / DEV-001；同一 PR [#37](https://github.com/QI-code1992/Equipment-repair/pull/37) 已恢复 Draft，目标为 `codex/stage-05-integration`。
- 审核基准：`1cee0317ab1eefca2ca4900e2e97804ae1448665`，结论 Changes requested；旧审核不得用于批准或集成。
- 已完成整改：实际 Worker 入口 `app.modules.knowledge.worker_main`；默认安全跳过、显式专用环境才运行的真实生命周期测试；不含凭据且不改写共享基础设施的 PowerShell 验证入口。
- 验证：Python 3.13 全量 `261 passed, 11 skipped, 2 warnings`；新增/Worker 定向 `5 passed, 1 skipped, 2 warnings`；`pip check`、`compileall`、`git diff --check` 通过。真实联调本轮未运行，须由 DEV-001 在完整候选 HEAD 上执行。
- 共享迁移阻断：当前 Alembic 单链截至 `0005_task007`，缺少 `knowledge_datasets`、`knowledge_documents`、`knowledge_citations`。任务书规定共享迁移由 DEV-001 最终决策，项目规则要求项目负责人确认具体数据库迁移范围；DEV-002 未创建并行迁移头。
- 请求动作：请 DEV-001 明确知识三表应接续的 revision/down_revision 与候选集成方式，并由项目负责人确认该具体迁移范围。迁移、真实复验、PR 描述更新和新精确 HEAD 复审全部完成前，PR 保持 Draft，不申请 Merge 授权、不解锁下游、不进入 Stage 6。
- 迁移决定与接收：项目负责人已批准四表 `0006_task005` / `0005_task007`；DEV-001 的三文件提交 `2fe848bfb5f7f7849b950cbecfa40644e6782a05` 已精确 cherry-pick 到同一 PR 分支，生成提交 `78ad1c81f6292c1fc3706b35d9dd495a8244d1b4`。
- 验证更新：DEV-001 PostgreSQL 17 升降级往返 `1 passed`；DEV-002 定向 `6 passed, 2 skipped`、全量 `262 passed, 12 skipped, 2 warnings`，`pip check`、`compileall`、唯一 `0006_task005 (head)` 和 diff check 通过。
- 下一动作：DEV-002 推送含迁移的完整新 HEAD 后，DEV-001 对该 HEAD 执行真实 RAGFlow/ClamAV 联调和复审；完成前仍不转 Ready、不申请 Merge 授权或解锁下游。
- 基础设施增量接收：项目负责人批准的 TASK-005 隔离验证基础设施由 DEV-001 在 `codex/task-005-validation-infra` 实现，DEV-002 已连续 cherry-pick `dbf4d68b`、`579a98e`、`6c2df42` 到同一 PR #37 分支。DEV-002 核验普通 Compose 拓扑不包含验证服务、清理目标受 marker/GUID/固定文件名约束、验证测试不直接调用底层同步函数且依赖 Compose Worker 常驻入口。
- DEV-002 回归：定向 `10 passed, 2 skipped, 2 warnings`；全量后端 `266 passed, 12 skipped, 2 warnings`；`pip check`、`compileall`、Alembic 唯一 `0006_task005 (head)`、`git diff --check` 通过。当前环境无 `docker`/`pwsh`，Compose 和 PowerShell 语法仅引用 DEV-001 实测，需 DEV-001 对新 HEAD 重新绑定复审。
- 下一动作：推送证据提交后，请 DEV-001 针对 PR #37 新精确 HEAD 执行/确认真实 PostgreSQL、RAGFlow、ClamAV、Compose Worker 联调与正式复审；复审前仍保持 Draft，不申请 Merge 授权。
## TASK-008 开发启动交接（2026-07-23）

- 开发者/审核者：DEV-002 / DEV-001；分支 `codex/task-008-fault-metric-agents`，目标 `codex/stage-05-integration`。
- 基线：`origin/codex/stage-05-integration@78e9dfb`；TASK-002、TASK-006、TASK-007 前置已满足，TASK-005 独立进行不阻塞本任务。
- 范围：故障草稿字段采集与人工确认、固定 40 项指标目录、最多五项批量查询、非法维度拒绝、受控健康分读取失败降级；不实现诊断 Agent 或模型计算业务数值。
- 当前候选：PR #43 已创建并 Ready，初始候选 HEAD `58a64d9dfbc4672cfd4cdc118127850dd83fed5e`；证据同步提交后需以新完整 HEAD 重新绑定审核。
- 验证：专项 `12 passed, 2 warnings`；后端全量 `240 passed, 10 skipped, 2 warnings`；`git diff --check` 与 `workflow/state.json` 解析通过。
- 风险/边界：未执行 Docker/PostgreSQL/RAGFlow 真实联调；无新增生产依赖、迁移、兼容层或通用抽象；健康分公开路由不提前突破 TASK-002 冻结路由表。
- 下一动作：DEV-002 推送证据同步后的新精确 HEAD，并在同一 PR #43 重新请求 DEV-001 审核；审核通过后再走 DEV-001 集成检查、项目负责人逐 PR/HEAD 授权和 DEV-001 合并。当前不请求授权、不解锁下游、不进入 Stage 6。

## TASK-008 P1 修复交接（2026-07-23）

- DEV-001 审核：PR #43 / HEAD `4e6aec342849f60fdd281c083f3a21147bc7d866` 为 Changes requested；阻断为故障确认未接入业务 API、健康分读取器未接入可执行边界。
- 修复候选：同一 PR 新 HEAD `24153155da11dac0579466c05c8a04c7371e8904`；确认提交复用既有维护服务、权限、幂等和审计；健康分 API 通过受控 reader 读取并失败降级；`get_health_score` 已加入白名单。
- 验证：专项 `14 passed, 2 warnings`；后端全量 `244 passed, 10 skipped, 2 warnings`；compileall、JSON 解析、diff-check 通过。
- 下一动作：DEV-001 重新绑定新精确 HEAD 审核。当前不请求 Merge 授权、不合并、不解锁 TASK-009/010/011、不进入 Stage 6。

## TASK-008 幂等冲突 P1 修复交接（2026-07-24）

- DEV-001 新反馈：PR #43 HEAD `aabfba77b0c2db924f11b67344922986c4888738` 的 `IdempotencyKeyReused` 未映射为 409。
- 修复：提交端点捕获冲突异常；同 Key 同体重放原响应，同 Key 不同体返回 `409 IDEMPOTENCY_KEY_REUSED`，故障记录和成功审计无重复。
- 验证：Agent 专项 `15 passed, 2 warnings`；后端全量 `245 passed, 10 skipped, 2 warnings`；compileall、diff-check 通过。
- 下一动作：推送本次修复后的新精确 HEAD，并在同一 PR #43 请求 DEV-001 复审；仍不申请 Merge 授权、不合并、不解锁下游、不进入 Stage 6。

## TASK-008 不完整草稿 P1 修复交接（2026-07-24）

- DEV-001 新反馈：PR #43 HEAD `4d84ec75b57e603b9a8bfc0542ef3d1e5074f0b2` 的不完整已确认草稿返回未处理异常。
- 修复：缺失 `occurred_at`/`duration_minutes` 时返回 `422 FAULT_DRAFT_INCOMPLETE` 和字段映射；失败不写业务故障、成功审计或成功幂等响应。
- 验证：专项 `18 passed, 2 warnings`；全量后端 `246 passed, 10 skipped, 2 warnings`；compileall、diff-check 通过。
- 下一动作：推送新精确 HEAD 并请求 DEV-001 复审；继续禁止 Merge 授权、合并、下游解锁和 Stage 6。
- 当前候选：PR #43，HEAD `ad50034ccb18422ac9a9c88325b9f0c4e9cb22dc`；目标 `codex/stage-05-integration`；状态 Open/Ready for review。
- 治理校准：正式台账、FCP、SELF_TEST、CODE_REVIEW、COMMIT_LOG 与本交接统一绑定当前候选；专项真实结果 `18 passed, 2 warnings`，全量后端 `246 passed, 10 skipped, 2 warnings`，compileall 与 diff-check 通过。
- 门禁：代码 P1 已关闭但尚待 DEV-001 对新精确 HEAD 复审；未申请 Merge 授权、未合并、未解锁下游、Stage 6 禁止。

## TASK-008 合并后治理收尾交接（2026-07-24）

- 集成：PR #43 获批 HEAD `19eaf1f213c50471f93b4e09e17df57bbeb1987b` 已在项目负责人授权后由 DEV-001 手动合入 `codex/stage-05-integration`，Merge Commit `84ac8815cab403cb71a86230b4f705944bb5f6d2`。
- 验证：双亲与祖先关系正确；Python 3.13 后端 `246 passed, 10 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 merge diff check 通过。
- 结果：项目负责人已确认 PR #45 精确 HEAD `883053f59890272ef1dbb311b8d47bce8aace45c`；非作者 DEV-002 已执行 Merge Commit `997e50e10a7964b60fc8d9b4357c6274df8f0e97`。TASK-008 治理闭环完成，可按依赖矩阵解锁下游；Stage 6 仍须独立批准。

## TASK-005 PR #37 合并后治理收尾候选（2026-07-24）

- 集成：PR #37 获批 HEAD `cac10a06d2ef48914c14fb7ad955cedb36878acd` 已由 DEV-001 在项目负责人授权后手动 Merge Commit `58fc0b12db1298333eef52c8720ec7d3d5e4846c` 合入 `codex/stage-05-integration`；第一父为 `ca2a07f5f9f19620568cc75f74c97a2d10ed98d3`，第二父为获批 HEAD。
- 验证：结果树与候选一致；双亲、祖先关系、JSON 和差异检查通过。后端 `284 passed, 12 skipped, 2 warnings`，`pip check`、`compileall`、普通与 validation Compose 配置通过；真实 PostgreSQL 17、MinIO、ClamAV、RAGFlow 和 Compose Worker 验证已完成。
- 结果：项目负责人已确认 PR #47 精确 HEAD `09f9701ee2ed97358b37cfd60ae79f12358acdcb`；非作者 DEV-002 已执行 Merge Commit `6763f1e7199765c08303aa567c3aed40210f7cf7`。TASK-005 治理闭环完成，可按依赖矩阵解锁 TASK-009；Stage 6 仍须独立批准。

## TASK-009 开发启动与复审交接（2026-07-24）

- 开发者/审核者：DEV-002 / DEV-001；分支 `codex/task-009-guidance-diagnosis`，目标 `codex/stage-05-integration`。
- 基线与候选：基于 `e0333e2196fc1db9dba0056021625972576215e2`，PR #49 当前完整 HEAD `a5c5d20ef1936f7690e9fb32d332195561257609`，代码提交 `f78deace39fde732bcea7ec36f9a3f5eea79dfc1`。
- 范围：操作指引两次定向检索/人工降级；报警码具体追问和否定证据；维修前诊断证据门槛；采纳/直接开始；8/24/4 上限；历史案例和知识引用通过受控外部边界。
- 证据：Agent API 与 Runtime `8 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；静态 Agent 检查、compileall、`git diff --check` 通过。
- 未验证：DEV-002 无 Docker 环境，真实 PostgreSQL/RAGFlow/LLM 联调待 DEV-001 执行；未新增生产依赖、迁移、兼容层或通用抽象。
- 下一动作：推送同一任务分支并创建唯一 Draft PR，向 DEV-001 请求绑定完整精确 HEAD 的正式复审。复审前不得请求 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## TASK-009 第二轮 P1 修复交接（2026-07-24）

- 审核基准：PR #49 / HEAD `15a5947f95d52a0044d4ee2978da09cc2509e41e`，结论 `Changes requested`；旧审核不得用于批准或集成。
- 修复提交：`8d4d4c48aaa4ee39d01be4cbb5cb18de374a784c`。
- 修复内容：故障诊断 API 不再信任客户端回传 `session`；服务端以 `DiagnosisDraft` 保存和恢复诊断状态，绑定 `_owner_user_id` 与故障；READY 写入幂等，重复提交返回既有结果，不重复写草稿或成功审计。
- 回归证据：伪造 READY/root cause 的客户端 `session` 请求 422；其他用户访问草稿 403；同 Key 重放/409 冲突覆盖；READY 后不同 Key 重放不新增草稿或 `agent.fault_diagnosis.ready` 审计；既有 `ADOPTED` 开始维修路径通过。
- 验证：聚焦 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。
- 请求动作：推送本证据提交后，以 PR #49 新完整精确 HEAD 请求 DEV-001 复审。当前不申请 Merge 授权、不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第三轮 P1 修复交接（2026-07-24）

- 审核基准：PR #49 / HEAD `4b965715fe6fb6869c14da6b23f6b26479243595`，结论 `Changes requested`；旧审核不得用于批准或集成。
- 修复提交：`e0c058e182d7c29881c3de75403b2ef0eb648de7`。
- 修复内容：故障诊断草稿创建除 `intelligence:agent` 外必须具备 `fault:repair`；`start` 请求不再接受客户端设备型号、症状、描述或数据集；诊断上下文和知识检索范围由服务端故障单、设备事实和 `fault_diagnosis` Agent 配置绑定。
- 回归证据：仅有 `intelligence:agent` 的用户返回 403 且不创建草稿；伪造客户端上下文/数据集返回 422；成功路径检索问题与数据集绑定服务端事实和配置；既有草稿越权、重放、READY 幂等和 `ADOPTED` 采纳路径继续通过。
- 验证：故障诊断定向 `5 passed, 2 warnings`；聚焦 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。
- 请求动作：推送本证据提交后，以 PR #49 新完整精确 HEAD 请求 DEV-001 复审。当前不申请 Merge 授权、不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第四轮 CR-043 基线收敛交接（2026-07-24）

- 审核基准：PR #49 / HEAD `3b8adf2f37e2490c7ec5695bd2e789dd9813fae8`，结论 `Changes requested`；阻断为正式基线尚未同步 CR-043。
- 修复内容：同步 PRD、SPEC、AC-037、需求追踪矩阵、API 契约、CR 台账和 `workflow/state.json`，明确当前设计不实现 `EquipmentGrant` 或设备/工厂行级授权隔离；AC-037 收敛为认证、路由权限、线程/草稿创建者隔离、服务端事实绑定、非法对象不泄露详情和审计。
- 变更边界：未修改 `codebase/`、测试、数据库迁移、依赖、部署或运行时配置；不新增兼容层或通用抽象。
- 验证：`workflow/state.json` JSON 解析、`git diff --check` 和授权冲突词扫描通过；因本次仅治理/基线文档变更，未重跑后端测试。
- 请求动作：推送本证据提交后，以 PR #49 新完整精确 HEAD 请求 DEV-001 复审。当前不申请 Merge 授权、不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第五轮 P1 修复交接（2026-07-24）

- 审核基准：PR #49 / HEAD `ef6bda4ff28147280868b4088ede72e39bebedb3`，结论 `Changes requested`；阻断为生产应用工厂未装配 `RagflowAdapter`，导致真实部署中的操作指引/故障诊断知识检索始终不可用。
- 修复提交：`655d4a2309251fd0bd0ae874787e63b73f35effd`。
- 修复内容：`Settings` 增加 RAGFlow 连接配置；`create_app()` 根据 `RAGFLOW_BASE_URL`、`RAGFLOW_API_KEY` 和 `RAGFLOW_TIMEOUT_SECONDS` 自动创建 `RagflowAdapter + UrllibRagflowTransport` 并写入 `app.state.knowledge_adapter`。显式传入 adapter 的测试/集成路径保持可用。
- 回归证据：新增应用工厂 adapter 装配测试；新增操作指引和故障诊断 API 回归，均使用真实应用工厂、真实 `UrllibRagflowTransport` 和本地 HTTP RAGFlow stub，不再手动写入 `app.state.knowledge_adapter` 或 monkeypatch 知识服务。
- 验证：相关 `16 passed, 2 warnings`；聚焦 `51 passed, 2 warnings`；完整后端 `296 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。真实 live-stack RAGFlow 用例因缺少专用环境为 `1 skipped`。
- 请求动作：推送本证据提交后，以 PR #49 新完整精确 HEAD 请求 DEV-001 复审；真实 RAGFlow 联调仍需 DEV-001 在具备环境时执行。当前不申请 Merge 授权、不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第六轮 P1 Compose 配置修复交接（2026-07-24）

- 审核基准：PR #49 / HEAD `a173233d39d752fe5f025d1423d2038c54b685ba`，结论 `Changes requested`；阻断为 Compose `api` 服务未传入 RAGFlow 配置，容器内 `app.state.knowledge_adapter` 为 `None`。
- 修复提交：`0599bb6de23ddab736b6d2f44a795c8303bee655`。
- 修复内容：`api` 环境现在传递 `RAGFLOW_BASE_URL`、`RAGFLOW_API_KEY` 与 `RAGFLOW_TIMEOUT_SECONDS`；安全模板显式设置超时 `30`。该配置与已合入本 PR 的 `create_app()` adapter 装配逻辑配对，不改变 RAGFlow 服务、业务 API 或权限契约。
- 回归证据：新增 API 服务块/模板超时契约，修复前分别观察到缺失变量和缺失模板值的红灯；修复后相关 `18 passed, 2 warnings`，完整后端 `296 passed, 12 skipped, 2 warnings`，14 项原型静态检查、编译和差异检查通过。
- 未验证：DEV-002 无 Docker 命令与专用 live-stack 配置，未执行 Compose 容器内 `RagflowAdapter` 断言、`/healthz` 或真实 TASK-009 RAGFlow 检索。请 DEV-001 对推送后的精确 HEAD 运行这些复验；`test_task005_live_stack.py` 在此环境为 `1 skipped, 2 warnings`。
- 门禁：当前不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## TASK-010 前端集成候选交接（2026-07-27）

- 开发者/审核者：DEV-002 / DEV-001；唯一 Draft PR #50，分支 `codex/task-010-frontend-integration`，目标 `codex/stage-05-integration`。代码检查点为 `76d348620859e8931fed40bf316d4f94131b28ad`；请在推送治理证据后以 PR #50 的完整精确 HEAD 复审，不得把本父提交当作最终候选。
- 已实现：前端改用既有维护和 Agent API；人工/AI 故障上报、健康分、分阶段诊断、服务端草稿证据、直接/采纳维修、结构化维修摘要、操作指引引用和 Agent Runtime SSE。权限或 AI/流式不可用时保留人工路径。
- 本地证据：前端 Vitest `22 passed`，生产构建通过，14 项静态回归通过，`git diff --check` 通过。
- 边界与待验：无后端、迁移、部署、生产依赖、原型或智能配置页修改；无兼容层或新通用抽象。DEV-002 未执行真实认证浏览器 E2E、Docker/PostgreSQL/RAGFlow/LLM live-stack；请 DEV-001 在最终 HEAD 上核验。
- 门禁：此交接只请求正式复审，非 Merge 授权。未获审核与后续集成批准前，不合并、不解锁 TASK-011、不进入 Stage 6。

## TASK-010 Bearer 认证 P1 修复交接（2026-07-27）

- 审核反馈：PR #50 旧 HEAD `ec4e7be630f7bd40dc48ac731aba042e59993225` 未将浏览器登录态送至需要 Bearer 的业务、Agent 和 SSE 路由，真实调用会得到 `401 UNAUTHENTICATED`。
- 修复提交：`aac8ac098465da3792ffbee11caa73d5ee16bc9e`；前端 API 边界从 `sessionStorage.access_token` 读取既有登录态，统一注入 Bearer 请求头，JSON 与 SSE 共用该路径；没有 token 时不伪造凭据。
- 证据：JSON、SSE 请求头回归均通过；API 专项 `10 passed`，前端全量 `23 passed`，生产构建、14 项静态回归、JSON 与完整 diff-check 通过。
- 下一动作：推送本证据后，以 PR #50 新完整精确 HEAD 请求 DEV-001 重审。仅为代码复审，非 Merge 授权；不合并、不解锁 TASK-011、不进入 Stage 6。

## TASK-010 登录与受保护路由 P1 修复交接（2026-07-27）

- 审核反馈：PR #50 旧 HEAD `654439d8579d20ad67878607febc74e50bf652df` 的 token 没有正式生产写入路径；首次用户会在所有受保护路由得到 401。
- 项目负责人授权：允许在同一 PR 增加最小 `/login`、登录 API、会话 token 写入、未认证保护和登录后 JSON/SSE Bearer 交互回归。
- 修复提交：`aef11599b0b820e7781abb5cb7faa83d8cb5b8b1`。登录成功写入 `sessionStorage.access_token` 后返回原路径；无 token 统一重定向登录；JSON/SSE Bearer 继续通过单一 API 边界读取该 token。
- 证据：API 专项 `11 passed`，前端全量 `26 passed`，生产构建、14 项静态回归、JSON 解析和完整 diff-check 通过。
- 待 DEV-001：在本证据提交推送后的最终精确 HEAD 上复审；真实账号浏览器 E2E 和 Docker/PostgreSQL/RAGFlow/LLM live-stack 尚未由 DEV-002 执行。仅请求复审，非 Merge 授权；不合并、不解锁 TASK-011、不进入 Stage 6。

## TASK-009 第八轮 P1 可执行探针修复交接（2026-07-26）

- 审核基准：PR #49 / HEAD `cc643881c251bddc37bb4ae83564b7e14a79a853`，结论 `Changes requested`；DEV-001 用专用 RAGFlow Key 复现 PowerShell/Docker 传参破坏多行 Python 源码并在检索前 `SyntaxError`。
- 修复提交：`913cb44b262e34e7d49e25162a1fb5bf3bfe113f`。
- 修复内容：移除 here-string 与 `python -c` 组合，新增 API 镜像内 `app.modules.knowledge.ragflow_probe`，由验证脚本以 `python -m` 运行，避免任何 Python 源码跨 PowerShell 原生命令参数边界。
- 回归证据：修复前 `2 failed, 1 passed`；修复后实际子进程运行探针并验证认证请求，相关 `20 passed, 2 warnings`；完整后端 `297 passed, 12 skipped, 2 warnings`；14 项静态回归、编译、JSON 和差异检查通过。
- 待 DEV-001：在 PR #49 推送后的最终精确 HEAD 上，用 Windows PowerShell、Docker 和专用 RAGFlow Key 重跑完整 live-stack，并复核 Compose、API 容器探针、adapter、`/healthz` 与真实 TASK-009 检索。
- 门禁：仅请求重新审核，不请求 Merge 授权；不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第九轮 live Agent 验证交接（2026-07-27）

- 审核基准：PR #49 / HEAD `42207a8093bb34ac7d63fb3f9e429585ede443d3`，结论 `Changes requested`；唯一 Important 为缺少真实 RAGFlow 经 TASK-009 API 路由的引用和不可用降级证据。
- 测试提交：`36c3bbd07f4033aabda4e43ff3f5ee9178696ce7`。
- 新增证据路径：现有隔离 live-stack 在真实文档 READY 后调用 `/api/agent/operation-guidance`，验证真实 chunk 引用及唯一文档标记；随后以不可达 adapter 调用同一路由，验证 `UNAVAILABLE`、人工回退和零伪引用。
- 自动执行：`Invoke-Validation.ps1` 已运行包含该用例的 `test_task005_live_stack.py`，继续负责临时 dataset、业务数据、对象、容器、网络和卷清理。
- 本地结果：相关 `7 passed, 1 skipped, 2 warnings`；完整后端 `297 passed, 12 skipped, 2 warnings`。live 项在 DEV-002 环境按设计跳过，必须由 DEV-001 用专用 Key 在最终 HEAD 上实际执行。
- 门禁：仅请求重新审核和 live-stack 复验，不请求 Merge 授权；不合并、不解锁 TASK-010/011、不进入 Stage 6。

## TASK-009 第七轮 P1 API 容器连通性修复交接（2026-07-24）

- 审核基准：PR #49 / HEAD `f920af89f7fbaefbb1f5547582ed4d44b44005ef`，结论 `Changes requested`；API 容器缺少 `host.docker.internal` 的 Linux host-gateway 映射，不能解析宿主机 RAGFlow。
- 修复提交：`a25f32f90ddf812c7cc75c1a940d09d5077a2eb5`。
- 修复内容：API 现在配置 `host.docker.internal:host-gateway`，并加入已有的 `ragflow-egress`；安全验证环境提供超时变量。live-stack 脚本从 API 容器读取生产 RAGFlow 配置，执行 DNS 解析及 Bearer 认证的 `/api/v1/datasets` 请求，失败会阻断验证。
- 回归证据：新增静态 Compose/脚本契约先失败后转绿；相关 `18 passed, 2 warnings`，完整后端 `296 passed, 12 skipped, 2 warnings`，14 项原型静态检查、编译和差异检查通过。
- 未验证：DEV-002 环境没有 Docker 或 PowerShell，尚未执行真实 Compose 重建、API 容器 `/healthz`、adapter 断言和 RAGFlow 实际检索。请 DEV-001 对推送后的精确 HEAD 执行这些复验，再决定是否可重新批准。
- 门禁：当前不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。
## CR-048 治理候选合并后正式启动通知（2026-07-31）

- PR #73 已按授权合入 `codex/stage-05-integration`。
- 获批 HEAD：`b4e28368c1294f30b80f4dd72187660eba06fc10`；Merge Commit：`8d9beaefe01baef38e54baecbe3426d9ab816623`。
- 合并后验证：双亲、目标分支、`git diff --check`、`workflow/state.json` 解析通过；Python 3.13 后端 `319 passed, 13 skipped, 2 warnings`。
- 正式请求：请项目负责人 DEV-002 确认已收到 TASK-012 开发启动通知。确认后 DEV-002 才可创建唯一 Draft PR `codex/task-012-p0-frontend-remediation`；API-002—007、P0 前端和 Stage 6/7/8 在确认前继续锁定。
## TASK-012 complete defect inventory handoff (2026-07-31)

- DEV-001 reviewed PR #75 exact HEAD `77a54a1587544374ed876e902bc132d58cf8ed9b` and recorded `Changes requested`.
- The complete inventory is `06-testing/DEFECTS.md`, DEF-TASK012-001 through DEF-TASK012-037. It includes prior P1 findings and additional permission, data-loss, filtering, interaction, duplicate-submit, and test-evidence findings.
- DEV-002 must fix the applicable items in the same TASK-012 development PR. This governance PR is only the review/evidence handoff and does not fix or close any defect.
- Until a new exact HEAD is reviewed and integration-checked, PR #75 must not be merged and TASK-012, Stage 6/7/8 remain locked.
- Second-pass additions are DEF-TASK012-038 through DEF-TASK012-040; DEV-002 must include them in the same remediation cycle.

## TASK-012 third-pass review handoff (2026-08-03)

- DEV-001 reviewed PR #75 exact HEAD `989e23481f071a46ee164c9595434d703d8a3a1f`; result remains `Changes requested`.
- New open findings are DEF-TASK012-041 through DEF-TASK012-046: operation-guidance idempotency, Global Agent two-step/orphan and in-flight handling, unsafe manual fallback on order-load failure, overly strict page gates, incomplete SSE framing/error parsing, and missing production/live-stack evidence.
- DEV-002 must remediate these in the same PR #75 and submit a new exact HEAD for whole-candidate review.
- PR #75 must not be merged; TASK-012 and Stage 6/7/8 remain locked. This governance PR contains no business-code fix.
