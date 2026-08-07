# 运维手册（候选版）

- 状态：TASK-004 RAGFlow 基础设施候选已具备；须经 DEV-002 审核和正式合入后生效。
- 原型资产：`03-ui-prototype/prototype/local-server-4209.js`
- 原型命令：`node 03-ui-prototype/prototype/local-server-4209.js`
- 原型地址：`http://127.0.0.1:4209/pages/intelligent-config.html`
- 本节不代表 Stage 6 准入；监控、完整备份恢复演练和生产发布仍未完成。

## 当前业务平台测试部署边界（2026-08-05）

- 当前平台测试环境位于阿里云 ECS，运行代码绑定 `780748cbc6b988feda66f2ebd02a6829bdafd1c1`，Compose 项目为 `equipment-preview-77fbc42`。该环境只用于业务平台测试，不是生产发布，也不代表 Stage 6/7/8 已通过。
- ECS 仅运行平台 PostgreSQL、Redis、MinIO、ClamAV、API、Worker、Validator、Nginx 和 Web。RAGFlow 必须留在本地 Windows Docker Desktop/WSL2，统一目标版本为 `v0.26.3`；ECS 仅经项目负责人维护的加密私网隧道访问 RAGFlow API。
- 测试公网入口、短期自签名证书、已验证范围和未验证 RAGFlow 成功链路见 `07-acceptance/ACCEPTANCE_ENVIRONMENT_DEPLOYMENT.md`。不得把管理员凭据、RAGFlow API Key、隧道参数、证书私钥或 `.env` 内容写入本手册。
- 当前 ECS 未配置运行时 `RAGFLOW_API_KEY`，因此真实 RAGFlow 检索成功路径尚未验证；不得以服务健康或不可用降级替代成功链路证据。

### TASK-013 推送自动同步

- `codebase/infra/scripts/ecs-test-autodeploy.sh` 由 `equipment-test-autodeploy.timer` 每 30 秒检查 `codex/task-013-prototype-fidelity-remediation` 的已推送 Commit；未提交的本地保存永不进入 ECS。
- 每个新 SHA 先在新的预览目录构建 API/Web 镜像，再重建 API/Web 并检查外层入口 `https://127.0.0.1/healthz`。构建、启动或健康检查失败时，脚本恢复预先保留标签的上一 API/Web 镜像和原预览目录；不执行数据库 downgrade，不删除 PostgreSQL、Redis、MinIO、ClamAV 或 RAGFlow 数据。
- 自动部署拒绝包含 Alembic 迁移变化的 Commit，要求人工执行并单独验证，避免测试数据库前向迁移后无法安全回退。
- ECS 上的 `/etc/equipment-test-autodeploy.env` 只保存非秘密路径、分支和项目名；不得放入 SSH 私钥、账号密码、RAGFlow Token 或 `.env` 内容。服务日志通过 `journalctl -u equipment-test-autodeploy.service` 查看，只应包含时间、SHA 和脱敏错误。

## TASK-004 RAGFlow 运行前置条件

- Docker Desktop 使用 Linux containers；Docker Engine `>=24`，Docker Compose `>=2.26.1`。
- 主机至少 4 CPU、16 GB RAM、50 GB 可用磁盘；Elasticsearch 默认内存上限为 4 GB。
- WSL2/Linux 的 `vm.max_map_count` 应不低于 `262144`。使用 `wsl -d docker-desktop sysctl vm.max_map_count` 检查；如不足，由运维人员按环境策略人工设置，仓库脚本不会修改系统全局配置。
- 运行前复制 `codebase/infra/.env.example` 为 Git 忽略的 `codebase/infra/.env.local`，并替换所有 `change-me` 值。不得提交、打印或发送真实密码、Token、Cookie 和密钥。
- 若本机 `8080` 或 `9380` 已占用，在本地环境文件中修改 `RAGFLOW_HTTP_PORT` 或 `RAGFLOW_API_PORT`；依赖容器不得增加宿主机端口映射。

## 配置、启动与验证

以下 Compose 命令以及会调用 Compose 的健康、持久化脚本显式绑定同一个 Git 忽略本地环境文件，禁止在真实验证时回退到 `.env.example`。网络隔离脚本只检查已启动容器和 Docker 网络，不读取 Compose 环境文件。

```powershell
$RagflowEnvFile = "codebase/infra/.env.local"
if (-not (Test-Path -LiteralPath $RagflowEnvFile -PathType Leaf)) { throw "Missing local RAGFlow environment file" }

docker compose --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml config --quiet
docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml up -d
powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/ragflow/scripts/verify.ps1 -EnvFile $RagflowEnvFile
powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/ragflow/scripts/verify-isolation.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/ragflow/scripts/verify-persistence.ps1 -EnvFile $RagflowEnvFile
docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml down
```

`verify.ps1` 必须确认 5 个容器均为 healthy、Web 返回 HTTP 200、API `GET /api/v1/system/version` 在有限重试窗口内返回 `code=0` 和 `data=v0.26.3`、Elasticsearch 为 `8.11.3` 系列，并逐一绑定展开 Compose 镜像、固定标签获批 SHA-256 和运行容器镜像 ID；任一漂移必须失败。本次执行窗口内的 RAGFlow 日志还必须没有依赖连接失败或秘密值命中，输出只保留时间、退出码和计数摘要。`verify-isolation.ps1` 必须确认四个依赖仅位于内部网络且没有宿主端口。`verify-persistence.ps1` 会通过各存储的正式接口写入随机探针；其中 MinIO 必须经 S3 API 创建临时 bucket/object，重启整栈后回读比对。只有所有断言成功后才自动清理探针；失败时保留调查证据，并由操作者确认后仅清理 TASK-004 命名空间。不得直接读写 `/data` 目录充当对象持久化证据。

常规停止只允许 `down`，禁止使用 `down -v`；后者会删除 TASK-004 命名卷并破坏持久化数据。

## TASK-005 接入契约

```text
Host Web: http://127.0.0.1:${RAGFLOW_HTTP_PORT}
Host API: http://127.0.0.1:${RAGFLOW_API_PORT}
Container API: http://ragflow:9380 on equipment-ragflow-access
Authentication: runtime-only RAGFlow API Token
Dataset creation: owned by TASK-005 through RAGFlow API
Forbidden: direct access to RAGFlow MySQL/Redis/MinIO/Elasticsearch
```

TASK-005 只能消费上述 API 契约，不能读取共享配置中的数据库凭据，也不能直连或修改 RAGFlow 的 MySQL、Redis、MinIO、Elasticsearch。TASK-004 正式集成及合并后验证完成前，TASK-005 继续锁定。

## 恢复、排障与日志边界

- Docker 引擎不可用：先运行 `docker info`，确认 Docker Desktop 已启动且处于 Linux containers 模式。
- 镜像拉取 DNS/TLS 失败：分别验证宿主机 `https://registry-1.docker.io/v2/` 与 Docker 引擎连接；可使用获批的 Docker Hub 透明镜像拉取同一固定版本，再核对镜像 ID/RepoDigest。不得静默改用 `latest` 或不同版本。
- 端口占用：使用 `docker ps` 或 `Get-NetTCPConnection` 定位占用者，改本地 `RAGFLOW_HTTP_PORT`/`RAGFLOW_API_PORT`，不得停止无关服务。
- Elasticsearch 不健康：检查 `docker compose ... logs ragflow-elasticsearch`、内存额度和 `vm.max_map_count`；不得由仓库脚本自动修改宿主机参数。
- 依赖健康超时：使用 `docker compose ... ps` 和单服务 `logs` 定位；日志摘录必须先移除密码、Token、Cookie、Authorization 和连接串。
- 重启恢复：先运行 `verify-persistence.ps1`。失败时保留命名卷和容器日志，不执行带 `-v` 的清理。
- 备份候选：MySQL 逻辑备份、Redis AOF、MinIO 数据目录、Elasticsearch snapshot 分别处理；完整备份恢复演练延后至 TASK-011，TASK-004 不宣称已完成灾难恢复。
