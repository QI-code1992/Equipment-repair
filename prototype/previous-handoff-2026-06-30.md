# Open Design 原型交接文档

生成时间：2026-06-30  
目标：在另一台设备上继续修改“新能源装载机设备故障智能运维平台”原型。

## 项目定位

这是一个多页面后台原型，主题为新能源装载机设备故障智能运维平台。整体 UI 方向已经稳定为：

- 左侧深色导航 + 右侧浅色工作区。
- 白色卡片、浅蓝背景、细边框、低饱和状态色。
- 运维后台优先：信息密度、可扫描性、字段不换行、表格内部横向滚动。
- 不要做营销页、大头图、装饰性大色块或模板感强的页面。

当前页面范围已经超过最初 9 页，至少包含登录、工作台、驾驶舱 BI、设备台账、新增设备、编辑设备、设备详情、故障上报、维修记录、数据导入、诊断中心、工单管理、维修执行、系统管理、智能配置等页面。以项目实际 `pages/` 目录为准。

## 关键文件

优先继续看这些文件：

- `index.html`：原型首页入口，已接入设备新增、编辑、详情等入口。
- `assets/app.css`：全局后台样式，新增/编辑/详情页有较多公共样式。
- `assets/app.js`：全局导航高亮、台账筛选/分页、新增/编辑页 BOM/资料交互、全局 Agent 等。
- `pages/equipment-ledger.html`：设备台账列表页。
- `pages/equipment-add.html`：新增设备独立页面。
- `pages/equipment-edit.html`：设备编辑独立页面，结构与新增页一致但预填数据。
- `pages/equipment-detail.html`：正式设备详情页，已由 `mqzyjfkf-pages_equipment-detail.html.html` 归并而来。
- `pages/fault-report.html`：故障上报页面，已多轮打磨。
- `pages/maintenance-records.html`：维修记录页面，当前最新修改目标。
- `critique.json`：每轮修改后的审查记录，会被频繁覆盖。

## 已确认的产品规则

### 设备台账

- 顶部筛选区只保留：工厂、车间、产线、设备编号、设备名称、健康评分。
- 工厂 / 车间 / 产线采用级联选择，点击“查询”后才生效。
- 设备列表字段为：序号、设备编号、设备名称、型号、负责人、健康评分、操作。
- 操作包含：详情、编辑。
- 设备列表每页 10 台，当前样例 12 台。
- 指标卡片区已经删除，不要恢复。

### 新增设备

- 新增设备不再用抽屉，入口跳转 `pages/equipment-add.html`。
- 页面为直接填报，不用分步配置。
- 模块包括：
  - 设备基础信息：设备编号、设备名称、设备型号、负责人多选、所属工厂、所属车间、所属产线。
  - 设备 BOM 组成：统一列表，不再是左树右表。1 级固定为设备名称，自动带出且不可修改；用户新增分支从 2 级开始，最多 4 级。
  - 设备额定参数：列表可增删改；操作列必须保持可读，不能竖向换行。
  - 知识资料：列表展示，上传需弹窗先选择文件类型，再选择 Word/PDF 等文件；资料可删除。
- 新增页和编辑页外层宽度已改为自适应，宽表在卡片内部横向滚动。

### 设备编辑

- `pages/equipment-edit.html` 与新增设备页面结构完全相同。
- 唯一区别：编辑页预填设备已有信息。
- 台账页“编辑”按钮跳转编辑页，不用弹窗或抽屉。

### 设备详情

- 不采用抽屉形式，正式页为 `pages/equipment-detail.html`。
- `mqzyjfkf-pages_equipment-detail.html.html` 已归并为正式详情页，原文件保留为来源参考。
- 台账、工作台、BI、首页相关入口已接到正式详情页。
- 详情页所有信息只读，不应出现可编辑控件。
- 侧边导航归属“设备台账”。

### 故障上报

- 文件：`pages/fault-report.html`。
- 参考过 `mqzzgs7j-AI页面2.html` 的布局与功能，但视觉已统一到当前后台原型风格。
- 状态文案统一为：待接单、维修中、已处理。不要恢复“已完成”作为故障状态。
- 已删除页面头部说明卡和状态汇总卡。
- 故障列表每页 10 条，当前样例 12 条。
- 字段、表头、按钮、状态标签不换行，宽内容在表格内部横向滚动。
- 开始维修弹窗包含图片和视频上传入口。
- 维修结束弹窗包含故障类型下拉：电池系统故障、电驱系统故障、整车电器故障、CAN总线故障、液压装置故障、机械传动故障、冷却系统故障、其他故障。
- 页面已做过可访问性 polish：焦点归位、Tab 焦点循环、Escape 关闭、字段错误提示、语义标题等。

### 维修记录

文件：`pages/maintenance-records.html`。当前最近修改集中在这里。

页面结构：

- 两个 Tab：维修概览、维修记录列表。
- 维修概览：
  - 顶部筛选栏：时间范围、所属工厂、所属车间、所属产线。
  - 6 个指标卡：总维修次数、待处理维修、平均修复时间（MTTR）、平均故障间隔（MTBF）、平均维修时间、维修完成率。
  - ECharts 图表：故障类型饼图、维修时长柱状图、设备状态饼图、故障排行横向条形图。
  - 图表与指标需随筛选联动。
- 维修记录列表：
  - 顶部筛选栏：时间范围、所属工厂、所属车间、所属产线。
  - 列表字段与故障上报列表保持一致。
  - 仅展示维修中和已处理数据。
  - 支持查看详情、导出 CSV。
  - 不提供新增、删除、编辑。
  - 每页 10 条，当前样例 12 条。

最近明确删除：

- 维修概览筛选下方的“当前筛选命中 / 筛选范围 / 数据已联动”摘要条已删除。
- 后续不要恢复这条摘要栏。

最近明确调整：

- 用户认为维修概览筛选栏、指标卡片、图表卡片之间过于拥挤。
- 已拉开这些区域的纵向间距，增大卡片内边距，并加了平板/手机端间距回落。
- 如果继续打磨维修记录页，优先检查“留白、卡片高度、图表尺寸、筛选区与卡片区分组节奏”。

## 当前技术状态

### ECharts

`pages/maintenance-records.html` 已通过 CDN 引入：

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

图表渲染逻辑在页面内联脚本中，不在全局 `assets/app.js`。如果另一台设备离线，图表可能加载失败；页面已有空态兜底，但视觉检查时最好保证网络可访问 CDN，或者把 ECharts 本地化。

### 页面内联脚本

`fault-report.html` 和 `maintenance-records.html` 都有较多页面内联 JS。修改时建议：

- 先定位页面内 `<script>`，不要优先改 `assets/app.js`。
- 改完后抽取内联脚本做语法检查。
- 保持动态写入内容时的 HTML 转义，不要重新引入未转义插入。

### 全局脚本

`assets/app.js` 当前包含：

- 新增/编辑/详情页导航归属到设备台账。
- 设备台账筛选 + 分页，`pageSize = 10`。
- 新增/编辑设备页基础信息级联、BOM 行、新增/删除、资料上传弹窗等。
- Agent 助手与数据来源提示。

不要随意重构全局脚本，很多页面共用。

## 建议下一步

如果用户继续说“维修记录页还是丑/太挤/图表不好看”，建议按这个顺序处理：

1. 先截图或预览当前 `maintenance-records.html`，确认问题出在概览 Tab 还是列表 Tab。
2. 如果是概览 Tab：
   - 调整 `.maintenance-tab-panel`、`.maintenance-filter-card`、`.maintenance-kpi-grid`、`.maintenance-chart-grid` 的间距。
   - 检查 ECharts 容器高度是否过低或图表边距太挤。
   - 保持图表颜色低饱和，不要回到硬色块。
3. 如果是列表 Tab：
   - 保持字段不换行。
   - 宽表只允许在卡片内部横向滚动。
   - 不要增加新增/编辑/删除功能。
4. 修改后至少跑结构级检查。

如果用户继续设备台账模块：

1. 先询问要改哪个模块，除非需求已经非常具体。
2. 不要恢复台账指标卡片区。
3. 新增/编辑/详情都按独立页面处理，不要退回抽屉。

## 建议技能

下一位 agent 建议优先调用：

- `brainstorming`：当用户继续逐模块确认字段、交互、状态和联动规则时使用。
- `frontend-design`：当用户要求页面样式、布局、响应式、按钮状态、卡片密度等前端设计打磨时使用。
- `impeccable-design-polish`：当用户要求“打磨到可交付”、检查层级/间距/空态/错误态/可访问性时使用。
- `creative-director`：当用户不满意整体审美，需要先定义风格标准、资源选择、诊断和方向再改时使用。
- `echarts-chart-skill`：当继续调整维修记录页图表类型、视觉编码、ECharts option 或数据展示时使用。
- `verification-before-completion`：在声称完成前做结构、语法和关键业务规则检查。

## 推荐检查命令

在项目根目录执行。不要打印密钥或环境变量。

```bash
node --check assets/app.js
python3 -m json.tool critique.json >/dev/null
```

抽取页面内联脚本检查时，可用临时文件方式，避免直接执行页面：

```bash
python3 - <<'PY'
from pathlib import Path
import re
html = Path('pages/maintenance-records.html').read_text()
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.S)
Path('/private/tmp/maintenance-inline.js').write_text('\n;\n'.join(scripts))
PY
node --check /private/tmp/maintenance-inline.js
```

常用关键检索：

```bash
rg -n "已完成|maintenance-insight-strip|detailDrawer" pages assets critique.json
rg -n "echarts|pageSize|data-maintenance-row|data-fault-row" pages/maintenance-records.html pages/fault-report.html
```

注意：`assets/app.js` 里有些“已完成”属于通用 toast 或数据导入口径，不一定是故障状态文案。判断时要看上下文。

## 已知注意事项

- `pages/equipment-detail.html` 很大，且包含从候选文件归并来的完整内容和样式；改动前尽量精准定位，不要整文件重写。
- `critique.json` 每轮都可能被覆盖，不是历史日志，只代表最近一次审查。
- 页面截图/压缩包文件很多，不要误把旧 zip 当作最新交付版本。最新修改直接在 HTML/CSS/JS 文件中。
- 当前没有在本轮重新打包 zip。如需迁移到另一台设备，建议打包整个项目目录，而不是只拿旧的 `prototype-pages-download-*.zip`。
