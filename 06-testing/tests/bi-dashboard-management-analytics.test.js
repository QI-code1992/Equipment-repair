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
assert(!html.includes('设备健康列表'), '工作台设备列表必须从驾驶舱删除');
assert(!html.includes('高风险设备 Top 5') && !html.includes('工单状态分布') && !html.includes('设备健康评分分布'), '旧版三栏分析模块必须从驾驶舱删除');
assert(!html.includes('数据同步任务') && !html.includes('知识图谱接口'), '旧版状态模块必须从驾驶舱删除');
console.log('bi dashboard management analytics static checks passed');
