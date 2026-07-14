const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function setActiveNav() {
  const current = location.pathname.split("/").pop() || "index.html";
  const activeFile = current === "repair-execution.html"
    ? "maintenance-records.html"
    : ["equipment-add.html", "equipment-edit.html", "equipment-detail.html"].includes(current)
      ? "equipment-ledger.html"
      : current;
  $$(".nav-item").forEach((item) => {
    const href = item.getAttribute("href") || "";
    item.classList.toggle("active", href.endsWith(activeFile));
  });
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

function initSidebar() {
  const sidebar = $(".sidebar");
  $(".menu-btn")?.addEventListener("click", () => sidebar?.classList.toggle("open"));
  $$(".nav-item").forEach((item) => {
    item.addEventListener("click", () => sidebar?.classList.remove("open"));
  });
}

function initTabs() {
  $$("[data-tab-group]").forEach((group) => {
    const tabs = $$(".tab", group);
    const panels = $$(".tab-panel", group);
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.tab;
        tabs.forEach((t) => t.classList.toggle("active", t === tab));
        panels.forEach((panel) => {
          panel.hidden = panel.dataset.panel !== target;
        });
      });
    });
  });
}

function initSegments() {
  $$(".segmented").forEach((segmented) => {
    segmented.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      $$("button", segmented).forEach((item) => item.classList.toggle("active", item === button));
      const target = segmented.dataset.toast;
      if (target) showToast(`${button.textContent.trim()}筛选已应用`);
    });
  });
}

function initDrawer() {
  $$("[data-open-drawer]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const drawer = $(`#${trigger.dataset.openDrawer}`);
      window.__lastDrawerTrigger = trigger;
      drawer?.classList.add("open");
      drawer?.setAttribute("aria-hidden", "false");
      drawer?.focus();
    });
  });
  $$("[data-close-drawer]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const drawer = trigger.closest(".drawer");
      drawer?.classList.remove("open");
      drawer?.setAttribute("aria-hidden", "true");
      window.__lastDrawerTrigger?.focus?.();
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const drawer = $(".drawer.open");
    if (!drawer) return;
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    window.__lastDrawerTrigger?.focus?.();
  });
}

function validateForm(form) {
  let ok = true;
  $$("[required]", form).forEach((field) => {
    const wrapper = field.closest(".field");
    const empty = !String(field.value || "").trim();
    wrapper?.classList.toggle("error", empty);
    if (empty) ok = false;
  });
  return ok;
}

function initForms() {
  $$("[data-validate-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!validateForm(form)) {
        showToast("请先补齐必填信息");
        return;
      }
      const next = form.dataset.next;
      showToast(form.dataset.success || "已提交，系统正在处理");
      if (next) {
        setTimeout(() => {
          location.href = next;
        }, 650);
      }
    });
    $$("input, select, textarea", form).forEach((field) => {
      field.addEventListener("input", () => field.closest(".field")?.classList.remove("error"));
      field.addEventListener("change", () => field.closest(".field")?.classList.remove("error"));
    });
  });
}

function initFileUploads() {
  $$("[data-file-upload]").forEach((upload) => {
    if (upload.dataset.fileUploadReady === "true") return;
    const input = $("input[type='file']", upload);
    const status = $("[data-file-upload-status]", upload);
    if (!input || !status) return;
    upload.dataset.fileUploadReady = "true";
    const emptyText = status.textContent.trim() || "未选择附件";

    input.addEventListener("change", () => {
      const count = input.files?.length || 0;
      if (!count) {
        status.textContent = emptyText;
        return;
      }
      status.textContent = count === 1 ? input.files[0].name : `已选择 ${count} 个附件`;
    });
  });
}

function initActions() {
  $$("[data-toast]").forEach((item) => {
    item.addEventListener("click", () => showToast(item.dataset.toast));
  });
  $$("[data-toggle-status]").forEach((button) => {
    button.addEventListener("click", () => {
      const row = button.closest("tr") || button.closest(".card") || document;
      const status = $(".status", row);
      const next = button.dataset.toggleStatus;
      if (status && next) {
        status.className = `status ${button.dataset.statusClass || "info"}`;
        status.textContent = next;
      }
      showToast(button.dataset.toast || "状态已更新");
    });
  });
  $$("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const text = button.dataset.copy || "新能源装载机故障诊断摘要";
      try {
        await navigator.clipboard.writeText(text);
        showToast("内容已复制");
      } catch {
        showToast("已生成复制内容");
      }
    });
  });
}

const ACTION_PANEL_TEMPLATES = {
  "model-create": {
    title: "新增设备型号",
    status: "型号库维护",
    toast: "型号已保存，设备台账下拉将同步可选",
    body: `
      <form class="action-panel-form" data-action-panel-form>
        <div class="form-grid">
          <div class="field"><label>型号编码 *</label><input required value="ZL950EV"><span class="error-text">请输入型号编码</span></div>
          <div class="field"><label>设备类型 *</label><select required><option>5 吨电动装载机</option><option>4 吨电动装载机</option><option>3.6 吨电动装载机</option></select><span class="error-text">请选择设备类型</span></div>
          <div class="field"><label>BOM 模板 *</label><select required><option>电池 / 电驱 / 液压标准 BOM</option><option>轻载平台 BOM</option><option>高压系统 BOM</option></select><span class="error-text">请选择 BOM 模板</span></div>
          <div class="field"><label>参数模板 *</label><select required><option>高压系统 V3</option><option>整机运行 V2</option><option>热管理 V1</option></select><span class="error-text">请选择参数模板</span></div>
          <div class="field full"><label>维修资料模板</label><textarea placeholder="关联维修手册、历史案例和安全注意事项">维修手册目录、历史案例标签、知识图谱初始化规则</textarea></div>
        </div>
        <div class="summary-box vertical action-panel-summary"><div><strong>业务闭环</strong><br>保存后进入设备型号库，并作为设备台账“设备型号”下拉来源。</div><div><strong>变更留痕</strong><br>写入系统管理操作日志，提示受影响设备重新审核知识图谱。</div></div>
        <div class="drawer-actions"><button class="btn btn-primary" type="submit">保存型号</button><button class="btn btn-secondary" type="button" data-action-panel-close>取消</button></div>
      </form>`
  },
  "fault-detail": {
    title: "上报单详情",
    status: "待补充",
    toast: "已进入上报单补充流程",
    body: `<div class="action-detail-list"><div><strong>上报单</strong><span>FR-240627-018 / EL-2024-019 / Agent 预收集</span></div><div><strong>缺失字段</strong><span>发生时间、持续时长、现场附件</span></div><div><strong>下一步</strong><span>补齐字段后提交故障分析，生成候选原因和维修建议。</span></div></div><div class="drawer-actions"><a class="btn btn-primary" href="fault-report.html">补充上报单</a><button class="btn btn-secondary" type="button" data-action-panel-close>关闭</button></div>`
  },
  "import-exception": {
    title: "导入异常明细",
    status: "12 行异常",
    toast: "异常行已标记为待处理",
    body: `<div class="table-wrap"><table><thead><tr><th>行号</th><th>字段</th><th>问题</th><th>处理建议</th></tr></thead><tbody><tr><td>128</td><td>设备编号</td><td>台账不存在</td><td>先新增设备或修正编号</td></tr><tr><td>412</td><td>电机温度</td><td>超出额定范围</td><td>进入故障上报复核</td></tr></tbody></table></div><div class="drawer-actions"><a class="btn btn-primary" href="equipment-ledger.html">去设备台账补齐</a><button class="btn btn-secondary" type="button" data-action-submit>确认已处理</button></div>`
  },
  "knowledge-deposit": {
    title: "知识沉淀队列",
    status: "待入库",
    toast: "已提交知识沉淀审核",
    body: `<div class="action-detail-list"><div><strong>来源批次</strong><span>IMP-0624-018 / 维修记录 368 条</span></div><div><strong>沉淀对象</strong><span>历史案例、故障模式、维修建议、关联 BOM</span></div><div><strong>审核入口</strong><span>维修记录页的新故障模式审核会承接该队列。</span></div></div><div class="drawer-actions"><a class="btn btn-primary" href="maintenance-records.html">进入审核</a><button class="btn btn-secondary" type="button" data-action-submit>加入队列</button></div>`
  },
  "maintenance-detail": {
    title: "维修记录详情",
    status: "待审核",
    toast: "维修记录已标记为已查看",
    body: `<div class="action-detail-list"><div><strong>记录编号</strong><span>MR-240625-011 / EL-2024-019</span></div><div><strong>实际原因</strong><span>冷却液流量不足；关联驱动电机过温故障。</span></div><div><strong>知识沉淀</strong><span>待专家审核后写入历史案例库。</span></div></div><div class="drawer-actions"><a class="btn btn-primary" href="repair-execution.html">查看执行记录</a><button class="btn btn-secondary" type="button" data-action-submit>确认已阅</button></div>`
  },
  "case-generate": {
    title: "历史案例生成",
    status: "已入库",
    toast: "历史案例草稿已生成",
    body: `<div class="action-detail-list"><div><strong>案例来源</strong><span>MR-240624-021 / 液压压力波动</span></div><div><strong>案例结构</strong><span>故障现象、实际原因、排查步骤、处理方法、关联备件。</span></div><div><strong>后续流转</strong><span>提交到智能配置知识库，等待索引重建。</span></div></div><div class="drawer-actions"><a class="btn btn-primary" href="intelligent-config.html">查看知识库</a><button class="btn btn-secondary" type="button" data-action-submit>生成案例</button></div>`
  },
  "draft-order": {
    title: "生成维修建议",
    status: "待确认",
    toast: "维修建议已创建",
    body: `<div class="action-detail-list"><div><strong>来源诊断</strong><span>驱动电机过温限扭 / 高风险</span></div><div><strong>建议派工</strong><span>电驱维修组；预计 3.5 工时；优先检查冷却回路。</span></div><div><strong>闭环动作</strong><span>确认后写入工单列表，状态为“草稿”。</span></div></div><div class="drawer-actions"><button class="btn btn-primary" type="button" data-action-submit>确认生成</button><a class="btn btn-secondary" href="fault-report.html">回到故障上报</a></div>`
  },
  "rebuild-index": {
    title: "重建知识库索引",
    status: "任务配置",
    toast: "索引重建任务已加入队列",
    body: `<div class="action-detail-list"><div><strong>重建范围</strong><span>BOM、维修手册、历史案例、新故障模式。</span></div><div><strong>影响模块</strong><span>故障分析依据来源、Agent 上报建议、设备详情知识图谱。</span></div><div><strong>预计耗时</strong><span>约 12 分钟；完成后刷新知识库数据集状态。</span></div></div><div class="drawer-actions"><button class="btn btn-primary" type="button" data-action-submit>发起重建</button><button class="btn btn-secondary" type="button" data-action-panel-close>取消</button></div>`
  },
  "password-reset": {
    title: "重置用户密码",
    status: "二次确认",
    toast: "密码重置链接已发送",
    body: `<div class="action-detail-list"><div><strong>用户</strong><span>张师傅 / 维修人员</span></div><div><strong>发送方式</strong><span>手机号短信 + 系统站内通知。</span></div><div><strong>审计记录</strong><span>操作会写入系统管理操作日志。</span></div></div><div class="drawer-actions"><button class="btn btn-primary" type="button" data-action-submit>确认发送</button><button class="btn btn-secondary" type="button" data-action-panel-close>取消</button></div>`
  },
  "agent-attach": {
    title: "上传 Agent 附件",
    status: "预收集",
    toast: "附件已加入上报预收集",
    body: `<label class="file-upload" data-file-upload><input class="file-upload-input" type="file" multiple><span class="file-upload-icon" aria-hidden="true">附</span><span class="file-upload-copy"><strong>上传仪表照片或日志</strong><span data-file-upload-status>未选择附件</span></span><span class="file-upload-action">选择文件</span></label><div class="drawer-actions"><button class="btn btn-primary" type="button" data-action-submit>加入预收集</button><button class="btn btn-secondary" type="button" data-action-panel-close>取消</button></div>`
  }
};

function ensureActionPanel() {
  let drawer = $("#actionPanelDrawer");
  if (drawer) return drawer;
  drawer = document.createElement("aside");
  drawer.className = "drawer drawer-wide action-panel-drawer";
  drawer.id = "actionPanelDrawer";
  drawer.setAttribute("aria-hidden", "true");
  drawer.setAttribute("tabindex", "-1");
  drawer.innerHTML = `
    <div class="drawer-head"><div><strong data-action-panel-title>业务操作</strong><div class="muted small" data-action-panel-status>待处理</div></div><button class="icon-btn" type="button" data-action-panel-close aria-label="关闭业务操作">×</button></div>
    <div class="drawer-body" data-action-panel-body></div>`;
  document.body.appendChild(drawer);
  drawer.addEventListener("click", (event) => {
    if (event.target.closest("[data-action-panel-close]")) closeActionPanel();
    const submit = event.target.closest("[data-action-submit]");
    if (submit) {
      showToast(drawer.dataset.submitToast || "操作已完成");
      closeActionPanel();
    }
  });
  drawer.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-action-panel-form]");
    if (!form) return;
    event.preventDefault();
    if (!validateForm(form)) {
      showToast("请先补齐必填信息");
      return;
    }
    showToast(drawer.dataset.submitToast || "操作已完成");
    closeActionPanel();
  });
  return drawer;
}

function closeActionPanel() {
  const drawer = $("#actionPanelDrawer");
  drawer?.classList.remove("open");
  drawer?.setAttribute("aria-hidden", "true");
  window.__lastActionPanelTrigger?.focus?.();
}

function openActionPanel(key, trigger) {
  const template = ACTION_PANEL_TEMPLATES[key];
  if (!template) return;
  const drawer = ensureActionPanel();
  $("[data-action-panel-title]", drawer).textContent = template.title;
  $("[data-action-panel-status]", drawer).textContent = template.status;
  $("[data-action-panel-body]", drawer).innerHTML = template.body;
  drawer.dataset.submitToast = template.toast || "操作已完成";
  window.__lastActionPanelTrigger = trigger;
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  drawer.focus();
  initFileUploads();
}

function initActionPanels() {
  $$("[data-action-panel]").forEach((trigger) => {
    trigger.addEventListener("click", () => openActionPanel(trigger.dataset.actionPanel, trigger));
  });
}

function initBiDashboard() {
  const filter = $("[data-bi-filter]");
  if (!filter) return;

  const rows = $$("tbody tr[data-risk]");
  const warningButton = $("[data-bi-warning]");
  const stateCards = $$("[data-state-card]");
  const stateButtons = $$("[data-state-preview]");
  const resultStatus = $("[data-bi-result]");

  const updateResultStatus = (filtered) => {
    const visibleRows = rows.filter((row) => !row.hidden);
    const warningRows = visibleRows.filter((row) => row.dataset.risk !== "ok");
    if (resultStatus) {
      resultStatus.textContent = filtered
        ? `当前显示 ${visibleRows.length} 台预警设备，建议优先进入故障分析生成工单。`
        : `当前显示 ${visibleRows.length} 台重点设备，其中 ${warningRows.length} 台需要预警处置。`;
      resultStatus.classList.toggle("is-filtered", filtered);
    }
  };

  $("[data-bi-query]")?.addEventListener("click", () => {
    const range = $("#range")?.value || "当前周期";
    showToast(`${range}驾驶舱数据已更新`);
  });

  $("[data-bi-reset]")?.addEventListener("click", () => {
    $$("select", filter).forEach((select) => {
      select.selectedIndex = 0;
    });
    rows.forEach((row) => {
      row.hidden = false;
    });
    if (warningButton) {
      warningButton.setAttribute("aria-pressed", "false");
      warningButton.textContent = "只看预警";
    }
    updateResultStatus(false);
    showToast("筛选条件已重置");
  });

  warningButton?.addEventListener("click", () => {
    const pressed = warningButton.getAttribute("aria-pressed") === "true";
    const next = !pressed;
    warningButton.setAttribute("aria-pressed", String(next));
    warningButton.textContent = next ? "显示全部" : "只看预警";
    rows.forEach((row) => {
      row.hidden = next && row.dataset.risk === "ok";
    });
    updateResultStatus(next);
    showToast(next ? "已筛出中高风险设备" : "已恢复全部设备");
  });

  $("[data-bi-export]")?.addEventListener("click", () => {
    showToast("驾驶舱明细已加入导出队列");
  });

  $$("[data-bi-detail]").forEach((button) => {
    button.addEventListener("click", () => {
      const subject = button.dataset.biDetail || "设备健康";
      const drawer = $("#biInsightDrawer");
      const title = $("[data-bi-drawer-title]", drawer);
      const action = $("[data-bi-drawer-action]", drawer);
      const risk = $("[data-bi-drawer-risk]", drawer);
      if (title) title.textContent = subject;
      if (action) action.textContent = button.textContent.includes("生成工单") ? "建议派工" : "持续跟踪";
      if (risk) {
        risk.textContent = subject.includes("分布")
          ? "待派单占比上升，需关注高风险设备工单闭环"
          : "驱动电机温升、BMS 通讯丢包";
      }
      window.__lastDrawerTrigger = button;
      drawer?.classList.add("open");
      drawer?.setAttribute("aria-hidden", "false");
      drawer?.focus();
      drawer?.querySelector(".mini-trend")?.classList.remove("motion-replay");
      requestAnimationFrame(() => drawer?.querySelector(".mini-trend")?.classList.add("motion-replay"));
      showToast(`${subject}分析已打开`);
    });
  });

  stateButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.dataset.statePreview;
      stateCards.forEach((card) => {
        const nextHidden = card.dataset.stateCard !== target ? true : !card.hidden;
        card.hidden = nextHidden;
        card.classList.toggle("motion-enter", !nextHidden);
        if (card.dataset.stateCard === target) {
          button.setAttribute("aria-expanded", String(!nextHidden));
        }
      });
      stateButtons.forEach((stateButton) => {
        if (stateButton !== button) stateButton.setAttribute("aria-expanded", "false");
      });
      showToast(target === "loading" ? "正在同步驾驶舱数据" : "已显示接口状态");
    });
  });
}

function initEquipmentLedgerFilters() {
  const filter = $("[data-equipment-ledger-filter]");
  if (!filter) return;

  const orgMap = {
    "华东总装厂": {
      "总装一车间": ["A1 产线", "A2 产线"],
      "电驱车间": ["E1 产线", "E2 产线"]
    },
    "西南矿区保障中心": {
      "露天矿维修车间": ["M1 保障线", "M2 保障线"],
      "电池检修车间": ["B1 检修线", "B2 检修线"]
    }
  };

  const factorySelect = $("[data-ledger-factory]", filter);
  const workshopSelect = $("[data-ledger-workshop]", filter);
  const lineSelect = $("[data-ledger-line]", filter);
  const rows = $$("[data-ledger-row]");
  const result = $("[data-ledger-result]");
  const pagination = $("[data-ledger-pagination]");
  const pageSize = 10;
  let filteredRows = [...rows];
  let currentPage = 1;

  rows.forEach((row) => {
    const deviceId = row.cells?.[1]?.textContent.trim();
    const health = window.HealthScoreService?.getEquipment(deviceId);
    if (!health) return;
    row.dataset.score = String(health.score);
    const scorePill = $(".score-pill", row);
    if (scorePill) {
      scorePill.textContent = String(health.score);
      scorePill.className = `score-pill ${health.riskClass === "normal" || health.riskClass === "low" ? "ok" : health.riskClass === "medium" ? "warn" : "bad"}`;
    }
    const detailLink = $("a[href^=\"equipment-detail.html\"]", row);
    if (detailLink) detailLink.href = `equipment-detail.html?device=${encodeURIComponent(health.id)}`;
  });

  const fillOptions = (select, placeholder, values) => {
    if (!select) return;
    select.innerHTML = `<option value="">${placeholder}</option>${values.map((value) => `<option value="${value}">${value}</option>`).join("")}`;
    select.disabled = values.length === 0;
  };

  const updateWorkshops = () => {
    const factory = factorySelect?.value || "";
    fillOptions(workshopSelect, "全部车间", factory ? Object.keys(orgMap[factory] || {}) : []);
    fillOptions(lineSelect, "全部产线", []);
  };

  const updateLines = () => {
    const factory = factorySelect?.value || "";
    const workshop = workshopSelect?.value || "";
    fillOptions(lineSelect, "全部产线", factory && workshop ? orgMap[factory]?.[workshop] || [] : []);
  };

  const getFilters = () => ({
    factory: factorySelect?.value || "",
    workshop: workshopSelect?.value || "",
    line: lineSelect?.value || "",
    keyword: ($("[data-ledger-keyword]", filter)?.value || "").trim().toLowerCase(),
    name: ($("[data-ledger-name]", filter)?.value || "").trim().toLowerCase(),
    score: $("[data-ledger-score]", filter)?.value || ""
  });

  const scoreMatches = (score, rule) => {
    if (!rule) return true;
    if (rule === "normal") return score === 100;
    if (rule === "low-risk") return score >= 80 && score <= 99;
    if (rule === "medium-risk") return score >= 60 && score <= 79;
    if (rule === "high-risk") return score >= 40 && score <= 59;
    if (rule === "severe-risk") return score >= 0 && score <= 39;
    if (rule === "lt70") return score < 70;
    if (rule === "70-85") return score >= 70 && score <= 85;
    if (rule === "gt85") return score > 85;
    return true;
  };

  const renderRows = () => {
    const total = filteredRows.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    currentPage = Math.min(Math.max(currentPage, 1), totalPages);
    const start = total === 0 ? 0 : (currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, total);
    const visibleRows = new Set(filteredRows.slice(start, end));

    rows.forEach((row) => {
      row.hidden = !visibleRows.has(row);
      const indexCell = $("[data-ledger-index]", row);
      if (indexCell) indexCell.textContent = String(rows.indexOf(row) + 1);
    });

    if (result) {
      const rangeText = total === 0 ? "暂无匹配设备" : `当前显示第 ${start + 1}-${end} 台`;
      const countText = total === rows.length ? `设备总数 ${rows.length} 台` : `设备总数 ${rows.length} 台；筛选结果 ${total} 台`;
      result.textContent = `${countText}；${rangeText}。`;
      result.classList.toggle("is-filtered", total !== rows.length);
    }

    if (!pagination) return;
    pagination.innerHTML = "";
    const createButton = (label, page, disabled = false, active = false) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.disabled = disabled;
      button.className = active ? "active" : "";
      button.addEventListener("click", () => {
        currentPage = page;
        renderRows();
      });
      return button;
    };
    pagination.append(createButton("上一页", currentPage - 1, currentPage === 1));
    for (let page = 1; page <= totalPages; page += 1) {
      pagination.append(createButton(String(page), page, false, page === currentPage));
    }
    pagination.append(createButton("下一页", currentPage + 1, currentPage === totalPages));
  };

  const queryRows = () => {
    const filters = getFilters();
    filteredRows = rows.filter((row) => {
      const score = Number(row.dataset.score || 0);
      return (!filters.factory || row.dataset.factory === filters.factory)
        && (!filters.workshop || row.dataset.workshop === filters.workshop)
        && (!filters.line || row.dataset.line === filters.line)
        && (!filters.keyword || (row.dataset.keywords || "").toLowerCase().includes(filters.keyword))
        && (!filters.name || (row.dataset.name || "").toLowerCase().includes(filters.name))
        && scoreMatches(score, filters.score);
    });
    currentPage = 1;
    renderRows();
    showToast(`已查询到 ${filteredRows.length} 台设备`);
  };

  const resetRows = () => {
    $$("input, select", filter).forEach((field) => {
      if (field.tagName === "SELECT") field.selectedIndex = 0;
      else field.value = "";
    });
    fillOptions(workshopSelect, "全部车间", []);
    fillOptions(lineSelect, "全部产线", []);
    filteredRows = [...rows];
    currentPage = 1;
    renderRows();
    showToast("筛选条件已重置，设备列表已恢复");
  };

  factorySelect?.addEventListener("change", updateWorkshops);
  workshopSelect?.addEventListener("change", updateLines);
  $("[data-ledger-query]", filter)?.addEventListener("click", queryRows);
  $("[data-ledger-reset]", filter)?.addEventListener("click", resetRows);
  renderRows();
}

function initEquipmentAddPage() {
  const form = $("[data-equipment-add-form]");
  if (!form) return;

  const orgMap = {
    "华东总装厂": {
      "总装一车间": ["A1 产线", "A2 产线"],
      "电驱车间": ["E1 产线", "E2 产线"]
    },
    "西南矿区保障中心": {
      "露天矿维修车间": ["M1 保障线", "M2 保障线"],
      "电池检修车间": ["B1 检修线", "B2 检修线"]
    }
  };

  const fillOptions = (select, placeholder, values) => {
    if (!select) return;
    select.innerHTML = `<option value="">${placeholder}</option>${values.map((value) => `<option>${value}</option>`).join("")}`;
    select.disabled = values.length === 0;
  };

  const factorySelect = $("[data-add-factory]", form);
  const workshopSelect = $("[data-add-workshop]", form);
  const lineSelect = $("[data-add-line]", form);
  factorySelect?.addEventListener("change", () => {
    const factory = factorySelect.value;
    fillOptions(workshopSelect, "请选择车间", factory ? Object.keys(orgMap[factory] || {}) : []);
    fillOptions(lineSelect, "请选择产线", []);
  });
  workshopSelect?.addEventListener("change", () => {
    const factory = factorySelect?.value || "";
    const workshop = workshopSelect.value;
    fillOptions(lineSelect, "请选择产线", factory && workshop ? orgMap[factory]?.[workshop] || [] : []);
  });
  const initialWorkshop = workshopSelect?.dataset.initialValue || "";
  const initialLine = lineSelect?.dataset.initialValue || "";
  if (factorySelect?.value) {
    fillOptions(workshopSelect, "请选择车间", Object.keys(orgMap[factorySelect.value] || {}));
    if (initialWorkshop && workshopSelect) workshopSelect.value = initialWorkshop;
    fillOptions(lineSelect, "请选择产线", initialWorkshop ? orgMap[factorySelect.value]?.[initialWorkshop] || [] : []);
    if (initialLine && lineSelect) lineSelect.value = initialLine;
  }

  const ownerInputs = $$("[data-owner-group] input", form);
  ownerInputs.forEach((input) => {
    input.addEventListener("change", () => {
      const hasOwner = ownerInputs.some((item) => item.checked);
      ownerInputs.forEach((item) => {
        item.required = !hasOwner && item === ownerInputs[0];
      });
      $("[data-owner-group]", form)?.closest(".field")?.classList.remove("error");
    });
  });

  $$("input, select, textarea", form).forEach((field) => {
    field.addEventListener("input", () => field.closest(".field")?.classList.remove("error"));
    field.addEventListener("change", () => field.closest(".field")?.classList.remove("error"));
  });

  const rootLabel = $("[data-bom-root-label]", form);
  const getBomRootName = () => $("[data-equipment-name-source]", form)?.value.trim() || "设备名称";
  $("[data-equipment-name-source]", form)?.addEventListener("input", (event) => {
    const name = event.target.value.trim() || "设备名称";
    if (rootLabel) rootLabel.textContent = name;
    refreshBomParentOptions();
  });

  const bomTable = $("[data-bom-table]", form);
  let bomSequence = $$("[data-bom-table] tr", form).length;
  const getBomRows = () => $$("[data-bom-table] tr", form);
  const getBomRowName = (row) => $("[data-bom-name]", row)?.value.trim() || $("[data-bom-code]", row)?.value.trim() || "未命名节点";
  const getBomRowDepth = (row) => Number($("[data-bom-depth]", row)?.value || 2);
  function refreshBomParentOptions() {
    const rows = getBomRows();
    rows.forEach((row) => {
      const parentSelect = $("[data-bom-parent]", row);
      const depthSelect = $("[data-bom-depth]", row);
      if (!parentSelect || !depthSelect) return;
      const currentValue = parentSelect.value || row.dataset.parentId || "bom-root";
      let depth = Number(depthSelect.value || 2);
      if (depth < 2) {
        depth = 2;
        depthSelect.value = "2";
      }
      const parentCandidates = depth <= 2
        ? [{ id: "bom-root", name: getBomRootName() }]
        : rows
          .filter((candidate) => candidate !== row && getBomRowDepth(candidate) === depth - 1)
          .map((candidate) => ({ id: candidate.dataset.bomId, name: getBomRowName(candidate) }));
      if (!parentCandidates.length) {
        depthSelect.value = "2";
        depth = 2;
      }
      const options = parentCandidates.length ? parentCandidates : [{ id: "bom-root", name: getBomRootName() }];
      parentSelect.innerHTML = options.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("");
      parentSelect.value = options.some((item) => item.id === currentValue) ? currentValue : options[0].id;
      row.dataset.parentId = parentSelect.value;
    });
  }
  refreshBomParentOptions();
  $("[data-add-bom-row]", form)?.addEventListener("click", () => {
    bomSequence += 1;
    const bomId = `bom-${String(bomSequence).padStart(3, "0")}`;
    const name = `新增分支 ${bomSequence}`;
    const row = document.createElement("tr");
    row.dataset.bomId = bomId;
    row.dataset.parentId = "bom-root";
    row.innerHTML = `<td><select data-bom-depth><option value="2" selected>2级</option><option value="3">3级</option><option value="4">4级</option></select></td><td><select data-bom-parent></select></td><td><input data-bom-code value="${bomId.toUpperCase()}"></td><td><input data-bom-name value="${name}"></td><td><input placeholder="填写节点描述"></td><td><input value="件"></td><td><input type="number" min="1" value="1"></td><td><button class="link-btn danger-link" type="button" data-delete-bom-row>删除</button></td>`;
    bomTable?.appendChild(row);
    refreshBomParentOptions();
    showToast(`${name}已添加到 BOM 列表`);
  });
  bomTable?.addEventListener("input", (event) => {
    if (event.target.closest("[data-bom-name], [data-bom-code]")) refreshBomParentOptions();
  });
  bomTable?.addEventListener("change", (event) => {
    const row = event.target.closest("tr");
    if (!row) return;
    if (event.target.closest("[data-bom-depth]")) {
      row.dataset.parentId = "bom-root";
      refreshBomParentOptions();
    }
    if (event.target.closest("[data-bom-parent]")) {
      row.dataset.parentId = event.target.value;
    }
  });
  bomTable?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-delete-bom-row]");
    if (!button) return;
    const row = button.closest("tr");
    if (!row) return;
    const removeIds = new Set([row.dataset.bomId]);
    let changed = true;
    while (changed) {
      changed = false;
      getBomRows().forEach((candidate) => {
        if (removeIds.has(candidate.dataset.parentId) && !removeIds.has(candidate.dataset.bomId)) {
          removeIds.add(candidate.dataset.bomId);
          changed = true;
        }
      });
    }
    const removedName = getBomRowName(row);
    getBomRows().forEach((candidate) => {
      if (removeIds.has(candidate.dataset.bomId)) candidate.remove();
    });
    refreshBomParentOptions();
    showToast(`${removedName}及其下级节点已删除`);
  });

  const paramTable = $("[data-param-table]", form);
  const refreshParamIndexes = () => {
    $$("[data-param-index]", form).forEach((cell, index) => {
      cell.textContent = String(index + 1);
    });
  };
  $("[data-add-param-row]", form)?.addEventListener("click", () => {
    const row = document.createElement("tr");
    row.innerHTML = `<td data-param-index></td><td><input placeholder="参数名"></td><td><input placeholder="额定值"></td><td><input placeholder="上限"></td><td><input placeholder="下限"></td><td><input placeholder="单位"></td><td><input placeholder="说明"></td><td><button class="link-btn" type="button" data-delete-param>删除</button></td>`;
    paramTable?.appendChild(row);
    refreshParamIndexes();
    showToast("已新增额定参数行");
  });
  paramTable?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-delete-param]");
    if (!button) return;
    const rows = $$("tr", paramTable);
    if (rows.length <= 1) {
      showToast("至少保留 1 条额定参数");
      return;
    }
    button.closest("tr")?.remove();
    refreshParamIndexes();
    showToast("参数行已删除");
  });

  const docTable = $("[data-doc-table]", form);
  const docUploadModal = $("[data-doc-upload-modal]", form);
  const docUploadInput = $("[data-doc-upload]", form);
  const docUploadStatus = $("[data-doc-upload-status]", form);
  const docTypeSelect = $("[data-doc-type]", form);
  const refreshDocIndexes = () => {
    $$("[data-doc-index]", form).forEach((cell, index) => {
      cell.textContent = String(index + 1);
    });
  };
  const closeDocUploadModal = () => {
    docUploadModal?.classList.remove("open");
    docUploadModal?.setAttribute("aria-hidden", "true");
  };
  const openDocUploadModal = () => {
    if (docUploadStatus) docUploadStatus.textContent = "未选择文件";
    if (docUploadInput) docUploadInput.value = "";
    docUploadModal?.classList.add("open");
    docUploadModal?.setAttribute("aria-hidden", "false");
    docTypeSelect?.focus();
  };
  const addDocFiles = (files, type) => {
    const now = new Date();
    const time = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    files.forEach((file) => {
      const ext = (file.name.split(".").pop() || "").toUpperCase();
      const size = file.size >= 1048576 ? `${(file.size / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(file.size / 1024))} KB`;
      const row = document.createElement("tr");
      row.innerHTML = `<td data-doc-index>${docTable.children.length + 1}</td><td>${type}</td><td>${escapeHtml(file.name)}</td><td>${size}</td><td>${time}</td><td>${ext === "DOCX" || ext === "DOC" ? "Word" : ext}</td><td><button class="link-btn danger-link" type="button" data-delete-doc>删除</button></td>`;
      docTable?.appendChild(row);
    });
    refreshDocIndexes();
    showToast(`已添加 ${files.length} 个知识资料文件`);
  };
  $("[data-open-doc-upload]", form)?.addEventListener("click", openDocUploadModal);
  $$("[data-close-doc-upload]", form).forEach((button) => {
    button.addEventListener("click", closeDocUploadModal);
  });
  docUploadModal?.addEventListener("click", (event) => {
    if (event.target === docUploadModal) closeDocUploadModal();
  });
  docUploadInput?.addEventListener("change", (event) => {
    const files = Array.from(event.target.files || []);
    if (docUploadStatus) {
      docUploadStatus.textContent = files.length === 0 ? "未选择文件" : files.length === 1 ? files[0].name : `已选择 ${files.length} 个文件`;
    }
  });
  $("[data-confirm-doc-upload]", form)?.addEventListener("click", () => {
    const files = Array.from(docUploadInput?.files || []);
    if (!files.length) {
      showToast("请先选择要上传的资料文件");
      return;
    }
    addDocFiles(files, docTypeSelect?.value || "维修手册");
    if (docUploadInput) docUploadInput.value = "";
    if (docUploadStatus) docUploadStatus.textContent = "未选择文件";
    closeDocUploadModal();
  });
  docTable?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-delete-doc]");
    if (!button) return;
    button.closest("tr")?.remove();
    refreshDocIndexes();
    showToast("知识资料已删除");
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const hasOwner = ownerInputs.some((item) => item.checked);
    const ownerField = $("[data-owner-group]", form)?.closest(".field");
    ownerField?.classList.toggle("error", !hasOwner);
    if (!validateForm(form) || !form.checkValidity() || !hasOwner) {
      showToast("请先补齐必填信息");
      return;
    }
    const isEditMode = form.dataset.equipmentMode === "edit";
    showToast(isEditMode ? "设备信息已保存" : "设备新增草稿已保存");
    window.setTimeout(() => {
      window.location.href = "equipment-ledger.html";
    }, 650);
  });
}

function initEquipmentDetailPage() {
  const bomHost = $("[data-detail-bom]");
  if (!bomHost) return;

  const title = $("[data-bom-detail-title]", bomHost);
  const card = $("[data-bom-detail-card]", bomHost);
  const nodes = {
    root: ["1级", "—", "EL-2024-019", "一号电动装载机", "ZL956EV 整机设备根节点", "台", "1"],
    power: ["2级", "一号电动装载机", "BOM-001", "动力系统", "电池、电机与控制器总成", "套", "1"],
    motor: ["3级", "动力系统", "BOM-001-01", "驱动电机", "额定功率 162kW，水冷散热", "台", "1"],
    bms: ["3级", "动力系统", "BOM-001-02", "BMS", "电池管理系统，负责单体监测与均衡", "套", "1"],
    hydraulic: ["2级", "一号电动装载机", "BOM-002", "液压系统", "液压泵、阀组与油路", "套", "1"],
    pump: ["3级", "液压系统", "BOM-002-01", "液压泵", "额定压力 18MPa，异常波动需复核", "台", "1"]
  };
  const labels = ["层级", "上级节点", "节点编码", "节点名称", "描述", "单位", "BOM 用量"];

  const render = (key) => {
    const values = nodes[key] || nodes.root;
    if (title) title.textContent = values[3];
    if (card) {
      card.innerHTML = values.map((value, index) => `<div><span>${labels[index]}</span><strong>${value}</strong></div>`).join("");
    }
  };

  $$("[data-bom-detail]", bomHost).forEach((button) => {
    button.addEventListener("click", () => {
      $$("[data-bom-detail]", bomHost).forEach((item) => item.classList.toggle("active", item === button));
      render(button.dataset.bomDetail);
    });
  });
}

function initAgentDrawer() {
  const drawer = $("#agentDrawer");
  const open = $("#openAi");
  const close = $("#closeAi");
  const scrim = $("#agentScrim");
  const input = $("#agentInput");
  const send = $("#agentSend");
  const contextLabel = $("[data-agent-context]");
  const summary = $("[data-agent-summary]");
  const reply = $("[data-agent-reply]");
  if (!drawer || !open) return;

  const pageTitle = $(".page-title")?.textContent?.trim() || document.title.split(" - ")[0] || "当前页面";
  const contextMap = {
    "设备台账": "当前页面上下文：设备列表；进入设备详情后会带入当前设备、BOM、额定参数和知识文档状态。",
    "故障分析": "当前页面上下文：诊断结果；可带入故障单、RAGFlow 引用来源、置信度和安全提示。",
    "维修记录": "当前页面上下文：工单列表；可带入当前工单、设备、诊断建议和维修状态。",
    "维修执行": "当前页面上下文：维修执行子页面；可带入工单、设备、实际原因和验收状态。",
    "维修记录": "当前页面上下文：维修记录；可带入维修结论、沉淀状态和关联案例。",
    "数据导入": "当前页面上下文：导入批次；可带入导入类型、导入日志和失败原因。",
    "Agent 上报": "当前页面上下文：正式 Agent 上报；本页可以确认摘要并提交故障单。"
  };
  const contextText = contextMap[pageTitle] || `当前页面上下文：${pageTitle}；未绑定具体业务对象，仅识别用户、角色和授权设备范围。`;
  if (contextLabel) contextLabel.textContent = contextText;
  if (summary) summary.textContent = pageTitle;

  const setOpen = (next) => {
    drawer.classList.toggle("open", next);
    scrim?.classList.toggle("open", next);
    drawer.setAttribute("aria-hidden", String(!next));
    open.setAttribute("aria-expanded", String(next));
    if (next) {
      window.__lastAgentTrigger = open;
      drawer.focus();
    } else {
      window.__lastAgentTrigger?.focus?.();
    }
  };

  open.addEventListener("click", () => setOpen(true));
  close?.addEventListener("click", () => setOpen(false));
  scrim?.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.classList.contains("open")) setOpen(false);
  });

  $$("[data-agent-intent]").forEach((button) => {
    button.addEventListener("click", () => {
      $$("[data-agent-intent]").forEach((item) => item.classList.toggle("active", item === button));
      const intent = button.dataset.agentIntent;
      if (reply) {
        reply.textContent = intent === "故障上报"
          ? "我会先预收集设备、现象、发生时间和工况；确认后请进入完整上报页正式提交。"
          : `已切换为“${intent}”意图，将优先读取${pageTitle}上下文并隐藏未授权设备详情。`;
      }
      showToast(`Agent 已切换为${intent}`);
    });
  });

  send?.addEventListener("click", () => {
    const text = input?.value?.trim();
    if (!text) {
      showToast("请先输入咨询或故障描述");
      return;
    }
    if (/EL-999|未授权|其他设备/.test(text)) {
      if (reply) reply.textContent = "当前账号无权查看或上报该设备故障，请联系系统管理员确认设备台账中的设备负责人配置。";
      showToast("已按权限边界拒绝");
      return;
    }
    if (reply) reply.textContent = "已预收集描述信息，还需在 Agent 上报页确认结构化摘要后正式提交。";
    input.value = "";
    showToast("Agent 已更新预收集摘要");
  });

  $("[data-agent-attach]")?.addEventListener("click", () => showToast("已准备上传现场照片或日志附件"));
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function initUserEntry() {
  const chip = $(".user-chip");
  if (!chip || $("[data-global-user-menu]")) return;
  const label = chip.querySelector("span:last-child")?.textContent?.trim() || "当前用户 · 平台用户";
  const [name, role = "平台用户"] = label.split(" · ");
  const isAdmin = /系统管理员/.test(label);
  chip.setAttribute("data-user-menu-trigger", "true");
  chip.setAttribute("role", "button");
  chip.setAttribute("tabindex", "0");
  chip.setAttribute("aria-haspopup", "menu");
  chip.setAttribute("aria-expanded", "false");
  chip.insertAdjacentHTML("beforeend", '<span class="user-menu-chevron" aria-hidden="true">⌄</span>');
  const menu = document.createElement("div");
  menu.className = "global-user-menu";
  menu.dataset.globalUserMenu = "true";
  menu.hidden = true;
  menu.innerHTML = `<div class="global-menu-user"><span class="avatar">${escapeHtml(name.slice(0, 1))}</span><div><strong>${escapeHtml(name)}</strong><span>${escapeHtml(role)} · liming</span></div></div><div class="global-menu-divider"></div><button class="global-menu-item" data-user-action="profile">个人资料</button><button class="global-menu-item" data-user-action="security">安全设置 / 修改密码</button>${isAdmin ? '<button class="global-menu-item" data-user-action="management">进入用户管理</button>' : ""}<div class="global-menu-divider"></div><button class="global-menu-item danger" data-user-action="logout">退出登录</button>`;
  document.body.appendChild(menu);
  const modal = document.createElement("div");
  modal.className = "user-entry-modal";
  modal.hidden = true;
  modal.innerHTML = `<div class="user-entry-backdrop" data-user-close></div><section class="user-entry-dialog" role="dialog" aria-modal="true"><button class="user-entry-close" type="button" data-user-close aria-label="关闭">×</button><div data-user-modal-content></div></section>`;
  document.body.appendChild(modal);
  const closeMenu = () => { menu.hidden = true; chip.setAttribute("aria-expanded", "false"); };
  const openModal = (title, content) => { closeMenu(); modal.querySelector("[data-user-modal-content]").innerHTML = `<h2>${title}</h2>${content}`; modal.hidden = false; };
  const closeModal = () => { modal.hidden = true; };
  const openMenu = () => { menu.hidden = !menu.hidden; chip.setAttribute("aria-expanded", String(!menu.hidden)); };
  chip.addEventListener("click", openMenu);
  chip.addEventListener("keydown", event => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); openMenu(); } });
  document.addEventListener("click", event => { if (!menu.contains(event.target) && !chip.contains(event.target)) closeMenu(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape") { closeMenu(); closeModal(); } });
  menu.addEventListener("click", event => {
    const action = event.target.closest("[data-user-action]")?.dataset.userAction;
    if (action === "profile") openModal("个人资料", `<div class="user-entry-profile"><span class="avatar large">${escapeHtml(name.slice(0, 1))}</span><strong>${escapeHtml(name)}</strong><span>${escapeHtml(role)} · 华东中心</span></div><dl class="user-entry-details"><div><dt>用户名</dt><dd>liming</dd></div><div><dt>所属组织</dt><dd>华东中心 / 总装一车间</dd></div><div><dt>账号状态</dt><dd><span class="status ok">已启用</span></dd></div><div><dt>最后登录</dt><dd>2026-07-14 09:32</dd></div></dl><div class="user-entry-footer"><button class="btn btn-secondary" data-user-close>关闭</button></div>`);
    if (action === "security") openModal("安全设置", `<form data-user-password-form><label>当前密码<input type="password" name="current" required placeholder="请输入当前密码"></label><label>新密码<input type="password" name="next" required minlength="8" placeholder="至少 8 位，需包含字母和数字"></label><label>确认新密码<input type="password" name="confirm" required minlength="8" placeholder="请再次输入新密码"></label><p class="user-entry-hint">密码至少 8 位，并包含字母和数字。</p><div class="user-entry-footer"><button type="button" class="btn btn-secondary" data-user-close>取消</button><button class="btn btn-primary">保存密码</button></div></form>`);
    if (action === "management") location.href = "system-management.html?tab=users";
    if (action === "logout") { closeMenu(); if (window.confirm("确认退出当前账号？")) showToast("已安全退出登录"); }
  });
  modal.addEventListener("click", event => { if (event.target.closest("[data-user-close]")) closeModal(); });
  modal.addEventListener("submit", event => { if (!event.target.matches("[data-user-password-form]")) return; event.preventDefault(); const form = event.target; const next = form.elements.next.value; if (next !== form.elements.confirm.value) { showToast("两次输入的新密码不一致"); return; } if (!/[A-Za-z]/.test(next) || !/\d/.test(next) || next.length < 8) { showToast("新密码需至少 8 位，并包含字母和数字"); return; } closeModal(); showToast("密码已更新"); });
}

function initNotificationCenter() {
  $$(".topbar-actions [data-toast*='刷新'], .topbar-actions[aria-label*='刷新']").forEach((button) => button.remove());
  $$(".topbar-actions").forEach((actions) => {
    let bell = $$(".icon-btn", actions).find((button) => button.getAttribute("aria-label") === "消息通知" || button.textContent.trim() === "铃");
    if (!bell) {
      bell = document.createElement("button");
      bell.className = "icon-btn";
      bell.type = "button";
      bell.textContent = "铃";
      actions.prepend(bell);
    }
    initNotificationCenterForBell(bell);
  });
}

function initNotificationCenterForBell(bell) {
  if (!bell || bell.dataset.notificationReady) return;
  bell.dataset.notificationReady = "true";
  const notifications = [
    { id: "n1", type: "故障", tone: "critical", title: "非常紧急故障待接单", summary: "EL-2024-019 驱动电机温度快速升高，车辆限扭。", object: "FL-20260714-019", time: "10分钟前", unread: true, target: "fault-report.html" },
    { id: "n2", type: "工单", tone: "risk", title: "维修完成待验收", summary: "WO-240625-011 已提交维修结果，请完成验收。", object: "WO-240625-011", time: "35分钟前", unread: true, target: "repair-execution.html" },
    { id: "n3", type: "健康风险", tone: "risk", title: "设备健康分进入关注区间", summary: "EL-2023-088 当前健康分 58，风险等级为高风险。", object: "EL-2023-088", time: "1小时前", unread: false, target: "equipment-detail.html" },
    { id: "n4", type: "维修", tone: "success", title: "维修记录已提交", summary: "张师傅已提交液压压力波动处理结果。", object: "MR-20260714-007", time: "2小时前", unread: false, target: "maintenance-records.html" },
    { id: "n5", type: "Agent", tone: "info", title: "诊断建议已生成", summary: "故障诊断 Agent 已完成冷却回路排查建议。", object: "FL-20260713-004", time: "昨天", unread: false, target: "fault-report.html" }
  ];
  bell.innerHTML = '<svg class="notification-bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg><span class="notification-badge" data-notification-badge aria-label="未读消息数量"></span>';
  bell.removeAttribute("data-toast");
  bell.setAttribute("aria-label", "消息通知");
  bell.setAttribute("aria-expanded", "false");
  bell.setAttribute("aria-controls", "notificationPanel");
  const panel = document.createElement("section");
  panel.className = "notification-panel";
  panel.id = "notificationPanel";
  panel.dataset.notificationPanel = "true";
  panel.hidden = true;
  panel.innerHTML = '<div class="notification-head"><strong>消息通知</strong><button type="button" class="notification-read-all" data-notification-read-all>全部已读</button></div><div class="notification-tabs" role="tablist"><button type="button" class="active" data-notification-filter="all">全部</button><button type="button" data-notification-filter="unread">未读</button></div><div class="notification-list" data-notification-list></div><button type="button" class="notification-load-more" data-notification-more>加载更多</button>';
  document.body.appendChild(panel);
  let filter = "all";
  const unreadCount = () => notifications.filter((item) => item.unread).length;
  const updateBadge = () => { const count = unreadCount(); const badge = $("[data-notification-badge]", bell); badge.textContent = count > 99 ? "99+" : count ? String(count) : ""; badge.hidden = count === 0; };
  const render = () => { const list = $("[data-notification-list]", panel); const items = notifications.filter((item) => filter === "all" || item.unread); if (!items.length) { list.innerHTML = `<div class="notification-empty">${filter === "unread" ? "暂无未读消息" : "暂无消息通知"}</div>`; return; } list.innerHTML = items.map((item) => `<button type="button" class="notification-item ${item.unread ? "is-unread" : "is-read"}" data-notification-id="${item.id}"><span class="notification-dot ${item.tone}"></span><span class="notification-copy"><strong><em class="notification-type ${item.tone}">${item.type}</em>${item.title}</strong><span>${item.summary}</span><small>${item.object} · ${item.time}</small></span></button>`).join(""); };
  const close = () => { panel.hidden = true; bell.setAttribute("aria-expanded", "false"); };
  bell.addEventListener("click", (event) => { event.stopPropagation(); panel.hidden = !panel.hidden; bell.setAttribute("aria-expanded", String(!panel.hidden)); if (!panel.hidden) render(); });
  panel.addEventListener("click", (event) => { const tab = event.target.closest("[data-notification-filter]"); if (tab) { filter = tab.dataset.notificationFilter; $$(`[data-notification-filter]`, panel).forEach((button) => button.classList.toggle("active", button === tab)); render(); return; } if (event.target.closest("[data-notification-read-all]")) { notifications.forEach((item) => { item.unread = false; }); updateBadge(); render(); showToast("已全部标记为已读"); return; } const itemButton = event.target.closest("[data-notification-id]"); if (itemButton) { const item = notifications.find((entry) => entry.id === itemButton.dataset.notificationId); if (!item) return; item.unread = false; updateBadge(); itemButton.classList.remove("is-unread"); showToast(`${item.title}已标记为已读`); if (item.target) { window.setTimeout(() => { location.href = item.target; }, 250); } } });
  document.addEventListener("click", (event) => { if (!panel.contains(event.target) && !bell.contains(event.target)) close(); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") close(); });
  $(`[data-notification-more]`, panel).addEventListener("click", () => showToast("已加载更多业务通知"));
  updateBadge(); render();
}

/* global shell theme experiment reverted
  const actions = document.querySelector('.topbar-actions');
  if (!actions) return;
  let notice = actions.querySelector('[data-notification-center]');
  if (!notice) {
    notice = document.createElement('button');
    notice.className = 'icon-btn notification-trigger';
    notice.type = 'button';
    notice.setAttribute('data-notification-center', '');
    notice.setAttribute('aria-label', '通知中心');
    notice.innerHTML = '铃<sup>3</sup>';
    actions.prepend(notice);
  }
  const chip = actions.querySelector('.user-chip');
  if (!chip) return;
  chip.setAttribute('data-user-menu', ''); chip.setAttribute('role', 'button'); chip.setAttribute('tabindex', '0');
  const menu = document.createElement('div'); menu.className = 'global-user-menu'; menu.hidden = true;
  const label = chip.querySelector('span:last-child')?.textContent?.trim() || '当前用户';
  menu.innerHTML = `<div class="global-menu-user"><span class="avatar">${escapeHtml(label.slice(0,1))}</span><div><strong>${escapeHtml(label.split(' · ')[0])}</strong><span>${escapeHtml(label.split(' · ')[1] || '运维平台用户')}</span></div></div><button class="global-menu-item" data-global-action="profile">个人中心</button><button class="global-menu-item" data-global-action="theme">个性化 / 主题皮肤</button><button class="global-menu-item" data-global-action="logout">退出登录</button>`;
  document.body.appendChild(menu);
  const noticePanel = document.createElement('div'); noticePanel.className = 'notification-panel'; noticePanel.hidden = true;
  noticePanel.innerHTML = `<div class="notification-head"><strong>通知中心</strong><button class="global-menu-item" data-global-action="read-all" style="width:auto;padding:4px 6px">全部已读</button></div><div class="notification-item"><strong>故障单待处理</strong><p>EL-2024-019 有 1 条非常紧急故障待接单 · 10分钟前</p></div><div class="notification-item"><strong>健康评分变化</strong><p>3 台设备进入关注区间，请及时查看 · 35分钟前</p></div><div class="notification-item"><strong>系统公告</strong><p>健康分服务已完成本次计算 · 1小时前</p></div>`;
  document.body.appendChild(noticePanel);
  const closeAll = () => { menu.hidden = true; noticePanel.hidden = true; };
  chip.addEventListener('click', () => { noticePanel.hidden = true; menu.hidden = !menu.hidden; });
  chip.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); chip.click(); } });
  notice.addEventListener('click', () => { menu.hidden = true; noticePanel.hidden = !noticePanel.hidden; });
  document.addEventListener('click', e => { if (!menu.contains(e.target) && !noticePanel.contains(e.target) && !chip.contains(e.target) && !notice.contains(e.target)) closeAll(); });
  menu.addEventListener('click', e => { const action = e.target.closest('[data-global-action]')?.dataset.globalAction; if (action === 'profile') showToast('个人中心将在正式版打开'); if (action === 'logout') showToast('已安全退出登录'); if (action === 'theme') openThemePicker(menu); });
  noticePanel.addEventListener('click', e => { if (e.target.closest('[data-global-action="read-all"]')) { notice.innerHTML = '铃'; showToast('通知已全部标记为已读'); } });
  const saved = localStorage.getItem('ops-theme'); if (saved) document.body.classList.add(saved);
}

function openThemePicker(menu) {
  const current = document.body.className.match(/theme-(night|graphite|glacier)/)?.[0] || 'theme-light';
  menu.innerHTML = `<div class="global-menu-user"><strong>主题皮肤</strong><span>全局页面即时生效</span></div><div class="theme-grid"><button class="theme-choice ${current==='theme-light'?'active':''}" data-theme="theme-light"><div class="theme-swatch" style="background:linear-gradient(135deg,#0b74de,#dceeff)"></div><small>晴空蓝</small></button><button class="theme-choice ${current==='theme-night'?'active':''}" data-theme="theme-night"><div class="theme-swatch" style="background:linear-gradient(135deg,#0b1424,#2d82b7)"></div><small>深海夜航</small></button><button class="theme-choice ${current==='theme-graphite'?'active':''}" data-theme="theme-graphite"><div class="theme-swatch" style="background:linear-gradient(135deg,#20252b,#d87832)"></div><small>工业石墨</small></button><button class="theme-choice ${current==='theme-glacier'?'active':''}" data-theme="theme-glacier"><div class="theme-swatch" style="background:linear-gradient(135deg,#edfafa,#35b8b2)"></div><small>冰川青</small></button></div><button class="global-menu-item" data-global-action="back-theme">返回个人菜单</button>`;
  menu.querySelectorAll('[data-theme]').forEach(btn => btn.addEventListener('click', e => { const theme=e.currentTarget.dataset.theme; const old=[...document.body.classList].filter(c=>c.startsWith('theme-')); old.forEach(c=>document.body.classList.remove(c)); if(theme!=='theme-light') document.body.classList.add(theme); localStorage.setItem('ops-theme', theme); const fx=document.createElement('div'); fx.className='theme-transition'; fx.style.setProperty('--theme-transition-color', theme==='theme-night'?'#0b1424':theme==='theme-graphite'?'#20252b':theme==='theme-glacier'?'#edfafa':'#f4f7fb'); document.body.appendChild(fx); setTimeout(()=>fx.remove(),700); openThemePicker(menu); }));
  menu.querySelector('[data-global-action="back-theme"]').addEventListener('click', () => { menu.hidden=true; initGlobalShell(); });
} */
document.addEventListener("DOMContentLoaded", () => {
  setActiveNav();
  initSidebar();
  initTabs();
  initSegments();
  initDrawer();
  initForms();
  initFileUploads();
  initActions();
  initActionPanels();
  initBiDashboard();
  initEquipmentLedgerFilters();
  initEquipmentAddPage();
  initEquipmentDetailPage();
  initAgentDrawer();
  initUserEntry();
  initNotificationCenter();
});
