/** UniCareer Employer – FR-17, FR-18. Chỉ xem đơn thuộc tin mình quản lý (API server phải bảo vệ). */
import {portalApi} from './api.js';
import {$,$$,esc,avatar,niceDateTime,pill,APPLICATION_STATES,updateCount,setupPortal,notify,errorPanel,emptyPanel,confirmDialog,normalize,setBusy} from './portal-ui.js';
setupPortal();
const state={jobs:[],applications:[],selectedId:null};
const search=()=>({q:normalize($('#app-query')?.value||''),job:$('#app-job')?.value||'',status:$('#app-status')?.value||''});
function renderStats(){const list=state.applications;updateCount('app-total',list.length);for(const st of ['RECEIVED','REVIEWING','ACCEPTED'])updateCount('app-'+st.toLowerCase(),list.filter(a=>a.status===st).length);}
function renderList(){
  const {q,job,status}=search();const list=state.applications.filter(a=>(!q||normalize(`${a.candidate_name} ${a.candidate_email} ${a.candidate_major}`).includes(q))&&(!job||String(a.job_id)===job)&&(!status||a.status===status));
  $('#app-visible-count').textContent=`${list.length} hồ sơ`;
  const mount=$('#applications-body');
  mount.innerHTML=list.map(a=>`<tr><td><span class="portal-person">${avatar(a.candidate_name,'portal-avatar--mint')}<span><strong>${esc(a.candidate_name||'Sinh viên')}</strong><small>${esc(a.candidate_email||'—')}</small></span></span></td><td><strong>${esc(a.job_title||'Công việc')}</strong><small>Mã tin #${esc(a.job_id)}</small></td><td>${esc(niceDateTime(a.applied_at))}</td><td>${pill(a.status,APPLICATION_STATES)}</td><td><button type="button" class="portal-text-button" data-application-id="${esc(a.application_id)}">Xem hồ sơ →</button></td></tr>`).join('')||'<tr><td colspan="5">Không có hồ sơ phù hợp.</td></tr>';
  if(state.selectedId){const selected=state.applications.find(a=>String(a.application_id)===String(state.selectedId));if(selected)renderDetail(selected);else closeDetail();}
}
function closeDetail(){state.selectedId=null;$('#applicant-detail').hidden=true;}
function renderDetail(a){state.selectedId=a.application_id;$('#applicant-detail').hidden=false;
 const skills=String(a.candidate_skills||'').split(',').map(x=>x.trim()).filter(Boolean);
 const html=`<div class="portal-detail"><div><div class="company-profile">${avatar(a.candidate_name,'portal-avatar--mint')}<div><h3>${esc(a.candidate_name)}</h3><p>${esc(a.candidate_email||'Email chưa cập nhật')}</p></div></div><dl><div class="portal-definition"><dt>Trường</dt><dd>${esc(a.candidate_university||'Chưa cập nhật')}</dd></div><div class="portal-definition"><dt>Chuyên ngành</dt><dd>${esc(a.candidate_major||'Chưa cập nhật')}</dd></div><div class="portal-definition"><dt>Ứng tuyển</dt><dd>${esc(a.job_title||'—')}</dd></div><div class="portal-definition"><dt>Ngày nộp</dt><dd>${esc(niceDateTime(a.applied_at))}</dd></div></dl><h3>Kỹ năng</h3><div class="company-skills">${skills.length?skills.map(s=>`<span class="company-skill">${esc(s)}</span>`).join(''):'<span class="muted">Sinh viên chưa khai báo kỹ năng.</span>'}</div><h3>Giới thiệu</h3><p>${esc(a.candidate_bio||'Chưa có nội dung.')}</p><h3>Thông tin CV</h3><p>${esc(a.cv_filename||'Chưa đính kèm tệp CV.')}</p><small class="portal-help">Bản mock chỉ lưu tên tệp, không có file PDF để tải. Khi kết nối Backend sẽ dùng URL CV được xác thực.</small></div>
 <aside><div class="company-status-form"><h3>Trạng thái xử lý đơn</h3><p class="portal-help">Trạng thái hiện tại: ${pill(a.status,APPLICATION_STATES)}</p><div class="field"><label for="company-status-select">Chuyển sang trạng thái</label><select id="company-status-select">${Object.entries(APPLICATION_STATES).map(([key,label])=>`<option value="${key}" ${key===a.status?'selected':''}>${esc(label)}</option>`).join('')}</select></div><button type="button" class="btn btn-full" id="company-save-status" data-save-application="${esc(a.application_id)}">Lưu trạng thái</button></div><div class="portal-divider"></div><a class="btn btn-outline btn-full" href="ai-recommend.html?job=${encodeURIComponent(a.job_id)}&candidate=${encodeURIComponent(a.candidate_id)}">✧ Đối chiếu kỹ năng CV</a><p class="portal-help" style="margin-top:13px">AI chỉ hỗ trợ tham khảo. Việc chấp nhận hoặc từ chối đơn là quyết định của nhà tuyển dụng.</p></aside></div>`;
 $('#applicant-detail-content').innerHTML=html;
}
async function load(){
  try{
    const [jobs,applications]=await Promise.all([portalApi.listEmployerJobs(),portalApi.listEmployerApplications()]);
    state.jobs=jobs;state.applications=applications;
    const jobSelect=$('#app-job');jobSelect.innerHTML='<option value="">Tất cả tin của tôi</option>'+jobs.map(j=>`<option value="${esc(j.job_id)}">${esc(j.title)}</option>`).join('');
    const jobFromURL=new URLSearchParams(location.search).get('job');if(jobFromURL&&jobs.some(j=>String(j.job_id)===jobFromURL))jobSelect.value=jobFromURL;
    renderStats();renderList();
  }catch(err){$('#applications-body').innerHTML=`<tr><td colspan="5">${errorPanel(err.message)}</td></tr>`;notify(err.message,true);}
}
$('#app-query')?.addEventListener('input',renderList);
$('#app-job')?.addEventListener('change',renderList);
$('#app-status')?.addEventListener('change',renderList);
$('#applications-body')?.addEventListener('click',e=>{const btn=e.target.closest('[data-application-id]');if(!btn)return;const a=state.applications.find(x=>String(x.application_id)===btn.dataset.applicationId);if(!a)return;renderDetail(a);$('#applicant-detail').scrollIntoView({behavior:'smooth',block:'start'});});
$('#applicant-close')?.addEventListener('click',closeDetail);
$('#applicant-detail-content')?.addEventListener('click',async e=>{
  const btn=e.target.closest('[data-save-application]');if(!btn)return;
  const a=state.applications.find(x=>String(x.application_id)===btn.dataset.saveApplication);if(!a)return;
  const next=$('#company-status-select')?.value;if(!next||next===a.status){notify('Trạng thái không thay đổi.');return;}
  if(!await confirmDialog('Cập nhật trạng thái đơn?',`Chuyển hồ sơ của ${a.candidate_name} sang “${APPLICATION_STATES[next]}”.`,'Cập nhật'))return;
  setBusy(btn,true);try{await portalApi.changeApplicationStatus(a.application_id,next);state.applications=await portalApi.listEmployerApplications();renderStats();renderList();notify(`Đã cập nhật hồ sơ của ${a.candidate_name} sang “${APPLICATION_STATES[next]}”.`);}catch(err){notify(err.message,true);setBusy(btn,false);}
});
load();
