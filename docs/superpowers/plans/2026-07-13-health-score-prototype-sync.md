# ⚠️ 历史计划：禁止作为开发依据

> 本文保留用于追溯早期原型同步过程。其评分区间、历史回算等内容已被后续确认规则替换；开发、测试和验收必须以 `docs/开发基线说明.md` 指向的当前有效文档为准。

# Health Score Prototype Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align all prototype health-score displays with the confirmed score bands and risk-level derivation.

**Architecture:** Health-score bands remain the source of truth. Workbench, dashboard, ledger filters, and equipment detail consume the same static prototype bands; no new scoring calculation is introduced.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, Node assert tests.

## Global Constraints

- Score calculation period remains 30 days; history display remains 60 days.
- Health-score display bands are 80–100 normal, 60–79 attention, 0–59 low health.
- Risk level is derived from score: 80–100 low, 60–79 medium, 40–59 high, 0–39 severe.
- Front-end prototype only consumes score results; it must not introduce another scoring algorithm.

---

### Task 1: Lock the health-score display contract

**Files:**
- Create: `tests/health-score-consistency.test.js`
- Modify: `pages/workbench.html`, `pages/equipment-ledger.html`, `pages/bi-dashboard.html`, `pages/equipment-detail.html`

- [ ] Write a Node assert test that expects the ledger filters, four risk bands, and the detail-page 82 score to show low risk.
- [ ] Run `node tests/health-score-consistency.test.js` and confirm it fails before the page changes.
- [ ] Update only the affected static markup and existing filter predicate.
- [ ] Run `node tests/health-score-consistency.test.js` and `node tests/health-score-drawer.test.js` and confirm both pass.
- [ ] Inspect the edited detail page in the local browser.
