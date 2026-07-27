# TASK-010 Auth Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the smallest formal login/session entry that makes existing protected frontend calls usable.

**Architecture:** `api.ts` owns the login request and session storage access. `LoginPage` owns credentials and error display. `App` owns route protection, preserving the requested path through router state.

**Tech Stack:** React, React Router, TypeScript, Vitest, Testing Library; no new dependencies.

## Global Constraints

- Reuse `POST /api/auth/login` and response field `access_token`; do not alter backend authentication.
- Store the token only in `sessionStorage.access_token`; never render or log it.
- Protect every existing route except `/login`.
- Retain existing JSON/SSE Bearer boundary and test it through fetch request arguments.
- Keep all work in PR #50; do not request merge authorization or unlock downstream work.

---

### Task 1: Login API and session boundary

**Files:**
- Modify: `codebase/frontend/src/api.ts`
- Test: `codebase/frontend/src/api.test.ts`

**Interfaces:**
- Produces `login(username: string, password: string): Promise<void>` that writes only the returned token after a successful response.
- Produces `hasActiveSession(): boolean` for route protection.

- [ ] **Step 1: Write failing API tests**

```ts
await login("repairer", "correct-password");
expect(window.sessionStorage.getItem("access_token")).toBe("session-token");
```

- [ ] **Step 2: Run the focused test and confirm it fails because `login` is missing.**

Run: `npm --prefix codebase/frontend test -- --run src/api.test.ts`

- [ ] **Step 3: Implement the minimal login request and session helpers.**

```ts
export async function login(username: string, password: string) {
  const response = await requestJson<{ access_token: string }>("/api/auth/login", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }),
  });
  window.sessionStorage.setItem("access_token", response.access_token);
}
```

- [ ] **Step 4: Re-run the focused API test and confirm it passes.**

### Task 2: Protected login route

**Files:**
- Create: `codebase/frontend/src/LoginPage.tsx`
- Modify: `codebase/frontend/src/App.tsx`
- Test: `codebase/frontend/src/App.test.tsx`

**Interfaces:**
- Consumes `login` and `hasActiveSession` from `api.ts`.
- Produces protected rendering for existing routes and a `/login` entry.

- [ ] **Step 1: Write failing interaction tests**

```tsx
render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);
expect(screen.getByRole("heading", { name: "登录" })).toBeInTheDocument();
```

- [ ] **Step 2: Run the focused App test and confirm it fails because the route is not protected.**

Run: `npm --prefix codebase/frontend test -- --run src/App.test.tsx`

- [ ] **Step 3: Add the minimal login form and route guard.**

```tsx
if (!hasActiveSession()) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
```

- [ ] **Step 4: Re-run the App test and confirm protected redirect, successful token write, and return navigation pass.**

### Task 3: Final evidence

**Files:**
- Modify: `05-development/CHECKPOINTS.md`, `05-development/SELF_TEST.md`, `05-development/CODE_REVIEW.md`, `05-development/COMMIT_LOG.md`, `workflow/DEV_TO_PM_HANDOFF.md`, `workflow/state.json`

- [ ] **Step 1: Run full frontend tests, build, static regressions, JSON parse and diff checks.**

Run: `npm --prefix codebase/frontend test && npm --prefix codebase/frontend run build && for file in 06-testing/tests/*.test.js; do node "$file"; done && python3 -m json.tool workflow/state.json >/dev/null && git diff --check`

- [ ] **Step 2: Record actual results, exact review candidate rules, scope, and unverified live browser/backend integration.**

- [ ] **Step 3: Commit and push the same PR #50 branch; request only DEV-001 code review for the final exact HEAD.**
