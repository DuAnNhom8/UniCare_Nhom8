const $=id=>document.getElementById(id);
let adminId=null;
const notify=(message,error=false)=>show($('message'),message,error);
const rowCell=(tr,value)=>{const td=element('td',String(value));tr.append(td);return td;};
async function loadOverview(){
 try{
  const values=await api('/admin/overview');const cards=[['Tài khoản',values.users_total],['Đang hoạt động',values.users_active],['Sinh viên',values.candidate_total],['Nhà tuyển dụng',values.employer_total],['Tin đăng',values.jobs_total],['Tin hoạt động',values.jobs_active],['Tin ẩn',values.jobs_hidden],['Đơn ứng tuyển',values.applications_total]];
  $('overview').replaceChildren();
  for(const [label,number] of cards){const c=element('div','','stat');c.append(element('div',String(number),'stat-number'),element('div',label,'muted small'));$('overview').append(c);}
 }catch(err){notify(err.message,true);}
}
async function loadUsers(){
 try{
  const query=new URLSearchParams({limit:'100'});if($('userRole').value)query.set('role',$('userRole').value);if($('userSearch').value.trim())query.set('keyword',$('userSearch').value.trim());
  const users=await api('/admin/users?'+query);$('users').replaceChildren();
  if(!users.length){const tr=document.createElement('tr');rowCell(tr,'Không tìm thấy tài khoản.').colSpan=6;$('users').append(tr);}
  for(const user of users){
   const tr=document.createElement('tr');rowCell(tr,user.user_id);rowCell(tr,user.email);rowCell(tr,user.role);rowCell(tr,new Date(user.created_at).toLocaleDateString('vi-VN'));rowCell(tr,user.is_active?'Hoạt động':'Bị khóa');
   const td=rowCell(tr,'');const btn=element('button',user.is_active?'Khóa':'Mở khóa',user.is_active?'danger':'secondary');btn.disabled=user.user_id===adminId&&user.is_active;
   btn.onclick=async()=>{if(!confirm(`Xác nhận ${user.is_active?'khóa':'mở khóa'} tài khoản ${user.email}?`))return;btn.disabled=true;try{await api(`/admin/users/${user.user_id}/status`,'PATCH',{is_active:!user.is_active});notify('Đã cập nhật tài khoản.');await Promise.all([loadUsers(),loadOverview()]);}catch(err){notify(err.message,true);btn.disabled=false;}};
   td.append(btn);$('users').append(tr);
  }
 }catch(err){notify(err.message,true);}
}
async function loadJobs(){
 try{
  const query=new URLSearchParams({limit:'100'});if($('jobStatus').value)query.set('status',$('jobStatus').value);if($('jobSearch').value.trim())query.set('keyword',$('jobSearch').value.trim());
  const jobs=await api('/admin/jobs?'+query);$('jobs').replaceChildren();
  if(!jobs.length){const tr=document.createElement('tr');rowCell(tr,'Không có tin phù hợp.').colSpan=5;$('jobs').append(tr);}
  for(const job of jobs){
   const tr=document.createElement('tr');rowCell(tr,job.job_id);rowCell(tr,job.title);rowCell(tr,job.deadline);rowCell(tr,job.status);
   const td=rowCell(tr,'');const hide=job.status!=='HIDDEN';const button=element('button',hide?'Ẩn tin':'Khôi phục',hide?'danger':'secondary');button.disabled=job.status==='CLOSED';
   button.onclick=async()=>{if(!confirm(`${hide?'Ẩn':'Khôi phục'} tin “${job.title}”?`))return;button.disabled=true;try{await api(`/admin/jobs/${job.job_id}/moderate`,'PATCH',{status:hide?'HIDDEN':'ACTIVE'});notify('Đã cập nhật kiểm duyệt.');await Promise.all([loadJobs(),loadOverview()]);}catch(err){notify(err.message,true);button.disabled=false;}};
   td.append(button);$('jobs').append(tr);
  }
 }catch(err){notify(err.message,true);}
}
$('reloadUsers').onclick=loadUsers;
$('reloadJobs').onclick=loadJobs;
$('reloadOverview').onclick=loadOverview;
$('logout').onclick=logout;
currentUser(['ADMIN']).then(me=>{adminId=me.user_id;return Promise.all([loadUsers(),loadJobs(),loadOverview()]);}).catch(err=>notify(err.message,true));
