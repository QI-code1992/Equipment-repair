# CR-049 Stage 5 回流记录

- 日期：2026-08-03
- 状态：In Development；PR #80
- 范围：TASK-005 验证基础设施的 PowerShell 输出处理与可执行契约回归。
- 根因：Windows PowerShell 将 Docker Compose 清理阶段的正常 stderr 误判为 `NativeCommandError`，导致 live-stack 验证无法稳定返回退出码。
- 修复边界：成功清理抑制进度噪声；非零退出仍失败；失败时保留并回显 stderr 诊断内容。
- 不变项：无生产业务代码、API 契约、数据库、依赖或部署行为变更。
- 验证：Python 契约 `3 passed`；PowerShell 可执行契约通过；`git diff --check` 通过。
- 后续门禁：PR #80 审核并集成后，必须对集成后的精确 SHA 独立重跑 TASK-005 live lifecycle。Stage 6 仍未批准。
