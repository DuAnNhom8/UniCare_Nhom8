/**
 * JAVASCRIPT PHÂN HỆ DOANH NGHIỆP & QUẢN LÝ TIN TUYỂN DỤNG (TV2)
 * Chuẩn UniCareer - Nhóm 8
 * Task: T85FE99 & T05FE9A - Xây dựng chức năng doanh nghiệp & tin tuyển dụng
 */

const API_BASE_URL = 'http://localhost:8000/api';

// Dữ liệu mẫu doanh nghiệp mặc định
const DEFAULT_COMPANY_DATA = {
  company_id: 1,
  employer_id: 2,
  company_name: 'TechNova',
  industry: 'Công nghệ thông tin / Phần mềm',
  website: 'https://technova.example',
  location: 'TP. Hồ Chí Minh',
  description: 'TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp.',
  job_count: 4,
  application_count: 12
};

// Dữ liệu mẫu tin tuyển dụng ban đầu (dự phòng khi offline)
let cachedJobs = [
  {
    job_id: 1,
    company_id: 1,
    title: 'Backend Developer Intern',
    job_type: 'INTERNSHIP',
    location: 'TP. Hồ Chí Minh',
    salary_range: '3–5 triệu/tháng',
    experience_level: 'Không yêu cầu',
    deadline: '2026-11-30',
    description: 'Tham gia phát triển backend và REST API với Python FastAPI và CSDL MySQL cho nền tảng UniCareer.',
    requirements: 'Kiến thức Python cơ bản, hiểu biết về REST API, cơ sở dữ liệu quan hệ, tinh thần học hỏi cao.',
    status: 'ACTIVE',
    approval_status: 'APPROVED',
    created_at: '2026-11-05T08:00:00'
  },
  {
    job_id: 2,
    company_id: 1,
    title: 'Frontend Developer Intern',
    job_type: 'INTERNSHIP',
    location: 'Hybrid (TP.HCM)',
    salary_range: '3–5 triệu/tháng',
    experience_level: 'Không yêu cầu',
    deadline: '2026-12-05',
    description: 'Xây dựng giao diện web responsive hiện đại với HTML5, CSS3, JavaScript và kết nối API hệ thống.',
    requirements: 'Thành thạo HTML/CSS/JS, có thẩm mỹ giao diện tốt, biết sử dụng Git căn bản.',
    status: 'ACTIVE',
    approval_status: 'APPROVED',
    created_at: '2026-11-02T09:30:00'
  },
  {
    job_id: 3,
    company_id: 1,
    title: 'Data Analyst Intern',
    job_type: 'INTERNSHIP',
    location: 'Hà Nội',
    salary_range: '4–6 triệu/tháng',
    experience_level: 'Không yêu cầu',
    deadline: '2026-11-28',
    description: 'Thu thập, xử lý và phân tích dữ liệu tuyển dụng, hỗ trợ xây dựng dashboard báo cáo chuyên sâu.',
    requirements: 'Kỹ năng SQL, Python pandas/numpy, tư duy phân tích số liệu tốt.',
    status: 'ACTIVE',
    approval_status: 'APPROVED',
    created_at: '2026-10-28T14:15:00'
  },
  {
    job_id: 4,
    company_id: 1,
    title: 'Business Analyst Intern',
    job_type: 'INTERNSHIP',
    location: 'TP. Hồ Chí Minh',
    salary_range: '3–5 triệu/tháng',
    experience_level: 'Không yêu cầu',
    deadline: '2026-11-24',
    description: 'Khảo sát quy trình nghiệp vụ tuyển dụng, viết tài liệu đặc tả yêu cầu SRS và hỗ trợ kiểm thử phần mềm.',
    requirements: 'Kỹ năng giao tiếp tốt, tư duy logic, khả năng viết tài liệu URD/SRS.',
    status: 'ACTIVE',
    approval_status: 'APPROVED',
    created_at: '2026-10-24T10:00:00'
  }
];

let allLoadedJobs = [];
let currentFilterStatus = 'ALL';
let currentSearchKeyword = '';

document.addEventListener('DOMContentLoaded', function () {
  initCompanyProfilePage();
  initManageJobsPage();
  initPostJobPage();
  initEditJobPage();
});

/* ==========================================================================
   1. PHÂN HỆ QUẢN LÝ THÔNG TIN DOANH NGHIỆP (Task T85FE99)
   ========================================================================== */

function initCompanyProfilePage() {
  const companyInfoForm = document.getElementById('companyInfoForm');
  if (!companyInfoForm) return;

  loadCompanyProfile();
  bindLivePreview();

  companyInfoForm.addEventListener('submit', handleCompanyFormSubmit);

  const btnReset = document.getElementById('btn-reset-company');
  if (btnReset) {
    btnReset.addEventListener('click', function () {
      if (confirm('Khôi phục lại thông tin ban đầu?')) {
        loadCompanyProfile();
        showAlert('Đã khôi phục dữ liệu ban đầu', 'info');
      }
    });
  }
}

async function loadCompanyProfile() {
  let companyData = null;

  try {
    const response = await fetch(`${API_BASE_URL}/companies/profile/current`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      companyData = await response.json();
      console.log('✅ Đã tải thông tin doanh nghiệp từ API:', companyData);
      updateStatusBadge('KẾT NỐI API TRỰC TIẾP', '#137333', '#e6f4ea');
    }
  } catch (error) {
    console.warn('⚠️ Không kết nối được Backend API, chuyển sang chế độ dữ liệu cục bộ:', error.message);
    updateStatusBadge('CHẾ ĐỘ OFFLINE / CACHE', '#b06000', '#fef7e0');
  }

  if (!companyData) {
    const saved = localStorage.getItem('unicareer_company_profile');
    companyData = saved ? JSON.parse(saved) : DEFAULT_COMPANY_DATA;
  }

  populateFormData(companyData);
  updatePreviewCard(companyData);
}

function populateFormData(data) {
  const nameEl = document.getElementById('company-name');
  const industryEl = document.getElementById('company-industry');
  const websiteEl = document.getElementById('company-website');
  const locationEl = document.getElementById('company-location');
  const descEl = document.getElementById('company-description');
  const idEl = document.getElementById('company-id');

  if (nameEl) nameEl.value = data.company_name || '';
  if (industryEl) industryEl.value = data.industry || '';
  if (websiteEl) websiteEl.value = data.website || '';
  if (locationEl) locationEl.value = data.location || '';
  if (descEl) descEl.value = data.description || '';
  if (idEl) idEl.value = data.company_id || 1;
}

function updatePreviewCard(data) {
  const previewName = document.getElementById('preview-company-name');
  const previewIndustry = document.getElementById('preview-industry');
  const previewLocation = document.getElementById('preview-location');
  const previewWebsite = document.getElementById('preview-website');
  const previewDesc = document.getElementById('preview-description');
  const previewAvatar = document.getElementById('preview-avatar');
  const sidebarAvatar = document.getElementById('sidebar-avatar');
  const sidebarName = document.getElementById('sidebar-company-name');

  const compName = data.company_name || 'TechNova';
  if (previewName) previewName.textContent = compName;
  if (previewIndustry) previewIndustry.textContent = data.industry || 'Chưa cập nhật';
  if (previewLocation) previewLocation.textContent = data.location || 'Chưa cập nhật';
  if (previewDesc) previewDesc.textContent = data.description || 'Chưa có thông tin giới thiệu.';

  if (previewWebsite) {
    const web = data.website || 'https://technova.example';
    previewWebsite.href = web;
    previewWebsite.textContent = web.replace(/^https?:\/\//, '');
  }

  const initials = getInitials(compName);
  if (previewAvatar) previewAvatar.textContent = initials;
  if (sidebarAvatar) sidebarAvatar.textContent = initials;
  if (sidebarName) sidebarName.textContent = compName;
}

function bindLivePreview() {
  const nameEl = document.getElementById('company-name');
  const industryEl = document.getElementById('company-industry');
  const websiteEl = document.getElementById('company-website');
  const locationEl = document.getElementById('company-location');
  const descEl = document.getElementById('company-description');

  const handleInput = () => {
    const currentData = {
      company_name: nameEl ? nameEl.value : '',
      industry: industryEl ? industryEl.value : '',
      website: websiteEl ? websiteEl.value : '',
      location: locationEl ? locationEl.value : '',
      description: descEl ? descEl.value : ''
    };
    updatePreviewCard(currentData);
  };

  if (nameEl) nameEl.addEventListener('input', handleInput);
  if (industryEl) industryEl.addEventListener('input', handleInput);
  if (websiteEl) websiteEl.addEventListener('input', handleInput);
  if (locationEl) locationEl.addEventListener('input', handleInput);
  if (descEl) descEl.addEventListener('input', handleInput);
}

async function handleCompanyFormSubmit(e) {
  e.preventDefault();

  const nameVal = document.getElementById('company-name')?.value.trim();
  const industryVal = document.getElementById('company-industry')?.value.trim();
  const websiteVal = document.getElementById('company-website')?.value.trim();
  const locationVal = document.getElementById('company-location')?.value.trim();
  const descVal = document.getElementById('company-description')?.value.trim();

  if (!nameVal) {
    showAlert('Vui lòng nhập tên công ty!', 'error');
    return;
  }

  const payload = {
    company_name: nameVal,
    industry: industryVal,
    website: websiteVal,
    location: locationVal,
    description: descVal
  };

  let savedSuccessfully = false;

  try {
    const response = await fetch(`${API_BASE_URL}/companies/profile/current`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const updated = await response.json();
      console.log('✅ Cập nhật qua API thành công:', updated);
      savedSuccessfully = true;
      localStorage.setItem('unicareer_company_profile', JSON.stringify(updated));
      updatePreviewCard(updated);
      showAlert('✅ Đã lưu và cập nhật thông tin doanh nghiệp thành công!', 'success');
    }
  } catch (error) {
    console.warn('⚠️ Lỗi gọi API, lưu tạm vào LocalStorage:', error);
  }

  if (!savedSuccessfully) {
    const localData = { ...DEFAULT_COMPANY_DATA, ...payload, updated_at: new Date().toISOString() };
    localStorage.setItem('unicareer_company_profile', JSON.stringify(localData));
    updatePreviewCard(localData);
    showAlert('✅ Đã lưu thông tin doanh nghiệp vào bộ nhớ máy (Offline Mode)!', 'success');
  }
}

/* ==========================================================================
   2. PHÂN HỆ QUẢN LÝ TIN TUYỂN DỤNG (Task T05FE9A - Tạo, Cập nhật, Đóng/Ẩn)
   ========================================================================== */

/**
 * Khởi tạo trang Danh sách tin tuyển dụng (manage-jobs.html)
 */
function initManageJobsPage() {
  const tableBody = document.getElementById('jobs-table-body');
  if (!tableBody) return;

  loadJobsList();
}

/**
 * Tải danh sách tin tuyển dụng từ API hoặc LocalStorage
 */
async function loadJobsList() {
  const tableBody = document.getElementById('jobs-table-body');
  const countPill = document.getElementById('jobs-count-pill');
  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 24px; color: #64748b;">⏳ Đang tải dữ liệu tin tuyển dụng...</td></tr>`;

  let jobs = null;
  try {
    const res = await fetch(`${API_BASE_URL}/jobs?company_id=1`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (res.ok) {
      jobs = await res.json();
      console.log('✅ Đã tải tin tuyển dụng từ API:', jobs);
      updateStatusBadge('API ONLINE', '#137333', '#e6f4ea');
      localStorage.setItem('unicareer_jobs_cache', JSON.stringify(jobs));
    }
  } catch (err) {
    console.warn('⚠️ Không thể tải từ API, sử dụng dữ liệu cục bộ:', err.message);
    updateStatusBadge('OFFLINE MODE', '#b06000', '#fef7e0');
  }

  if (!jobs || jobs.length === 0) {
    const saved = localStorage.getItem('unicareer_jobs_cache');
    jobs = saved ? JSON.parse(saved) : cachedJobs;
  }

  allLoadedJobs = jobs;
  updateFilterCounters(allLoadedJobs);
  renderJobsTable();
}

/**
 * Cập nhật số lượng trên các nút lọc (Tất cả, Đang tuyển, Đã đóng, Tạm ẩn)
 */
function updateFilterCounters(jobs) {
  const allEl = document.getElementById('count-all');
  const activeEl = document.getElementById('count-active');
  const closedEl = document.getElementById('count-closed');
  const hiddenEl = document.getElementById('count-hidden');

  const total = jobs.length;
  const activeCount = jobs.filter(j => j.status === 'ACTIVE').length;
  const closedCount = jobs.filter(j => j.status === 'CLOSED').length;
  const hiddenCount = jobs.filter(j => j.status === 'HIDDEN').length;

  if (allEl) allEl.textContent = total;
  if (activeEl) activeEl.textContent = activeCount;
  if (closedEl) closedEl.textContent = closedCount;
  if (hiddenEl) hiddenEl.textContent = hiddenCount;

  const countPill = document.getElementById('jobs-count-pill');
  if (countPill) countPill.textContent = `${total} tin`;
}

/**
 * Render bảng danh sách tin tuyển dụng kèm các nút thao tác
 */
function renderJobsTable() {
  const tableBody = document.getElementById('jobs-table-body');
  if (!tableBody) return;

  let filtered = allLoadedJobs;

  // Lọc theo trạng thái
  if (currentFilterStatus !== 'ALL') {
    filtered = filtered.filter(j => j.status === currentFilterStatus);
  }

  // Lọc theo từ khóa tìm kiếm
  if (currentSearchKeyword) {
    const kw = currentSearchKeyword.toLowerCase();
    filtered = filtered.filter(j =>
      (j.title && j.title.toLowerCase().includes(kw)) ||
      (j.location && j.location.toLowerCase().includes(kw))
    );
  }

  if (filtered.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 32px; color: #94a3b8;">
          Không có tin tuyển dụng nào phù hợp với bộ lọc hiện tại.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = filtered.map(job => {
    // Trạng thái hiển thị Badge
    let statusBadgeHtml = '';
    if (job.status === 'ACTIVE') {
      statusBadgeHtml = '<span class="status status--success" style="background: #e6f4ea; color: #137333; font-weight: 600;">● Đang tuyển</span>';
    } else if (job.status === 'CLOSED') {
      statusBadgeHtml = '<span class="status status--closed" style="background: #fce8e6; color: #c5221f; font-weight: 600;">✖ Đã đóng</span>';
    } else if (job.status === 'HIDDEN') {
      statusBadgeHtml = '<span class="status status--hidden" style="background: #f1f3f4; color: #5f6368; font-weight: 600;">⊘ Tạm ẩn</span>';
    } else {
      statusBadgeHtml = `<span class="status">${job.status}</span>`;
    }

    // Các nút thao tác đóng/ẩn/mở lại theo trạng thái hiện tại
    let actionButtonsHtml = '';
    if (job.status === 'ACTIVE') {
      actionButtonsHtml = `
        <a class="btn btn-outline btn-sm" href="edit-job.html?job_id=${job.job_id}" title="Sửa nội dung">✏️ Sửa</a>
        <button class="btn btn-outline btn-sm" style="color: #c5221f; border-color: #fad2cf;" onclick="changeJobStatus(${job.job_id}, 'CLOSED')" title="Đóng tin tuyển dụng">🔒 Đóng</button>
        <button class="btn btn-outline btn-sm" style="color: #5f6368;" onclick="changeJobStatus(${job.job_id}, 'HIDDEN')" title="Tạm ẩn tin tuyển dụng">Ẩn tin</button>
      `;
    } else if (job.status === 'CLOSED') {
      actionButtonsHtml = `
        <a class="btn btn-outline btn-sm" href="edit-job.html?job_id=${job.job_id}" title="Sửa nội dung">✏️ Sửa</a>
        <button class="btn btn-outline btn-sm" style="color: #137333; border-color: #ceead6; font-weight: 600;" onclick="changeJobStatus(${job.job_id}, 'ACTIVE')" title="Mở lại nhận hồ sơ">🔓 Mở lại</button>
        <button class="btn btn-outline btn-sm" style="color: #5f6368;" onclick="changeJobStatus(${job.job_id}, 'HIDDEN')">Ẩn tin</button>
      `;
    } else {
      // HIDDEN
      actionButtonsHtml = `
        <a class="btn btn-outline btn-sm" href="edit-job.html?job_id=${job.job_id}" title="Sửa nội dung">✏️ Sửa</a>
        <button class="btn btn-outline btn-sm" style="color: #137333; border-color: #ceead6; font-weight: 600;" onclick="changeJobStatus(${job.job_id}, 'ACTIVE')" title="Công khai lại tin">👁 Hiện tin</button>
        <button class="btn btn-outline btn-sm" style="color: #c5221f;" onclick="changeJobStatus(${job.job_id}, 'CLOSED')">Đóng tin</button>
      `;
    }

    const typeDisplay = job.job_type === 'INTERNSHIP' ? 'Thực tập' : (job.job_type === 'FULL_TIME' ? 'Toàn thời gian' : 'Bán thời gian');
    const deadlineDisplay = job.deadline ? formatDate(job.deadline) : 'Chưa đặt';

    return `
      <tr>
        <td>
          <strong>${escapeHtml(job.title)}</strong>
          <small style="display:block; color:#64748b; margin-top:2px;">Mã tin: #${job.job_id} · ${escapeHtml(job.salary_range || 'Thỏa thuận')}</small>
        </td>
        <td>
          <span>${escapeHtml(job.location || 'TP. Hồ Chí Minh')}</span>
          <small style="display:block; color:#64748b;">${typeDisplay}</small>
        </td>
        <td>
          <span>${deadlineDisplay}</span>
        </td>
        <td>
          ${statusBadgeHtml}
        </td>
        <td style="text-align: center; white-space: nowrap;">
          <div style="display: inline-flex; gap: 6px;">
            ${actionButtonsHtml}
            <button class="btn btn-outline btn-sm" style="color: #dc2626; border-color: #fca5a5;" onclick="deleteJobPost(${job.job_id})" title="Xóa tin này">🗑</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Xử lý lọc theo trạng thái (Tất cả, Đang tuyển, Đã đóng, Tạm ẩn)
 */
function filterJobsByStatus(status, btnEl) {
  currentFilterStatus = status;
  const buttons = document.querySelectorAll('#filter-status-group button');
  buttons.forEach(b => b.classList.remove('active-filter'));
  if (btnEl) btnEl.classList.add('active-filter');
  renderJobsTable();
}

/**
 * Xử lý tìm kiếm tin tuyển dụng realtime
 */
function handleJobSearch(keyword) {
  currentSearchKeyword = keyword.trim();
  renderJobsTable();
}

/**
 * Cập nhật trạng thái ĐÓNG / ẨN / MỞ LẠI tin tuyển dụng (PATCH /api/jobs/{id}/status)
 */
async function changeJobStatus(jobId, newStatus) {
  const statusTexts = {
    'ACTIVE': 'mở lại và công khai',
    'CLOSED': 'đóng nhận hồ sơ',
    'HIDDEN': 'tạm ẩn'
  };
  const confirmMsg = `Bạn có chắc chắn muốn ${statusTexts[newStatus] || newStatus} tin tuyển dụng #${jobId}?`;
  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });

    if (res.ok) {
      const updated = await res.json();
      console.log('✅ Đã đổi trạng thái qua API:', updated);
      updateJobInLocalList(updated);
      showAlert(`✅ Đã chuyển trạng thái tin tuyển dụng #${jobId} sang [${newStatus}] thành công!`, 'success');
      return;
    }
  } catch (err) {
    console.warn('⚠️ API không phản hồi, cập nhật cục bộ:', err);
  }

  // Fallback cập nhật offline
  const idx = allLoadedJobs.findIndex(j => j.job_id == jobId);
  if (idx !== -1) {
    allLoadedJobs[idx].status = newStatus;
    localStorage.setItem('unicareer_jobs_cache', JSON.stringify(allLoadedJobs));
    updateFilterCounters(allLoadedJobs);
    renderJobsTable();
    showAlert(`✅ Đã chuyển trạng thái tin tuyển dụng #${jobId} sang [${newStatus}] (Offline Mode)!`, 'success');
  }
}

/**
 * Xóa tin tuyển dụng (DELETE /api/jobs/{id})
 */
async function deleteJobPost(jobId) {
  if (!confirm(`Bạn có chắc chắn muốn XÓA vĩnh viễn tin tuyển dụng #${jobId}?`)) return;

  try {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      allLoadedJobs = allLoadedJobs.filter(j => j.job_id != jobId);
      localStorage.setItem('unicareer_jobs_cache', JSON.stringify(allLoadedJobs));
      updateFilterCounters(allLoadedJobs);
      renderJobsTable();
      showAlert(`🗑 Đã xóa thành công tin tuyển dụng #${jobId}!`, 'success');
      return;
    }
  } catch (err) {
    console.warn('⚠️ Lỗi xóa qua API:', err);
  }

  allLoadedJobs = allLoadedJobs.filter(j => j.job_id != jobId);
  localStorage.setItem('unicareer_jobs_cache', JSON.stringify(allLoadedJobs));
  updateFilterCounters(allLoadedJobs);
  renderJobsTable();
  showAlert(`🗑 Đã xóa tin tuyển dụng #${jobId} (Offline Mode)!`, 'info');
}

function updateJobInLocalList(updatedJob) {
  const idx = allLoadedJobs.findIndex(j => j.job_id == updatedJob.job_id);
  if (idx !== -1) {
    allLoadedJobs[idx] = updatedJob;
  }
  localStorage.setItem('unicareer_jobs_cache', JSON.stringify(allLoadedJobs));
  updateFilterCounters(allLoadedJobs);
  renderJobsTable();
}

/**
 * Khởi tạo trang Đăng tin tuyển dụng mới (post-job.html)
 */
function initPostJobPage() {
  const form = document.getElementById('postJobForm');
  if (!form) return;

  // Set mặc định ngày hạn nộp là 30 ngày sau
  const deadlineInput = document.getElementById('job-deadline');
  if (deadlineInput && !deadlineInput.value) {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() + 30);
    deadlineInput.value = defaultDate.toISOString().split('T')[0];
  }

  form.addEventListener('submit', handlePostJobSubmit);
}

/**
 * Xử lý Tạo mới tin tuyển dụng (POST /api/jobs)
 */
async function handlePostJobSubmit(e) {
  e.preventDefault();

  const title = document.getElementById('job-title')?.value.trim();
  const job_type = document.getElementById('job-type')?.value;
  const location = document.getElementById('job-location')?.value.trim();
  const salary_range = document.getElementById('job-salary')?.value.trim();
  const deadline = document.getElementById('job-deadline')?.value;
  const experience_level = document.getElementById('job-experience')?.value.trim();
  const status = document.getElementById('job-status')?.value || 'ACTIVE';
  const description = document.getElementById('job-description')?.value.trim();
  const requirements = document.getElementById('job-requirements')?.value.trim();

  if (!title || !description || !requirements) {
    showAlert('Vui lòng điền đầy đủ tiêu đề, mô tả và yêu cầu công việc!', 'error');
    return;
  }

  const payload = {
    company_id: 1,
    title,
    job_type,
    location,
    salary_range,
    deadline: deadline || null,
    experience_level,
    status,
    description,
    requirements
  };

  const submitBtn = document.getElementById('btn-submit-post');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Đang đăng tin...';
  }

  try {
    const res = await fetch(`${API_BASE_URL}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const created = await res.json();
      showAlert(`🎉 Đăng tin tuyển dụng "${created.title}" thành công!`, 'success');
      setTimeout(() => {
        window.location.href = 'manage-jobs.html';
      }, 1000);
      return;
    } else {
      const errData = await res.json();
      showAlert(`Lỗi khi tạo tin: ${errData.detail || 'Không thể tạo'}`, 'error');
    }
  } catch (err) {
    console.warn('⚠️ Lỗi kết nối API:', err);
    // Offline save
    const newId = Date.now() % 10000;
    const fallbackCreated = { ...payload, job_id: newId, approval_status: 'APPROVED', created_at: new Date().toISOString() };
    const saved = localStorage.getItem('unicareer_jobs_cache');
    let list = saved ? JSON.parse(saved) : cachedJobs;
    list.unshift(fallbackCreated);
    localStorage.setItem('unicareer_jobs_cache', JSON.stringify(list));

    showAlert(`🎉 Đăng tin tuyển dụng thành công (Offline Mode)!`, 'success');
    setTimeout(() => {
      window.location.href = 'manage-jobs.html';
    }, 1000);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = '🚀 Đăng tin tuyển dụng';
    }
  }
}

/**
 * Khởi tạo trang Chỉnh sửa tin tuyển dụng (edit-job.html)
 */
function initEditJobPage() {
  const form = document.getElementById('editJobForm');
  if (!form) return;

  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get('job_id') || urlParams.get('id') || 1;

  loadJobForEditing(jobId);
  form.addEventListener('submit', handleEditJobSubmit);
}

/**
 * Tải chi tiết tin tuyển dụng và điền vào form chỉnh sửa
 */
async function loadJobForEditing(jobId) {
  let jobData = null;

  try {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (res.ok) {
      jobData = await res.json();
      console.log('✅ Đã tải chi tiết tin tuyển dụng từ API:', jobData);
    }
  } catch (err) {
    console.warn('⚠️ Lỗi tải job từ API:', err);
  }

  if (!jobData) {
    const saved = localStorage.getItem('unicareer_jobs_cache');
    const list = saved ? JSON.parse(saved) : cachedJobs;
    jobData = list.find(j => j.job_id == jobId) || list[0];
  }

  if (!jobData) return;

  // Điền dữ liệu vào form
  const idInput = document.getElementById('job-id');
  const titleInput = document.getElementById('job-title');
  const statusSelect = document.getElementById('job-status');
  const typeSelect = document.getElementById('job-type');
  const locInput = document.getElementById('job-location');
  const salInput = document.getElementById('job-salary');
  const deadInput = document.getElementById('job-deadline');
  const expInput = document.getElementById('job-experience');
  const descInput = document.getElementById('job-description');
  const reqInput = document.getElementById('job-requirements');

  if (idInput) idInput.value = jobData.job_id;
  if (titleInput) titleInput.value = jobData.title || '';
  if (statusSelect) statusSelect.value = jobData.status || 'ACTIVE';
  if (typeSelect) typeSelect.value = jobData.job_type || 'INTERNSHIP';
  if (locInput) locInput.value = jobData.location || '';
  if (salInput) salInput.value = jobData.salary_range || '';
  if (deadInput && jobData.deadline) deadInput.value = jobData.deadline.split('T')[0];
  if (expInput) expInput.value = jobData.experience_level || '';
  if (descInput) descInput.value = jobData.description || '';
  if (reqInput) reqInput.value = jobData.requirements || '';

  // Cập nhật tiêu đề trang và badge
  const heading = document.getElementById('edit-job-heading');
  const summary = document.getElementById('edit-job-summary');
  const badge = document.getElementById('edit-job-status-badge');

  if (heading) heading.textContent = `Chỉnh sửa tin #${jobData.job_id}: ${jobData.title}`;
  if (summary) summary.textContent = `Cập nhật thông tin, thay đổi trạng thái đóng hoặc ẩn tin tuyển dụng.`;

  updateEditPageStatusBadge(jobData.status);
}

function updateEditPageStatusBadge(status) {
  const badge = document.getElementById('edit-job-status-badge');
  const btnClose = document.getElementById('btn-quick-close');
  const btnHide = document.getElementById('btn-quick-hide');
  const btnReopen = document.getElementById('btn-quick-reopen');

  if (badge) {
    if (status === 'ACTIVE') {
      badge.textContent = '● Đang tuyển';
      badge.style.background = '#e6f4ea';
      badge.style.color = '#137333';
      if (btnClose) btnClose.style.display = 'inline-block';
      if (btnHide) btnHide.style.display = 'inline-block';
      if (btnReopen) btnReopen.style.display = 'none';
    } else if (status === 'CLOSED') {
      badge.textContent = '✖ Đã đóng';
      badge.style.background = '#fce8e6';
      badge.style.color = '#c5221f';
      if (btnClose) btnClose.style.display = 'none';
      if (btnHide) btnHide.style.display = 'inline-block';
      if (btnReopen) btnReopen.style.display = 'inline-block';
    } else {
      badge.textContent = '⊘ Tạm ẩn';
      badge.style.background = '#f1f3f4';
      badge.style.color = '#5f6368';
      if (btnClose) btnClose.style.display = 'inline-block';
      if (btnHide) btnHide.style.display = 'none';
      if (btnReopen) btnReopen.style.display = 'inline-block';
    }
  }
}

/**
 * Xử lý Lưu thay đổi tin tuyển dụng (PUT /api/jobs/{id})
 */
async function handleEditJobSubmit(e) {
  e.preventDefault();

  const jobId = document.getElementById('job-id')?.value;
  const title = document.getElementById('job-title')?.value.trim();
  const status = document.getElementById('job-status')?.value;
  const job_type = document.getElementById('job-type')?.value;
  const location = document.getElementById('job-location')?.value.trim();
  const salary_range = document.getElementById('job-salary')?.value.trim();
  const deadline = document.getElementById('job-deadline')?.value;
  const experience_level = document.getElementById('job-experience')?.value.trim();
  const description = document.getElementById('job-description')?.value.trim();
  const requirements = document.getElementById('job-requirements')?.value.trim();

  if (!title || !description || !requirements) {
    showAlert('Vui lòng điền đầy đủ tiêu đề, mô tả và yêu cầu công việc!', 'error');
    return;
  }

  const payload = {
    title,
    status,
    job_type,
    location,
    salary_range,
    deadline: deadline || null,
    experience_level,
    description,
    requirements
  };

  const saveBtn = document.getElementById('btn-save-job');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.textContent = '⏳ Đang lưu...';
  }

  try {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const updated = await res.json();
      updateEditPageStatusBadge(updated.status);
      showAlert(`✅ Đã lưu thay đổi cho tin tuyển dụng #${jobId} thành công!`, 'success');
      setTimeout(() => {
        window.location.href = 'manage-jobs.html';
      }, 1000);
      return;
    }
  } catch (err) {
    console.warn('⚠️ Lỗi gọi API PUT:', err);
  }

  // Fallback offline
  const saved = localStorage.getItem('unicareer_jobs_cache');
  let list = saved ? JSON.parse(saved) : cachedJobs;
  const idx = list.findIndex(j => j.job_id == jobId);
  if (idx !== -1) {
    list[idx] = { ...list[idx], ...payload, updated_at: new Date().toISOString() };
    localStorage.setItem('unicareer_jobs_cache', JSON.stringify(list));
  }
  updateEditPageStatusBadge(status);
  showAlert(`✅ Đã lưu thay đổi tin tuyển dụng #${jobId} (Offline Mode)!`, 'success');
  setTimeout(() => {
    window.location.href = 'manage-jobs.html';
  }, 1000);
}

/**
 * Thao tác nhanh Đóng / Ẩn / Mở lại từ trang chỉnh sửa
 */
async function quickToggleJobStatus(newStatus) {
  const jobId = document.getElementById('job-id')?.value;
  if (!jobId) return;

  const statusSelect = document.getElementById('job-status');
  if (statusSelect) statusSelect.value = newStatus;

  try {
    const res = await fetch(`${API_BASE_URL}/jobs/${jobId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      updateEditPageStatusBadge(newStatus);
      showAlert(`✅ Đã chuyển trạng thái tin tuyển dụng thành [${newStatus}]!`, 'success');
      return;
    }
  } catch (err) {
    console.warn('⚠️ Lỗi PATCH:', err);
  }

  updateEditPageStatusBadge(newStatus);
  showAlert(`✅ Đã chuyển trạng thái tin tuyển dụng thành [${newStatus}]!`, 'info');
}

/* ==========================================================================
   3. HÀM TIỆN ÍCH DÙNG CHUNG (Alerts, Helpers)
   ========================================================================== */

function showAlert(message, type = 'info') {
  const alertEl = document.getElementById('company-alert');
  if (!alertEl) {
    alert(message);
    return;
  }

  alertEl.textContent = message;
  alertEl.style.display = 'block';

  if (type === 'success') {
    alertEl.style.backgroundColor = '#e6f4ea';
    alertEl.style.color = '#137333';
    alertEl.style.border = '1px solid #ceead6';
  } else if (type === 'error') {
    alertEl.style.backgroundColor = '#fce8e6';
    alertEl.style.color = '#c5221f';
    alertEl.style.border = '1px solid #fad2cf';
  } else {
    alertEl.style.backgroundColor = '#e8f0fe';
    alertEl.style.color = '#1967d2';
    alertEl.style.border = '1px solid #d2e3fc';
  }

  setTimeout(() => {
    alertEl.style.display = 'none';
  }, 4000);
}

function updateStatusBadge(text, color, bgColor) {
  const badge = document.getElementById('status-badge') || document.getElementById('api-status-pill');
  if (badge) {
    badge.textContent = text;
    badge.style.color = color;
    badge.style.backgroundColor = bgColor;
  }
}

function getInitials(name) {
  if (!name) return 'TN';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const parts = dateStr.split('T')[0].split('-');
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return dateStr;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
