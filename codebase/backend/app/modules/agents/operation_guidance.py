from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Iterable

from app.integrations.ragflow.adapter import RagflowError


class GuidanceState(StrEnum):
    QUESTIONING = "QUESTIONING"
    UNAVAILABLE = "UNAVAILABLE"


MAX_DIRECTIONAL_RETRIEVALS = 2


@dataclass(frozen=True, slots=True)
class GuidanceContext:
    equipment_id: str
    equipment_model: str
    symptom: str
    description: str


@dataclass(frozen=True, slots=True)
class GuidanceReference:
    citation: str
    text: str


@dataclass(frozen=True, slots=True)
class GuidanceSession:
    context: GuidanceContext
    state: GuidanceState
    question: str | None = None
    evidence: tuple[GuidanceReference, ...] = ()
    retrieval_count: int = 0
    manual_fallback: bool = False
    loading_seconds: int = 3


class OperationGuidanceAgent:
    """受控操作指引边界；检索失败时保留人工流程。"""

    def __init__(self, retrieve: Callable[[str], Iterable[dict[str, Any]]]) -> None:
        self._retrieve = retrieve

    def start(self, context: GuidanceContext) -> GuidanceSession:
        queries = (
            f"{context.equipment_model} {context.symptom}",
            f"{context.equipment_model} {context.description}",
        )
        references: list[GuidanceReference] = []
        try:
            for query in queries[:MAX_DIRECTIONAL_RETRIEVALS]:
                references.extend(
                    GuidanceReference(str(item["citation"]), str(item["text"]))
                    for item in self._retrieve(query)
                )
        except (ConnectionError, RagflowError, TimeoutError):
            return GuidanceSession(
                context=context,
                state=GuidanceState.UNAVAILABLE,
                manual_fallback=True,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("guidance retrieval returned an invalid reference") from error
        return GuidanceSession(
            context=context,
            state=GuidanceState.QUESTIONING,
            question="请描述故障出现时的工况或最近一次可复现步骤。",
            evidence=tuple(references),
            retrieval_count=min(len(queries), MAX_DIRECTIONAL_RETRIEVALS),
            manual_fallback=True,
        )

    def answer(self, session: GuidanceSession, answer: str) -> GuidanceSession:
        if session.state is GuidanceState.UNAVAILABLE:
            return session
        return replace(session, question="请提供可验证的测量值、报警码或部件检查结果。")
