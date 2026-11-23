const $ = id => document.getElementById(id);
let company = null;
let jobs = [];
let selectedJob = null;
let editJobId = null;
const statuses = {RECEIVED:'Đã nhận',REVIEWING:'Đang xem xét',MATCHED:'Phù hợp',REJECTED:'Từ chối'};
const notify = (message, error=false) => show($('message'), message, error);
function cell(tr,text) { const td = element('td',String(text ?? '—')); tr.append(td); return td; }
function action(parent,title,handler,style='secondary') { const button = element('button',title,style);button.type='button';button.onclick=handler;parent.append(button);return button; }
async function loadCompany() {
 company=await api('/companies/me');
 $('companyId').textContent=`Mã công ty #${company.company_id}`;
 $('companyName').value=company.company_name;
 $('companyDescription').value=company.description||'';
 $('companyWebsite').value=company.website||'';
}
$('companyForm').onsubmit=async e=>{
 e.preventDefault();
 try {await api('/companies/me','PATCH',{company_name:$('companyName').value.trim(),description:$('companyDescription').value.trim()||null,website:$('companyWebsite').value.trim()||null});notify('Đã lưu thông tin công ty.');}
 catch(err){notify(err.message,true);}
};
function resetJobForm(){ editJobId=null;$('jobForm').reset();$('jobFormTitle').textContent='Đăng tin tuyển dụng';$('saveJob').textContent='Đăng tin'; }
$('cancelJob').onclick=resetJobForm;
$('jobForm').onsubmit=async e=>{
 e.preventDefault();
 const data={title:$('title').value.trim(),deadline:$('deadline').value,location:$('location').value.trim()||null,salary_range:$('salary').value.trim()||null,description:$('description').value.trim(),requirements:$('requirements').value.trim()};
 try { if(editJobId)await api(`/employer/jobs/${editJobId}`,'PATCH',data);else await api('/employer/jobs','POST',data);notify(editJobId?'Đã cập nhật tin.':'Đã đăng tin.');resetJobForm();await loadJobs();}
 catch(err){notify(err.message,true);}
};
function startEdit(job){
 editJobId=job.job_id;
 for(const [key,value] of Object.entries({title:job.title,deadline:job.deadline,location:job.location||'',salary:job.salary_range||'',description:job.description,requirements:job.requirements})){$(key).value=value;}
 $('jobFormTitle').textContent=`Chỉnh sửa tin #${job.job_id}`;$('saveJob').textContent='Lưu chỉnh sửa';
 $('jobForm').scrollIntoView({behavior:'smooth',block:'start'});
}
async function setJobStatus(job,status){
 if(!confirm(`${status==='CLOSED'?'Đóng':status==='HIDDEN'?'Ẩn':'Mở lại'} tin “${job.title}”?`))return;
 try{await api(`/employer/jobs/${job.job_id}`,'PATCH',{status});notify('Đã cập nhật trạng thái tin.');await loadJobs();}
 catch(err){notify(err.message,true);}
}
async function loadJobs(){
 try{
  jobs=await api('/employer/jobs');$('jobs').replaceChildren();
  if(!jobs.length){const tr=document.createElement('tr');cell(tr,'Chưa có tin tuyển dụng.').colSpan=5;$('jobs').append(tr);}
  for(const job of jobs){
   const tr=document.createElement('tr');cell(tr,job.job_id);cell(tr,job.title);cell(tr,job.deadline);cell(tr,job.status);
   const actions=cell(tr,'');actions.className='actions';
   action(actions,'Đơn ứng tuyển',()=>selectJob(job));action(actions,'Sửa',()=>startEdit(job));
   if(job.status==='ACTIVE') {action(actions,'Đóng',()=>setJobStatus(job,'CLOSED'));action(actions,'Ẩn',()=>setJobStatus(job,'HIDDEN'),'danger');}
   if(job.status==='CLOSED')action(actions,'Mở lại',()=>setJobStatus(job,'ACTIVE'));
   $('jobs').append(tr);
  }
  if(selectedJob){const current=jobs.find(j=>j.job_id===selectedJob.job_id);selectedJob=current||null;}
 }catch(err){notify(err.message,true);}
}
async function selectJob(job){selectedJob=job;$('appTitle').textContent=`Đơn ứng tuyển • ${job.title}`;await loadApplications();$('appTitle').scrollIntoView({behavior:'smooth'});}
async function loadApplications(){
 $('applications').replaceChildren();$('detail').classList.add('hidden');
 if(!selectedJob){const tr=document.createElement('tr');cell(tr,'Hãy chọn một tin tuyển dụng.').colSpan=4;$('applications').append(tr);return;}
 try{
  const applications=await api(`/employer/jobs/${selectedJob.job_id}/applications`);
  if(!applications.length){const tr=document.createElement('tr');cell(tr,'Chưa có ứng viên.').colSpan=4;$('applications').append(tr);return;}
  for(const item of applications){
   const tr=document.createElement('tr');cell(tr,item.candidate_name);cell(tr,new Date(item.applied_at).toLocaleString('vi-VN'));
   const statusCell=cell(tr,'');const select=document.createElement('select');select.setAttribute('aria-label',`Trạng thái của ${item.candidate_name}`);
   for(const [code,label] of Object.entries(statuses))select.append(new Option(label,code));select.value=item.status;
   select.onchange=async()=>{select.disabled=true;try{await api(`/employer/applications/${item.application_id}/status`,'PATCH',{status:select.value});notify(`Đã cập nhật trạng thái đơn #${item.application_id}.`);item.status=select.value;}catch(err){select.value=item.status;notify(err.message,true);}finally{select.disabled=false;}};
   statusCell.append(select);
   const acts=cell(tr,'');action(acts,'Xem hồ sơ',()=>viewDetail(item.application_id));$('applications').append(tr);
  }
 }catch(err){notify(err.message,true);}
}
async function viewDetail(applicationId){
 try{
  const data=await api(`/employer/applications/${applicationId}`);const target=$('detail');target.replaceChildren();target.classList.remove('hidden');
  target.append(element('h3',`Hồ sơ • ${data.candidate_name}`));
  for(const [label,value] of [['Vị trí',data.job_title],['Email',data.candidate_email],['Số điện thoại',data.phone],['Trường',data.university],['Ngành học',data.major],['Giới thiệu',data.bio]]){
   const p=document.createElement('p');p.append(element('strong',label+': '),document.createTextNode(value||'Chưa cập nhật'));target.append(p);
  }
  target.append(element('h4','Kỹ năng'));if(!data.skills.length)target.append(element('p','Chưa cập nhật kỹ năng.','muted'));
  for(const skill of data.skills)target.append(element('span',skill,'pill'));
  if(data.has_cv)action(target,'Xem CV PDF',()=>openCV(applicationId));
  else target.append(element('p','Ứng viên chưa tải CV PDF.','muted'));
  target.scrollIntoView({behavior:'smooth',block:'nearest'});
 }catch(err){notify(err.message,true);}
}
async function openCV(applicationId){
 try{
  const res=await fetch(`/employer/applications/${applicationId}/cv`,{headers:{Authorization:'Bearer '+getToken()}});
  if(!res.ok){const value=await res.json();throw Error(value.detail||'Không mở được CV');}
  const pdf=await res.blob();const url=URL.createObjectURL(pdf);const opened=window.open(url,'_blank','noopener,noreferrer');
  if(!opened){const link=document.createElement('a');link.href=url;link.download=`candidate_${applicationId}_cv.pdf`;link.click();}
  setTimeout(()=>URL.revokeObjectURL(url),120000);
 }catch(err){notify(err.message,true);}
}
$('reloadJobs').onclick=loadJobs;
$('reloadApps').onclick=loadApplications;
$('logout').onclick=logout;
currentUser(['EMPLOYER']).then(async()=>{await loadCompany();await loadJobs();await loadApplications();}).catch(err=>notify(err.message,true));
