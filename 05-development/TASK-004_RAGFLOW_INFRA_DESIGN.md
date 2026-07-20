# TASK-004 独立 RAGFlow 基础设施设计

## 1. 文档状态

- 任务：`TASK-004` — 部署独立 RAGFlow 容器环境
- 状态：已由项目负责人确认，进入实施计划检查点
- 设计确认日期：2026-07-20
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- 输入基线：`codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`
- 任务分支：`codex/task-004-ragflow-infra`
- PR 目标分支：`codex/stage-05-integration`
- 需求映射：FR-002、NFR-003、NFR-005、NFR-007；AC-009、AC-029、AC-033；CR-028

## 2. 目标与边界

本任务在 Windows Docker Desktop/WSL2 上交付可重复启动、可检查、可恢复且与业务栈隔离的 RAGFlow 依赖栈。它向 TASK-005 提供稳定的运行契约，但不实现知识业务功能。

包含：

- RAGFlow、MySQL、Redis、MinIO、Elasticsearch 8.11 的独立 Compose 编排；
- 固定镜像版本、内部网络、专用账户、专用数据卷和健康检查；
- Docker Desktop 前置条件、启动、停止、重启、排障与数据恢复候选说明；
- 真实容器健康、版本、重启持久化、端口与网络隔离证据；
- 交付给 TASK-005 的地址、凭据引用、健康探测、数据集初始化边界和恢复步骤。

不包含：

- 平台知识文档 API、数据库模型、迁移、Worker 或 Python RAGFlow 适配器；
- 真实文档上传、解析、切片、索引、混合检索或引用回传；
- 超时后的业务页面降级逻辑；
- 外部聊天、Embedding、Rerank 模型配置；
- Nginx 公网 HTTPS、生产发布、Stage 6 测试或 Stage 7 验收。

上述应用与文档生命周期能力属于 TASK-005 或后续集成任务。TASK-004 不以伪文档、mock 适配器或静态引用证明这些能力。

## 3. 上游兼容基线与镜像策略

采用 RAGFlow 官方稳定发布 `v0.25.6` 的 Docker 配置作为兼容基线，并按任务书继续使用 Elasticsearch 8.11：

| 服务 | 固定镜像标签 | 设计理由 |
|---|---|---|
| RAGFlow | `infiniflow/ragflow:v0.25.6` | 2026-05-26 官方稳定发布；不使用 `nightly` 或 `latest` |
| Elasticsearch | `elasticsearch:8.11.3` | RAGFlow v0.25.6 官方默认 `STACK_VERSION`，满足 Elasticsearch 8.11 约束 |
| MySQL | `mysql:8.0.39` | RAGFlow v0.25.6 官方 Compose 固定版本 |
| MinIO | `pgsty/minio:RELEASE.2026-03-25T00-00-00Z` | RAGFlow v0.25.6 官方 Compose 使用的固定 MinIO 发布镜像 |
| Redis | `redis:7.4.2-alpine` | 满足任务书明确的 Redis 依赖；不复用平台 Redis，也不使用浮动标签 |

RAGFlow 官方 v0.25.6 已将默认缓存容器改为 Valkey 8，但 TASK-004 获批任务书明确要求 Redis，因此本任务保持 Redis，并通过真实启动和 RAGFlow 连接健康验证兼容性。若 Redis 兼容验证失败，不静默替换为 Valkey；先记录阻断并按变更流程处理。

首次成功拉取后记录每个镜像的本地 RepoDigest，后续验证同时核对固定标签与 digest。中国大陆镜像源只可作为显式的拉取替代，不可改写运行时镜像身份或把镜像站凭据写入仓库。

官方参考：

- `https://github.com/infiniflow/ragflow/releases/tag/v0.25.6`
- `https://github.com/infiniflow/ragflow/blob/v0.25.6/docker/README.md`
- `https://github.com/infiniflow/ragflow/blob/v0.25.6/docker/docker-compose-base.yml`
- `https://github.com/infiniflow/ragflow/blob/v0.25.6/docker/docker-compose.yml`

## 4. 目录与配置单一事实源

计划使用以下规范位置：

```text
codebase/infra/
  .env.example
  ragflow/
    docker-compose.yml
    service_conf.yaml.template
    init.sql
    scripts/
      verify.ps1
      verify-isolation.ps1
      verify-persistence.ps1
08-release-handoff/
  RUNBOOK.md
```

- `codebase/infra/ragflow/docker-compose.yml` 是 TASK-004 唯一 Compose 定义；不复制官方整仓库。
- `service_conf.yaml.template` 只保留 RAGFlow 连接五个本任务服务所需的最小配置，并引用环境变量。
- `init.sql` 只初始化 RAGFlow 自身数据库，不创建平台业务数据。
- 验证脚本只读检查或执行可逆的容器重启；不得删除卷。
- `RUNBOOK.md` 在现有规范文件中原位补充候选步骤，不创建 `v2`、`copy` 或本地历史副本。

## 5. Compose 拓扑与信任边界

Compose 项目名固定为 `equipment-ragflow`。服务名固定为：

- `ragflow`
- `ragflow-mysql`
- `ragflow-redis`
- `ragflow-minio`
- `ragflow-elasticsearch`

MySQL、Redis、MinIO 和 Elasticsearch 只加入 `ragflow-internal`，该网络设置 `internal: true`，且不发布任何宿主机端口。RAGFlow 同时加入 `ragflow-internal` 和命名访问网络 `equipment-ragflow-access`：前者只连接四个依赖，后者提供出站能力和 TASK-005 唯一的容器间接入点。任何依赖服务都不得加入访问网络。

RAGFlow 的 Web/API 接口另外只绑定本机回环地址，例如 `127.0.0.1:${RAGFLOW_HTTP_PORT}:80` 和 `127.0.0.1:${RAGFLOW_API_PORT}:9380`，用于 DEV-001 本机验证，不形成公网暴露。TASK-005 的业务服务后续把 `equipment-ragflow-access` 引用为 external network，只访问 `ragflow:9380` 别名；不得加入 `ragflow-internal`。

平台现有 `platform` 网络、PostgreSQL、Redis 和后续平台 MinIO 不加入 `ragflow-internal`。RAGFlow 栈也不加入 `platform`。网络共享只暴露 RAGFlow HTTP 边界，不共享依赖服务账户。

RAGFlow 仅依赖四个内部服务达到健康状态后启动。每个服务使用 `restart: unless-stopped`，不指定固定 `container_name`，避免破坏 Compose 项目隔离和并行诊断。

## 6. 数据、账户与密钥边界

使用五个专用命名卷：

- `ragflow_mysql_data`
- `ragflow_redis_data`
- `ragflow_minio_data`
- `ragflow_elasticsearch_data`
- `ragflow_logs`

账户和秘密仅通过运行时 `.env` 或操作员会话环境注入。仓库只提交变量名和明显不可用于正式环境的示例值；真实 `.env`、密码、Token、Cookie、密钥和镜像站凭据禁止提交、输出到验证证据或写入日志。

环境模板至少定义：

- `RAGFLOW_IMAGE`
- `RAGFLOW_HTTP_PORT`、`RAGFLOW_API_PORT`
- `RAGFLOW_MYSQL_DATABASE`、`RAGFLOW_MYSQL_USER`、`RAGFLOW_MYSQL_PASSWORD`
- `RAGFLOW_REDIS_PASSWORD`
- `RAGFLOW_MINIO_USER`、`RAGFLOW_MINIO_PASSWORD`
- `RAGFLOW_ELASTIC_PASSWORD`
- `RAGFLOW_TIMEZONE`
- Elasticsearch 内存上限

MySQL 使用非平台专用用户和数据库；Redis、MinIO、Elasticsearch 使用各自独立密码。RAGFlow 配置模板只通过 `${...}` 引用这些变量，不复制明文值。

## 7. 健康与启动契约

健康检查分两层：

1. 容器内服务健康：
   - MySQL：使用专用用户执行 `mysqladmin ping`；
   - Redis：带密码执行 `redis-cli ping`；
   - MinIO：请求 `/minio/health/live`；
   - Elasticsearch：带认证请求 `/_cluster/health`，同时验证返回版本为 `8.11.x`；
   - RAGFlow：从容器内请求本机 HTTP 服务并要求成功响应。
2. 宿主机接入健康：
   - 请求 `127.0.0.1:${RAGFLOW_HTTP_PORT}` 和 API 接入口；
   - 检查 `docker compose ps` 中五个服务均为 running/healthy；
   - 检查 RAGFlow 日志没有依赖连接失败，同时对输出做秘密值扫描。

健康检查使用有限超时、重试和 `start_period`，允许 Elasticsearch 与 RAGFlow 首次初始化。失败必须保留非敏感日志并返回非零退出码，不以等待无限循环或伪造 healthy 掩盖错误。

## 8. 持久化、重启与恢复

持久化验证使用一组仅供 TASK-004 的探针数据：MySQL 探针表、Redis 探针键、MinIO 探针对象和 Elasticsearch 探针索引。验证顺序为：

1. 五个服务达到健康；
2. 写入带随机测试批次 ID 的探针数据；
3. 执行 `docker compose restart`，不得执行 `down -v`；
4. 等待全部服务重新健康；
5. 逐项读取并比对探针数据；
6. 删除本轮探针数据，不删除卷或业务初始化数据。

恢复候选步骤记录卷清单、停止写入、导出 MySQL、复制/导出 MinIO 数据、生成 Elasticsearch 快照前置条件和 Redis 数据策略。TASK-004 只验证重启持久化和恢复步骤可执行性；完整备份恢复演练及每日保留策略属于 TASK-011。

任何包含 `down -v`、卷删除或数据目录清理的命令都不得由验证脚本自动执行，必须获得项目负责人针对具体数据范围的明确授权。

## 9. TASK-005 交付契约

TASK-004 合入后向 TASK-005 提供：

| 契约项 | 固定内容 |
|---|---|
| 本机 Web 地址 | `http://127.0.0.1:${RAGFLOW_HTTP_PORT}` |
| 本机 API 地址 | `http://127.0.0.1:${RAGFLOW_API_PORT}` |
| 容器 API 地址 | `equipment-ragflow-access` 网络内的 `http://ragflow:9380` |
| 容器内部依赖地址 | 仅由 RAGFlow 使用，不交给平台业务服务 |
| 认证 | TASK-005 使用 RAGFlow 正式 API Token；Token 仅运行时注入，不写入仓库 |
| 健康判定 | Compose 五服务健康且本机 RAGFlow HTTP/API 探测成功 |
| 数据集初始化 | 由 TASK-005 通过 RAGFlow API 创建和记录数据集 ID；TASK-004 不预置业务数据集 |
| 恢复 | 按 RUNBOOK 重启栈并确认健康；数据损坏时转入备份恢复流程，不自动重建卷 |

TASK-005 不直接连接本任务的 MySQL、Redis、MinIO 或 Elasticsearch，不依赖它们的账户。它只通过 RAGFlow HTTP API 消费知识能力。

## 10. 验证设计

实施按测试驱动顺序进行：先写能够因当前缺少 RAGFlow Compose 而失败的静态契约检查，再补最小 Compose 和配置使其通过，最后运行真实容器验证。

静态失败/通过矩阵：

- 缺少任一固定服务或镜像标签时失败；
- Elasticsearch 不是 `8.11.3` 时失败；
- 内部依赖存在 `ports` 发布或加入访问网络时失败；
- 专用依赖网络不是 internal 时失败；
- RAGFlow 缺少命名访问网络，或其他服务能够访问依赖网络时失败；
- 使用平台服务名、平台账户变量或平台网络时失败；
- 环境模板含疑似真实秘密或 Compose 展开后缺变量时失败；
- 未定义健康检查、命名卷或重启策略时失败。

真实验证矩阵：

```powershell
docker compose --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml config --quiet
docker compose -p equipment-ragflow --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml up -d
docker compose -p equipment-ragflow --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml ps
powershell -File codebase/infra/ragflow/scripts/verify.ps1
powershell -File codebase/infra/ragflow/scripts/verify-isolation.ps1
powershell -File codebase/infra/ragflow/scripts/verify-persistence.ps1
git diff --check
```

验证证据至少记录：执行时间、Docker/Compose 版本、镜像 tag/digest、五个容器状态、Elasticsearch 完整版本、回环端口、内部依赖无宿主端口、重启前后探针一致性、命令退出码和已脱敏日志摘要。

## 11. 错误处理与残余风险

- Docker Desktop 未启动、WSL2 内核参数不足、内存或磁盘不足时立即失败，并给出具体前置条件，不自动修改系统全局配置。
- 镜像拉取失败时区分 DNS/TLS、仓库限流和镜像不存在；不把镜像下载失败写成服务验证通过。
- Elasticsearch 首次启动可能需要较长时间；达到有限重试上限后保留日志并停止后续持久化测试。
- Redis 7 与 RAGFlow v0.25.6 的兼容性必须以真实 RAGFlow 连接健康为准，这是本设计的首要验证风险。
- RAGFlow v0.25.6 后续可能发布安全修复；本任务先保证可重复基线，不在未批准情况下追随新版本。升级需独立变更、兼容验证和回滚方案。
- 仅绑定 `127.0.0.1` 解决本机开发暴露面，不等于生产网络安全；公网入口与 HTTPS 属于 TASK-011。

## 12. 完成判定

TASK-004 只有同时满足以下条件才可转 Ready 并请求 DEV-002 审核精确 HEAD：

- Compose、模板、脚本和 RUNBOOK 候选均已提交到规范位置；
- 五个容器在真实 Docker Desktop/WSL2 环境健康；
- Elasticsearch 报告 8.11.x，实际镜像为固定 `8.11.3`；
- 内部依赖没有宿主机或公网端口，且未复用平台网络或账户；
- 重启后探针数据与配置可恢复；
- Python 3.13 最小回归、现有平台 Compose、TASK-004 静态检查和 `git diff --check` 通过；
- SELF_TEST、CODE_REVIEW、COMMIT_LOG、CHECKPOINTS、DEV_TO_PM_HANDOFF 与缺陷/风险记录一致；
- 未实现 TASK-005 的 API、适配器、文档生命周期或引用逻辑；
- Draft PR 描述包含真实命令结果、影响文件、未验证项、依赖/兼容/抽象/无关修改声明和当前精确 HEAD。
