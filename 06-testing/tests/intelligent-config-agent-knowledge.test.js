const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "..", "03-ui-prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");
const agentPanel = html.match(/<section class="config-panel" data-config-panel="agents"[\s\S]*?<section class="config-panel" data-config-panel="knowledge"/)?.[0] || "";
const profileBlock = html.match(/const agentKnowledgeProfiles = \{[\s\S]*?\n      \};/)?.[0] || "";

assert(
  profileBlock.includes('"故障诊断 Agent": {') &&
    profileBlock.includes('selected: ["设备类知识库"]') &&
    profileBlock.includes('locked: ["设备类知识库"]'),
  "Fault diagnosis Agent should default-bind device knowledge base as a locked binding"
);

assert(
  profileBlock.includes('"AI故障上报 Agent": {') &&
    profileBlock.includes('"AI故障上报 Agent": { tip:') &&
    profileBlock.includes('selected: [], locked: []'),
  "AI fault report Agent should not default-bind device knowledge base"
);

assert(
  html.includes("data-kb-locked") &&
    html.includes("默认绑定") &&
    html.includes("不可取消"),
  "Locked knowledge base bindings should be shown as non-removable default bindings"
);

assert(
  html.includes("function ensureLockedAgentKnowledge") &&
    html.includes("if (locked.includes(name))"),
  "Locked knowledge base bindings should be protected from removal"
);

assert(
  agentPanel.includes('data-agent-card="故障诊断 Agent"') &&
    agentPanel.includes("<span>知识库数量</span><strong>1</strong>"),
  "Fault diagnosis Agent card should show one default-bound knowledge base"
);

console.log("intelligent-config agent knowledge checks passed");
