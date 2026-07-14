# 用户入口与权限范围用户管理实施计划

**目标：** 在静态原型中实现右上角用户胶囊菜单、个人资料/安全设置弹窗，并让系统管理用户页按 `user_management.view_all` 展示全量、授权范围或本人视图。

**架构：** 复用 `assets/app.js` 作为跨页面用户入口行为层；在各业务页的 topbar 注入统一用户胶囊和菜单；在 `system-management.html` 保留现有管理列表，并增加权限上下文与 self-only 渲染分支。原型仅模拟状态，不接入真实认证。

**技术栈：** HTML、CSS、原生 JavaScript、现有静态测试脚本。

## Global Constraints

- 不新增数据导入功能。
- 不改变 Stage 2/3 审批状态。
- 服务端权限是正式系统事实；原型只模拟 `user_management.view_all`。
- 完成后必须通过 `06-testing/tests/*.test.js`、JavaScript 语法检查和 `git diff --check`。

## Tasks

### Task 1: 统一用户入口

**Files:** `03-ui-prototype/prototype/assets/app.js`; all 11 pages containing `.user-chip`.

- 将用户胶囊改为带按钮语义、下拉箭头和 `data-user-menu-trigger`。
- 在 topbar 注入身份摘要、个人资料、安全设置、权限用户管理和退出登录菜单。
- 在 `app.js` 实现打开/关闭、外部点击、Escape、个人资料弹窗、安全设置校验、退出确认和系统管理跳转。

### Task 2: 权限范围用户管理

**Files:** `03-ui-prototype/prototype/pages/system-management.html`.

- 使用原型会话权限变量模拟 `user_management.view_all`。
- 有权限时保留组织树、搜索、角色/状态筛选和用户操作。
- 无权限时隐藏用户列表管理工具，展示“我的账号”卡片和修改密码入口。
- 支持 `?tab=users` 自动激活用户管理 Tab。

### Task 3: Regression evidence

**Files:** `06-testing/tests/user-entry-management.test.js`.

- 检查 11 个页面包含统一用户入口标记。
- 检查用户菜单动作、权限标记、self-only 文案和 query-tab 跳转存在。
- 运行全部静态检查、语法检查和差异检查。
