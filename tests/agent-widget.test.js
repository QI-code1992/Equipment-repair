const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const appJs = fs.readFileSync(path.join(root, "prototype/prototype/assets/app.js"), "utf8");
const appCss = fs.readFileSync(path.join(root, "prototype/prototype/assets/app.css"), "utf8");
const globalAgentPath = path.join(root, "prototype/prototype/assets/global-agent.js");
const globalAgentJs = fs.existsSync(globalAgentPath) ? fs.readFileSync(globalAgentPath, "utf8") : "";
const equipmentDetail = fs.readFileSync(path.join(root, "prototype/prototype/pages/equipment-detail.html"), "utf8");
const pagesDir = path.join(root, "prototype/prototype/pages");
const businessPages = fs.readdirSync(pagesDir)
  .filter((file) => file.endsWith(".html") && file !== "login.html")
  .map((file) => ({
    file,
    html: fs.readFileSync(path.join(pagesDir, file), "utf8")
  }));

function assertIncludes(source, needle) {
  if (!source.includes(needle)) {
    throw new Error(`Expected to find ${needle}`);
  }
}

function assertNotIncludes(source, needle) {
  if (source.includes(needle)) {
    throw new Error(`Expected not to find ${needle}`);
  }
}

function assertBefore(source, first, second) {
  const firstIndex = source.indexOf(first);
  const secondIndex = source.indexOf(second);
  if (firstIndex < 0 || secondIndex < 0 || firstIndex > secondIndex) {
    throw new Error(`Expected ${first} before ${second}`);
  }
}

assertIncludes(globalAgentJs, "initGlobalAgentWidget");
assertIncludes(globalAgentJs, "removeLegacyAgentDrawer");
assertIncludes(globalAgentJs, "AI故障上报");
assertIncludes(globalAgentJs, "智能问数");
assertIncludes(globalAgentJs, "智能问数已就绪");
assertIncludes(globalAgentJs, "推荐问题");
assertIncludes(globalAgentJs, "conversationSuggestionsHTML");
assertIncludes(globalAgentJs, "hasUserTurn");
assertIncludes(globalAgentJs, "if (!hasUserTurn(tab)) return \"\";");
assertIncludes(globalAgentJs, "data-agent-suggestion");
assertIncludes(globalAgentJs, "你可以继续问");
assertIncludes(globalAgentJs, "已填入建议问题，可修改后发送");
assertIncludes(globalAgentJs, "askAnswerHTML");
assertIncludes(globalAgentJs, "detectAskIntent");
assertIncludes(globalAgentJs, "buildAskResult");
assertIncludes(globalAgentJs, "buildAskFollowupQuestions");
assertIncludes(globalAgentJs, "askFollowupsHTML");
assertIncludes(globalAgentJs, "addMsg(\"ask\", \"bot\", askAnswerHTML(result, text));");
assertIncludes(globalAgentJs, "result.metrics.map");
assertIncludes(globalAgentJs, "result.columns.map");
assertIncludes(globalAgentJs, "维修超期集中在备件等待和外协检测两个环节");
assertIncludes(globalAgentJs, "待接单故障单按紧急程度排序后");
assertIncludes(globalAgentJs, "故障频次排行显示");
assertIncludes(globalAgentJs, "报告摘要已按管理层口径整理");
assertIncludes(globalAgentJs, "const recommendedCard = hasUserTurn(\"ask\") ? \"\" :");
assertIncludes(globalAgentJs, "return `${renderMessages(\"ask\")}${recommendedCard}`;");
assertIncludes(globalAgentJs, "if (state.currentTab === \"ask\")");
assertIncludes(globalAgentJs, "切换查看全部设备");
assertIncludes(globalAgentJs, "这些高风险设备的主要原因是什么？");
assertIncludes(globalAgentJs, "可以生成一段报告摘要吗？");
assertIncludes(globalAgentJs, "近30天高风险设备有哪些？");
assertIncludes(globalAgentJs, "本月维修超期工单有哪些？");
assertIncludes(globalAgentJs, "一车间近7天故障最多的设备有哪些？");
assertIncludes(globalAgentJs, "待接单故障单按紧急程度排序");
assertIncludes(globalAgentJs, "ops-agent-table-wrap");
assertBefore(globalAgentJs, "智能问数已就绪", "推荐问题");
assertNotIncludes(globalAgentJs, "无时间问题");
assertNotIncludes(globalAgentJs, "条件不足示例");
assertNotIncludes(globalAgentJs, "继续追问：只看一车间");
assertIncludes(globalAgentJs, "操作指引");
assertBefore(globalAgentJs, "renderMessages(\"guide\")", "data-guide=\"how\"");
assertIncludes(globalAgentJs, "AI待提交");
assertIncludes(globalAgentJs, "近30天");
assertIncludes(globalAgentJs, "ops-agent-robot-icon");
assertIncludes(globalAgentJs, "ops-agent-robot-antenna");
assertIncludes(globalAgentJs, "scheduleFabSnap");
assertIncludes(globalAgentJs, "snapFabToNearestEdge");
assertIncludes(globalAgentJs, "isPointerInsideFab");
assertIncludes(globalAgentJs, "const snapMargin = 0");
assertIncludes(globalAgentJs, "3000");
assertNotIncludes(globalAgentJs, "<span class=\"ops-agent-fab-icon\" aria-hidden=\"true\">AI</span>");
assertNotIncludes(globalAgentJs, "<div class=\"ops-agent-logo\" aria-hidden=\"true\">AI</div>");
assertIncludes(globalAgentJs, "agentDeviceModal");
assertIncludes(globalAgentJs, "data-agent-device-search");
assertIncludes(globalAgentJs, "data-agent-device-search-button");
assertIncludes(globalAgentJs, "data-agent-device-search-result");
assertIncludes(globalAgentJs, "filterDeviceRows");
assertIncludes(globalAgentJs, "ops-agent-upload-icon");
assertIncludes(globalAgentJs, "opsAgentFileInput");
assertIncludes(globalAgentJs, "const supportsAttachment = state.currentTab === \"fault\";");
assertIncludes(globalAgentJs, "attachButton.hidden = !supportsAttachment;");
assertIncludes(globalAgentJs, "attachButton.style.display = supportsAttachment ? \"\" : \"none\";");
assertIncludes(globalAgentJs, "handleAttachmentFiles");
assertIncludes(globalAgentJs, "attachmentPanelHTML");
assertIncludes(globalAgentJs, "data-attachment-remove");
assertIncludes(globalAgentJs, "上传完成");
assertIncludes(globalAgentJs, "validateFaultStepInput");
assertIncludes(globalAgentJs, "parseUrgencyValue");
assertIncludes(globalAgentJs, "isFaultPhenomenonProvided");
assertIncludes(globalAgentJs, "当前步骤需要先选择紧急程度");
assertIncludes(globalAgentJs, "第3步：请描述故障现象");
assertIncludes(globalAgentJs, "请用一句话描述设备出现了什么异常，例如：主轴异响、振动变大、温升异常、报警停机、漏油等。");
assertIncludes(globalAgentJs, "输入后，我会继续引导发生时间和可能故障位置（非必填）。");
assertIncludes(globalAgentJs, "识别到你一次描述了多台设备");
assertNotIncludes(globalAgentJs, "当前步骤需要描述明确的故障现象");
assertIncludes(globalAgentJs, "第4步：补充信息");
assertIncludes(globalAgentJs, "data-agent-action=\"skip-optional\"");
assertIncludes(globalAgentJs, "跳过非必填，进入补充追问");
assertIncludes(globalAgentJs, "data-agent-action=\"skip-supplement-question\"");
assertIncludes(globalAgentJs, "data-agent-action=\"finish-supplement-now\"");
assertIncludes(globalAgentJs, "跳过本题");
assertIncludes(globalAgentJs, "结束追问并生成故障说明");
assertIncludes(globalAgentJs, "getSupplementQuestions");
assertIncludes(globalAgentJs, "answerSupplementQuestion");
assertIncludes(globalAgentJs, "finishSupplementQuestions");
assertIncludes(globalAgentJs, "summarizeSupplementAnswer");
assertIncludes(globalAgentJs, "补充追问 1/5");
assertIncludes(globalAgentJs, "AI大模型正在分析中");
assertIncludes(globalAgentJs, "setTimeout");
assertIncludes(globalAgentJs, "completeSupplementAnalysis");
assertIncludes(globalAgentJs, "五轮追问已完成");
assertIncludes(globalAgentJs, "大模型总结");
assertIncludes(globalAgentJs, "buildNaturalFaultDescription");
assertIncludes(globalAgentJs, "isMeaningfulSupplementAnswer");
assertIncludes(globalAgentJs, "未提供有效信息");
assertIncludes(globalAgentJs, "当前信息不足以形成有效的故障说明");
assertNotIncludes(globalAgentJs, "我已完成大模型总结，形成故障说明。");
assertNotIncludes(globalAgentJs, "`现象：${f.phenomenon || \"未填写\"}`");
assertNotIncludes(globalAgentJs, "`条件：${f.conditions || \"待现场继续补充工况、触发条件和影响范围\"}`");
assertNotIncludes(globalAgentJs, "补充信息：${");
assertIncludes(appCss, ".ops-agent-fab");
assertIncludes(appCss, ".ops-agent-table-wrap");
assertIncludes(appCss, "overflow-x: auto;");
assertIncludes(appCss, "table-layout: fixed;");
assertIncludes(appCss, "width: 72px;");
assertIncludes(appCss, "height: 72px;");
assertIncludes(appCss, "border-radius: 999px;");
assertIncludes(appCss, ".ops-agent-panel");
assertIncludes(appCss, ".ops-agent-tab.active");
assertIncludes(appCss, ".ops-agent-input.is-attach-hidden");
assertIncludes(appCss, ".ops-agent-attach[hidden]");
assertIncludes(appCss, ".ops-agent-input.is-attach-hidden .ops-agent-attach");
assertIncludes(globalAgentJs, "ops-agent-broom-icon");
assertIncludes(equipmentDetail, "../assets/app.css");
assertIncludes(equipmentDetail, "window.__GLOBAL_AGENT_CONTEXT");
assertIncludes(equipmentDetail, "../assets/global-agent.js");
assertNotIncludes(appJs, "function initGlobalAgentWidget");
assertNotIncludes(appJs, "function removeLegacyAgentDrawer");
assertNotIncludes(appJs, "initGlobalAgentWidget();");
assertNotIncludes(equipmentDetail, "function initGlobalAgentWidget()");
assertNotIncludes(equipmentDetail, "function removeLegacyAgentDrawer()");
assertNotIncludes(globalAgentJs, ">⌫</button>");
assertNotIncludes(equipmentDetail, ">⌫</button>");
assertNotIncludes(globalAgentJs, "opsAgentMin");
assertNotIncludes(globalAgentJs, "最小化");
assertNotIncludes(globalAgentJs, ">−</button>");
assertNotIncludes(equipmentDetail, "ops-agent-broom-icon");
assertNotIncludes(equipmentDetail, "opsAgentMin");
assertNotIncludes(equipmentDetail, "最小化");
assertBefore(equipmentDetail, "<span>工作台</span>", "<span>驾驶舱 BI</span>");
assertBefore(equipmentDetail, "<span>驾驶舱 BI</span>", "<span>工厂建模</span>");
assertBefore(equipmentDetail, "<span>工厂建模</span>", "<span>设备台账</span>");

for (const { file, html } of businessPages) {
  assertIncludes(html, "../assets/global-agent.js");
  assertNotIncludes(html, "function initGlobalAgentWidget()");
}

console.log("agent widget static checks passed");
