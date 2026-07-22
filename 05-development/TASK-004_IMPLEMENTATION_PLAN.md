# TASK-004 独立 RAGFlow 基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Windows Docker Desktop/WSL2 上交付固定版本、健康可测、重启可恢复且与平台依赖隔离的 RAGFlow 容器环境，并向 TASK-005 提供唯一的 HTTP 接入契约。

**Architecture:** MySQL、Redis、MinIO、Elasticsearch 只加入 `equipment-ragflow-internal` 内部网络；RAGFlow 同时加入内部网络和 `equipment-ragflow-access` 访问网络。宿主机仅以 `127.0.0.1` 暴露 RAGFlow Web/API，TASK-005 后续只通过访问网络的 `http://ragflow:9380` 调用 RAGFlow，不能直接连接其依赖。

**Tech Stack:** Docker 29.6.1、Docker Compose 5.1.4、PowerShell 7/Windows PowerShell、RAGFlow v0.25.6、Elasticsearch 8.11.3、MySQL 8.0.39、Redis 7.4.2、MinIO、Python 3.13（平台回归）。

## Global Constraints

- 输入基线固定为 `codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`。
- 任务分支固定为 `codex/task-004-ragflow-infra`，目标分支固定为 `codex/stage-05-integration`。
- 任务开发者为 `DEV-001`，指定审核者为 `DEV-002`；DEV-001 不得批准或合并自己的 PR。
- 使用同一个 Draft PR；当前 HEAD 变化后必须重新绑定审核结论。
- 不修改 PRD、SPEC、AC、原型、业务 API、数据库迁移、Python RAGFlow 适配器或知识文档生命周期。
- 不新增 Python、Node 或生产运行时依赖；Compose 镜像是 TASK-004 获批交付物。
- 不提交真实 `.env`、密码、Token、Cookie、密钥、私有镜像凭据或卷数据。
- 不执行 `docker compose down -v`、`docker volume rm` 或其他卷删除命令。
- 内部依赖不得发布宿主机端口；RAGFlow 端口只能绑定 `127.0.0.1`。
- Elasticsearch 镜像固定为 `elasticsearch:8.11.3`，运行时版本必须报告 `8.11.x`。
- RAGFlow 镜像固定为 `infiniflow/ragflow:v0.25.6`；不得使用 `latest` 或 `nightly`。
- 每个实现切片先产生可解释的 RED，再做最小 GREEN；每个稳定切片独立提交。
- Docker Desktop 未启动、资源不足或镜像拉取失败必须如实记录，不得写成验证通过。
- Stage 6 仍禁止进入；TASK-005 只有在 TASK-004 审核、授权、正式合入并完成合并后验证后才解锁。

---

## 文件结构

| 文件 | 责任 |
|---|---|
| `codebase/infra/.env.example` | 平台现有变量与 TASK-004 安全示例变量的单一模板。 |
| `codebase/infra/ragflow/docker-compose.yml` | TASK-004 唯一 Compose 定义。 |
| `codebase/infra/ragflow/service_conf.yaml.template` | RAGFlow 到四个专用依赖的变量化连接配置。 |
| `codebase/infra/ragflow/tests/verify-compose-contract.ps1` | 静态检查镜像、端口、网络、健康、卷和平台隔离。 |
| `codebase/infra/ragflow/scripts/verify.ps1` | 检查五个容器、RAGFlow HTTP 与 Elasticsearch 版本。 |
| `codebase/infra/ragflow/scripts/verify-isolation.ps1` | 检查实际 Docker 网络成员和宿主机端口。 |
| `codebase/infra/ragflow/scripts/verify-persistence.ps1` | 写入探针、重启、读取比对并清理探针。 |
| `codebase/infra/ragflow/scripts/compose-execution.psm1` | 对外部 Compose 命令统一检查退出码，供持久化清理失败路径复用。 |
| `codebase/infra/ragflow/tests/verify-cleanup-failure.ps1` | 以子进程和固定非零退出码验证四类清理失败均不会输出 PASS。 |
| `08-release-handoff/RUNBOOK.md` | 启停、验证、排障、恢复候选和 TASK-005 接入说明。 |
| `05-development/SELF_TEST.md` | TASK-004 真实命令和结果。 |
| `05-development/CODE_REVIEW.md` | DEV-001 三轮自审及 DEV-002 审核入口。 |
| `05-development/COMMIT_LOG.md` | TASK-004 切片和最终候选 SHA。 |
| `05-development/CHECKPOINTS.md` | 可恢复的 TASK-004 功能检查点。 |
| `workflow/DEV_TO_PM_HANDOFF.md` | 精确 HEAD、证据、风险、未验证项和请求动作。 |

---

### Task 1: 建立 Compose 静态契约 RED

**Files:**

- Create: `codebase/infra/ragflow/tests/verify-compose-contract.ps1`
- Read: `05-development/TASK-004_RAGFLOW_INFRA_DESIGN.md`

**Interfaces:**

- Consumes: `codebase/infra/.env.example` 和计划中的 RAGFlow Compose 路径。
- Produces: 退出码为 0/非 0 的静态门禁；后续所有 Compose 修改必须先通过它。

- [ ] **Step 1: 创建静态契约检查脚本**

写入以下核心结构；脚本只读取 `docker compose config --format json`，不启动容器：

```powershell
param(
    [string]$ComposeFile = "codebase/infra/ragflow/docker-compose.yml",
    [string]$EnvFile = "codebase/infra/.env.example"
)

$ErrorActionPreference = "Stop"

function Assert-Contract([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "TASK-004 contract failed: $Message" }
}

$raw = docker compose --env-file $EnvFile -f $ComposeFile config --format json
if ($LASTEXITCODE -ne 0) { throw "docker compose config failed" }
$config = $raw | ConvertFrom-Json

$expectedImages = @{
    ragflow                 = "infiniflow/ragflow:v0.25.6"
    "ragflow-elasticsearch" = "elasticsearch:8.11.3"
    "ragflow-mysql"         = "mysql:8.0.39"
    "ragflow-minio"         = "pgsty/minio:RELEASE.2026-03-25T00-00-00Z"
    "ragflow-redis"         = "redis:7.4.2-alpine"
}

Assert-Contract ($config.services.PSObject.Properties.Name.Count -eq 5) "service count must be five"
foreach ($entry in $expectedImages.GetEnumerator()) {
    $service = $config.services.($entry.Key)
    Assert-Contract ($null -ne $service) "missing service $($entry.Key)"
    Assert-Contract ($service.image -eq $entry.Value) "unexpected image for $($entry.Key)"
    Assert-Contract ($null -ne $service.healthcheck) "missing healthcheck for $($entry.Key)"
    Assert-Contract ($service.restart -eq "unless-stopped") "missing restart policy for $($entry.Key)"
}

$internalServices = @("ragflow-mysql", "ragflow-redis", "ragflow-minio", "ragflow-elasticsearch")
foreach ($name in $internalServices) {
    Assert-Contract ($null -eq $config.services.$name.ports) "$name publishes a host port"
    Assert-Contract ($config.services.$name.networks.PSObject.Properties.Name -contains "ragflow-internal") "$name missing internal network"
    Assert-Contract (-not ($config.services.$name.networks.PSObject.Properties.Name -contains "ragflow-access")) "$name joined access network"
}

Assert-Contract ($config.networks."ragflow-internal".internal -eq $true) "dependency network is not internal"
Assert-Contract ($config.networks."ragflow-internal".name -eq "equipment-ragflow-internal") "internal network name drift"
Assert-Contract ($config.networks."ragflow-access".name -eq "equipment-ragflow-access") "access network name drift"

$ragflowNetworks = $config.services.ragflow.networks.PSObject.Properties.Name
Assert-Contract ($ragflowNetworks -contains "ragflow-internal") "ragflow missing internal network"
Assert-Contract ($ragflowNetworks -contains "ragflow-access") "ragflow missing access network"

$published = @($config.services.ragflow.ports)
Assert-Contract ($published.Count -eq 2) "ragflow must publish exactly two loopback ports"
foreach ($port in $published) {
    Assert-Contract ($port.host_ip -eq "127.0.0.1") "ragflow port is not loopback-only"
}

Write-Output "TASK-004 compose contract: PASS"
```

- [ ] **Step 2: 运行脚本确认 RED**

Run:

```powershell
powershell -NoProfile -File codebase/infra/ragflow/tests/verify-compose-contract.ps1
```

Expected: FAIL，因为 `codebase/infra/ragflow/docker-compose.yml` 尚不存在；错误必须明确指向缺少 Compose 文件，不得启动容器。

- [ ] **Step 3: 提交 RED**

```powershell
git add codebase/infra/ragflow/tests/verify-compose-contract.ps1
git commit -m "test(task-004): define ragflow compose contract"
```

---

### Task 2: 实现最小 Compose 与安全配置 GREEN

**Files:**

- Create: `codebase/infra/ragflow/docker-compose.yml`
- Create: `codebase/infra/ragflow/service_conf.yaml.template`
- Modify: `codebase/infra/.env.example`
- Test: `codebase/infra/ragflow/tests/verify-compose-contract.ps1`

**Interfaces:**

- Consumes: Task 1 的静态门禁。
- Produces: `equipment-ragflow` 五服务编排、`equipment-ragflow-internal`、`equipment-ragflow-access`、宿主机回环地址和变量化依赖连接。

- [ ] **Step 1: 在 `.env.example` 追加安全示例变量**

保持现有平台变量不变，追加：

```dotenv

# TASK-004 isolated RAGFlow stack; replace every change-me value outside Git.
RAGFLOW_IMAGE=infiniflow/ragflow:v0.25.6
RAGFLOW_HTTP_PORT=8080
RAGFLOW_API_PORT=9380
RAGFLOW_TIMEZONE=Asia/Shanghai
RAGFLOW_MYSQL_DATABASE=rag_flow
RAGFLOW_MYSQL_USER=rag_flow
RAGFLOW_MYSQL_PASSWORD=change-me-ragflow-mysql
RAGFLOW_MYSQL_ROOT_PASSWORD=change-me-ragflow-mysql-root
RAGFLOW_REDIS_PASSWORD=change-me-ragflow-redis
RAGFLOW_MINIO_USER=rag_flow
RAGFLOW_MINIO_PASSWORD=change-me-ragflow-minio
RAGFLOW_ELASTIC_PASSWORD=change-me-ragflow-elasticsearch
RAGFLOW_ELASTIC_MEM_LIMIT=4294967296
```

- [ ] **Step 2: 创建变量化 RAGFlow 配置模板**

`service_conf.yaml.template` 的有效配置固定为：

```yaml
ragflow:
  host: 0.0.0.0
  http_port: 9380
mysql:
  name: '${MYSQL_DBNAME}'
  user: '${MYSQL_USER}'
  password: '${MYSQL_PASSWORD}'
  host: 'ragflow-mysql'
  port: 3306
  max_connections: 100
  stale_timeout: 300
minio:
  user: '${MINIO_USER}'
  password: '${MINIO_PASSWORD}'
  host: 'ragflow-minio:9000'
es:
  hosts: 'http://ragflow-elasticsearch:9200'
  username: 'elastic'
  password: '${ELASTIC_PASSWORD}'
redis:
  db: 1
  password: '${REDIS_PASSWORD}'
  host: 'ragflow-redis:6379'
```

- [ ] **Step 3: 创建五服务 Compose**

实现以下不可变结构：

```yaml
name: equipment-ragflow

services:
  ragflow:
    image: ${RAGFLOW_IMAGE}
    depends_on:
      ragflow-mysql: { condition: service_healthy }
      ragflow-redis: { condition: service_healthy }
      ragflow-minio: { condition: service_healthy }
      ragflow-elasticsearch: { condition: service_healthy }
    environment:
      DOC_ENGINE: elasticsearch
      MYSQL_HOST: ragflow-mysql
      MYSQL_PORT: "3306"
      MYSQL_DBNAME: ${RAGFLOW_MYSQL_DATABASE}
      MYSQL_USER: ${RAGFLOW_MYSQL_USER}
      MYSQL_PASSWORD: ${RAGFLOW_MYSQL_PASSWORD}
      REDIS_HOST: ragflow-redis
      REDIS_PORT: "6379"
      REDIS_PASSWORD: ${RAGFLOW_REDIS_PASSWORD}
      MINIO_HOST: ragflow-minio
      MINIO_PORT: "9000"
      MINIO_USER: ${RAGFLOW_MINIO_USER}
      MINIO_PASSWORD: ${RAGFLOW_MINIO_PASSWORD}
      ES_HOST: ragflow-elasticsearch
      ES_PORT: "9200"
      ELASTIC_PASSWORD: ${RAGFLOW_ELASTIC_PASSWORD}
      TZ: ${RAGFLOW_TIMEZONE}
    ports:
      - "127.0.0.1:${RAGFLOW_HTTP_PORT}:80"
      - "127.0.0.1:${RAGFLOW_API_PORT}:9380"
    volumes:
      - ragflow_logs:/ragflow/logs
      - ./service_conf.yaml.template:/ragflow/conf/service_conf.yaml.template:ro
    networks:
      ragflow-internal: {}
      ragflow-access:
        aliases: [ragflow]
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:80/ >/dev/null"]
      interval: 10s
      timeout: 5s
      retries: 60
      start_period: 60s
    restart: unless-stopped

  ragflow-mysql:
    image: mysql:8.0.39
    environment:
      MYSQL_DATABASE: ${RAGFLOW_MYSQL_DATABASE}
      MYSQL_USER: ${RAGFLOW_MYSQL_USER}
      MYSQL_PASSWORD: ${RAGFLOW_MYSQL_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${RAGFLOW_MYSQL_ROOT_PASSWORD}
    command: ["--max_connections=1000", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_unicode_ci", "--default-authentication-plugin=mysql_native_password"]
    volumes: [ragflow_mysql_data:/var/lib/mysql]
    networks: [ragflow-internal]
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -u$${MYSQL_USER} -p$${MYSQL_PASSWORD} --silent"]
      interval: 10s
      timeout: 5s
      retries: 60
      start_period: 30s
    restart: unless-stopped

  ragflow-redis:
    image: redis:7.4.2-alpine
    environment:
      REDIS_PASSWORD: ${RAGFLOW_REDIS_PASSWORD}
    command: ["sh", "-c", "exec redis-server --appendonly yes --requirepass \"$$REDIS_PASSWORD\""]
    volumes: [ragflow_redis_data:/data]
    networks: [ragflow-internal]
    healthcheck:
      test: ["CMD-SHELL", "redis-cli -a \"$$REDIS_PASSWORD\" ping 2>/dev/null | grep -q PONG"]
      interval: 10s
      timeout: 5s
      retries: 60
    restart: unless-stopped

  ragflow-minio:
    image: pgsty/minio:RELEASE.2026-03-25T00-00-00Z
    environment:
      MINIO_ROOT_USER: ${RAGFLOW_MINIO_USER}
      MINIO_ROOT_PASSWORD: ${RAGFLOW_MINIO_PASSWORD}
    command: ["server", "--console-address", ":9001", "/data"]
    volumes: [ragflow_minio_data:/data]
    networks: [ragflow-internal]
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 60
    restart: unless-stopped

  ragflow-elasticsearch:
    image: elasticsearch:8.11.3
    environment:
      discovery.type: single-node
      xpack.security.enabled: "true"
      xpack.security.http.ssl.enabled: "false"
      xpack.security.transport.ssl.enabled: "false"
      ELASTIC_PASSWORD: ${RAGFLOW_ELASTIC_PASSWORD}
      bootstrap.memory_lock: "false"
    mem_limit: ${RAGFLOW_ELASTIC_MEM_LIMIT}
    volumes: [ragflow_elasticsearch_data:/usr/share/elasticsearch/data]
    networks: [ragflow-internal]
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS -u elastic:\"$$ELASTIC_PASSWORD\" 'http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s' >/dev/null"]
      interval: 10s
      timeout: 10s
      retries: 60
      start_period: 30s
    restart: unless-stopped

volumes:
  ragflow_logs: {}
  ragflow_mysql_data: {}
  ragflow_redis_data: {}
  ragflow_minio_data: {}
  ragflow_elasticsearch_data: {}

networks:
  ragflow-internal:
    name: equipment-ragflow-internal
    internal: true
  ragflow-access:
    name: equipment-ragflow-access
```

- [ ] **Step 4: 运行静态契约确认 GREEN**

Run:

```powershell
powershell -NoProfile -File codebase/infra/ragflow/tests/verify-compose-contract.ps1
docker compose --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml config --quiet
git diff --check
```

Expected: 三条命令退出码均为 0；脚本输出 `TASK-004 compose contract: PASS`。

- [ ] **Step 5: 提交 Compose GREEN**

```powershell
git add codebase/infra/.env.example codebase/infra/ragflow/docker-compose.yml codebase/infra/ragflow/service_conf.yaml.template
git commit -m "feat(task-004): add isolated ragflow compose stack"
```

---

### Task 3: 实现真实健康与版本验证

**Files:**

- Create: `codebase/infra/ragflow/scripts/verify.ps1`
- Test: `codebase/infra/ragflow/docker-compose.yml`

**Interfaces:**

- Consumes: Compose 项目 `equipment-ragflow` 和显式传入的本地 `EnvFile`；`.env.example` 只作为模板和静态配置输入。
- Produces: 五服务健康、RAGFlow Web/API 契约、Elasticsearch `8.11.x`、展开 Compose 镜像、实际运行容器镜像 ID 与 5 个获批镜像精确 digest 的脱敏证据，并记录执行时间、命令退出码和脱敏日志摘要。

- [ ] **Step 1: 在 Docker Desktop 未启动状态运行健康脚本路径并确认 RED**

先创建脚本入口，执行 `docker info`，非 0 时抛出 `Docker Desktop Linux engine is unavailable`。运行并记录当前可解释 RED，不把环境未启动写成代码缺陷。

- [ ] **Step 2: 完成健康验证脚本**

脚本固定执行：

```powershell
$RagflowEnvFile = "codebase/infra/.env.local"
if (-not (Test-Path -LiteralPath $RagflowEnvFile -PathType Leaf)) { throw "Missing local RAGFlow environment file" }
$compose = @("compose", "-p", "equipment-ragflow", "--env-file", $RagflowEnvFile, "-f", "codebase/infra/ragflow/docker-compose.yml")

docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop Linux engine is unavailable" }

& docker @compose up -d
if ($LASTEXITCODE -ne 0) { throw "RAGFlow compose up failed" }

$deadline = (Get-Date).AddMinutes(15)
do {
    $rows = (& docker @compose ps --format json | ConvertFrom-Json)
    $healthy = @($rows | Where-Object { $_.Health -eq "healthy" }).Count
    if ($healthy -eq 5) { break }
    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $deadline)

if ($healthy -ne 5) { throw "Not all five TASK-004 services became healthy" }

$expanded = & docker @compose config --format json | ConvertFrom-Json
$webPort = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 80 })[0].published
$web = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$webPort/"
if ($web.StatusCode -ne 200) { throw "RAGFlow Web endpoint is unhealthy" }

$apiPort = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 9380 })[0].published
$apiDeadline = (Get-Date).AddSeconds(60)
do {
    try { $api = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$apiPort/api/v1/system/version" }
    catch { $api = $null }
    if ($null -ne $api -and $api.StatusCode -eq 200) { break }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $apiDeadline)
if ($null -eq $api) { throw "RAGFlow API endpoint did not become healthy before timeout" }
$apiContract = $api.Content | ConvertFrom-Json
if ($api.StatusCode -ne 200 -or $apiContract.code -ne 0 -or $apiContract.data -ne "v0.25.6") {
    throw "RAGFlow API version contract drift"
}

$versionJson = & docker @compose exec -T ragflow-elasticsearch sh -lc 'curl -fsS -u "elastic:$ELASTIC_PASSWORD" http://localhost:9200/'
$version = ($versionJson | ConvertFrom-Json).version.number
if ($version -notlike "8.11.*") { throw "Unexpected Elasticsearch version: $version" }

Write-Output "TASK-004 health: PASS; services=5; elasticsearch=$version; web_status=200; api_status=200; ragflow=v0.25.6"
```

实现时不得把环境变量实际值写到输出；镜像校验必须同时完成三层绑定：展开 Compose 配置中的镜像标签等于获批标签、固定标签的 `RepoDigests` 包含获批 SHA-256、运行容器的镜像 ID 等于获批标签解析出的本地镜像 ID。任一缺失或不一致均返回非零，不输出 Registry 凭据。健康验证还必须扫描 RAGFlow 日志中的依赖连接失败，并以运行时秘密值进行精确泄漏扫描；输出只允许包含开始/结束时间、命令退出码和命中计数等脱敏摘要。

- [ ] **Step 3: 启动 Docker Desktop 并运行真实 GREEN**

Run:

```powershell
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify.ps1 -EnvFile $RagflowEnvFile
docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml ps
```

Expected: 五个服务均为 `healthy`；RAGFlow Web 返回 HTTP 200；RAGFlow API 版本契约返回 `v0.25.6`；Elasticsearch 为 `8.11.x`；Compose 展开镜像、运行容器镜像 ID 和五个镜像摘要均与获批值完全一致；依赖连接失败和秘密值命中均为 0；证据包含执行时间和各 Docker 命令退出码。

- [ ] **Step 4: 提交健康验证**

```powershell
git add codebase/infra/ragflow/scripts/verify.ps1
git commit -m "test(task-004): verify ragflow container health"
```

---

### Task 4: 实现运行时网络与端口隔离验证

**Files:**

- Create: `codebase/infra/ragflow/scripts/verify-isolation.ps1`
- Test: `codebase/infra/ragflow/docker-compose.yml`

**Interfaces:**

- Consumes: 已运行的 `equipment-ragflow` Compose 项目。
- Produces: 内部网络成员、访问网络成员及宿主机发布端口的机器可检查断言。

- [ ] **Step 1: 写隔离断言并制造 RED**

脚本先断言一个不存在的依赖发布端口会被拒绝；在临时内存对象上执行该断言，确认测试本身能够失败，不修改 Compose 或启动额外容器。

- [ ] **Step 2: 实现真实 Docker 网络检查**

核心断言：

```powershell
$internal = docker network inspect equipment-ragflow-internal | ConvertFrom-Json
$access = docker network inspect equipment-ragflow-access | ConvertFrom-Json

$internalNames = @($internal[0].Containers.PSObject.Properties.Value.Name)
$accessNames = @($access[0].Containers.PSObject.Properties.Value.Name)

foreach ($suffix in @("mysql", "redis", "minio", "elasticsearch")) {
    if (-not ($internalNames -match "equipment-ragflow-$suffix-")) {
        throw "Missing internal dependency: $suffix"
    }
    if ($accessNames -match "equipment-ragflow-$suffix-") {
        throw "Internal dependency leaked to access network: $suffix"
    }
}

if (-not ($internalNames -match "equipment-ragflow-ragflow-")) { throw "RAGFlow missing internal network" }
if (-not ($accessNames -match "equipment-ragflow-ragflow-")) { throw "RAGFlow missing access network" }

$published = docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml ps --format json | ConvertFrom-Json
foreach ($row in $published) {
    if ($row.Service -ne "ragflow" -and $row.Publishers.Count -gt 0) {
        throw "Internal dependency publishes a host port: $($row.Service)"
    }
    foreach ($publisher in @($row.Publishers)) {
        if ($row.Service -eq "ragflow" -and $publisher.URL -ne "127.0.0.1") {
            throw "RAGFlow port is not loopback-only"
        }
    }
}

Write-Output "TASK-004 isolation: PASS"
```

- [ ] **Step 3: 运行 GREEN**

```powershell
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-isolation.ps1
```

Expected: 输出 `TASK-004 isolation: PASS`，退出码 0。

- [ ] **Step 4: 提交隔离验证**

```powershell
git add codebase/infra/ragflow/scripts/verify-isolation.ps1
git commit -m "test(task-004): verify ragflow network isolation"
```

---

### Task 5: 实现重启持久化验证

**Files:**

- Create: `codebase/infra/ragflow/scripts/verify-persistence.ps1`
- Test: RAGFlow 四个依赖卷和 RAGFlow 日志卷。

**Interfaces:**

- Consumes: 健康的 `equipment-ragflow` 栈。
- Produces: MySQL、Redis、MinIO S3 对象、Elasticsearch 在 `compose restart` 后保持探针一致的证据。

- [ ] **Step 1: 写探针生命周期并确认缺失探针 RED**

使用随机批次 ID，例如 `$probe = "task004-$([guid]::NewGuid().ToString('N'))"`。先执行读取断言而不写入，Expected: FAIL 且指出四个探针均不存在；不创建或删除卷。

- [ ] **Step 2: 实现四类探针写入**

通过容器内部命令写入，不把密码传到宿主机输出：

```powershell
$bucket = "task004-$([guid]::NewGuid().ToString('N'))"
& docker @compose exec -T -e TASK004_PROBE=$probe ragflow-mysql sh -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "CREATE TABLE IF NOT EXISTS task004_probe (id VARCHAR(80) PRIMARY KEY); INSERT IGNORE INTO task004_probe VALUES (\"$TASK004_PROBE\");"'
& docker @compose exec -T -e TASK004_PROBE=$probe ragflow-redis sh -lc 'redis-cli -a "$REDIS_PASSWORD" SET task004:persistence "$TASK004_PROBE" >/dev/null'
& docker @compose exec -T ragflow-minio sh -lc 'mc alias set task004 http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"'
& docker @compose exec -T ragflow-minio mc mb "task004/$bucket"
& docker @compose exec -T -e TASK004_PROBE=$probe ragflow-minio sh -lc 'printf "%s" "$TASK004_PROBE" > /tmp/persistence-probe.txt'
& docker @compose exec -T ragflow-minio mc cp /tmp/persistence-probe.txt "task004/$bucket/persistence-probe.txt"
& docker @compose exec -T -e TASK004_PROBE=$probe ragflow-elasticsearch sh -lc 'curl -fsS -u "elastic:$ELASTIC_PASSWORD" -H "Content-Type: application/json" -X PUT http://localhost:9200/task004-persistence/_doc/current -d "{\"value\":\"$TASK004_PROBE\"}" >/dev/null'
```

- [ ] **Step 3: 重启并等待健康**

Run inside script:

```powershell
& docker @compose restart
```

等待逻辑复用 Task 3 的有限 15 分钟策略，但不创建共享 helper 或额外抽象层；脚本内保持局部、直接实现。

- [ ] **Step 4: 读取、比对和清理探针**

四项读取结果必须逐字等于 `$probe`。MinIO 必须通过 `mc cat`（S3 API）回读，不得直接读取 `/data`。成功后仅删除本轮探针：MySQL 行/探针表、Redis 键、MinIO 临时对象/bucket、Elasticsearch 探针索引。任何读取失败时保留卷并返回非零，不执行清卷命令。

- [ ] **Step 5: 运行真实 GREEN**

```powershell
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-persistence.ps1 -EnvFile $RagflowEnvFile
```

Expected: 输出 `TASK-004 restart persistence: PASS`，五个服务在重启后恢复 healthy，四项探针一致并被清理；MinIO 证据来自 S3 bucket/object 生命周期。

- [ ] **Step 6: 提交持久化验证**

```powershell
git add codebase/infra/ragflow/scripts/verify-persistence.ps1
git commit -m "test(task-004): verify ragflow restart persistence"
```

---

### Task 6: 补齐运行手册与 TASK-005 交付契约

**Files:**

- Modify: `08-release-handoff/RUNBOOK.md`
- Read: `05-development/TASK-004_RAGFLOW_INFRA_DESIGN.md`

**Interfaces:**

- Consumes: Tasks 2–5 的真实命令。
- Produces: DEV-001 可复现操作步骤和 TASK-005 唯一接入地址。

- [ ] **Step 1: 写入运行前置条件**

明确记录：Docker Desktop Linux containers、Docker ≥24、Compose ≥2.26.1、至少 4 CPU/16GB RAM/50GB disk、WSL2 的 `vm.max_map_count >= 262144`。只提供检查和人工设置指引，不由脚本自动修改系统全局配置。

- [ ] **Step 2: 写入启停和验证命令**

运行手册必须包含并解释：

```powershell
$RagflowEnvFile = "codebase/infra/.env.local"
if (-not (Test-Path -LiteralPath $RagflowEnvFile -PathType Leaf)) { throw "Missing local RAGFlow environment file" }

docker compose --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml config --quiet
docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml up -d
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify.ps1 -EnvFile $RagflowEnvFile
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-isolation.ps1
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-persistence.ps1 -EnvFile $RagflowEnvFile
docker compose -p equipment-ragflow --env-file $RagflowEnvFile -f codebase/infra/ragflow/docker-compose.yml down
```

明确禁止在常规操作中使用 `down -v`。

- [ ] **Step 3: 写入 TASK-005 接入契约**

固定记录：

```text
Host Web: http://127.0.0.1:${RAGFLOW_HTTP_PORT}
Host API: http://127.0.0.1:${RAGFLOW_API_PORT}
Container API: http://ragflow:9380 on equipment-ragflow-access
Authentication: runtime-only RAGFlow API Token
Dataset creation: owned by TASK-005 through RAGFlow API
Forbidden: direct access to RAGFlow MySQL/Redis/MinIO/Elasticsearch
```

- [ ] **Step 4: 写入恢复和排障边界**

包含镜像拉取 DNS/TLS、Docker 引擎未启动、Elasticsearch 内存/`vm.max_map_count`、依赖健康超时、日志脱敏、重启恢复和备份候选。完整备份恢复演练明确延后到 TASK-011。

- [ ] **Step 5: 验证并提交运行手册**

```powershell
rg -n "equipment-ragflow|down -v|TASK-005|ragflow:9380|8.11.3" 08-release-handoff/RUNBOOK.md
git diff --check
git add 08-release-handoff/RUNBOOK.md
git commit -m "docs(task-004): document ragflow operations contract"
```

Expected: 关键契约均可检索；`down -v` 只出现在禁止说明中；格式检查通过。

---

### Task 7: 完整验证、三轮自审与正式交付证据

**Files:**

- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`
- Modify only if a real defect exists: `06-testing/DEFECTS.md`

**Interfaces:**

- Consumes: Tasks 1–6 的提交和真实 Docker 状态。
- Produces: 可供 DEV-002 审核的精确 HEAD、证据、风险、回滚和 TASK-005 锁定结论。

- [ ] **Step 1: 运行完整验证矩阵**

```powershell
py -3.13 -m pytest codebase/backend/tests/test_health.py -q
docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
powershell -NoProfile -File codebase/infra/ragflow/tests/verify-compose-contract.ps1
docker compose --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml config --quiet
$RagflowEnvFile = "codebase/infra/.env.local"
if (-not (Test-Path -LiteralPath $RagflowEnvFile -PathType Leaf)) { throw "Missing local RAGFlow environment file" }
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify.ps1 -EnvFile $RagflowEnvFile
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-isolation.ps1
powershell -NoProfile -File codebase/infra/ragflow/scripts/verify-persistence.ps1 -EnvFile $RagflowEnvFile
powershell -NoProfile -File codebase/infra/ragflow/tests/verify-review-remediation.ps1
powershell -NoProfile -File codebase/infra/ragflow/tests/verify-cleanup-failure.ps1
git diff --check
```

Expected: Python 健康回归通过；两套 Compose config 通过；TASK-004 运行态、审核契约和清理失败行为验证全部 PASS；无 diff whitespace 错误。

- [ ] **Step 2: 第一轮自审 — Standards**

检查 AGENTS.md、任务书、设计、镜像固定、端口、网络、秘密、无新增依赖、无迁移、无 TASK-005 代码。发现问题直接修复并重跑相关验证。

- [ ] **Step 3: 第二轮自审 — Spec 与失败路径**

逐项映射 FR-002、NFR-003/005/007、AC-009/029/033 和 CR-028；重点检查 Docker 未启动、服务不健康、版本错误、网络泄漏、探针丢失时均明确失败。发现问题直接修复并重跑完整矩阵。

- [ ] **Step 4: 第三轮自审 — 完整 diff 与边界**

```powershell
git diff --stat origin/codex/stage-05-integration...HEAD
git diff --name-status origin/codex/stage-05-integration...HEAD
git diff --check origin/codex/stage-05-integration...HEAD
```

确认只有 TASK-004 设计、计划、基础设施、运行手册和正式证据；没有业务代码、数据库迁移、原型或 TASK-005 实现。

- [ ] **Step 5: 更新正式台账**

每份台账记录相同事实：任务仍需 DEV-002 审核和正式合入；TASK-005 在合入前继续锁定；Stage 6 禁止进入。SELF_TEST 记录真实命令和结果；CODE_REVIEW 记录三轮审查；COMMIT_LOG/CHECKPOINTS 记录精确提交；DEV_TO_PM_HANDOFF 记录请求 DEV-002 审核的动作。

- [ ] **Step 6: 提交证据并确定精确 HEAD**

```powershell
git add 05-development/SELF_TEST.md 05-development/CODE_REVIEW.md 05-development/COMMIT_LOG.md 05-development/CHECKPOINTS.md workflow/DEV_TO_PM_HANDOFF.md
git commit -m "docs(task-004): record ragflow validation evidence"
git rev-parse HEAD
```

- [ ] **Step 7: 推送并维护同一个 Draft PR**

```powershell
git push -u origin codex/task-004-ragflow-infra
```

若 Draft PR 尚不存在，创建一次：

```text
Title: [TASK-004] feat: deploy isolated RAGFlow infrastructure
Head: codex/task-004-ragflow-infra
Base: codex/stage-05-integration
State: Draft
Developer: DEV-001
Reviewer: DEV-002
```

PR 描述必须包含任务/AC、精确 HEAD、影响文件、真实命令结果、镜像版本/digest、网络/端口/持久化证据、风险、回滚、无新增生产依赖/兼容代码/抽象层/无关修改声明。不得在证据完成前转 Ready。

- [ ] **Step 8: 发起 DEV-002 精确 HEAD 审核**

验证完成后把同一 PR 转 Ready，并请求 DEV-002 审核 Standards、Spec、TASK-005 契约和 Docker 真实证据。任何 Critical/Important 都必须在同一分支修复并产生新 HEAD 后重新审核。

---

## 完成后的集成门禁

DEV-002 批准当前精确 HEAD 后，DEV-001 仍须检查目标分支、HEAD、required checks、依赖、冲突、共享契约、风险、回滚和合并后验证计划，并向项目负责人提交绑定 PR 编号和完整 HEAD 的独立 Merge 授权请求。DEV-001 是作者，不得执行 Merge；获批后由非作者 DEV-002 手动 Merge Commit。合并后完成五服务健康、隔离和重启持久化复核，记录 Merge SHA，才能正式解锁 TASK-005。合入集成分支不等于 Stage 5 完成，也不允许进入 Stage 6。
