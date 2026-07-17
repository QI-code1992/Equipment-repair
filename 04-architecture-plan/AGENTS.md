# AGENTS.md

## 1. 适用范围与优先级

本文件仅约束 Stage 5 开发实现。编码前必须阅读并遵守本文件。

规则优先级：安全与项目负责人明确决定 > `formal-software-delivery-workflow` 的阶段门禁和变更控制 > 本文件 > 当前任务实现细节。本文件不能绕过阶段审批、变更台账、检查点、验收或发布流程。

## 2. 技术基线

- 后端：Python 3.13、FastAPI、SQLAlchemy、Alembic。
- 数据与运行：PostgreSQL、Redis、MinIO、Docker Compose、Nginx。
- AI：LangGraph、独立 RAGFlow + Elasticsearch 8.11、外部 OpenAI 兼容 LLM API。
- 前端：TypeScript Web 前端；现有静态原型位于 `03-ui-prototype/prototype/`。
- 工程代码库：正式后端、正式前端和基础设施统一位于 `codebase/`；Stage 3 静态原型仍位于 `03-ui-prototype/prototype/`，不得复制到代码库。
- 包管理：Python 依赖以 `codebase/backend/pyproject.toml` 为准；前端依赖以 Stage 5 创建后的 `codebase/frontend/package.json` 为准。

## 3. 命令与验证

Stage 5 目标环境为 Python 3.13 和 Docker Desktop/Compose。进入 Stage 5 后，后端与 Compose 的最小基线命令为：

```bash
cd codebase/backend
python3.13 -m pytest tests/test_health.py -q
cd ../..
docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
```

Windows 可将 Python 命令替换为 `py -3.13 -m pytest tests/test_health.py -q`。原型静态回归在 macOS/Linux 使用：

```bash
for file in 06-testing/tests/*.test.js; do node "$file"; done
```

PowerShell 使用：

```powershell
Get-ChildItem '06-testing\tests' -Filter '*.test.js' | ForEach-Object { node $_.FullName }
```

当前协调环境只有 Python 3.9 且没有 Docker，不能在 Stage 4 文档修订中验证上述 Python 3.13 和 Compose 命令；`DEF-003`、`DEF-004` 记录现有阻断，实际修复和验证属于门禁后的 TASK-001。正式前端当前只有占位文件，尚无可执行的前端测试、lint 或构建命令。

Stage 5 新增命令必须同步写入 `codebase/backend/pyproject.toml` 或 `codebase/frontend/package.json`，并在 `05-development/SELF_TEST.md` 记录真实结果。每次修改至少运行最小相关测试、格式/静态检查（如项目已配置）及 `git diff --check`。不得因为当前命令已写入本文件而声称测试已经通过。

## 4. 修改边界

允许按已批准实施计划修改：`codebase/backend/`、`codebase/frontend/`、`codebase/infra/`、对应工程测试目录、`05-development/`、`06-testing/`、`08-release-handoff/`。正式代码不得放入 `05-development/`；原型及其专用资源只归档于 `03-ui-prototype/`。

禁止修改：`.env`、密钥、生成目录、`node_modules/`、容器卷数据、已归档证据；不得直接向 `main` 或 `codex/stage-05-integration` 推送。

修改以下内容前必须获得项目负责人针对具体范围的确认：生产依赖、数据库迁移、认证/权限、公开 API、部署与 CI/CD 配置、用户可见流程、PRD/SPEC/原型/验收标准。

## 5. 实现规则

- 采用满足当前任务的最小实现，优先修改现有代码。
- 不做无关重构、格式化、重命名、目录调整或依赖升级。
- 默认不增加兼容代码；仅在真实旧数据、外部调用方或部署窗口存在时，经确认后增加，并写明删除条件与测试。
- 单一场景不创建多余的 interface、factory、manager、service、adapter 或通用 helper；外部副作用边界除外。
- 普通函数目标不超过 40 行，超过 60 行需说明职责拆分；普通源文件目标不超过 300 行，超过 500 行不得继续累加职责；嵌套原则上不超过 3 层。
- 不吞掉异常，不记录密码、Token、Cookie、密钥、原始思维链或敏感附件原文。
- 四个 Agent 必须按各自 `agent_id` 的独立配置运行；历史维修案例只查 PostgreSQL，文档检索只经 RAGFlow。

## 6. 测试与提交

- 先写能证明需求尚未满足的最小失败测试，再实现并转绿。
- 测试外部行为，不为覆盖率编写无业务价值测试。
- 每个稳定功能单元须在远端 `codex/*` 分支保留可恢复提交，并记录到 `05-development/CHECKPOINTS.md`。
- Commit 格式：`type(scope): summary`；允许 `feat`、`fix`、`docs`、`test`、`refactor`、`chore`。
- PR/交付说明须包含需求或 CR、范围、测试结果、风险与回退方式、依赖/兼容/抽象层变化和无关修改说明。

## 7. PR、审核与 Merge

- 任务开发 Agent 从 `codex/stage-05-integration` 建立任务分支，并为自己的任务创建一个目标为该集成分支的 Draft PR；后续修订继续 push 到同一 PR，不因审核轮次重复创建 PR。
- 任务开发 Agent 不得批准或合并自己的 PR。完成自测和证据记录后，将同一 PR 转为 Ready，并请求任务书指定的另一 Agent 审核精确 HEAD。
- 指定审核者必须固定 PR HEAD，审查 Standards、Spec、任务边界、依赖和证据。Critical 或 Important 不为零时提交 `Changes requested`；HEAD 变化后旧批准不得继续使用。
- 审核通过后，DEV-001 Agent 负责核查目标分支、当前 HEAD、审核结论、required checks、依赖、冲突、共享契约、证据、风险和回滚。
- DEV-001 Agent 集成检查通过后，必须向项目负责人逐 PR 请求 Merge 授权；请求必须绑定 PR 编号与精确 HEAD。未获明确批准不得合并。
- 项目负责人授权后，若 HEAD、目标分支、依赖或检查结论变化，授权立即失效。DEV-001 Agent 必须重新审核或核查并重新询问。
- 只有 DEV-001 Agent 可在授权后对 Stage 5 PR 执行 Merge Commit。禁止 GitHub auto-merge、merge queue、任务开发者自行合并，以及直接 push 集成分支。
- 合并到 `codex/stage-05-integration` 不代表 Stage 5 完成或允许进入 Stage 6；合并到 `main` 仍须 Stage 6、Stage 7、Stage 8 和项目负责人发布授权。

## 8. 编码前与完成前检查

编码前确认：任务已获准、最小实现范围明确、相关测试与基线已阅读、无未经批准的新依赖或抽象。

完成前检查：审阅完整 diff；运行相关测试和已配置检查；说明真实结果、未验证项及原因；报告修改文件、依赖、兼容代码、抽象层、无关修改和当前 Commit SHA。不得仅以“已完成”作为验收结论。
