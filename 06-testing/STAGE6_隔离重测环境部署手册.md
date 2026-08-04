# Stage 6 独立重测隔离测试环境部署手册

## 1. 目的、范围与边界

本手册用于部署“新能源装载机设备故障智能运维平台”的 **Stage 6 独立重测隔离环境**，为当前未关闭的 P1 测试阻断项提供可重复、可审计的真实运行环境：

- `DEF-STAGE6-003`：真实知识文档生命周期的分段时序与唯一阻塞组件定位；
- `DEF-STAGE6-004`：受浏览器信任的本地 HTTPS 浏览器 E2E；
- `DEF-STAGE6-005`：1/2/5/10 并发、受控备份/随机恢复及恢复期只读负载。

本环境不是 Stage 7 验收环境，不是生产环境，也不代表任何 Stage Gate 已通过。不得使用生产数据、生产账号、生产密钥、生产证书、生产卷或公网入口；Nginx 必须仅绑定 `127.0.0.1`。

本次唯一系统被测对象（SUT）为：

```text
仓库：QI-code1992/Equipment-repair
分支：codex/stage-05-integration
精确提交：e8a28cee7515ad58e025ec81c65b460284919d75
```

若任何代码、配置或分支 HEAD 变化，已有测试证据均不再适用于新 HEAD，必须重新记录环境、夹具、命令、UTC 时间与结果。

## 2. 环境与角色要求

部署电脑应是专用或可隔离的 Windows 10/11 电脑，具备：

- Docker Desktop，已启用 Linux containers 与 WSL2 后端；
- Windows PowerShell 5.1 或 PowerShell 7；
- Git；
- Python 3.13；
- Node.js 20.19+ 或 22.12+、npm 10+；
- 足够的 Docker 磁盘与内存。RAGFlow 的 Elasticsearch 默认内存限制为 4 GiB，建议 Docker Desktop 至少分配 8 GiB 内存；
- 可在本机安装/信任仅供测试的本地 HTTPS 根证书；
- 可访问镜像仓库和 GitHub。

建议分工：部署执行人负责环境、临时数据、证书和清理；独立测试执行人负责 Stage 6 记录与缺陷结论。两者都不得将密码、Token、私钥或上传附件正文写入仓库、PR、聊天记录或测试报告。

## 3. 启动前安全检查

1. 关闭或隔离任何现有的本项目 Docker 环境，确认本次使用新的 Compose 项目名。
2. 确认没有使用生产数据库、MinIO、RAGFlow、域名、证书或凭据。
3. 准备一个仅用于本次测试的 RAGFlow API Key。将 Key 保存到 **Git 工作区外** 的临时文件，文件内容只能是一行 Key；不要把 Key 粘贴到终端历史、截图或文档。
4. 为本机生成受浏览器信任的临时证书。推荐使用组织批准的本机开发根证书工具（如 `mkcert`）；证书仅覆盖 `127.0.0.1` 或本机测试主机名。禁止使用生产证书或将端口暴露到公网。
5. 创建本次运行记录，至少包含：SUT SHA、执行人、UTC 开始时间、Docker Desktop 版本、浏览器版本、Compose 项目名、回环端口、临时 RAGFlow 数据集 ID、测试账号标识和清理负责人。记录配置文件路径，不记录其中的秘密。

## 4. 获取并固定代码

在 Windows PowerShell 中执行；以下示例将仓库放在 `D:\stage6\Equipment-repair`，可按实际位置替换。

```powershell
git clone https://github.com/QI-code1992/Equipment-repair.git D:\stage6\Equipment-repair
Set-Location D:\stage6\Equipment-repair
git fetch origin codex/stage-05-integration
git switch --detach e8a28cee7515ad58e025ec81c65b460284919d75
git rev-parse HEAD
git status --short
```

最后一条 SHA 必须严格等于 `e8a28cee7515ad58e025ec81c65b460284919d75`，且工作区不得有修改或未跟踪的运行文件。后续运行产生的 `.env.local`、证书、备份和证据应保存到 Git 忽略路径或工作区外。

## 5. 准备本地配置与证书

复制模板，但不要提交生成文件：

```powershell
Copy-Item codebase\infra\.env.example codebase\infra\.env.local
New-Item -ItemType Directory -Force codebase\infra\nginx\certs | Out-Null
```

编辑 `codebase\infra\.env.local`，将所有 `change-me` 值替换为本次随机测试值，并至少满足下列约束：

```dotenv
# 平台隔离资源
POSTGRES_DB=equipment_stage6
POSTGRES_USER=<随机测试用户名>
POSTGRES_PASSWORD=<随机高强度密码>
MINIO_ACCESS_KEY=<随机测试访问键>
MINIO_SECRET_KEY=<随机测试密钥>
MINIO_BUCKET=stage6-<随机后缀>

# 平台 HTTPS：只绑定回环地址
NGINX_HTTPS_PORT=18443
NGINX_CERT_DIRECTORY=./nginx/certs

# 独立 RAGFlow 栈在宿主机回环 API 端口 19380 提供服务
RAGFLOW_API_PORT=19380
RAGFLOW_HTTP_PORT=18080
RAGFLOW_BASE_URL=http://host.docker.internal:19380
RAGFLOW_API_KEY=<本次临时 API Key>
```

将证书分别保存为：

```text
codebase/infra/nginx/certs/tls.crt
codebase/infra/nginx/certs/tls.key
```

私钥必须只在部署电脑保留，并确保 `codebase/infra/.env.local` 与 `codebase/infra/nginx/certs/` 不被 Git 跟踪：

```powershell
git check-ignore -v codebase\infra\.env.local codebase\infra\nginx\certs\tls.key
```

若该命令没有显示忽略规则，停止部署并先修复忽略配置；不得继续把秘密文件留在可能提交的位置。

## 6. 构建前端并预检 Compose

```powershell
Set-Location codebase\frontend
npm ci
npm run build
Set-Location ..\..

docker version
docker compose --env-file codebase\infra\.env.local -f codebase\infra\docker-compose.yml config --quiet
docker compose --env-file codebase\infra\.env.local -f codebase\infra\ragflow\docker-compose.yml config --quiet
```

`npm run build` 和两个 Compose 配置检查必须成功。若失败，保留脱敏错误和版本信息，登记环境阻断；不得用修改源代码、跳过证书或改用生产服务来绕过。

## 7. 启动独立 RAGFlow 栈

先启动并验证 RAGFlow。它使用自己的 Docker 项目 `equipment-ragflow`、内部网络和命名卷；平台 API 仅通过 `host.docker.internal:19380` 访问其 API。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File codebase\infra\ragflow\scripts\verify.ps1 `
  -EnvFile codebase\infra\.env.local
```

该脚本会启动 RAGFlow、MySQL、Redis、MinIO 和 Elasticsearch，并检查服务健康、固定镜像、API 版本、Elasticsearch 版本、依赖日志和秘密泄漏。成功后，仅在本机创建一个新的测试数据集和 `operation_guidance` Agent 配置；记录数据集 ID 与 Agent 配置标识，但不要记录 API Key。

> 重要：生产操作指引接口不信任客户端 `dataset_ids`。必须将测试数据集绑定到 `operation_guidance` Agent 配置，否则真实测试将正确返回 `UNAVAILABLE`，不能证明成功路径。

## 8. 启动平台隔离栈

为本次栈生成唯一项目名。示例项目名中的随机后缀必须替换，且不得复用旧环境：

```powershell
$project = "equipment-task011-live-" + ([guid]::NewGuid().ToString('N').Substring(0, 10))
$project

docker compose --profile validation `
  --env-file codebase\infra\.env.local `
  -p $project `
  -f codebase\infra\docker-compose.yml up -d --build

docker compose --profile validation `
  --env-file codebase\infra\.env.local `
  -p $project `
  -f codebase\infra\docker-compose.yml ps
```

应看到 PostgreSQL、Redis、MinIO、ClamAV、API、Nginx、Worker、Migrate 等服务按验证 profile 启动。Nginx 的公开映射必须仅为 `127.0.0.1:<本次端口>`，不能是 `0.0.0.0`。

## 9. 基础运行态检查

确认健康检查、静态资源 MIME 类型和容器内 RAGFlow 探针：

```powershell
$https = "https://127.0.0.1:18443"
curl.exe -k --fail --silent --show-error "$https/healthz"
curl.exe -k --fail --silent --show-error "$https/" | Out-File -Encoding utf8 .\stage6-index.html

docker compose --profile validation --env-file codebase\infra\.env.local -p $project -f codebase\infra\docker-compose.yml exec -T api python -m app.modules.knowledge.ragflow_probe
docker compose --profile validation --env-file codebase\infra\.env.local -p $project -f codebase\infra\docker-compose.yml run --rm validator python -m pytest tests/integration/test_task005_postgres.py -q
```

命令行可以在本机测试中使用 `-k` 仅验证服务连通性；它**不能**关闭 `DEF-STAGE6-004`。浏览器 E2E 必须使用已信任的临时根证书，且不能出现证书错误页。

## 10. 执行 Stage 6 阻断项重测

### 10.1 `DEF-STAGE6-003`：真实知识生命周期

1. 使用本次专用数据集、RAGFlow Agent 配置和非敏感测试文档。
2. 从上传开始记录 UTC 分段时间戳，至少包括：附件扫描开始/结束、MinIO 写入、Worker 领取、RAGFlow 上传、解析/索引、`READY`、检索、引用校验和清理。
3. 在每个关键阶段记录容器状态和脱敏日志摘要，以便在超时时定位唯一阻塞组件。
4. 运行真实生命周期测试。不得让它以 skipped 结束：

```powershell
docker compose --profile validation --env-file codebase\infra\.env.local -p $project -f codebase\infra\docker-compose.yml run --rm `
  -e TASK005_RAGFLOW_DATASET_ID=<本次临时数据集ID> `
  validator python -m pytest tests/integration/test_task005_live_stack.py -q -rs
```

若需要修复 API、Worker、RAGFlow、基础设施或运行配置，立即停止将其作为测试问题处理：登记缺陷并回流 Stage 5。修复合入后必须针对新的精确 SHA 完整重跑。

### 10.2 `DEF-STAGE6-004`：受信任 HTTPS 浏览器 E2E

使用 Chrome 或 Edge 打开 `https://127.0.0.1:18443`。在没有证书警告的前提下，使用临时账号完成并记录：

1. 未认证访问受保护路由时跳转登录；
2. 登录后访问 Workbench；
3. 访问 `/intelligent-config`；
4. 访问 `/fault-report`；
5. 以权限受限账号验证写操作被正确禁用或拒绝，且不会产生必然 403 的可点击操作；
6. 退出后跳转 `/login`，并且受保护页面不保留可操作页面壳。

记录浏览器版本、临时账号角色、SUT SHA、UTC 时间、每项操作与截图/视频路径。截图中不得包含密码、Token 或敏感测试附件。

### 10.3 `DEF-STAGE6-005`：性能、备份、恢复和恢复期只读负载

使用 `06-testing/performance/stage6_performance.py` 依次执行认证、附件、真实 Agent 成功与 Agent 不可用降级。每个场景按 1/2/5/10 并发、总 300 秒运行；认证/附件 P95 不超过 1 秒，两个 Agent 场景 P95 不超过 15 秒。每份 JSON 必须写明：`sut_commit`、`harness_commit`、`evidence_subject_commit`、隔离项目名、夹具和 UTC 时间。

随后执行受控附件备份、随机隔离恢复，并在恢复窗口持续 60 秒运行 10 并发 `GET /api/auth/me` 只读请求。恢复不超过 180 秒，只读 P95 不超过 2 秒。旧 SHA 的 JSON 只能作为历史追溯，不能作为本次通过证据。

可使用下列现有编排脚本完成平台 readiness、迁移、RAGFlow、HTTPS、重启和备份/恢复基础流程；传入的临时数据集 ID 必须是本次创建的资源：

```powershell
$backupDir = Join-Path $env:TEMP ("equipment-stage6-backup-" + [guid]::NewGuid().ToString('N'))
powershell -NoProfile -ExecutionPolicy Bypass -File codebase\infra\scripts\verify-platform-readiness.ps1 `
  -EnvFile codebase\infra\.env.local `
  -ProjectName $project `
  -LiveHttpsUrl $https `
  -RagflowDatasetId <本次临时数据集ID> `
  -BackupOutputDirectory $backupDir
```

该脚本完成的是基础编排，不替代本节要求的全量 1/2/5/10 并发与恢复期只读性能结果。

## 11. 证据归档与结论限制

将脱敏后的命令、结果、UTC 时间、镜像/容器摘要、浏览器版本、环境 ID、夹具 ID、SUT SHA 与失败诊断归档到 `06-testing/` 的本次 SUT SHA 目录。不得归档 `.env.local`、证书私钥、Token、数据库转储中的敏感数据或完整附件正文。

只有 `DEF-STAGE6-003`、`DEF-STAGE6-004`、`DEF-STAGE6-005` 的关闭条件全部满足，且完整报告明确绑定本 SUT，独立测试角色才能提出 Stage 6 结论。项目负责人仍需单独决定是否批准新的 Stage 6 → Stage 7 Gate。

## 12. 停止、清理与保留

在证据已脱敏归档、缺陷已记录且项目负责人允许清理后，先删除本次 RAGFlow 临时 Agent 配置、数据集、测试文档、临时账号和测试附件；确认删除结果。随后只停止本次随机项目：

```powershell
docker compose --profile validation --env-file codebase\infra\.env.local -p $project -f codebase\infra\docker-compose.yml down --remove-orphans
```

如需删除本次隔离卷，必须先确认项目名、备份结果和清理范围正确，再对该项目执行受控 `down --volumes`。不得删除无关 Docker 项目、RAGFlow 持久化卷、生产资源或共享数据。清理 `codebase/infra/.env.local`、本地证书和工作区外临时 Key 文件前，保留不含秘密的清理结果记录。
