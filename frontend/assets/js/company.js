/**
 * JAVASCRIPT PHÂN HỆ DOANH NGHIỆP & TUYỂN DỤNG (TV2)
 * Chuẩn UniCareer - Nhóm 8
 * Task: T85FE99 - Xây dựng chức năng doanh nghiệp (Tạo, xem và cập nhật thông tin doanh nghiệp)
 */

const API_BASE_URL = 'http://localhost:8000/api';

// Dữ liệu mặc định mẫu
const DEFAULT_COMPANY_DATA = {
  company_id: 1,
  employer_id: 2,
  company_name: 'TechNova',
  industry: 'Công nghệ thông tin / Phần mềm',
  website: 'https://technova.example',
  location: 'TP. Hồ Chí Minh',
  description: 'TechNova phát triển các giải pháp phần mềm và sản phẩm số cho doanh nghiệp.',
  job_count: 3,
  application_count: 12
};

document.addEventListener('DOMContentLoaded', function () {
  initCompanyProfilePage();
  initCompanyForms();
});

/**
 * Khởi tạo trang Thông tin công ty (Screen 12)
 */
function initCompanyProfilePage() {
  const companyInfoForm = document.getElementById('companyInfoForm');
  if (!companyInfoForm) return;

  // 1. Tải thông tin công ty hiện tại (Xem thông tin)
  loadCompanyProfile();

  // 2. Lắng nghe sự kiện gõ phím để live-preview
  bindLivePreview();

  // 3. Xử lý nút lưu thông tin (Cập nhật thông tin)
  companyInfoForm.addEventListener('submit', handleCompanyFormSubmit);

  // 4. Nút Đặt lại form
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

/**
 * Tải thông tin công ty từ Backend API hoặc LocalStorage (Xem thông tin doanh nghiệp)
 */
async function loadCompanyProfile() {
  let companyData = null;

  try {
    // Thử gọi Backend API
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

  // Fallback: Lấy từ LocalStorage hoặc dữ liệu mặc định
  if (!companyData) {
    const saved = localStorage.getItem('unicareer_company_profile');
    companyData = saved ? JSON.parse(saved) : DEFAULT_COMPANY_DATA;
  }

  // Điền dữ liệu vào form và khung preview
  populateFormData(companyData);
  updatePreviewCard(companyData);
}

/**
 * Điền dữ liệu vào các input form
 */
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

/**
 * Cập nhật giao diện khung xem trước và thanh bên
 */
function updatePreviewCard(data) {
  const name = data.company_name || 'Tên doanh nghiệp';
  const industry = data.industry || 'Lĩnh vực chưa cập nhật';
  const location = data.location || 'Chưa cập nhật địa chỉ';
  const website = data.website || '#';
  const description = data.description || 'Chưa có thông tin giới thiệu.';

  // Tính chữ viết tắt Avatar (Initials)
  const initials = getInitials(name);

  // Cập nhật card preview bên phải
  const previewName = document.getElementById('preview-name');
  const previewIndustry = document.getElementById('preview-industry');
  const previewLocation = document.getElementById('preview-location');
  const previewWebsite = document.getElementById('preview-website');
  const previewDesc = document.getElementById('preview-description');
  const previewAvatar = document.getElementById('preview-avatar');

  if (previewName) previewName.textContent = name;
  if (previewIndustry) previewIndustry.textContent = industry;
  if (previewLocation) previewLocation.textContent = location;
  if (previewDesc) previewDesc.textContent = description;
  if (previewAvatar) previewAvatar.textContent = initials;
  if (previewWebsite) {
    previewWebsite.textContent = website;
    previewWebsite.href = website.startsWith('http') ? website : `https://${website}`;
  }

  // Cập nhật thanh bên (Sidebar)
  const sidebarAvatar = document.getElementById('sidebar-avatar');
  const sidebarName = document.getElementById('sidebar-name');
  if (sidebarAvatar) sidebarAvatar.textContent = initials;
  if (sidebarName) sidebarName.textContent = name;
}

/**
 * Lấy chữ viết tắt làm Avatar (Ví dụ: TechNova -> TN, FPT Software -> FS)
 */
function getInitials(name) {
  if (!name) return 'DN';
  const words = name.trim().split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

/**
 * Lắng nghe input thay đổi để cập nhật Live Preview trực tiếp
 */
function bindLivePreview() {
  const fields = ['company-name', 'company-industry', 'company-location', 'company-website', 'company-description'];
  fields.forEach(fieldId => {
    const el = document.getElementById(fieldId);
    if (el) {
      el.addEventListener('input', () => {
        updatePreviewCard({
          company_name: document.getElementById('company-name')?.value,
          industry: document.getElementById('company-industry')?.value,
          location: document.getElementById('company-location')?.value,
          website: document.getElementById('company-website')?.value,
          description: document.getElementById('company-description')?.value,
        });
      });
    }
  });
}

/**
 * Xử lý sự kiện lưu/cập nhật thông tin công ty
 */
async function handleCompanyFormSubmit(e) {
  e.preventDefault();

  const companyName = document.getElementById('company-name')?.value.trim();
  const industry = document.getElementById('company-industry')?.value.trim();
  const website = document.getElementById('company-website')?.value.trim();
  const location = document.getElementById('company-location')?.value.trim();
  const description = document.getElementById('company-description')?.value.trim();
  const companyId = document.getElementById('company-id')?.value || 1;

  if (!companyName || companyName.length < 2) {
    showAlert('⚠️ Tên doanh nghiệp không được để trống (tối thiểu 2 ký tự)!', 'error');
    return;
  }

  const payload = {
    company_name: companyName,
    industry: industry,
    website: website,
    location: location,
    description: description
  };

  const btnSave = document.getElementById('btn-save-company');
  const originalBtnText = btnSave ? btnSave.innerHTML : '';
  if (btnSave) {
    btnSave.disabled = true;
    btnSave.innerHTML = '<span>⏳</span> Đang lưu thông tin...';
  }

  let saveSuccess = false;
  let responseData = null;

  try {
    // 1. Gửi request PUT cập nhật tới Backend API
    const response = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      responseData = await response.json();
      saveSuccess = true;
      console.log('✅ Cập nhật thành công qua API:', responseData);
    } else {
      console.warn('Backend trả về lỗi mã:', response.status);
    }
  } catch (error) {
    console.warn('⚠️ Lỗi kết nối mạng khi lưu API, tự động đồng bộ qua bộ nhớ đệm:', error);
  }

  // 2. Lưu vào LocalStorage để dữ liệu luôn được ghi nhớ
  const updatedData = responseData || {
    ...DEFAULT_COMPANY_DATA,
    ...payload,
    company_id: companyId
  };
  localStorage.setItem('unicareer_company_profile', JSON.stringify(updatedData));

  // 3. Cập nhật giao diện
  updatePreviewCard(updatedData);

  const updatedTime = new Date().toLocaleTimeString('vi-VN');
  const lastUpdatedEl = document.getElementById('last-updated-text');
  if (lastUpdatedEl) {
    lastUpdatedEl.textContent = `Đã cập nhật lúc ${updatedTime} (${saveSuccess ? 'Backend API' : 'Cục bộ'})`;
  }

  showAlert('✅ Đã lưu và cập nhật thông tin doanh nghiệp thành công!', 'success');

  // Khôi phục nút
  if (btnSave) {
    btnSave.disabled = false;
    btnSave.innerHTML = originalBtnText;
  }
}

/**
 * Hiển thị thông báo Alert / Toast trên đầu form
 */
function showAlert(message, type = 'success') {
  const alertEl = document.getElementById('company-alert');
  if (!alertEl) {
    alert(message);
    return;
  }

  alertEl.style.display = 'block';
  alertEl.textContent = message;

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

  // Tự ẩn sau 4 giây
  setTimeout(() => {
    alertEl.style.display = 'none';
  }, 4000);
}

function updateStatusBadge(text, color, bgColor) {
  const badge = document.getElementById('status-badge');
  if (badge) {
    badge.textContent = text;
    badge.style.color = color;
    badge.style.backgroundColor = bgColor;
  }
}

/**
 * Các chức năng khác của phân hệ tuyển dụng (Giữ tương thích các trang)
 */
function initCompanyForms() {
  // 1. Form Đăng tin tuyển dụng mới (Screen 14)
  const postJobForm = document.getElementById('postJobForm');
  if (postJobForm) {
    postJobForm.addEventListener('submit', function (e) {
      e.preventDefault();
      alert('🎉 Đăng tin tuyển dụng thành công! Tin đã được gửi đi chờ kiểm duyệt (PENDING).');
      window.location.href = 'manage-jobs.html';
    });
  }

  // 2. Form Chỉnh sửa tin tuyển dụng (Screen 15)
  const editJobForm = document.getElementById('editJobForm');
  if (editJobForm) {
    editJobForm.addEventListener('submit', function (e) {
      e.preventDefault();
      alert('✅ Đã lưu các thay đổi cho tin tuyển dụng!');
      window.location.href = 'manage-jobs.html';
    });
  }
}

// Thao tác đóng tin tuyển dụng (Screen 13)
function toggleCloseJob(linkEl) {
  if (confirm('Bạn có chắc chắn muốn đóng tin tuyển dụng này? Ứng viên sẽ không thể nộp đơn nữa.')) {
    const row = linkEl.closest('tr');
    if (row) {
      const statusCell = row.cells[3];
      statusCell.innerHTML = '<span class="badge badge-closed">CLOSED</span>';
      linkEl.outerHTML = '<a href="javascript:void(0)" class="action-link" style="color: var(--status-active);" onclick="toggleReopenJob(this)">Mở lại tin</a>';
      alert('Đã đóng tin tuyển dụng.');
    }
  }
}

// Thao tác mở lại tin tuyển dụng (Screen 13)
function toggleReopenJob(linkEl) {
  const row = linkEl.closest('tr');
  if (row) {
    const statusCell = row.cells[3];
    statusCell.innerHTML = '<span class="badge badge-active">ACTIVE</span> <span class="badge badge-approved" style="margin-left: 4px;">APPROVED</span>';
    linkEl.outerHTML = '<a href="javascript:void(0)" class="action-link danger" onclick="toggleCloseJob(this)">Đóng tin</a>';
    alert('Đã mở lại tin tuyển dụng thành công!');
  }
}

// Thao tác đóng/gỡ tin từ trang chỉnh sửa (Screen 15)
function confirmCloseJob() {
  if (confirm('Bạn có chắc chắn muốn đóng hoặc gỡ tin tuyển dụng này khỏi hệ thống?')) {
    alert('Tin tuyển dụng đã chuyển sang trạng thái CLOSED.');
    window.location.href = 'manage-jobs.html';
  }
}
