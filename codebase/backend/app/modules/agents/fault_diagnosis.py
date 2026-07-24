from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Callable, Iterable

from app.integrations.ragflow.adapter import RagflowError


MAX_AGENT_STEPS = 8
MAX_QUESTIONS = 24
MAX_EVIDENCE = 4


class DiagnosisState(StrEnum):
    OPEN_LOADING = "OPEN_LOADING"
    QUESTIONING = "QUESTIONING"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    DIAGNOSIS_READY = "DIAGNOSIS_READY"
    ADOPTED = "ADOPTED"
    DIRECT_START = "DIRECT_START"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class DiagnosisContext:
    fault_report_id: str
    equipment_model: str
    symptom: str
    description: str
    alarm_code_present: bool = False


@dataclass(frozen=True, slots=True)
class Evidence:
    category: str
    detail: str


@dataclass(frozen=True, slots=True)
class DiagnosisSession:
    context: DiagnosisContext
    state: DiagnosisState
    question: str | None = None
    evidence: tuple[Evidence, ...] = ()
    prefill: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
    steps: int = 0
    questions: int = 0


@dataclass(frozen=True, slots=True)
class AdoptedDiagnosis:
    state: DiagnosisState
    prefill: dict[str, Any]
    summary: dict[str, Any]


class DiagnosisNotReadyError(ValueError):
    pass


class FaultDiagnosisAgent:
    """执行证据门禁；历史案例与知识引用由外部受控服务提供。"""

    def __init__(
        self,
        case_retrieve: Callable[[DiagnosisContext], Iterable[dict[str, Any]]],
        knowledge_retrieve: Callable[[DiagnosisContext], Iterable[dict[str, Any]]],
        analyze: Callable[[DiagnosisContext, tuple[Evidence, ...]], dict[str, Any]] | None = None,
    ) -> None:
        self._case_retrieve = case_retrieve
        self._knowledge_retrieve = knowledge_retrieve
        self._analyze = analyze or self._default_analysis

    def start(self, context: DiagnosisContext) -> DiagnosisSession:
        try:
            tuple(self._case_retrieve(context))
            tuple(self._knowledge_retrieve(context))
        except (ConnectionError, RagflowError, TimeoutError):
            return DiagnosisSession(context, DiagnosisState.UNAVAILABLE)
        if context.alarm_code_present:
            return DiagnosisSession(
                context,
                DiagnosisState.EVIDENCE_PENDING,
                question="请输入具体报警码，或选择“暂无报码/未读取”。",
            )
        return DiagnosisSession(
            context,
            DiagnosisState.QUESTIONING,
            question="请描述故障复现工况。",
        )

    def answer(self, session: DiagnosisSession, answer: str) -> DiagnosisSession:
        if session.state is not DiagnosisState.EVIDENCE_PENDING:
            return session
        normalized = answer.strip()
        negative = normalized in {"暂无报码", "未读取", "没有报警码"}
        if not negative and not any(char.isdigit() for char in normalized):
            return replace(session, questions=min(session.questions + 1, MAX_QUESTIONS))
        evidence = Evidence(
            "alarm_code_negative" if negative else "alarm_code", normalized
        )
        return replace(
            session,
            state=DiagnosisState.QUESTIONING,
            question="请描述故障复现工况。",
            evidence=(*session.evidence, evidence),
            steps=min(session.steps + 1, MAX_AGENT_STEPS),
            questions=min(session.questions + 1, MAX_QUESTIONS),
        )

    def add_evidence(
        self, session: DiagnosisSession, category: str, detail: str
    ) -> DiagnosisSession:
        if session.state not in {DiagnosisState.QUESTIONING, DiagnosisState.EVIDENCE_PENDING}:
            return session
        if not category.strip() or not detail.strip() or len(session.evidence) >= MAX_EVIDENCE:
            return session
        evidence = (*session.evidence, Evidence(category.strip(), detail.strip()))
        categories = {item.category for item in evidence}
        if "reproduction" not in categories or len(categories - {"reproduction"}) < 1:
            return replace(
                session,
                evidence=evidence,
                question="请提供一项不同类型的技术证据。",
                steps=min(session.steps + 1, MAX_AGENT_STEPS),
                questions=min(session.questions + 1, MAX_QUESTIONS),
            )
        result = self._analyze(session.context, evidence)
        return replace(
            session,
            state=DiagnosisState.DIAGNOSIS_READY,
            evidence=evidence,
            prefill={"actual_cause": result["root_cause"], "actual_solution": result["recommendations"]},
            summary={
                "symptom": session.context.symptom,
                "key_evidence": [item.detail for item in evidence],
                "root_cause": result["root_cause"],
                "recommendations": result["recommendations"],
                "safety_notes": result.get("safety_notes", []),
            },
            steps=min(session.steps + 1, MAX_AGENT_STEPS),
        )

    def adopt(self, session: DiagnosisSession) -> AdoptedDiagnosis:
        if session.state is not DiagnosisState.DIAGNOSIS_READY or not session.prefill or not session.summary:
            raise DiagnosisNotReadyError("diagnosis evidence threshold is not met")
        return AdoptedDiagnosis(DiagnosisState.ADOPTED, session.prefill, session.summary)

    def direct_start(self, session: DiagnosisSession) -> DiagnosisSession:
        return replace(session, state=DiagnosisState.DIRECT_START, prefill=None, summary=None)

    @staticmethod
    def _default_analysis(_: DiagnosisContext, evidence: tuple[Evidence, ...]) -> dict[str, Any]:
        return {
            "root_cause": "候选根因需人工确认",
            "recommendations": "按已收集证据执行人工检查清单",
            "safety_notes": ["高风险系统先停机并执行安全检查"],
        }
