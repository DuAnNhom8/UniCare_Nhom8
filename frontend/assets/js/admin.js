/**
 * JAVASCRIPT PHÂN HỆ QUẢN TRỊ HỆ THỐNG (Admin JS)
 * Chuẩn UniCareer - Nhóm 8 (Task T05FEB0)
 */

document.addEventListener("DOMContentLoaded", () => {
  initAdminDashboard();
  initAdminUsers();
  initAdminApproveJobs();
});

// 1. Dashboard Quản trị (dashboard.html)
async function initAdminDashboard() {
  const statsContainer = document.querySelector(".portal-stats");
  if (!statsContainer || !document.querySelector(".portal-kicker")?.textContent.includes("DASHBOARD")) return;

  try {
    const stats = await UniCareerAPI.admin.getStats();
    if (stats) {
      const statBoxes = statsContainer.querySelectorAll(".portal-stat");
      if (statBoxes.length >= 4) {
        statBoxes[0].querySelector(".portal-stat__value").textContent = stats.total_users || 0;
        statBoxes[0].querySelector(".portal-stat__note").textContent = `${stats.candidate_count || 0} sinh viên · ${stats.employer_count || 0} NTD`;

        statBoxes[1].querySelector(".portal-stat__value").textContent = stats.company_count || 0;
        statBoxes[1].querySelector(".portal-stat__note").textContent = "Doanh nghiệp đối tác";

        statBoxes[2].querySelector(".portal-stat__value").textContent = stats.total_jobs || 0;
        statBoxes[2].querySelector(".portal-stat__note").textContent = `${stats.active_jobs || 0} tin đang mở tuyển`;

        statBoxes[3].querySelector(".portal-stat__value").textContent = String(stats.pending_jobs || 0).padStart(2, "0");
        statBoxes[3].querySelector(".portal-stat__note").textContent = "Tin chờ kiểm duyệt";
      }

      // Cập nhật banner chờ duyệt
      const bannerDesc = document.querySelector(".portal-banner p");
      if (bannerDesc) {
        bannerDesc.textContent = `Hiện có ${stats.pending_jobs || 0} tin tuyển dụng đang chờ quản trị viên xem xét và duyệt công khai.`;
      }
    }
  } catch (err) {
    console.warn("Lỗi tải số liệu thống kê Dashboard:", err.message);
  }
}

// 2. Quản lý người dùng (users.html)
async function initAdminUsers() {
  const userTableBody = document.querySelector(".portal-table-wrap tbody");
  if (!userTableBody || !document.querySelector(".portal-kicker")?.textContent.includes("USERS")) return;

  const countBadge = document.querySelector(".portal-panel__heading .portal-pill");
  const searchInput = document.getElementById("user-search");
  let allUsers = [];

  function renderUsers(list) {
    if (!list || list.length === 0) {
      userTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;">Không tìm thấy người dùng phù hợp.</td></tr>`;
      return;
    }

    userTableBody.innerHTML = list.map(user => {
      const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString("vi-VN") : "Hôm nay";
      const displayName = user.full_name || user.company_name || user.email.split("@")[0];
      const roleLabel = user.role === "CANDIDATE" ? "Sinh viên" : (user.role === "EMPLOYER" ? "Nhà tuyển dụng" : "Quản trị viên");
      const statusBadge = user.is_active
        ? `<span class="status status--success" style="padding:4px 8px;border-radius:6px;font-size:12px;font-weight:600;">Đang hoạt động</span>`
        : `<span class="status status--rejected" style="padding:4px 8px;border-radius:6px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Đã khóa</span>`;

      const actionBtn = user.role === "ADMIN"
        ? `<button class="btn btn-outline btn-sm" disabled style="opacity:0.5;">Admin</button>`
        : `<button class="btn btn-outline btn-sm toggle-status-btn" data-user-id="${user.user_id}" data-active="${user.is_active}" style="${user.is_active ? 'color:#dc2626;border-color:#fca5a5;' : 'color:#16a34a;border-color:#86efac;'}">${user.is_active ? 'Khóa' : 'Mở khóa'}</button>`;

      return `
        <tr>
          <td><strong>${displayName}</strong><br><small style="color:#64748b;">${user.email}</small></td>
          <td>${roleLabel}</td>
          <td>${createdDate}</td>
          <td>${statusBadge}</td>
          <td>${actionBtn}</td>
        </tr>
      `;
    }).join("");

    // Gắn sự kiện khóa / mở khóa
    userTableBody.querySelectorAll(".toggle-status-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const uId = parseInt(btn.getAttribute("data-user-id"));
        const currentActive = btn.getAttribute("data-active") === "true";
        const nextState = !currentActive;

        if (confirm(`Bạn có chắc chắn muốn ${nextState ? 'mở khóa' : 'khóa'} tài khoản người dùng này?`)) {
          try {
            await UniCareerAPI.admin.toggleUserStatus(uId, nextState);
            alert(`✅ Đã ${nextState ? 'mở khóa' : 'khóa'} tài khoản thành công!`);
            loadAndRenderUsers();
          } catch (err) {
            alert("❌ Lỗi: " + err.message);
          }
        }
      });
    });
  }

  async function loadAndRenderUsers() {
    try {
      allUsers = await UniCareerAPI.admin.getUsers();
      if (countBadge) {
        countBadge.textContent = `${allUsers.length} tài khoản thực tế`;
      }
      renderUsers(allUsers);
    } catch (err) {
      console.warn("Lỗi tải danh sách người dùng:", err.message);
    }
  }

  loadAndRenderUsers();

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = allUsers.filter(u =>
        u.email.toLowerCase().includes(q) ||
        (u.full_name && u.full_name.toLowerCase().includes(q)) ||
        (u.company_name && u.company_name.toLowerCase().includes(q))
      );
      renderUsers(filtered);
    });
  }
}

// 3. Kiểm duyệt tin tuyển dụng (approve-jobs.html)
async function initAdminApproveJobs() {
  const tableBody = document.querySelector(".portal-table-wrap tbody");
  if (!tableBody || !document.querySelector(".portal-kicker")?.textContent.includes("MODERATION")) return;

  const countBadge = document.querySelector(".portal-panel__heading .portal-pill");
  const searchInput = document.getElementById("job-search");
  let allJobs = [];

  function renderJobs(jobs) {
    if (!jobs || jobs.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;">Hiện không có tin tuyển dụng nào trong hàng đợi.</td></tr>`;
      return;
    }

    tableBody.innerHTML = jobs.map(job => {
      const createdDate = job.created_at ? new Date(job.created_at).toLocaleDateString("vi-VN") : "Hôm nay";
      const statusBadge = job.approval_status === "APPROVED"
        ? `<span class="status status--success" style="padding:4px 8px;border-radius:6px;font-size:12px;font-weight:600;">Đã duyệt</span>`
        : (job.approval_status === "REJECTED"
          ? `<span class="status status--rejected" style="padding:4px 8px;border-radius:6px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Từ chối</span>`
          : `<span class="status status--warning" style="padding:4px 8px;border-radius:6px;font-size:12px;font-weight:600;background:#fef3c7;color:#92400e;">Chờ duyệt</span>`);

      return `
        <tr>
          <td><strong>${job.title}</strong><br><small style="color:#64748b;">${job.job_type} · ${job.location || 'Toàn quốc'}</small></td>
          <td>TechNova Solutions</td>
          <td>${createdDate}</td>
          <td>${statusBadge}</td>
          <td>
            <div style="display:flex;gap:6px;">
              <button class="btn btn-sm btn-approve" data-job-id="${job.job_id}" style="background:#16a34a;color:#fff;">Duyệt</button>
              <button class="btn btn-sm btn-reject btn-outline" data-job-id="${job.job_id}" style="color:#dc2626;border-color:#fca5a5;">Từ chối</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");

    // Gắn sự kiện Duyệt & Từ chối
    tableBody.querySelectorAll(".btn-approve").forEach(btn => {
      btn.addEventListener("click", async () => {
        const jId = parseInt(btn.getAttribute("data-job-id"));
        try {
          await UniCareerAPI.admin.setJobApproval(jId, "APPROVED");
          alert(`✅ Đã phê duyệt công khai tin tuyển dụng #${jId}!`);
          loadJobs();
        } catch (err) {
          alert("❌ Lỗi: " + err.message);
        }
      });
    });

    tableBody.querySelectorAll(".btn-reject").forEach(btn => {
      btn.addEventListener("click", async () => {
        const jId = parseInt(btn.getAttribute("data-job-id"));
        try {
          await UniCareerAPI.admin.setJobApproval(jId, "REJECTED");
          alert(`⚠️ Đã từ chối tin tuyển dụng #${jId}.`);
          loadJobs();
        } catch (err) {
          alert("❌ Lỗi: " + err.message);
        }
      });
    });
  }

  async function loadJobs() {
    try {
      allJobs = await UniCareerAPI.admin.getJobs();
      if (countBadge) {
        countBadge.textContent = `${allJobs.length} tin trên hệ thống`;
      }
      renderJobs(allJobs);
    } catch (err) {
      console.warn("Lỗi tải danh sách tin tuyển dụng:", err.message);
    }
  }

  loadJobs();

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = allJobs.filter(j =>
        j.title.toLowerCase().includes(q) ||
        (j.location && j.location.toLowerCase().includes(q))
      );
      renderJobs(filtered);
    });
  }
}
