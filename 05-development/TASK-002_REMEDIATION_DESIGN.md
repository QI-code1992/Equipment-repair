# TASK-002 正式审核阻断项修复设计

## 1. 文档状态

- 负责人：DEV-001
- 日期：2026-07-16
- 状态：已获项目负责人确认，待书面复核
- 修复来源：PR #15 的 DEV-002 `Changes requested`
- 被拒绝 Commit：`cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`
- 变更记录：`CR-036`
- 原设计：`05-development/TASK-002_DESIGN.md`

本设计只修复 TASK-002 对已批准基线的实现偏差，不修改 PRD、SPEC、验收标准或原型，不构成新的产品范围。

## 2. 审核结论与修复目标

DEV-002 已确认原候选的 Python 3.13 后端测试、`compileall` 和 `git diff --check` 通过，但以下阻断项未关闭：

1. TASK-002 新增的公开路由、请求、响应、错误码和幂等语义未同步到 `04-architecture-plan/API_SPEC.md`。
2. 多个受保护写操作失败时只返回错误，未持久化失败审计，也未返回 `audit_event_id`。
3. 设备主数据字段未覆盖 FR-001 和 SPEC。
4. 组织模型未覆盖根节点、工厂、车间、产线层级及其启停、唯一性和删除规则。
5. 用户更新/停用、固定角色、菜单权限和操作权限维护不完整。
6. 审计脱敏未覆盖敏感附件正文和内容字段。

修复采用“契约完整、定向补齐”方案：保留现有 Python 3.13、FastAPI、SQLAlchemy、Alembic 和 PostgreSQL 技术栈，补齐 TASK-002 的正式契约和领域规则，不进行平台级重构。

## 3. 范围边界

### 3.1 本次必须完成

- 设备完整字段、查询、创建和更新。
- 组织根节点、工厂、车间、产线的合法层级与生命周期规则。
- 用户查询、创建、更新、启停和角色分配。
- 四个固定角色及固定权限目录；维护角色—权限关系。
- 所有受保护写操作的成功/失败审计和错误 `audit_event_id`。
- 幂等键的成功重放与请求体冲突语义。
- 凭证和敏感附件内容的递归脱敏。
- `API_SPEC`、必要的数据模型文档、自动化测试及 Stage 5 交付台账同步。

### 3.2 明确延期

- 活动故障或维修中事实阻止设备停用：由 TASK-003 创建真实故障/维修事实后实现。
- 工单或维修历史阻止设备删除：由 TASK-003/TASK-004 建立真实引用后实现。
- 附件上传、MinIO/S3、扫描、下载和生命周期：由附件相关后续任务实现；TASK-002 只保存图片引用元数据并保证审计不落附件正文。
- 不增加工厂、组织或设备的行级授权过滤。

## 4. 模块设计

保持现有模块边界，并将业务规则从路由下沉到聚焦的领域服务：

- `identity`：用户管理、固定角色、权限目录和会话身份。
- `equipment`：设备主数据与组织树。
- `audit`：成功审计、统一失败审计和元数据脱敏。
- `idempotency`：成功响应重放及 Key/请求体冲突检测。

路由负责请求解析、权限依赖和响应映射；领域服务负责层级、状态、唯一性、引用保护和事务内业务规则。只拆分当前修复需要的职责，不新增通用 CRUD、Repository、Manager 或 Factory 层。

## 5. 数据模型

### 5.1 Organization

字段：

- `id`
- `type`：`ROOT`、`FACTORY`、`WORKSHOP`、`LINE`
- `code`：全局唯一
- `name`
- `parent_id`
- `sort_order`
- `enabled`
- `remark`
- `created_at`、`updated_at`

规则：

- 系统仅有一个固定根节点 `ROOT`；根节点不可停用、删除或修改类型。
- 只允许 `ROOT -> FACTORY -> WORKSHOP -> LINE`。
- `code` 全局唯一，同一父节点下 `name` 唯一。
- 停用节点时在同一事务内级联停用全部后代。
- 停用节点不能新增子节点。
- 重新启用父节点时不自动启用后代。
- 有子节点或设备引用的节点禁止删除。
- 后续任务产生的历史引用由产生该引用的任务扩展保护。

### 5.2 Equipment

字段：

- `id`
- `code`：全局唯一
- `name`
- `model`
- `type`
- `manufacturer`
- `manufactured_at`
- `commissioned_at`
- `operating_hours`：大于等于零
- `status`：`NORMAL`、`FAULT`、`REPAIRING`、`DISABLED`
- `organization_id`
- `owner_user_id`
- `image_refs`：只含对象引用与展示元数据，不含文件正文
- `created_at`、`updated_at`

设备所属组织必须存在、启用且类型为 `LINE`；负责人必须是启用用户。组织、负责人、状态和其他主数据变更均记录审计。旧 `enabled` 迁移为 `status` 后删除，不保留双事实来源兼容层。

TASK-002 不提供设备物理删除接口；依赖故障、工单和维修历史的删除规则待对应事实表存在后实现。

### 5.3 User、Role 与 Permission

用户以 `username` 为稳定登录标识，支持列表、详情、创建和更新启用状态/角色分配。禁止用户停用自己，禁止停用最后一个有效系统管理员；密码不得出现在查询响应或审计元数据中。

固定角色：

- `SYSTEM_ADMIN`
- `EQUIPMENT_ADMIN`
- `REPAIR_WORKER`
- `LINE_OPERATOR`

角色不可新增、删除或改名。权限代码使用固定目录，权限本身不可通过 API 动态增删。系统管理员始终拥有全部权限且不可削弱；其他三个角色允许更新权限集合。角色权限、用户角色和用户启停变化均记录审计。

## 6. API 契约

### 6.1 身份与权限

- `GET /api/permissions`
- `GET /api/roles`
- `PATCH /api/roles/{role_id}/permissions`
- `GET /api/users`
- `GET /api/users/{user_id}`
- `POST /api/users`
- `PATCH /api/users/{user_id}`

移除与固定角色规则冲突的 `POST /api/roles`。

### 6.2 组织

- `GET /api/organizations`
- `POST /api/organizations`
- `PATCH /api/organizations/{organization_id}`
- `DELETE /api/organizations/{organization_id}`

组织列表返回完整节点字段和 `parent_id`，调用方按父子关系构建树。

### 6.3 设备

- `GET /api/equipment`
- `GET /api/equipment/{equipment_id}`
- `POST /api/equipment`
- `PATCH /api/equipment/{equipment_id}`

`API_SPEC.md` 必须固定每个接口的权限、字段、必填项、响应、错误码、幂等要求和审计语义。

## 7. 错误响应与失败审计

受保护写操作失败统一返回：

```json
{
  "detail": {
    "code": "ORGANIZATION_CODE_EXISTS",
    "message": "组织编码已存在",
    "fields": {
      "code": "duplicate"
    },
    "audit_event_id": "审计事件 ID"
  }
}
```

- 字段校验失败：`422`。
- 唯一性或幂等冲突：`409`。
- 资源不存在：`404`。
- 权限不足：`403`。
- 业务规则阻止操作：按 `API_SPEC` 固定为 `409` 或 `422`。

失败处理顺序：

1. 回滚主业务事务。
2. 使用独立数据库事务写入失败审计。
3. 记录操作者、动作、资源、`failure`、业务错误码和脱敏后的请求摘要。
4. 审计提交成功后将事件 ID 写入错误响应。
5. 权限依赖已经写入拒绝审计时复用该事件，避免重复。

FastAPI 请求字段校验失败也进入统一处理。若审计数据库不可用，返回服务错误并记录安全日志，不伪造事件 ID，不向客户端暴露 SQL、堆栈或敏感输入。

## 8. 幂等语义

创建和更新接口要求 `Idempotency-Key`：

- 相同用户、方法、路径、Key 和请求体重放成功响应及原 `audit_event_id`。
- 相同 Key 与不同请求体返回 `409 IDEMPOTENCY_KEY_REUSED` 并记录失败审计。
- 业务失败响应不缓存；修正请求后使用新 Key 重试。
- 查询和组织删除不进入幂等响应缓存；删除仍记录成功或失败审计。

## 9. 审计脱敏

审计服务递归处理字典和列表：

- 密码、Token、Authorization、Cookie 和密钥始终脱敏。
- `attachment_content`、`file_content`、`file_bytes`、`content_base64` 等直接字段始终脱敏。
- 位于 `attachment`、`file`、`upload`、`document`、`image` 上下文中的 `body`、`content`、`data`、`bytes`、`text`、`base64` 字段脱敏。
- 文件名、类型、大小和对象引用等非正文元数据可保留。
- 普通业务对象的 `body` 或 `content` 不因字段名称相同而无条件删除。

测试覆盖嵌套对象、数组、大小写变化及凭证和附件混合输入。

## 10. Alembic 迁移

新增 `0002`，不改写远端已存在的 `0001`：

- 组织表增加完整字段和约束，并创建唯一根节点。
- 已有顶层开发数据迁入根节点；按现有深度映射工厂、车间、产线，超过三层时明确中止。
- 为旧组织生成带迁移标识的唯一编码，避免伪装成正式业务编码。
- 设备 `enabled=true/false` 映射为 `NORMAL/DISABLED`，运行时长默认为零，图片引用默认为空数组。
- 创建四个固定角色，并将当前引导管理员映射到 `SYSTEM_ADMIN`。
- 无法安全映射的自定义角色使迁移明确中止，并提示重建开发数据库，不静默丢失授权关系。

降级删除新增字段会造成数据损失；迁移说明和运行手册必须标注仅允许非生产环境在备份后执行。

## 11. 测试策略

严格按 TDD 顺序先增加失败测试，再做最小实现：

1. 设备完整字段、唯一性、组织和负责人校验。
2. 组织层级、全局编码、同级名称、级联停用和删除保护。
3. 固定角色初始化、用户更新/停用、角色权限维护及管理员保护。
4. 所有受保护写操作的成功/失败审计、字段错误和 `audit_event_id`。
5. 幂等成功重放和 Key/请求体冲突。
6. 附件正文和凭证的递归脱敏。
7. Alembic 空库升级及 `0001 -> 0002` 升级。
8. `API_SPEC` 与实际路由、字段和错误码的一致性。

完整验证包括 Python 3.13 后端测试、`compileall`、`git diff --check`、Alembic、Compose 配置、容器健康、`/healthz` HTTP 和 PostgreSQL 事务/约束行为。所有结果必须按真实输出记录，失败、跳过或未验证项不得隐藏。

## 12. 实施与交付顺序

1. 项目负责人复核本书面设计。
2. 编写详细、可执行的 TASK-002 修复实施计划。
3. 按 TDD 逐项修复阻断项并执行相关测试。
4. 同步 `API_SPEC`、必要的数据模型文档和 Stage 5 台账。
5. 运行完整验证和独立代码 Review。
6. 形成新的精确 Commit SHA，更新 FCP、`SELF_TEST`、`CODE_REVIEW`、`COMMIT_LOG`、任务书状态和交接记录。
7. 推送 `codex/task-002-identity-equipment`，更新 PR #15 并重新请求 DEV-002 审核。

在 DEV-002 复审通过前，TASK-002 保持“待审核”，不得作为已完成或可合并任务。

## 13. 实现约束自检

- 所有设计决策均已明确，无占位内容或未决产品问题。
- 不新增生产依赖。
- 不增加旧 `enabled` 兼容字段或平行权限实现。
- 不增加通用 CRUD、Repository、Manager、Factory 或其他推测性抽象。
- 不修改 PRD、SPEC、AC 或原型以迁就实现。
- 不包含 TASK-003、TASK-004 或附件存储任务的生产实现。
