function initializeAIMatchingPage() {
  if (document.getElementById("candidate-ai-form")) {
    initializeCandidateAI();
  }
  if (document.getElementById("ai-analyze") && !document.getElementById("candidate-ai-form")) {
    initializeEmployerAI();
  }
}

document.addEventListener("DOMContentLoaded", initializeAIMatchingPage);
document.addEventListener("unicareer:page-loaded", initializeAIMatchingPage);

function aiText(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value == null ? "" : String(value);
  return element;
}

function showAIStatus(message, isError) {
  const status = document.getElementById("ai-status");
  if (!status) return;
  status.textContent = message;
  status.classList.toggle("is-error", Boolean(isError));
}

function renderAIResult(result) {
  const container = document.getElementById("ai-result");
  if (!container) return;
  const match = document.createElement("div");
  match.className = "company-match";

  const score = document.createElement("div");
  score.className = "company-score";
  score.append(aiText("strong", "", `${result.score}%`));
  score.append(aiText("small", "", "Mức độ phù hợp tham khảo"));
  const meter = document.createElement("span");
  meter.className = "meter";
  const fill = document.createElement("i");
  fill.style.width = `${result.score}%`;
  meter.append(fill);
  score.append(meter);

  const details = document.createElement("div");
  details.className = "company-match__skills";
  details.append(aiText("p", "", result.summary));
  [
    ["Kỹ năng phù hợp", result.matched_skills],
    ["Kỹ năng có thể bổ sung", result.missing_skills],
    ["Gợi ý phát triển", result.recommendations],
  ].forEach(([title, items]) => {
    details.append(aiText("h3", "", title));
    const list = document.createElement("div");
    list.className = "company-skills";
    if (items.length) {
      items.forEach((item) => list.append(aiText("span", "company-skill", item)));
    } else {
      list.append(aiText("span", "muted", "Không có mục nào."));
    }
    details.append(list);
  });
  match.append(score, details);

  container.replaceChildren(
    match,
    aiText("p", "portal-help", `Phân tích được lưu · ${result.model} · Chỉ mang tính tham khảo, không phải quyết định tuyển dụng.`),
  );
}

function fillSelect(select, placeholder, items, getValue, getLabel) {
  select.replaceChildren(new Option(placeholder, ""));
  items.forEach((item) => select.add(new Option(getLabel(item), String(getValue(item)))));
}

async function initializeCandidateAI() {
  const form = document.getElementById("candidate-ai-form");
  const jobSelect = document.getElementById("ai-job");
  const cvSelect = document.getElementById("ai-cv");
  const button = document.getElementById("ai-analyze");
  try {
    const [jobs, cvs, profile] = await Promise.all([
      UniCareerAPI.jobs.listPublic({ limit: 50 }),
      UniCareerAPI.candidate.listCVs(),
      UniCareerAPI.candidate.getProfile(),
    ]);
    const role = document.querySelector(".portal-sidebottom small");
    if (role) role.textContent = "Sinh viên";
    if (profile.full_name?.trim()) updateCandidateIdentity(profile.full_name);
    fillSelect(jobSelect, "Chọn công việc", jobs.items, (job) => job.job_id, (job) =>
      `${job.title} · ${job.company_name || "Doanh nghiệp"}`);
    fillSelect(cvSelect, "Chọn CV đã lưu", cvs, (cv) => cv.cv_id, (cv) =>
      `${cv.title} · ${cv.cv_type === "builder" ? "CV theo mẫu" : "CV tải lên"}`);
    button.disabled = !jobs.items.length || !cvs.length;
    if (!jobs.items.length) showAIStatus("Hiện không có tin tuyển dụng phù hợp để phân tích.", true);
    else if (!cvs.length) showAIStatus("Tạo CV theo mẫu hoặc tải CV PDF/DOCX lên trước khi dùng chức năng phân tích AI.", true);
  } catch (error) {
    showAIStatus(error.message, true);
    button.disabled = true;
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    button.disabled = true;
    showAIStatus("Đang gửi CV đến Gemini để phân tích...");
    try {
      const result = await UniCareerAPI.ai.analyzeCandidateCV({
        cv_id: Number(cvSelect.value),
        job_id: Number(jobSelect.value),
        consent_to_gemini: document.getElementById("ai-consent").checked,
      });
      renderAIResult(result);
      showAIStatus("Đã phân tích và lưu kết quả.");
    } catch (error) {
      showAIStatus(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

async function initializeEmployerAI() {
  const jobSelect = document.getElementById("ai-job");
  const applicantSelect = document.getElementById("ai-candidate");
  const button = document.getElementById("ai-analyze");
  try {
    const company = await UniCareerAPI.company.getProfile();
    const applications = await UniCareerAPI.company.listApplications(company.company_id);
    const jobs = await UniCareerAPI.jobs.list({ limit: 100 });
    fillSelect(jobSelect, "Chọn công việc", jobs, (job) => job.job_id, (job) => job.title);

    const companyName = document.querySelector(".portal-sidebottom strong");
    const companyRole = document.querySelector(".portal-sidebottom small");
    const avatar = document.querySelector(".portal-avatar");
    if (companyName) companyName.textContent = company.company_name;
    if (companyRole) companyRole.textContent = "Nhà tuyển dụng";
    if (avatar) avatar.textContent = company.company_name.slice(0, 2).toLocaleUpperCase("vi");

    function updateApplicants() {
      const selectedJob = jobSelect.value;
      const matching = applications.filter((application) =>
        String(application.job_id) === selectedJob);
      fillSelect(applicantSelect, "Chọn hồ sơ ứng tuyển", matching, (application) => application.application_id, (application) =>
        `${application.candidate_name || "Ứng viên"} · ${application.cv_title || "CV"} · ${
          application.cv_ai_allowed ? "đã cho phép AI" : application.cv_id ? "chưa cho phép AI" : "chưa có CV"
        }`);
      button.disabled = true;
      if (!selectedJob) {
        showAIStatus("Chọn tin tuyển dụng để xem hồ sơ ứng tuyển.");
      } else if (!matching.length) {
        showAIStatus("Tin tuyển dụng này chưa có hồ sơ ứng tuyển.");
      } else if (!matching.some((application) => application.cv_id && application.cv_ai_allowed)) {
        showAIStatus("Đã hiển thị hồ sơ, nhưng chưa có CV nào được ứng viên cho phép phân tích AI.");
      } else {
        showAIStatus("Chọn hồ sơ có trạng thái “đã cho phép AI” để phân tích.");
      }
    }

    function updateSelectedApplicant() {
      const selected = applications.find((application) =>
        String(application.application_id) === applicantSelect.value);
      button.disabled = !selected || !selected.cv_id || !selected.cv_ai_allowed;
      if (!selected) return;
      if (!selected.cv_id) {
        showAIStatus("Hồ sơ này hiện không còn CV đính kèm.");
      } else if (!selected.cv_ai_allowed) {
        showAIStatus("CV đính kèm chưa được ứng viên cho phép phân tích AI. Chỉ ứng viên mới có thể bật quyền này.");
      } else {
        showAIStatus("CV đã được ứng viên cho phép phân tích.");
      }
    }

    jobSelect.addEventListener("change", updateApplicants);
    applicantSelect.addEventListener("change", updateSelectedApplicant);
    updateApplicants();
  } catch (error) {
    showAIStatus(error.message, true);
    button.disabled = true;
    return;
  }

  button.addEventListener("click", async () => {
    if (!applicantSelect.value) {
      showAIStatus("Hãy chọn hồ sơ ứng tuyển.", true);
      return;
    }
    button.disabled = true;
    showAIStatus("Đang gửi CV được cho phép đến Gemini để phân tích...");
    try {
      const result = await UniCareerAPI.ai.analyzeApplication({
        application_id: Number(applicantSelect.value),
      });
      renderAIResult(result);
      showAIStatus("Đã phân tích và lưu kết quả.");
    } catch (error) {
      showAIStatus(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}