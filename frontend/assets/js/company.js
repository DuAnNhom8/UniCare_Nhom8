/**
 * JAVASCRIPT PHÂN HỆ DOANH NGHIỆP & TUYỂN DỤNG (TV2)
 * Chuẩn UniCareer - Nhóm 8
 */

document.addEventListener('DOMContentLoaded', function () {
  initCompanyForms();
});

function initCompanyForms() {
  // 1. Form Cập nhật thông tin công ty (Screen 12)
  const companyInfoForm = document.getElementById('companyInfoForm');
  if (companyInfoForm) {
    companyInfoForm.addEventListener('submit', function (e) {
      e.preventDefault();
      alert('✅ Đã lưu và cập nhật thông tin doanh nghiệp thành công!');
    });
  }

  // 2. Form Đăng tin tuyển dụng mới (Screen 14)
  const postJobForm = document.getElementById('postJobForm');
  if (postJobForm) {
    postJobForm.addEventListener('submit', function (e) {
      e.preventDefault();
      alert('🎉 Đăng tin tuyển dụng thành công! Tin đã được gửi đi chờ kiểm duyệt (PENDING).');
      window.location.href = 'manage-jobs.html';
    });
  }

  // 3. Form Chỉnh sửa tin tuyển dụng (Screen 15)
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
