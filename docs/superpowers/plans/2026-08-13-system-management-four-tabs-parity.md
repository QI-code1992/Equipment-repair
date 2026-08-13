# 系统管理四标签页原型还原实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将系统管理的角色管理、用户管理、登录日志和操作日志按 `system-management.html` 原型恢复为一致的桌面页面结构和交互，同时保持真实 API 边界。

**Architecture:** 只调整 `PortalPages.tsx` 内既有系统管理实现和对应局部 CSS；列表、筛选和分页使用已加载的正式数据。不存在的业务字段和写操作以原型位置上的禁用控件和明确提示表达，不创建假数据或假成功路径。

**Tech Stack:** React、TypeScript、现有 API client、Vitest、现有 CSS。

## 全局约束

- 原型唯一来源：`03-ui-prototype/prototype/pages/system-management.html`。
- 桌面视觉验收：`1440 x 900`、100% 浏览器缩放。
- 不修改原型、后端接口、权限模型、数据库迁移、依赖或部署配置。
- 不允许新增原型外的可见模块；缺失 API 的字段和动作必须受控不可用。

### Task 1: 角色管理

**Files:**
- Modify: `codebase/frontend/src/PortalPages.tsx`
- Modify: `codebase/frontend/src/styles.css`
- Test: `codebase/frontend/src/PortalPages.test.tsx`

- [x] 写失败测试，断言原型角色工具栏、列表列、状态计数、分页及角色编辑对话框。
- [x] 运行定向测试，确认因当前结构缺页脚或原型样式失败。
- [x] 用最小改动对齐角色管理结构和交互；仅 `PATCH /api/roles/{id}/permissions` 可保存，新增/删除保持受控不可用。
- [x] 运行定向测试；稳定检查点待连同四标签页一起提交。

### Task 2: 用户管理

**Files:**
- Modify: `codebase/frontend/src/PortalPages.tsx`
- Modify: `codebase/frontend/src/styles.css`
- Test: `codebase/frontend/src/PortalPages.test.tsx`

- [x] 写失败测试，断言组织树区域、原型七列表格、角色筛选、分页、新增/编辑/详情对话框及缺失字段边界。
- [x] 运行定向测试，确认失败原因是结构尚未出现。
- [x] 接入 `/api/users`、`/api/roles`；只对用户名、密码、角色和启停调用真实 API，其余原型字段明确不可用。
- [x] 运行定向测试；稳定检查点待连同四标签页一起提交。

### Task 3: 登录日志和操作日志

**Files:**
- Modify: `codebase/frontend/src/PortalPages.tsx`
- Modify: `codebase/frontend/src/styles.css`
- Test: `codebase/frontend/src/PortalPages.test.tsx`

- [x] 写失败测试，断言各自原型筛选控件、七列表格、状态标签、刷新和分页。
- [x] 运行定向测试，确认失败原因是当前四列简化表格。
- [x] 仅使用 `/api/audit-events` 返回的正式字段；不支持的姓名、IP、终端、说明以受控不可用展示，筛选在已加载数据内执行。
- [x] 运行定向测试；稳定检查点待连同四标签页一起提交。

### Task 4: 视觉证据与全量验证

**Files:**
- Modify: `06-testing/FRONTEND_PROTOTYPE_DIFFERENCE_MATRIX.md`
- Create: `06-testing/frontend-evidence/system-management/`

- [ ] 在 `1440 x 900` 捕获原型与四个正式标签页同状态截图，记录 SHA、路由、时间与数据状态。当前被浏览器对原型 `file://` 地址的安全策略阻断，且正式路由需要认证会话；不可用自动化测试替代。
- [x] 更新差异矩阵，不将未验证项标记为完成。
- [x] 运行 `npm test -- --run`、`npm run build`、`git diff --check`。
