# AGENTS.md

## 项目定位

本项目是“新能源装载机设备故障智能运维平台”。它以 Web 平台、模块化 FastAPI 后端和受约束的 AI Agent 能力，支持设备台账、故障上报、维修执行、健康分析、知识检索与运营管理。

项目按 `formal-software-delivery-workflow` 的 Stage-Gate（阶段门）流程管理。所有 AI 会话应先识别任务属于需求、原型、架构、开发、测试、验收或发布中的哪一阶段；不得仅依赖聊天记录判断项目基线或宣称阶段完成。

## 规则优先级

1. 安全红线、用户明确指令和已批准的项目基线。
2. `formal-software-delivery-workflow` 的阶段门、变更控制、审批、检查点、验收与发布规则。
3. 本文件的项目导航和协作规则。
4. `04-architecture-plan/AGENTS.md` 的 Stage 5 编码约束（仅编码任务）。
5. 当前任务的具体要求。

本文件是项目级会话入口，不得覆盖 Stage-Gate、变更台账、审批、验收或发布规则。规则冲突或基线不一致时，停止受影响范围的工作，说明冲突并等待项目负责人确认。

## 会话开始检查

处理任务前，按任务范围读取必要文件：

- 始终读取：`README.md`、`workflow/state.json`。
- 涉及正式阶段、基线、审批或交付：同时读取 `workflow/STAGE_APPROVALS.md`、`workflow/CHANGE_REQUESTS.md` 与相关阶段文档。
- 涉及产品需求：读取 `01-requirements/PRD.md`、`01-requirements/SPEC.md`、`01-requirements/ACCEPTANCE_CRITERIA.md`。
- 涉及交互或原型：读取 `02-product-interaction-design/` 下的相关规格，以及 `03-ui-prototype/PROTOTYPE_BASELINE.md`、`03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`。
- 涉及以原型还原、修改或验收正式前端：必须额外读取 `03-ui-prototype/FRONTEND_RECONSTRUCTION_RULES.md`、对应原型 HTML/CSS/资源、页面差异矩阵及相关前端测试；按其中的 HTML 对照、目标 viewport 截图、视觉差异与完成判定执行。
- 涉及架构、接口、数据或 AI：读取 `04-architecture-plan/SYSTEM_ARCHITECTURE.md`、`API_SPEC.md`、`DATA_MODEL.md`、`ADR/ADR-001-boundary-and-source-of-truth.md` 和相关专项设计。
- 涉及代码实现、测试、集成或审查：必须额外读取 `04-architecture-plan/AGENTS.md`、`04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`、`04-architecture-plan/IMPLEMENTATION_PLAN.md`，以及相关代码和测试。

若 `workflow/state.json`、阶段审批记录或文档相互矛盾，以已批准的精确 Commit SHA 和项目负责人最新明确决定为准；在确认前不得扩大实现范围。

## 目录与真值来源

| 路径 | 内容与约束 |
| --- | --- |
| `00-opportunity/` 至 `08-release-handoff/` | Stage 0–8 的正式交付物与证据；在对应阶段目录内更新，不创建 `v1`、`final2`、`backup` 等历史副本。 |
| `workflow/` | 当前状态、审批、变更请求和双向交接台账；跨阶段流程控制的唯一位置。 |
| `03-ui-prototype/prototype/` | Stage 3 静态原型的唯一源码；不得复制或迁入正式前端。 |
| `codebase/backend/` | 正式 FastAPI 后端及服务本地测试。 |
| `codebase/frontend/` | 正式 Web 前端；当前以前端实际工程与其 `package.json` 为准。 |
| `codebase/infra/` | Docker Compose、Nginx、环境模板和运维配置；绝不提交真实 `.env`、密钥或运行卷数据。 |
| `06-testing/` | 测试计划、报告、缺陷、回归记录及跨服务/原型测试证据。 |

正式工程代码只能位于 `codebase/`；`05-development/` 只保存实施计划、检查点、评审与自测记录，不能存放生产代码。

## 已确认的技术与业务边界

- 后端基线为 Python 3.13、FastAPI；运行数据使用 PostgreSQL、Redis、MinIO 和 Docker Compose。
- AI 基线为 LangGraph、独立部署的 RAGFlow + Elasticsearch 8.11，以及外部 OpenAI 兼容 LLM API。
- 业务 API 和 PostgreSQL 是业务事实、历史维修案例和健康分的唯一来源；模型不得直接读写业务数据库、计算指标或写入业务事实。
- RAGFlow 只检索非结构化文档并返回引用；历史维修案例只来自 PostgreSQL。
- 四个 Agent（AI 故障上报、智能问数、操作指引、故障诊断）必须按各自 `agent_id` 使用独立配置；不得引入共享默认配置覆盖。
- 不输出、不持久化原始思维链；日志、测试和示例不得包含密码、Token、Cookie、密钥或敏感附件原文。
- 当前不实施工厂或设备行级隔离；仍必须实现平台账号认证、角色/菜单/操作权限，以及 Agent 线程的创建者或管理员访问限制。

## 开发与变更规则

- 只修改完成当前已批准任务所必需的文件；不顺手重构、格式化、重命名、迁移目录或升级依赖。
- 任何产品范围、PRD/SPEC、原型、公开 API、数据模型、数据库迁移、权限、部署或 CI/CD 的实质变化，先走 `workflow/CHANGE_REQUESTS.md` 的变更控制并获得确认。
- 未经明确批准，不增加生产依赖、兼容层或无真实第二调用点的抽象层。
- 对于 Stage 5 代码任务及从后续阶段回流的 Stage 5 修复，遵守 `04-architecture-plan/AGENTS.md` 的实现、测试、提交和报告规则；任务边界、依赖、负责人、分支、PR 审核与合并规则以 `DEVELOPMENT_TASK_BOOK.md` 为准。
- 原型还原不得新增、删除或替代已批准原型中的页面、模块、卡片、组件、字体层级、资源或关键交互；真实 API/权限状态只能替换演示数据。未通过专项规范规定的截图对照和完成判定，不得表述为页面完成或视觉验收通过。
- Stage 6 独立测试、测试结论和纯治理 PR 不默认继承 Stage 5 的 DEV-001/DEV-002 互审、单 Draft PR、非作者 Merge 或自批/自合并限制。发现必须修改业务代码、测试代码、数据库、基础设施、部署或运行时配置的缺陷时，先登记并回流 Stage 5，再按当前任务书完成修复、审核和集成。
- 不直接推送到 `main`。正式开发只在任务书允许的 `codex/*` 分支上进行；Stage 5 开发任务不得自批或自合并；其他阶段以已批准的阶段规则和项目负责人明确授权为准。
- 每个稳定功能单元保留可恢复提交，并在 `05-development/CHECKPOINTS.md` 记录检查点；阶段推进和验收必须绑定精确 Commit SHA。

## 验证与交付

- 先运行最小相关测试，再运行项目已配置的静态检查、格式检查或类型检查，并执行 `git diff --check`。
- 当前可用的最小后端验证命令见 `04-architecture-plan/AGENTS.md`；不得虚构不存在的前端构建、lint 或测试命令。
- 原型静态测试位于 `06-testing/tests/`；生产后端测试位于 `codebase/backend/tests/`。测试计划与真实证据归档到 `06-testing/`。
- 页面视觉对照截图、Screenshot Diff 或人工并列对照结论必须归档到 `06-testing/`，并绑定原型路径、路由、viewport 和精确 Commit SHA。
- 完成后审阅完整 diff，并如实报告：修改文件、执行命令及结果、未验证项和原因、依赖/兼容/抽象层变化，以及无关修改（应为无）。

## 维护本文件

当已批准的技术基线、目录真值来源、协作方式或安全边界发生变化时，随对应 Stage 4 基线或正式变更同步更新本文件。不要将临时任务细节、聊天结论或可从代码直接推导的实现细节写入此文件。
