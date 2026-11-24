function initializeCompanyPage() {
  initializeCompanyIdentity();
  initializeCompanyProfile();
  initializeCompanyJobs();
  initializeJobForms();
  initializeCompanyApplications();
  initializeCompanyDashboard();
}

document.addEventListener("DOMContentLoaded", initializeCompanyPage);
document.addEventListener("unicareer:page-loaded", initializeCompanyPage);

async function initializeCompanyIdentity() {
  try {
    const company = await UniCareerAPI.company.getProfile();
    updateCompanyIdentity(company.company_name);
    document.querySelectorAll(".portal-sidebottom small").forEach((element) => {
      element.textContent = "Nhà tuyển dụng";
    });
  } catch (error) {
    if (error.status !== 404) {
      const help = document.querySelector(".portal-help");
      if (help) help.textContent = error.message;
    }
  }
}

function companyText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value == null ? "" : String(value);
  return element;
}

function companyDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value).slice(0, 10) : date.toLocaleDateString("vi-VN");
}

function jobTypeFromControl(control) {
  const value = control.value || control.options[control.selectedIndex]?.textContent || "";
  if (value.includes("Thực tập")) return "INTERNSHIP";
  if (value.includes("Bán thời gian")) return "PART_TIME";
  if (value.includes("Toàn thời gian")) return "FULL_TIME";
  return value;
}

function statusLabel(status) {
  return {
    ACTIVE: ["Đang tuyển", "status--success"],
    CLOSED: ["Đã đóng", "status--received"],
    HIDDEN: ["Đang ẩn", "status--warning"],
    PENDING: ["Chờ duyệt", "status--warning"],
    APPROVED: ["Đã duyệt", "status--success"],
    REJECTED: ["Từ chối", "status--rejected"],
    REVIEWING: ["Đang xem xét", "status--reviewing"],
    ACCEPTED: ["Đã chấp nhận", "status--accepted"],
  }[status] || [status || "—", "status--received"];
}

function companyJobStatus(job) {
  const statusWrap = document.createElement("div");
  statusWrap.className = "company-job-status";
  const jobStatus = statusLabel(job.status);
  const approvalStatus = statusLabel(job.approval_status);
  const approvalClass = job.approval_status === "APPROVED"
    ? "status--reviewing" : approvalStatus[1];
  [
    ["Tin đăng", jobStatus],
    ["Kiểm duyệt", [approvalStatus[0], approvalClass]],
  ].forEach(([label, status]) => {
    const statusItem = document.createElement("div");
    statusItem.className = "company-job-status__item";
    statusItem.append(
      companyText("small", "company-job-status__label", label),
      companyText("span", `status ${status[1]} company-job-status__badge`, status[0]),
    );
    statusWrap.append(statusItem);
  });
  return statusWrap;
}

function setCompanyFeedback(id, message, isError) {
  const target = document.getElementById(id);
  if (!target) return;
  target.textContent = message;
  target.classList.toggle("is-error", Boolean(isError));
}

async function initializeCompanyProfile() {
  const form = document.getElementById("company-form");
  if (!form) return;
  const feedback = document.getElementById("company-status");
  try {
    const company = await UniCareerAPI.company.getProfile();
    fillCompanyForm(company);
    renderCompanyInfo(company);
  } catch (error) {
    if (error.status !== 404) {
      setCompanyFeedback("company-status", error.message, true);
      return;
    }
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    const data = {
      company_name: document.getElementById("company-name").value.trim(),
      industry: document.getElementById("company-industry").value.trim(),
      website: document.getElementById("company-website").value.trim(),
      location: document.getElementById("company-location")?.value.trim() || "",
      description: document.getElementById("company-description").value.trim(),
    };
    try {
      const company = await UniCareerAPI.company.saveProfile(data);
      fillCompanyForm(company);
      renderCompanyInfo(company);
      feedback.textContent = "Đã lưu hồ sơ doanh nghiệp.";
      feedback.classList.remove("is-error");
    } catch (error) {
      setCompanyFeedback("company-status", error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

function fillCompanyForm(company) {
  const fields = {
    "company-name": company.company_name,
    "company-industry": company.industry,
    "company-website": company.website,
    "company-location": company.location,
    "company-description": company.description,
  };
  Object.entries(fields).forEach(([id, value]) => {
    const field = document.getElementById(id);
    if (field && value != null) field.value = value;
  });
}

function renderCompanyInfo(company) {
  const panel = document.querySelector(".company-profile");
  if (panel) {
    const industry = panel.querySelector("p");
    const description = panel.parentElement.querySelector(".portal-divider + p");
    if (industry) industry.textContent = company.industry || "Doanh nghiệp";
    if (description) description.textContent = company.description || "Chưa có giới thiệu doanh nghiệp.";
  }
  updateCompanyIdentity(company.company_name);
  const values = document.querySelectorAll(".portal-stats .portal-stat__value");
  if (values[0]) values[0].textContent = String(company.job_count);
  if (values[1]) values[1].textContent = String(company.application_count);
}

function updateCompanyIdentity(companyName) {
  const name = typeof companyName === "string" ? companyName.trim() : "";
  if (!name) return;

  const initials = name.split(/\s+/).slice(0, 2)
    .map((part) => part.slice(0, 1)).join("").toLocaleUpperCase("vi");
  document.querySelectorAll(".portal-sidebottom strong, .company-profile h3").forEach((element) => {
    element.textContent = name;
  });
  document.querySelectorAll(".portal-avatar").forEach((element) => {
    element.textContent = initials || "DN";
  });
}

function markCompanyStatsUnavailable() {
  document.querySelectorAll(".portal-stats .portal-stat__value").forEach((value) => {
    value.textContent = "—";
  });
}

async function listAllCompanyJobs() {
  const jobs = [];
  let skip = 0;
  while (true) {
    const batch = await UniCareerAPI.jobs.list({ limit: 100, skip });
    jobs.push(...batch);
    if (batch.length < 100) return jobs;
    skip += batch.length;
  }
}

async function initializeCompanyJobs(page = 1) {
  const table = document.querySelector(".portal-table");
  const body = table?.querySelector("tbody");
  if (!body || !location.pathname.endsWith("/manage-jobs.html")) return;
  const pagination = document.getElementById("company-jobs-pagination");
  const pageSize = 10;
  try {
    const jobs = await listAllCompanyJobs();
    page = Math.min(page, Math.max(1, Math.ceil(jobs.length / pageSize)));
    const count = document.querySelector(".portal-panel__heading .portal-pill");
    if (count) count.textContent = `${jobs.length} tin`;
    body.replaceChildren();
    if (!jobs.length) {
      body.append(emptyTableRow(5, "Chưa có tin tuyển dụng."));
      renderPortalPagination(pagination, page, 0, pageSize, initializeCompanyJobs);
      return;
    }
    jobs.slice((page - 1) * pageSize, page * pageSize).forEach((job) => {
      const row = document.createElement("tr");
      const titleCell = document.createElement("td");
      titleCell.append(companyText("strong", "", job.title));
      titleCell.append(companyText("small", "", `${job.location || "—"} · ${job.job_type}`));
      const actions = document.createElement("td");
      const edit = companyText("a", "btn btn-sm company-job-action company-job-action--primary", "Chỉnh sửa");
      edit.href = `edit-job.html?job_id=${encodeURIComponent(job.job_id)}`;
      const statusCell = document.createElement("td");
      statusCell.append(companyJobStatus(job));
      const actionWrap = document.createElement("div");
      actionWrap.className = "company-job-actions";
      actionWrap.append(edit);
      ["ACTIVE", "CLOSED", "HIDDEN"].filter((value) => value !== job.status).forEach((value) => {
        const buttonClass = value === "ACTIVE"
          ? "company-job-action--success"
          : value === "CLOSED" ? "company-job-action--warning" : "company-job-action--neutral";
        const button = companyText(
          "button",
          `btn btn-sm company-job-action ${buttonClass}`,
          value === "ACTIVE" ? "Mở lại" : value === "CLOSED" ? "Đóng" : "Ẩn",
        );
        button.type = "button";
        button.addEventListener("click", async () => {
          try {
            await UniCareerAPI.jobs.setStatus(job.job_id, value);
            initializeCompanyJobs(page);
          } catch (error) {
            alert(error.message);
          }
        });
        actionWrap.append(button);
      });
      const remove = companyText("button", "btn btn-sm company-job-action company-job-action--danger", "Xóa");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!confirm("Xóa tin tuyển dụng này và các đơn liên quan?")) return;
        try {
          await UniCareerAPI.jobs.remove(job.job_id);
          initializeCompanyJobs(page);
        } catch (error) {
          alert(error.message);
        }
      });
      actionWrap.append(remove);
      actions.append(actionWrap);
      row.append(
        titleCell,
        companyText("td", "", companyDate(job.created_at)),
        companyText("td", "", job.application_count),
        statusCell,
        actions,
      );
      body.append(row);
    });
    renderPortalPagination(pagination, page, jobs.length, pageSize, initializeCompanyJobs);
  } catch (error) {
    const count = document.querySelector(".portal-panel__heading .portal-pill");
    if (count) count.textContent = "— tin";
    if (pagination) pagination.hidden = true;
    body.replaceChildren(emptyTableRow(5, error.message));
  }
}

function emptyTableRow(columnCount, message) {
  const row = document.createElement("tr");
  const cell = companyText("td", "", message);
  cell.colSpan = columnCount;
  row.append(cell);
  return row;
}

function readJobForm() {
  return {
    title: document.getElementById("job-title").value.trim(),
    job_type: jobTypeFromControl(document.getElementById("job-type")),
    location: document.getElementById("job-location").value.trim(),
    salary_range: document.getElementById("job-salary").value.trim(),
    deadline: document.getElementById("job-deadline").value,
    experience_level: document.getElementById("job-experience").value.trim(),
    description: document.getElementById("job-description").value.trim(),
    requirements: document.getElementById("job-requirements").value.trim(),
  };
}

function fillJobForm(job) {
  document.getElementById("job-title").value = job.title;
  const type = document.getElementById("job-type");
  const typeText = { FULL_TIME: "Toàn thời gian", PART_TIME: "Bán thời gian", INTERNSHIP: "Thực tập" }[job.job_type];
  const option = Array.from(type.options).find((item) => item.value === job.job_type || item.textContent.trim() === typeText);
  if (option) type.value = option.value || option.textContent;
  document.getElementById("job-location").value = job.location || "";
  document.getElementById("job-salary").value = job.salary_range || "";
  document.getElementById("job-deadline").value = String(job.deadline).slice(0, 10);
  document.getElementById("job-experience").value = job.experience_level || "";
  document.getElementById("job-description").value = job.description;
  document.getElementById("job-requirements").value = job.requirements;
}

function initializeJobForms() {
  const createForm = document.getElementById("post-job-form");
  if (createForm) {
    createForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = createForm.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        await UniCareerAPI.jobs.create(readJobForm());
        setCompanyFeedback("job-form-status", "Tin đã được gửi và đang chờ quản trị viên kiểm duyệt.");
        window.location.href = "manage-jobs.html";
      } catch (error) {
        setCompanyFeedback("job-form-status", error.message, true);
      } finally {
        button.disabled = false;
      }
    });
  }

  const editForm = document.getElementById("edit-job-form");
  if (!editForm) return;
  const params = new URLSearchParams(location.search);
  const jobId = params.get("job_id") || params.get("id");
  if (!jobId || !/^\d+$/.test(jobId)) {
    setCompanyFeedback("job-form-status", "Thiếu mã tin tuyển dụng hợp lệ.", true);
    editForm.querySelector('button[type="submit"]').disabled = true;
    return;
  }
  UniCareerAPI.jobs.get(jobId).then((job) => {
    fillJobForm(job);
    document.getElementById("edit-job-title").textContent = `Chỉnh sửa: ${job.title}`;
    document.getElementById("edit-job-summary").textContent = `Trạng thái kiểm duyệt: ${statusLabel(job.approval_status)[0]}.`;
    const badge = document.getElementById("edit-job-status");
    badge.textContent = statusLabel(job.status)[0];
    badge.className = `status ${statusLabel(job.status)[1]}`;
    editForm.querySelector('button[type="submit"]').disabled = false;
  }).catch((error) => {
    setCompanyFeedback("job-form-status", error.message, true);
    editForm.querySelector('button[type="submit"]').disabled = true;
  });
  editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = editForm.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await UniCareerAPI.jobs.update(jobId, readJobForm());
      setCompanyFeedback("job-form-status", "Đã lưu nội dung. Tin vẫn giữ trạng thái kiểm duyệt hiện tại.");
      window.location.href = "manage-jobs.html";
    } catch (error) {
      setCompanyFeedback("job-form-status", error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

async function initializeCompanyApplications() {
  const body = document.querySelector(".portal-table tbody");
  if (!body || !location.pathname.endsWith("/applications.html")) return;
  const previewDialog = document.getElementById("cv-preview-dialog");
  const previewTitle = document.getElementById("cv-preview-title");
  const previewStatus = document.getElementById("cv-preview-status");
  const previewFrame = document.getElementById("cv-preview-frame");
  const previewFallback = document.getElementById("cv-preview-fallback");
  const previewClose = document.getElementById("cv-preview-close");
  const previewDownload = document.getElementById("cv-preview-download");
  let previewRequestId = 0;
  let previewObjectUrl = null;
  let activePreviewApplication = null;
  function clearPreview() {
    if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = null;
    if (previewFrame) {
      previewFrame.removeAttribute("src");
      previewFrame.hidden = true;
    }
  }
  previewClose?.addEventListener("click", () => previewDialog?.close());
  previewDialog?.addEventListener("close", () => {
    previewRequestId += 1;
    clearPreview();
    activePreviewApplication = null;
  });
  previewDownload?.addEventListener("click", async () => {
    if (!activePreviewApplication) return;
    try {
      const filename = activePreviewApplication.cv_type === "builder"
        ? `${activePreviewApplication.cv_title}.html`
        : activePreviewApplication.cv_title;
      await UniCareerAPI.company.downloadCV(activePreviewApplication.cv_id, filename);
    } catch (error) {
      if (previewStatus) {
        previewStatus.hidden = false;
        previewStatus.textContent = error.message;
      }
    }
  });
  async function openCVPreview(application) {
    if (!previewDialog || !previewTitle || !previewStatus || !previewFrame || !previewFallback) {
      alert("Không tìm thấy cửa sổ xem trước CV.");
      return;
    }
    const requestId = ++previewRequestId;
    activePreviewApplication = application;
    clearPreview();
    previewTitle.textContent = application.cv_title || "Xem trước CV";
    previewStatus.textContent = "Đang tải CV để xem trước...";
    previewStatus.hidden = false;
    previewFallback.hidden = true;
    if (!previewDialog.open) previewDialog.showModal();
    try {
      const blob = await UniCareerAPI.company.previewCV(application.cv_id);
      if (requestId !== previewRequestId || !previewDialog.open) return;
      const contentType = blob.type.toLowerCase();
      if (!contentType.includes("application/pdf") && !contentType.includes("text/html")) {
        previewStatus.textContent = "Định dạng này chưa thể xem trực tiếp. Bạn có thể tải CV về.";
        previewFallback.hidden = false;
        return;
      }
      previewObjectUrl = URL.createObjectURL(blob);
      previewFrame.title = `Bản xem trước: ${application.cv_title || "CV ứng viên"}`;
      if (contentType.includes("text/html")) previewFrame.setAttribute("sandbox", "");
      else previewFrame.removeAttribute("sandbox");
      previewFrame.src = previewObjectUrl;
      previewFrame.hidden = false;
      previewStatus.hidden = true;
    } catch (error) {
      if (requestId !== previewRequestId) return;
      previewStatus.textContent = error.message;
      previewStatus.hidden = false;
    }
  }
  const filters = {
    query: document.getElementById("applicant-query"),
    job: document.getElementById("application-job"),
    status: document.getElementById("application-status"),
  };
  let company;
  let applications;
  let jobs;
  const pagination = document.getElementById("company-applications-pagination");
  const pageSize = 10;
  let currentPage = 1;
  try {
    company = await UniCareerAPI.company.getProfile();
    [applications, jobs] = await Promise.all([
      UniCareerAPI.company.listApplications(company.company_id),
      listAllCompanyJobs(),
    ]);
  } catch (error) {
    body.replaceChildren(emptyTableRow(5, error.message));
    const pill = document.querySelector(".portal-panel__heading .portal-pill");
    if (pill) pill.textContent = "— hồ sơ";
    markCompanyStatsUnavailable();
    return;
  }
  const jobFilter = filters.job;
  if (jobFilter) {
    jobFilter.replaceChildren(new Option("Tất cả tin của tôi", ""));
    jobs.forEach((job) => jobFilter.add(new Option(job.title, String(job.job_id))));
  }
  function render(page = currentPage) {
    currentPage = page;
    const query = filters.query?.value.trim().toLocaleLowerCase("vi") || "";
    const selectedJob = filters.job?.value || "";
    const selectedStatus = filters.status?.selectedIndex > 0
      ? filters.status.value || filters.status.options[filters.status.selectedIndex].textContent.trim()
      : "";
    const visible = applications.filter((app) => {
      const statusText = filters.status?.options[filters.status.selectedIndex]?.textContent.trim();
      const statusMatch = !selectedStatus || app.status === selectedStatus
        || statusLabel(app.status)[0] === statusText;
      return (!selectedJob || String(app.job_id) === selectedJob)
        && statusMatch
        && (!query || `${app.candidate_name || ""} ${app.candidate_email} ${app.candidate_university || ""} ${app.candidate_major || ""} ${app.candidate_skills || ""} ${app.job_title}`.toLocaleLowerCase("vi").includes(query));
    });
    currentPage = Math.min(currentPage, Math.max(1, Math.ceil(visible.length / pageSize)));
    body.replaceChildren();
    if (!visible.length) {
      body.append(emptyTableRow(5, applications.length
        ? "Không có hồ sơ phù hợp."
        : "Chưa có ứng viên ứng tuyển."));
    }
    visible.slice((currentPage - 1) * pageSize, currentPage * pageSize).forEach((app) => {
      const row = document.createElement("tr");
      const person = document.createElement("td");
      person.className = "company-applicant-cell";
      const name = app.candidate_name || "Ứng viên";
      const initials = name.split(/\s+/).slice(0, 2)
        .map((part) => part.slice(0, 1)).join("").toLocaleUpperCase("vi");
      const applicant = document.createElement("div");
      applicant.className = "company-applicant";
      applicant.append(companyText("span", "company-applicant__avatar", initials));
      const details = document.createElement("div");
      details.className = "company-applicant__details";
      details.append(companyText("strong", "", name));
      details.append(companyText("small", "", app.candidate_email));
      const education = [app.candidate_university, app.candidate_major].filter(Boolean).join(" · ");
      if (education) details.append(companyText("small", "", education));
      if (app.candidate_skills) {
        details.append(companyText("small", "company-applicant__skills", `Kỹ năng: ${app.candidate_skills}`));
      }
      applicant.append(details);
      person.append(applicant);
      const statusCell = document.createElement("td");
      const [label, className] = statusLabel(app.status);
      statusCell.append(companyText("span", `status ${className}`, label));
      const actions = document.createElement("td");
      const actionGroup = document.createElement("div");
      actionGroup.className = "company-applicant-actions";
      if (app.cv_id) {
        const preview = companyText(
          "button",
          "btn btn-sm company-applicant-action company-applicant-action--cv",
          "Xem CV",
        );
        preview.type = "button";
        preview.addEventListener("click", async () => {
          await openCVPreview(app);
        });
        actionGroup.append(preview);
      } else {
        actionGroup.append(companyText("span", "muted", "CV không còn"));
      }
      const select = document.createElement("select");
      select.className = "company-applicant-status-select";
      if (app.status === "PENDING") {
        const pending = new Option(statusLabel("PENDING")[0], "PENDING");
        pending.selected = true;
        pending.disabled = true;
        select.add(pending);
      }
      ["REVIEWING", "ACCEPTED", "REJECTED"].forEach((value) => {
        const option = new Option(statusLabel(value)[0], value);
        option.selected = value === app.status;
        select.add(option);
      });
      const save = companyText(
        "button",
        "btn btn-sm company-applicant-action company-applicant-action--update",
        "Cập nhật",
      );
      save.type = "button";
      save.disabled = ["ACCEPTED", "REJECTED"].includes(app.status);
      save.addEventListener("click", async () => {
        save.disabled = true;
        try {
          await UniCareerAPI.company.updateApplication(company.company_id, app.application_id, select.value);
          app.status = select.value;
          render();
        } catch (error) {
          alert(error.message);
          save.disabled = false;
        }
      });
      actionGroup.append(select, save);
      actions.append(actionGroup);
      const jobTitle = companyText("td", "", app.job_title);
      const appliedAt = companyText("td", "", companyDate(app.applied_at));
      row.append(
        person,
        jobTitle,
        appliedAt,
        statusCell,
        actions,
      );
      body.append(row);
    });
    const pill = document.querySelector(".portal-panel__heading .portal-pill");
    if (pill) pill.textContent = `${applications.length} hồ sơ`;
    const statValues = document.querySelectorAll(".portal-stats .portal-stat__value");
    if (statValues[0]) statValues[0].textContent = String(applications.length);
    if (statValues[1]) statValues[1].textContent = String(applications.filter((item) => item.status === "PENDING").length);
    if (statValues[2]) statValues[2].textContent = String(applications.filter((item) => item.status === "REVIEWING").length);
    if (statValues[3]) statValues[3].textContent = String(applications.filter((item) => item.status === "ACCEPTED").length);
    renderPortalPagination(pagination, currentPage, visible.length, pageSize, render);
  }
  [filters.query, filters.job, filters.status].filter(Boolean).forEach((control) => {
    control.addEventListener("input", () => render(1));
    control.addEventListener("change", () => render(1));
  });
  render();
}

async function initializeCompanyDashboard() {
  if (!location.pathname.endsWith("/dashboard.html") || !location.pathname.includes("/company/")) return;
  try {
    const company = await UniCareerAPI.company.getProfile();
    const jobs = await UniCareerAPI.jobs.list({ limit: 100 });
    const apps = await UniCareerAPI.company.listApplications(company.company_id);
    const values = document.querySelectorAll(".portal-stats .portal-stat__value");
    if (values[0]) values[0].textContent = String(jobs.filter((job) => job.status === "ACTIVE").length);
    if (values[1]) values[1].textContent = String(apps.length);
    if (values[2]) values[2].textContent = String(apps.filter((app) => app.status === "REVIEWING").length);
    if (values[3]) values[3].textContent = String(apps.filter((app) => app.status === "ACCEPTED").length);
    const name = document.querySelector(".portal-heading p");
    if (name) name.textContent = `Theo dõi tin tuyển dụng và hồ sơ ứng viên tại ${company.company_name}.`;
    const body = document.querySelector(".portal-table tbody");
    if (body) {
      body.replaceChildren();
      jobs.slice(0, 5).forEach((job) => {
        const row = document.createElement("tr");
        const statusCell = companyText("td", "company-dashboard__status", "");
        statusCell.append(companyJobStatus(job));
        row.append(
          companyText("td", "", `${job.title} · ${job.location || "—"}`),
          statusCell,
        );
        row.append(companyText("td", "", job.application_count));
        body.append(row);
      });
      if (!jobs.length) body.append(emptyTableRow(3, "Chưa có tin tuyển dụng."));
    }
  } catch (error) {
    markCompanyStatsUnavailable();
    const body = document.querySelector(".portal-table tbody");
    if (body) body.replaceChildren(emptyTableRow(3, error.message));
    const summary = document.querySelector(".portal-heading p");
    if (summary) {
      summary.textContent = error.status === 404
        ? "Hãy cập nhật hồ sơ doanh nghiệp để bắt đầu."
        : "Không thể tải số liệu tuyển dụng.";
    }
    const message = document.querySelector(".portal-help");
    if (message) {
      message.textContent = error.status === 404
        ? "Hãy cập nhật hồ sơ doanh nghiệp để xem số liệu tuyển dụng."
        : error.message;
    }
  }
}
