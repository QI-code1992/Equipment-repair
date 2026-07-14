const fs = require('fs');
const html = fs.readFileSync('03-ui-prototype/prototype/pages/bi-dashboard.html', 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(html.includes('data-bi-filter'), '驾驶舱应保留全局筛选表单');
for (const section of ['管理摘要', '趋势分析', '效率分析', '排行分析', '指标历史对比']) {
  assert(html.includes(section), `驾驶舱应包含${section}模块`);
}
for (const metric of ['设备健康综合评分', '故障总数', '工单总数', '工单按时完成率', '平均维修时长']) {
  assert(html.includes(metric), `管理摘要应包含${metric}`);
}
assert(html.includes('健康综合评分趋势') && html.includes('故障数量趋势') && html.includes('工单数量趋势'), '趋势区应包含三类趋势图');
assert(html.includes('区域 / 组织 TOP 5') && html.includes('工厂 TOP 5') && html.includes('车间 TOP 5'), '排行区应包含组织层级排行');
assert(html.includes('dashboard-table-card" aria-labelledby="health-table-title" hidden'), '重复的工作台设备列表必须保持隐藏');
assert(html.includes('dashboard-table-card" aria-labelledby="health-table-title" hidden'), '工作台预警处置模块必须保持隐藏');
console.log('bi dashboard management analytics static checks passed');
