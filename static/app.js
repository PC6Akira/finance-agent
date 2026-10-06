/* 基金投研 Agent 前端逻辑：登录 + 四个 Tab（对话 / 持仓 / 基金数据 / 数据源测试）。 */
(function () {
  "use strict";

  // --- 调色板（dataviz 参考，light / dark 跟随系统） ---
  const PALETTES = {
    light: {
      surface: "#fcfcfb", ink: "#0b0b0b", secondary: "#52514e", muted: "#898781",
      grid: "#e1e0d9", axis: "#c3c2b7", series1: "#2a78d6", series2: "#eb6834",
    },
    dark: {
      surface: "#1a1a19", ink: "#ffffff", secondary: "#c3c2b7", muted: "#898781",
      grid: "#2c2c2a", axis: "#383835", series1: "#3987e5", series2: "#d95926",
    },
  };
  let darkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const pal = () => PALETTES[darkMode ? "dark" : "light"];

  // --- 状态 ---
  let token = localStorage.getItem("token") || "";
  let charts = {}; // 缓存 ECharts 实例

  const $ = (id) => document.getElementById(id);

  // --- 工具：API 请求 ---
  async function api(path, opts) {
    opts = opts || {};
    const headers = Object.assign({}, opts.headers || {});
    if (token) headers["Authorization"] = "Bearer " + token;
    let body;
    if (opts.json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(opts.json);
    }
    const res = await fetch(path, { method: opts.method || "GET", headers: headers, body: body });
    if (res.status === 401) { doLogout(true); throw new Error("未登录或登录已过期"); }
    let data = null;
    try { data = await res.json(); } catch (e) { /* 无 body */ }
    if (!res.ok) throw new Error((data && data.detail) || ("请求失败（" + res.status + "）"));
    return data;
  }

  function setMsg(el, text, kind) {
    el.textContent = text || "";
    el.className = "msg" + (kind ? " " + kind : "");
  }

  // --- 视图切换 ---
  function showApp(on) {
    $("login-view").hidden = on;
    $("app-view").hidden = !on;
  }

  function switchTab(name) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll("section.panel").forEach((s) => { s.hidden = s.id !== "tab-" + name; });
    if (name === "fund") resizeCharts();
  }

  // --- 登录 / 注册 / 登出 ---
  function doLogout(silent) {
    token = "";
    localStorage.removeItem("token");
    showApp(false);
    if (!silent) { /* 已在前端清除 */ }
  }

  async function doLogin() {
    const username = $("auth-username").value.trim();
    const password = $("auth-password").value;
    try {
      const data = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      }).then(async (r) => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || "登录失败");
        return d;
      });
      token = data.token;
      localStorage.setItem("token", token);
      $("auth-msg").textContent = "";
      enterApp(data.username);
    } catch (e) {
      $("auth-msg").textContent = "❌ " + e.message;
    }
  }

  async function doRegister() {
    const username = $("auth-username").value.trim();
    const password = $("auth-password").value;
    try {
      const d = await api("/api/auth/register", { method: "POST", json: { username: username, password: password } });
      $("auth-msg").textContent = "✅ " + d.message + "，请登录";
    } catch (e) {
      $("auth-msg").textContent = "❌ " + e.message;
    }
  }

  function enterApp(username) {
    $("user-name").textContent = username;
    showApp(true);
    switchTab("chat");
    $("chat-input").focus();
    loadHoldings();
    loadRecommend();
  }

  // --- 对话 ---
  async function sendMessage(text) {
    text = (text || "").trim();
    if (!text) return;
    appendBubble("user", text);
    $("chat-input").value = "";
    $("btn-send").disabled = true;
    const thinking = appendBubble("assistant", "思考中…");
    try {
      const data = await api("/api/chat", { method: "POST", json: { message: text } });
      thinking.textContent = data.reply;
    } catch (e) {
      thinking.textContent = "⚠️ " + e.message;
      thinking.style.color = "var(--danger)";
    } finally {
      $("btn-send").disabled = false;
    }
  }

  function appendBubble(role, text) {
    const el = document.createElement("div");
    el.className = "msg-bubble " + role;
    el.textContent = text;
    $("chat-log").appendChild(el);
    $("chat-log").scrollTop = $("chat-log").scrollHeight;
    return el;
  }

  // --- 持仓 ---
  async function loadHoldings() {
    try {
      const rows = await api("/api/holdings");
      const tbody = $("holdings-table").querySelector("tbody");
      tbody.innerHTML = "";
      rows.forEach((h) => {
        const tr = document.createElement("tr");
        const cells = [h.fund_code, h.fund_name || "", h.amount == null ? "" : h.amount, h.cost == null ? "" : h.cost];
        cells.forEach((c) => { const td = document.createElement("td"); td.textContent = String(c); tr.appendChild(td); });
        const td = document.createElement("td");
        td.className = "del";
        const btn = document.createElement("button");
        btn.className = "link-del";
        btn.textContent = "删除";
        btn.onclick = () => removeHolding(h.fund_code);
        td.appendChild(btn);
        tr.appendChild(td);
        tbody.appendChild(tr);
      });
    } catch (e) {
      setMsg($("holding-msg"), e.message, "error");
    }
  }

  async function addHolding() {
    const fund_code = $("h-code").value.trim();
    const amount = parseFloat($("h-amount").value);
    const costRaw = $("h-cost").value.trim();
    const cost = costRaw === "" ? null : parseFloat(costRaw);
    try {
      const d = await api("/api/holdings", { method: "POST", json: { fund_code: fund_code, amount: amount, cost: cost } });
      setMsg($("holding-msg"), d.message, "ok");
      $("h-code").value = ""; $("h-amount").value = ""; $("h-cost").value = "";
      loadHoldings();
      loadRecommend();
    } catch (e) {
      setMsg($("holding-msg"), e.message, "error");
    }
  }

  async function removeHolding(code) {
    try {
      await api("/api/holdings/" + encodeURIComponent(code), { method: "DELETE" });
      loadHoldings();
      loadRecommend();
    } catch (e) {
      setMsg($("holding-msg"), e.message, "error");
    }
  }

  async function loadRecommend() {
    const row = $("rec-row");
    row.innerHTML = "";
    try {
      const d = await api("/api/recommend");
      d.questions.forEach((q) => {
        if (!q) return;
        const btn = document.createElement("button");
        btn.textContent = q;
        btn.onclick = () => { $("chat-input").value = q; switchTab("chat"); $("chat-input").focus(); };
        row.appendChild(btn);
      });
    } catch (e) { /* 静默 */ }
  }

  // --- 基金数据 ---
  async function loadFund() {
    const code = $("f-code").value.trim();
    if (!code) return;
    setMsg($("fund-msg"), "加载中…");
    try {
      const d = await api("/api/fund/" + encodeURIComponent(code));
      renderNav(d.nav);
      renderIndustry(d.industry);
      renderBacktest(d.backtest);
      renderFundHoldings(d.holdings);
      renderRisk(d.risk_points);
      setMsg($("fund-msg"), "");
    } catch (e) {
      setMsg($("fund-msg"), e.message, "error");
    }
  }

  function renderFundHoldings(holdings) {
    const tbody = $("fund-holdings-table").querySelector("tbody");
    tbody.innerHTML = "";
    holdings.forEach((h) => {
      const tr = document.createElement("tr");
      [h.stock_code, h.stock_name, (h.weight == null ? "" : h.weight + "%")].forEach((c) => {
        const td = document.createElement("td");
        td.textContent = String(c);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }

  function renderRisk(points) {
    const el = $("risk-points");
    el.innerHTML = "";
    if (!points || points.length === 0) {
      el.innerHTML = '<div class="muted">未发现明显风险点（在设定阈值内）。</div>';
      return;
    }
    points.forEach((p) => {
      const div = document.createElement("div");
      div.className = "risk-item";
      const b = document.createElement("b");
      b.textContent = p.metric + "：";
      div.appendChild(b);
      div.appendChild(document.createTextNode(p.value + " → " + p.risk));
      el.appendChild(div);
    });
  }

  // --- ECharts 渲染 ---
  function getChart(id) {
    if (!charts[id]) charts[id] = echarts.init($(id), null, { renderer: "canvas" });
    return charts[id];
  }

  function resizeCharts() {
    Object.values(charts).forEach((c) => c.resize());
  }

  function baseTooltip() {
    const p = pal();
    return {
      trigger: "axis",
      backgroundColor: p.surface,
      borderColor: p.grid,
      textStyle: { color: p.ink, fontSize: 12 },
      axisPointer: { lineStyle: { color: p.axis }, crossStyle: { color: p.axis } },
    };
  }

  function renderNav(nav) {
    const p = pal();
    getChart("chart-nav").setOption({
      tooltip: baseTooltip(),
      grid: { left: 48, right: 20, top: 20, bottom: 36 },
      xAxis: {
        type: "category", data: nav.dates, boundaryGap: false,
        axisLine: { lineStyle: { color: p.axis } }, axisTick: { show: false },
        axisLabel: { color: p.muted },
      },
      yAxis: {
        type: "value", scale: true,
        splitLine: { lineStyle: { color: p.grid } }, axisLabel: { color: p.muted },
      },
      series: [{
        type: "line", data: nav.nav, showSymbol: false, smooth: false,
        lineStyle: { width: 2, color: p.series1 }, itemStyle: { color: p.series1 },
      }],
    });
  }

  function renderIndustry(ind) {
    const p = pal();
    getChart("chart-industry").setOption({
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: p.surface, borderColor: p.grid, textStyle: { color: p.ink, fontSize: 12 } },
      grid: { left: 96, right: 40, top: 12, bottom: 28 },
      xAxis: { type: "value", splitLine: { lineStyle: { color: p.grid } }, axisLabel: { color: p.muted } },
      yAxis: { type: "category", data: ind.labels, axisLine: { lineStyle: { color: p.axis } }, axisTick: { show: false }, axisLabel: { color: p.secondary } },
      series: [{
        type: "bar", data: ind.weights, barWidth: 18,
        itemStyle: { color: p.series1, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", color: p.secondary, formatter: "{c}%" },
      }],
    });
  }

  function renderBacktest(bt) {
    const p = pal();
    getChart("chart-backtest").setOption({
      tooltip: baseTooltip(),
      legend: { top: 0, right: 0, textStyle: { color: p.secondary, fontSize: 12 }, itemWidth: 16, itemHeight: 8 },
      grid: { left: 48, right: 20, top: 32, bottom: 36 },
      xAxis: {
        type: "category", data: bt.dates, boundaryGap: false,
        axisLine: { lineStyle: { color: p.axis } }, axisTick: { show: false }, axisLabel: { color: p.muted },
      },
      yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: p.grid } }, axisLabel: { color: p.muted, formatter: "{value}%" } },
      series: [
        { name: "买入持有", type: "line", data: bt.buy_hold, showSymbol: false, lineStyle: { width: 2, color: p.series1 }, itemStyle: { color: p.series1 } },
        { name: "定投", type: "line", data: bt.dca, showSymbol: false, lineStyle: { width: 2, color: p.series2 }, itemStyle: { color: p.series2 } },
      ],
    });
  }

  // --- 数据源测试 ---
  const DS_ENDPOINTS = {
    nav: (c) => "/api/datasource/nav/" + c,
    holdings: (c) => "/api/datasource/holdings/" + c,
    industry: (c) => "/api/datasource/industry/" + c,
    reports: (c) => "/api/datasource/reports/" + c,
    cls: () => "/api/datasource/cls",
    personnel: (c) => "/api/datasource/personnel/" + c,
    dividend: (c) => "/api/datasource/dividend/" + c,
  };

  async function loadDatasource(name) {
    const code = encodeURIComponent($("ds-code").value.trim());
    setMsg($("ds-msg"), "加载中…");
    try {
      const records = await api(DS_ENDPOINTS[name](code));
      renderRecords(records);
      setMsg($("ds-msg"), "共 " + records.length + " 条");
    } catch (e) {
      setMsg($("ds-msg"), e.message, "error");
      $("ds-table-wrap").innerHTML = "";
    }
  }

  async function doSearch() {
    const q = $("ds-query").value.trim();
    if (!q) return;
    setMsg($("ds-msg"), "搜索中…");
    try {
      const records = await api("/api/datasource/search?q=" + encodeURIComponent(q));
      renderRecords(records);
      setMsg($("ds-msg"), "共 " + records.length + " 条");
    } catch (e) {
      setMsg($("ds-msg"), e.message, "error");
      $("ds-table-wrap").innerHTML = "";
    }
  }

  function renderRecords(records) {
    const wrap = $("ds-table-wrap");
    wrap.innerHTML = "";
    if (!records || records.length === 0) {
      wrap.innerHTML = '<div class="muted">无数据</div>';
      return;
    }
    const cols = Object.keys(records[0]);
    const table = document.createElement("table");
    table.className = "table";
    const thead = document.createElement("thead");
    const htr = document.createElement("tr");
    cols.forEach((c) => { const th = document.createElement("th"); th.textContent = c; htr.appendChild(th); });
    thead.appendChild(htr);
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    records.forEach((r) => {
      const tr = document.createElement("tr");
      cols.forEach((c) => {
        const td = document.createElement("td");
        const v = r[c];
        if (c === "url" && v) {
          const a = document.createElement("a");
          a.href = v; a.target = "_blank"; a.textContent = "链接";
          td.appendChild(a);
        } else {
          td.textContent = v == null ? "" : String(v);
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
  }

  // --- 事件绑定 ---
  $("btn-login").addEventListener("click", doLogin);
  $("btn-register").addEventListener("click", doRegister);
  $("auth-password").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });
  $("btn-logout").addEventListener("click", () => { if (token) api("/api/auth/logout", { method: "POST" }).catch(() => {}); doLogout(); });

  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));

  $("btn-send").addEventListener("click", () => sendMessage($("chat-input").value));
  $("chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage($("chat-input").value); }
  });

  $("btn-add-holding").addEventListener("click", addHolding);
  $("btn-query-fund").addEventListener("click", loadFund);
  document.querySelectorAll(".ds-btns button").forEach((b) => b.addEventListener("click", () => loadDatasource(b.dataset.ds)));
  $("btn-search").addEventListener("click", doSearch);

  window.addEventListener("resize", resizeCharts);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    darkMode = e.matches;
    Object.keys(charts).forEach((id) => {
      const el = $(id);
      if (el && !el.closest("section").hidden) resizeCharts();
    });
  });

  // --- 启动：若已有 token，尝试恢复会话 ---
  (async function boot() {
    if (!token) { showApp(false); return; }
    try {
      const me = await api("/api/auth/me");
      enterApp(me.username);
    } catch (e) {
      showApp(false);
    }
  })();
})();
