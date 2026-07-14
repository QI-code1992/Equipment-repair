# 用户入口与用户管理设计规范

- Status: Candidate / awaiting implementation approval
- Date: 2026-07-14
- Scope: 工作台右上角用户入口、个人资料、安全设置、用户管理权限衔接
- Prototype baseline: `03-ui-prototype/prototype/pages/workbench.html`, `03-ui-prototype/prototype/pages/system-management.html`

## 1. Design decision

采用“双层结构”：右上角用户胶囊提供当前会话快捷操作；完整用户管理继续位于“系统管理”。右上角不承载用户列表和复杂授权操作。

## 2. User capsule

- Structure: avatar, name, role/title, 16px dropdown arrow.
- Size: height 44px, pill radius 22px, avatar 32px.
- Default: white surface, light blue-gray border.
- Hover/open: brand-blue border; open state rotates arrow 180 degrees.
- Long names: capsule displays at most 6 Chinese characters; full name remains in identity summary.
- Missing avatar: use first character of display name.

## 3. Dropdown menu

Width 256px; right-aligned to the capsule; white surface, 8–12px radius, light shadow, 12px padding.

1. Identity summary: avatar, name, username, current role and organization; read-only.
2. Personal profile: opens a read-only modal without leaving the current page.
3. Security / change password: opens a modal without leaving the current page.
4. Enter user management: visible only when the user has the user-management permission.
5. Logout: separated by a divider, danger color, confirmation required.

Clicking outside, pressing Escape, or clicking the capsule again closes the menu. Menu depth is limited to one level.

## 4. Personal profile modal

Read-only modal, approximately 480px wide. Shows name, username, organization, current role, account status and last login. Close by ×, Cancel/Close, backdrop or Escape. Avatar upload is out of scope for this prototype increment.

## 5. Security modal

Read-only current session context plus change-password form: current password, new password and confirmation. Password visibility toggles are provided. Save is disabled until validation passes. Mismatch and current-password errors are shown inline. Success displays “密码已更新” and closes the modal. Prototype does not simulate forced session invalidation.

## 6. Permission model

| Permission | Scope | UI |
|---|---|---|
| `user_management.view_all` | View/manage users in the granted scope | Show full user-management entry and permitted list/actions |
| No user-management permission | Current user only | Hide management entry; retain profile and security |
| System administrator | All users | Full CRUD, enable/disable, reset password, role and organization authorization |
| Ordinary user with self scope | Current user only | “我的账号” view; no organization tree, search, role filter or other-user data |

The server remains the source of truth. Direct URL access without permission returns an authorization state and must not render user data.

## 7. Navigation and user-management views

The management entry navigates to `/system-management?tab=users` and activates the User Management tab. Users with `user_management.view_all` see organization tree, search, role/status filters, pagination and permitted actions. Ordinary users see only a “我的账号” detail card and a change-password action.

Usernames cannot be edited. System administrator accounts cannot be deleted or disabled. Disable and reset-password actions require confirmation. Role and organization assignment is edited inside the user form, not inline in the table.

## 8. Visual tokens

- Modal radius: 12px.
- Dropdown shadow: low-elevation, no heavy blur.
- Title: 18px, semibold.
- Body/menu text: 14px.
- Secondary text: existing neutral gray token.
- Primary action: existing brand blue.
- Destructive action: existing danger red.
- Footer action order: Cancel / primary action.

## 9. Prototype acceptance boundary

This document defines the approved design direction. It does not approve Stage 2 or Stage 3, and it does not claim browser/runtime validation. Implementation must add states for default, hover, open, outside-click close, Escape close, permission denied, self-only view, validation error, save success and logout confirmation.
