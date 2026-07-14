const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");
const deviceKnowledgeRow = html.match(/<tr>[\s\S]*?EL-2024-019 维修手册\.pdf[\s\S]*?<\/tr>/)?.[0] || "";

assert(deviceKnowledgeRow.includes("设备类知识库"), "Device knowledge row should remain identifiable by its knowledge type");
assert(!deviceKnowledgeRow.includes("data-knowledge-delete"), "Device knowledge files should not be deletable from intelligent configuration");

console.log("intelligent-config device knowledge source checks passed");
