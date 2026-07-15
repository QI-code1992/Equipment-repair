# AI/RAGFlow/LangGraph 集成基线摘要

- 状态：候选版 v2.1 / 等待 Stage 4 文档包评审
- 主依据：`平台级架构设计.md`

## 技术与边界

Python 3.13 + FastAPI；PostgreSQL 为业务库；MinIO/S3 存附件；Redis 做短期缓存和限流。RAGFlow 使用独立 Docker Compose 依赖栈，不与业务 PostgreSQL、Redis、MinIO 共享实例或账号。LangGraph 编排受控工作流并使用 PostgreSQL checkpoint；LLM 通过 OpenAI 兼容网关调用聊天、Embedding、Rerank 模型。

业务后端是唯一业务事实源和写入口。RAGFlow 只负责解析、切片、检索、重排和引用；LangGraph 只做受约束状态机、白名单工具调用、多轮补齐、人工确认和总结；LLM 不得猜测指标、权限、故障结论、维修事实或引用。

## 知识契约

业务文档保存业务文档 ID、对象存储 file ID、RAGFlow document ID、解析状态和失败原因。状态为 `UPLOADING`、`PARSING`、`READY`、`FAILED`；只有 `READY` 文档可检索。每条引用必须包含文档和切片标识。空检索必须明确返回无可引用依据。

## Agent 契约

共享状态：`thread_id`、`agent_id`、`user_id`、`role`、`page_context`、`messages`、`tool_results`、`citations`、`pending_confirmation`、`config_snapshot`、`audit_id`。线程绑定创建用户，不得跨用户复用；支持 SSE 的 `run_started`、`reasoning_status`、`tool_started`、`tool_finished`、`token`、`question_suggestions`、`citation`、`interrupt`、`completed`、`error` 事件和同一线程恢复。

每个 `agent_id` 独立加载启用状态、模型、流式、问题建议、引用、知识库、上下文和深度思考参数，并在运行开始时固化快照。禁止页面加载以共享默认值重置配置；不提供 Agent 配置版本或发布/回滚能力。

工具白名单：`get_metric_batch`、`get_health_score`、`get_equipment`、`get_similar_repair_cases`、`retrieve_knowledge`、`get_page_capability`、`create_fault_draft`、`submit_confirmed_business_action`、`get_fault_progress`。禁止直接数据库、任意 SQL、健康分写入、维修记录写入、权限/用户修改和文件系统执行工具。

AI 故障上报缺少发生时间或持续时长时必须 interrupt；正式提交必须由用户确认。智能问数仅允许 40 项内置指标和允许维度，并且一次正式查询最多五项已校验指标；健康分必须通过统一健康分服务读取。操作指引最多两次定向知识检索。诊断 Agent 最多 8 个图步骤、24 次工具调用和 4 个并发只读检索；证据不足只能追问、接收附件或允许直接开始维修，不能产生可采纳根因。

深度思考开启时，模型绑定必须声明支持推理，运行时须传递推理参数并真实执行“理解问题 → 决定下一步 → 工具调用 → 核验证据”的图循环。只展示与实际执行一致的安全过程状态；不得输出、记录或用于审计模型原始思维链。

## 安全与交付

模型配置缺失时 AI 健康检查失败，不得伪造结果。附件先经业务服务校验大小、类型和病毒扫描。审计记录用户、线程、节点、工具、引用、模型、耗时、结果和错误，但不得记录密钥、密码、Cookie、令牌或敏感附件原文。Windows + Docker Desktop/WSL2；Funnel 只暴露前端/API HTTPS；每日 00:10 备份，保留 10 天。
