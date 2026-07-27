# TASK-011 平台补齐、端到端、安全与发布准备实施计划

> **执行约束：** DEV-001 在隔离分支 `codex/task-011-e2e-release-readiness` 完成以下步骤；DEV-002 审核同一 Draft PR 的精确 HEAD。该计划不构成 Stage 6、Stage 7 或生产发布批准。

**目标：** 在既有 Stage 5 集成基线上补齐健康分、附件安全、HTTPS、备份恢复、超时降级、真实全栈 E2E 与交接证据。

**架构：** 保持 FastAPI、PostgreSQL、Redis、MinIO、ClamAV、RAGFlow 和前端的既有职责。新增内容以端到端测试、有限职责的部署脚本和 Nginx 反向代理为主；不得改变业务 API、数据库迁移、原型或 Agent 契约。

**技术栈：** Python 3.13、pytest、FastAPI、Docker Compose、Nginx、PowerShell、TypeScript/Vitest。

## 全局约束

- 基线为 `d460a40a028480fefae718dbcf28cd55a3328a91`；任务分支只允许推送到 `codex/*`，PR 目标固定为 `codex/stage-05-integration`。
- 不新增生产依赖、数据库迁移、公开 API、认证/权限规则、兼容层或通用抽象；如实际缺口要求其中任一项，停止实施并先走变更控制。
- 附件只接受对象引用与元数据，单文件最大 100 MB；扫描、对象存储、RAGFlow 与外部 LLM 失败必须显式降级，不能伪造引用或业务结果。
- 只 Nginx 暴露 HTTPS；PostgreSQL、Redis、MinIO、ClamAV、Worker、RAGFlow 与 Elasticsearch 不得暴露公网端口。
- 真实运行用 Git 忽略的本地环境文件和仓库外的 RAGFlow Key；不得记录或打印密码、Token、Cookie、连接串或附件正文。
- Stage 6 仍锁定；本任务只形成 Stage 5 的精确候选 SHA、验证证据和 DEV→PM 交接。

## 文件结构

| 文件 | 职责 |
|---|---|
| `codebase/backend/tests/e2e/test_platform_readiness.py` | 通过真实 HTTP/容器边界验证健康、附件安全、降级与恢复契约。 |
| `codebase/infra/nginx/default.conf` | 唯一 HTTPS 入口、前端静态资源和 API/SSE 反向代理。 |
| `codebase/infra/scripts/backup.ps1` | 生成带时间戳的 PostgreSQL 逻辑备份与 MinIO 对象清单，不输出秘密。 |
| `codebase/infra/scripts/restore-verify.ps1` | 在临时 Compose 项目中恢复指定备份并读取探针，失败时保留证据。 |
| `codebase/infra/scripts/verify-platform-readiness.ps1` | 编排有限时长的 Compose、端口隔离、API、RAGFlow 与恢复验证。 |
| `codebase/infra/docker-compose.yml`、`.env.example` | 只补充 Nginx、健康检查、备份/恢复脚本所需的最小配置。 |
| `06-testing/TEST_PLAN.md`、`TEST_CASES.md`、`TEST_REPORT.md` | 把 TASK-011 的可执行测试、真实结果和未验证项写成正式测试材料。 |
| `08-release-handoff/*`、`05-development/*`、`workflow/DEV_TO_PM_HANDOFF.md` | 更新部署、回滚、发布前检查、开发自测、检查点与交接，不宣称发布。 |

---

### 任务 1：建立 E2E 红灯测试与测试环境护栏

**文件：**

- Create: `codebase/backend/tests/e2e/__init__.py`
- Create: `codebase/backend/tests/e2e/test_platform_readiness.py`
- Modify: `codebase/backend/pyproject.toml`（仅当现有 pytest 配置无法发现 `tests/e2e` 时）

- [ ] **步骤 1：写出不依赖真实秘密的失败测试。**

  测试固定使用 `httpx` 或 `TestClient` 访问现有 `/healthz`；通过注入现有的 `knowledge_storage`、`knowledge_scanner` 和 `knowledge_adapter` 假对象断言：扫描失败不产生对象引用、RAGFlow 超时返回既有 `UNAVAILABLE`/人工流程状态、健康分服务异常不返回旧值或 `0`。测试数据使用随机 `uuid4()` 标识，禁止硬编码真实 Key。

- [ ] **步骤 2：确认红灯原因是缺少 TASK-011 的执行路径。**

  Run: `python -m pytest codebase/backend/tests/e2e/test_platform_readiness.py -q`

  Expected: 失败信息只指出 E2E 模块、测试夹具或运行配置尚未存在；不得因为真实 Docker、RAGFlow Key 或公网访问缺失而把测试写成假绿。

- [ ] **步骤 3：实现最小测试夹具。**

  夹具只从显式环境变量读取运行地址与临时测试用户；缺失时 `pytest.skip("TASK-011 live-stack environment is not configured")`。单元可替代路径必须明确断言服务端返回值，不引入新的 service/factory/adapter。

- [ ] **步骤 4：运行最小回归。**

  Run: `python -m pytest codebase/backend/tests/e2e/test_platform_readiness.py codebase/backend/tests/test_health.py -q`

  Expected: 本地无 live-stack 时仅有带原因的跳过；已存在健康测试全部通过。

- [ ] **步骤 5：提交检查点。**

  `git add codebase/backend/tests/e2e codebase/backend/pyproject.toml; git commit -m "test(task-011): add readiness e2e coverage"`

### 任务 2：补齐附件与健康分的端到端失败路径

**文件：**

- Modify: `codebase/backend/tests/e2e/test_platform_readiness.py`
- Modify: `codebase/backend/tests/modules/test_maintenance_lifecycle.py`（仅在已有附件引用校验缺少边界时）
- Modify: `codebase/backend/tests/modules/test_health_score.py`（仅在已有失败值断言缺少边界时）

- [ ] **步骤 1：为附件边界补充失败断言。**

  覆盖 `size_bytes > 104857600`、不允许的 MIME、扫描超时/感染、对象存储写入失败；每种结果必须拒绝业务提交且无 `object_key`、无敏感内容进入审计。复用已有 maintenance schema 与 audit assertion，不创建第二套附件模型。

- [ ] **步骤 2：运行并观察红灯。**

  Run: `python -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q`

  Expected: 新增断言在实现前失败，且原有维修生命周期测试不受影响。

- [ ] **步骤 3：在现有实现边界补齐最小逻辑。**

  仅修改已存在的 maintenance schema/service 或 health-score read boundary：校验大小/MIME、把扫描和存储异常转换为稳定业务错误、让健康分异常保持显式失败。不得改变路由、迁移、权限码、Agent 或审计表结构。

- [ ] **步骤 4：验证绿灯与降级契约。**

  Run: `python -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py codebase/backend/tests/modules/test_health_score.py codebase/backend/tests/e2e/test_platform_readiness.py -q`

  Expected: 通过或仅 live-stack 测试按显式原因跳过；无异常被吞掉、无旧健康分或伪造附件引用。

- [ ] **步骤 5：提交检查点。**

  `git add codebase/backend/app codebase/backend/tests; git commit -m "fix(task-011): enforce attachment and health failure boundaries"`

### 任务 3：配置 Nginx HTTPS 与容器暴露边界

**文件：**

- Create: `codebase/infra/nginx/default.conf`
- Modify: `codebase/infra/docker-compose.yml`
- Modify: `codebase/infra/.env.example`
- Create: `codebase/infra/tests/verify-nginx-contract.ps1`

- [ ] **步骤 1：写静态契约测试。**

  脚本解析 `docker compose ... config --format json`，断言仅 `nginx` 有宿主机发布端口；`postgres`、`redis`、`minio`、`clamav`、`worker`、`migrate`、`validator` 均没有 `ports`；Nginx 配置必须将 `/api/` 代理到 `api`，并对 `/api/agent/runs/` 保留 SSE 的 `proxy_buffering off` 与有限超时。

- [ ] **步骤 2：运行红灯。**

  Run: `powershell -NoProfile -File codebase/infra/tests/verify-nginx-contract.ps1`

  Expected: 在 Nginx 服务与配置尚不存在时失败，错误只说明缺少入口或边界。

- [ ] **步骤 3：以最小 Compose/Nginx 配置实现。**

  Nginx 使用环境变量提供的证书路径；本地开发仅绑定 `127.0.0.1`，禁止提交真实证书。健康检查访问 Nginx 的 `/healthz` 反向代理；前端如尚无容器镜像，先以 `api` 反代和静态占位页覆盖，不新增前端框架或依赖。

- [ ] **步骤 4：验证配置与端口隔离。**

  Run:

  ```powershell
  docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
  powershell -NoProfile -File codebase/infra/tests/verify-nginx-contract.ps1
  git diff --check
  ```

  Expected: 三条命令退出码为 0；证书缺失时启动必须明确失败，不允许降级为公网明文 HTTP。

- [ ] **步骤 5：提交检查点。**

  `git add codebase/infra; git commit -m "feat(task-011): add nginx ingress boundary"`

### 任务 4：实现可验证的备份、恢复与重启演练

**文件：**

- Create: `codebase/infra/scripts/backup.ps1`
- Create: `codebase/infra/scripts/restore-verify.ps1`
- Create: `codebase/infra/scripts/verify-platform-readiness.ps1`
- Modify: `codebase/infra/docker-compose.yml`（仅注入脚本需要的命令/健康信息）

- [ ] **步骤 1：写失败保护测试。**

  为 `backup.ps1` 设计 Pester 不可用时的 PowerShell 自检：缺失本地 env 文件、目标目录不是空或受控路径、备份文件不存在、恢复项目名与生产项目相同，均 `throw`。脚本不得执行 `down -v`、递归删除工作区或读取/输出秘密。

- [ ] **步骤 2：实现备份脚本。**

  参数固定为 `-EnvFile`、`-OutputDirectory`、`-ProjectName`。脚本用 `docker compose exec -T postgres pg_dump --format=custom` 生成时间戳文件，用 MinIO S3 API 产生对象清单；写入 SHA-256 清单和不含秘密的元数据 JSON。未成功完成全部步骤时退出非零且保留现有证据。

- [ ] **步骤 3：实现恢复验证脚本。**

  参数固定为 `-EnvFile`、`-BackupDirectory`、`-ProjectName`。只接受新生成、带随机后缀的临时 Compose 项目；启动数据库/对象存储、执行 `pg_restore`、使用 API/S3 回读随机探针、再执行有限重启和健康轮询。成功后只清理该临时项目；失败不删卷。

- [ ] **步骤 4：运行安全自检与真实演练。**

  Run:

  ```powershell
  $Task011EnvFile = "codebase/infra/.env.local"
  $Task011BackupDirectory = "$env:TEMP/equipment-task011-backups"
  powershell -NoProfile -File codebase/infra/scripts/backup.ps1 -EnvFile $Task011EnvFile -OutputDirectory $Task011BackupDirectory -ProjectName equipment-task011
  powershell -NoProfile -File codebase/infra/scripts/restore-verify.ps1 -EnvFile $Task011EnvFile -BackupDirectory $Task011BackupDirectory -ProjectName equipment-task011
  ```

  Expected: 恢复项目与原项目隔离、探针经 PostgreSQL 和 S3 API 回读一致、重启后 `/healthz` 正常；输出不含秘密。

- [ ] **步骤 5：提交检查点。**

  `git add codebase/infra; git commit -m "test(task-011): verify backup and restore readiness"`

### 任务 5：执行真实全栈 E2E、安全与降级演练

**文件：**

- Modify: `codebase/backend/tests/e2e/test_platform_readiness.py`
- Modify: `codebase/infra/scripts/verify-platform-readiness.ps1`
- Modify: `06-testing/TEST_PLAN.md`
- Modify: `06-testing/TEST_CASES.md`
- Create: `06-testing/TEST_REPORT.md`

- [ ] **步骤 1：定义可复现验证矩阵。**

  将 AC-029—038、NFR-001—009 映射到具体命令、测试用户、期望响应与证据：Agent/RAGFlow 不可用的人工维修回退、线程隔离、秘密脱敏、附件扫描拒绝、健康分失败、Nginx 端口隔离、容器重启、RAGFlow 引用、备份恢复。

- [ ] **步骤 2：运行本地全量回归。**

  ```powershell
  python -m pytest codebase/backend/tests -q
  npm --prefix codebase/frontend test -- --run
  npm --prefix codebase/frontend run build
  Get-ChildItem '06-testing\tests' -Filter '*.test.js' | ForEach-Object { node $_.FullName }
  ```

  Expected: 记录精确 passed/skipped/warnings；不把跳过记为通过。

- [ ] **步骤 3：运行真实 Docker/RAGFlow 演练。**

  `verify-platform-readiness.ps1` 先检查 Docker Linux engine、本地 env 文件和仓库外 RAGFlow Key，再启动临时项目并调用现有 TASK-005 live-stack 验证、TASK-009 真实 Agent 路由、Nginx HTTPS、附件/降级、重启和恢复脚本。每一步设有限时；失败时报告服务与断言，不输出日志秘密。

- [ ] **步骤 4：记录结果和残余风险。**

  `TEST_REPORT.md` 必须包含精确 HEAD、环境、命令、原始结果摘要、跳过原因、已关闭缺陷和未关闭风险。真实证据缺少时标记 `BLOCKED`，不得写成通过。

- [ ] **步骤 5：提交检查点。**

  `git add codebase/backend/tests/e2e codebase/infra 06-testing; git commit -m "test(task-011): record platform readiness evidence"`

### 任务 6：完成 Stage 5 交接、复审和合入准备

**文件：**

- Modify: `05-development/DEV_NOTES.md`
- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `08-release-handoff/RUNBOOK.md`
- Modify: `08-release-handoff/DEPLOYMENT_CHECKLIST.md`
- Modify: `08-release-handoff/ROLLBACK_PLAN.md`
- Modify: `08-release-handoff/RELEASE_NOTES.md`
- Modify: `08-release-handoff/HANDOFF.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`

- [ ] **步骤 1：更新运维与回滚材料。**

  记录 HTTPS 证书前置条件、启动/停止、备份/恢复、端口隔离、RAGFlow Key 保管、故障排查和选择性回退命令。明确 `down -v` 不属于常规操作，Stage 6/7/生产发布均未获批准。

- [ ] **步骤 2：三轮自审。**

  Standards：核对 AGENTS、任务书、无新增依赖/迁移/API/兼容层。Spec：逐项核对 NFR、AC、失败路径与禁用边界。Diff：运行 `git diff --check origin/codex/stage-05-integration...HEAD`，并确认没有原型、秘密、生成目录或无关重构。

- [ ] **步骤 3：生成精确 HEAD 和交接。**

  更新检查点、真实自测、已知限制、回滚方式和 DEV-002 需要复核的 Agent/前端证据；提交后执行 `git rev-parse HEAD`。

- [ ] **步骤 4：创建 Draft PR 并请求 DEV-002 复审。**

  标题：`[TASK-011] test: verify platform readiness and operations`；描述包含任务/AC、精确 HEAD、文件范围、真实命令结果、未验证项、风险、回滚、依赖/兼容/抽象层/无关修改声明。HEAD 变化后必须重新请求 DEV-002 审核。

## 计划自检

- 覆盖：任务书的健康分、附件、Nginx HTTPS、备份恢复、超时降级、全量 E2E、安全恢复演练和开发交接均对应任务 1—6。
- 边界：不把 Stage 6 结论、Stage 7 验收或生产发布写入 TASK-011 成功条件；不修改批准原型、公开 API、迁移或权限。
- 验证：每个实现单元先有红灯测试，再转绿；真实 Docker/RAGFlow 与恢复证据无法取得时明确 `BLOCKED`。
