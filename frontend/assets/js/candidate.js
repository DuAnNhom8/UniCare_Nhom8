/**
 * JAVASCRIPT PHÂN HỆ SINH VIÊN & ỨNG TUYỂN (Candidate JS)
 * Chuẩn UniCareer - Nhóm 8 (Task T05FEB0)
 */

document.addEventListener("DOMContentLoaded", () => {
  initCandidateSession();
  initCandidateProfile();
  initCandidateJobList();
  initCandidateJobDetail();
  initApplyJobForm();
  initMyApplications();
});

function getActiveCandidateId() {
  const user = (typeof UniCareerAPI !== "undefined") ? UniCareerAPI.getCurrentUser() : null;
  if (user && user.user_id && user.role === "CANDIDATE") {
    return user.user_id;
  }
  // Mặc định cho bản trải nghiệm demo nếu chưa đăng nhập
  return 3;
}

function initCandidateSession() {
  const user = (typeof UniCareerAPI !== "undefined") ? UniCareerAPI.getCurrentUser() : null;
  const navSide = document.querySelector(".nav-side");
  if (!navSide) return;

  if (user && user.role === "CANDIDATE") {
    navSide.innerHTML = `
      <span class="demo-label" style="background:#e0f2fe;color:#0369a1;padding:4px 8px;border-radius:4px;font-size:12px;">👤 ${user.email}</span>
      <a class="btn btn-outline" href="#" id="candidate-logout-btn">Đăng xuất</a>
    `;
    const logoutBtn = document.getElementById("candidate-logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        UniCareerAPI.auth.logout();
        window.location.href = "../auth/login.html";
      });
    }
  }
}

// 1. Quản lý Hồ sơ cá nhân (profile.html)
async function initCandidateProfile() {
  const profileForm = document.querySelector(".cv-layout form");
  if (!profileForm) return;

  const candidateId = getActiveCandidateId();
  const nameInput = document.getElementById("profile-name");
  const phoneInput = document.getElementById("profile-phone");
  const emailInput = document.getElementById("profile-email");
  const schoolInput = document.getElementById("profile-school");
  const majorInput = document.getElementById("profile-major");
  const skillsInput = document.getElementById("profile-skills");
  const introInput = document.getElementById("profile-intro");
  const saveBtn = profileForm.querySelector("button");

  if (saveBtn) {
    saveBtn.removeAttribute("disabled");
    saveBtn.textContent = "Lưu thay đổi";
    saveBtn.type = "submit";
  }

  // Tải dữ liệu hồ sơ thực tế từ Backend
  try {
    const profile = await UniCareerAPI.candidate.getProfile(candidateId);
    if (profile) {
      if (nameInput && profile.full_name) nameInput.value = profile.full_name;
      if (phoneInput && profile.phone) phoneInput.value = profile.phone;
      if (emailInput && profile.email) emailInput.value = profile.email;
      if (schoolInput && profile.university) schoolInput.value = profile.university;
      if (majorInput && profile.major) majorInput.value = profile.major;
      if (skillsInput && profile.skills) skillsInput.value = profile.skills;
      if (introInput && profile.bio) introInput.value = profile.bio;

      // Cập nhật thẻ mini profile bên trái
      const miniProfile = document.querySelector(".mini-profile");
      if (miniProfile) {
        miniProfile.innerHTML = `
          <div class="company-logo">${(profile.full_name || "SV").slice(0, 2).toUpperCase()}</div>
          <h3>${profile.full_name || "Sinh viên"}</h3>
          <p>${profile.university || "Đại học"} · ${profile.major || "Chuyên ngành"}</p>
          <p><strong>Kỹ năng:</strong> ${profile.skills || "Chưa cập nhật"}</p>
        `;
      }
    }
  } catch (err) {
    console.warn("Chưa tải được hồ sơ backend, dùng dữ liệu mặc định:", err.message);
  }

  profileForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "Đang lưu...";
    }

    try {
      const payload = {
        full_name: nameInput ? nameInput.value.trim() : null,
        phone: phoneInput ? phoneInput.value.trim() : null,
        university: schoolInput ? schoolInput.value.trim() : null,
        major: majorInput ? majorInput.value.trim() : null,
        skills: skillsInput ? skillsInput.value.trim() : null,
        bio: introInput ? introInput.value.trim() : null
      };

      await UniCareerAPI.candidate.updateProfile(candidateId, payload);
      alert("✅ Đã cập nhật hồ sơ cá nhân thành công!");
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = "Lưu thay đổi";
      }
    } catch (err) {
      alert("❌ Lỗi khi lưu hồ sơ: " + err.message);
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = "Lưu thay đổi";
      }
    }
  });
}

// 2. Danh sách & Tìm kiếm việc làm (candidate/index.html)
async function initCandidateJobList() {
  const jobListContainer = document.querySelector(".job-list");
  if (!jobListContainer) return;

  const searchForm = document.querySelector(".hero-search");
  let loadedJobs = [];

  async function fetchAndRender(searchQuery = "", location = "") {
    try {
      const params = { status: "ACTIVE" };
      if (searchQuery) params.search = searchQuery;
      if (location && !location.includes("Tất cả")) params.location = location;

      loadedJobs = await UniCareerAPI.jobs.list(params);
      if (Array.isArray(loadedJobs) && loadedJobs.length > 0) {
        jobListContainer.innerHTML = loadedJobs.map(job => `
          <article class="job-card card" data-job-id="${job.job_id}">
            <div class="job-main">
              <div class="company-logo">${(job.title || "J").slice(0, 1)}</div>
              <div>
                <p class="company-name">TechNova Solutions</p>
                <h3><a href="job-detail.html?id=${job.job_id}">${job.title}</a></h3>
                <p class="muted">${job.description ? job.description.slice(0, 100) + '...' : ''}</p>
                <div class="job-tags">
                  <span class="tag">⌖ ${job.location || 'Toàn quốc'}</span>
                  <span class="tag">◷ ${job.job_type || 'Thực tập'}</span>
                  <span class="tag">${job.salary_range || 'Thỏa thuận'}</span>
                </div>
              </div>
            </div>
            <div class="job-action">
              <a class="btn btn-outline" href="job-detail.html?id=${job.job_id}">Xem chi tiết</a>
              <a class="btn" href="apply-job.html?job_id=${job.job_id}">Ứng tuyển</a>
            </div>
          </article>
        `).join("");
      }
    } catch (err) {
      console.warn("Lỗi tải danh sách việc làm:", err.message);
    }
  }

  fetchAndRender();

  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const qInput = searchForm.querySelector("input[name='q']");
      const locSelect = searchForm.querySelector("select[name='location']");
      fetchAndRender(qInput ? qInput.value.trim() : "", locSelect ? locSelect.value : "");
    });
  }
}

// 3. Chi tiết tin tuyển dụng (job-detail.html)
async function initCandidateJobDetail() {
  const detailHeader = document.querySelector(".detail-header");
  if (!detailHeader) return;

  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("id") || "1";

  try {
    const job = await UniCareerAPI.jobs.get(jobId);
    if (job) {
      const titleElem = detailHeader.querySelector("h1");
      const companyElem = detailHeader.querySelector(".company-name");
      const descElem = detailHeader.querySelector(".muted");
      const applyBtn = detailHeader.querySelector(".detail-actions a.btn");

      if (titleElem) titleElem.textContent = job.title;
      if (companyElem) companyElem.textContent = "TechNova Solutions";
      if (descElem) descElem.textContent = `Vị trí ${job.title} đang mở nhận hồ sơ.`;
      if (applyBtn) applyBtn.href = `apply-job.html?job_id=${job.job_id}`;

      // Điền nội dung mô tả & yêu cầu
      const detailContent = document.querySelector(".detail-content");
      if (detailContent) {
        detailContent.innerHTML = `
          <h2>Mô tả công việc</h2>
          <div class="prose">
            <p>${job.description}</p>
          </div>
          <h2 style="margin-top:24px;">Yêu cầu ứng viên</h2>
          <div class="prose">
            <p>${job.requirements}</p>
          </div>
          <div style="margin-top:24px;">
            <p><strong>Thời hạn nộp hồ sơ:</strong> ${job.deadline || 'Đang mở'}</p>
            <p><strong>Mức lương hỗ trợ:</strong> ${job.salary_range || 'Thỏa thuận'}</p>
            <p><strong>Địa điểm làm việc:</strong> ${job.location || 'TP. Hồ Chí Minh'}</p>
          </div>
        `;
      }
    }
  } catch (err) {
    console.warn("Không thể tải chi tiết công việc:", err.message);
  }
}

// 4. Nộp đơn ứng tuyển (apply-job.html)
async function initApplyJobForm() {
  const applyForm = document.querySelector(".apply-layout form");
  if (!applyForm) return;

  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("job_id") || "1";
  const candidateId = getActiveCandidateId();

  const titleElem = document.getElementById("apply-job-title");
  const coverLetterInput = document.getElementById("cover-letter");
  const submitBtn = applyForm.querySelector("button");

  if (submitBtn) {
    submitBtn.removeAttribute("disabled");
    submitBtn.textContent = "Gửi hồ sơ ứng tuyển";
    submitBtn.type = "submit";
  }

  // Tải thông tin việc làm và ứng viên
  try {
    const job = await UniCareerAPI.jobs.get(jobId);
    if (job && titleElem) {
      titleElem.textContent = `Ứng tuyển: ${job.title}`;
    }
    const profile = await UniCareerAPI.candidate.getProfile(candidateId);
    if (profile) {
      const summaryFields = document.querySelectorAll(".profile-summary .summary-field strong");
      if (summaryFields.length >= 4) {
        summaryFields[0].textContent = profile.full_name || "Ứng viên";
        summaryFields[1].textContent = profile.email || "sinhvien@ptit.edu.vn";
        summaryFields[2].textContent = profile.university || "Học viện Công nghệ Bưu chính Viễn thông";
        summaryFields[3].textContent = profile.cv_url ? "Hồ sơ CV cá nhân" : "NguyenMinhAnh_CV.pdf";
      }
    }
  } catch (err) {
    console.warn("Lỗi tải thông tin đơn ứng tuyển:", err.message);
  }

  applyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Đang gửi đơn...";
    }

    try {
      const letter = coverLetterInput ? coverLetterInput.value.trim() : "";
      await UniCareerAPI.candidate.apply(jobId, candidateId, letter);
      alert("🎉 Nộp hồ sơ ứng tuyển thành công! Nhà tuyển dụng sẽ xem xét hồ sơ của bạn.");
      window.location.href = "my-applications.html";
    } catch (err) {
      alert("❌ Không thể nộp đơn: " + err.message);
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Gửi hồ sơ ứng tuyển";
      }
    }
  });
}

// 5. Xem danh sách đơn đã ứng tuyển (my-applications.html)
async function initMyApplications() {
  const appList = document.querySelector(".application-list");
  if (!appList) return;

  const candidateId = getActiveCandidateId();

  try {
    const applications = await UniCareerAPI.candidate.getApplications(candidateId);
    if (Array.isArray(applications) && applications.length > 0) {
      const statusMap = {
        "RECEIVED": { label: "Đã tiếp nhận", class: "status--received" },
        "REVIEWING": { label: "Đang xem xét", class: "status--reviewing" },
        "ACCEPTED": { label: "Đã chấp nhận", class: "status--accepted" },
        "REJECTED": { label: "Từ chối", class: "status--rejected" }
      };

      appList.innerHTML = applications.map(app => {
        const st = statusMap[app.status] || { label: app.status, class: "status--received" };
        const appliedDate = app.applied_at ? new Date(app.applied_at).toLocaleDateString("vi-VN") : "Hôm nay";
        return `
          <article class="application-card card">
            <div>
              <p class="company-name">${app.company_name || 'TechNova Solutions'}</p>
              <h3>${app.job_title}</h3>
              <p class="muted">Đã nộp ngày: ${appliedDate} · Lương: ${app.salary_range || 'Thỏa thuận'} · Điểm AI: ${app.ai_match_score || 85}%</p>
              ${app.ai_feedback ? `<p style="font-size:13px;color:#0284c7;margin-top:4px;">💡 Đánh giá AI: ${app.ai_feedback}</p>` : ''}
            </div>
            <div class="application-right">
              <span class="status ${st.class}" style="padding:6px 12px;border-radius:12px;font-weight:600;font-size:13px;">${st.label}</span>
              <a class="btn btn-outline btn-sm" href="job-detail.html?id=${app.job_id}">Xem tin</a>
            </div>
          </article>
        `;
      }).join("");
    }
  } catch (err) {
    console.warn("Lỗi tải danh sách đơn ứng tuyển:", err.message);
  }
}
