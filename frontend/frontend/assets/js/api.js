/**
 * UniCareer API adapter.
 * SRS_UniCare.docx quy định REST API nhưng KHÔNG quy định endpoint cụ thể.
 * MODE = 'mock' để chạy độc lập; chuyển thành 'api' khi Backend xác nhận contract.
 * Không dùng dữ liệu localStorage/mock làm xác thực hoặc phân quyền thật.
 */
export const APP_CONFIG = Object.freeze({
  MODE: 'mock', // 'mock' | 'api'
  API_BASE_URL: 'http://127.0.0.1:8000',
  API_PREFIX: '/api', // chỉnh theo router FastAPI của nhóm
  PAGE_SIZE: 6,
  STORAGE_PREFIX: 'unicareer_fe_demo_v1'
});

export const STATUS_LABELS = Object.freeze({
  RECEIVED: 'Đã tiếp nhận', REVIEWING: 'Đang xem xét',
  ACCEPTED: 'Đã chấp nhận', REJECTED: 'Đã từ chối'
});
export const TYPE_LABELS = Object.freeze({
  INTERNSHIP: 'Thực tập', PART_TIME: 'Bán thời gian', FULL_TIME: 'Toàn thời gian'
});
const key = suffix => `${APP_CONFIG.STORAGE_PREFIX}_${suffix}`;
const today = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
const dateOffset = (days) => {
  const d = new Date(); d.setHours(12, 0, 0, 0); d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
};
const clean = str => String(str ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase().trim();
const baseJobs = [
  [101,'Thực tập sinh Backend Python','TechNova','TP. Hồ Chí Minh','3 - 5 triệu','INTERNSHIP','Không yêu cầu','Python, FastAPI, MySQL',34],
  [102,'Frontend Developer Intern','BluePeak Digital','TP. Hồ Chí Minh','4 - 6 triệu','INTERNSHIP','Không yêu cầu','HTML, CSS, JavaScript',37],
  [103,'Data Analyst Intern','NextStep Labs','Hà Nội','5 - 7 triệu','INTERNSHIP','Không yêu cầu','SQL, Excel, Python',27],
  [104,'Thực tập sinh QA Tester','Brightsoft','Đà Nẵng','3 - 4 triệu','INTERNSHIP','Không yêu cầu','Testing, API, Postman',25],
  [105,'UI/UX Design Intern','Mosaic Studio','TP. Hồ Chí Minh','Thỏa thuận','INTERNSHIP','Không yêu cầu','Figma, Prototype, Design',41],
  [106,'Full-stack Developer Junior','CloudNest','Hà Nội','12 - 18 triệu','FULL_TIME','Dưới 1 năm','JavaScript, Python, SQL',50],
  [107,'Thực tập sinh Business Analyst','Prism Solutions','TP. Hồ Chí Minh','4 - 5 triệu','INTERNSHIP','Không yêu cầu','UML, SQL, Documentation',38],
  [108,'Chuyên viên hỗ trợ kỹ thuật','NovaCare','Đà Nẵng','7 - 10 triệu','FULL_TIME','Dưới 1 năm','Networking, SQL, Support',44],
  [109,'Thực tập sinh DevOps','Orbit Tech','Hà Nội','5 - 8 triệu','INTERNSHIP','Không yêu cầu','Linux, Docker, Git',31],
  [110,'Cộng tác viên Content Marketing','HelloWork Studio','Làm việc từ xa','Thỏa thuận','PART_TIME','Không yêu cầu','SEO, Viết nội dung, Marketing',33],
  [111,'Junior Mobile Flutter Developer','PixelWave','TP. Hồ Chí Minh','10 - 15 triệu','FULL_TIME','1–2 năm','Flutter, Dart, REST API',46],
  [112,'Thực tập sinh Database Developer','ByteWorks','Hà Nội','4 - 6 triệu','INTERNSHIP','Không yêu cầu','MySQL, SQL, Python',29],
  [113,'Product Operations Part-time','FieldLab','Làm việc từ xa','6 - 8 triệu','PART_TIME','Không yêu cầu','Excel, SQL, Giao tiếp',53],
  [114,'Backend Engineer','Internal Example','TP. Hồ Chí Minh','15 - 22 triệu','FULL_TIME','1–2 năm','Python, FastAPI, MySQL',-3],
  [115,'Frontend Intern (chờ duyệt)','Internal Example','Hà Nội','3 - 5 triệu','INTERNSHIP','Không yêu cầu','HTML, CSS',29]
];
const mockJobs = baseJobs.map(([job_id,title,company_name,location,salary_range,job_type,experience_level,skillsString,deadlineDays]) => {
  // Kept as individually named fields for straightforward mapping to JOB_POSTS.
  const job = {job_id, company_id: job_id, company_name,
    title, location, salary_range, job_type, experience_level,
    skills:skillsString.split(',').map(s=>s.trim()),
    deadline:dateOffset(deadlineDays), status:'ACTIVE', approval_status:'APPROVED',
    created_at:dateOffset(-1 - (job_id - 101))};
  job.description = `Cùng ${company_name} phát triển các sản phẩm và quy trình chuyên nghiệp.\nTham gia các nhiệm vụ thực tế phù hợp với vị trí ${job.title}.\nPhối hợp cùng nhóm để hoàn thành công việc đúng tiến độ.\nĐược hướng dẫn, nhận phản hồi và trau dồi kỹ năng.`;
  job.requirements = `Có kiến thức nền tảng về ${job.skills.join(', ')}.\nCó tinh thần trách nhiệm, chủ động học hỏi và khả năng làm việc nhóm.\nƯu tiên sinh viên hoặc người mới đi làm có dự án thực tế.`;
  job.benefits = 'Môi trường học tập năng động và có người hướng dẫn.\nTham gia dự án thực tế, phát triển kỹ năng chuyên môn.\nChế độ hỗ trợ theo nội dung tuyển dụng.';
  job.company_description = `${company_name} là doanh nghiệp giả lập dùng cho bản demo frontend UniCareer.`;
  return job;
});
// Không để hiển thị tin chờ duyệt hoặc đã đóng trong danh sách công khai.
mockJobs.find(j=>j.job_id===114).status='CLOSED';
mockJobs.find(j=>j.job_id===115).approval_status='PENDING';

export class ApiError extends Error {
  constructor(message, status = 0) { super(message); this.name='ApiError'; this.status=status; }
}

function readJSON(name, fallback) {
  try { const value=localStorage.getItem(key(name)); return value ? JSON.parse(value) : fallback; }
  catch { return fallback; }
}
function writeJSON(name, value) {
  try { localStorage.setItem(key(name),JSON.stringify(value)); }
  catch { throw new ApiError('Không thể lưu dữ liệu trình duyệt. Hãy kiểm tra chế độ riêng tư hoặc bộ nhớ.'); }
}
const DEFAULT_PROFILE = Object.freeze({
  candidate_id:1, full_name:'Nguyễn Minh Anh', email:'minhanh@student.example',
  phone:'0900 123 456', university:'Đại học Công nghệ', major:'Công nghệ thông tin',
  skills:'Python, FastAPI, MySQL', bio:'Sinh viên yêu thích phát triển ứng dụng web.', cv_text:'', cv_filename:''
});
function baseURL(path) { return `${APP_CONFIG.API_BASE_URL.replace(/\/$/,'')}${APP_CONFIG.API_PREFIX}${path}`; }
async function request(path, {method='GET', data=null, multipart=false}={}) {
  const token = sessionStorage.getItem('unicareer_access_token');
  const headers={Accept:'application/json', ...(token?{Authorization:`Bearer ${token}`}:{})};
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),15000);
  try {
    let body;
    if(data!==null){ if(multipart){body=data;}else{headers['Content-Type']='application/json';body=JSON.stringify(data);} }
    const res=await fetch(baseURL(path),{method,headers,body,signal:controller.signal});
    let payload=null;
    try { payload=await res.json(); } catch { /* 204 or non-JSON response */ }
    if(!res.ok){
      let error = payload?.detail || payload?.message || `Yêu cầu thất bại (HTTP ${res.status}).`;
      if(Array.isArray(error))error=error.map(e=>e.msg).join('; ');
      throw new ApiError(String(error),res.status);
    }
    return payload;
  } catch(err){
    if(err.name==='AbortError') throw new ApiError('Máy chủ phản hồi quá lâu. Vui lòng thử lại.');
    if(err instanceof ApiError)throw err;
    throw new ApiError('Không kết nối được FastAPI. Kiểm tra API_BASE_URL, CORS và máy chủ.');
  } finally {clearTimeout(timeout);}
}
const isPublic = (j) => j.status==='ACTIVE' && j.approval_status==='APPROVED' && (!j.deadline || j.deadline>=today());
const getSalaryNums = s => (String(s||'').match(/\d+(?:[.,]\d+)?/g)||[]).map(n=>Number(n.replace(',','.')));
function salaryMatches(salary, filter) {
  if(!filter)return true;
  if(filter==='negotiable')return clean(salary).includes('thoa thuan');
  const nums = getSalaryNums(salary); if(nums.length===0)return false;
  const low=nums[0], high=nums[1]??nums[0];
  if(filter==='under5')return low<5;
  if(filter==='5to10')return high>=5 && low<=10;
  if(filter==='over10')return high>10;
  return true;
}
const normalizeJob = j => ({...j,job_id:j.job_id??j.id,company_name:j.company_name??j.company?.company_name??j.company?.name??'Doanh nghiệp',skills:Array.isArray(j.skills)?j.skills:[]});

export const api = {
  async listJobs({q='',location='',type='',salary='',experience='',sort='newest',page=1,pageSize=APP_CONFIG.PAGE_SIZE}={}){
    let jobs;
    if(APP_CONFIG.MODE==='mock') {
      jobs=currentMockJobs().filter(isPublic);
    } else {
      // Contract dự kiến: GET /api/jobs; đổi endpoint & field theo Backend thực tế.
      // Giai đoạn tích hợp MVP: endpoint cần trả về danh sách để lọc/phân trang ở FE.
      // Nếu Backend dùng server-side pagination, sửa logic này theo response metadata.
      const result=await request('/jobs');
      jobs=(Array.isArray(result)?result:(result?.items??result?.results??result?.jobs??result?.data??[])).map(normalizeJob).filter(isPublic);
      // Nếu API đã phân trang phía server, cần thống nhất total/pages với Backend.
    }
    const query=clean(q);
    jobs=jobs.filter(j=>!query||clean([j.title,j.company_name,j.description,...(j.skills||[])].join(' ')).includes(query));
    jobs=jobs.filter(j=>!location||clean(j.location).includes(clean(location)));
    jobs=jobs.filter(j=>!type||j.job_type===type);
    jobs=jobs.filter(j=>salaryMatches(j.salary_range,salary));
    jobs=jobs.filter(j=>!experience||clean(j.experience_level).includes(clean(experience)));
    jobs=[...jobs].sort((a,b)=>{
      if(sort==='deadline')return a.deadline.localeCompare(b.deadline);
      if(sort==='salary')return (getSalaryNums(b.salary_range)[0]??0)-(getSalaryNums(a.salary_range)[0]??0);
      return b.created_at.localeCompare(a.created_at);
    });
    const total=jobs.length;
    const totalPages=Math.max(1,Math.ceil(total/pageSize));
    const safePage=Math.min(Math.max(1,Number(page)||1),totalPages);
    return {items:jobs.slice((safePage-1)*pageSize,safePage*pageSize),total,totalPages,page:safePage};
  },
  async getJob(jobId){
    if(APP_CONFIG.MODE==='mock'){
      const j=currentMockJobs().find(x=>String(x.job_id)===String(jobId));
      if(!j)throw new ApiError('Không tìm thấy công việc.',404);
      return {...j};
    }
    return normalizeJob(await request(`/jobs/${encodeURIComponent(jobId)}`));
  },
  async getProfile(){
    if(APP_CONFIG.MODE==='mock')return {...DEFAULT_PROFILE,...readJSON('profile',{})};
    return await request('/candidate/profile');
  },
  async saveProfile(profile){
    if(APP_CONFIG.MODE==='mock'){
      const next={...DEFAULT_PROFILE,...readJSON('profile',{}),...profile};writeJSON('profile',next);return next;
    }
    return request('/candidate/profile',{method:'PUT',data:profile});
  },
  async listApplications(){
    if(APP_CONFIG.MODE==='mock')return readJSON('applications',[]);
    const result=await request('/candidate/applications');
    return Array.isArray(result)?result:(result?.items??result?.applications??[]);
  },
  async submitApplication({jobId,coverLetter='',cvFile=null}){
    if(APP_CONFIG.MODE==='mock'){
      const job=await this.getJob(jobId);
      if(!isPublic(job))throw new ApiError('Tin không còn mở hoặc chưa được kiểm duyệt.',400);
      const apps=await this.listApplications();
      if(apps.some(a=>String(a.job_id)===String(jobId)))throw new ApiError('Bạn đã ứng tuyển vào công việc này.',409);
      const application={application_id:Date.now(),job_id:Number(jobId),job_title:job.title,company_name:job.company_name,
        candidate_id:1,status:'RECEIVED',applied_at:new Date().toISOString(),cover_letter:coverLetter.trim(),
        cv_filename:cvFile?.name??'',note:'Chỉ lưu tên tệp CV trong mock; không tải nội dung tệp lên máy chủ.'};
      writeJSON('applications',[application,...apps]);return application;
    }
    // Trường hợp CV: gửi multipart. Cần đổi tên field theo endpoint FastAPI thực tế.
    if(cvFile){const data=new FormData();data.append('job_id',String(jobId));data.append('cover_letter',coverLetter);data.append('cv',cvFile);return request('/applications',{method:'POST',data,multipart:true});}
    return request('/applications',{method:'POST',data:{job_id:Number(jobId),cover_letter:coverLetter}});
  }
};


/* ===================================================================
 * UNI CAREER PORTAL: 3 TASK MỚI (Admin / Employer / AI)
 * Đây là bộ dữ liệu & API adapter của frontend, KHÔNG có xác thực quyền
 * thực tế trong MOCK. Backend FastAPI phải kiểm tra role + ownership.
 * =================================================================== */
const MOCK_USERS = Object.freeze([
  {user_id:1,email:'minhanh@student.example',role:'CANDIDATE',is_active:true,created_at:dateOffset(-13),full_name:'Nguyễn Minh Anh'},
  {user_id:2,email:'hr@technova.example',role:'EMPLOYER',is_active:true,created_at:dateOffset(-30),full_name:'Nhà tuyển dụng TechNova'},
  {user_id:3,email:'baongoc@student.example',role:'CANDIDATE',is_active:true,created_at:dateOffset(-20),full_name:'Lê Bảo Ngọc'},
  {user_id:4,email:'minhkhoi@student.example',role:'CANDIDATE',is_active:true,created_at:dateOffset(-17),full_name:'Trần Minh Khôi'},
  {user_id:5,email:'thanhha@student.example',role:'CANDIDATE',is_active:false,created_at:dateOffset(-23),full_name:'Phạm Thanh Hà'},
  {user_id:99,email:'admin@unicareer.example',role:'ADMIN',is_active:true,created_at:dateOffset(-65),full_name:'Quản trị UniCareer'}
]);
const MOCK_PROFILES = Object.freeze({
  3:{candidate_id:3,full_name:'Lê Bảo Ngọc',university:'Đại học Công nghệ',major:'Công nghệ thông tin',skills:'Python, SQL, FastAPI, Git',bio:'Đã hoàn thành dự án API quản lý sinh viên.',cv_text:'Python FastAPI SQL MySQL Git REST API'},
  4:{candidate_id:4,full_name:'Trần Minh Khôi',university:'Đại học Sư phạm Kỹ thuật',major:'Kỹ thuật phần mềm',skills:'Python, MySQL, Docker, Git',bio:'Yêu thích thiết kế backend.',cv_text:'Python MySQL Docker Git, phát triển web backend'},
  5:{candidate_id:5,full_name:'Phạm Thanh Hà',university:'Đại học Kinh tế',major:'Hệ thống thông tin',skills:'HTML, CSS, JavaScript, Excel',bio:'Quan tâm phân tích nghiệp vụ.',cv_text:'HTML CSS JavaScript Excel SQL'}
});
const SEED_EMPLOYER_APPS = Object.freeze([
  {application_id:801,job_id:101,candidate_id:3,status:'RECEIVED',applied_at:dateOffset(-1)+'T09:15:00',cv_filename:'BaoNgoc_CV.pdf'},
  {application_id:802,job_id:101,candidate_id:4,status:'REVIEWING',applied_at:dateOffset(-2)+'T14:30:00',cv_filename:'MinhKhoi_CV.pdf'},
  {application_id:803,job_id:101,candidate_id:5,status:'REJECTED',applied_at:dateOffset(-4)+'T08:45:00',cv_filename:'ThanhHa_CV.pdf'},
  {application_id:804,job_id:102,candidate_id:3,status:'ACCEPTED',applied_at:dateOffset(-5)+'T10:00:00',cv_filename:'BaoNgoc_CV.pdf'}
]);
const EXTRA_JOBS = Object.freeze([
  {job_id:116,company_id:116,company_name:'SkyLab',title:'Thực tập sinh Software Tester',location:'Đà Nẵng',salary_range:'4 - 6 triệu',job_type:'INTERNSHIP',experience_level:'Không yêu cầu',skills:['Testing','Postman','Git'],deadline:dateOffset(35),status:'ACTIVE',approval_status:'PENDING',created_at:dateOffset(-1),description:'Tham gia kiểm thử web và API. Báo cáo lỗi sản phẩm.',requirements:'Biết test case, Postman và Git.',company_description:'SkyLab - công ty demo.'},
  {job_id:117,company_id:117,company_name:'DataSpring',title:'Data Engineer Fresher',location:'Hà Nội',salary_range:'8 - 12 triệu',job_type:'FULL_TIME',experience_level:'Dưới 1 năm',skills:['Python','SQL','ETL'],deadline:dateOffset(40),status:'ACTIVE',approval_status:'PENDING',created_at:dateOffset(-2),description:'Xây dựng pipeline dữ liệu và báo cáo.',requirements:'Python, SQL, xử lý dữ liệu.',company_description:'DataSpring - công ty demo.'}
]);
function currentMockJobs(){
  const overrides=readJSON('portal_job_overrides',{});
  return [...mockJobs,...EXTRA_JOBS].map(j=>({...j,...(overrides[String(j.job_id)]||{})}));
}
function mockUsers(){return readJSON('portal_users',MOCK_USERS.map(u=>({...u})));}
function mockEmployerApplications(){return readJSON('portal_employer_apps',SEED_EMPLOYER_APPS.map(a=>({...a})));}
function getCandidateName(id){return mockUsers().find(u=>Number(u.user_id)===Number(id))?.full_name||'Sinh viên';}
const mockEmployerCompanyId=101; // demo: TechNova (Employer id=2) quản lý các tin company_id=101
const normalizeList=(res,keys=['items'])=> Array.isArray(res)?res:(keys.map(k=>res?.[k]).find(Array.isArray)||[]);
function requirePositiveId(id){if(!Number.isInteger(Number(id))||Number(id)<=0)throw new ApiError('Mã không hợp lệ.',400);return Number(id);}
function findMockJob(id){const j=currentMockJobs().find(j=>j.job_id===Number(id));if(!j)throw new ApiError('Không tìm thấy tin.',404);return j;}
function ensureMockEmployerJob(jobId){const job=findMockJob(jobId);if(job.company_id!==mockEmployerCompanyId)throw new ApiError('Tin này không thuộc doanh nghiệp demo.',403);return job;}
const upsertApps=(applicationId, status)=>{
  const own=readJSON('applications',[]);
  const i=own.findIndex(a=>String(a.application_id)===String(applicationId));
  if(i!==-1){own[i]={...own[i],status};writeJSON('applications',own);return own[i];}
  const seeded=mockEmployerApplications();const j=seeded.findIndex(a=>String(a.application_id)===String(applicationId));
  if(j===-1)throw new ApiError('Không tìm thấy đơn ứng tuyển.',404);
  seeded[j]={...seeded[j],status};writeJSON('portal_employer_apps',seeded);return seeded[j];
};
const ALLOWED_APPLICATION_STATUSES=['RECEIVED','REVIEWING','ACCEPTED','REJECTED'];
const ALLOWED_APPROVALS=['PENDING','APPROVED','REJECTED'];
// Các API dưới đây chỉ được dùng trong giao diện demo hoặc nối với router FastAPI
// đã xác thực quyền. Không coi sessionStorage hay kiểm tra UI là bảo mật thực tế.
export const portalApi={
  async adminDashboard(){
    if(APP_CONFIG.MODE==='api')return request('/admin/dashboard');
    const users=mockUsers(),jobs=currentMockJobs();return {
      total_users:users.length,total_employers:users.filter(u=>u.role==='EMPLOYER').length,
      total_jobs:jobs.length,pending_jobs:jobs.filter(j=>j.approval_status==='PENDING').length,
      recent_jobs:jobs.filter(j=>j.approval_status==='PENDING').slice(0,5),
      recent_users:[...users].sort((a,b)=>b.created_at.localeCompare(a.created_at)).slice(0,5)
    };
  },
  async listUsers(){return APP_CONFIG.MODE==='api'?normalizeList(await request('/admin/users'),['items','users']):mockUsers().map(x=>({...x}));},
  async setUserActive(userId,isActive){
    userId=requirePositiveId(userId);
    if(APP_CONFIG.MODE==='api')return request(`/admin/users/${userId}/status`,{method:'PATCH',data:{is_active:Boolean(isActive)}});
    const users=mockUsers(),idx=users.findIndex(u=>u.user_id===userId);
    if(idx===-1)throw new ApiError('Không tìm thấy tài khoản.',404);
    if(users[idx].role==='ADMIN')throw new ApiError('Không khóa/mở tài khoản quản trị trong bản demo.',403);
    users[idx]={...users[idx],is_active:Boolean(isActive)};writeJSON('portal_users',users);return {...users[idx]};
  },
  async listModerationJobs(){return APP_CONFIG.MODE==='api'?normalizeList(await request('/admin/jobs'),['items','jobs']):currentMockJobs();},
  async moderateJob(jobId, approvalStatus){
    jobId=requirePositiveId(jobId);approvalStatus=String(approvalStatus).toUpperCase();
    if(!ALLOWED_APPROVALS.includes(approvalStatus)||approvalStatus==='PENDING')throw new ApiError('Quyết định kiểm duyệt không hợp lệ.',400);
    if(APP_CONFIG.MODE==='api')return request(`/admin/jobs/${jobId}/approval`,{method:'PATCH',data:{approval_status:approvalStatus}});
    const job=findMockJob(jobId);
    if(job.approval_status!=='PENDING')throw new ApiError('Chỉ tin chờ duyệt mới được phê duyệt hoặc từ chối.',409);
    const patch={approval_status:approvalStatus};
    const all=readJSON('portal_job_overrides',{});all[jobId]={...(all[jobId]||{}),...patch};writeJSON('portal_job_overrides',all);
    return {...job,...patch};
  },
  async hideJob(jobId){
    jobId=requirePositiveId(jobId);
    if(APP_CONFIG.MODE==='api')return request(`/admin/jobs/${jobId}/status`,{method:'PATCH',data:{status:'HIDDEN'}});
    const job=findMockJob(jobId),all=readJSON('portal_job_overrides',{});
    all[jobId]={...(all[jobId]||{}),status:'HIDDEN'};writeJSON('portal_job_overrides',all);
    return {...job,status:'HIDDEN'};
  },
  async employerDashboard(){
    if(APP_CONFIG.MODE==='api')return request('/employer/dashboard');
    const jobs=currentMockJobs().filter(j=>j.company_id===mockEmployerCompanyId);
    const apps=await this.listEmployerApplications();return {jobs,applications:apps,
      active_jobs:jobs.filter(j=>j.status==='ACTIVE').length,total_applications:apps.length,
      reviewing:apps.filter(a=>a.status==='REVIEWING').length};
  },
  async listEmployerJobs(){
    if(APP_CONFIG.MODE==='api')return normalizeList(await request('/employer/jobs'),['items','jobs']);
    return currentMockJobs().filter(j=>j.company_id===mockEmployerCompanyId);
  },
  async listEmployerApplications(jobId=''){
    if(APP_CONFIG.MODE==='api'){
      const suffix=jobId?`?job_id=${encodeURIComponent(jobId)}`:'';
      return normalizeList(await request(`/employer/applications${suffix}`),['items','applications']);
    }
    const jobs=new Set((await this.listEmployerJobs()).map(j=>String(j.job_id)));
    const raw=[...mockEmployerApplications(),...readJSON('applications',[])].filter(a=>jobs.has(String(a.job_id)));
    const allJobs=currentMockJobs();const users=mockUsers();
    return raw.filter(a=>!jobId||String(a.job_id)===String(jobId)).map(a=>{
      const job=allJobs.find(j=>j.job_id===Number(a.job_id));
      const user=users.find(u=>u.user_id===Number(a.candidate_id));
      const profile=Number(a.candidate_id)===1?{...DEFAULT_PROFILE,...readJSON('profile',{})}:MOCK_PROFILES[a.candidate_id]||{};
      return {...a,job_title:job?.title||a.job_title||'Tin tuyển dụng',company_name:job?.company_name||a.company_name||'Doanh nghiệp',
        candidate_name:profile.full_name||user?.full_name||getCandidateName(a.candidate_id),
        candidate_email:user?.email||'',candidate_major:profile.major||'',candidate_university:profile.university||'',
        candidate_skills:profile.skills||'',candidate_bio:profile.bio||'',candidate_cv_text:profile.cv_text||'',
        cv_filename:a.cv_filename||profile.cv_filename||''};
    }).sort((a,b)=>String(b.applied_at).localeCompare(String(a.applied_at)));
  },
  async changeApplicationStatus(applicationId,status){
    applicationId=requirePositiveId(applicationId);status=String(status).toUpperCase();
    if(!ALLOWED_APPLICATION_STATUSES.includes(status))throw new ApiError('Trạng thái đơn không hợp lệ.',400);
    if(APP_CONFIG.MODE==='api')return request(`/employer/applications/${applicationId}/status`,{method:'PATCH',data:{status}});
    const allowed=await this.listEmployerApplications();
    if(!allowed.some(a=>Number(a.application_id)===applicationId))throw new ApiError('Bạn không có quyền xử lý đơn này.',403);
    return upsertApps(applicationId,status);
  },
  async getCandidateForMatch(candidateId){
    candidateId=requirePositiveId(candidateId);
    if(APP_CONFIG.MODE==='api')return request(`/employer/candidates/${candidateId}`);
    if(candidateId===1)return {...DEFAULT_PROFILE,...readJSON('profile',{})};
    if(!MOCK_PROFILES[candidateId])throw new ApiError('Không tìm thấy hồ sơ demo.',404);
    return {...MOCK_PROFILES[candidateId]};
  },
  async analyzeCV({candidateId=null,cvText='',jobId}){
    jobId=requirePositiveId(jobId);
    if(APP_CONFIG.MODE==='api'){
      // Hợp đồng REST đề xuất. Backend gọi dịch vụ AI và bảo vệ API key.
      return request('/ai/match',{method:'POST',data:{candidate_id:candidateId?Number(candidateId):null,job_id:jobId,cv_text:String(cvText)}});
    }
    const job=findMockJob(jobId);
    if(job.status!=='ACTIVE'||job.approval_status!=='APPROVED'||job.deadline<today())throw new ApiError('Hãy chọn tin đã duyệt, đang mở và còn hạn.',400);
    let profile={skills:'',cv_text:''};if(candidateId)profile=await this.getCandidateForMatch(candidateId);
    const cv=[profile.skills,profile.cv_text,cvText].filter(Boolean).join(' ');
    if(cv.trim().length<8)throw new ApiError('Hồ sơ chưa có đủ thông tin kỹ năng để đối chiếu.',400);
    // MOCK: đối chiếu thuật ngữ kỹ năng, KHÔNG phải mô hình AI và không dùng để ra quyết định tuyển dụng.
    const known=['Python','FastAPI','MySQL','SQL','REST API','Git','Docker','HTML','CSS','JavaScript','React','Flutter','Dart','Testing','Postman','Excel','Power BI','Figma','ETL','Linux'];
    const n=x=>clean(x).replace(/[^a-z0-9 ]/g,' ');
    const sourceText=n([job.requirements,...(job.skills||[])].join(' '));
    const cvNorm=n(cv);
    const required=known.filter(skill=>sourceText.includes(n(skill)));
    const matched=required.filter(skill=>cvNorm.includes(n(skill)));
    const missing=required.filter(skill=>!cvNorm.includes(n(skill)));
    const score=required.length?Math.round(matched.length/required.length*100):0;
    const suggestion=missing.length?`Ưu tiên bổ sung ví dụ dự án và kỹ năng liên quan: ${missing.join(', ')}.`:'Hãy bổ sung kết quả dự án cụ thể để thể hiện rõ kinh nghiệm.';
    return {job_id:jobId,candidate_id:candidateId?Number(candidateId):null,ai_match_score:score,
      matched_skills:matched,missing_skills:missing,required_skills:required,
      ai_feedback:suggestion,engine:'demo_keyword',is_demo:true};
  }
};
