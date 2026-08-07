# Browser Password Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the “记住密码” login copy while making the browser, rather than the application, the only password manager.

**Architecture:** `LoginPage` supplies browser-recognizable form-field semantics and an explanatory preference only. The existing `login()` function continues to transmit credentials once and retain only the access token; no password persistence path is introduced.

**Tech Stack:** React 19, TypeScript, React Testing Library, Vitest.

## Global Constraints

- Do not persist a password in localStorage, sessionStorage, Cookie, IndexedDB, or a backend API.
- Do not add production dependencies, API fields, database migrations, permission changes, or deployment changes.
- Preserve `autocomplete="username"` and `autocomplete="current-password"`.
- Work only on `codex/task-013-prototype-fidelity-remediation`.

---

### Task 1: Make Password-Manager Semantics Explicit

**Files:**
- Modify: `codebase/frontend/src/LoginPage.test.tsx`
- Modify: `codebase/frontend/src/LoginPage.tsx`

**Interfaces:**
- Consumes: existing `login(username: string, password: string): Promise<void>`.
- Produces: a standard login form whose fields identify themselves as `username` and `current-password` without application-side password persistence.

- [ ] **Step 1: Write the failing test**

```tsx
it("uses browser password-manager semantics without application password storage", () => {
  renderLogin();

  expect(screen.getByLabelText("用户名")).toHaveAttribute("name", "username");
  expect(screen.getByLabelText("密码")).toHaveAttribute("name", "password");
  expect(screen.getByText(/浏览器密码管理器/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --run src/LoginPage.test.tsx`

Expected: FAIL because the inputs have no stable `name` attributes and the browser-manager explanation is absent.

- [ ] **Step 3: Write the minimal implementation**

```tsx
<input aria-label="用户名" name="username" autoComplete="username" ... />
<input aria-label="密码" name="password" type={passwordVisible ? "text" : "password"} autoComplete="current-password" ... />
<small>密码由浏览器密码管理器保存，平台不会保存密码。</small>
```

Keep the checkbox out of the login request and do not introduce browser storage calls for the password.

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm test -- --run src/LoginPage.test.tsx`

Expected: PASS with no failing LoginPage tests.

- [ ] **Step 5: Run focused frontend verification**

Run:

```powershell
npm test -- --run
npm run build
```

Expected: all frontend tests pass and the production build succeeds.

- [ ] **Step 6: Commit**

```powershell
git add codebase/frontend/src/LoginPage.tsx codebase/frontend/src/LoginPage.test.tsx docs/superpowers/specs/2026-08-07-browser-password-manager-design.md docs/superpowers/plans/2026-08-07-browser-password-manager.md
git commit -m "fix(login): clarify browser password management"
```
