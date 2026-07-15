# 系统架构

- 基线：候选版 v2.1
- 状态：架构设计已书面评审通过；等待 API、数据模型和实施计划评审后申请 Stage 4 门禁
- 主架构依据：[平台级架构设计.md](平台级架构设计.md)

## 系统上下文

```text
公网平台账号用户
  -> Nginx（唯一 HTTPS 入口）
  -> 静态 Web 前端 / FastAPI 模块化单体
       -> PostgreSQL（业务事实、配置、线程、审计）
       -> Redis（缓存、限流、队列协调）
       -> MinIO（附件）
       -> Worker（异步预诊断、文档同步、通知、备份）
       -> LangGraph Agent Runtime
            -> PostgreSQL 历史维修案例与业务工具
            -> RAGFlow 适配器 -> RAGFlow 独立依赖栈 + Elasticsearch 8.11
            -> 外部 OpenAI 兼容 LLM 网关
```

仅 Nginx 暴露公网 HTTPS。PostgreSQL、Redis、MinIO、RAGFlow、Elasticsearch 和 Worker 均在 Docker 内部网络；Windows 主机使用 Docker Desktop/WSL2。

## 领域边界

- **业务 API**：唯一业务事实写入者，负责认证、角色/菜单/操作权限、字段校验、幂等与审计。
- **Agent Runtime**：只编排受控模型与白名单工具；模型不直连数据库，也不能直接写入业务事实。
- **RAGFlow**：只处理非结构化文档、检索、重排与引用；同类设备历史维修记录只来自 PostgreSQL。
- **后台 Worker**：执行预诊断草稿、文档处理状态同步、案例沉淀、通知与备份；不持有前台会话。

本期没有工厂/设备行级授权隔离或 `EquipmentGrant`。仍执行平台账号认证、角色、菜单与操作权限；Agent 线程只允许创建者或系统管理员读取。

## 四个 Agent

全局入口是 AI 故障上报、智能问数、操作指引三个 Tab 的页面外壳，不是 Agent。故障诊断位于“故障上报 > 开始维修”。

| Agent | 编排模式 | 允许的主要能力 |
|---|---|---|
| AI 故障上报 | 字段采集状态机 | 设备读取、故障草稿、人工确认提交 |
| 智能问数 | 查询计划状态机 | 固定指标目录与批量指标查询、解释 |
| 操作指引 | 页面能力优先状态机 | 当前页面能力匹配、最多两次定向知识检索 |
| 故障诊断 | 受约束的思考—行动—核验图 | 历史案例、RAGFlow、附件证据、预诊断与人工采纳 |

`AgentConfig` 按 `agent_id` 独立存储当前有效模型、流式、问题建议、引用、上下文、检索参数和深度思考设置。运行启动时复制为只读快照；保存不生成 Agent 版本、发布或回滚流程。页面加载不得写入一份共享默认配置覆盖四个 Agent。

## 深度思考与流式事件

启用深度思考时，运行时必须验证所绑定模型支持推理并传递对应推理参数。图实际执行“理解问题 → 决定下一步 → 调用工具 → 核验证据 → 回复或追问”；不输出或持久化原始思维链。SSE 只发送真实且安全的过程事件：`run_started`、`reasoning_status`、`tool_started`、`tool_finished`、`token`、`question_suggestions`、`citation`、`interrupt`、`completed`、`error`。

## 降级与恢复

Agent 未启用、配置不完整、RAGFlow/外部 LLM 失败或超时，业务页面保留人工上报、直接开始维修和人工结束维修。不得构造伪诊断或伪引用。线程 checkpoint、运行快照和未完成确认存入 PostgreSQL，以支持刷新或容器重启后的恢复。

RAGFlow 由开发工作在本机 Windows 的 Docker Desktop/WSL2 中下载、部署、初始化、调试和对接。验收前必须实际验证健康检查、文档上传、解析、切片、索引、混合检索、引用回传、超时降级和容器重启后的可用性；不允许以本地 mock 或静态案例替代该集成。
