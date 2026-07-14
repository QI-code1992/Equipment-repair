# 测试计划

- 状态：候选版 / 尚未执行生产测试
- 范围：Stage 1 验收标准、Stage 2 流程、Stage 3 状态、Stage 4 契约、生产实现和发布风险。

Test layers: unit; API/schema; permission; health-score rule; Agent graph/checkpoint/SSE; RAG citation and document lifecycle; integration; browser E2E; security; performance; backup/restore. Each case must identify environment, fixture, exact Commit SHA, result and evidence. Production tests must verify missing model configuration fails clearly, unauthorized Agent equipment is rejected without detail leakage, non-catalog metrics are rejected, AI fault interrupts resume by the same thread, and secrets never appear in audit records.
