# 消息通知面板设计规范

- Status: Candidate / approved for prototype implementation
- Date: 2026-07-14
- Scope: 顶部消息通知铃铛、下拉面板、未读状态和业务跳转

## 1. Product boundary

所有用户均可收到业务消息，不按角色或设备授权范围过滤。通知类型不设固定白名单，故障、工单、健康风险、维修、Agent、知识库和其他业务事件均可进入通知集合。本期明确不做账号、权限、配置变更和系统公告类系统通知。

不新增通知中心页面；所有查看、筛选、已读和详情操作均在铃铛下拉面板内完成。

## 2. Bell entry

- Use a 20–22px inline SVG linear bell icon; never render a text glyph or emoji.
- Icon button keeps the existing topbar square size and radius.
- Unread count is an independent badge at the top-right; 0 hides the badge and counts above 99 display `99+`.
- Default icon is neutral blue-gray; hover/open state uses brand blue.
- `aria-label="消息通知"`; the badge is hidden from assistive technology when redundant.

## 3. Dropdown panel

- Width: approximately 360px; aligned below the bell and within the viewport.
- Surface: white, 12px radius, light border and low-elevation shadow.
- Header: “消息通知” and “全部已读”.
- Local tabs: “全部” and “未读”.
- Default list: latest 10 notifications.
- Each item includes type label, title, short summary, related object ID, time and unread state.
- Click outside or Escape closes the panel.
- Opening the panel shows a page scrim and locks the main page scroll; only the notification list can scroll vertically. The scrim, Escape or the bell closes the panel and restores page scrolling.

## 4. Notification behavior

- Clicking an item marks it read immediately.
- If a business target exists, the item opens the target page/detail; otherwise it stays in the panel and only changes read state.
- “全部已读” clears unread state but never deletes records.
- Additional records use in-panel “加载更多” (the list is independently scrollable); no independent-page navigation.
- No delete, bulk delete, notification preferences, mute, sound, vibration or browser push in this increment.

## 5. Visual states

- Notification type colors remain on the type label: critical red, risk/pending orange, normal blue, success green.
- Read: no left status dot, gray text and lower-contrast surface.
- Unread: red 6px status dot and stronger title weight. The dot represents unread state only, never notification type or risk.

## 6. Empty/error/detail states

- Empty: “暂无消息通知”.
- Empty unread filter: “暂无未读消息”.
- Load failure: “通知加载失败，请重试” with retry action.
- Long title/summary: two-line clamp; expanded detail remains inside the panel.
- Detail view shows full title, type/risk, content, related object, timestamp and optional “查看业务详情”. Opening detail marks the item read.

## 7. Prototype acceptance boundary

Prototype uses deterministic local notification data and simulated read state. It must not claim server push, persistence across accounts, or production authorization. The bell icon must remain an actual SVG icon in every page shell.
