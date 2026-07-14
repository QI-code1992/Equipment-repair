# 消息通知面板设计规范

- 状态：候选版 / 已批准进入原型实现
- 日期：2026-07-14
- 范围：顶部消息通知铃铛、下拉面板、未读状态和业务跳转

## 1. 产品边界

所有用户均可收到业务消息，不按角色或设备授权范围过滤。通知类型不设固定白名单，故障、工单、健康风险、维修、Agent、知识库和其他业务事件均可进入通知集合。本期明确不做账号、权限、配置变更和系统公告类系统通知。

不新增通知中心页面；所有查看、筛选、已读和详情操作均在铃铛下拉面板内完成。

## 2. 铃铛入口

- 使用 20–22px 内联 SVG 线性铃铛图标，不渲染文字字符或 emoji。
- 图标按钮沿用现有顶部栏方形尺寸和圆角。
- 未读数量作为独立徽标显示在右上角；数量为 0 时隐藏，超过 99 显示 `99+`。
- 默认图标使用中性蓝灰色，悬停/打开状态使用品牌蓝。
- `aria-label="消息通知"`; the badge is hidden from assistive technology when redundant.

## 3. 下拉面板

- 宽度约 360px，位于铃铛下方且不超出视口。
- 白色背景、12px 圆角、浅边框和低层级阴影。
- 头部显示“消息通知”和“全部已读”。
- 面板内 Tab 为“全部”和“未读”。
- 默认列表显示最近 10 条通知。
- 每条通知包含类型标签、标题、摘要、关联对象 ID、时间和已读状态。
- 点击外部区域或按 Esc 关闭面板。
- Opening the panel shows a page scrim and locks the main page scroll; only the notification list can scroll vertically. The scrim, Escape or the bell closes the panel and restores page scrolling.

## 4. 通知行为

- Clicking an item marks it read immediately.
- If a business target exists, the item opens the target page/detail; otherwise it stays in the panel and only changes read state.
- “全部已读” clears unread state but never deletes records.
- Additional records use in-panel “加载更多” (the list is independently scrollable); no independent-page navigation.
- No delete, bulk delete, notification preferences, mute, sound, vibration or browser push in this increment.

## 5. 视觉状态

- Notification type colors remain on the type label: critical red, risk/pending orange, normal blue, success green.
- Read: no left status dot, gray text and lower-contrast surface.
- Unread: red 6px status dot and stronger title weight. The dot represents unread state only, never notification type or risk.

## 6. 空状态、错误和详情状态

- Empty: “暂无消息通知”.
- Empty unread filter: “暂无未读消息”.
- Load failure: “通知加载失败，请重试” with retry action.
- Long title/summary: two-line clamp; expanded detail remains inside the panel.
- Detail view shows full title, type/risk, content, related object, timestamp and optional “查看业务详情”. Opening detail marks the item read.

## 7. 原型验收边界

Prototype uses deterministic local notification data and simulated read state. It must not claim server push, persistence across accounts, or production authorization. The bell icon must remain an actual SVG icon in every page shell.
