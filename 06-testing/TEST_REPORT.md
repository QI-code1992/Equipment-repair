# 测试报告

- 状态：生产验证受阻
- 精确 Commit SHA：无
- 正式迁移后的原型静态检查：通过。
- 指标检查已改为检查可见的只读指标弹窗，而不是过期且不可达的编辑实现字符串；当前 40 项指标只读要求不变。
- 生产测试执行情况：尚未执行。

## TASK-011 第二轮复审修复（2026-07-27）

- 候选 HEAD：`8e6ba04d2128586060db17e746c4230db266c5bc`（后续编排脚本提交后必须重新填写）。
- 已通过：附件受控临时文件扫描/存储专项 `15 passed, 2 warnings`；Nginx 静态入口契约通过。
- 已实现但未执行：`codebase/infra/scripts/verify-platform-readiness.ps1` 会在显式提供隔离 env、随机 live 项目、HTTPS 地址与备份目录时执行 HTTPS、端口隔离、RAGFlow 探针、真实 Agent 降级、重启和备份恢复。
- BLOCKED：当前 Windows Docker Compose 环境未实际发布已声明的 loopback HTTPS 端口，无法在宿主机运行上述完整 E2E；不得将该项记为通过。需要修复 Docker Compose 端口发布后，以新精确 HEAD 重跑并记录结果。
- 复现证据：Docker Engine `29.6.1`、Compose `v5.1.4`；Nginx 容器的 `HostConfig.PortBindings` 为 `127.0.0.1:8443 -> 443`，但 `NetworkSettings.Ports` 为 `{"443/tcp":[]}`，宿主机 curl 连接失败。以短格式与长格式 Compose ports 均复现；此前等价 `docker run -p 127.0.0.1:8443:80` 可发布并返回 200。因此阻断位于 Compose→Docker 运行态端口发布层，而非 Nginx、证书或端口占用。
- 后续处置与真实结果：升级 Docker Desktop 后确认根因是 Nginx 仅在 `internal: true` 的 `platform` 网络；增加仅供 Nginx 使用的非 internal `ingress` 网络后，`127.0.0.1:18444 -> 443` 实际发布，HTTPS `/healthz` 200，HTTPS E2E 通过。API 重启后动态解析 Docker DNS，HTTPS 再次 200。`backup.ps1` 与随机 `equipment-task011-restore-c7d91e2f` 的真实恢复均通过。
- 仍 BLOCKED：真实 Agent/RAGFlow 路径需要 `TASK005_ALLOW_LIVE_TESTS=1` 及专用 RAGFlow 数据集配置；当前临时环境缺少该配置，容器 validator 的 live 测试明确 `skipped`。不得以 RAGFlow probe 或普通 PostgreSQL 验证替代该证据。
