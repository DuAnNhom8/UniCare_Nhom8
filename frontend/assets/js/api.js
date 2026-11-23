/* API chung cho UniCareer. Chỉ lưu access token trong sessionStorage của tab. */
(function () {
  const local = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const separateFrontend = local && window.location.port && window.location.port !== "8000";
  const origin = separateFrontend ? "http://127.0.0.1:8000" : window.location.origin;
  const apiBase = (window.UNICAREER_API_BASE || `${origin}/api`).replace(/\/$/, "");
  const key = "unicareer_access_token";

  async function request(path, { method = "GET", body, signal, auth = false, raw = false } = {}) {
    const headers = { Accept: raw ? "application/pdf" : "application/json" };
    if (auth) {
      const token = sessionStorage.getItem(key);
      if (!token) throw Object.assign(new Error("Bạn cần đăng nhập để tiếp tục."), { status: 401 });
      headers.Authorization = `Bearer ${token}`;
    }
    if (body !== undefined && !(body instanceof FormData)) headers["Content-Type"] = "application/json";
    let response;
    try {
      response = await fetch(`${apiBase}${path}`, {
        method, headers, body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body), signal,
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new Error("Không kết nối được FastAPI. Hãy kiểm tra MySQL và máy chủ ở cổng 8000.");
    }
    if (!response.ok) {
      let message = `API trả lỗi HTTP ${response.status}.`;
      try {
        const payload = await response.json();
        if (typeof payload.detail === "string") message = payload.detail;
        else if (Array.isArray(payload.detail)) message = payload.detail.map((item) => item.msg).join("; ");
      } catch (_) { /* Giữ lỗi HTTP gốc. */ }
      throw Object.assign(new Error(message), { status: response.status });
    }
    return raw ? response.blob() : response.json();
  }

  window.UniCareerAPI = {
    hasSession() { return Boolean(sessionStorage.getItem(key)); },
    signOut() { sessionStorage.removeItem(key); },
    async login(email, password) {
      const response = await request("/auth/login", { method: "POST", body: { email, password } });
      sessionStorage.setItem(key, response.access_token);
      return response;
    },
    register(email, password, role) {
      return request("/auth/register", { method: "POST", body: { email, password, role } });
    },
    getProfile() { return request("/auth/me", { auth: true }); },
    listJobs(params, options = {}) {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== "" && value !== null && value !== undefined) query.set(key, String(value));
      });
      return request(`/jobs/public?${query}`, options);
    },
    getJob(id, options) { return request(`/jobs/public/${encodeURIComponent(id)}`, options); },
    listCVs() { return request("/candidate/cvs", { auth: true }); },
    uploadCV(file) {
      const body = new FormData(); body.append("file", file);
      return request("/candidate/cvs", { method: "POST", body, auth: true });
    },
    async downloadCV(id) {
      const blob = await request(`/candidate/cvs/${encodeURIComponent(id)}/download`, { raw: true, auth: true });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = "CV.pdf"; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    },
    checkApplication(jobId) { return request(`/candidate/applications/check/${encodeURIComponent(jobId)}`, { auth: true }); },
    submitApplication(data) { return request("/candidate/applications", { method: "POST", body: data, auth: true }); },
    listApplications(params = {}) {
      return request(`/candidate/applications?${new URLSearchParams(params)}`, { auth: true });
    },
  };
})();
