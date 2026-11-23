/* Xử lý form đăng ký/đăng nhập. Không sử dụng candidate_id từ client. */
document.addEventListener('DOMContentLoaded', () => {
  const login = document.getElementById('login-form');
  const register = document.getElementById('register-form');
  if (login) login.addEventListener('submit', submitLogin);
  if (register) register.addEventListener('submit', submitRegister);
});

function safeNextPage() {
  const urlParam = new URLSearchParams(location.search).get('next');
  if (!urlParam) return null;
  try {
    const dest = new URL(urlParam, location.origin);
    if (dest.origin === location.origin && dest.pathname.startsWith('/frontend/pages/candidate/')) return dest.href;
  } catch (_) { /* Bad redirect ignored. */ }
  return null;
}

async function submitLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const feedback = document.getElementById('auth-feedback');
  button.disabled = true;
  feedback.textContent = 'Đang xác thực...';
  try {
    await UniCareerAPI.login(form.querySelector("#email").value, form.querySelector("#password").value);
    const me = await UniCareerAPI.getProfile();
    feedback.textContent = 'Đăng nhập thành công!';
    location.href = safeNextPage() || (me.role === 'CANDIDATE' ? '../candidate/index.html' : '../company/dashboard.html');
  } catch (error) {
    feedback.textContent = error.message;
    button.disabled = false;
  }
}

async function submitRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const feedback = document.getElementById('auth-feedback');
  const button = form.querySelector('button[type="submit"]');
  const password = document.getElementById('password').value;
  const confirmation = document.getElementById('confirm-password').value;
  if (password !== confirmation) {
    feedback.textContent = 'Xác nhận mật khẩu không khớp.';
    return;
  }
  button.disabled = true;
  feedback.textContent = 'Đang tạo tài khoản...';
  try {
    await UniCareerAPI.register(document.getElementById('email').value, password, form.querySelector('[name="role"]:checked').value.toUpperCase());
    await UniCareerAPI.login(document.getElementById('email').value, password);
    feedback.textContent = 'Đã tạo tài khoản!';
    location.href = form.querySelector('[name="role"]:checked').value === 'candidate'
      ? '../candidate/index.html' : '../company/dashboard.html';
  } catch (error) {
    feedback.textContent = error.message;
    button.disabled = false;
  }
}
