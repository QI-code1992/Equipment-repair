# TASK-010 正式前端与批准流程集成实施计划

> **执行约束：** 所有实现位于独立 worktree；每个任务按“失败测试 → 最小实现 → 通过测试 → 提交”执行。TASK-010 由 DEV-002 开发、DEV-001 审核；只能推送到 `codex/task-010-frontend-integration`，不得自批、自合并或请求 Merge 授权。

**目标：** 用正式 TypeScript 前端接入已合并的故障、Agent 和维修 API，完成可降级的故障上报、维修诊断与结束维修摘要流程。

**架构：** 保持现有 React 应用壳、路由与智能配置页。将 HTTP/SSE 和业务 DTO 收敛在已有 `src/api.ts`；工作台、故障上报、维修执行分别是单一页面组件，只有当前确有多处调用的请求逻辑留在 API 边界。页面不保存或构造诊断事实，只渲染服务端返回状态。

**技术栈：** React 19、TypeScript、React Router、Vite、Vitest、Testing Library；不增加依赖。

## 全局约束

- 不复制、导入或运行 `03-ui-prototype/`；正式事实只位于 `codebase/frontend/`。
- 只使用已合并 API；不改后端、公开 API、数据库、部署或智能配置页的业务行为。
- 所有写请求使用调用期创建的 `Idempotency-Key`；不可把服务端会话、根因、方案或原始思维链提交给 API。
- `ADOPTED` 必须带服务端 `diagnosis_draft_id`；`DIRECT` 必须不带该字段。
- 401/403、网络失败、Agent/RAGFlow/LLM 不可用都必须保留人工路径，不模拟 AI 结果或引用。
- 最终验证包含前端测试、构建、全部原型静态回归、浏览器关键流和 `git diff --check`；Docker/真实 RAGFlow 由 DEV-001 环境复核。

---

### Task 1：扩展前端 API 契约与错误边界

**文件：**

- Modify: `codebase/frontend/src/api.ts`
- Modify: `codebase/frontend/src/api.test.ts`

**Consumes：** 已合并的 `/api/fault-reports`、`/api/agent/fault-reports/submit`、`/api/agent/operation-guidance`、`/api/agent/fault-diagnosis`、`/api/fault-reports/{id}/start-repair`、`/api/work-orders/{id}/repair-result` 以及 Agent Runtime SSE 契约。

**Produces：** `ApiError`、`postJson`、`createFaultReport`、`submitAgentFaultReport`、`getHealthScore`、`getOperationGuidance`、`runFaultDiagnosis`、`startRepair`、`completeRepair`、`readRunEvents` 和对应 TypeScript DTO；后续页面只调用这些函数。

- [ ] **Step 1: 写 API 客户端失败测试。**

```ts
it("sends adopted repair start with one idempotency key", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ work_order_id: "wo-1" }), { status: 200 })));
  await startRepair("fault-1", { mode: "ADOPTED", diagnosis_draft_id: "draft-1" });
  expect(fetch).toHaveBeenCalledWith("/api/fault-reports/fault-1/start-repair", expect.objectContaining({
    method: "POST",
    headers: expect.objectContaining({ "Idempotency-Key": expect.any(String) }),
    body: JSON.stringify({ mode: "ADOPTED", diagnosis_draft_id: "draft-1" }),
  }));
});

it("throws a public ApiError for a forbidden response", async () => {
  const validFault = { equipment_id: "eq-1", urgency: "HIGH", symptom: "液压压力异常", occurred_at: "2026-07-27T10:00:00+08:00", attachment_refs: [] };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: "FORBIDDEN" } }), { status: 403 })));
  await expect(createFaultReport(validFault)).rejects.toMatchObject({ status: 403, code: "FORBIDDEN" });
});
```

- [ ] **Step 2: 运行失败测试。**

Run: `npm --prefix codebase/frontend test -- src/api.test.ts`

Expected: FAIL，缺少维护/诊断 API 函数或错误类型。

- [ ] **Step 3: 最小实现 DTO、`postJson` 和 API 函数。**

```ts
export class ApiError extends Error {
  constructor(readonly status: number, readonly code: string | null) {
    super(code ?? `HTTP_${status}`);
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(body),
  });
}

export function startRepair(faultId: string, payload: StartRepairRequest) {
  return postJson<RepairStart>(`/api/fault-reports/${faultId}/start-repair`, payload);
}
```

`requestJson` 必须在非 2xx 时读取公开 `detail.code`（不存在则为 `null`）并抛出 `ApiError`；`DIRECT`/`ADOPTED` 以 TypeScript 联合类型约束。SSE 解析只能返回 `event` 与 JSON `data`，不记录或伪造事件。

- [ ] **Step 4: 验证 API 客户端。**

Run: `npm --prefix codebase/frontend test -- src/api.test.ts`

Expected: PASS。

- [ ] **Step 5: 提交稳定 API 边界。**

```bash
git add codebase/frontend/src/api.ts codebase/frontend/src/api.test.ts
git commit -m "feat(frontend): add maintenance and agent API client"
```

### Task 2：工作台与故障上报页面

**文件：**

- Create: `codebase/frontend/src/WorkbenchPage.tsx`
- Create: `codebase/frontend/src/WorkbenchPage.test.tsx`
- Create: `codebase/frontend/src/FaultReportPage.tsx`
- Create: `codebase/frontend/src/FaultReportPage.test.tsx`
- Modify: `codebase/frontend/src/App.tsx`
- Modify: `codebase/frontend/src/styles.css`

**Consumes：** Task 1 API 函数和 `ApiError`。

**Produces：** `/` 工作台和 `/fault-report` 的真实业务入口；其他路由保持不变。

- [ ] **Step 1: 写页面失败测试。**

```tsx
it("keeps manual fault submission available when the AI submission is unavailable", async () => {
  vi.mocked(submitAgentFaultReport).mockRejectedValue(new ApiError(503, "AGENT_CONFIG_INVALID"));
  render(<FaultReportPage />);
  await userEvent.click(screen.getByRole("button", { name: "使用 AI 整理" }));
  expect(await screen.findByText("AI 故障上报暂不可用，请继续人工填写。")) .toBeInTheDocument();
  expect(screen.getByRole("button", { name: "提交故障" })).toBeEnabled();
});

it("renders permission denial without static workbench data", async () => {
  vi.mocked(getHealthScore).mockRejectedValue(new ApiError(403, "FORBIDDEN"));
  render(<WorkbenchPage />);
  expect(await screen.findByText("无权查看工作台数据。")) .toBeInTheDocument();
  expect(screen.queryByText("模拟健康分")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: 运行失败测试。**

Run: `npm --prefix codebase/frontend test -- src/WorkbenchPage.test.tsx src/FaultReportPage.test.tsx`

Expected: FAIL，页面组件尚不存在。

- [ ] **Step 3: 最小实现受控表单与状态视图。**

```tsx
const [state, setState] = useState<"loading" | "ready" | "empty" | "forbidden" | "error">("loading");

function messageFor(error: unknown) {
  return error instanceof ApiError && error.status === 403 ? "无权执行此操作。" : "提交失败，请稍后重试。";
}

async function submitManual() {
  setSubmitting(true);
  try {
    const created = await createFaultReport(payload);
    setNotice(`故障已提交：${created.number}`);
  } catch (error) {
    setError(messageFor(error));
  } finally {
    setSubmitting(false);
  }
}
```

工作台只展示 API 实际返回的健康分或状态；故障表单收集 `equipment_id`、紧急程度、现象、发生时间、可选位置/描述，不接受附件正文。AI 上报只在用户确认后调用现有提交 API；失败不清空人工表单。

- [ ] **Step 4: 将 App 路由替换为新页面。**

```tsx
<Route path="/" element={<WorkbenchPage />} />
<Route path="/fault-report" element={<FaultReportPage />} />
<Route path="/repair-execution" element={<RepairExecutionPage />} />
```

保留 `/intelligent-config` 指向既有 `IntelligentConfigPage`，不复制或导入原型代码。

- [ ] **Step 5: 验证页面与路由。**

Run: `npm --prefix codebase/frontend test -- src/App.test.tsx src/WorkbenchPage.test.tsx src/FaultReportPage.test.tsx`

Expected: PASS。

- [ ] **Step 6: 提交。**

```bash
git add codebase/frontend/src/App.tsx codebase/frontend/src/WorkbenchPage.tsx codebase/frontend/src/WorkbenchPage.test.tsx codebase/frontend/src/FaultReportPage.tsx codebase/frontend/src/FaultReportPage.test.tsx codebase/frontend/src/styles.css
git commit -m "feat(frontend): integrate fault reporting workflows"
```

### Task 3：维修诊断、真实引用与直接开始边界

**文件：**

- Create: `codebase/frontend/src/RepairExecutionPage.tsx`
- Create: `codebase/frontend/src/RepairExecutionPage.test.tsx`
- Modify: `codebase/frontend/src/styles.css`

**Consumes：** Task 1 `runFaultDiagnosis`、`getOperationGuidance`、`startRepair` DTO；Task 2 路由。

**Produces：** 可从 `/repair-execution` 进入的受控诊断流程，向维修结果区传递真实 `work_order_id`、`start_mode` 和可选摘要。

- [ ] **Step 1: 写诊断失败测试。**

```tsx
it("shows adoption only for a server-ready diagnosis", async () => {
  vi.mocked(runFaultDiagnosis).mockResolvedValue({ state: "EVIDENCE_PENDING", diagnosis_draft_id: "draft-1", evidence: [], steps: 2, questions: 1 });
  render(<RepairExecutionPage />);
  await userEvent.click(screen.getByRole("button", { name: "开始 AI 诊断" }));
  expect(await screen.findByText("证据仍不足，可补充信息或直接开始维修。")) .toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "采纳 AI 建议并开始维修" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "直接开始维修" })).toBeEnabled();
});

it("renders returned citations collapsed and never invents a citation", async () => {
  vi.mocked(getOperationGuidance).mockResolvedValue({ state: "QUESTIONING", evidence: [{ citation: "chunk-9", text: "检查液压油温度" }] });
  render(<RepairExecutionPage />);
  await userEvent.click(screen.getByRole("button", { name: "获取操作指引" }));
  expect(await screen.findByRole("button", { name: "查看 1 条引用" })) .toBeInTheDocument();
  expect(screen.queryByText("引用：示例文档")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: 运行失败测试。**

Run: `npm --prefix codebase/frontend test -- src/RepairExecutionPage.test.tsx`

Expected: FAIL，维修页面尚不存在。

- [ ] **Step 3: 最小实现服务端诊断状态机 UI。**

```tsx
const canAdopt = diagnosis?.state === "DIAGNOSIS_READY" && Boolean(diagnosis.diagnosis_draft_id);

async function directStart() {
  const started = await startRepair(faultId, { mode: "DIRECT" });
  setRepair({ ...started, summary: null });
}

async function adoptStart() {
  if (!diagnosis?.diagnosis_draft_id) return;
  const started = await startRepair(faultId, { mode: "ADOPTED", diagnosis_draft_id: diagnosis.diagnosis_draft_id });
  setRepair({ ...started, summary: diagnosis.summary ?? null });
}
```

启用诊断时使用服务端返回的 `state`、`question`、`evidence`、`prefill`、`summary` 和 `diagnosis_draft_id`；回答/证据只提交 `diagnosis_draft_id` 与允许字段。`OPEN_LOADING` 的四步状态约三秒展示；消息区独立滚动且输入区固定。`UNAVAILABLE`、`EVIDENCE_PENDING`、错误与 403 均保留直接开始。

- [ ] **Step 4: 实现操作指引引用折叠与 SSE 消费。**

```tsx
<details>
  <summary>查看 {guidance.evidence.length} 条引用</summary>
  {guidance.evidence.map((item) => <p key={item.citation}><code>{item.citation}</code>{item.text}</p>)}
</details>
```

仅在后端实际返回 `evidence.length > 0` 时渲染 `<details>`。对 Agent Runtime 已返回的 `run_id` 使用 `readRunEvents` 读取 `/api/agent/runs/{run_id}/events`；流失败显示“流式结果中断，请按人工流程继续”，不得拼接虚构消息。

- [ ] **Step 5: 验证诊断与降级。**

Run: `npm --prefix codebase/frontend test -- src/RepairExecutionPage.test.tsx`

Expected: PASS。

- [ ] **Step 6: 提交。**

```bash
git add codebase/frontend/src/RepairExecutionPage.tsx codebase/frontend/src/RepairExecutionPage.test.tsx codebase/frontend/src/styles.css
git commit -m "feat(frontend): integrate repair diagnosis flow"
```

### Task 4：结束维修结果与 AI 摘要显隐

**文件：**

- Modify: `codebase/frontend/src/RepairExecutionPage.tsx`
- Modify: `codebase/frontend/src/RepairExecutionPage.test.tsx`

**Consumes：** Task 3 已启动的工单状态、`completeRepair`、仅内存保存的服务端摘要。

**Produces：** 已完成维修结果和符合 AC 的摘要位置。

- [ ] **Step 1: 写结束维修失败测试。**

```tsx
it("places adopted AI summary after parts notes and hides it for direct start", async () => {
  render(<RepairExecutionPage initialRepair={{ work_order_id: "wo-1", start_mode: "ADOPTED", summary: "已收集两类证据" }} />);
  await userEvent.type(screen.getByLabelText("备件更换说明"), "更换压力传感器");
  await userEvent.click(screen.getByRole("button", { name: "提交维修结果" }));
  const parts = screen.getByText("更换压力传感器");
  const summary = screen.getByText("AI 对话摘要：已收集两类证据");
  expect(parts.compareDocumentPosition(summary) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});
```

- [ ] **Step 2: 运行失败测试。**

Run: `npm --prefix codebase/frontend test -- src/RepairExecutionPage.test.tsx`

Expected: FAIL，结果区或摘要位置尚未实现。

- [ ] **Step 3: 最小实现维修结果表单。**

```tsx
{completed && <section aria-label="维修完成结果">
  <p>{completed.parts_replacement_notes}</p>
  {repair?.start_mode === "ADOPTED" && repair.summary && <p>AI 对话摘要：{repair.summary}</p>}
</section>}
```

提交只能调用 `completeRepair(workOrderId, { actual_cause, actual_solution, repair_result, parts_replacement_notes })`。结束维修字段以用户最终输入为准；`DIRECT` 或空摘要绝不显示摘要区。

- [ ] **Step 4: 验证。**

Run: `npm --prefix codebase/frontend test -- src/RepairExecutionPage.test.tsx`

Expected: PASS。

- [ ] **Step 5: 提交。**

```bash
git add codebase/frontend/src/RepairExecutionPage.tsx codebase/frontend/src/RepairExecutionPage.test.tsx
git commit -m "feat(frontend): show adopted diagnosis summary after repair"
```

### Task 5：完整前端验证、证据与审核交接

**文件：**

- Modify: `05-development/CHECKPOINTS.md`
- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`
- Modify: `workflow/state.json`

**Consumes：** Tasks 1–4 的精确提交和真实命令输出。

**Produces：** 可由 DEV-001 复核的 TASK-010 候选证据；不更新为已审核、已集成或解锁下游。

- [ ] **Step 1: 先运行前端测试和构建。**

Run:

```bash
npm --prefix codebase/frontend test
npm --prefix codebase/frontend run build
```

Expected: 所有前端测试和 TypeScript/Vite 构建 PASS。

- [ ] **Step 2: 运行静态回归与差异检查。**

Run:

```bash
for file in 06-testing/tests/*.test.js; do node "$file"; done
git diff origin/codex/stage-05-integration...HEAD --check
git diff --check
```

Expected: 每个静态回归 PASS，两个差异检查无输出。

- [ ] **Step 3: 执行浏览器关键流检查。**

检查 `/fault-report` 的人工提交与 AI 不可用降级、`/repair-execution` 的诊断加载/引用折叠/采纳/直接开始/结束维修摘要位置，以及 `/intelligent-config` 仍可加载。记录浏览器、日期、实际结果和不可用的外部环境，不伪称 Docker/RAGFlow 验证。

- [ ] **Step 4: 更新治理证据。**

将每个稳定 Commit、实际测试结果、候选精确 HEAD、未验证的 Docker/真实 RAGFlow 项、任务边界与回滚方式分别写入上述六个台账。`workflow/state.json` 只能标记为等待 DEV-001 审核，`dependencyUnlockAllowed` 必须保持 `false`。

- [ ] **Step 5: 提交治理证据并核验候选。**

```bash
git add 05-development/CHECKPOINTS.md 05-development/SELF_TEST.md 05-development/CODE_REVIEW.md 05-development/COMMIT_LOG.md workflow/DEV_TO_PM_HANDOFF.md workflow/state.json
git commit -m "docs(task-010): record frontend integration evidence"
git push -u origin codex/task-010-frontend-integration
gh pr create --draft --base codex/stage-05-integration --head codex/task-010-frontend-integration --title "[TASK-010] feat: integrate approved frontend flows" --body-file .git/TASK-010-PR.md
gh pr view --json number,headRefOid,baseRefName,isDraft,mergeStateStatus,url
```

Expected: 同一个 Draft PR 创建或更新成功，输出的 `headRefOid` 是完整候选 HEAD。随后仅请求 DEV-001 对该精确 HEAD 审核；不请求 Merge 授权。

## 计划自检

- 规格覆盖：API 契约（Task 1）、工作台/故障上报（Task 2）、诊断/引用/采纳/直接开始（Task 3）、结束维修摘要（Task 4）、全部证据与门禁（Task 5）。
- 范围：不引入依赖、不修改后端或原型，智能配置页只作为回归检查，不改变其实现。
- 安全：客户端不提交诊断事实；错误与降级不泄漏受保护内容或伪造 AI 输出。
- 流程：所有业务代码步骤都有先失败后转绿的测试和独立提交；最终只进入 DEV-001 审核等待状态。
