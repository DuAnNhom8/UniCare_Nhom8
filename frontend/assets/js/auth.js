/**
 * JAVASCRIPT XÁC THỰC NGƯỜI DÙNG & ĐIỀU HƯỚNG PHÂN QUYỀN (Auth JS)
 * Chuẩn UniCareer - Nhóm 8 (Task T05FEB0)
 */

document.addEventListener("DOMContentLoaded", () => {
  initLoginForm();
  initRegisterForm();
});

function showAuthAlert(message, type = "error", parentSelector = "form") {
  let existingAlert = document.querySelector(".auth-runtime-alert");
  if (existingAlert) existingAlert.remove();

  const alertBox = document.createElement("div");
  alertBox.className = `auth-runtime-alert portal-pill ${type === "success" ? "portal-pill--success" : "portal-pill--danger"}`;
  alertBox.style.display = "block";
  alertBox.style.marginBottom = "14px";
  alertBox.style.padding = "10px 14px";
  alertBox.style.fontSize = "14px";
  alertBox.style.borderRadius = "8px";
  alertBox.style.backgroundColor = type === "success" ? "#ecfdf5" : "#fef2f2";
  alertBox.style.color = type === "success" ? "#065f46" : "#991b1b";
  alertBox.style.border = `1px solid ${type === "success" ? "#a7f3d0" : "#fecaca"}`;
  alertBox.textContent = message;

  const parent = document.querySelector(parentSelector);
  if (parent) {
    parent.parentNode.insertBefore(alertBox, parent);
  }
}

function initLoginForm() {
  const loginSection = document.querySelector(".auth-card--login");
  if (!loginSection) return;

  const form = loginSection.querySelector("form");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const submitBtn = loginSection.querySelector("button");

  if (submitBtn) {
    submitBtn.removeAttribute("disabled");
    submitBtn.type = "submit";
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = emailInput ? emailInput.value.trim() : "";
      const password = passwordInput ? passwordInput.value : "";

      if (!email || !password) {
        showAuthAlert("Vui lòng điền đầy đủ Email và Mật khẩu.", "error");
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Đang xác thực...";
      }

      try {
        const res = await UniCareerAPI.auth.login(email, password);
        showAuthAlert("Đăng nhập thành công! Đang chuyển hướng...", "success");

        // Điều hướng theo phân quyền
        setTimeout(() => {
          const role = res.user.role;
          if (role === "EMPLOYER") {
            window.location.href = "../company/dashboard.html";
          } else if (role === "ADMIN") {
            window.location.href = "../admin/dashboard.html";
          } else {
            window.location.href = "../candidate/index.html";
          }
        }, 800);
      } catch (err) {
        showAuthAlert(err.message || "Đăng nhập thất bại. Vui lòng kiểm tra lại.", "error");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Đăng nhập";
        }
      }
    });
  }
}

function initRegisterForm() {
  const registerSection = document.querySelector(".auth-card--register");
  if (!registerSection) return;

  const form = registerSection.querySelector("form");
  const nameInput = document.getElementById("name");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("confirm-password");
  const submitBtn = registerSection.querySelector(".register-actions button");
  const helpNote = registerSection.querySelector(".register-actions .portal-help");

  if (submitBtn) {
    submitBtn.removeAttribute("disabled");
    submitBtn.type = "submit";
  }
  if (helpNote) {
    helpNote.textContent = "Hệ thống xác thực đã kết nối và sẵn sàng hoạt động.";
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const roleElem = form.querySelector("input[name='role']:checked");
      const role = roleElem ? roleElem.value.toUpperCase() : "CANDIDATE";
      const name = nameInput ? nameInput.value.trim() : "";
      const email = emailInput ? emailInput.value.trim() : "";
      const password = passwordInput ? passwordInput.value : "";
      const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : "";

      if (!email || !password || !name) {
        showAuthAlert("Vui lòng điền đầy đủ các thông tin bắt buộc.", "error");
        return;
      }

      if (password !== confirmPassword) {
        showAuthAlert("Mật khẩu xác nhận không khớp.", "error");
        return;
      }

      if (password.length < 6) {
        showAuthAlert("Mật khẩu phải có độ dài ít nhất 6 ký tự.", "error");
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Đang tạo tài khoản...";
      }

      try {
        const payload = {
          email,
          password,
          role,
          full_name: role === "CANDIDATE" ? name : null,
          company_name: role === "EMPLOYER" ? name : null
        };

        await UniCareerAPI.auth.register(payload);
        showAuthAlert("Đăng ký tài khoản thành công! Đang chuyển đến màn hình Đăng nhập...", "success");

        setTimeout(() => {
          window.location.href = "login.html";
        }, 1200);
      } catch (err) {
        showAuthAlert(err.message || "Đăng ký thất bại. Vui lòng kiểm tra lại.", "error");
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Tạo tài khoản";
        }
      }
    });
  }
}
