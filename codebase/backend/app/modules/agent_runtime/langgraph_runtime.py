from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph


class RuntimeState(TypedDict, total=False):
    run_id: str
    step: str
    status: str
    events: list[dict[str, Any]]
    resumed: bool
    resume: bool
    confirmation: dict[str, Any]


_memory_saver = InMemorySaver()


def _runtime_node(state: RuntimeState) -> RuntimeState:
    events = list(state.get("events", []))
    if state.get("resumed"):
        events.append({"event": "checkpoint_resumed", "data": {"run_id": state["run_id"]}})
    else:
        events.append({"event": "checkpoint_saved", "data": {"run_id": state["run_id"]}})
    return {**state, "step": "waiting_for_model", "status": "WAITING_FOR_MODEL", "events": events}


def _graph(checkpointer: Any):
    builder = StateGraph(RuntimeState)
    builder.add_node("runtime", _runtime_node)
    builder.add_edge(START, "runtime")
    builder.add_edge("runtime", END)
    return builder.compile(checkpointer=checkpointer)


@contextmanager
def _checkpointer(database_url: str | None) -> Iterator[Any]:
    if database_url and database_url.startswith("postgresql"):
        with PostgresSaver.from_conn_string(database_url) as saver:
            saver.setup()
            yield saver
        return
    yield _memory_saver


def run_checkpoint(
    *,
    run_id: str,
    initial_state: RuntimeState,
    database_url: str | None,
    resumed: bool = False,
) -> RuntimeState:
    config = {"configurable": {"thread_id": run_id}}
    with _checkpointer(database_url) as checkpointer:
        graph = _graph(checkpointer)
        previous = graph.get_state(config)
        if resumed and previous.values:
            state = {
                **previous.values,
                "resume": initial_state.get("resume", True),
                "confirmation": initial_state.get("confirmation", {}),
                "run_id": run_id,
                "resumed": True,
            }
        else:
            state = {**initial_state, "run_id": run_id, "resumed": resumed}
        return graph.invoke(state, config)
