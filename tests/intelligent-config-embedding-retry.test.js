const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "03-ui-prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");

assert(
  html.includes('data-retry-embedding-index') && html.includes('>重试</button>'),
  "Embedding rebuild failure should offer a retry action"
);

assert(
  html.includes('rebuildFailed:') && html.includes('索引重建失败') && html.includes('旧模型继续提供检索'),
  "Embedding rebuild failure should keep the old model serving retrieval"
);

assert(
  html.includes('if (state === "confirmed")') &&
    !html.includes('if (state === "confirmed") {\n            knowledgeEmbeddingChecks[currentKnowledgeName] = { state: "indexing", targetEmbedding: select.value };'),
  "Submitting a rebuild should not immediately replace the active embedding model"
);

assert(
  html.includes('data-retry-embedding-index') && html.includes('重试后仍将继续使用旧模型提供检索'),
  "Retry should preserve the old embedding model until the new index succeeds"
);

console.log("intelligent-config embedding retry checks passed");
