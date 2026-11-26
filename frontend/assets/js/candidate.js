function initializeCandidatePage() {
  initializePublicJobList();
  initializePublicJobDetail();
  initializeApplicationForm();
  initializeApplicationHistory();
  initializeCandidateProfile();
  initializeCVManager();
}

document.addEventListener("DOMContentLoaded", initializeCandidatePage);
document.addEventListener("unicareer:page-loaded", initializeCandidatePage);

const JOB_TYPE_NAMES = {
  FULL_TIME: "Toàn thời gian",
  PART_TIME: "Bán thời gian",
  INTERNSHIP: "Thực tập",
};

function candidateText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value == null ? "" : String(value);
  return element;
}

function formatDate(value) {
  if (!value) return "Chưa xác định";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

function safeRenderPagination(container, page, total, pageSize, onPageChange) {
  if (typeof window.renderPortalPagination === "function") {
    try {
      window.renderPortalPagination(container, page, total, pageSize, onPageChange);
      return;
    } catch (_) {}
  }
  if (!container) return;
  const pageCount = Math.ceil(total / pageSize);
  container.replaceChildren();
  container.hidden = pageCount <= 1;
  if (pageCount <= 1) return;

  const addButton = (label, targetPage, options = {}) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `portal-page-button${options.active ? " is-active" : ""}`;
    button.textContent = label;
    button.disabled = Boolean(options.disabled);
    if (options.active) button.setAttribute("aria-current", "page");
    if (options.label) button.setAttribute("aria-label", options.label);
    button.addEventListener("click", () => onPageChange(targetPage));
    container.append(button);
  };

  addButton("‹ Trước", page - 1, { disabled: page <= 1, label: "Trang trước" });
  const pages = Array.from(new Set([1, page - 1, page, page + 1, pageCount]))
    .filter((v) => v >= 1 && v <= pageCount)
    .sort((a, b) => a - b);
  let previousPage = 0;
  pages.forEach((value) => {
    if (previousPage && value - previousPage > 1) {
      const ellipsis = document.createElement("span");
      ellipsis.className = "portal-page-ellipsis";
      ellipsis.textContent = "…";
      container.append(ellipsis);
    }
    addButton(String(value), value, { active: value === page, label: `Trang ${value}` });
    previousPage = value;
  });
  addButton("Sau ›", page + 1, { disabled: page >= pageCount, label: "Trang tiếp theo" });
  const summary = document.createElement("span");
  summary.className = "portal-pagination-summary";
  summary.textContent = `Trang ${page}/${pageCount} · ${total} mục`;
  container.append(summary);
}

function selectedJobType(select) {
  if (!select || select.selectedIndex === 0) return "";
  const value = select.value || select.options[select.selectedIndex].textContent;
  if (value.includes("Thực tập")) return "INTERNSHIP";
  if (value.includes("Bán thời gian")) return "PART_TIME";
  if (value.includes("Toàn thời gian")) return "FULL_TIME";
  return value;
}

function selectedText(select) {
  if (!select || select.selectedIndex === 0) return "";
  return select.value || select.options[select.selectedIndex].textContent.trim();
}

function showCandidateError(target, error) {
  if (!target) return;
  target.textContent = error.message;
  target.classList.add("is-error");
  if (error.status === 401) {
    const login = document.createElement("a");
    login.href = `../auth/login.html?next=${encodeURIComponent(location.pathname + location.search)}`;
    login.textContent = " Đăng nhập để tiếp tục.";
    target.append(login);
  }
}

function renderCandidateProfileCard(profile) {
  const displayName = document.getElementById("candidate-display-name");
  const displayEmail = document.getElementById("candidate-display-email");
  const displayStatus = document.getElementById("candidate-display-status");
  const avatar = document.getElementById("candidate-avatar");
  const avatarImage = document.getElementById("candidate-avatar-image");
  const name = profile.full_name?.trim() || "Ứng viên";
  if (displayName) displayName.textContent = name;
  if (avatar) avatar.textContent = name.slice(0, 2).toLocaleUpperCase("vi");
  if (displayEmail) displayEmail.textContent = profile.email || "Chưa cập nhật email";
  if (displayStatus) {
    const labels = {
      OPEN: "Đang tìm việc",
      INTERNSHIP: "Ưu tiên thực tập",
      NOT_LOOKING: "Chưa có nhu cầu",
    };
    displayStatus.textContent = labels[profile.job_search_status] || labels.OPEN;
    displayStatus.className = `status ${profile.job_search_status === "NOT_LOOKING" ? "status--received" : "status--success"}`;
  }
  if (avatarImage) {
    avatarImage.hidden = !profile.avatar_url;
    avatarImage.alt = `Ảnh đại diện của ${name}`;
    avatarImage.onerror = () => {
      avatarImage.hidden = true;
    };
    if (profile.avatar_url) avatarImage.src = profile.avatar_url;
    else avatarImage.removeAttribute("src");
  }
  if (profile.full_name?.trim()) updateCandidateIdentity(profile.full_name);
}

function makeJobCard(job) {
  const card = candidateText("article", "job-card card");
  const logo = candidateText("div", "company-logo", (job.company_name || "U").slice(0, 1).toUpperCase());
  const content = document.createElement("div");
  content.append(candidateText("p", "company-name", job.company_name || "Doanh nghiệp"));
  const title = document.createElement("h3");
  const link = candidateText("a", "", job.title);
  link.href = `job-detail.html?id=${encodeURIComponent(job.job_id)}`;
  title.append(link);
  content.append(title);
  const meta = candidateText("div", "job-meta");
  [
    `⌖ ${job.location || "Chưa cập nhật"}`,
    `◷ ${JOB_TYPE_NAMES[job.job_type] || "Khác"}`,
    job.salary_range || "Thỏa thuận",
  ].forEach((value) => meta.append(candidateText("span", "", value)));
  content.append(meta);
  const actions = candidateText("div", "job-actions");
  const detail = candidateText("a", "btn btn-outline", "Xem chi tiết");
  detail.href = link.href;
  actions.append(detail);
  if (document.body.dataset.portalRole === "candidate") {
    const apply = candidateText("a", "btn", "Ứng tuyển");
    apply.href = `apply-job.html?id=${encodeURIComponent(job.job_id)}`;
    actions.append(apply);
  }
  actions.append(candidateText("span", "deadline", `Hạn: ${formatDate(job.deadline)}`));
  card.append(logo, content, actions);
  return card;
}

function initializePublicJobList() {
  const list = document.querySelector(".job-list");
  const form = document.querySelector(".hero-search");
  if (!list || !form) return;
  const query = form.querySelector('input[type="search"]');
  const heroLocation = form.querySelector("select");
  const type = document.getElementById("job-type");
  const place = document.getElementById("job-place");
  const salary = document.getElementById("job-salary");
  const sort = document.getElementById("job-sort");
  const counter = document.querySelector("[data-job-count]");
  const feedback = document.querySelector(".jobs-empty");
  const pagination = document.getElementById("job-pagination");
  const pageSize = 10;
  let activeRequest;

  async function loadJobs(page = 1) {
    if (activeRequest) activeRequest.abort();
    const requestController = new AbortController();
    activeRequest = requestController;
    list.replaceChildren();
    if (pagination) pagination.hidden = true;
    if (feedback) {
      feedback.hidden = false;
      feedback.textContent = "Đang tải việc làm...";
    }
    try {
      const locationValue = selectedText(place) || selectedText(heroLocation);
      const salaryValue = selectedText(salary);
      const result = await UniCareerAPI.jobs.listPublic({
        keyword: query?.value.trim(),
        location: locationValue && !locationValue.startsWith("Tất cả") ? locationValue : "",
        job_type: selectedJobType(type),
        salary: salaryValue === "negotiable" ? "negotiable" : salaryValue ? "paid" : "",
        sort: selectedText(sort) === "deadline" ? "deadline" : "latest",
        limit: pageSize,
        skip: (page - 1) * pageSize,
      }, { signal: requestController.signal });
      if (activeRequest !== requestController) return;
      result.items.forEach((job) => list.append(makeJobCard(job)));
      if (counter) counter.textContent = `${result.total} cơ hội đang tuyển`;
      if (feedback) {
        feedback.hidden = result.total > 0;
        feedback.textContent = result.total
          ? ""
          : "Không tìm thấy việc làm phù hợp. Hãy thử thay đổi bộ lọc.";
      }
      safeRenderPagination(pagination, page, result.total, pageSize, loadJobs);
    } catch (error) {
      if (error.name === "AbortError" || activeRequest !== requestController) return;
      if (counter) counter.textContent = "Không tải được danh sách";
      if (pagination) pagination.hidden = true;
      showCandidateError(feedback, error);
    } finally {
      if (activeRequest === requestController) activeRequest = null;
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadJobs(1);
  });
  [heroLocation, type, place, salary, sort].filter(Boolean).forEach((control) => {
    control.addEventListener("change", () => loadJobs(1));
  });
  loadJobs(1);
}

async function initializePublicJobDetail() {
  const header = document.querySelector(".detail-header");
  const id = new URLSearchParams(location.search).get("id");
  if (!header || !id) return;
  const feedback = candidateText("p", "portal-help", "Đang tải thông tin công việc...");
  header.before(feedback);
  try {
    const job = await UniCareerAPI.jobs.getPublic(id);
    const main = header.querySelector(".job-header-main");
    const company = main?.querySelector(".company-name");
    const title = main?.querySelector("h1");
    const summary = main?.querySelector(".muted");
    const logo = main?.querySelector(".company-logo");
    if (company) company.textContent = job.company_name || "Doanh nghiệp";
    if (title) title.textContent = job.title;
    if (summary) summary.textContent = job.experience_level || "Cơ hội nghề nghiệp";
    if (logo) logo.textContent = (job.company_name || "U").slice(0, 1).toUpperCase();
    const info = header.querySelectorAll(".detail-info .info-pill");
    if (info[0]) info[0].textContent = `⌖ ${job.location || "Chưa cập nhật"}`;
    if (info[1]) info[1].textContent = `◷ ${JOB_TYPE_NAMES[job.job_type] || "Khác"}`;
    if (info[2]) info[2].textContent = job.salary_range || "Thỏa thuận";
    document.querySelectorAll(".detail-actions a.btn-lg, .detail-sidebar .btn-full").forEach((link) => {
      link.href = `apply-job.html?id=${encodeURIComponent(job.job_id)}`;
    });
    const content = document.querySelector(".detail-content");
    if (content) {
      const prose = content.querySelectorAll(".prose");
      if (prose[0]) prose[0].textContent = job.description;
      if (prose[1]) prose[1].textContent = job.requirements;
      const aside = document.querySelector(".detail-sidebar");
      if (aside) {
        const detailValues = aside.querySelectorAll(".aside-list li strong");
        [formatDate(job.deadline), JOB_TYPE_NAMES[job.job_type] || "Khác", job.experience_level || "Không yêu cầu", job.location || "Chưa cập nhật"]
          .forEach((value, index) => {
            if (detailValues[index]) detailValues[index].textContent = value;
          });
        const companyCard = aside.querySelectorAll(".card")[1];
        const companyDescription = companyCard?.querySelector("p");
        if (companyDescription) companyDescription.textContent = job.company_description || "Chưa có giới thiệu doanh nghiệp.";
      }
    }
    document.title = `${job.title} | UniCareer`;
    feedback.remove();
  } catch (error) {
    feedback.textContent = error.message;
  }
}

async function initializeApplicationForm() {
  const form = document.getElementById("application-form");
  if (!form) return;
  const id = new URLSearchParams(location.search).get("id");
  const feedback = document.getElementById("apply-feedback");
  const state = document.getElementById("apply-state");
  const select = document.getElementById("cv-select");
  const button = document.getElementById("apply-submit");
  form.hidden = true;
  if (!id || !/^\d+$/.test(id)) {
    showCandidateError(feedback, new Error("Thiếu mã công việc. Hãy chọn việc làm từ danh sách."));
    return;
  }
  try {
    const job = await UniCareerAPI.jobs.getPublic(id);
    document.getElementById("apply-job-title").textContent = `Ứng tuyển ${job.title}`;
    document.getElementById("apply-job-company").textContent = job.company_name || "Doanh nghiệp";
    document.getElementById("apply-job-position").textContent = job.title;
    document.getElementById("apply-job-company-location").textContent = `${job.company_name || "Doanh nghiệp"} · ${job.location || "Chưa cập nhật"}`;
    document.getElementById("apply-job-meta").textContent = `${JOB_TYPE_NAMES[job.job_type] || "Khác"} · ${job.salary_range || "Thỏa thuận"}`;
    document.getElementById("apply-job-logo").textContent = (job.company_name || "U").slice(0, 1);
    document.getElementById("apply-job-breadcrumb").href = `job-detail.html?id=${encodeURIComponent(job.job_id)}`;
    document.getElementById("apply-job-view-link").href = `job-detail.html?id=${encodeURIComponent(job.job_id)}`;
    const user = await UniCareerAPI.getMe();
    if (user.role !== "candidate") throw Object.assign(new Error("Chỉ ứng viên được nộp đơn."), { status: 403 });
    const profile = await UniCareerAPI.candidate.getProfile();
    const applicantName = document.getElementById("apply-candidate-name");
    const applicantEmail = document.getElementById("apply-candidate-email");
    const fullName = profile.full_name?.trim() || user.full_name?.trim() || "";
    if (fullName) updateCandidateIdentity(fullName);
    if (applicantName) applicantName.textContent = fullName || "Ứng viên";
    if (applicantEmail) applicantEmail.textContent = user.email;
    const applicantSchool = document.getElementById("apply-candidate-school");
    if (applicantSchool) applicantSchool.textContent = "Thông tin học vấn nằm trong CV đã chọn";
    document.getElementById("apply-email").value = user.email;
    document.getElementById("apply-email").readOnly = true;
    const duplicate = await UniCareerAPI.candidate.checkApplication(id);
    if (duplicate.applied) {
      state.textContent = "Đã ứng tuyển";
      feedback.textContent = "Bạn đã nộp hồ sơ cho công việc này.";
      document.getElementById("apply-next").hidden = false;
      return;
    }
    const cvs = await UniCareerAPI.candidate.listCVs();
    select.replaceChildren(new Option("Chọn CV đã lưu", ""));
    cvs.forEach((cv) => select.add(new Option(cv.title, String(cv.cv_id))));
    const cvSummary = document.getElementById("apply-candidate-cv");
    const updateCvSummary = () => {
      if (cvSummary) cvSummary.textContent = select.options[select.selectedIndex]?.textContent || "Chưa chọn";
    };
    select.addEventListener("change", updateCvSummary);
    state.textContent = "Có thể ứng tuyển";
    feedback.textContent = cvs.length
      ? "Chọn một CV đã nhập trong Hồ sơ CV."
      : "Bạn chưa có CV. Hãy tạo CV trong Hồ sơ CV trước khi ứng tuyển.";
    form.hidden = false;
  } catch (error) {
    state.textContent = "Không thể ứng tuyển";
    showCandidateError(feedback, error);
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    button.disabled = true;
    feedback.textContent = "Đang gửi hồ sơ...";
    feedback.classList.remove("is-error");
    try {
      const cvId = Number(select.value);
      if (!cvId) throw new Error("Hãy chọn CV đã nhập trong Hồ sơ CV.");
      await UniCareerAPI.candidate.apply({
        job_id: Number(id),
        cv_id: cvId,
        cover_letter: document.getElementById("cover-letter").value.trim() || null,
      });
      form.hidden = true;
      state.textContent = "Đã nộp hồ sơ";
      feedback.textContent = "Nộp đơn thành công. Bạn có thể theo dõi trạng thái tại trang Đơn ứng tuyển.";
      document.getElementById("apply-next").hidden = false;
    } catch (error) {
      showCandidateError(feedback, error);
      if (error.status === 409) {
        form.hidden = true;
        state.textContent = "Đã ứng tuyển";
        document.getElementById("apply-next").hidden = false;
      }
    } finally {
      button.disabled = false;
    }
  });
}

const APPLICATION_LABELS = {
  PENDING: ["Đã tiếp nhận", "status--received"],
  REVIEWING: ["Đang xem xét", "status--reviewing"],
  ACCEPTED: ["Đã chấp nhận", "status--accepted"],
  REJECTED: ["Đã từ chối", "status--rejected"],
};

async function initializeApplicationHistory() {
  const list = document.getElementById("application-history");
  if (!list) return;
  const feedback = document.getElementById("applications-feedback");
  const pagination = document.getElementById("applications-pagination");
  const pageSize = 10;

  async function loadApplications(page = 1) {
    list.replaceChildren();
    if (pagination) pagination.hidden = true;
    try {
      const result = await UniCareerAPI.candidate.listApplications({
        skip: (page - 1) * pageSize,
        limit: pageSize,
      });
      result.items.forEach((application) => {
        const card = candidateText("article", "application-card card");
        const left = document.createElement("div");
        left.append(candidateText("p", "company-name", application.company_name));
        left.append(candidateText("h3", "", application.job_title));
        const applied = new Date(application.applied_at);
        left.append(candidateText(
          "p", "muted",
          `Đã nộp ${Number.isNaN(applied.getTime()) ? "—" : applied.toLocaleDateString("vi-VN")} · CV: ${application.cv_title || "Không còn CV"}`,
        ));
        const right = candidateText("div", "application-right");
        const [label, className] = APPLICATION_LABELS[application.status] || [application.status, "status--received"];
        right.append(candidateText("span", `status ${className}`, label));
        const link = candidateText("a", "btn btn-outline btn-sm", "Xem tin");
        link.href = `job-detail.html?id=${encodeURIComponent(application.job_id)}`;
        right.append(link);
        card.append(left, right);
        list.append(card);
      });
      feedback.textContent = result.total ? `Bạn đã nộp ${result.total} đơn.` : "Bạn chưa ứng tuyển công việc nào.";
      safeRenderPagination(pagination, page, result.total, pageSize, loadApplications);
    } catch (error) {
      showCandidateError(feedback, error);
    }
  }
  await loadApplications();
}

async function initializeCandidateProfile() {
  const form = document.getElementById("profile-form");
  const passwordForm = document.getElementById("password-form");
  if (!form && !passwordForm) return;
  const status = document.getElementById("profile-status");
  if (passwordForm) {
    const passwordStatus = document.getElementById("password-status");
    passwordForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const currentPassword = document.getElementById("profile-current-password").value;
      const newPassword = document.getElementById("profile-new-password").value;
      if (newPassword !== document.getElementById("profile-confirm-password").value) {
        passwordStatus.textContent = "Mật khẩu nhập lại chưa khớp.";
        passwordStatus.classList.add("is-error");
        return;
      }
      const button = passwordForm.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        await UniCareerAPI.candidate.changePassword(currentPassword, newPassword);
        passwordForm.reset();
        passwordStatus.textContent = "Đã cập nhật mật khẩu.";
        passwordStatus.classList.remove("is-error");
      } catch (error) {
        showCandidateError(passwordStatus, error);
      } finally {
        button.disabled = false;
      }
    });
  }

  if (form) {
    const fields = {
      full_name: "profile-name",
      email: "profile-email",
      phone: "profile-phone",
      avatar_url: "profile-avatar-url",
      github_url: "profile-github",
      linkedin_url: "profile-linkedin",
      job_search_status: "profile-status-select",
    };
    try {
      const user = await UniCareerAPI.getMe();
      if (user.role !== "candidate") throw new Error("Chỉ ứng viên được cập nhật hồ sơ cá nhân.");
      const profile = await UniCareerAPI.candidate.getProfile();
      profile.full_name = profile.full_name?.trim() || user.full_name?.trim() || "";
      profile.email = user.email;
      renderCandidateProfileCard(profile);
      Object.entries(fields).forEach(([key, id]) => {
        const input = document.getElementById(id);
        if (input) input.value = profile[key] ?? (key === "job_search_status" ? "OPEN" : "");
      });
    } catch (error) {
      showCandidateError(status, error);
      form.querySelector('button[type="submit"]').disabled = true;
      return;
    }
    document.getElementById("profile-avatar-url").addEventListener("input", () => {
      renderCandidateProfileCard({
        full_name: document.getElementById("profile-name").value,
        email: document.getElementById("profile-email").value,
        avatar_url: document.getElementById("profile-avatar-url").value,
        job_search_status: document.getElementById("profile-status-select").value,
      });
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        const values = Object.fromEntries(
          Object.entries(fields).map(([key, id]) => {
            const value = document.getElementById(id).value.trim();
            return [key, value || (key === "full_name" || key === "email" ? value : null)];
          }),
        );
        const profile = await UniCareerAPI.candidate.updateProfile(values);
        renderCandidateProfileCard(profile);
        status.textContent = "Đã cập nhật thông tin tài khoản.";
        status.classList.remove("is-error");
      } catch (error) {
        showCandidateError(status, error);
      } finally {
        button.disabled = false;
      }
    });
  }
}

async function initializeCVManager() {
  const builderForm = document.getElementById("cv-builder-form");
  if (!builderForm) return;
  const status = document.getElementById("cv-status");
  const list = document.getElementById("cv-list");
  const builderStatus = document.getElementById("cv-builder-status");
  const editor = document.getElementById("cv-editor-panel");
  const previewDialog = document.getElementById("cv-preview");
  const previewContent = document.getElementById("cv-preview-content");
  const pagination = document.getElementById("cv-pagination");
  const uploadForm = document.getElementById("cv-upload-form");
  const uploadStatus = document.getElementById("cv-upload-status");
  const pageSize = 10;
  const builderFields = {
    objective: "cv-objective",
    education: "cv-education",
    experience: "cv-experience",
    projects: "cv-projects",
    skills: "cv-skills",
    certifications: "cv-certifications",
  };
  let profile = {};
  let cvs = [];
  let cvPage = 1;

  function setField(id, value) {
    const input = document.getElementById(id);
    if (input) input.value = value || "";
  }

  function openEditor(cv) {
    if (!builderForm || !editor) return;
    builderForm.reset();
    const personal = cv?.personal_info || {};
    const content = cv?.content || {};
    builderForm.dataset.cvId = cv?.cv_id ? String(cv.cv_id) : "";
    setField("cv-title", cv?.title || "");
    setField("cv-full-name", personal.full_name || profile.full_name);
    setField("cv-email", personal.email || profile.email);
    setField("cv-phone", personal.phone || profile.phone);
    setField("cv-github", personal.github_url || profile.github_url);
    setField("cv-linkedin", personal.linkedin_url || profile.linkedin_url);
    Object.entries(builderFields).forEach(([key, id]) => setField(id, content[key]));
    document.getElementById("cv-editor-heading").textContent = cv ? "Chỉnh sửa phiên bản CV" : "Tạo CV theo mẫu";
    editor.hidden = false;
    builderStatus.textContent = "";
    editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderPreview(cv) {
    const personal = cv.personal_info || {};
    const content = cv.content || {};
    previewContent.replaceChildren();
    const name = candidateText("h1", "", personal.full_name || cv.title);
    name.id = "cv-preview-name";
    previewContent.append(name);
    const contact = [personal.email, personal.phone].filter(Boolean).join(" · ");
    if (contact) previewContent.append(candidateText("p", "cv-preview-contact", contact));
    const links = document.createElement("p");
    ["github_url", "linkedin_url"].forEach((key) => {
      const value = personal[key];
      if (!value) return;
      try {
        const url = new URL(value);
        if (!["http:", "https:"].includes(url.protocol)) return;
        const link = candidateText("a", "", key === "github_url" ? "GitHub" : "LinkedIn");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        links.append(link);
      } catch (_) {
        return;
      }
    });
    if (links.childElementCount) previewContent.append(links);
    const labels = {
      objective: "Mục tiêu nghề nghiệp",
      education: "Học vấn",
      experience: "Kinh nghiệm làm việc",
      projects: "Dự án",
      skills: "Kỹ năng",
      certifications: "Chứng chỉ",
    };
    Object.entries(labels).forEach(([key, label]) => {
      if (!content[key]?.trim()) return;
      previewContent.append(candidateText("h2", "", label));
      const paragraph = candidateText("p", "cv-preview-section", content[key]);
      previewContent.append(paragraph);
    });
    previewDialog.showModal();
  }

  function renderCVPage(page = cvPage) {
    cvPage = page;
    list.replaceChildren();
    document.getElementById("cv-count").textContent = `${cvs.length} phiên bản`;
    if (!cvs.length) {
      const empty = candidateText("div", "cv-empty", "Bạn chưa có phiên bản CV. Hãy tạo CV theo mẫu hoặc tải lên tệp PDF/DOCX.");
      list.append(empty);
      safeRenderPagination(pagination, cvPage, 0, pageSize, renderCVPage);
      return;
    }
    cvs.slice((cvPage - 1) * pageSize, cvPage * pageSize).forEach((cv) => {
      const row = candidateText("div", "cv-file-row");
      const isBuilder = cv.cv_type === "builder";
      row.append(candidateText(
        "span",
        `company-logo ${isBuilder ? "company-logo--purple" : "company-logo--orange"}`,
        isBuilder ? "CV" : cv.title.split(".").pop().toUpperCase(),
      ));
      const info = candidateText("div", "cv-file-info");
      info.append(candidateText("strong", "", cv.title));
      info.append(candidateText(
        "span",
        "cv-type-label",
        isBuilder ? "CV đã nhập theo mẫu" : "CV tải lên (PDF/DOCX)",
      ));
      if (cv.description) info.append(candidateText("p", "muted", cv.description));
      const actions = candidateText("div", "cv-actions");
      const download = candidateText("button", "btn btn-outline", isBuilder ? "Tải bản xem" : "Tải CV");
      download.type = "button";
      download.addEventListener("click", async () => {
        try {
          const filename = isBuilder ? `${cv.title}.html` : cv.title;
          await UniCareerAPI.candidate.downloadCV(cv.cv_id, filename);
        } catch (error) {
          showCandidateError(status, error);
        }
      });
      actions.append(download);
      if (isBuilder) {
        const preview = candidateText("button", "btn btn-outline", "Xem trước");
        preview.type = "button";
        preview.addEventListener("click", () => renderPreview(cv));
        const edit = candidateText("button", "btn btn-outline", "Chỉnh sửa");
        edit.type = "button";
        edit.addEventListener("click", () => openEditor(cv));
        actions.append(preview, edit);
      }
      const remove = candidateText("button", "btn btn-outline", "Xóa");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!confirm("Bạn có chắc muốn xóa CV này?")) return;
        try {
          await UniCareerAPI.candidate.deleteCV(cv.cv_id);
          await loadCVs();
          status.textContent = "Đã xóa CV.";
          status.classList.remove("is-error");
        } catch (error) {
          showCandidateError(status, error);
        }
      });
      actions.append(remove);
      row.append(info, actions);
      const aiConsentLabel = document.createElement("label");
      aiConsentLabel.className = "checkline cv-consent";
      const aiConsent = document.createElement("input");
      aiConsent.type = "checkbox";
      aiConsent.checked = cv.allow_ai_analysis;
      aiConsent.addEventListener("change", async () => {
        aiConsent.disabled = true;
        try {
          await UniCareerAPI.candidate.setCVAIConsent(cv.cv_id, aiConsent.checked);
          cv.allow_ai_analysis = aiConsent.checked;
          status.textContent = aiConsent.checked
            ? "Đã cho phép nhà tuyển dụng phân tích CV này bằng AI."
            : "Đã tắt quyền phân tích AI cho CV này.";
          status.classList.remove("is-error");
        } catch (error) {
          aiConsent.checked = !aiConsent.checked;
          showCandidateError(status, error);
        } finally {
          aiConsent.disabled = false;
        }
      });
      aiConsentLabel.append(
        aiConsent,
        candidateText("span", "", "Cho phép nhà tuyển dụng phân tích CV này bằng AI"),
      );
      row.append(aiConsentLabel);
      list.append(row);
    });
    safeRenderPagination(pagination, cvPage, cvs.length, pageSize, renderCVPage);
  }

  async function loadCVs() {
    cvs = await UniCareerAPI.candidate.listCVs();
    cvPage = Math.min(cvPage, Math.max(1, Math.ceil(cvs.length / pageSize)));
    renderCVPage(cvPage);
  }
  try {
    const user = await UniCareerAPI.getMe();
    if (user.role !== "candidate") throw new Error("Chỉ ứng viên được quản lý CV.");
    profile = await UniCareerAPI.candidate.getProfile();
    profile.email = user.email;
    await loadCVs();
  } catch (error) {
    showCandidateError(status, error);
    document.getElementById("cv-create-button").disabled = true;
    const uploadButton = uploadForm?.querySelector('button[type="submit"]');
    if (uploadButton) uploadButton.disabled = true;
    return;
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = document.getElementById("cv-upload-file");
      const file = input.files[0];
      if (!file) return;
      if (file.size > 10 * 1024 * 1024) {
        uploadStatus.textContent = "Tệp CV vượt quá giới hạn 10 MB.";
        uploadStatus.classList.add("is-error");
        return;
      }

      const button = uploadForm.querySelector('button[type="submit"]');
      button.disabled = true;
      uploadStatus.textContent = "Đang tải CV lên...";
      uploadStatus.classList.remove("is-error");
      try {
        const uploadedCV = await UniCareerAPI.candidate.uploadCV(file);
        cvs = [uploadedCV, ...cvs.filter((cv) => cv.cv_id !== uploadedCV.cv_id)];
        cvPage = 1;
        renderCVPage();
        uploadForm.reset();
        uploadStatus.textContent = "Đã tải CV lên. Bạn có thể bật quyền phân tích AI trong danh sách CV.";
      } catch (error) {
        showCandidateError(uploadStatus, error);
      } finally {
        button.disabled = false;
      }
    });
  }

  if (builderForm) {
    document.getElementById("cv-create-button").addEventListener("click", () => openEditor());
    ["cv-editor-cancel", "cv-editor-cancel-bottom"].forEach((id) => {
      document.getElementById(id).addEventListener("click", () => {
        builderForm.reset();
        builderForm.dataset.cvId = "";
        editor.hidden = true;
      });
    });
    builderForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!builderForm.reportValidity()) return;
      const button = builderForm.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        const payload = {
          title: document.getElementById("cv-title").value.trim(),
          personal_info: {
            full_name: document.getElementById("cv-full-name").value.trim(),
            email: document.getElementById("cv-email").value.trim() || null,
            phone: document.getElementById("cv-phone").value.trim() || null,
            github_url: document.getElementById("cv-github").value.trim() || null,
            linkedin_url: document.getElementById("cv-linkedin").value.trim() || null,
          },
          content: Object.fromEntries(
            Object.entries(builderFields).map(([key, id]) => [key, document.getElementById(id).value.trim()]),
          ),
        };
        const cvId = builderForm.dataset.cvId;
        if (cvId) await UniCareerAPI.candidate.updateCV(cvId, payload);
        else await UniCareerAPI.candidate.createCV(payload);
        await loadCVs();
        editor.hidden = true;
        builderStatus.textContent = "";
        status.textContent = cvId ? "Đã cập nhật phiên bản CV." : "Đã tạo phiên bản CV mới.";
        status.classList.remove("is-error");
      } catch (error) {
        showCandidateError(builderStatus, error);
      } finally {
        button.disabled = false;
      }
    });
  }

  if (previewDialog) {
    document.getElementById("cv-preview-close").addEventListener("click", () => previewDialog.close());
    document.getElementById("cv-preview-print").addEventListener("click", () => {
      document.body.classList.add("cv-printing");
      window.print();
    });
    window.addEventListener("afterprint", () => document.body.classList.remove("cv-printing"));
  }
}