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
  ,"function diagnosticAgentRuntime()"
  ,"function streamAssistantMessage(fault, payload)"
  ,"function diagnosticEnough(ai)"
  ,"确认采纳 AI 建议并提交"
  ,"等待诊断完成"
  ,"AI 临时诊断不会带入结束维修"
  ,"repair-agent-streaming"
  ,"查看诊断建议与维修方案"
  ,"查看 ${escapeHtml(source.title)} 详情"
  ,"没有可验证数据时，我不能把推测当作根因"
  ,"ai.facts.length >= 4"
  ,"你提到有报警码。请把具体报码发给我"
  ,"alarmCode"
  ,"诊断过程关键信息"
  ,"fault-detail-ai-summary"
  ,"source.kind === \"case\""
  ,"以上为匹配案例的故障现象、处理方式与复测结果"
  ,"repairAgentRequiredTag"
  ,"awaitingAlarmCode"
  ,"请输入具体报警码，例如 P0xxx / 控制器报码"
  ,"function repairQuestionPlan(fault)"
  ,"电池单体与压差数据"
  ,"转向角实际值与目标值"
  ,"液压压力、油温或滤芯压差读数"
].forEach(requireText);

console.log("repair agent static checks passed");
