# 消息通知面板实施计划

**目标：** 在现有页面顶部实现 SVG 铃铛通知入口和仅限下拉面板的业务通知交互。

**架构：** 复用 `assets/app.js` 初始化跨页面通知面板，复用 `assets/app.css` 的浮层和状态样式；页面已有铃铛按钮由共享脚本转换为 SVG 图标并绑定面板。通知数据保持本地确定性样例，点击后在面板内更新已读状态。

**技术栈：** HTML、CSS、原生 JavaScript、现有静态测试脚本。

## Tasks

### Task 1: Bell and panel shell

Modify `03-ui-prototype/prototype/assets/app.js` and `app.css` to replace text bell content with an inline SVG, add unread badge, panel header/tabs/list, outside-click/Escape handling and all-read action.

### Task 2: Notification interactions

Implement deterministic business notifications, unread/read rendering, in-panel detail expansion, load-more simulation, empty state and retry state. Exclude system notifications and independent-page navigation.

### Task 3: Regression

Add `06-testing/tests/notification-panel.test.js`; run all tests, JavaScript syntax checks, HTTP 200 smoke checks and `git diff --check`.
