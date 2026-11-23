/** UniCareer AI Matching – FR-23, FR-24. Mock = đối chiếu kỹ năng, không phải mô hình AI. */
import { api, portalApi, APP_CONFIG } from './api.js';
import { $, esc, setupPortal, notify, errorPanel, setBusy } from './portal-ui.js';

setupPortal();

const page = document.body.dataset.portalPage;
const employer = page === 'ai-recommend';

function skillTags(skills, positive) {
  if (!Array.isArray(skills) || !skills.length) {
    return '<span class="muted" style="font-size:13px">Không ghi nhận kỹ năng trong danh sách đối chiếu.</span>';
  }

  const styles = positive
    ? 'background:#e7f8ef;border-color:#c5ead8;color:#087f61'
    : 'background:#fff5e9;border-color:#f3e0bb;color:#966b24';

  return `<div class="company-skills">${skills.map(skill => `<span class="company-skill" style="${styles}">${esc(skill)}</span>`).join('')}</div>`;
}

function renderResult(container, data) {
  const score = Math.max(0, Math.min(100, Number(data.ai_match_score) || 0));
  const isDemo = APP_CONFIG.MODE === 'mock' || data.is_demo === true || data.engine === 'demo_keyword';
  const matched = data.matched_skills || data.matching_skills || [];
  const missing = data.missing_skills || data.skill_gaps || [];
  const feedback = data.ai_feedback || data.feedback || 'Chưa có nhận xét từ hệ thống.';

  container.innerHTML = `
    <section class="portal-panel">
      <div class="portal-panel__heading">
        <div>
          <h2>Kết quả đánh giá CV</h2>
          <p>${isDemo ? 'Đối chiếu theo từ khóa – dữ liệu mô phỏng' : 'Phản hồi từ dịch vụ phân tích qua Backend'}</p>
        </div>
        <span class="portal-pill ${isDemo ? 'portal-pill--warn' : 'portal-pill--good'}">
          ${isDemo ? 'DEMO – KHÔNG PHẢI AI' : 'Kết quả tham khảo'}
        </span>
      </div>
      <div class="company-match">
        <div class="company-score">
          <strong>${esc(score)}%</strong>
          <span class="meter" aria-label="Mức độ đáp ứng ${esc(score)} phần trăm">
            <i style="width:${score}%"></i>
          </span>
          <small>Tỷ lệ trùng kỹ năng đã nhận diện. Không dùng để xếp loại con người.</small>
        </div>
        <div class="company-match__skills">
          <h3>✓ Kỹ năng phù hợp (${matched.length})</h3>
          ${skillTags(matched, true)}
          <div class="portal-divider"></div>
          <h3>△ Kỹ năng chưa tìm thấy (${missing.length})</h3>
          ${skillTags(missing, false)}
          <h3>Gợi ý cải thiện hồ sơ</h3>
          <p>${esc(feedback)}</p>
        </div>
      </div>
      <p class="company-warning" style="margin:20px 0 0">
        ${isDemo
    ? 'Demo chỉ so khớp các thuật ngữ kỹ năng trong văn bản, không phân tích ý nghĩa hoặc đánh giá năng lực thật.'
    : 'AI chỉ hỗ trợ tham khảo, không tự động từ chối hoặc chấp nhận ứng viên.'}
      </p>
    </section>
  `;
}

async function employerAI() {
  const form = $('#ai-employer-form');
  const job = $('#ai-job');
  const candidate = $('#ai-candidate');
  const result = $('#ai-result');
  const submit = $('#ai-submit');
  let jobs = [];
  let applications = [];

  try {
    [jobs, applications] = await Promise.all([
      portalApi.listEmployerJobs(),
      portalApi.listEmployerApplications(),
    ]);

    // Đồng nhất với nghiệp vụ: chỉ phân tích tin đang mở, đã duyệt, còn hạn.
    const today = new Date().toISOString().slice(0, 10);
    jobs = jobs.filter(jobItem =>
      jobItem.status === 'ACTIVE'
      && jobItem.approval_status === 'APPROVED'
      && (!jobItem.deadline || jobItem.deadline >= today),
    );
    job.innerHTML = '<option value="">Chọn tin đang tuyển...</option>'
      + jobs.map(jobItem => `<option value="${esc(jobItem.job_id)}">${esc(jobItem.title)}</option>`).join('');

    const params = new URLSearchParams(location.search);
    const prefJob = params.get('job');
    const prefCandidate = params.get('candidate');
    if (prefJob && jobs.some(jobItem => String(jobItem.job_id) === prefJob)) {
      job.value = prefJob;
    }

    function updateCandidates() {
      const matched = applications.filter(application => String(application.job_id) === job.value);
      const unique = new Map(matched.map(application => [String(application.candidate_id), application]));
      candidate.innerHTML = '<option value="">Chọn ứng viên đã nộp...</option>'
        + [...unique.values()].map(application => `<option value="${esc(application.candidate_id)}">${esc(application.candidate_name || 'Sinh viên')} (${esc(application.candidate_major || 'Chưa có ngành học')})</option>`).join('');
      candidate.disabled = !job.value || unique.size === 0;
      if (prefCandidate && unique.has(prefCandidate)) candidate.value = prefCandidate;
    }

    job.addEventListener('change', updateCandidates);
    updateCandidates();

    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!job.value || !candidate.value) {
        notify('Hãy chọn tin và ứng viên hợp lệ.', true);
        return;
      }

      setBusy(submit, true, 'Đang đối chiếu kỹ năng...');
      result.innerHTML = '<section class="portal-panel"><div class="loading">Đang phân tích các kỹ năng trong CV...</div></section>';
      try {
        const data = await portalApi.analyzeCV({
          jobId: Number(job.value),
          candidateId: Number(candidate.value),
        });
        renderResult(result, data);
        result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } catch (error) {
        result.innerHTML = `<section class="portal-panel">${errorPanel(error.message)}</section>`;
        notify(error.message, true);
      } finally {
        setBusy(submit, false);
      }
    });
  } catch (error) {
    result.innerHTML = `<section class="portal-panel">${errorPanel(error.message)}</section>`;
    submit.disabled = true;
    notify(error.message, true);
  }
}

async function candidateAI() {
  const form = $('#ai-candidate-form');
  const jobs = $('#candidate-ai-job');
  const cv = $('#candidate-cv-text');
  const result = $('#candidate-ai-result');
  const submit = $('#ai-candidate-submit');

  try {
    const [list, profile] = await Promise.all([
      api.listJobs({ pageSize: 100 }),
      api.getProfile(),
    ]);
    jobs.innerHTML = '<option value="">Chọn công việc muốn đánh giá...</option>'
      + list.items.map(jobItem => `<option value="${esc(jobItem.job_id)}">${esc(jobItem.title)} – ${esc(jobItem.company_name)}</option>`).join('');
    cv.value = [profile.cv_text || '', profile.skills || ''].filter(Boolean).join('\n');

    const preferred = new URLSearchParams(location.search).get('job');
    if (preferred && list.items.some(jobItem => String(jobItem.job_id) === preferred)) {
      jobs.value = preferred;
    }

    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!jobs.value || cv.value.trim().length < 8) {
        notify('Chọn công việc và nhập ít nhất 8 ký tự về CV/kỹ năng.', true);
        return;
      }

      setBusy(submit, true, 'Đang đối chiếu kỹ năng...');
      result.innerHTML = '<section class="portal-panel"><div class="loading">Đang phân tích nội dung CV...</div></section>';
      try {
        const data = await portalApi.analyzeCV({
          jobId: Number(jobs.value),
          cvText: cv.value.trim(),
        });
        renderResult(result, data);
      } catch (error) {
        result.innerHTML = `<section class="portal-panel">${errorPanel(error.message)}</section>`;
        notify(error.message, true);
      } finally {
        setBusy(submit, false);
      }
    });
  } catch (error) {
    result.innerHTML = `<section class="portal-panel">${errorPanel(error.message)}</section>`;
    submit.disabled = true;
    notify(error.message, true);
  }
}

if (employer) {
  employerAI();
} else if (page === 'ai-matching') {
  candidateAI();
}
