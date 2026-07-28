# 测试报告

- 状态：Stage 6 独立测试进行中；静态全局审查与 PR #61 合并后的核心运行态验证已完成。性能边界、最终独立质量结论、Stage 7 验收及生产发布均未完成或获批。

## Stage 6 运行态性能边界与降级复验（2026-07-28，候选 `931df829877305d6ee51a3cef871fe7a9735b9e2`）

- SUT：`931df829877305d6ee51a3cef871fe7a9735b9e2`；压测工具：`93df55f6b124d00f140bd11cc303f5682f8c9c1b`。操作指引将设备型号、症状和描述合并为一次定向检索；实际检索总数不超过两次，避免以重试突破规格上限。
- 环境：Windows Docker Desktop 的两个隔离 Compose 项目。成功路径通过 `https://127.0.0.1:18450` 调用专用 RAGFlow 数据集；故障路径通过 `https://127.0.0.1:18451`，仅将该项目的 `RAGFLOW_BASE_URL` 指向 `host.docker.internal:1`。两者均使用专用 PostgreSQL、MinIO、ClamAV、临时用户和本地自签名 TLS，未连接生产资源。`--insecure-tls` 仅用于该本机自签名测试环境。
- 并发与阈值：每个业务场景总计 300 秒，依次运行 1、2、5、10 并发，最大并发为 10；认证与附件 P95 阈值 1 秒，两个 Agent 场景 P95 阈值 15 秒。每份结果 JSON 均记录 SUT、工具、环境和夹具，不含令牌、口令或密钥。
- 认证：`results-auth-v2.json` 为 43,938 次、零意外错误，P95 为 32.70、33.11、41.25、71.63 ms。
- 附件：`results-attachment-v2.json` 为 15,233 次、零意外错误，P95 为 47.87、55.88、110.58、225.28 ms，覆盖 HTTPS、ClamAV 和 MinIO。
- 真实 RAGFlow 成功路径：`results-agent-success-final-v2.json` 为 1,204 次，均为 `QUESTIONING` 且每次都有非空引用，零意外错误，P95 为 2,021、1,928、1,372、2,219 ms。
- 受控降级路径：`results-agent-unavailable-v2.json` 为 22,422 次，均为 `UNAVAILABLE`、每次零引用，零意外错误，P95 为 46.79、44.82、71.04、148.77 ms。
- 历史结果处置：先前的 `f6a188…` / `6725bb…` 结果存在阈值、夹具或候选 SHA 追溯不足，均不作为本段通过证据。
- 备份恢复：首次包含 15,525 个附件压测遗留对象的恢复耗时约 194.7 秒，已保留为对象数量边界发现，不能用作受控性能基线。随后在新的隔离项目中创建 1 个 API 实际写入的附件对象并重测：备份 3.578 秒、随机恢复项目 `equipment-task011-restore-bkp9d7d41` 恢复 10.584 秒，两个脚本均退出码 0。恢复期间固定运行 10 并发认证只读请求 60 秒，`results-backup-restore-readonly.json` 记录 12,443 次请求、零意外错误、P50 43.29 ms、P95 76.64 ms，满足恢复不超过 180 秒和只读 P95 不超过 2 秒的受控门槛。
- 当前候选静态复核：Gitleaks 工作树扫描、Semgrep、Trivy（HIGH/CRITICAL）与 CodeQL 2.26.1 Python/JavaScript 安全套件均已执行；CodeQL 两份 SARIF 均无结果。Trivy 仍仅报告已处置的 `react-router` `GHSA-qwww-vcr4-c8h2`，不得将该历史风险处置改写为依赖已升级。
- 当前结论：认证、附件、真实 RAGFlow 成功、真实 `UNAVAILABLE` 降级、重启后的容器运行态，以及受控备份恢复/10 并发只读组合验证均通过。本报告仍不自行作 Stage 6 整体通过结论，也不放行 Stage 7；须经 DEV-002 对当前 PR 候选审核，并由 DEV-002 单独作出 Stage 6 Gate 决定。

## Stage 6 PR #61 合并后核心运行态验证（2026-07-28）

- 合并基线：`codex/stage-05-integration` 的 Merge Commit `144ad1ac5802dcbe53a55a426f46ce9bef8eba0f`；双亲为此前集成 HEAD `e32478e20c0f27558356d4f0e7d5a6d4c8eba477` 与获授权 PR #61 HEAD `b73311cfd3beebe048c5ef64320886ccdea363e0`。
- 环境边界：Windows Docker Desktop 的隔离 Compose 项目、专用 PostgreSQL/MinIO/ClamAV、专用 RAGFlow 数据集和本地自签名 HTTPS；未连接生产数据库、对象存储或生产密钥。临时浏览器用户、Compose 项目、备份目录与 RAGFlow 数据集不得纳入仓库或作为生产数据。
- 前端与静态：`npm ci`、前端 `26 passed`、生产构建和 Nginx 配置契约通过；15 项 `06-testing/tests/*.test.js` 全部通过。依赖安装仍报告既有两项 high severity，未执行自动升级；其 React Router 适用性处置继续受已记录的 BrowserRouter SPA 边界约束。
- 真实运行态：`verify-platform-readiness.ps1` 在该 Merge Commit 上通过，包含真实 HTTPS 根入口的哈希 `.js/.css` 响应头断言、PostgreSQL 迁移 `1 passed, 3 warnings`、真实 Agent/RAGFlow 成功及 `UNAVAILABLE` 降级 `1 passed, 2 warnings`、HTTPS E2E `1 passed`、API 重启恢复、备份及随机隔离恢复 `equipment-task011-restore-393052f7ebe3`。
- 浏览器：真实 Chromium/Edge 无头会话验证未认证访问重定向 `/login`，登录后会话令牌写入，且 `/intelligent-config`、`/fault-report` 两个受保护路由可访问。
- 结论与未完成项：PR #61 的 MIME P1 已在合并结果验证关闭；但性能/负载边界尚未执行，最终独立质量结论、Stage 7 验收及生产发布均仍需各自门禁，不得由本记录自动放行。

## Stage 6 静态全局复扫（2026-07-28）

- 基线：`codex/stage-05-integration`，Merge Commit `20dde0449f5fb4aadb99e0c008fe0f751b8b5b63`；该提交的双亲为 `138fc8858b19ab84a58816455c490099db53dbe8` 与经授权修复 HEAD `4f88415c02644e69ecf5ffe277210330158f1e14`。
- 执行边界：仅执行静态工具和 Node 静态用例；未启动 Docker、RAGFlow、数据库、浏览器 E2E 或外部模型。
- 静态用例：全部 `06-testing/tests/*.test.js` 通过（15 项，含 React Router RSC 风险边界用例）。
- CodeQL 2.26.1：Python 安全与质量套件扫描 136 个 Python 文件，62 项均为未使用导入/迁移元数据、类型注释识别或控制流保守分析等质量提示；未发现新的生产安全规则结果。JavaScript/TypeScript 安全扩展套件扫描 34 个文件，19 项均位于 `03-ui-prototype/`，其中 18 项为原型页面对本地表单/文件名的 DOM HTML 重渲染路径，1 项为无效替换表达式；正式 `codebase/frontend/` 无 CodeQL 安全命中。
- Semgrep 1.171.0：扫描 238 个 Git 跟踪文件、520 条规则，13 项。生产目录中的 Docker root 告警不适用：最终 `production` stage 已创建并使用 `appuser`，Trivy 也未报 root 运行。RAGFlow `urllib` 告警已由两处 HTTP(S)+hostname 校验和受控部署配置边界缓解；Nginx 动态上游为固定 `api:8000`，`/api/` 与 SSE 是受后端 Bearer/权限保护的公开业务入口，不应加 `internal`。其余命中均在 Stage 3 原型，见下方残余风险。
- Gitleaks 8.30.1：当前工作树无泄露；完整历史扫描 362 个提交，有两项 `curl-auth-user` 命中，均为 `ELASTIC_PASSWORD` 环境变量引用，不是硬编码密码或 Token，报告中未保留秘密值。
- Trivy 0.72.0：无秘密；依赖保留 `GHSA-qwww-vcr4-c8h2`（`react-router` 7.18.1，HIGH），适用性按项目负责人已批准的 BrowserRouter SPA 风险处置执行。Dockerfile 仅有 LOW `DS-0026`（未声明 `HEALTHCHECK`）；当前健康证据由 Compose/运行态 `/healthz` 演练提供，仍建议后续将镜像级健康检查纳入独立低优先级加固，不阻断本轮静态复扫。

### 静态审查残余风险与结论

- P2 / 原型路径边界：`03-ui-prototype/prototype/local-server-4209.js` 是仅绑定 `127.0.0.1` 的 Stage 3 本地预览服务器；路径已 `normalize` 并拒绝离开根目录，但 `startsWith(root)` 对同前缀兄弟目录不是稳健边界。不得将该服务器用于共享或生产部署；若需要发布原型，必须回到 Stage 3，改用相对路径校验并重新评审。
- P2 / 原型供应链：两个 Stage 3 HTML 页面通过 CDN 加载资源但未声明 SRI。正式前端构建不使用这些页面；若原型需要对外托管，必须在 Stage 3 处理 SRI 或本地锁定资源并重新评审。
- 不把上述原型风险或 Trivy LOW 建议写作已关闭；它们不构成当前正式 `codebase/` 的 Critical/Important 阻断。PR #59 的 Docker 非 root、TLS 限制、RAGFlow URL 约束和错误信息脱敏在当前合并基线仍有效。
- 结论：静态全局复扫已完成，生产代码未发现新的 Critical/Important 静态安全阻断；但 Stage 6 整体仍未通过，必须继续完成真实 RAGFlow、容器/依赖运行验证、浏览器 E2E 和最终独立测试报告。

## Stage 6 静态风险处置：GHSA-qwww-vcr4-c8h2（2026-07-28）

- 依赖告警：Trivy/NPM 报告 `react-router-dom` 间接依赖 `react-router` 的 HIGH `GHSA-qwww-vcr4-c8h2`。公告所称修复版本 `8.3.0` 当前不存在；npm 可用的最新稳定版为 `7.18.1`，不得伪造升级结论。
- 可达性证据：正式前端由 Vite 启动，入口使用 `BrowserRouter`、`Routes` 与 `Route`；仓库未使用 React Router RSC、SSR、route `action`、`loader` 或服务端 React Router。
- 项目负责人风险处置：接受该公告在当前 Vite BrowserRouter SPA 架构下不适用；不得引入 React Router RSC、SSR、route action/loader 或服务端 React Router。若任一条件变化，必须重新评估风险并升级依赖。
- 回归：`06-testing/tests/react-router-rsc-risk.test.js` 断言上述架构边界。

## TASK-011 合并后最终验证与治理收尾（2026-07-27）

- 合并基准：`b1e4ea6c409946667e22e4bff427c4dccaa86f22`，父提交为 `22f619f…` 与授权源 HEAD `f3150a27441b0e8e4308cdcc7a06a5357ca702e7`；PR #54 已合并至 `codex/stage-05-integration`。
- 合并后回归：`python -m pytest -q`（`codebase/backend`）为 `309 passed, 13 skipped, 2 warnings`；前端测试 `26 passed`，生产构建通过；14 项静态回归、`compileall`、`docker compose ... config --quiet`、`git diff --check`（两父提交）均通过。
- 真实 live-stack：在授权源 HEAD 上的 `verify-platform-readiness.ps1` 通过：PostgreSQL 迁移回归 `1 passed, 3 warnings`、真实 RAGFlow Agent 成功/`UNAVAILABLE` 降级路径 `1 passed, 2 warnings`、HTTPS E2E `1 passed`、API 重启恢复、备份与随机隔离恢复 `equipment-task011-restore-05b381455286` 均通过。
- 清理与限制：临时 RAGFlow 数据集已通过 API 删除并复核不存在；无生产密钥、数据或卷被提交。Stage 6 独立测试、Stage 7 验收及生产发布均未获批准。
- 收尾记录：治理 PR #55 已合入 `53bdf90ec8ab743165d0542099a15d3c9de598b3`，使 TASK-011 台账状态与已合并事实一致；不构成 Stage 6 批准。
- 精确 Commit SHA：无
- 正式迁移后的原型静态检查：通过。
- 指标检查已改为检查可见的只读指标弹窗，而不是过期且不可达的编辑实现字符串；当前 40 项指标只读要求不变。
- 生产测试执行情况：尚未执行。

## TASK-011 第二轮复审修复（2026-07-27）

- 历史候选 HEAD：`8e6ba04d2128586060db17e746c4230db266c5bc`（该轮结果仅保留为第二轮修复记录，不作为最终 live-stack 证据）。
- 历史已通过：附件受控临时文件扫描/存储专项 `15 passed, 2 warnings`；Nginx 静态入口契约通过。
- 历史实现状态：`codebase/infra/scripts/verify-platform-readiness.ps1` 已具备在显式提供隔离 env、随机 live 项目、HTTPS 地址与备份目录时执行 HTTPS、端口隔离、RAGFlow 探针、真实 Agent 降级、重启和备份恢复的编排能力。
- 历史阻断：当时 Windows Docker Compose 环境未实际发布已声明的 loopback HTTPS 端口，无法在宿主机运行完整 E2E；该阻断已在下方绑定证据中解除。
- 复现证据：Docker Engine `29.6.1`、Compose `v5.1.4`；Nginx 容器的 `HostConfig.PortBindings` 为 `127.0.0.1:8443 -> 443`，但 `NetworkSettings.Ports` 为 `{"443/tcp":[]}`，宿主机 curl 连接失败。以短格式与长格式 Compose ports 均复现；此前等价 `docker run -p 127.0.0.1:8443:80` 可发布并返回 200。因此阻断位于 Compose→Docker 运行态端口发布层，而非 Nginx、证书或端口占用。
- 后续处置与真实结果：升级 Docker Desktop 后确认根因是 Nginx 仅在 `internal: true` 的 `platform` 网络；增加仅供 Nginx 使用的非 internal `ingress` 网络后，`127.0.0.1:18444 -> 443` 实际发布，HTTPS `/healthz` 200，HTTPS E2E 通过。API 重启后动态解析 Docker DNS，HTTPS 再次 200。`backup.ps1` 与随机 `equipment-task011-restore-c7d91e2f` 的真实恢复均通过。
- 历史阻断：真实 Agent/RAGFlow 路径曾因缺少专用 RAGFlow 数据集配置而 `skipped`；该状态已在下方绑定证据中解除。不得以 RAGFlow probe 或普通 PostgreSQL 验证替代真实 Agent 证据。
- TASK-011 最终真实 live-stack 验证（2026-07-27）：通过。以临时专用 RAGFlow 数据集运行 `tests/integration/test_task005_live_stack.py`，真实 Agent 路由成功路径与 `UNAVAILABLE` 降级路径均已执行，结果 `1 passed, 2 warnings`；临时文档由测试清理，临时数据集随后通过 API 删除并复核不存在。
- 同次 `verify-platform-readiness.ps1`：通过。PostgreSQL 迁移回归 `1 passed, 3 warnings`、HTTPS E2E `1 passed`、API 重启后 HTTPS 健康检查恢复、备份与随机隔离恢复项目 `equipment-task011-restore-92603b700b09` 均通过。脚本现要求 `RagflowDatasetId`，并将 live Agent 测试的跳过结果视为失败，不能再以探针或普通数据库测试替代。

## TASK-011 最终验证证据绑定（2026-07-27）

- PR 验证候选 HEAD：`1bcb70d2b0bb154c230180c53570940bcfa33311`；目标分支：`codex/stage-05-integration`。本段记录的命令均在该候选上执行；后续提交仅补充本证据文本，不改变已验证的应用、部署或测试代码。
- 真实 RAGFlow Agent：先创建一次性专用数据集，再运行 `docker compose --profile validation --env-file <redacted> -p equipment-task011-live-b7c91d2e -f codebase/infra/docker-compose.yml run --rm -e TASK005_RAGFLOW_DATASET_ID=<temporary-id> validator python -m pytest tests/integration/test_task005_live_stack.py -q -rs`，结果 `1 passed, 2 warnings`。覆盖真实文档写入、RAGFlow 检索、`POST /api/agent/operation-guidance` 成功引用与 `UNAVAILABLE` / `manual_fallback=true` 降级路径；测试文档与临时数据集均已删除并复核不存在。
- 完整 live-stack：运行 `powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/scripts/verify-platform-readiness.ps1 -EnvFile <redacted> -ProjectName equipment-task011-live-b7c91d2e -LiveHttpsUrl https://127.0.0.1:18444 -RagflowDatasetId <temporary-id> -BackupOutputDirectory <temporary-dir>`，结果 `TASK-011 platform readiness: PASS`。其中 PostgreSQL 迁移回归 `1 passed, 3 warnings`、真实 Agent/RAGFlow `1 passed, 2 warnings`、HTTPS E2E `1 passed`；API 重启后 HTTPS 健康检查恢复；备份及隔离恢复项目 `equipment-task011-restore-92603b700b09` 通过。
- 本地回归：`python -m pytest codebase/backend/tests/modules/test_attachment_api.py -q` 为 `12 passed, 2 warnings`；`python -m pytest -q`（在 `codebase/backend`）为 `309 passed, 13 skipped, 2 warnings`；`python -m compileall -q codebase/backend/app`、`codebase/infra/tests/verify-backup-contract.ps1` 与 `git diff --check` 均通过。13 个跳过项为未配置的 opt-in/live 环境测试；最终 RAGFlow 证据不在跳过项中。
