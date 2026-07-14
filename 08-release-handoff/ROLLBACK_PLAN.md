# 回滚方案

任何发布前都要用 Commit/tag 保护当前状态。发生缺陷时，在回滚分支撤销指定发布 Commit 或恢复选定路径，不得重置共享历史。必须验证目标版本保留所有已接受功能，并使用新的精确 SHA 重新执行受影响测试和 Stage 6/7。

Current recovery target: `snapshot/legacy-import-20260714` (asset-import snapshot only; not a release target).
