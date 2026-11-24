document.addEventListener("DOMContentLoaded", () => {
  const requestedRole = new URLSearchParams(location.search).get("role");
  if (requestedRole === "employer") {
    const employerRole = document.querySelector('#register-form [name="role"][value="employer"]');
    if (employerRole) employerRole.checked = true;
  }
  const login = document.getElementById("login-form");
  const register = document.getElementById("register-form");
  if (login) login.addEventListener("submit", submitLogin);
  if (register) register.addEventListener("submit", submitRegister);
});

function authFeedback(form) {
  return document.getElementById(form.id === "login-form" ? "login-status" : "register-status");
}

function destinationFor(role) {
  const next = new URLSearchParams(location.search).get("next");
  if (next) {
    const target = new URL(next, location.href);
    if (target.origin === location.origin && target.pathname.includes("/pages/")) {
      return target.href;
    }
  }
  if (role === "employer") return "../company/dashboard.html";
  if (role === "admin") return "../admin/dashboard.html";
  return "../candidate/index.html";
}

async function submitLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const feedback = authFeedback(form);
  button.disabled = true;
  feedback.textContent = "Đang đăng nhập...";
  try {
    const result = await UniCareerAPI.login(
      form.querySelector("#email").value.trim(),
      form.querySelector("#password").value,
    );
    feedback.textContent = "Đăng nhập thành công.";
    window.location.href = destinationFor(result.user.role);
  } catch (error) {
    feedback.textContent = error.message;
    feedback.style.color = "#b42318";
  } finally {
    button.disabled = false;
  }
}

async function submitRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const feedback = authFeedback(form);
  const password = form.querySelector("#password").value;
  const confirmation = form.querySelector("#confirm-password").value;
  if (password !== confirmation) {
    feedback.textContent = "Mật khẩu xác nhận không khớp.";
    feedback.style.color = "#b42318";
    return;
  }
  button.disabled = true;
  feedback.textContent = "Đang tạo tài khoản...";
  feedback.style.color = "";
  try {
    const role = form.querySelector('[name="role"]:checked').value;
    const fullName = form.querySelector("#name").value.trim();
    await UniCareerAPI.register(
      form.querySelector("#email").value.trim(),
      password,
      role,
      fullName,
    );
    const result = await UniCareerAPI.login(
      form.querySelector("#email").value.trim(),
      password,
    );
    feedback.textContent = "Tạo tài khoản thành công.";
    window.location.href = destinationFor(result.user.role);
  } catch (error) {
    feedback.textContent = error.message;
    feedback.style.color = "#b42318";
  } finally {
    button.disabled = false;
  }
}
