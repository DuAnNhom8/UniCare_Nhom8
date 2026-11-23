/* Trang danh sách và chi tiết việc làm: hoàn toàn lấy dữ liệu từ FastAPI/MySQL. */
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("public-job-list")) initJobList();
  if (document.getElementById("public-job-detail")) initJobDetail();
  if (document.getElementById("application-form")) initApplicationForm();
  if (document.getElementById("application-history")) initApplicationHistory();
  if (document.getElementById("cv-upload-form")) initCVManager();
  updateCandidateSessionNav();
});

const JOB_TYPE_LABELS = {
  FULL_TIME: "Toàn thời gian", PART_TIME: "Bán thời gian", INTERNSHIP: "Thực tập",
};
const PAGE_SIZE = 12;

function formatJobDate(value) {
  if (!value) return "Chưa xác định";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

function textElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text ?? "";
  return element;
}

function makeJobCard(job) {
  const article = textElement("article", "job-card card");
  const logo = textElement("div", "company-logo", (job.company_name || "U").charAt(0).toUpperCase());
  const content = document.createElement("div");
  content.append(textElement("p", "company-name", job.company_name || "Doanh nghiệp"));

  const heading = document.createElement("h3");
  const jobLink = textElement("a", "", job.title);
  jobLink.href = `job-detail.html?id=${encodeURIComponent(job.job_id)}`;
  heading.append(jobLink);
  content.append(heading);

  const meta = textElement("div", "job-meta");
  [ `⌖ ${job.location || "Chưa cập nhật"}`,
    `◷ ${JOB_TYPE_LABELS[job.job_type] || "Khác"}`,
    job.salary_range || "Thỏa thuận" ].forEach((item) => meta.append(textElement("span", "", item)));
  content.append(meta);

  const action = textElement("div", "job-actions");
  const detail = textElement("a", "btn btn-outline", "Xem chi tiết");
  detail.href = jobLink.href;
  action.append(detail, textElement("span", "deadline", `Hạn: ${formatJobDate(job.deadline)}`));
  article.append(logo, content, action);
  return article;
}

function initJobList() {
  const form = document.getElementById("job-search-form");
  const query = form.querySelector('input[name="q"]');
  const heroLocation = form.querySelector('select[name="location"]');
  const type = document.getElementById("job-type");
  const place = document.getElementById("job-place");
  const salary = document.getElementById("job-salary");
  const sort = document.getElementById("job-sort");
  const list = document.getElementById("public-job-list");
  const count = document.querySelector("[data-job-count]");
  const feedback = document.getElementById("job-feedback");
  const moreButton = document.getElementById("job-load-more");
  const filterToggle = document.querySelector(".mobile-filter-trigger");
  const filters = document.getElementById("job-filters");
  let controller = null;
  let nextSkip = 0;
  let total = 0;
  let debounceTimer;

  const url = new URLSearchParams(location.search);
  query.value = url.get("keyword") || "";
  for (const [select, key] of [[heroLocation, "location"], [place, "location"],
    [type, "job_type"], [salary, "salary"], [sort, "sort"]]) {
    const requested = url.get(key);
    if (requested && Array.from(select.options).some((option) => option.value === requested)) {
      select.value = requested;
    }
  }

  function params() {
    return {
      keyword: query.value.trim(),
      location: place.value || heroLocation.value,
      job_type: type.value,
      salary: salary.value,
      sort: sort.value,
    };
  }

  function syncUrl() {
    const clean = new URLSearchParams();
    Object.entries(params()).forEach(([key, value]) => {
      if (value && !(key === "sort" && value === "latest")) clean.set(key, value);
    });
    const qs = clean.toString();
    history.replaceState(null, "", `${location.pathname}${qs ? `?${qs}` : ""}${location.hash}`);
  }

  async function load(reset = true) {
    if (controller) controller.abort();
    controller = new AbortController();
    const signal = controller.signal;
    const skip = reset ? 0 : nextSkip;
    if (reset) {
      nextSkip = 0;
      list.replaceChildren();
      syncUrl();
    }
    feedback.hidden = false;
    feedback.textContent = "Đang tải danh sách việc làm...";
    moreButton.hidden = true;
    try {
      const result = await window.UniCareerAPI.listJobs({ ...params(), skip, limit: PAGE_SIZE }, { signal });
      if (signal.aborted) return;
      total = result.total;
      result.items.forEach((job) => list.append(makeJobCard(job)));
      nextSkip = skip + result.items.length;
      count.textContent = `${total} cơ hội đang tuyển`;
      feedback.hidden = total !== 0;
      if (total === 0) feedback.textContent = "Không tìm thấy việc làm phù hợp. Hãy thử thay đổi bộ lọc.";
      moreButton.hidden = nextSkip >= total;
    } catch (error) {
      if (error.name === "AbortError") return;
      feedback.hidden = false;
      feedback.textContent = error.message;
      count.textContent = "Không tải được danh sách";
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    load();
    document.getElementById("job-list").scrollIntoView({ behavior: "smooth" });
  });
  query.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => load(), 350);
  });
  heroLocation.addEventListener("change", () => {
    place.value = Array.from(place.options).some((opt) => opt.value === heroLocation.value) ? heroLocation.value : "";
    load();
  });
  place.addEventListener("change", () => {
    heroLocation.value = Array.from(heroLocation.options).some((opt) => opt.value === place.value) ? place.value : "";
    load();
  });
  [type, salary, sort].forEach((control) => control.addEventListener("change", () => load()));
  moreButton.addEventListener("click", () => load(false));
  filterToggle?.addEventListener("click", () => {
    const open = filters.classList.toggle("is-open");
    filterToggle.setAttribute("aria-expanded", String(open));
  });
  load();
}

async function initJobDetail() {
  const params = new URLSearchParams(location.search);
  const id = params.get("id");
  const loading = document.getElementById("job-detail-feedback");
  const content = document.getElementById("public-job-detail");
  if (!id || !/^\d+$/.test(id) || Number(id) < 1) {
    loading.textContent = "Đường dẫn không hợp lệ. Hãy chọn một công việc từ danh sách.";
    return;
  }
  try {
    const job = await window.UniCareerAPI.getJob(id);
    const fields = {
      "job-title": job.title,
      "job-company": job.company_name || "Doanh nghiệp",
      "job-logo": (job.company_name || "U").charAt(0).toUpperCase(),
      "job-summary": job.experience_level || "Cơ hội nghề nghiệp",
      "job-location": `⌖ ${job.location || "Chưa cập nhật"}`,
      "job-type": `◷ ${JOB_TYPE_LABELS[job.job_type] || "Khác"}`,
      "job-salary": job.salary_range || "Thỏa thuận",
      "job-description": job.description,
      "job-requirements": job.requirements,
      "job-deadline": formatJobDate(job.deadline),
      "job-type-aside": JOB_TYPE_LABELS[job.job_type] || "Khác",
      "job-experience": job.experience_level || "Không yêu cầu",
      "job-location-aside": job.location || "Chưa cập nhật",
      "job-company-description": job.company_description || "Chưa có giới thiệu doanh nghiệp.",
    };
    Object.entries(fields).forEach(([field, value]) => {
      document.getElementById(field).textContent = value;
    });
    document.querySelectorAll("[data-apply-link]").forEach((anchor) => {
      anchor.href = `apply-job.html?id=${encodeURIComponent(job.job_id)}`;
    });
    document.title = `${job.title} | UniCareer`;
    loading.hidden = true;
    content.hidden = false;
  } catch (error) {
    loading.textContent = error.message;
  }
}


function showSessionError(target, error, link = true) {
  target.replaceChildren();
  const span = textElement('span', 'is-error', error.message);
  target.append(span);
  if (link && error.status === 401) {
    target.append(document.createTextNode(' '));
    const login = textElement('a', '', 'Đăng nhập ngay');
    login.href = `../auth/login.html?next=${encodeURIComponent(location.pathname + location.search)}`;
    target.append(login);
  }
}

function updateCandidateSessionNav() {
  const loginLink = document.querySelector('.nav-side a[href="../auth/login.html"]');
  if (!loginLink || !window.UniCareerAPI?.hasSession()) return;
  loginLink.textContent = 'Đăng xuất';
  loginLink.href = '#';
  loginLink.addEventListener('click', (event) => {
    event.preventDefault();
    UniCareerAPI.signOut();
    location.reload();
  });
}

async function initApplicationForm() {
  const form = document.getElementById('application-form');
  const feedback = document.getElementById('apply-feedback');
  const state = document.getElementById('apply-state');
  const select = document.getElementById('cv-select');
  const submit = document.getElementById('apply-submit');
  const id = new URLSearchParams(location.search).get('id');
  if (!id || !/^\d+$/.test(id) || Number(id) <= 0) {
    feedback.textContent = 'Thiếu mã công việc. Hãy chọn việc làm từ danh sách.';
    state.textContent = 'Không hợp lệ';
    return;
  }
  try {
    const job = await UniCareerAPI.getJob(id);
    const title = `Ứng tuyển ${job.title}`;
    document.getElementById('apply-job-title').textContent = title;
    document.getElementById('apply-job-company').textContent = job.company_name || 'Doanh nghiệp';
    document.getElementById('apply-job-position').textContent = job.title;
    document.getElementById('apply-job-company-location').textContent = ` · ${job.company_name || 'Doanh nghiệp'} · ${job.location || 'Chưa cập nhật'}`;
    document.getElementById('apply-job-meta').textContent = `${JOB_TYPE_LABELS[job.job_type] || 'Khác'} · ${job.salary_range || 'Thỏa thuận'}`;
    document.getElementById('apply-job-logo').textContent = (job.company_name || 'U').charAt(0);
    for (const field of ['apply-job-breadcrumb', 'apply-job-view-link']) {
      document.getElementById(field).href = `job-detail.html?id=${encodeURIComponent(job.job_id)}`;
    }
    document.title = `${title} | UniCareer`;
    const user = await UniCareerAPI.getProfile();
    document.getElementById('apply-account').textContent = user.email;
    if (user.role !== 'CANDIDATE') {
      state.textContent = 'Không đủ quyền';
      feedback.textContent = 'Chỉ ứng viên được nộp đơn.';
      return;
    }
    const check = await UniCareerAPI.checkApplication(id);
    if (check.applied) {
      state.textContent = 'Đã nộp đơn';
      feedback.textContent = 'Bạn đã ứng tuyển công việc này. Mỗi ứng viên chỉ được nộp một đơn cho mỗi việc làm.';
      document.getElementById('apply-next').hidden = false;
      return;
    }
    const cvs = await UniCareerAPI.listCVs();
    cvs.forEach((cv) => {
      const option = new Option(cv.title, String(cv.cv_id));
      select.add(option);
    });
    state.textContent = 'Có thể ứng tuyển';
    feedback.textContent = cvs.length ? 'Chọn CV đã lưu hoặc tải lên CV PDF mới.' : 'Bạn chưa có CV. Hãy tải lên CV PDF để gửi đơn.';
    form.hidden = false;
  } catch (error) {
    state.textContent = 'Không thể ứng tuyển';
    showSessionError(feedback, error);
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    submit.disabled = true;
    feedback.classList.remove('is-error', 'is-success');
    feedback.textContent = 'Đang gửi hồ sơ...';
    try {
      let cvId = Number(select.value);
      const file = document.getElementById('cv-upload').files[0];
      if (file) {
        if (!file.name.toLowerCase().endsWith('.pdf') || file.size > 5 * 1024 * 1024) {
          throw new Error('CV phải là PDF và không quá 5 MB.');
        }
        feedback.textContent = 'Đang tải CV lên...';
        const saved = await UniCareerAPI.uploadCV(file);
        cvId = saved.cv_id;
      }
      if (!cvId) throw new Error('Hãy chọn CV đã lưu hoặc tải lên CV mới.');
      await UniCareerAPI.submitApplication({
        job_id: Number(id), cv_id: cvId, cover_letter: document.getElementById('cover-letter').value.trim() || null,
      });
      feedback.textContent = 'Nộp đơn thành công! Bạn có thể xem trạng thái tại trang Đơn ứng tuyển.';
      feedback.classList.add('is-success');
      state.textContent = 'Đã nộp đơn';
      form.hidden = true;
      document.getElementById('apply-next').hidden = false;
    } catch (error) {
      showSessionError(feedback, error);
      feedback.classList.add('is-error');
      if (error.status === 409) {
        form.hidden = true;
        state.textContent = 'Đã nộp đơn';
        document.getElementById('apply-next').hidden = false;
      } else submit.disabled = false;
    }
  });
}

const APPLICATION_STATUS = {
  PENDING: ['Đã tiếp nhận', 'status--received'],
  REVIEWING: ['Đang xem xét', 'status--reviewing'],
  ACCEPTED: ['Đã chấp nhận', 'status--accepted'],
  REJECTED: ['Đã từ chối', 'status--rejected'],
};

function makeApplicationCard(application) {
  const article = textElement('article', 'application-card card');
  const left = document.createElement('div');
  left.append(textElement('p', 'company-name', application.company_name));
  left.append(textElement('h3', '', application.job_title));
  const date = new Date(application.applied_at);
  left.append(textElement('p', 'muted', `Đã nộp ${Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN')} · CV: ${application.cv_title || 'Không còn tệp CV'}`));
  const right = textElement('div', 'application-right');
  const [status, statusClass] = APPLICATION_STATUS[application.status] || [application.status, 'status--received'];
  right.append(textElement('span', `status ${statusClass}`, status));
  const link = textElement('a', 'btn btn-outline btn-sm', 'Xem tin');
  link.href = `job-detail.html?id=${encodeURIComponent(application.job_id)}`;
  right.append(link);
  article.append(left, right);
  return article;
}

async function initApplicationHistory() {
  const list = document.getElementById('application-history');
  const feedback = document.getElementById('applications-feedback');
  const more = document.getElementById('applications-more');
  let nextSkip = 0;
  let total = 0;
  let loading = false;
  async function load() {
    if (loading) return;
    loading = true;
    more.disabled = true;
    feedback.textContent = 'Đang tải đơn ứng tuyển...';
    try {
      const data = await UniCareerAPI.listApplications({ skip: nextSkip, limit: 10 });
      total = data.total;
      data.items.forEach((application) => list.append(makeApplicationCard(application)));
      nextSkip += data.items.length;
      feedback.textContent = total ? `Đã nộp ${total} đơn ứng tuyển.` : 'Bạn chưa ứng tuyển công việc nào.';
      more.hidden = nextSkip >= total;
    } catch (error) {
      showSessionError(feedback, error);
      more.hidden = true;
    } finally {
      loading = false;
      more.disabled = false;
    }
  }
  more.addEventListener('click', load);
  load();
}

async function initCVManager() {
  const form = document.getElementById('cv-upload-form');
  const feedback = document.getElementById('cv-feedback');
  const list = document.getElementById('saved-cvs');
  const button = document.getElementById('cv-upload-submit');
  async function loadCVs() {
    const cvs = await UniCareerAPI.listCVs();
    list.replaceChildren();
    if (!cvs.length) list.append(textElement('p', 'muted', 'Chưa có CV nào.'));
    cvs.forEach((cv) => {
      const row = textElement('div', 'cv-record');
      row.append(textElement('strong', '', cv.title));
      const download = textElement('button', 'btn btn-outline btn-sm', 'Tải về');
      download.type = 'button';
      download.addEventListener('click', async () => {
        try { await UniCareerAPI.downloadCV(cv.cv_id); }
        catch (error) { showSessionError(feedback, error); }
      });
      row.append(download);
      list.append(row);
    });
  }
  try {
    const user = await UniCareerAPI.getProfile();
    if (user.role !== 'CANDIDATE') throw Object.assign(new Error('Chỉ ứng viên được quản lý CV.'), { status: 403 });
    document.getElementById('cv-profile-email').textContent = user.email;
    await loadCVs();
    form.hidden = false;
  } catch (error) { showSessionError(feedback, error); return; }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = document.getElementById('cv-file').files[0];
    if (!file) return;
    button.disabled = true;
    feedback.textContent = 'Đang tải CV...';
    try {
      await UniCareerAPI.uploadCV(file);
      feedback.textContent = 'Đã lưu CV thành công.';
      form.reset();
      await loadCVs();
    } catch (error) { showSessionError(feedback, error); }
    finally { button.disabled = false; }
  });
}
