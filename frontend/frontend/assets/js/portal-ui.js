/** UniCareer portal UI helpers. Mọi dữ liệu từ API phải được escape trước khi gán innerHTML. */
export const $=(selector,scope=document)=>scope.querySelector(selector);
export const $$=(selector,scope=document)=>[...scope.querySelectorAll(selector)];
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function niceDate(value){if(!value)return '—';const d=new Date(value);return Number.isNaN(d.getTime())?'—':new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'}).format(d);}
export function niceDateTime(value){if(!value)return '—';const d=new Date(value);return Number.isNaN(d.getTime())?'—':new Intl.DateTimeFormat('vi-VN',{dateStyle:'short',timeStyle:'short'}).format(d);}
export const ROLE_NAMES={ADMIN:'Quản trị viên',EMPLOYER:'Nhà tuyển dụng',CANDIDATE:'Sinh viên'};
export const APPLICATION_STATES={RECEIVED:'Đã tiếp nhận',REVIEWING:'Đang xem xét',ACCEPTED:'Đã chấp nhận',REJECTED:'Đã từ chối'};
export const APPROVAL_STATES={PENDING:'Chờ duyệt',APPROVED:'Đã duyệt',REJECTED:'Từ chối'};
export const JOB_STATES={ACTIVE:'Đang mở',CLOSED:'Đã đóng',HIDDEN:'Đã ẩn'};
export function pill(value,labels={}){const v=String(value??'').toUpperCase();const kind={ACTIVE:'good',APPROVED:'good',ACCEPTED:'good',RECEIVED:'subtle',REVIEWING:'info',PENDING:'warn',REJECTED:'bad',HIDDEN:'bad',CLOSED:'subtle'}[v]||'subtle';return `<span class="portal-pill portal-pill--${kind}"><span class="portal-pill__dot"></span>${esc(labels[v]||v||'—')}</span>`;}
export function avatar(name,variant=''){const initials=String(name||'UC').split(/\s+/).filter(Boolean).slice(-2).map(v=>[...v][0]).join('').toUpperCase();return `<span aria-hidden="true" class="portal-avatar ${variant}">${esc(initials)}</span>`;}
let toastTimeout;
export function notify(message,isError=false){let item=$('#portal-toast');if(!item){item=document.createElement('div');item.id='portal-toast';item.setAttribute('role','status');item.setAttribute('aria-live','polite');item.className='portal-toast';document.body.append(item);}item.textContent=message;item.className='portal-toast is-visible'+(isError?' is-error':'');clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>item.classList.remove('is-visible'),4400);}
export function errorPanel(message){return `<div class="portal-empty" role="alert"><span class="portal-empty__icon">!</span><h3>Không thể tải dữ liệu</h3><p>${esc(message)}</p><button class="btn btn-outline" type="button" data-reload>Thử lại</button></div>`;}
export function emptyPanel(title,detail){return `<div class="portal-empty"><span class="portal-empty__icon">⌕</span><h3>${esc(title)}</h3><p>${esc(detail)}</p></div>`;}
export function updateCount(id,count){const e=document.getElementById(id);if(e)e.textContent=new Intl.NumberFormat('vi-VN').format(Number(count)||0);}
export function setBusy(button,busy,label='Đang xử lý...'){if(!button)return;if(busy){button.dataset.originalText=button.textContent;button.disabled=true;button.textContent=label;}else{button.disabled=false;if(button.dataset.originalText)button.textContent=button.dataset.originalText;}}
export function setupPortal(){const toggle=$('[data-portal-menu]'),sidebar=$('.portal-sidebar'),backdrop=$('.portal-backdrop');function setOpen(next){sidebar?.classList.toggle('is-open',next);backdrop?.classList.toggle('is-visible',next);toggle?.setAttribute('aria-expanded',String(next));}toggle?.addEventListener('click',()=>setOpen(!sidebar?.classList.contains('is-open')));backdrop?.addEventListener('click',()=>setOpen(false));$$('[data-reload]').forEach(btn=>btn.addEventListener('click',()=>window.location.reload()));}
export async function confirmDialog(title,description,confirmLabel='Xác nhận'){
  const dialog=$('#portal-confirm');if(!dialog||typeof dialog.showModal!=='function')return window.confirm(`${title}\n${description}`);
  $('#confirm-title',dialog).textContent=title;$('#confirm-description',dialog).textContent=description;const yes=$('#confirm-yes',dialog),no=$('#confirm-no',dialog);yes.textContent=confirmLabel;
  dialog.showModal();return new Promise(resolve=>{let settled=false;const finish=answer=>{if(settled)return;settled=true;yes.removeEventListener('click',onYes);no.removeEventListener('click',onNo);dialog.removeEventListener('cancel',onCancel);if(dialog.open)dialog.close();resolve(answer);};const onYes=()=>finish(true),onNo=()=>finish(false),onCancel=e=>{e.preventDefault();finish(false)};yes.addEventListener('click',onYes);no.addEventListener('click',onNo);dialog.addEventListener('cancel',onCancel);});
}
export function normalize(text){return String(text??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase().trim();}
