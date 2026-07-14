# AI/RAGFlow/LangGraph 集成基线摘要

- 状态：候选版 / 已纳入外部开发基线
- 来源：`workflow/EXTERNAL_BASELINE_INPUTS.md`

## 技术与边界

Python 3.13 + FastAPI；PostgreSQL 为业务库；MinIO/S3 存附件；Redis 做短期缓存和限流。RAGFlow 使用独立 Docker Compose 依赖栈，不与业务 PostgreSQL、Redis、MinIO 共享实例或账号。LangGraph 编排受控工作流并使用 PostgreSQL checkpoint；LLM 通过 OpenAI 兼容网关调用聊天、Embedding、Rerank 模型。

业务后端是唯一业务事实源和写入口。RAGFlow 只负责解析、切片、检索、重排和引用；LangGraph 只做意图识别、路由、白名单工具调用、多轮补齐、人工确认和总结；LLM 不得猜测指标、权限、故障结论、维修事实或引用。

## 知识契约

业务文档保存业务文档 ID、对象存储 file ID、RAGFlow document ID、解析状态和失败原因。状态为 `UPLOADING`、`PARSING`、`READY`、`FAILED`；只有 `READY` 文档可检索。每条引用必须包含文档和切片标识。空检索必须明确返回无可引用依据。

## Agent 契约

共享状态：`thread_id`、`user_id`、`role`、`page_context`、`messages`、`tool_results`、`citations`、`pending_confirmation`、`audit_id`。线程绑定创建用户，不得跨用户复用；支持 SSE 的 token/tool/interrupt/completed/error 事件和同一线程恢复。

工具白名单：`get_metric`、`get_health_score`、`get_granted_equipment`、`retrieve_knowledge`、`create_fault_draft`、`submit_fault_report`、`get_fault_progress`。禁止直接数据库、任意 SQL、健康分写入、维修记录写入、权限/用户修改和文件系统执行工具。

AI 故障上报缺少发生时间或持续时长时必须 interrupt；正式提交必须由用户确认。智能问数仅允许 40 项内置指标和允许维度，健康分必须通过统一健康分服务读取。运维指导和诊断建议可带引用，但不得直接写入维修记录。

## 安全与交付

模型配置缺失时 AI 健康检查失败，不得伪造结果。附件先经业务服务校验大小、类型和病毒扫描。审计记录用户、线程、节点、工具、引用、模型、耗时、结果和错误，但不得记录密钥、密码、Cookie、令牌或敏感附件原文。Windows + Docker Desktop/WSL2；Funnel 只暴露前端/API HTTPS；每日 00:10 备份，保留 10 天。
