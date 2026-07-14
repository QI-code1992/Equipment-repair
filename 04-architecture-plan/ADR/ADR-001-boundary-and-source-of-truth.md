# ADR-001: Business Source of Truth and AI Boundaries

- Status: Proposed
- Decision: Business API/database owns business facts and health-score results; LangGraph orchestrates; RAGFlow retrieves citations; LLM summarizes tool output.
- Context: Mixing static demo values, model guesses and knowledge-store facts creates unsafe and unauditable maintenance decisions.
- Consequences: More explicit APIs and audit records; safer fallback and test boundaries; Agent cannot directly write or calculate business state.
- Revisit when: production data contracts, compliance requirements or deployment topology materially change.
