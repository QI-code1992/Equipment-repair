const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "..", "03-ui-prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");
const segPanel = html.match(/<section class="upload-step-panel" data-upload-panel="3"[\s\S]*?<section class="upload-step-panel" data-upload-panel="4"/)?.[0] || "";

assert(segPanel.includes("data-seg-current-label"), "分段预览应展示当前切片序号");
assert(segPanel.includes("data-seg-prev") && segPanel.includes("data-seg-next"), "分段预览应支持上一段/下一段切换");
assert((segPanel.match(/data-seg-chunk="/g) || []).length >= 4, "右侧切片卡片应可点击并带 data-seg-chunk");
assert((segPanel.match(/data-seg-source="/g) || []).length >= 4, "左侧原文片段应有可定位的来源锚点");
assert((segPanel.match(/data-raptor-summary/g) || []).length >= 4, "每个切片卡片应包含可折叠 RAPTOR 摘要");
assert(segPanel.includes("RAPTOR 摘要"), "切片卡片底部应展示 RAPTOR 摘要折叠入口");
assert(html.includes("function selectSegChunk"), "应实现选择切片的交互函数");
assert(html.includes("scrollIntoView"), "选择切片后应定位到左侧原文片段");

console.log("intelligent-config segment preview checks passed");
