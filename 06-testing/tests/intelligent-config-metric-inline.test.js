const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const html = fs.readFileSync(path.join(root, "03-ui-prototype/prototype/pages/intelligent-config.html"), "utf8");
const metricModalStart = html.indexOf('data-modal="metricDictModal"');
const metricModal = metricModalStart >= 0 ? html.slice(metricModalStart, metricModalStart + 6000) : "";

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

assertIncludes(html, "智能问数指标管理");
assertIncludes(html, "指标管理");
assertIncludes(metricModal, "内置指标只读展示");
assertIncludes(metricModal, "内置指标口径");
assertIncludes(metricModal, "metric-card-list");
assertNotIncludes(metricModal, "新增指标");
assertNotIncludes(metricModal, "新增和编辑均在表格行内完成");
assertNotIncludes(metricModal, "data-metric-add");
assertNotIncludes(metricModal, "data-metric-delete");
assertNotIncludes(metricModal, "data-metric-save-all");
assertIncludes(html, "getConfiguredLlmModels");
assertIncludes(html, "populateAgentLlmOptions");
assertIncludes(html, "data-agent-llm-select");
assertIncludes(html, "data-default-llm=\"true\"");
assertIncludes(html, "data-agent-test");
assertIncludes(html, "testAgentConfig");
assertIncludes(html, "getAgentCardConfig");
assertIncludes(html, ".agent-kb-pick-item { display: grid; grid-template-columns: minmax(0, 1fr) auto;");
assertIncludes(html, ".agent-kb-pick-item .agent-kb-icon { display: none; }");
assertIncludes(html, "agentTestScenarios");
assertIncludes(html, "renderAgentTestModal");
assertIncludes(html, "runAgentTest");
assertIncludes(html, '"AI故障上报 Agent": { tip: "建议绑定故障案例或业务流程知识库，未绑定时仍可收集故障信息。", selected: [], locked: [] }');
assertIncludes(html, '"智能问数 Agent": { tip: "当前 Agent 可不绑定知识库，主要依赖业务 API 和指标口径。", selected: [], locked: [] }');
assertIncludes(html, '"操作指引 Agent": { tip: "建议绑定系统操作知识库，用于回答操作路径和权限说明。", selected: [], locked: [] }');
assertIncludes(html, '"故障诊断 Agent": { tip: "设备类知识库为默认绑定且不可取消；诊断时按当前设备ID精准检索设备资料，其他知识库可人工添加。", selected: ["设备类知识库"], locked: ["设备类知识库"] }');
assertIncludes(html, "data-agent-test-modal");
assertIncludes(html, "data-agent-test-input");
assertIncludes(html, "data-agent-test-result");
assertIncludes(html, "等待运行测试");
assertIncludes(html, "设备启动后液压泵附近异响");
assertIncludes(html, "近 30 天故障数量是多少");
assertIncludes(html, "如何新增一台设备");
assertIncludes(html, "驱动电机温度偏高");
assertIncludes(html, "agentPromptVersions");
assertIncludes(html, "applyPromptVersion");
assertIncludes(html, "const promptVersion = event.target.closest?.('[data-prompt-version]')");
assertIncludes(html, "editor.value = version.prompt");
assertNotIncludes(html, "Embedding 模型不能作为 Agent 对话模型。\">?</span></label><select required data-agent-llm-select");
assertNotIncludes(html, "data-metric-save-row");
assertNotIncludes(html, "data-metric-cancel-row");
assertNotIncludes(html, "toast(\"测试运行完成\")");
assertNotIncludes(html, "renderAgentTestModal(agentName);\\n        runAgentTest();");
assertNotIncludes(html, "未绑定 LLM 与知识库，无法启用或测试");
assertNotIncludes(html, "智能问数 Agent 启用时不强制绑定知识库，但必须绑定 LLM");
assertNotIncludes(html, "故障诊断检索设备类知识库时必须携带设备编号");
assertNotIncludes(html, "如输入设备编号，将优先匹配对应设备知识");
assertNotIncludes(html, "保存前建议测试运行；提示词、知识库和推理参数变更会影响 Agent 实际回答。");
assertNotIncludes(html, "回答呈现策略");
assertNotIncludes(html, "大模型会根据问题和查询结果自主选择表格、趋势或结论摘要");
assertNotIncludes(html, "结果展示格式");
assertNotIncludes(html, "表格优先");
assertNotIncludes(html, "趋势说明优先");
assertNotIncludes(html, "指标编码");
assertNotIncludes(html, "data-metric-form");
assertNotIncludes(html, "data-metric-field=\"code\"");
assertNotIncludes(html, "item.code");
assertNotIncludes(html, "data-metric-inline=\"enabled\"");

console.log("intelligent config metric inline checks passed");
