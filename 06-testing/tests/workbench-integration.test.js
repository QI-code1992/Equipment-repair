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
  'function renderTrend(range)',
  'window.showToast?.("工作台数据已刷新")',
  '../assets/health-score-service.js',
  '../assets/app.js',
  '../assets/global-agent.js'
].forEach(expectText);

console.log("workbench integration static checks passed");
