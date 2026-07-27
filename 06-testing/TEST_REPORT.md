# 测试报告

- 状态：生产验证受阻

## TASK-011 合并后最终验证与治理收尾候选（2026-07-27）

- 合并基准：`b1e4ea6c409946667e22e4bff427c4dccaa86f22`，父提交为 `22f619f…` 与授权源 HEAD `f3150a27441b0e8e4308cdcc7a06a5357ca702e7`；PR #54 已合并至 `codex/stage-05-integration`。
- 合并后回归：`python -m pytest -q`（`codebase/backend`）为 `309 passed, 13 skipped, 2 warnings`；前端测试 `26 passed`，生产构建通过；14 项静态回归、`compileall`、`docker compose ... config --quiet`、`git diff --check`（两父提交）均通过。
- 真实 live-stack：在授权源 HEAD 上的 `verify-platform-readiness.ps1` 通过：PostgreSQL 迁移回归 `1 passed, 3 warnings`、真实 RAGFlow Agent 成功/`UNAVAILABLE` 降级路径 `1 passed, 2 warnings`、HTTPS E2E `1 passed`、API 重启恢复、备份与随机隔离恢复 `equipment-task011-restore-05b381455286` 均通过。
- 清理与限制：临时 RAGFlow 数据集已通过 API 删除并复核不存在；无生产密钥、数据或卷被提交。Stage 6 独立测试、Stage 7 验收及生产发布均未获批准。
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
