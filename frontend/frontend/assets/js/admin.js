/** UniCareer Admin – FR-20, FR-21. Mọi thao tác thật phải xác thực role ADMIN trên FastAPI. */
import { portalApi } from './api.js';
import {
  $, $$, esc, niceDate, avatar, pill, ROLE_NAMES, APPROVAL_STATES, JOB_STATES,
  updateCount, setupPortal, notify, errorPanel, confirmDialog, normalize, setBusy,
} from './portal-ui.js';

setupPortal();

const current=document.body.dataset.portalPage;
const state = {
  users: [],
  jobs: [],
  tab: 'PENDING',
  selectedJobId: null,
};

const renderFailure = (selector, error, colspan = 5) => {
  const node = $(selector);
  if (node) {
    node.innerHTML = `<tr><td colspan="${colspan}">${errorPanel(error.message)}</td></tr>`;
  }
};

function person(user) {
  return `<span class="portal-person">${avatar(user.full_name || user.email)}<span><strong>${esc(user.full_name || user.email)}</strong><small>${esc(user.email || '')}</small></span></span>`;
}

function jobName(job) {
  return `<strong>${esc(job.title)}</strong><small>#${esc(job.job_id)} · ${esc(job.job_type || '')}</small>`;
}

async function dashboard() {
  try {
    const data=await portalApi.adminDashboard();
    updateCount('stat-users', data.total_users);
    updateCount('stat-employers', data.total_employers);
    updateCount('stat-jobs', data.total_jobs);
    updateCount('stat-pending', data.pending_jobs);

    const jobs = data.recent_jobs || [];
    const users = data.recent_users || [];

    $('#dashboard-pending').innerHTML = jobs.length
      ? jobs.map(job => `<tr><td>${jobName(job)}</td><td>${esc(job.company_name || '—')}</td><td>${pill(job.approval_status, APPROVAL_STATES)}</td></tr>`).join('')
      : '<tr><td colspan="3">Không có tin chờ duyệt.</td></tr>';

    $('#dashboard-users').innerHTML = users.length
      ? users.map(user => `<tr><td>${person(user)}</td><td>${esc(ROLE_NAMES[user.role] || user.role)}</td><td>${pill(user.is_active ? 'ACTIVE' : 'CLOSED', { ACTIVE: 'Hoạt động', CLOSED: 'Đã khóa' })}</td></tr>`).join('')
      : '<tr><td colspan="3">Chưa có người dùng.</td></tr>';
  } catch (error) {
    renderFailure('#dashboard-pending', error, 3);
    renderFailure('#dashboard-users', error, 3);
    notify(error.message, true);
  }
}

function usersView() {
  const query = normalize($('#user-query').value);
  const role = $('#user-role').value;
  const activity = $('#user-state').value;
  const list = state.users.filter(user =>
    (!query || normalize(`${user.full_name || ''} ${user.email || ''}`).includes(query))
    && (!role || role === user.role)
    && (!activity || (activity === 'active') === Boolean(user.is_active)),
  );

  $('#users-count').textContent = `${list.length} tài khoản`;
  $('#users-body').innerHTML = list.map(user => `
    <tr>
      <td>${person(user)}</td>
      <td>${esc(ROLE_NAMES[user.role] || user.role)}</td>
      <td>${esc(niceDate(user.created_at))}</td>
      <td>${pill(user.is_active ? 'ACTIVE' : 'CLOSED', { ACTIVE: 'Hoạt động', CLOSED: 'Đã khóa' })}</td>
      <td>
        <button
          type="button"
          data-user-id="${esc(user.user_id)}"
          class="portal-text-button ${user.is_active ? 'is-danger' : ''}"
          ${user.role === 'ADMIN' ? 'disabled title="Không xử lý tài khoản admin"' : ''}
        >${user.role === 'ADMIN' ? 'Không áp dụng' : user.is_active ? 'Khóa tài khoản' : 'Mở khóa'}</button>
      </td>
    </tr>
  `).join('') || '<tr><td colspan="5">Không có tài khoản phù hợp.</td></tr>';
}

async function users() {
  try {
    state.users = await portalApi.listUsers();
    usersView();
    $$('#user-query, #user-role, #user-state').forEach(input => {
      input.addEventListener(input.tagName === 'INPUT' ? 'input' : 'change', usersView);
    });

    $('#users-body').addEventListener('click', async event => {
      const button = event.target.closest('[data-user-id]');
      if (!button) return;

      const user = state.users.find(item => String(item.user_id) === button.dataset.userId);
      if (!user || user.role === 'ADMIN') return;

      const next = !Boolean(user.is_active);
      const confirmed = await confirmDialog(
        next ? 'Mở khóa tài khoản?' : 'Khóa tài khoản?',
        `${next ? 'Cho phép' : 'Ngừng cho phép'} ${user.email} đăng nhập vào hệ thống.`,
        next ? 'Mở khóa' : 'Khóa tài khoản',
      );
      if (!confirmed) return;

      setBusy(button, true);
      try {
        await portalApi.setUserActive(user.user_id, next);
        state.users = await portalApi.listUsers();
        usersView();
        notify(`Đã ${next ? 'mở khóa' : 'khóa'} tài khoản ${user.email}.`);
      } catch (error) {
        notify(error.message, true);
        setBusy(button, false);
      }
    });
  } catch (error) {
    renderFailure('#users-body', error);
    notify(error.message, true);
  }
}

function moderationView() {
  $$('.portal-tabs [data-tab]').forEach(button => {
    button.setAttribute('aria-selected', String(button.dataset.tab === state.tab));
  });

  const query = normalize($('#moderation-query').value);
  const filtered = state.jobs.filter(job =>
    job.approval_status === state.tab
    && (!query || normalize(`${job.title} ${job.company_name}`).includes(query)),
  );
  const pending = state.jobs.filter(job => job.approval_status === 'PENDING').length;

  $('#tab-count-pending').textContent = pending ? `(${pending})` : '';
  $('#moderation-count').textContent = `${filtered.length} tin`;
  $('#moderation-body').innerHTML = filtered.map(job => `
    <tr>
      <td>${jobName(job)}</td>
      <td>${esc(job.company_name)}</td>
      <td>${esc(niceDate(job.created_at))}</td>
      <td>${pill(job.status, JOB_STATES)}</td>
      <td>
        <button type="button" class="portal-text-button" data-detail-job="${esc(job.job_id)}">
          Xem chi tiết →
        </button>
      </td>
    </tr>
  `).join('') || '<tr><td colspan="5">Không có tin phù hợp bộ lọc.</td></tr>';

  if (state.selectedJobId) showModerationDetail(state.selectedJobId);
}

function showModerationDetail(jobId) {
  const job = state.jobs.find(item => String(item.job_id) === String(jobId));
  if (!job) return;

  const mount = $('#moderation-detail');
  mount.hidden = false;
  state.selectedJobId = job.job_id;
  $('#moderation-title').textContent = job.title;
  $('#moderation-company').textContent = `${job.company_name || 'Doanh nghiệp'} · Mã #${job.job_id}`;
  $('#moderation-detail-body').innerHTML = `
    <div class="portal-detail">
      <div>
        <h3>Mô tả công việc</h3>
        <p style="white-space:pre-line">${esc(job.description || 'Chưa có mô tả.')}</p>
        <h3>Yêu cầu ứng viên</h3>
        <p style="white-space:pre-line">${esc(job.requirements || 'Chưa có yêu cầu.')}</p>
      </div>
      <aside>
        <dl>
          <div class="portal-definition"><dt>Địa điểm</dt><dd>${esc(job.location || '—')}</dd></div>
          <div class="portal-definition"><dt>Mức lương</dt><dd>${esc(job.salary_range || 'Thỏa thuận')}</dd></div>
          <div class="portal-definition"><dt>Loại hình</dt><dd>${esc(job.job_type || '—')}</dd></div>
          <div class="portal-definition"><dt>Hạn ứng tuyển</dt><dd>${esc(niceDate(job.deadline))}</dd></div>
          <div class="portal-definition"><dt>Trạng thái tin</dt><dd>${pill(job.status, JOB_STATES)}</dd></div>
          <div class="portal-definition"><dt>Kiểm duyệt</dt><dd>${pill(job.approval_status, APPROVAL_STATES)}</dd></div>
        </dl>
      </aside>
    </div>
  `;

  const buttons = [];
  if (job.approval_status === 'PENDING') {
    buttons.push(
      '<button class="btn" type="button" data-moderate="APPROVED">✓ Phê duyệt</button>',
      '<button class="btn btn-outline" type="button" data-moderate="REJECTED">✕ Từ chối</button>',
    );
  }
  if (job.status !== 'HIDDEN') {
    buttons.push('<button class="btn btn-outline" type="button" data-moderate="HIDDEN">Ẩn tin vi phạm</button>');
  }
  $('#moderation-actions').innerHTML = buttons.join('')
    || '<span class="muted">Tin đã ẩn; không còn thao tác khả dụng.</span>';
}

async function moderation() {
  try {
    state.jobs = await portalApi.listModerationJobs();
    moderationView();

    $$('.portal-tabs [data-tab]').forEach(button => {
      button.addEventListener('click', () => {
        state.tab = button.dataset.tab;
        state.selectedJobId = null;
        $('#moderation-detail').hidden = true;
        moderationView();
      });
    });

    $('#moderation-query').addEventListener('input', moderationView);
    $('#moderation-body').addEventListener('click', event => {
      const button = event.target.closest('[data-detail-job]');
      if (!button) return;

      showModerationDetail(button.dataset.detailJob);
      $('#moderation-detail').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    $('#moderation-close').addEventListener('click', () => {
      state.selectedJobId = null;
      $('#moderation-detail').hidden = true;
    });

    $('#moderation-actions').addEventListener('click', async event => {
      const button = event.target.closest('[data-moderate]');
      if (!button || !state.selectedJobId) return;

      const action = button.dataset.moderate;
      const label = action === 'APPROVED' ? 'phê duyệt' : action === 'REJECTED' ? 'từ chối' : 'ẩn';
      const confirmed = await confirmDialog(
        `Xác nhận ${label} tin?`,
        `Quyết định sẽ thay đổi trạng thái tin tuyển dụng #${state.selectedJobId}.`,
        `Xác nhận ${label}`,
      );
      if (!confirmed) return;

      setBusy(button, true);
      try {
        if (action === 'HIDDEN') {
          await portalApi.hideJob(state.selectedJobId);
        } else {
          await portalApi.moderateJob(state.selectedJobId, action);
        }
        state.jobs = await portalApi.listModerationJobs();
        moderationView();
        notify(`Đã ${label} tin tuyển dụng.`);
      } catch (error) {
        notify(error.message, true);
        setBusy(button, false);
      }
    });
  } catch (error) {
    renderFailure('#moderation-body', error);
    notify(error.message, true);
  }
}

if (current === 'dashboard') {
  dashboard();
} else if (current === 'users') {
  users();
} else if (current === 'approve-jobs') {
  moderation();
}
