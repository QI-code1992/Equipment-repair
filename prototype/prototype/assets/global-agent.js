(function () {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function showToast(message) {
    let toast = $(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => toast.classList.remove("show"), 2400);
  }

  function removeLegacyAgentDrawer() {
    $("#openAi")?.remove();
    $("#agentDrawer")?.remove();
    $("#agentScrim")?.remove();
  }
  
  function initGlobalAgentWidget() {
    if (document.body.classList.contains("launcher") || document.body.dataset.globalAgentReady === "true") return;
    removeLegacyAgentDrawer();
    document.body.dataset.globalAgentReady = "true";
  
    const agentContext = window.__GLOBAL_AGENT_CONTEXT || {};
    const pageTitle = agentContext.pageTitle || $(".page-title")?.textContent?.trim() || document.title.split(" - ")[0] || "当前页面";
    const contextDevice = agentContext.device || null;
    const baseDevices = [
      { code: "EL-2024-019", name: "一号电动装载机", workshop: "总装一车间", line: "A1 产线", status: "高风险" },
      { code: "EL-2023-031", name: "二号电动装载机", workshop: "电驱车间", line: "E1 产线", status: "关注" },
      { code: "EL-2022-008", name: "三号电动装载机", workshop: "露天矿维修车间", line: "M1 保障线", status: "正常" }
    ];
    const devices = contextDevice
      ? [contextDevice, ...baseDevices.filter((device) => device.code !== contextDevice.code)]
      : baseDevices;
    const tabNames = { fault: "AI故障上报", ask: "智能问数", guide: "操作指引" };
    const placeholders = {
      fault: "按引导输入故障现象、发生时间、可能位置或补充回答",
      ask: "输入问数问题，未说明时间默认近30天",
      guide: "询问当前页面功能、操作路径或限制原因"
    };
    const defaultMessages = {
      fault: [{
        role: "bot",
        html: contextDevice
          ? `<div class="ops-agent-bubble-title">AI故障上报已就绪</div>我可以帮你通过对话生成待提交故障单。当前已识别设备详情上下文，可直接补充故障现象。<br><span class="muted">Agent 只生成“AI待提交”单，最终提交仍由用户在故障上报页面完成。</span>`
          : `<div class="ops-agent-bubble-title">AI故障上报已就绪</div>我可以帮你通过对话生成待提交故障单。请先选择设备。<br><span class="muted">Agent 只生成“AI待提交”单，最终提交仍由用户在故障上报页面完成。</span>`
      }],
      ask: [{
        role: "bot",
        html: `<div class="ops-agent-bubble-title">智能问数已就绪</div>可查询设备、故障、维修和工单数据。信息不足时我会追问；未说明时间范围时默认近30天。`
      }],
      guide: [{
        role: "bot",
        html: `<div class="ops-agent-bubble-title">操作指引已就绪</div>我会基于当前页面解释功能、操作路径、限制原因和下一步建议。跨页面流程会先确认目标。`
      }]
    };
    const freshFaultState = () => ({
      device: contextDevice,
      urgency: "",
      phenomenon: "",
      occurTime: "",
      location: "",
      desc: "",
      conditions: "",
      impact: "",
      tempAction: "",
      extraInfo: "",
      frequency: "",
      supplementIndex: 0,
      supplementAnswers: [],
      supplementLimit: 5,
      supplementCompleted: false,
      supplementFinishedEarly: false,
      analysisRunId: 0,
      attachments: [],
      stage: "collect",
      step: contextDevice ? "urgency" : "device",
      ticketNo: "",
      ticketStatus: "",
      optionalNoticeShown: false
    });
    const state = {
      currentTab: "fault",
      messages: JSON.parse(JSON.stringify(defaultMessages)),
      fault: freshFaultState(),
      ask: { context: { time: "近30天", scope: "全部设备" }, result: null, lastSuccess: null, awaitingCondition: false },
      guide: { expanded: false, awaitingCrossConfirm: false, flowTarget: "" }
    };
    let analysisSequence = 0;
  
    const root = document.createElement("div");
    root.className = "ops-agent-root";
    const robotIcon = (variant = "") => `<svg class="ops-agent-robot-icon ${variant}" viewBox="0 0 64 64" aria-hidden="true">
      <path class="ops-agent-robot-antenna" d="M32 9v7" />
      <circle class="ops-agent-robot-light" cx="32" cy="7" r="3" />
      <rect class="ops-agent-robot-head" x="13" y="18" width="38" height="32" rx="13" />
      <path class="ops-agent-robot-ear" d="M10 31h-4M58 31h-4" />
      <circle class="ops-agent-robot-eye" cx="25" cy="33" r="5.5" />
      <circle class="ops-agent-robot-eye" cx="39" cy="33" r="5.5" />
      <path class="ops-agent-robot-mouth" d="M20 43c6 4 18 4 24 0" />
      <path class="ops-agent-robot-visor" d="M20 25h24" />
    </svg>`;
    root.innerHTML = `
      <button class="ops-agent-fab" id="opsAgentFab" type="button" aria-label="打开运维Agent">
        <span class="ops-agent-fab-icon" aria-hidden="true">${robotIcon("is-fab")}</span>
      </button>
      <section class="ops-agent-panel" id="opsAgentPanel" role="dialog" aria-label="运维Agent">
        <header class="ops-agent-header">
          <div class="ops-agent-header-row">
            <div class="ops-agent-title-wrap">
              <div class="ops-agent-logo" aria-hidden="true">${robotIcon("is-header")}</div>
              <div>
                <div class="ops-agent-title">运维 Agent</div>
                <div class="ops-agent-subtitle">AI故障上报、智能问数、操作指引，支持多轮追问、附件识别与业务联动。</div>
              </div>
            </div>
            <div class="ops-agent-actions">
              <button class="ops-agent-icon-btn" id="opsAgentClear" type="button" title="清除当前Tab对话" aria-label="清除当前Tab对话">
                <svg class="ops-agent-broom-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M14.5 3.5 20.5 9.5" />
                  <path d="M13.2 5.8 18.2 10.8 9.2 19.8 4.2 14.8z" />
                  <path d="M4.2 14.8 2.9 19.1 4.9 21.1 9.2 19.8" />
                  <path d="M5.6 16.2 3.9 20.1" />
                  <path d="M7.2 17.8 5.5 21" />
                </svg>
              </button>
              <button class="ops-agent-icon-btn" id="opsAgentResize" type="button" title="展开/还原">↗</button>
              <button class="ops-agent-icon-btn" id="opsAgentClose" type="button" title="关闭">×</button>
            </div>
          </div>
          <nav class="ops-agent-tabs" id="opsAgentTabs">
            <button class="ops-agent-tab active" type="button" data-agent-tab="fault">AI故障上报</button>
            <button class="ops-agent-tab" type="button" data-agent-tab="ask">智能问数</button>
            <button class="ops-agent-tab" type="button" data-agent-tab="guide">操作指引</button>
          </nav>
        </header>
        <main class="ops-agent-body" id="opsAgentBody"></main>
        <footer class="ops-agent-input">
          <button class="ops-agent-attach" id="opsAgentAttach" type="button" title="上传附件" aria-label="上传附件">
            <svg class="ops-agent-upload-icon" viewBox="0 0 28 28" aria-hidden="true">
              <path class="file" d="M8 4.5h8.2L21 9.3v14.2H8z" />
              <path class="fold" d="M16.2 4.5v5h4.8" />
              <path class="arrow" d="M14 19V11.2" />
              <path class="arrow" d="M10.8 14.2 14 11l3.2 3.2" />
            </svg>
          </button>
          <input class="ops-agent-file-input" id="opsAgentFileInput" type="file" multiple accept="image/*,.pdf,.txt,.log,.csv,.xlsx,.xls,.doc,.docx,.mp4,.mov">
          <input class="ops-agent-text-input" id="opsAgentInput" placeholder="请描述故障现象，支持图片、日志、视频附件">
          <button class="ops-agent-send" id="opsAgentSend" type="button">发送</button>
        </footer>
      </section>
      <div class="ops-agent-modal-mask" id="agentDeviceModal">
        <div class="ops-agent-modal" role="dialog" aria-label="设备选择器">
          <div class="ops-agent-modal-head">
            <h3>选择设备</h3>
            <button class="ops-agent-icon-btn" id="opsAgentCloseDevice" type="button" aria-label="关闭设备选择器">×</button>
          </div>
          <div class="ops-agent-modal-body">
            <div class="ops-agent-search-line"><input value="EL" aria-label="搜索设备" data-agent-device-search><button class="ops-agent-primary" type="button" data-agent-device-search-button>搜索</button></div>
            <div class="ops-agent-search-result" data-agent-device-search-result>默认展示全部设备。</div>
            <table class="ops-agent-table">
              <thead><tr><th>设备编号</th><th>设备名称</th><th>所属车间</th><th>所属产线</th><th>状态</th></tr></thead>
              <tbody>${devices.map((device, index) => `<tr class="ops-agent-device-row" data-device-index="${index}"><td>${device.code}</td><td>${device.name}</td><td>${device.workshop}</td><td>${device.line}</td><td>${device.status}</td></tr>`).join("")}</tbody>
            </table>
          </div>
        </div>
      </div>`;
    document.body.appendChild(root);
  
    const fab = $("#opsAgentFab", root);
    const panel = $("#opsAgentPanel", root);
    const body = $("#opsAgentBody", root);
    const inputBar = $(".ops-agent-input", root);
    const attachButton = $("#opsAgentAttach", root);
    const input = $("#opsAgentInput", root);
    const fileInput = $("#opsAgentFileInput", root);
    const modal = $("#agentDeviceModal", root);
    const deviceSearchInput = $("[data-agent-device-search]", root);
    const deviceSearchButton = $("[data-agent-device-search-button]", root);
    const deviceSearchResult = $("[data-agent-device-search-result]", root);

    function filterDeviceRows() {
      const keyword = (deviceSearchInput?.value || "").trim().toLowerCase();
      let visibleCount = 0;
      $$(".ops-agent-device-row", root).forEach((row) => {
        const device = devices[Number(row.dataset.deviceIndex)];
        const haystack = [device.code, device.name, device.workshop, device.line, device.status].join(" ").toLowerCase();
        const visible = !keyword || haystack.includes(keyword);
        row.hidden = !visible;
        if (visible) visibleCount += 1;
      });
      if (deviceSearchResult) {
        deviceSearchResult.textContent = keyword
          ? visibleCount
            ? `已找到 ${visibleCount} 台匹配设备。`
            : "未找到匹配设备，请更换设备编号、名称、车间或产线关键词。"
          : "默认展示全部设备。";
      }
    }
  
    function addMsg(tab, role, html) {
      state.messages[tab].push({ role, html });
    }
  
    function renderMessages(tab) {
      return `<div class="ops-agent-stack">${state.messages[tab].map((message) => `
        <div class="ops-agent-message ${message.role === "user" ? "user" : ""}">
          ${message.role === "bot" ? `<div class="ops-agent-avatar">AI</div>` : ""}
          <div class="ops-agent-bubble">${message.html}</div>
        </div>`).join("")}</div>`;
    }

    function conversationSuggestions(tab) {
      if (tab === "ask") {
        return ["近30天高风险设备有哪些？", "本月维修超期工单有哪些？", "待接单故障单按紧急程度排序"];
      }
      if (tab === "guide") {
        return state.guide.flowTarget
          ? ["这个流程下一步怎么操作？", "哪些状态会阻塞闭环？", "如何回到当前页面继续处理？"]
          : ["当前页面怎么用？", "为什么无法删除设备？", "如何查看故障闭环？"];
      }
      const f = state.fault;
      if (!f.device) return ["我要选择设备", "如何按设备编号搜索？", "为什么一次只能选一台设备？"];
      if (!f.urgency) return ["什么情况选非常紧急？", "紧急程度怎么判断？", "我想选择一般"];
      if (!f.phenomenon) return ["主轴异响、振动变大", "报警停机并无法复位", "液压压力波动"];
      if (f.step === "optional") return ["今天上午10点，可能是驱动电机", "跳过非必填，进入补充追问", "可能是散热系统"];
      if (f.step === "supplement") return ["跳过本题", "结束追问并生成故障说明", "现场已复位但仍报警"];
      if (f.stage === "ready") return ["生成预览", "继续补充现场处置", "补充报警代码和参数"];
      return ["继续对话修改", "生成待提交单", "去故障上报页查看"];
    }

    function hasUserTurn(tab) {
      return state.messages[tab].some((message) => message.role === "user");
    }

    function conversationSuggestionsHTML(tab) {
      if (!hasUserTurn(tab)) return "";
      const suggestions = conversationSuggestions(tab).slice(0, 3);
      if (!suggestions.length) return "";
      return `<div class="ops-agent-card ops-agent-suggestions"><div class="ops-agent-bubble-title">你可以继续问</div><div class="ops-agent-quick-row">${suggestions.map((text) => `<button class="ops-agent-pill" type="button" data-agent-suggestion="${escapeHtml(text)}">${escapeHtml(text)}</button>`).join("")}</div></div>`;
    }
  
    function buildFaultDesc() {
      return buildNaturalFaultDescription();
    }

    function isMeaningfulSupplementAnswer(text, index = -1) {
      const clean = (text || "").trim();
      if (!clean || /^(跳过|无|没有|暂无|不补充|不知道|不清楚|未知)$/.test(clean)) return false;
      if (/^[\d\s.,，。;；:_-]+$/.test(clean)) return false;
      if (clean.length <= 1) return false;
      if (/^[a-zA-Z]+$/.test(clean) && clean.length <= 3) return false;
      const topicPatterns = [
        /启动|加速|运行|连续|重载|转向|制动|工况|条件|作业|负载|冷车|热车|上电|行驶/,
        /停机|限速|无法|影响|导致|造成|风险|产线|安全|作业|报警|降功率|停产/,
        /复位|停机|降载|切换|隔离|通知|维修|处理|重启|断电|检查|临时/,
        /报警|代码|参数|温度|振动|异响|泄漏|压力|SOC|电压|电流|指示灯|日志/,
        /首次|重复|频次|偶发|每天|每班|最近|再次|一直|经常|第.*次|历史/
      ];
      return index < 0 ? topicPatterns.some((pattern) => pattern.test(clean)) : topicPatterns[index].test(clean);
    }

    function buildNaturalFaultDescription() {
      const f = state.fault;
      const answers = f.supplementAnswers || [];
      const valid = answers.map((answer, index) => isMeaningfulSupplementAnswer(answer, index));
      const hasValidSupplement = valid.some(Boolean);
      const phenomenon = (f.phenomenon || "").trim();
      if (!hasValidSupplement && f.supplementCompleted) {
        return "用户已完成5项补充问答，但所填写内容无法识别出明确的故障工况、影响范围、临时处置、异常参数及历史发生情况。当前信息不足以形成有效的故障说明，建议重新补充具体的现场情况后再进行分析。";
      }

      const sentence = [];
      const condition = valid[0] && f.conditions
        ? f.conditions.replace(/^故障主要在/, "").replace(/等工况或条件下出现$/, "")
        : "";
      const impact = valid[1] && f.impact ? f.impact.replace(/^现场反馈影响为：/, "") : "";
      const action = valid[2] && f.tempAction ? f.tempAction.replace(/^现场临时处置为：/, "") : "";
      const observation = valid[3] && f.extraInfo ? f.extraInfo.replace(/^现场可观察信息：/, "") : "";
      const frequency = valid[4] && f.frequency ? f.frequency.replace(/^复现频次\/最近情况为：/, "") : "";
      const phenomenonText = isMeaningfulSupplementAnswer(phenomenon) ? phenomenon : "";
      const conditionText = condition ? (/时$|中$|过程$|过程中$|后$/.test(condition) ? condition : `${condition}过程中`) : "";

      sentence.push(`设备${conditionText ? `在${conditionText}` : ""}发生故障${phenomenonText ? `，现场描述为${phenomenonText}` : ""}${impact ? `，${impact}` : ""}。`);
      sentence.push(action ? `现场已进行${action}，但当前未明确设备是否恢复正常。` : "现场临时处置未提供有效信息，当前无法判断是否已采取复位、停机或其他处置。");
      sentence.push(observation ? `现场存在${observation}，具体报警代码及关键参数仍需进一步确认。` : "报警代码、运行参数或其他可观察异常信息未提供有效信息。");
      sentence.push(frequency ? `本次故障发生情况为${frequency}，建议进一步确认报警内容及处置后的设备状态。` : "历史发生情况未提供有效信息，建议补充是否首次发生、复现频次及最近一次发生时间。");
      if (f.occurTime || f.location) {
        sentence.push(`${[f.occurTime ? `故障发生时间为${f.occurTime}` : "", f.location ? `可能故障位置为${f.location}` : ""].filter(Boolean).join("，")}。`);
      }
      return sentence.join("");
    }
  
    function faultProgressHTML() {
      const f = state.fault;
      const done = (key) => {
        if (key === "device") return Boolean(f.device);
        if (key === "urgency") return Boolean(f.urgency);
        if (key === "phenomenon") return Boolean(f.phenomenon);
        if (key === "optional") return f.supplementCompleted || f.stage === "ready" || f.stage === "preview" || f.stage === "done";
        if (key === "preview") return f.stage === "preview" || f.stage === "done";
        return false;
      };
      const isActive = (key) => f.step === key || (key === "optional" && (f.step === "supplement" || f.step === "analyzing"));
      const step = (key, label) => `<div class="ops-agent-step ${done(key) ? "done" : isActive(key) ? "active" : ""}">${label}</div>`;
      return `<div class="ops-agent-progress">${step("device", "1 选择设备")}${step("urgency", "2 紧急程度")}${step("phenomenon", "3 故障现象")}${step("optional", "4 补充信息")}${step("preview", "5 预览/待提交")}</div>`;
    }
  
    function faultGuideHTML() {
      const f = state.fault;
      if (f.stage === "preview" || f.stage === "done") return "";
      if (!f.device) {
        return `<div class="ops-agent-card notice"><div class="ops-agent-bubble-title">第1步：选择设备</div>故障上报必须先选择 1 台设备。<div class="ops-agent-card-actions"><button class="ops-agent-primary" type="button" data-agent-action="choose-device">选择设备</button></div></div>`;
      }
      if (!f.urgency) {
        return `<div class="ops-agent-card"><div class="ops-agent-bubble-title">第2步：请选择紧急程度</div><div class="ops-agent-card-actions"><button class="ops-agent-primary" data-urgency="非常紧急" type="button">非常紧急</button><button class="ops-agent-ghost" data-urgency="紧急" type="button">紧急</button><button class="ops-agent-ghost" data-urgency="一般" type="button">一般</button></div></div>`;
      }
      if (!f.phenomenon) {
        return `<div class="ops-agent-card"><div class="ops-agent-bubble-title">第3步：请描述故障现象</div>请用一句话描述设备出现了什么异常，例如：主轴异响、振动变大、温升异常、报警停机、漏油等。<br><span class="muted">输入后，我会继续引导发生时间和可能故障位置（非必填）。</span></div>`;
      }
      if (f.step === "optional") {
        return `<div class="ops-agent-card"><div class="ops-agent-bubble-title">第4步：补充信息</div>请先补充可选信息：故障发生时间和可能的故障位置。例如：今天上午10点，可能是驱动电机或散热系统。<div class="ops-agent-card-actions"><button class="ops-agent-ghost" type="button" data-agent-action="skip-optional">跳过非必填，进入补充追问</button></div></div>`;
      }
      if (f.step === "supplement") {
        return `<div class="ops-agent-card"><div class="ops-agent-bubble-title">补充追问 ${f.supplementIndex + 1}/5</div>${escapeHtml(currentSupplementQuestion())}<br><span class="muted">这些追问用于形成故障说明：现象+条件+影响+已做的临时处置。最多追问5个，可随时结束。</span><div class="ops-agent-card-actions"><button class="ops-agent-ghost" type="button" data-agent-action="skip-supplement-question">跳过本题</button><button class="ops-agent-primary" type="button" data-agent-action="finish-supplement-now">结束追问并生成故障说明</button></div></div>`;
      }
      if (f.step === "analyzing") {
        return `<div class="ops-agent-card"><div class="ops-agent-bubble-title">AI大模型正在分析中</div>正在汇总本轮问答信息并生成故障说明，请稍候。<br><span class="muted">将结合设备、紧急程度、故障现象、补充信息和追问回答进行总结。</span></div>`;
      }
      return `<div class="ops-agent-card success"><div class="ops-agent-bubble-title">${f.supplementFinishedEarly ? "已结束追问并生成故障说明" : "五轮追问已完成"}</div><div class="muted">大模型总结已形成故障说明。</div><div class="ops-agent-readonly">${escapeHtml(buildFaultDesc())}</div><div class="ops-agent-card-actions"><button class="ops-agent-primary" type="button" data-agent-action="make-preview">生成预览</button><button class="ops-agent-ghost" type="button" data-agent-action="add-more">继续补充</button></div></div>`;
    }
  
    function previewHTML() {
      const f = state.fault;
      if (f.stage !== "preview" && f.stage !== "done") return "";
      const d = f.device || {};
      const attachmentNames = f.attachments.map((file) => file.name || file).join("、");
      return `<div class="ops-agent-message"><div class="ops-agent-avatar">AI</div><div class="ops-agent-bubble">
        <div class="ops-agent-bubble-title">故障单只读预览</div>
        <div class="ops-agent-readonly">预览字段不可直接编辑；如需调整，请继续对话修改。</div>
        <div class="ops-agent-card"><dl class="ops-agent-field-grid">
          <dt>故障编号</dt><dd>${escapeHtml(f.ticketNo || "生成AI待提交单后产生")}</dd>
          <dt>设备</dt><dd>${escapeHtml(d.name || "-")}</dd>
          <dt>所属车间</dt><dd>${escapeHtml(d.workshop || "-")}</dd>
          <dt>所属产线</dt><dd>${escapeHtml(d.line || "-")}</dd>
          <dt>紧急程度</dt><dd>${escapeHtml(f.urgency || "紧急")}</dd>
          <dt>故障现象</dt><dd>${escapeHtml(f.phenomenon || "-")}</dd>
          <dt>发生时间</dt><dd>${escapeHtml(f.occurTime || "未填写，可在故障上报页补充")}</dd>
          <dt>可能位置</dt><dd>${escapeHtml(f.location || "未填写，可在故障上报页补充")}</dd>
          <dt>故障说明</dt><dd>${escapeHtml(buildFaultDesc())}</dd>
          <dt>附件</dt><dd>${f.attachments.length ? escapeHtml(attachmentNames) : "未上传，可稍后补充"}</dd>
          <dt>状态</dt><dd>${escapeHtml(f.ticketStatus || "预览待确认")}</dd>
        </dl></div>
        <div class="ops-agent-card-actions">${f.stage === "preview" ? `<button class="ops-agent-primary" type="button" data-agent-action="make-ticket">生成待提交单</button><button class="ops-agent-ghost" type="button" data-agent-action="continue-fault">继续对话</button>` : `<a class="ops-agent-primary" href="fault-report.html">去故障上报页查看</a><button class="ops-agent-ghost" type="button" data-agent-action="continue-fault">继续对话修改</button>`}</div>
      </div></div>`;
    }
  
    function formatFileSize(size) {
      if (!Number.isFinite(size) || size <= 0) return "未知大小";
      if (size < 1024) return `${size}B`;
      if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`;
      return `${(size / 1024 / 1024).toFixed(1)}MB`;
    }

    function attachmentPanelHTML() {
      const files = state.fault.attachments;
      if (!files.length) return "";
      return `<div class="ops-agent-card ops-agent-attachment-panel">
        <div class="ops-agent-bubble-title">附件上传</div>
        <div class="ops-agent-attachment-list">
          ${files.map((file) => `<div class="ops-agent-attachment-item">
            <span class="ops-agent-attachment-file-icon">${file.status === "uploading" ? "…" : "✓"}</span>
            <span class="ops-agent-attachment-meta"><b>${escapeHtml(file.name || file)}</b><small>${escapeHtml(file.type || "附件")} · ${escapeHtml(formatFileSize(file.size || 0))} · ${file.status === "uploading" ? "上传中" : "上传完成"}</small></span>
            <button class="ops-agent-attachment-remove" type="button" data-attachment-remove="${escapeHtml(file.id || "")}" aria-label="移除附件">×</button>
          </div>`).join("")}
        </div>
      </div>`;
    }

    function faultHTML() {
      return `${faultProgressHTML()}${renderMessages("fault")}${attachmentPanelHTML()}${faultGuideHTML()}${previewHTML()}`;
    }
  
    function detectAskIntent(question) {
      if (/维修超期|超期工单|工单超期/.test(question)) return "overdue";
      if (/待接单|紧急程度|非常紧急/.test(question)) return "dispatch";
      if (/故障最多|频次|排行|趋势/.test(question)) return "frequency";
      if (/原因|为什么|根因/.test(question)) return "reason";
      if (/报告|摘要|管理层/.test(question)) return "summary";
      return "risk";
    }

    function buildAskFollowupQuestions(question, result) {
      const scopeFollowup = result.context.scope === "一车间" ? "切换查看全部设备" : "只看一车间的数据";
      if (result.intent === "overdue") {
        return [scopeFollowup, "哪些工单超期最久？", "可以按负责人汇总超期原因吗？"];
      }
      if (result.intent === "dispatch") {
        return [scopeFollowup, "只看非常紧急的待接单故障", "这些故障分别影响哪些产线？"];
      }
      if (result.intent === "frequency") {
        return [scopeFollowup, "故障最多的前三台设备原因是什么？", "这些设备近30天趋势如何？"];
      }
      if (result.intent === "reason") {
        return [scopeFollowup, "哪些原因需要优先处理？", "可以生成一段处理建议吗？"];
      }
      if (result.intent === "summary") {
        return [scopeFollowup, "把摘要改成管理层口径", "列出需要立即处理的事项"];
      }
      return [scopeFollowup, "这些高风险设备的主要原因是什么？", "可以生成一段报告摘要吗？"];
    }

    function askFollowupsHTML(question, result) {
      const followups = buildAskFollowupQuestions(question, result).slice(0, 3);
      return `<div class="ops-agent-card ops-agent-suggestions"><div class="ops-agent-bubble-title">你可以继续问</div><div class="ops-agent-quick-row">${followups.map((text) => `<button class="ops-agent-pill" type="button" data-agent-suggestion="${escapeHtml(text)}">${escapeHtml(text)}</button>`).join("")}</div></div>`;
    }

    function askAnswerHTML(result, question) {
      if (!result) return "";
      return `<div class="ops-agent-bubble-title">查询结果：${escapeHtml(result.context.time)} ${escapeHtml(result.context.scope)}</div>
        <p class="muted">${escapeHtml(result.note)}</p>
        <div class="ops-agent-result-grid">${result.metrics.map((metric) => `<div class="ops-agent-metric"><label>${escapeHtml(metric.label)}</label><b>${escapeHtml(metric.value)}</b></div>`).join("")}</div>
        <div class="ops-agent-table-wrap"><table class="ops-agent-table"><thead><tr>${result.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead><tbody>${result.rows.map((row) => `<tr>${result.columns.map((column) => `<td>${escapeHtml(row[column] || "-")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
        <div class="ops-agent-card-actions"><button class="ops-agent-ghost" type="button" data-agent-action="copy-ask">复制结果</button><button class="ops-agent-ghost" type="button" data-agent-action="export-ask">导出Excel</button><button class="ops-agent-ghost" type="button" data-agent-action="report-ask">生成报告摘要</button></div>
        ${askFollowupsHTML(question, result)}`;
    }
  
    function askHTML() {
      const recommended = [
        "近30天高风险设备有哪些？",
        "本月维修超期工单有哪些？",
        "一车间近7天故障最多的设备有哪些？",
        "待接单故障单按紧急程度排序"
      ];
      const recommendedCard = hasUserTurn("ask") ? "" : `<div class="ops-agent-card"><div class="ops-agent-bubble-title">推荐问题</div><div class="ops-agent-quick-row">${recommended.map((question) => `<button class="ops-agent-pill" type="button" data-ask="${question}">${question}</button>`).join("")}</div></div>`;
      return `${renderMessages("ask")}${recommendedCard}`;
    }
  
    function guideHTML() {
      const flowCard = state.guide.awaitingCrossConfirm
        ? `<div class="ops-agent-card notice"><div class="ops-agent-bubble-title">跨页面流程确认</div>你是想查看某台设备的故障闭环，还是查看全部未闭环故障？<div class="ops-agent-card-actions"><button class="ops-agent-primary" type="button" data-flow-target="device">某台设备闭环</button><button class="ops-agent-ghost" type="button" data-flow-target="all">全部未闭环故障</button></div></div>`
        : "";
      const doneCard = state.guide.flowTarget
        ? `<div class="ops-agent-card success"><div class="ops-agent-bubble-title">故障闭环查看路径</div>${state.guide.flowTarget === "device" ? "设备台账 → 选择设备 → 设备详情 → 历史故障/维修记录 → 查看处理闭环。" : "故障上报 → 筛选待接单/处理中/待验收 → 查看故障详情 → 跟踪闭环节点。"}</div>`
        : "";
      return `<div class="ops-agent-context"><span><b>当前页面：</b>${escapeHtml(pageTitle)}</span><span>仅操作指引 Tab 展示页面上下文</span></div>
        ${renderMessages("guide")}
        <div class="ops-agent-quick-row"><button class="ops-agent-pill" type="button" data-guide="how">当前页面怎么用？</button><button class="ops-agent-pill" type="button" data-guide="delete">为什么无法删除设备？</button><button class="ops-agent-pill" type="button" data-guide="flow">如何查看故障闭环？</button></div>
        ${flowCard}${doneCard}${conversationSuggestionsHTML("guide")}`;
    }
  
    function render() {
      $$(".ops-agent-tab", root).forEach((tab) => tab.classList.toggle("active", tab.dataset.agentTab === state.currentTab));
      const supportsAttachment = state.currentTab === "fault";
      inputBar.classList.toggle("is-attach-hidden", !supportsAttachment);
      attachButton.hidden = !supportsAttachment;
      attachButton.style.display = supportsAttachment ? "" : "none";
      input.placeholder = placeholders[state.currentTab];
      body.innerHTML = state.currentTab === "fault" ? faultHTML() : state.currentTab === "ask" ? askHTML() : guideHTML();
      body.scrollTop = body.scrollHeight;
    }
  
    function openPanel() {
      panel.classList.add("is-open");
      fab.hidden = true;
      render();
    }
  
    function closePanel() {
      panel.classList.remove("is-open");
      fab.hidden = false;
    }
  
    function parseUrgencyValue(text) {
      if (/非常紧急|特急|严重|停机|立即|马上|高优先/.test(text)) return "非常紧急";
      if (/一般|普通|不紧急|低优先/.test(text)) return "一般";
      if (/紧急|急/.test(text)) return "紧急";
      return "";
    }

    function detectMultiDevice(text) {
      const codeMatches = text.match(/EL-\d{4}-\d{3}|EQ-[A-Z]+-\d{3}|CNC加工中心\d+号|装载机\d+号/g) || [];
      return codeMatches.length > 1 || /多台|两台|2台|三台|同时.*设备|以及.*设备|和.*设备/.test(text);
    }

    function isFaultPhenomenonProvided(text) {
      return Boolean(text.trim());
    }

    function parseOptionalFaultInfo(text) {
      const f = state.fault;
      if (/今天|昨天|上午|下午|晚上|\d+点|\d{1,2}:\d{2}/.test(text)) {
        f.occurTime = text.match(/今天[^，。；;]*/)?.[0]
          || text.match(/昨天[^，。；;]*/)?.[0]
          || text.match(/\d+点[^，。；;]*/)?.[0]
          || text.match(/\d{1,2}:\d{2}[^，。；;]*/)?.[0]
          || text;
      }
      if (/电机|电池|BMS|液压|泵|传感器|控制器|油路|散热|主轴|轴承|制动|转向/.test(text)) {
        f.location = text.match(/电机|电池|BMS|液压|泵|传感器|控制器|油路|散热|主轴|轴承|制动|转向/)?.[0] || "";
      }
      if (!/^(跳过|无|没有|暂无|不补充)$/.test(text.trim())) {
        f.desc = f.desc ? `${f.desc}；${text}` : text;
      }
    }

    function getSupplementQuestions() {
      return [
        "故障通常在什么工况或条件下出现？例如启动、加速、连续运行、重载作业、转向或制动时。",
        "这次故障对生产、安全或设备运行造成了什么影响？例如停机、限速、无法作业、存在安全风险。",
        "现场已经做过哪些临时处置？例如停机、复位、降载、切换备用设备或通知维修。",
        "是否有报警代码、温度、振动、异响、泄漏、压力、SOC 等可观察信息？",
        "这个问题是首次出现还是重复出现？大概频次和最近一次出现时间是什么？"
      ];
    }

    function currentSupplementQuestion() {
      const f = state.fault;
      return getSupplementQuestions()[f.supplementIndex] || "";
    }

    function mergeFaultText(base, extra) {
      if (!extra) return base || "";
      return base ? `${base}；${extra}` : extra;
    }

    function summarizeSupplementAnswer(index, text) {
      const clean = text.trim();
      if (!isMeaningfulSupplementAnswer(clean, index)) return "未提供有效信息";
      if (index === 0) return `故障主要在${clean.replace(/^在/, "")}等工况或条件下出现`;
      if (index === 1) return /影响|导致|造成|停机|限速|无法|风险/.test(clean) ? clean : `现场反馈影响为：${clean}`;
      if (index === 2) return /已|已经|临时|复位|停机|降载|切换|隔离|通知|处理/.test(clean) ? clean : `现场临时处置为：${clean}`;
      if (index === 3) return `现场可观察信息：${clean}`;
      if (index === 4) return /首次|重复|频次|每天|每班|偶发|一直|最近/.test(clean) ? clean : `复现频次/最近情况为：${clean}`;
      return clean;
    }

    function answerSupplementQuestion(text) {
      const f = state.fault;
      const index = Math.min(f.supplementIndex, f.supplementLimit - 1);
      const summary = summarizeSupplementAnswer(index, text);
      f.supplementAnswers[index] = text.trim();
      if (index === 0) f.conditions = mergeFaultText(f.conditions, summary);
      if (index === 1) f.impact = mergeFaultText(f.impact, summary);
      if (index === 2) f.tempAction = mergeFaultText(f.tempAction, summary);
      if (index === 3) f.extraInfo = mergeFaultText(f.extraInfo, summary);
      if (index === 4) f.frequency = mergeFaultText(f.frequency, summary);
      if (index + 1 >= f.supplementLimit) {
        finishSupplementQuestions();
        return;
      }
      f.supplementIndex = index + 1;
      addMsg("fault", "bot", `已记录本轮回答。补充追问 ${f.supplementIndex + 1}/5：${escapeHtml(currentSupplementQuestion())}`);
    }

    function skipSupplementQuestion() {
      const f = state.fault;
      const index = Math.min(f.supplementIndex, f.supplementLimit - 1);
      f.supplementAnswers[index] = "";
      if (index + 1 >= f.supplementLimit) {
        finishSupplementQuestions(false);
        return;
      }
      f.supplementIndex = index + 1;
      addMsg("fault", "bot", `已跳过本题。补充追问 ${f.supplementIndex + 1}/5：${escapeHtml(currentSupplementQuestion())}`);
    }

    function startSupplementQuestions(skippedOptional = false) {
      const f = state.fault;
      f.step = "supplement";
      f.supplementIndex = 0;
      addMsg("fault", "bot", `${skippedOptional ? "已跳过非必填信息。" : "可选信息已记录。"}补充追问 1/5：${escapeHtml(currentSupplementQuestion())}`);
    }

    function finishSupplementQuestions(completedAll = true) {
      const f = state.fault;
      const runId = analysisSequence + 1;
      analysisSequence = runId;
      f.analysisRunId = runId;
      f.step = "analyzing";
      f.stage = "analyzing";
      f.desc = buildFaultDesc();
      setTimeout(() => {
        if (state.fault.analysisRunId !== runId) return;
        completeSupplementAnalysis(completedAll);
      }, 1200);
    }

    function completeSupplementAnalysis(completedAll = true) {
      const f = state.fault;
      f.supplementCompleted = true;
      f.supplementFinishedEarly = !completedAll;
      f.step = "ready";
      f.stage = "ready";
      f.desc = buildFaultDesc();
      render();
    }

    function validateFaultStepInput(text) {
      const f = state.fault;
      if (f.step === "analyzing") {
        addMsg("fault", "bot", "AI大模型正在分析中，请稍候。分析完成后会自动生成故障说明预览卡片。");
        return false;
      }
      if (!f.device) {
        addMsg("fault", "bot", "当前步骤需要先选择设备。请点击“选择设备”，每次仅支持选择 1 台设备。");
        f.step = "device";
        return false;
      }
      if (f.step === "urgency") {
        const urgency = parseUrgencyValue(text);
        if (!urgency) {
          addMsg("fault", "bot", "当前步骤需要先选择紧急程度。请输入或点击：非常紧急、紧急、一般。");
          return false;
        }
        f.urgency = urgency;
        f.step = "phenomenon";
        addMsg("fault", "bot", "已记录紧急程度。第3步：请描述故障现象。请用一句话描述设备出现了什么异常，例如：主轴异响、振动变大、温升异常、报警停机、漏油等。输入后，我会继续引导发生时间和可能故障位置（非必填）。");
        return true;
      }
      if (f.step === "phenomenon") {
        if (detectMultiDevice(text)) {
          addMsg("fault", "bot", "识别到你一次描述了多台设备。每次仅支持上报1台设备，请重新选择其中1台设备后再继续。");
          return false;
        }
        if (!isFaultPhenomenonProvided(text)) {
          addMsg("fault", "bot", "故障现象不能为空。请按现场真实情况自定义输入。");
          return false;
        }
        f.phenomenon = text.trim();
        f.desc = f.phenomenon;
        f.step = "optional";
        addMsg("fault", "bot", "已记录故障现象。第4步：补充信息。请补充发生时间和可能故障位置（非必填）；也可以点击“跳过非必填，进入补充追问”。");
        return true;
      }
      if (f.step === "optional") {
        parseOptionalFaultInfo(text);
        startSupplementQuestions(false);
        return true;
      }
      if (f.step === "supplement") {
        answerSupplementQuestion(text);
        return true;
      }
      parseOptionalFaultInfo(text);
      f.stage = "ready";
      addMsg("fault", "bot", "已补充到故障说明中。你可以继续补充，或生成结构化预览。");
      return true;
    }
  
    function validatePreview() {
      const f = state.fault;
      if (!f.device) {
        addMsg("fault", "bot", "还缺少必填项：请选择 1 台设备。设备未选择时不能生成预览。");
        render();
        showToast("必须先选择1台设备");
        return;
      }
      if (!f.urgency) {
        addMsg("fault", "bot", "请先选择紧急程度，再描述故障现象。");
        render();
        return;
      }
      if (!f.phenomenon) {
        addMsg("fault", "bot", "还缺少必填项：故障现象。请描述设备出现了什么异常。");
        render();
        return;
      }
      if (!f.supplementCompleted) {
        f.step = f.step === "optional" ? "optional" : "supplement";
        addMsg("fault", "bot", "请先完成第4步补充信息，并完成或结束补充追问，再生成预览。追问结束后我会进行大模型总结，形成故障说明。");
        render();
        return;
      }
      f.stage = "preview";
      f.step = "preview";
      render();
    }

    function buildAskResult(text, follow = false) {
      const time = /近\s*7\s*天|7天/.test(text) ? "近7天" : /本月/.test(text) ? "本月" : /近\s*30\s*天|30天/.test(text) ? "近30天" : state.ask.context.time || "近30天";
      const scope = /一车间/.test(text) ? "一车间" : /二车间/.test(text) ? "二车间" : /全部设备|全部/.test(text) ? "全部设备" : follow ? state.ask.context.scope : "全部设备";
      const intent = detectAskIntent(text);
      const context = { time, scope };
      const prefix = follow ? `已继承上一轮时间范围，并按“${scope}”继续分析` : `已按 ${time}、${scope} 完成查询`;
      const variants = {
        risk: {
          note: `${prefix}。当前高风险主要集中在电驱、BMS 通信和液压压力波动，建议优先处理连续告警设备。`,
          metrics: [
            { label: "高风险设备", value: scope === "一车间" ? "4" : "7" },
            { label: "风险上升", value: scope === "一车间" ? "2" : "3" },
            { label: "待处理工单", value: scope === "一车间" ? "3" : "5" }
          ],
          columns: ["设备", "风险等级", "主要原因"],
          rows: [
            { 设备: "EL-2024-019", 风险等级: "高", 主要原因: "驱动电机过温限扭" },
            { 设备: "EL-2023-031", 风险等级: "高", 主要原因: "BMS 通信中断 2 次" },
            { 设备: "EL-2022-008", 风险等级: "中", 主要原因: "液压压力波动" }
          ]
        },
        overdue: {
          note: `${prefix}。维修超期集中在备件等待和外协检测两个环节，最长超期 26 小时。`,
          metrics: [
            { label: "超期工单", value: scope === "一车间" ? "3" : "6" },
            { label: "最长超期", value: "26h" },
            { label: "平均超期", value: "9h" }
          ],
          columns: ["工单", "设备", "超期原因"],
          rows: [
            { 工单: "WO-2407018", 设备: "EL-2024-019", 超期原因: "驱动电机备件等待 26h" },
            { 工单: "WO-2406981", 设备: "EL-2025-006", 超期原因: "外协绝缘检测排队" },
            { 工单: "WO-2406955", 设备: "EL-2021-047", 超期原因: "维修复检未确认" }
          ]
        },
        dispatch: {
          note: `${prefix}。待接单故障单按紧急程度排序后，非常紧急单据需要优先派发到电驱维修组。`,
          metrics: [
            { label: "待接单", value: scope === "一车间" ? "4" : "8" },
            { label: "非常紧急", value: "2" },
            { label: "平均等待", value: "37m" }
          ],
          columns: ["故障单", "紧急程度", "建议班组"],
          rows: [
            { 故障单: "GD20260702003", 紧急程度: "非常紧急", 建议班组: "电驱维修组" },
            { 故障单: "GD20260702001", 紧急程度: "非常紧急", 建议班组: "BMS 专项组" },
            { 故障单: "GD20260701988", 紧急程度: "紧急", 建议班组: "液压维修组" }
          ]
        },
        frequency: {
          note: `${prefix}。故障频次排行显示，EL-2023-031 近7天重复告警最多，建议排查通信链路稳定性。`,
          metrics: [
            { label: "重复故障设备", value: scope === "一车间" ? "3" : "5" },
            { label: "最高频次", value: "4次" },
            { label: "环比变化", value: "+18%" }
          ],
          columns: ["设备", "近7天故障", "高频类型"],
          rows: [
            { 设备: "EL-2023-031", 近7天故障: "4次", 高频类型: "BMS 通信中断" },
            { 设备: "EL-2024-019", 近7天故障: "3次", 高频类型: "电机温升异常" },
            { 设备: "EL-2024-102", 近7天故障: "2次", 高频类型: "制动压力波动" }
          ]
        },
        reason: {
          note: `${prefix}。从当前结果看，主要原因可归为温升、通信和液压压力三类，其中温升类影响优先级最高。`,
          metrics: [
            { label: "原因类别", value: "3" },
            { label: "温升占比", value: "42%" },
            { label: "需复核设备", value: "2" }
          ],
          columns: ["原因类别", "关联设备", "处理建议"],
          rows: [
            { 原因类别: "驱动电机温升", 关联设备: "EL-2024-019", 处理建议: "检查散热风道与限扭参数" },
            { 原因类别: "BMS 通信中断", 关联设备: "EL-2023-031", 处理建议: "复核线束接插件和通信日志" },
            { 原因类别: "液压压力波动", 关联设备: "EL-2022-008", 处理建议: "核查泵压与阀组状态" }
          ]
        },
        summary: {
          note: `${prefix}。报告摘要已按管理层口径整理：风险集中、处置优先级和待协调资源如下。`,
          metrics: [
            { label: "重点风险", value: "3类" },
            { label: "需今日处理", value: "5项" },
            { label: "需协调资源", value: "2项" }
          ],
          columns: ["摘要项", "结论", "建议动作"],
          rows: [
            { 摘要项: "风险集中", 结论: "电驱与BMS 问题占比较高", 建议动作: "今日完成高风险设备复核" },
            { 摘要项: "工单压力", 结论: "超期多来自备件等待", 建议动作: "协调备件到货和替代件确认" },
            { 摘要项: "运维建议", 结论: "重复故障需专项排查", 建议动作: "建立 EL-2023-031 跟踪单" }
          ]
        }
      };
      return { intent, context, ...variants[intent] };
    }
  
    function runAsk(text, follow = false) {
      if (/^查设备$|^设备$|^查数据$/.test(text.trim())) {
        addMsg("ask", "bot", "这个问题条件不足。请补充指标口径、对象范围或时间范围。");
        state.ask.awaitingCondition = true;
        render();
        return;
      }
      const result = buildAskResult(text, follow);
      state.ask.context = result.context;
      state.ask.result = result;
      state.ask.lastSuccess = state.ask.result;
      addMsg("ask", "bot", askAnswerHTML(result, text));
      render();
    }
  
    function handleSend() {
      const text = input.value.trim();
      if (!text) {
        showToast("请输入内容");
        return;
      }
      addMsg(state.currentTab, "user", escapeHtml(text));
      if (state.currentTab === "fault") {
        validateFaultStepInput(text);
      } else if (state.currentTab === "ask") {
        runAsk(text, /只看|继续|改成|换成/.test(text));
        input.value = "";
        return;
      } else if (/闭环|跨页面|跳转|流程/.test(text)) {
        state.guide.awaitingCrossConfirm = true;
        addMsg("guide", "bot", "这是跨页面流程。我先确认你的具体目标，再给出路径，不会直接带你离开当前页面。");
      } else {
        addMsg("guide", "bot", `当前页面是“${escapeHtml(pageTitle)}”。你可以先确认目标对象，再按页面主按钮或筛选区完成操作；需要跨页面时我会先确认。`);
      }
      input.value = "";
      render();
    }
  
    fab.addEventListener("click", () => {
      if (fab.dataset.dragged !== "true") openPanel();
      fab.dataset.dragged = "false";
    });
    $("#opsAgentClose", root).addEventListener("click", closePanel);
    $("#opsAgentResize", root).addEventListener("click", () => {
      panel.classList.toggle("is-expanded");
      showToast(panel.classList.contains("is-expanded") ? "已展开弹框" : "已还原弹框");
    });
    $("#opsAgentClear", root).addEventListener("click", () => {
      state.messages[state.currentTab] = JSON.parse(JSON.stringify(defaultMessages[state.currentTab]));
      if (state.currentTab === "fault") state.fault = freshFaultState();
      if (state.currentTab === "ask") state.ask = { context: { time: "近30天", scope: "全部设备" }, result: null, lastSuccess: null, awaitingCondition: false };
      if (state.currentTab === "guide") state.guide = { expanded: false, awaitingCrossConfirm: false, flowTarget: "" };
      render();
      showToast("已清除当前Tab对话，其他Tab历史不受影响");
    });
    $("#opsAgentTabs", root).addEventListener("click", (event) => {
      const tab = event.target.closest("[data-agent-tab]");
      if (!tab) return;
      state.currentTab = tab.dataset.agentTab;
      render();
    });
    $("#opsAgentSend", root).addEventListener("click", handleSend);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") handleSend();
    });
    attachButton.addEventListener("click", () => {
      if (state.currentTab === "fault") {
        fileInput.click();
      } else {
        showToast("附件上传仅用于AI故障上报");
      }
    });
    fileInput.addEventListener("change", () => {
      handleAttachmentFiles(fileInput.files);
      fileInput.value = "";
    });

    function handleAttachmentFiles(fileList) {
      const files = Array.from(fileList || []);
      if (!files.length) return;
      const now = Date.now();
      files.forEach((file, index) => {
        const id = `att-${now}-${index}`;
        state.fault.attachments.push({
          id,
          name: file.name,
          size: file.size,
          type: file.type || "附件",
          status: "uploading"
        });
        setTimeout(() => {
          const target = state.fault.attachments.find((item) => item.id === id);
          if (!target) return;
          target.status = "done";
          render();
        }, 650 + index * 160);
      });
      addMsg("fault", "bot", `已选择 ${files.length} 个附件，正在上传并关联到当前故障单。`);
      render();
      showToast("附件上传中");
    }
    body.addEventListener("click", (event) => {
      const action = event.target.closest("[data-agent-action]")?.dataset.agentAction;
      if (action === "choose-device") modal.classList.add("show");
      const attachmentRemoveId = event.target.closest("[data-attachment-remove]")?.dataset.attachmentRemove;
      if (attachmentRemoveId) {
        state.fault.attachments = state.fault.attachments.filter((file) => file.id !== attachmentRemoveId);
        render();
        showToast("已移除附件");
      }
      if (action === "skip-optional") {
        if (state.fault.step === "optional") {
          addMsg("fault", "user", "跳过非必填，进入补充追问");
          startSupplementQuestions(true);
          render();
        }
      }
      if (action === "skip-supplement-question") {
        if (state.fault.step === "supplement") {
          addMsg("fault", "user", "跳过本题");
          skipSupplementQuestion();
          render();
        }
      }
      if (action === "finish-supplement-now") {
        if (state.fault.step === "supplement") {
          addMsg("fault", "user", "结束追问并生成故障说明");
          finishSupplementQuestions(false);
          render();
        }
      }
      if (action === "make-preview") validatePreview();
      if (action === "add-more" || action === "continue-fault") {
        addMsg("fault", "bot", "请继续输入要补充或修改的内容，我会融合到故障说明中。");
        state.fault.stage = "ready";
        render();
      }
      if (action === "make-ticket") {
        state.fault.ticketNo = "GD20260702001";
        state.fault.ticketStatus = "AI待提交";
        state.fault.stage = "done";
        addMsg("fault", "bot", "已生成“AI待提交”故障单，并使用正式故障编号。可前往故障上报页面执行详情、编辑、提交或删除。");
        render();
        showToast("已生成 AI待提交 故障单");
      }
      if (action === "copy-ask") showToast("问数结果已复制");
      if (action === "export-ask") showToast("已生成可下载Excel结果");
      if (action === "report-ask") {
        addMsg("ask", "bot", "报告摘要：近30天风险主要集中在驱动电机、BMS 通讯和液压系统，建议优先处理高风险告警和维修超期工单。");
        render();
      }
      const suggestedText = event.target.closest("[data-agent-suggestion]")?.dataset.agentSuggestion;
      if (suggestedText) {
        if (state.currentTab === "ask") {
          addMsg("ask", "user", escapeHtml(suggestedText));
          runAsk(suggestedText, /只看|继续|改成|换成/.test(suggestedText));
          return;
        }
        input.value = suggestedText;
        input.focus();
        showToast("已填入建议问题，可修改后发送");
      }
      const urgency = event.target.closest("[data-urgency]")?.dataset.urgency;
      if (urgency) {
        state.fault.urgency = urgency;
        state.fault.step = "phenomenon";
        addMsg("fault", "user", `紧急程度：${urgency}`);
        addMsg("fault", "bot", "已记录紧急程度。第3步：请描述故障现象。请用一句话描述设备出现了什么异常，例如：主轴异响、振动变大、温升异常、报警停机、漏油等。输入后，我会继续引导发生时间和可能故障位置（非必填）。");
        render();
      }
      const ask = event.target.closest("[data-ask]")?.dataset.ask;
      if (ask) {
        addMsg("ask", "user", escapeHtml(ask));
        runAsk(ask, /只看|继续|改成|换成/.test(ask));
      }
      const guide = event.target.closest("[data-guide]")?.dataset.guide;
      if (guide === "how") {
        addMsg("guide", "user", "当前页面怎么用？");
        addMsg("guide", "bot", `当前页面是“${escapeHtml(pageTitle)}”。先通过顶部筛选或主操作按钮定位对象，再查看列表、详情或状态卡片完成业务处理。`);
        render();
      }
      if (guide === "delete") {
        addMsg("guide", "user", "为什么无法删除设备？");
        addMsg("guide", "bot", "可能原因：设备有关联未关闭故障单或维修工单，或当前账号没有维护权限。建议先关闭关联业务，再由设备管理员处理。");
        render();
      }
      if (guide === "flow") {
        addMsg("guide", "user", "如何查看故障闭环？");
        state.guide.awaitingCrossConfirm = true;
        state.guide.flowTarget = "";
        render();
      }
      const flowTarget = event.target.closest("[data-flow-target]")?.dataset.flowTarget;
      if (flowTarget) {
        state.guide.awaitingCrossConfirm = false;
        state.guide.flowTarget = flowTarget;
        render();
      }
    });
    $("#opsAgentCloseDevice", root).addEventListener("click", () => modal.classList.remove("show"));
    deviceSearchButton?.addEventListener("click", filterDeviceRows);
    deviceSearchInput?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") filterDeviceRows();
    });
    modal.addEventListener("click", (event) => {
      if (event.target === modal) modal.classList.remove("show");
      const row = event.target.closest("[data-device-index]");
      if (!row) return;
      const device = devices[Number(row.dataset.deviceIndex)];
      state.fault.device = device;
      state.fault.step = "urgency";
      addMsg("fault", "user", `已选择设备：${escapeHtml(device.name)}`);
      addMsg("fault", "bot", `已选择 1 台设备，并自动带出所属车间和产线。<div class="ops-agent-card"><dl class="ops-agent-field-grid"><dt>设备编号</dt><dd>${device.code}</dd><dt>设备名称</dt><dd>${device.name}</dd><dt>所属车间</dt><dd>${device.workshop}</dd><dt>所属产线</dt><dd>${device.line}</dd></dl></div>下一步请先选择紧急程度。`);
      modal.classList.remove("show");
      render();
      showToast("设备已选择并自动带出车间/产线");
    });
  
    let snapTimer;
    let isPointerInsideFab = false;
    const snapMargin = 0;
    const snapSafeGap = 20;
    const snapFabToNearestEdge = () => {
      if (dragging || isPointerInsideFab || panel.classList.contains("is-open")) return;
      const rect = fab.getBoundingClientRect();
      const distanceToLeft = rect.left;
      const distanceToRight = window.innerWidth - rect.right;
      const nextLeft = distanceToLeft <= distanceToRight ? snapMargin : window.innerWidth - rect.width - snapMargin;
      const nextTop = Math.max(snapSafeGap, Math.min(window.innerHeight - rect.height - snapSafeGap, rect.top));
      fab.classList.add("is-snapping");
      fab.style.left = `${nextLeft}px`;
      fab.style.right = "auto";
      fab.style.top = `${nextTop}px`;
      fab.style.bottom = "auto";
      window.setTimeout(() => fab.classList.remove("is-snapping"), 260);
    };
    const scheduleFabSnap = () => {
      window.clearTimeout(snapTimer);
      snapTimer = window.setTimeout(() => {
        fab.classList.add("is-idle");
        snapFabToNearestEdge();
      }, 3000);
    };
    const resetIdle = () => {
      fab.classList.remove("is-idle");
      scheduleFabSnap();
    };
    ["mousemove", "mouseover", "mousedown", "touchstart"].forEach((eventName) => fab.addEventListener(eventName, resetIdle));
    fab.addEventListener("mouseenter", () => {
      isPointerInsideFab = true;
      window.clearTimeout(snapTimer);
      fab.classList.remove("is-idle");
    });
    fab.addEventListener("mouseleave", () => {
      isPointerInsideFab = false;
      resetIdle();
    });
    resetIdle();
    let dragging = false;
    let startX = 0;
    let startY = 0;
    let startLeft = 0;
    let startBottom = 0;
    fab.addEventListener("pointerdown", (event) => {
      dragging = true;
      window.clearTimeout(snapTimer);
      startX = event.clientX;
      startY = event.clientY;
      const rect = fab.getBoundingClientRect();
      startLeft = rect.left;
      startBottom = parseFloat(getComputedStyle(fab).bottom);
      fab.setPointerCapture(event.pointerId);
    });
    fab.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const dx = event.clientX - startX;
      const dy = startY - event.clientY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) fab.dataset.dragged = "true";
      const left = Math.max(snapSafeGap, Math.min(window.innerWidth - fab.offsetWidth - snapSafeGap, startLeft + dx));
      const bottom = Math.max(snapSafeGap, Math.min(window.innerHeight - fab.offsetHeight - snapSafeGap, startBottom + dy));
      fab.style.left = `${left}px`;
      fab.style.bottom = `${bottom}px`;
      fab.style.right = "auto";
      fab.style.top = "auto";
    });
    fab.addEventListener("pointerup", () => {
      dragging = false;
      scheduleFabSnap();
      window.setTimeout(() => {
        fab.dataset.dragged = "false";
      }, 60);
    });
  
    render();
  }

  window.initGlobalAgentWidget = initGlobalAgentWidget;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGlobalAgentWidget);
  } else {
    initGlobalAgentWidget();
  }
})();
