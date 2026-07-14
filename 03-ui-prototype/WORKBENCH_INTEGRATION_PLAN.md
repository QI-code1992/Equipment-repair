# 工作台原型融合实施计划

> **执行要求：** 按任务逐项执行；每项先完成失败测试，再写最小实现，随后运行通过测试。所有产物必须提交并推送到 GitHub。

**目标：** 将外部 ZIP 的工作台视觉与交互融入现有静态原型，同时保持所有非工作台页面和现有全局能力不变。

**架构：** 工作台继续是自包含的静态 HTML 页面。其页面内脚本持有演示数据、筛选状态与渲染函数，并只依赖现有 `health-score-service.js`、`app.js` 和 `global-agent.js`；不修改共享资源。测试以 Node 静态断言锁定页面结构、关键交互钩子、详情跳转和全局 Agent 引入。

**技术栈：** HTML、内联 CSS、浏览器原生 JavaScript、Node.js 静态回归检查、Git/GitHub。

## 全局约束

- 工作台外部视觉、交互与数据以输入 ZIP 的 `equipment-repair-prototype-review/pages/workbench.html` 为准。
- 只修改工作台、其专用测试及 Stage 3/工作流记录；不得修改其他页面与共享 `app.js`、`app.css`、`global-agent.js`。
- 保留当前页面对 `../assets/health-score-service.js`、`../assets/app.js` 和 `../assets/global-agent.js` 的引入。
- 保留当前全局 AI、通知入口与导航能力；不得重新引入已移除的侧栏说明卡或废弃刷新控件。
- 完成前必须提交并推送至 `origin/main`，并在检查点记录精确 Commit SHA。

---

### Task 1：锁定工作台融合的失败回归测试

**文件：**
- 新建：`06-testing/tests/workbench-integration.test.js`
- 读取：`03-ui-prototype/prototype/pages/workbench.html`

**接口：**
- 消费：工作台页面中的 `data-*` 交互钩子和现有设备详情路由。
- 产出：命令 `node 06-testing/tests/workbench-integration.test.js`；成功时输出 `workbench integration static checks passed`。

- [ ] **Step 1：写入失败测试**

```js
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const workbench = fs.readFileSync(
  path.join(root, "03-ui-prototype/prototype/pages/workbench.html"),
  "utf8"
);

function expectText(text) {
  if (!workbench.includes(text)) throw new Error(`Expected to find ${text}`);
}

[
  'class="card scope-card" aria-label="组织范围筛选"',
  'data-metric-grid',
  'data-filter="pending"',
  'data-filter="risk"',
  'data-queue-list',
  'data-tab="veryUrgent"',
  'data-health-content',
  'data-range',
  'data-custom-dates',
  'data-trend-chart',
  'data-refresh',
  'equipment-detail.html?device=${encodeURIComponent(fault.deviceId)}',
  'function setFilter(filter)',
  'function renderTrend(days)',
  'window.showToast?.("工作台数据已刷新")',
  '../assets/health-score-service.js',
  '../assets/app.js',
  '../assets/global-agent.js'
].forEach(expectText);

console.log("workbench integration static checks passed");
```

- [ ] **Step 2：运行测试，确认它因缺少新工作台结构而失败**

运行：

```powershell
node 06-testing/tests/workbench-integration.test.js
```

预期：命令以非零状态结束，错误包含 `Expected to find class="card scope-card" aria-label="组织范围筛选"` 或第一个缺失的工作台钩子。

- [ ] **Step 3：提交测试前红灯证据（不提交代码）**

记录命令输出到本次执行日志；不创建提交，避免将已知失败测试单独推送为检查点。

### Task 2：页面级移植与最小依赖适配

**文件：**
- 修改：`03-ui-prototype/prototype/pages/workbench.html`
- 参考输入：ZIP 内 `equipment-repair-prototype-review/pages/workbench.html`
- 不修改：`03-ui-prototype/prototype/assets/app.js`
- 不修改：`03-ui-prototype/prototype/assets/app.css`
- 不修改：`03-ui-prototype/prototype/assets/global-agent.js`

**接口：**
- 消费：`HealthScoreService`、`window.showToast`、现有 `equipment-detail.html?device=<id>` 路由与全局 Agent 脚本。
- 产出：`scopeForm` 组织筛选、`setFilter(filter)` 指标/标签联动、`renderAll()` 页面刷新、`renderTrend(days)` 趋势渲染。

- [ ] **Step 1：以 ZIP 的工作台作为页面主体来源**

将 ZIP 中 `pages/workbench.html` 的以下主体结构移植到目标页面：

```html
<form class="card scope-card" aria-label="组织范围筛选">…</form>
<div class="metric-grid" data-metric-grid>…</div>
<div class="primary-grid">…<div class="queue-list" data-queue-list></div>…</div>
<article class="card trend-card">…<select aria-label="趋势时间范围" data-range>…</select>…</article>
<article class="card activity-card">…</article>
```

同时移植 ZIP 工作台中与上述结构对应的页面内 CSS、设备/故障/动态演示数据及渲染函数；不得从 ZIP 复制任何共享 `assets/` 文件。

- [ ] **Step 2：保留当前原型的全局能力和已批准清理项**

在移植后的页面末尾保留以下脚本顺序：

```html
<script src="../assets/health-score-service.js"></script>
<script>/* 工作台专用数据、筛选和渲染逻辑 */</script>
<script src="../assets/app.js"></script>
<script src="../assets/global-agent.js?v=20260714-workbench-content-contained"></script>
```

使用当前页面的通知入口、用户入口和导航内容；不复制 ZIP 内的 `.sidebar-foot`，也不添加 ZIP 内已被当前原型淘汰的全局刷新入口。工作台自身的 `data-refresh` 按钮保留。

- [ ] **Step 3：实现工作台的最小筛选与联动逻辑**

确保页面内脚本保留以下行为：

```js
function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll("[data-filter]").forEach((button) =>
    button.classList.toggle("active", button.dataset.filter === filter)
  );
  document.querySelectorAll("[data-tab]").forEach((button) =>
    button.classList.toggle("active", button.dataset.tab === filter)
  );
  renderQueue();
}

document.addEventListener("click", (event) => {
  const metric = event.target.closest("[data-filter]");
  if (metric) setFilter(metric.dataset.filter);
  const tab = event.target.closest("[data-tab]");
  if (tab) setFilter(tab.dataset.tab);
  if (event.target.closest("[data-refresh]")) {
    document.querySelector("[data-update-time]").textContent = "2026-07-14 10:30（刚刚）";
    renderAll();
    window.showToast?.("工作台数据已刷新");
  }
});
```

组织范围变化必须调用 `setFilter("all")` 后重新渲染指标、提醒、健康概览和今日概览；趋势选择为 `custom` 时显示 `data-custom-dates`，否则隐藏它并调用 `renderTrend(event.target.value)`。

- [ ] **Step 4：运行 Task 1 测试，确认绿灯**

运行：

```powershell
node 06-testing/tests/workbench-integration.test.js
```

预期：输出 `workbench integration static checks passed`，退出码为 `0`。

### Task 3：回归验证、原型检查点与 GitHub 交付

**文件：**
- 修改：`03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`
- 修改：`workflow/CHANGE_REQUESTS.md`
- 读取：`06-testing/tests/*.test.js`

**接口：**
- 消费：Task 1 的测试、现有全部静态测试与当前 `main` 分支。
- 产出：`PCP-012`、精确 Commit SHA、已推送的 GitHub 检查点。

- [ ] **Step 1：执行工作台与全量静态回归检查**

运行：

```powershell
node 06-testing/tests/workbench-integration.test.js
Get-ChildItem 06-testing/tests -Filter *.test.js | ForEach-Object { node $_.FullName; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
git diff --check
```

预期：每个测试输出成功信息，所有命令退出码均为 `0`；`git diff --check` 无输出。


- [ ] **Step 2：创建 `PCP-012` 检查点记录**

在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md` 追加检查点条目。先完成实施提交并读取 `git rev-parse HEAD`，再在记录中写入该命令的完整输出；随后用单独的文档提交推送该精确 SHA。

```md
## PCP-012: Workbench filter and detail-link integration

- 状态：Stable / awaiting Stage 3 approval
- 范围：工作台组织范围筛选、指标/待办联动、健康概览、趋势筛选、刷新反馈与设备详情跳转
- 来源：`03-ui-prototype/prototype/pages/workbench.html`
- Commit SHA：实施提交完成后由 `git rev-parse HEAD` 输出的完整 40 位 SHA
- 验证：`node 06-testing/tests/workbench-integration.test.js`；全量 `06-testing/tests/*.test.js`；`git diff --check`
- 结果：全部通过
- 恢复：使用本条记录中的 Commit SHA 执行 `git restore --source <记录的 SHA> -- 03-ui-prototype/prototype/pages/workbench.html 06-testing/tests/workbench-integration.test.js`
- 备注：非工作台页面和共享资源未修改。
```

- [ ] **Step 3：提交并推送实现与检查点**

运行：

```powershell
git add 03-ui-prototype/prototype/pages/workbench.html 06-testing/tests/workbench-integration.test.js 03-ui-prototype/PROTOTYPE_CHECKPOINTS.md workflow/CHANGE_REQUESTS.md
git commit -m "feat(prototype): integrate workbench filters"
git push origin main
git rev-parse HEAD
```

预期：推送成功；将输出的 SHA 写回 `PCP-012` 与 CR-023 验证字段，再执行一次文档提交和推送。

- [ ] **Step 4：验证远程交付状态**

运行：

```powershell
git status --porcelain=v1 --branch
git ls-remote origin refs/heads/main
```

预期：状态为 `## main...origin/main` 且远程 `main` SHA 与本地 `HEAD` 一致。
