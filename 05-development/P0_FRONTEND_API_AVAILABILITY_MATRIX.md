# P0 正式前端 API 可用性矩阵

- 目的：为 `DEF-STAGE7-001` 的 Stage 5 回流修复建立“批准页面 → 正式路由 → 已批准 API → 权限/状态 → 缺口”的唯一实施清单。
- 基线：`a334afd1b8cb4eeb139d78b7f5f1b5617bb2cd32`。
- 参照：`02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`、`03-ui-prototype/`、`04-architecture-plan/API_SPEC.md` 与 `codebase/backend/app/main.py` 注册的 Router。
- 规则：`AVAILABLE` 仅表示可按现有契约实现；`PARTIAL` 表示部分 P0 需明确降级或补契约；`BLOCKED_API_GAP` 禁止用原型样例或 mock 填充。Data import 已批准排除，不进入本矩阵。

无论页面当前标记为何，只有其全部 P0 功能具备已集成的真实 API、自动化和浏览器证据后才可计为完成。开发期或运行期的“数据不可用”提示只能如实呈现故障，不能作为 `PARTIAL` 页面、TASK-012 或 `DEF-STAGE7-001` 的关闭依据。

| P0 页面 / 正式路由 | 原型参考 | 已确认可消费的正式 API 与权限 | 必须覆盖的真实状态 | 结论与下一动作 |
|---|---|---|---|---|
| Login `/login` | `pages/login.html` | `POST /api/auth/login`、`GET /api/auth/me`、`DELETE /api/auth/session`；登录后 Bearer 会话 | 登录中、凭据错误、禁用、会话失效、登出 | `AVAILABLE`。正式登录页、会话恢复、受保护路由与测试可实施。 |
| Workbench `/` | `pages/workbench.html` | `GET /api/agent/health-score/{equipment_id}`（`intelligence:agent`）、`GET /api/equipment`（`equipment:read`） | 加载、无设备、健康服务失败、无权限 | `PARTIAL`。健康查询与设备入口可实现；待办、告警汇总和快捷事项无等价读取接口，列为 `API-GAP-001`。 |
| 驾驶舱 BI `/bi-dashboard` | `pages/bi-dashboard.html`、`驾驶舱BI设计细化.md` | `GET /api/metrics/catalog`、`POST /api/metrics/query-batch`（最多 5 项、`equipment:read`） | 筛选中、查询中、空、错误、无权限、图表切换 | `PARTIAL`。受控指标查询可实现；管理摘要、趋势、效率、区域/工厂/车间排行、历史对比和全局筛选聚合无等价接口，列为 `API-GAP-002`。 |
| Factory modeling `/factory-modeling` | `pages/factory-modeling.html` | `GET/POST/PATCH/DELETE /api/organizations`；`organization:read/write` | 树加载、搜索、展开/收起、表单校验、根节点/删除受阻、错误、无权限 | `AVAILABLE`。前端按 `parent_id` 构树，服务端返回阻断错误。 |
| Equipment ledger `/equipment` | `pages/equipment-ledger.html` | `GET /api/equipment`；`equipment:read` | 加载、空、筛选无结果、错误、无权限 | `AVAILABLE`。浏览器本地筛选仅作用于真实列表，不伪造分页或统计。 |
| Equipment add `/equipment/new` | `pages/equipment-add.html` | `GET /api/organizations`、`GET /api/users`、`POST /api/equipment`；`equipment:read/write` | 依赖加载、表单校验、提交中、409/422、无权限 | `AVAILABLE`。写入必须有 `Idempotency-Key`。 |
| Equipment edit `/equipment/:id/edit` | `pages/equipment-edit.html` | `GET /api/equipment/{id}`、`GET /api/organizations`、`GET /api/users`、`PATCH /api/equipment/{id}` | 初始加载、保存、409/422、设备/组织/负责人不存在、无权限 | `AVAILABLE`。不提供物理删除按钮，因为正式契约没有设备删除接口。 |
| Equipment detail `/equipment/:id` | `pages/equipment-detail.html` | `GET /api/equipment/{id}`、可选健康分读取 | 加载、404、健康不可用、无权限 | `PARTIAL`。基础详情与健康信息可实现；维修历史/实时趋势若原型要求聚合，列为 `API-GAP-003`。 |
| Fault report `/fault-report` | `pages/fault-report.html` | `POST /api/attachments`、`POST /api/fault-reports`、`POST /api/agent/fault-reports/submit`、`POST /api/agent/fault-diagnosis`、`POST /api/fault-reports/{id}/start-repair`；`fault:create/repair`、`intelligence:agent` | 草稿、附件扫描失败、校验、预诊断、追问、报警码必填、`NO_EVIDENCE`、`UNAVAILABLE`、采纳/直接开始 | `AVAILABLE`。不得在页面显示存储/扫描内部细节或原始推理链。 |
| Agent report `/agent-report` | `pages/agent-report.html` | `POST /api/agent/threads`、`/messages`、`/resume`、`GET /runs/{id}/events`、`GET /threads/{id}`，以及 `POST /api/agent/fault-reports/submit`；`intelligence:agent`、`fault:create` | 收集中、缺字段、预览、不可提交、提交成功/错误 | `AVAILABLE`。必须以真实线程和正式提交门禁实现。 |
| Global Agent 抽屉 | 原型全局脚本 | 同 Agent Runtime 契约；只允许 fault-reporting、metric-query、operation-guidance 三类 Agent | 关闭/打开、收集、预览、错误、线程访问拒绝 | `AVAILABLE`。诊断 Agent 仅由故障维修上下文创建。 |
| Maintenance records `/maintenance-records` | `pages/maintenance-records.html` | `GET /api/repair-cases/similar`（条件查询，`maintenance:view`） | 加载、空、错误、无权限 | `BLOCKED_API_GAP`。相似案例不能替代维修记录列表、详情和知识状态；列为 `API-GAP-004`。 |
| Repair execution `/repair-execution` | `pages/repair-execution.html` | `POST /api/work-orders/{id}/repair-result`；`fault:close` | 编辑、人工最终字段校验、提交中、状态冲突、无权限 | `PARTIAL`。提交可实现；分配工单列表、工作单详情和维修记录读取无等价接口，列为 `API-GAP-005`。 |
| System management `/system-management` | `pages/system-management.html` | `GET/POST/PATCH /api/users`、`GET/PATCH /api/roles`、`GET /api/permissions`；`identity:read/write` 与 self-only 用户读取 | 标签切换、加载、保存、403、self-only、最后管理员保护、错误 | `PARTIAL`。用户/角色/权限可实现；审计列表读取接口不存在，列为 `API-GAP-006`。 |
| Intelligent config `/intelligent-config` | `pages/intelligent-config.html` | `/api/model-providers`、`/api/model-bindings`、`/api/agent-configs`、`POST/GET /api/knowledge/documents*`、指标目录/批量查询；`intelligence:*` | 加载、保存、配置无效、知识上传/索引失败、重试、无权限、只读 | `PARTIAL`。模型、四 Agent、知识文档与受控指标可实现；调用记录、Token 用量、完整知识管线重试/只读 40 指标的读取契约需逐项核对，暂列 `API-GAP-007`。 |

## 待项目负责人确认的最小后端契约缺口

| 编号 | 缺口 | 受影响页面 | 需要先确认的范围 |
|---|---|---|---|
| API-GAP-001 | 当前用户待办、告警摘要与快捷事项读取 | Workbench | 资源定义、角色/权限、排序/筛选、空态和错误语义；不在前端计算或伪造。 |
| API-GAP-002 | BI 管理摘要、趋势、效率、组织层级排行、历史对比与全局筛选 | BI | 指标口径、时间窗、组织维度、权限、聚合来源与响应上限；可能影响架构/API 基线。 |
| API-GAP-003 | 设备详情维修历史与趋势读取 | Equipment detail | 是否提供设备级历史/趋势，数据来源、权限、分页和脱敏字段。 |
| API-GAP-004 | 维修记录列表、详情及知识状态读取 | Maintenance records | 工单/维修记录查询模型、筛选、角色权限、知识状态定义和分页。 |
| API-GAP-005 | 分配工单列表和工作单详情读取 | Repair execution | 工单分配语义、维修人员可见范围、状态、排序和读取权限。 |
| API-GAP-006 | 审计事件只读查询 | System management | 审计字段白名单、筛选、分页、权限和脱敏保证；禁止返回敏感请求摘要。 |
| API-GAP-007 | 智能配置调用记录、Token 用量、知识重试与只读指标读取 | Intelligent config | 指标来源、保留期、聚合维度、权限、重试行为和隐私边界。 |

这些缺口在获得项目负责人对精确 API 范围的确认前保持阻断；可先实现矩阵中标记为 `AVAILABLE` 的页面部分，但不得以静态样例伪造缺失业务能力。
