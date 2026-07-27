# 开发记录

## Stage 5 最终集成总结候选（2026-07-27，等待 Gate 决定）

- 结论：DEV-001 已完成 Stage 5 最终集成总结，候选集成 HEAD 为 `8a5e6ced473ea6219666d858ce5b751e61362871`。这是供项目负责人审阅的 Gate 材料，不是 Stage 6 批准；`lastApprovedStage` 不变，任何 Stage 6 正式测试仍被禁止。
- 任务与 FCP：任务书的依赖矩阵已记录 TASK-001—TASK-011（含 TASK-006-FE）均已审核、集成或完成合并后治理；现行 `workflow/state.json` 对 TASK-002、003、005、006-FE、007、008、009、010、011 均为 `CLOSED_POST_MERGE_GOVERNANCE_COMPLETED`。对应证据集中在 `05-development/CHECKPOINTS.md` 的 FCP-001、FCP-002-R6、FCP-003、FCP-005-R6、FCP-006-DB-R2、FCP-007、FCP-008、FCP-009-R9、FCP-010-R4 和 FCP-011；历史候选 FCP 仅保留可追溯性，不作为未完成状态。
- 已合并关键链路：TASK-009 PR #49 → `0c0341b5112615780cf032b86869fa4ac205125c`；TASK-010 PR #50 → `e0c133bacf2328bdd091831450693008cb34c2ad`；TASK-011 代码/修复 PR #52、#53、#54 → `298ba147650652aed2af4dae35af640c59ff8a41`、`22f619f82ef876f86da30da38a0cf69ad008f313`、`b1e4ea6c409946667e22e4bff427c4dccaa86f22`；TASK-011 治理 PR #55、#56 → `53bdf90ec8ab743165d0542099a15d3c9de598b3`、`8a5e6ced473ea6219666d858ce5b751e61362871`。
- 回归与 live-stack：最终记录显示后端 `309 passed, 13 skipped, 2 warnings`；前端 `26 passed` 且生产构建通过；14 项静态回归、`compileall`、JSON 解析与 `git diff --check` 通过。真实 live-stack 已覆盖 PostgreSQL 迁移、真实 RAGFlow Agent 成功与受控 `UNAVAILABLE` 降级、HTTPS E2E、API 重启恢复、备份与隔离恢复，详细命令、环境隔离名和结果见 `06-testing/TEST_REPORT.md`。
- 残余风险：RAGFlow 外部依赖曾出现间歇性不可用，最终重跑通过但应在 Stage 6 持续监测；前端依赖审计有 2 项既有 high-severity 发现，未在本阶段擅自升级依赖；本总结不替代独立验证。
- 回滚：如 Stage 6 发现阻断问题，按受影响任务的 Merge Commit 使用受控 `git revert -m 1 <merge-sha>` 回退；恢复应先在隔离项目验证，禁止删除命名卷、覆盖共享数据库或直接改写集成历史。
- 建议的 Stage 6 测试计划（仅在项目负责人批准后执行）：以本候选 HEAD 固定环境，按 `06-testing/TEST_PLAN.md` 独立复核单元/API、权限与审计脱敏、Agent/SSE/引用、浏览器 E2E、RAG/附件安全、HTTPS/端口隔离、重启、备份恢复、安全与性能边界；每项记录精确 SHA、环境、夹具、结果和证据。

- 状态：Stage 5 已建立工程基线
- 候选源码：`03-ui-prototype/prototype/`（仅用于设计）
- 生产源码目录：`codebase/backend/`、`codebase/frontend/`；基础设施位于 `codebase/infra/`
- 启动条件：Stage 4 架构和实施计划获批
- 规则：实现变更通过 `workflow/CHANGE_REQUESTS.md` 返回最早受影响的基线。

## 2026-07-15 · Task 1

- 建立固定生产目录：`backend/`、`frontend/`、`infra/`。
- `GET /healthz` 依据应用名、`POSTGRES_DSN`、`REDIS_URL` 进行配置级健康判断；任一缺失返回 503，全部存在返回 200。
- Compose 服务使用内部网络，未向宿主机发布 PostgreSQL、Redis 或 API 端口。
- Docker Hub 拉取 PostgreSQL/Redis 时出现 TLS EOF；Compose 通过 `DOCKER_IMAGE_PREFIX` 支持可配置镜像前缀，开发样例指向已验证可访问的镜像镜像源。该配置不改变服务名、网络或环境变量契约。

## 2026-07-15 · CR-032 代码库目录迁移

- 将正式工程目录统一迁移为 `codebase/backend/`、`codebase/frontend/`、`codebase/infra/`。
- `03-ui-prototype/prototype/` 保持原位，继续作为 Stage 3 原型唯一事实来源；未创建 `codebase/prototype/`。
- 未保留旧目录兼容副本；后续开发、测试和部署命令必须使用 `codebase/` 路径。

## 2026-07-15 · TASK-006 非数据库切片

- 状态：TASK-006 非数据库切片已验证；TASK-006 总任务仍未完成。验证输入 HEAD 为 `f7da3393f8861e3f7b8a453629fce7079915e58e`。
- 实现提交：`33d7712334044437eba0d3fc884859d48a3c71ed`（不可变领域模型）、`7cbf76bb9ae627e023cbeaa86fd883b18a916373`（独立配置服务与两个外部端口）、`f7da3393f8861e3f7b8a453629fce7079915e58e`（未挂载 API 契约）。Tasks 1–3 已逐任务审查。
- 已完成：四个稳定 Agent ID 的领域模型、`AgentConfigRepository` 与 `ModelCatalog` 两个外部端口、单独初始化/读取/保存、模型推理能力校验、不可变且无密钥的配置快照、未挂载正式应用的 API 契约。
- 未完成：数据库仓储、迁移、事务与并发唯一性、认证/权限/审计接入、正式路由挂载、真实模型测试、前端集成。
- 依赖边界：数据库部分继续 Blocked By TASK-002；TASK-007 不得解锁。DEV-002 未执行或宣称 Docker、Compose、RAGFlow 验证通过。
- 工程声明：未新增生产依赖、兼容代码或范围外抽象；未修改 `app/main.py`、数据库、infra、前端或原型，无无关修改。
- 验证环境与结果：Python 3.13.14；模块测试 `21 passed, 1 warning`，后端全量 `25 passed, 1 warning`。两次测试均为同一条第三方 `StarletteDeprecationWarning`，无 skip 或失败。
- Task 2 非阻塞 Minor：补充空仓库 `list_all()`/未初始化读取；补充路径与请求体身份不匹配的隔离断言；对全部快照字段使用 sentinel 验证完整复制；补充数值范围精确上下边界回归。

### 2026-07-15 · TASK-006 请求校验安全加固补充

- 安全修复提交：`04e651c1453fbd0551303aff9f4d6236ea2e59d4`。路由级 `APIRoute` 捕获 FastAPI/Pydantic 前置 `RequestValidationError`，固定返回 `AGENT_CONFIG_INVALID`、安全 message 与字段列表，不返回 `input`、原始异常或请求体；路由工厂签名、Pydantic schema 和 OpenAPI 结构保持不变。
- 严格 RED/GREEN：非法 `deep_thinking_level` 敏感 sentinel、缺失 `max_reply_tokens`、`context_turns` 类型错误三个场景先分别得到预期行为断言失败，修复后三者 `3 passed`。补充验证：API `7 passed`、模块 `24 passed`、后端全量 `28 passed`，均只有既有第三方弃用 warning。
- 最终审查 Important 已关闭。正式路由仍未挂载；数据库仓储、迁移、事务/并发唯一性、认证/权限/审计、真实模型测试和前端集成仍未完成，数据库部分继续由 TASK-002 后续处理，TASK-007 不解锁。
- 既有四项 Minor 测试增强与 `AgentConfigService._validate` 约 50 行的长度关注继续作为非阻塞项，本次未扩大范围处理。未新增生产依赖、兼容代码、抽象层或无关修改。
