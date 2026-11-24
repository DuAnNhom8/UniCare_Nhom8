function initializeAdminPage() {
  initializeAdminDashboard();
  initializeAdminUsers();
  initializeAdminJobReview();
}

document.addEventListener("DOMContentLoaded", initializeAdminPage);
document.addEventListener("unicareer:page-loaded", initializeAdminPage);

function adminText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value == null ? "" : String(value);
  return element;
}

function adminStatus(status) {
  return {
    ACTIVE: ["Đang tuyển", "status--success"],
    PENDING: ["Chờ duyệt", "status--warning"],
    APPROVED: ["Đã duyệt", "status--success"],
    REJECTED: ["Từ chối", "status--rejected"],
  }[status] || [status, "status--received"];
}

document.querySelectorAll(".portal-sidebottom small").forEach((label) => {
  label.textContent = "Quản trị hệ thống";
});

async function initializeAdminDashboard() {
  if (!location.pathname.endsWith("/admin/dashboard.html")) return;
  try {
    const [stats, users, pendingJobs] = await Promise.all([
      UniCareerAPI.admin.getStats(),
      UniCareerAPI.admin.getUsers(),
      UniCareerAPI.admin.getJobs("PENDING"),
    ]);
    const values = document.querySelectorAll(".portal-stats .portal-stat__value");
    const notes = document.querySelectorAll(".portal-stats .portal-stat__note");
    if (values[0]) values[0].textContent = String(stats.total_users);
    if (values[1]) values[1].textContent = String(stats.employer_count);
    if (values[2]) values[2].textContent = String(stats.total_jobs);
    if (values[3]) values[3].textContent = String(stats.pending_jobs).padStart(2, "0");
    if (notes[0]) notes[0].textContent = `${stats.candidate_count} ứng viên`;
    if (notes[1]) notes[1].textContent = `${stats.company_count} doanh nghiệp`;
    if (notes[2]) notes[2].textContent = `${stats.active_jobs} tin đang tuyển`;
    const banner = document.querySelector(".portal-banner p");
    if (banner) banner.textContent = `Có ${stats.pending_jobs} tin đang chờ quản trị viên xem xét.`;
    const pendingJobsBody = document.getElementById("pending-jobs-body");
    if (pendingJobsBody) {
      pendingJobsBody.replaceChildren();
      pendingJobs.slice(0, 5).forEach((job) => {
        const row = document.createElement("tr");
        const titleCell = document.createElement("td");
        titleCell.append(adminText("strong", "", job.title));
        titleCell.append(adminText("small", "", `${job.job_type} · ${job.location || "—"}`));
        const status = adminStatus(job.approval_status);
        const statusCell = document.createElement("td");
        statusCell.append(adminText("span", `status ${status[1]}`, status[0]));
        row.append(
          titleCell,
          adminText("td", "", job.company_name || "—"),
          statusCell,
        );
        pendingJobsBody.append(row);
      });
      if (!pendingJobs.length) {
        const row = document.createElement("tr");
        const cell = adminText("td", "", "Không có tin đang chờ duyệt.");
        cell.colSpan = 3;
        row.append(cell);
        pendingJobsBody.append(row);
      }
    }

    const usersBody = document.getElementById("recent-users-body");
    if (usersBody) {
      usersBody.replaceChildren();
      users.slice(0, 3).forEach((user) => {
        const row = document.createElement("tr");
        const account = user.full_name || user.company_name || user.email;
        const role = user.role === "candidate" ? "Sinh viên"
          : user.role === "employer" ? "Nhà tuyển dụng" : "Quản trị viên";
        const status = user.is_active
          ? ["Đang hoạt động", "status--success"]
          : ["Đã khóa", "status--rejected"];
        const statusCell = document.createElement("td");
        statusCell.append(adminText("span", `status ${status[1]}`, status[0]));
        row.append(
          adminText("td", "", account),
          adminText("td", "", role),
          statusCell,
        );
        usersBody.append(row);
      });
      if (!users.length) {
        const row = document.createElement("tr");
        const cell = adminText("td", "", "Chưa có tài khoản.");
        cell.colSpan = 3;
        row.append(cell);
        usersBody.append(row);
      }
    }
  } catch (error) {
    const help = document.querySelector(".portal-help");
    if (help) help.textContent = error.message;
    ["pending-jobs-body", "recent-users-body"].forEach((id) => {
      const body = document.getElementById(id);
      if (!body) return;
      const row = document.createElement("tr");
      const cell = adminText("td", "", error.message);
      cell.colSpan = 3;
      row.replaceChildren(cell);
      body.replaceChildren(row);
    });
  }
}

async function initializeAdminUsers() {
  if (!location.pathname.endsWith("/admin/users.html")) return;
  const body = document.querySelector(".portal-table tbody");
  if (!body) return;
  const search = document.getElementById("user-search");
  const roleFilter = document.getElementById("user-role");
  const statusFilter = document.getElementById("user-status");
  const pagination = document.getElementById("admin-users-pagination");
  const pageSize = 10;
  let currentPage = 1;
  let users = [];
  function render(page = currentPage) {
    currentPage = page;
    const query = search?.value.trim().toLocaleLowerCase("vi") || "";
    const roleText = roleFilter?.selectedIndex > 0
      ? roleFilter.options[roleFilter.selectedIndex].textContent.trim()
      : "";
    const statusText = statusFilter?.selectedIndex > 0
      ? statusFilter.options[statusFilter.selectedIndex].textContent.trim()
      : "";
    const visible = users.filter((user) => {
      const roleName = user.role === "candidate" ? "Sinh viên" : user.role === "employer" ? "Nhà tuyển dụng" : "Quản trị viên";
      const statusName = user.is_active ? "Đang hoạt động" : "Đã khóa";
      return (!query || `${user.full_name || ""} ${user.company_name || ""} ${user.email}`.toLocaleLowerCase("vi").includes(query))
        && (!roleText || roleName === roleText)
        && (!statusText || statusName === statusText);
    });
    currentPage = Math.min(currentPage, Math.max(1, Math.ceil(visible.length / pageSize)));
    body.replaceChildren();
    if (!visible.length) {
      const row = document.createElement("tr");
      const cell = adminText("td", "", "Không tìm thấy người dùng phù hợp.");
      cell.colSpan = 5;
      row.append(cell);
      body.append(row);
    }
    visible.slice((currentPage - 1) * pageSize, currentPage * pageSize).forEach((user) => {
      const row = document.createElement("tr");
      const account = document.createElement("td");
      account.append(adminText("strong", "", user.full_name || user.company_name || user.email.split("@")[0]));
      account.append(adminText("small", "", user.email));
      const statusCell = document.createElement("td");
      statusCell.append(adminText("span", `status ${user.is_active ? "status--success" : "status--rejected"}`, user.is_active ? "Đang hoạt động" : "Đã khóa"));
      const action = document.createElement("td");
      if (user.role === "admin") {
        action.append(adminText("span", "muted", "Quản trị viên"));
      } else {
        const button = adminText("button", "btn btn-outline btn-sm", user.is_active ? "Khóa" : "Mở khóa");
        button.type = "button";
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            await UniCareerAPI.admin.setUserStatus(user.user_id, !user.is_active);
            user.is_active = !user.is_active;
            render();
          } catch (error) {
            alert(error.message);
            button.disabled = false;
          }
        });
        action.append(button);
      }
      row.append(
        account,
        adminText("td", "", user.role === "candidate" ? "Sinh viên" : user.role === "employer" ? "Nhà tuyển dụng" : "Quản trị viên"),
        adminText("td", "", new Date(user.created_at).toLocaleDateString("vi-VN")),
        statusCell,
        action,
      );
      body.append(row);
    });
    const badge = document.querySelector(".portal-panel__heading .portal-pill");
    if (badge) badge.textContent = `${users.length} tài khoản`;
    renderPortalPagination(pagination, currentPage, visible.length, pageSize, render);
  }
  try {
    users = await UniCareerAPI.admin.getUsers();
    render();
  } catch (error) {
    body.replaceChildren();
    const row = document.createElement("tr");
    const cell = adminText("td", "", error.message);
    cell.colSpan = 5;
    row.append(cell);
    body.append(row);
  }
  [search, roleFilter, statusFilter].filter(Boolean).forEach((control) => {
    control.addEventListener("input", () => render(1));
    control.addEventListener("change", () => render(1));
  });
}

async function initializeAdminJobReview() {
  if (!location.pathname.endsWith("/admin/approve-jobs.html")) return;
  const body = document.querySelector(".portal-table tbody");
  if (!body) return;
  const search = document.getElementById("job-search");
  const tabs = Array.from(document.querySelectorAll(".portal-tabs button"));
  const pagination = document.getElementById("admin-jobs-pagination");
  const pageSize = 10;
  let activeStatus = "PENDING";
  let currentPage = 1;
  let jobs = [];
  async function load() {
    try {
      jobs = await UniCareerAPI.admin.getJobs(activeStatus);
      render();
    } catch (error) {
      body.replaceChildren();
      const row = document.createElement("tr");
      const cell = adminText("td", "", error.message);
      cell.colSpan = 5;
      row.append(cell);
      body.append(row);
    }
  }
  function render(page = currentPage) {
    currentPage = page;
    const query = search?.value.trim().toLocaleLowerCase("vi") || "";
    const visible = jobs.filter((job) => `${job.title} ${job.company_name || ""} ${job.location || ""}`.toLocaleLowerCase("vi").includes(query));
    currentPage = Math.min(currentPage, Math.max(1, Math.ceil(visible.length / pageSize)));
    body.replaceChildren();
    if (!visible.length) {
      const row = document.createElement("tr");
      const cell = adminText("td", "", "Không có tin phù hợp.");
      cell.colSpan = 5;
      row.append(cell);
      body.append(row);
    }
    visible.slice((currentPage - 1) * pageSize, currentPage * pageSize).forEach((job) => {
      const row = document.createElement("tr");
      const titleCell = document.createElement("td");
      titleCell.append(adminText("strong", "", job.title));
      titleCell.append(adminText("small", "", `${job.job_type} · ${job.location || "—"}`));
      const approval = adminStatus(job.approval_status);
      const statusCell = document.createElement("td");
      statusCell.append(adminText("span", `status ${approval[1]}`, approval[0]));
      const actionsCell = document.createElement("td");
      const actions = document.createElement("div");
      actions.className = "admin-job-actions";
      ["APPROVED", "REJECTED"].forEach((value) => {
        if (job.approval_status === value) return;
        const actionClass = value === "APPROVED"
          ? "admin-job-action--approve"
          : "admin-job-action--reject";
        const button = adminText(
          "button",
          `btn admin-job-action ${actionClass}`,
          value === "APPROVED" ? "Duyệt" : "Từ chối",
        );
        button.type = "button";
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            await UniCareerAPI.admin.setJobApproval(job.job_id, value);
            await load();
          } catch (error) {
            alert(error.message);
            button.disabled = false;
          }
        });
        actions.append(button);
      });
      actionsCell.append(actions);
      row.append(
        titleCell,
        adminText("td", "", job.company_name || "—"),
        adminText("td", "", new Date(job.created_at).toLocaleDateString("vi-VN")),
        statusCell,
        actionsCell,
      );
      body.append(row);
    });
    const badge = document.querySelector(".portal-panel__heading .portal-pill");
    if (badge) badge.textContent = `${jobs.length} tin`;
    renderPortalPagination(pagination, currentPage, visible.length, pageSize, render);
  }
  tabs.forEach((tab, index) => {
    const value = ["PENDING", "APPROVED", "REJECTED"][index];
    tab.disabled = false;
    tab.addEventListener("click", () => {
      activeStatus = value;
      currentPage = 1;
      tabs.forEach((item) => item.setAttribute("aria-selected", String(item === tab)));
      load();
    });
  });
  search?.addEventListener("input", () => render(1));
  load();
}