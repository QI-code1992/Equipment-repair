# Notifications Backend Design

## Goal

为共享 App Shell 提供持久化通知列表、未读数、单条已读和全部已读接口。

## Design

- PostgreSQL 表 `notifications` 保存全局广播通知内容和可选 `related_object_id`。
- 表 `notification_reads` 以 `notification_id + user_id` 唯一记录当前用户的已读时间。
- 所有接口复用 `get_current_user`，不新增通知专用权限。
- `GET /api/notifications` 返回 `items`、`total` 和 `unread_count`，支持 `page`、`page_size`、`unread_only`。
- `GET /api/notifications/unread-count` 返回当前用户未读数。
- `PATCH /api/notifications/{notification_id}/read` 标记当前用户已读，重复调用保持成功。
- `POST /api/notifications/read-all` 标记当前用户当前可见的全部通知为已读，重复调用保持成功。
- 列表按 `created_at DESC, id ASC` 排序；通知不存在时标记接口返回 404。
- 首批生产事件为故障提交、维修结果提交和 Agent 诊断就绪；健康分按 PRD 的 `100 / 80-99 / 60-79 / 40-59 / 0-39` 分段，仅跨段时生成通知。
- 不生成“维修完成待验收”通知，也不生成账号、权限、配置变更或系统公告通知。

## Verification

先写失败的 FastAPI 契约测试，再实现 SQLAlchemy 模型、路由和 Alembic 迁移 `0007_task013_notifications`。
