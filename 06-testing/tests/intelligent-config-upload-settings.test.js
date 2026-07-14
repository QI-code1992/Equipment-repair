const fs = require("fs");
const path = require("path");
const assert = require("assert");

const htmlPath = path.join(__dirname, "..", "..", "03-ui-prototype", "prototype", "pages", "intelligent-config.html");
const html = fs.readFileSync(htmlPath, "utf8");
const uploadSettings = html.match(/<section class="upload-step-panel" data-upload-panel="2"[\s\S]*?<section class="upload-step-panel" data-upload-panel="3"/)?.[0] || "";
const uploadProcess = html.match(/function renderUploadProcessSummary\(\) \{[\s\S]*?\n      \}/)?.[0] || "";
const knowledgeTable = html.match(/<tbody data-knowledge-file-tbody>[\s\S]*?<\/tbody>/)?.[0] || "";

assert(html.includes("用于文件归档和筛选；切片方式需单独选择。"), "文档类型提示语应说明归档筛选与切片方式分开选择");
assert(html.includes("摘要最大 Token"), "RAPTOR token 字段应命名为摘要最大 Token");
assert(!html.includes("单段最大 Token"), "RAPTOR token 字段不应误写为单段最大 Token");
assert(html.includes('value="0.1" data-raptor-cluster-threshold'), "RAPTOR 聚类阈值默认值应为 0.1");
assert(html.includes('value="64" data-raptor-max-cluster'), "RAPTOR 最大聚类数默认值应为 64");
assert(html.includes('value="256" data-raptor-max-token'), "RAPTOR 摘要最大 Token 默认值应为 256");
assert(html.includes("请将以下分段内容总结为便于检索的短摘要"), "RAPTOR 摘要提示词应提供默认内容");
assert(html.includes("<option>GMM</option>") && html.includes("<option>AHC</option>"), "RAPTOR 聚类方法应只展示 GMM/AHC");
assert(!html.includes("不展示随机种子等技术参数，后台按默认策略处理。"), "不应展示随机种子等技术参数说明");
assert(!/后台映射|开发对接|dataset|parser_config|chunk_method|use_raptor|clustering_method|max_cluster|max_token|RAGFlow/.test(uploadSettings), "创建设置客户可见区域不应暴露后台对接字段或实现词");
assert(!uploadSettings.includes('class="field-hint"'), "创建设置字段提示应合并到问号说明内，避免破坏字段对齐");
assert(uploadProcess.includes("<div><span>初始状态</span><strong>待提交</strong></div>"), "提交前的数据处理确认页初始状态应展示待提交");
assert(!uploadSettings.includes("<option>设备类知识库</option>"), "上传知识的目标知识库类型不应出现设备类知识库");
assert(html.includes(".kb-file-name-text"), "知识文件列表应提供固定宽度的文件名文本样式");
assert(/\.kb-file-name-text\s*\{[\s\S]*text-overflow:\s*ellipsis/.test(html), "知识文件列表文件名超长时应省略显示");
assert((knowledgeTable.match(/class="kb-file-name-cell"/g) || []).length >= 4, "知识文件列表现有行的文件名称列应使用固定列样式");
assert((knowledgeTable.match(/class="kb-file-name-text" title="/g) || []).length >= 4, "知识文件列表现有行应通过悬浮展示完整文件名");
assert(html.includes('class="kb-file-name-cell"><span class="kb-file-name-text" title="${escapedFile}"'), "新增上传行也应使用文件名省略样式和悬浮完整名称");

console.log("intelligent-config upload setting checks passed");
