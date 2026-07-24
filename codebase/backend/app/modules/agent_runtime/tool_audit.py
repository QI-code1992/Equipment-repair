from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.modules.audit.service import sanitize_audit_metadata, write_audit_event

from .models import AgentRun, ToolCall


ALLOWED_TOOLS = frozenset({
    "retrieve_knowledge",
    "get_similar_repair_cases",
    "query_metric_batch",
    "get_health_score",
    "get_page_capability",
    "create_fault_draft",
    "submit_confirmed_business_action",
})


def record_tool_call(
    db: Session,
    *,
    run: AgentRun,
    actor_user_id: str,
    tool_name: str,
    input_data: Mapping[str, object],
    result_summary: Mapping[str, object],
    status: str = "completed",
) -> ToolCall:
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError("tool is not allowlisted")
    call = ToolCall(
        run_id=run.id,
        tool_name=tool_name,
        status=status,
        input_json=sanitize_audit_metadata(dict(input_data)),
        result_summary_json=sanitize_audit_metadata(dict(result_summary)),
    )
    db.add(call)
    write_audit_event(
        db,
        actor_user_id=actor_user_id,
        action="agent.tool_call",
        resource_type="agent_run",
        resource_id=run.id,
        result=status,
        metadata={"tool_name": tool_name, "input": input_data, "result": result_summary},
    )
    return call
