# 健康分与权限原型同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让静态原型通过统一健康分适配层展示一致的当前健康分，并将系统管理权限目录扩展到八个当前菜单，同时移除数据导入的当前入口。

**Architecture:** 新建浏览器全局 `window.HealthScoreService` 作为当前健康分快照的唯一原型来源。设备详情、台账、工作台和 BI 通过该服务读取分数、风险等级和分布；系统管理继续维护账号归属组织，但只维护菜单与按钮权限，不增加数据范围。

**Tech Stack:** 静态 HTML、原生浏览器 JavaScript、Node.js `node:assert/strict` 源码检查测试。

## Global Constraints

- 风险等级固定为：100 正常；80–99 低风险；60–79 中风险；40–59 高风险；0–39 严重风险。
- 评分周期仍为最近 30 天，历史展示仍为最近 60 天；本计划不改变扣分或恢复规则。
- BI 日期筛选不影响当前健康分和当前风险等级。
- 工厂建模仅定义设备位置；系统管理组织仅归属账号；本计划不增加数据权限。
- 角色固定为系统管理员、设备管理员、维修工、产线作业员。
- 数据导入为历史保留页面：保留文件，不提供当前菜单、权限或开发入口。
- 项目不是 Git 仓库；每项以测试输出和变更摘要替代提交。

---

### Task 1: 锁定统一健康分适配层契约

**Files:**
- Create: `tests/health-score-service-contract.test.js`
- Create: `assets/health-score-service.js`

**Interfaces:**
- Produces: `window.HealthScoreService.getEquipment(deviceId)`，返回 `{ id, score, risk, riskClass, updatedAt }`。
- Produces: `window.HealthScoreService.getDistribution(deviceIds?)`，返回 `{ normal, low, medium, high, severe }`。
- Produces: `window.HealthScoreService.getRisk(score)`，按五档规则返回风险等级。

- [ ] **Step 1: Write the failing test**

```js
const service = read('assets/health-score-service.js');
assert.match(service, /window\.HealthScoreService/);
assert.match(service, /getEquipment/);
assert.match(service, /getDistribution/);
assert.match(service, /score === 100/);
assert.match(service, /score >= 80/);
assert.match(service, /score >= 60/);
assert.match(service, /score >= 40/);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node tests/health-score-service-contract.test.js`  
Expected: FAIL，原因是 `assets/health-score-service.js` 尚不存在。

- [ ] **Step 3: Write the minimal implementation**

```js
(function () {
  const snapshots = {
    'EL-2024-019': { score: 82, updatedAt: '2026-07-12 14:20' },
    'EL-2023-088': { score: 68, updatedAt: '2026-07-12 14:20' },
    'EL-2022-031': { score: 72, updatedAt: '2026-07-12 14:20' }
  };
  function getRisk(score) {
    if (score === 100) return '正常';
    if (score >= 80) return '低风险';
    if (score >= 60) return '中风险';
    if (score >= 40) return '高风险';
    return '严重风险';
  }
  window.HealthScoreService = { getRisk, getEquipment, getDistribution };
}());
```

补全原型中设备列表使用的全部设备编号，保证未知设备返回 `null`，不伪造评分。

- [ ] **Step 4: Run test to verify it passes**

Run: `node tests/health-score-service-contract.test.js`  
Expected: `health-score-service-contract: passed`。

- [ ] **Step 5: Record verification**

在本计划任务下记录测试通过输出；不执行 Git 提交，因为项目无 Git 仓库。

### Task 2: 接入设备详情与设备台账

**Files:**
- Modify: `pages/equipment-detail.html:3250-3282, 4237-4280`
- Modify: `pages/equipment-ledger.html:17-39, script imports`
- Modify: `tests/health-score-drawer.test.js`
- Modify: `tests/health-score-consistency.test.js`

**Interfaces:**
- Consumes: `window.HealthScoreService.getEquipment(deviceId)`。
- Produces: 设备详情按 URL `device` 参数渲染健康分、风险等级和更新时间。
- Produces: 台账按每行设备编号从统一服务渲染评分和风险等级。

- [ ] **Step 1: Write failing assertions**

```js
assert.match(detail, /new URLSearchParams\(window\.location\.search\)/);
assert.match(detail, /HealthScoreService\.getEquipment/);
assert.match(ledger, /HealthScoreService\.getEquipment/);
assert.match(ledger, /equipment-detail\.html\?device=/);
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `node tests/health-score-drawer.test.js && node tests/health-score-consistency.test.js`  
Expected: FAIL，缺少服务调用或设备参数链接。

- [ ] **Step 3: Implement minimal page integration**

在各页原有公共脚本前加载：

```html
<script src="../assets/health-score-service.js"></script>
```

详情页通过：

```js
const deviceId = new URLSearchParams(window.location.search).get('device') || 'EL-2024-019';
const health = window.HealthScoreService?.getEquipment(deviceId);
```

只用 `health.score`、`health.risk`、`health.updatedAt` 更新环形分数、风险卡和抽屉标题；保留既有抽屉交互与扣分示例文本。台账逐行读取设备编号，渲染分数，并将“详情”链接改为带 `device` 参数。

- [ ] **Step 4: Run targeted tests to verify pass**

Run: `node tests/health-score-drawer.test.js && node tests/health-score-consistency.test.js`  
Expected: 两项均通过。

- [ ] **Step 5: Record verification**

记录通过输出；不执行 Git 提交。

### Task 3: 接入工作台与 BI 的统一当前健康分快照

**Files:**
- Modify: `pages/workbench.html:430-640`
- Modify: `pages/bi-dashboard.html:70-190, script imports`
- Modify: `tests/health-score-consistency.test.js`

**Interfaces:**
- Consumes: `window.HealthScoreService.getEquipment()`、`getDistribution()`、`getRisk()`。
- Produces: 工作台健康等级统计和 BI 健康分布均使用五档当前快照。

- [ ] **Step 1: Write failing assertions**

```js
assert.match(workbench, /HealthScoreService\.getEquipment/);
assert.match(workbench, /HealthScoreService\.getDistribution/);
assert.match(dashboard, /HealthScoreService\.getDistribution/);
assert.doesNotMatch(dashboard, /0-59 高\/严重风险/);
assert.doesNotMatch(dashboard, /健康分低于 60，自动转入故障分析/);
```

- [ ] **Step 2: Run consistency test to verify failure**

Run: `node tests/health-score-consistency.test.js`  
Expected: FAIL，原因是工作台、BI 尚未调用统一服务，且 BI 仍合并风险区间。

- [ ] **Step 3: Implement minimal integration**

工作台的设备样例保留组织与故障展示字段，但健康分改为由 `getEquipment(item.id)` 覆盖；`renderHealthLevels` 使用服务返回的 `getDistribution`。BI 使用统一服务生成当前平均分、设备健康列表和五档分布，且保留日期控件仅用于历史统计文案。将旧“自动生成工单”替换为“请进入故障上报查看并处理”。

- [ ] **Step 4: Run consistency test to verify pass**

Run: `node tests/health-score-consistency.test.js`  
Expected: `health-score-consistency: passed`。

- [ ] **Step 5: Record verification**

记录通过输出；不执行 Git 提交。

### Task 4: 扩展八菜单权限目录与四个固定角色

**Files:**
- Create: `tests/system-permission-catalog.test.js`
- Modify: `pages/system-management.html:1544-1574`

**Interfaces:**
- Produces: `permissionCatalog` 覆盖工作台、驾驶舱 BI、工厂建模、设备台账、故障上报、维修记录、系统管理、智能配置。
- Produces: 角色数组仅含系统管理员、设备管理员、维修工、产线作业员。

- [ ] **Step 1: Write the failing test**

```js
for (const label of ['工作台', '驾驶舱 BI', '工厂建模', '设备台账', '故障上报', '维修记录', '系统管理', '智能配置']) {
  assert.match(page, new RegExp(`label: "${label}"`));
}
assert.match(page, /name: "维修工"/);
assert.doesNotMatch(page, /车间主管/);
assert.doesNotMatch(page, /数据导入.*items:/);
```

- [ ] **Step 2: Run test to verify failure**

Run: `node tests/system-permission-catalog.test.js`  
Expected: FAIL，权限目录缺少驾驶舱 BI、工厂建模和智能配置等菜单。

- [ ] **Step 3: Implement minimal catalog and role update**

将 `permissionCatalog` 改为八组，每组至少有菜单查看权限和页面现有按钮对应权限。例如：

```js
{ id: 'bi', label: '驾驶舱 BI', items: [['bi:view', '查看驾驶舱'], ['bi:export', '导出报表']] },
{ id: 'intelligence', label: '智能配置', items: [['intelligence:view', '查看智能配置'], ['intelligence:model', '模型配置'], ['intelligence:agent', '智能体配置'], ['intelligence:knowledge', '知识库配置'], ['intelligence:audit', '查看调用记录']] }
```

删除数据导入权限组；将 `设备维修工` 角色名称改为 `维修工`；保持四个角色，不添加车间主管或任何数据范围字段。

- [ ] **Step 4: Run test to verify pass**

Run: `node tests/system-permission-catalog.test.js`  
Expected: `system-permission-catalog: passed`。

- [ ] **Step 5: Record verification**

记录通过输出；不执行 Git 提交。

### Task 5: 移除当前数据导入入口，保留历史页面

**Files:**
- Create: `tests/data-import-retired.test.js`
- Modify: `pages/agent-report.html`
- Modify: `pages/bi-dashboard.html`
- Modify: `pages/equipment-add.html`
- Modify: `pages/equipment-detail.html`
- Modify: `pages/equipment-edit.html`
- Modify: `pages/equipment-ledger.html`
- Modify: `pages/factory-modeling.html`
- Modify: `pages/fault-report.html`
- Modify: `pages/intelligent-config.html`
- Modify: `pages/maintenance-records.html`
- Modify: `pages/repair-execution.html`
- Modify: `pages/system-management.html`
- Modify: `pages/workbench.html`

**Interfaces:**
- Produces: 八菜单导航不含 `data-import.html`。
- Produces: `pages/data-import.html` 保留在文件系统。

- [ ] **Step 1: Write the failing test**

```js
assert.ok(fs.existsSync(path.join(root, 'pages', 'data-import.html')));
for (const page of currentPages) {
  const html = read(`pages/${page}`);
  assert.doesNotMatch(html, /href="data-import\.html"/);
  assert.doesNotMatch(html, />数据导入</);
}
```

- [ ] **Step 2: Run test to verify failure**

Run: `node tests/data-import-retired.test.js`  
Expected: FAIL，当前页面导航仍包含数据导入入口。

- [ ] **Step 3: Implement minimal navigation removal**

从十四个当前页面的侧边栏删除数据导入菜单项；不删除 `pages/data-import.html`，不修改其中的历史内容。移除与数据导入菜单有关的当前页文案和系统管理权限项。

- [ ] **Step 4: Run test to verify pass**

Run: `node tests/data-import-retired.test.js`  
Expected: `data-import-retired: passed`。

- [ ] **Step 5: Record verification**

记录通过输出；不执行 Git 提交。

### Task 6: 全量回归与浏览器验证

**Files:**
- Modify: `docs/运行说明.md`

- [ ] **Step 1: Update test commands**

在运行说明中加入：

```powershell
node tests/health-score-service-contract.test.js
node tests/system-permission-catalog.test.js
node tests/data-import-retired.test.js
```

- [ ] **Step 2: Run all source tests**

Run:

```powershell
Get-ChildItem tests -Filter *.test.js | ForEach-Object { node $_.FullName }
```

Expected: 每个测试打印 `passed`，命令退出码为 0。

- [ ] **Step 3: Browser smoke check**

启动现有静态服务器，分别打开设备详情、设备台账、工作台、驾驶舱 BI、系统管理，确认：

```text
EL-2024-019 在详情与台账显示相同当前分数和低风险等级；
BI 分布展示五档；
系统管理有八个权限组；
侧边栏没有数据导入；
data-import.html 文件仍存在。
```

- [ ] **Step 4: Record verification**

记录测试命令输出与浏览器检查结果；不执行 Git 提交。
