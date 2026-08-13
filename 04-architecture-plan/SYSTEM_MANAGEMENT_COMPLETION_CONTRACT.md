# 系统管理后端补齐契约

批准日期：2026-08-13。该契约覆盖 TASK-002 中“仅四个固定角色、不可创建角色”的限制。

## 角色

内置角色保持 `built_in=true`。系统管理员不可改权限、不可删除；自定义角色可通过 `POST /api/roles` 创建、`PATCH /api/roles/{role_id}` 更新、`DELETE /api/roles/{role_id}` 删除。角色列表返回 `id,code,name,description,built_in,enabled,user_count,updated_at,permission_codes`。已绑定用户的自定义角色不得停用或删除，返回 `409 ROLE_HAS_USERS`。

## 用户和会话

用户读写字段为 `username,enabled,role_ids,display_name,gender,email,phone,remark,organization_id`；用户名不可修改。`POST /api/users/{user_id}/password-reset` 接受 `new_password`，不返回明文或哈希，撤销目标用户全部未撤销会话。用户删除不提供接口，停用为唯一生命周期终止操作；禁止停用自己或最后一个有效系统管理员。

## 写入与审计

所有本契约新增写接口均要求 `identity:write` 和 `Idempotency-Key`。同一用户的 key 全局唯一，方法、路径或规范化请求体不同返回 `409 IDEMPOTENCY_KEY_REUSED`。成功和失败均写入脱敏审计；密码、哈希、Token、Cookie 和附件正文不进入审计。

## 日志读取

`GET /api/login-events?username=&result=&page=&page_size=` 与 `GET /api/audit-events?action=&resource_type=&result=&page=&page_size=` 均要求 `system:audit`。登录记录返回用户名、显示名、时间、结果和失败原因；审计记录返回操作者显示名、模块、目标、结果和白名单摘要。两者均按时间倒序、ID 升序稳定排序。
