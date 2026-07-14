const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "03-ui-prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");
const tokenPanel = html.match(/<section class="config-panel" data-config-panel="tokens"[\s\S]*?<\/section>\s*<\/div>\s*<\/section>/)?.[0] || "";
const callModal = html.match(/<div class="modal-mask" data-modal="callRecordModal"[\s\S]*?<div class="modal-mask" data-modal="knowledgeFileModal"/)?.[0] || "";

assert(tokenPanel.includes("今日 Token"), "overview should include today's token card");
assert(tokenPanel.includes("总 Token"), "overview should include total token card");
assert(tokenPanel.includes("费用估算"), "overview should include estimated cost card");
assert(tokenPanel.includes("调用次数"), "overview should include call count card");
assert(tokenPanel.includes("Rerank 调用次数"), "overview and detail should keep Rerank call count");
assert(tokenPanel.includes("无法估算费用的用量"), "overview should include unpriced usage card");
assert(tokenPanel.includes("全部历史累计"), "total token metric should use all-history cumulative wording");
assert(!tokenPanel.includes("较前 30 天"), "token summary should not use period comparison wording");

assert(!tokenPanel.includes("token-toolbar"), "token page should not show the old filter/title toolbar");
assert(!tokenPanel.includes("查看各业务场景使用智能能力产生的调用量"), "token page should not show the old explanatory filter card copy");
assert(!tokenPanel.includes("<input class=\"date-input\""), "token page should not show query date filters");
assert(!tokenPanel.includes("<select><option>全部业务入口"), "token page should not show query selects");

assert(tokenPanel.includes("Token 趋势"), "trend should be token-focused");
assert(tokenPanel.includes("输入 Token") && tokenPanel.includes("输出 Token") && tokenPanel.includes("Embedding Token"), "trend should keep token dimensions");
assert(!tokenPanel.includes("费用趋势"), "trend should not include cost trend");
assert(!tokenPanel.includes("调用次数</button>"), "trend should not include inactive call-count switch button");
assert(!tokenPanel.includes("Rerank 调用次数</span></div></article>"), "trend metric strip should not show Rerank call count");

assert(!tokenPanel.includes("业务入口分布"), "business entry distribution should be removed");
assert(tokenPanel.includes("模型消耗分析"), "dashboard should show model consumption analysis");
assert(tokenPanel.includes("LLM 对话模型") && tokenPanel.includes("Embedding 向量模型") && tokenPanel.includes("Rerank 重排服务"), "model consumption should include LLM, Embedding, and Rerank");
assert(tokenPanel.includes("Agent 消耗分析"), "dashboard should keep Agent consumption analysis");

assert(tokenPanel.includes("Token 明细"), "detail table should remain available");
assert(!tokenPanel.includes("<th>触发入口</th>"), "detail table should remove trigger entry");
assert(!tokenPanel.includes("<th>计费状态</th>"), "detail table should remove billing status");
assert(tokenPanel.includes("<th>Rerank 调用次数</th>"), "detail table should keep Rerank call count");
assert(tokenPanel.includes("<th>关联调用记录</th>"), "detail table should keep trace link");
assert(tokenPanel.includes("每页 15 条"), "detail table should show 15 rows per page pagination");
assert(tokenPanel.includes("当前第 1 / 9 页"), "detail table should show pagination state");

assert(html.includes(".rank-track span { position: absolute; inset: 0 auto 0 0;"), "progress bars should align the fill to the background track");
assert(!callModal.includes("相似度最高 0.86"), "agent detail should hide similarity score text");
assert(!callModal.includes("rerank 最高 0.91"), "agent detail should hide rerank score text");
assert(!callModal.includes('status ok">0.86') && !callModal.includes('status ok">0.81'), "agent detail source score badges should be removed");

console.log("intelligent-config token usage checks passed");
