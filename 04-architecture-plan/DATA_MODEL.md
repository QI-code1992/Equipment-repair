# Data Model Candidate

Core aggregates: `User`, `Role`, `Permission`, `Equipment`, `EquipmentGrant`, `FaultReport`, `Diagnosis`, `WorkOrder`, `MaintenanceRecord`, `KnowledgeDataset`, `KnowledgeDocument`, `KnowledgeCitation`, `MetricDefinition`, `HealthScoreSnapshot`, `AgentThread`, `AgentRun`, `AuditEvent`.

Relationships: equipment has many faults, work orders and maintenance records; a fault may produce one diagnosis and one or more work-order revisions; documents map business metadata to RAGFlow IDs; health snapshots reference triggering faults/orders; Agent runs reference actor, tool calls, citations and confirmation events; audit events reference actor and target.

Invariants:

- equipment code unique;
- one active equipment per fault report;
- no deactivation with pending/in-repair fault;
- only READY knowledge documents are retrievable;
- health snapshots are append-only evidence;
- metric definitions are code/config managed and read-only to users;
- business writes are attributable to an authenticated actor.
- knowledge documents retain business ID, object-storage file ID and RAGFlow document ID; failed documents retain failure reason and are excluded from retrieval.
- Agent threads bind `thread_id` to one user; audit records retain tool, model, citation, duration, result and error metadata without secrets.
