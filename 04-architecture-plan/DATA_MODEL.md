# 数据模型（候选版）

Core aggregates: `User`, `Role`, `Permission`, `Equipment`, `EquipmentGrant`, `FaultReport`, `Diagnosis`, `WorkOrder`, `MaintenanceRecord`, `KnowledgeDataset`, `KnowledgeDocument`, `KnowledgeCitation`, `MetricDefinition`, `HealthScoreSnapshot`, `AgentThread`, `AgentRun`, `AuditEvent`.

关系：设备可以有多条故障、工单和维修记录；一条故障可以产生一条诊断和多个工单修订；文档业务元数据映射到 RAGFlow ID；健康快照关联触发故障/工单；Agent 运行记录关联操作者、工具调用、引用和确认事件；审计事件关联操作者和目标对象。

不变量：

- equipment code unique;
- one active equipment per fault report;
- no deactivation with pending/in-repair fault;
- only READY knowledge documents are retrievable;
- health snapshots are append-only evidence;
- metric definitions are code/config managed and read-only to users;
- business writes are attributable to an authenticated actor.
- knowledge documents retain business ID, object-storage file ID and RAGFlow document ID; failed documents retain failure reason and are excluded from retrieval.
- Agent threads bind `thread_id` to one user; audit records retain tool, model, citation, duration, result and error metadata without secrets.
