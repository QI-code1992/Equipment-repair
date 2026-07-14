const fs = require('fs');
const html = fs.readFileSync('03-ui-prototype/prototype/pages/bi-dashboard.html', 'utf8');
const css = fs.readFileSync('03-ui-prototype/prototype/assets/app.css', 'utf8');
const detail = fs.readFileSync('03-ui-prototype/prototype/pages/equipment-detail.html', 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(html.includes('data-bi-filter'), '驾驶舱应保留全局筛选表单');
for (const section of ['管理摘要', '趋势分析', '效率分析', '设备健康列表', '指标历史对比']) {
  assert(html.includes(section), `驾驶舱应包含${section}模块`);
}
for (const metric of ['设备健康综合评分', '故障总数', '工单总数', '工单按时完成率', '平均维修时长']) {
  assert(html.includes(metric), `管理摘要应包含${metric}`);
}
assert(html.includes('健康综合评分趋势') && html.includes('故障数量趋势') && html.includes('工单数量趋势'), '趋势区应包含三类趋势图');
assert(html.includes('设备健康列表'), '驾驶舱应包含设备健康列表');
assert(html.includes('设备编号 / 名称') && html.includes('近7天故障') && html.includes('工单状态'), '设备健康列表应包含设备健康字段');
assert(html.includes('equipment-detail.html?device=ZL-2026-08&openHealthScore=1'), '设备健康列表应提供查看分析入口');
assert(!html.includes('生成工单'), '设备健康列表不应提供生成工单操作');
assert(!html.includes('区域 / 组织 TOP 5') && !html.includes('工厂 TOP 5') && !html.includes('车间 TOP 5'), '排行区应从驾驶舱移除');
assert(css.includes('.bi-analytics-panel + .dashboard-table-card{margin-top:24px}'), '效率分析与设备列表之间应保留明确间距');
assert(html.includes('echarts@5.5.1/dist/echarts.min.js'), '趋势分析应加载 ECharts');
assert(html.includes('data-bi-chart="health"') && html.includes('data-bi-chart="faults"') && html.includes('data-bi-chart="orders"'), '趋势分析应提供三个真实图表容器');
assert(html.includes('data-bi-period'), '趋势分析应支持日周月切换');
assert(!html.includes('class="line-chart'), '趋势分析不应继续使用 CSS 模拟线条');
assert(html.includes('equipment-detail.html?device=ZL-2026-08&openHealthScore=1'), '查看分析应跳转设备详情并请求打开健康评分抽屉');
assert(detail.includes('openHealthScore') && detail.includes('openHealthDrawer()'), '设备详情页应支持通过 URL 参数自动打开健康评分明细抽屉');
console.log('bi dashboard management analytics static checks passed');
