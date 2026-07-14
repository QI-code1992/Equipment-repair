const fs = require("fs");
const path = require("path");

const html = fs.readFileSync(
  path.join(__dirname, "..", "..", "03-ui-prototype", "prototype", "pages", "fault-report.html"),
  "utf8"
);

function requireText(text) {
  if (!html.includes(text)) throw new Error("Missing " + text);
}

[
  "function createRepairAiState(fault)",
  "function queueRepairPreDiagnosis(fault)",
  "function ensureRepairAiReady(fault)",
  "function discardRepairAi(fault)",
  'id="startRepairLeftScroll"',
  'id="repairAgentScroll"',
  'id="repairAgentLoading"',
  'id="repairAgentEvidence"',
  "正在检索同类设备历史维修记录",
  "预计剩余",
  "function applyRepairAgentReply(fault, reply)",
  "已确认事实",
  "data-repair-agent-choice",
  "data-repair-agent-plan",
  "采纳 AI 建议并开始维修",
  "直接开始维修",
  "function buildRepairAiSummary(fault)",
  "function startRepair(fault, { adoptAi })",
  'id="endAgentSummary"',
  "AI 诊断对话摘要",
  "3000",
  "30000",
  "if (!fault.repairAi.openedAt)",
  "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)",
  ".repair-agent-scroll {",
  "display: block",
  "overflow-x: hidden"
  ,"#startRepairModal .start-repair-shell { grid-template-columns: minmax(0, 1fr); }"
].forEach(requireText);

console.log("repair agent static checks passed");
