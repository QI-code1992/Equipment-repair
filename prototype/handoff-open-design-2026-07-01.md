# Open Design 原型交接文档（2026-07-01）

## 交接范围

本交接面向 `D:\open_design\project` 下的新能源装载机设备故障智能运维平台原型。当前重点是两个页面：

- `prototype/pages/fault-report.html`：故障上报功能，已做新增上报、开始维修、结束维修、详情、附件下载等多轮改造。
- `prototype/pages/maintenance-records.html`：维修记录功能，保留“维修概览 / 维修记录列表”双 Tab，最近重点是维修记录列表 Tab 的详情页美化。

本包同时附带：

- `prototype/index.html`
- `prototype/assets/`
- `prototype/pages/`
- `prototype/critique.json`
- `previous-handoff-2026-06-30.md`：上一版交接文档，避免重复展开历史细节。

## 视觉与产品约束

继续保持既有后台系统风格：左侧深色导航、右侧浅蓝工作区、白色卡片、细边框、低饱和状态色、高信息密度。不要改成营销页、落地页、装饰性大色块或强模板感界面。

关键禁区：

- 不要恢复设备台账指标卡片区。
- 故障状态不要恢复“已完成”，统一使用“待接单 / 维修中 / 已处理”。
- 不要恢复维修概览筛选下方的“当前筛选命中 / 筛选范围 / 数据已联动”摘要条。
- 维修记录功能需要保留两个 Tab：`维修概览` 和 `维修记录列表`。
- `维修概览` Tab 保留 6 个指标卡和 4 个图表。
- `维修记录列表` Tab 只展示搜索区和维修记录列表，不展示指标卡和图表。

## 当前故障上报功能状态

文件：`prototype/pages/fault-report.html`

已完成的主要能力：

- 新增故障上报弹窗已升级为完整录入面板。
- 设备选择后自动带出所属车间、所属产线；这两个字段只读置灰。
- 紧急程度支持“非常紧急 / 紧急 / 一般”，有紧凑样式和不同底色。
- 发生时间默认当前时间，允许改历史时间，不允许未来时间。
- 提交并生成故障单后会写入数据、关闭弹窗、清空筛选并刷新列表。
- 开始维修弹窗会带出故障上报信息：紧急程度、故障发生时间、可能故障位置、故障说明和现场附件。
- 开始维修时维修人根据当前账号自动带出，只读不可选。
- 结束维修弹窗支持必填校验，提交后将状态从维修中转为已处理，并写回处理结果。
- 故障详情已状态化展示：待接单、维修中、已处理状态分别展示对应内容。
- 附件证据支持下载。附件行本身不可点击，只有右侧“下载”链接触发浏览器下载；避免点击文件行误触发上传。

注意事项：

- 故障上报页的大量交互在页面内联脚本里，不在 `assets/app.js`。
- 修改按钮无响应、附件下载、弹窗字段时，优先检查页面内联脚本的事件绑定和缺失 DOM 引用。
- 附件原型里部分历史样例是字符串附件，会生成可下载的占位内容；新上传文件使用浏览器本地临时下载 URL。

## 当前维修记录功能状态

文件：`prototype/pages/maintenance-records.html`

已完成的主要能力：

- 页面保留 `维修概览` 和 `维修记录列表` 双 Tab。
- `维修概览` Tab 保留 6 个指标卡：总维修次数、待处理维修、平均修复时间 MTTR、平均故障间隔 MTBF、平均维修时间、维修完成率。
- `维修概览` Tab 保留 4 个图表：故障类型分布、维修时长分布、设备状态分布、故障排行 Top10。
- `维修记录列表` Tab 只保留搜索区和维修记录列表。
- 已修复 Tab 隐藏问题：`.maintenance-panel[hidden] { display: none !important; }`，避免切到列表时概览面板仍显示。
- 维修记录列表详情弹窗已多轮美化：顶部摘要状态卡、三段维修进度、关键字段、故障摘要、现场描述、维修进度、处理闭环和附件证据区。
- 维修中与已处理状态详情使用不同状态样式和文案，但仍映射自维修记录页自己的数据。

最近用户仍不满意的点：

- 用户认为“维修记录列表 Tab 的详情页面颜色单调、对齐效果差、丑陋”。已做过一轮加强，但后续最好用截图/预览继续做视觉验收，而不是只做结构校验。
- 后续如果继续改详情页，只改 `维修记录列表 Tab > 详情弹窗`，不要动 `维修概览` Tab。

## 关键文件

- `prototype/index.html`：原型入口。
- `prototype/assets/app.css`：全局后台样式。
- `prototype/assets/app.js`：全局导航、台账分页、设备新增/编辑等公共交互。
- `prototype/pages/fault-report.html`：故障上报功能，当前改动最多。
- `prototype/pages/maintenance-records.html`：维修记录功能，当前最新目标。
- `prototype/critique.json`：最近一次设计自评记录，会被覆盖。
- `previous-handoff-2026-06-30.md`：上一版完整交接文档。

## 建议下一步

1. 打开 `prototype/pages/maintenance-records.html`，切换到 `维修记录列表` Tab。
2. 点击维修中、已处理记录的“详情”，截图对比当前详情弹窗。
3. 只针对 `record-detail-*` 和 `maintenance-record-detail` 相关样式/模板继续美化。
4. 确认 `维修概览` Tab 的 KPI、图表仍存在且可切换显示。
5. 修改完成后做结构检查和内联脚本语法检查。

## 建议技能

- `brainstorming`：继续做局部设计前，先明确审美目标、信息层级和约束。
- `frontend-design`：用于维修记录详情页、故障详情页、弹窗布局、字段对齐、状态视觉等前端设计打磨。
- `systematic-debugging`：按钮无响应、Tab 显示错乱、附件下载/上传误触发时使用。
- `test-driven-development`：修复具体交互缺陷前，先写小检查确认旧实现失败。
- `verification-before-completion`：提交前确认结构、脚本语法和关键业务规则。
- `handoff`：再次交接时使用，文档保存到系统临时目录。

## 推荐检查命令

在 PowerShell 下从项目根目录 `D:\open_design\project` 执行：

```powershell
# 检查维修记录页关键结构
$path = '4be2eecd-5451-41f2-aa5b-6e771e0c1869\4be2eecd-5451-41f2-aa5b-6e771e0c1869\pages\maintenance-records.html'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
$text.Contains('id="panel-overview"')
$text.Contains('id="panel-records"')
$text.Contains('.maintenance-panel[hidden]')
$text.Contains('record-detail-hero')

# 检查故障上报页关键结构
$path = '4be2eecd-5451-41f2-aa5b-6e771e0c1869\4be2eecd-5451-41f2-aa5b-6e771e0c1869\pages\fault-report.html'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
$text.Contains('fault-media-action')
$text.Contains('submitReportForm')
$text.Contains('submitEndRepairForm')
```

脚本语法检查可用 Node 抽取页面内联脚本，注意按 UTF-8 读取，避免中文被 PowerShell 默认编码破坏。

## 交接包说明

本目录是系统临时目录下生成的交接包。`prototype/` 是核心原型文件副本，可直接打开 `prototype/index.html` 或具体页面继续检查。若要继续在原工作区修改，请回到：

`D:\open_design\project\4be2eecd-5451-41f2-aa5b-6e771e0c1869\4be2eecd-5451-41f2-aa5b-6e771e0c1869`
