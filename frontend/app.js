const views = {
  overview: "全链路质量概览",
  cases: "用例资产管理",
  mock: "Mock 服务中心",
  ci: "CI 与报告中心",
};

const loginScreen = document.querySelector("#loginScreen");
const appShell = document.querySelector("#appShell");
const loginForm = document.querySelector("#loginForm");
const navItems = document.querySelectorAll(".nav-item");
const viewNodes = document.querySelectorAll(".view");
const title = document.querySelector("#viewTitle");
const toast = document.querySelector("#toast");
const runLog = document.querySelector("#runLog");
const jobStatus = document.querySelector("#jobStatus");

let currentJobId = null;
let pollTimer = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "same-origin",
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "请求失败");
  }
  return data;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 1800);
}

function switchView(viewName) {
  navItems.forEach((item) => item.classList.toggle("active", item.dataset.view === viewName));
  viewNodes.forEach((view) => view.classList.toggle("active", view.id === viewName));
  title.textContent = views[viewName];
}

function showApp(user) {
  loginScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
  document.querySelector("#userChip").textContent = user.username;
}

function showLogin() {
  appShell.classList.add("hidden");
  loginScreen.classList.remove("hidden");
}

function renderDashboard(data) {
  document.querySelector("#chainNodes").textContent = data.metrics.chain_nodes;
  document.querySelector("#mockRoutes").textContent = data.metrics.mock_routes;
  document.querySelector("#caseFiles").textContent = data.metrics.case_files;
  document.querySelector("#reportType").textContent = data.metrics.report_type;
  document.querySelector("#envText").textContent = data.environment;

  document.querySelector("#flowSteps").innerHTML = data.flow
    .map((step, index) => `<div class="flow-step ${step.status}"><b>${index + 1}</b><span>${step.name}</span></div>`)
    .join("");
}

function renderCases(data) {
  document.querySelector("#caseTable").innerHTML = data.cases
    .map(
      (item) => `
        <tr>
          <td>${item.path}</td>
          <td>${item.type}</td>
          <td>${item.count}</td>
          <td><span class="pill ${item.status === "ready" ? "ok" : "warn"}">${item.label}</span></td>
        </tr>
      `,
    )
    .join("");
}

function renderMock(data) {
  document.querySelector("#endpointGrid").innerHTML = data.endpoints
    .map((item) => `<div><b>${item.path}</b><span>${item.desc}</span></div>`)
    .join("");
}

function renderCi(data) {
  document.querySelector("#ciInfo").innerHTML = `
    <dt>Job</dt><dd>${data.job_name}</dd>
    <dt>安装</dt><dd>${data.install}</dd>
    <dt>执行</dt><dd>${data.test}</dd>
    <dt>归档</dt><dd>${data.artifacts}</dd>
  `;
}

async function loadData() {
  const [dashboard, cases, mock, ci] = await Promise.all([
    api("/api/dashboard"),
    api("/api/cases"),
    api("/api/mock"),
    api("/api/ci"),
  ]);
  renderDashboard(dashboard);
  renderCases(cases);
  renderMock(mock);
  renderCi(ci);
}

async function checkLogin() {
  try {
    const data = await api("/api/me");
    showApp(data.user);
    await loadData();
  } catch {
    showLogin();
  }
}

function renderJob(job) {
  jobStatus.textContent = job.status;
  runLog.innerHTML = job.logs.map((line) => `<p>${line}</p>`).join("");
  runLog.scrollTop = runLog.scrollHeight;
}

async function pollJob() {
  if (!currentJobId) return;
  const job = await api(`/api/jobs/${currentJobId}`);
  renderJob(job);
  if (job.status === "passed" || job.status === "failed") {
    window.clearInterval(pollTimer);
    pollTimer = null;
    showToast(`任务${job.status === "passed" ? "通过" : "失败"}`);
  }
}

navItems.forEach((item) => {
  item.addEventListener("click", () => switchView(item.dataset.view));
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.querySelector("#username").value.trim();
  const password = document.querySelector("#password").value;

  try {
    const data = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    showApp(data.user);
    await loadData();
    showToast("登录成功");
  } catch (error) {
    showToast(error.message);
  }
});

document.querySelector("#logoutBtn").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  showLogin();
  showToast("已退出登录");
});

document.querySelector("#refreshBtn").addEventListener("click", async () => {
  await loadData();
  showToast("页面数据已刷新");
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const command = button.dataset.copy;
    try {
      await navigator.clipboard.writeText(command);
      showToast("命令已复制");
    } catch {
      showToast(command);
    }
  });
});

document.querySelector("#runBtn").addEventListener("click", async () => {
  const job = await api("/api/run-tests", { method: "POST" });
  currentJobId = job.job_id;
  renderJob(job);
  showToast("已触发全链路任务");
  if (pollTimer) window.clearInterval(pollTimer);
  pollTimer = window.setInterval(pollJob, 900);
});

checkLogin();
