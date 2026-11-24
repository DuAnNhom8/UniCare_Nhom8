(function () {
  const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const separateFrontend = isLocalhost && window.location.port && window.location.port !== "8000";
  const origin = separateFrontend ? "http://127.0.0.1:8000" : window.location.origin;
  const baseUrl = (window.UNICAREER_API_BASE || `${origin}/api`).replace(/\/$/, "");
  const tokenKey = "unicareer_access_token";

  async function request(path, options) {
    const config = options || {};
    const headers = { Accept: config.raw ? "*/*" : "application/json" };
    const token = localStorage.getItem(tokenKey) || localStorage.getItem("access_token");
    if (config.auth) {
      if (!token) throw Object.assign(new Error("Bạn cần đăng nhập để tiếp tục."), { status: 401 });
      headers.Authorization = `Bearer ${token}`;
    }
    if (config.body !== undefined && !(config.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    let response;
    try {
      response = await fetch(`${baseUrl}${path}`, {
        method: config.method || "GET",
        headers,
        body: config.body instanceof FormData
          ? config.body
          : config.body === undefined ? undefined : JSON.stringify(config.body),
        signal: config.signal,
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new Error("Không kết nối được máy chủ UniCareer. Hãy kiểm tra API và cấu hình MySQL.");
    }
    if (!response.ok) {
      let message = `Máy chủ trả lỗi HTTP ${response.status}.`;
      try {
        const payload = await response.json();
        if (typeof payload.detail === "string") message = payload.detail;
        else if (Array.isArray(payload.detail)) message = payload.detail.map((item) => item.msg).join("; ");
      } catch (_) {
        // Keep the HTTP status when the server does not return JSON.
      }
      throw Object.assign(new Error(message), { status: response.status });
    }
    if (response.status === 204) return null;
    return config.raw ? response.blob() : response.json();
  }

  function authHeaders() {
    return { auth: true };
  }

  async function download(path, filename) {
    const blob = await request(path, { ...authHeaders(), raw: true });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename || "download";
    link.click();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
  }

  window.UniCareerAPI = {
    request,
    hasSession() {
      return Boolean(localStorage.getItem(tokenKey) || localStorage.getItem("access_token"));
    },
    signOut() {
      ["access_token", "unicareer_access_token", "unicareer_user", "unicareer_full_name"].forEach((key) => {
        localStorage.removeItem(key);
      });
    },
    async login(email, password) {
      const result = await request("/auth/login", { method: "POST", body: { email, password } });
      const fullName = result.user.full_name?.trim() || "";
      result.user.full_name = fullName || null;
      localStorage.setItem(tokenKey, result.access_token);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("unicareer_user", JSON.stringify(result.user));
      if (fullName) localStorage.setItem("unicareer_full_name", fullName);
      else localStorage.removeItem("unicareer_full_name");
      return result;
    },
    register(email, password, role, fullName) {
      return request("/auth/register", {
        method: "POST",
        body: { email, password, role, full_name: fullName || "" },
      });
    },
    getMe() {
      return request("/auth/me", authHeaders());
    },
    logout() {
      return request("/auth/logout", { ...authHeaders(), method: "POST" });
    },
    jobs: {
      listPublic(params, options) {
        const query = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
          if (value !== "" && value !== null && value !== undefined) query.set(key, String(value));
        });
        return request(`/jobs/public?${query}`, options);
      },
      getPublic(id) {
        return request(`/jobs/public/${encodeURIComponent(id)}`);
      },
      list(params) {
        const query = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
          if (value !== "" && value !== null && value !== undefined) query.set(key, String(value));
        });
        return request(`/jobs?${query}`, authHeaders());
      },
      get(id) {
        return request(`/jobs/${encodeURIComponent(id)}`, authHeaders());
      },
      create(data) {
        return request("/jobs", { ...authHeaders(), method: "POST", body: data });
      },
      update(id, data) {
        return request(`/jobs/${encodeURIComponent(id)}`, { ...authHeaders(), method: "PUT", body: data });
      },
      setStatus(id, value) {
        return request(`/jobs/${encodeURIComponent(id)}/status`, {
          ...authHeaders(), method: "PATCH", body: { status: value },
        });
      },
      remove(id) {
        return request(`/jobs/${encodeURIComponent(id)}`, { ...authHeaders(), method: "DELETE" });
      },
    },
    candidate: {
      getProfile() {
        return request("/users/me/profile", authHeaders());
      },
      updateProfile(data) {
        return request("/users/me/profile", { ...authHeaders(), method: "PUT", body: data });
      },
      changePassword(currentPassword, newPassword) {
        return request("/users/me/password", {
          ...authHeaders(),
          method: "PUT",
          body: { current_password: currentPassword, new_password: newPassword },
        });
      },
      listCVs() {
        return request("/candidate/cvs", authHeaders());
      },
      uploadCV(file) {
        const body = new FormData();
        body.append("file", file);
        return request("/candidate/cvs/upload", {
          ...authHeaders(), method: "POST", body,
        });
      },
      createCV(data) {
        return request("/candidate/cvs/builder", { ...authHeaders(), method: "POST", body: data });
      },
      updateCV(id, data) {
        return request(`/candidate/cvs/${encodeURIComponent(id)}`, {
          ...authHeaders(), method: "PUT", body: data,
        });
      },
      deleteCV(id) {
        return request(`/candidate/cvs/${encodeURIComponent(id)}`, { ...authHeaders(), method: "DELETE" });
      },
      setCVAIConsent(id, allowAIAnalysis) {
        return request(`/candidate/cvs/${encodeURIComponent(id)}/ai-consent`, {
          ...authHeaders(), method: "PUT", body: { allow_ai_analysis: allowAIAnalysis },
        });
      },
      downloadCV(id, title) {
        return download(`/candidate/cvs/${encodeURIComponent(id)}/download`, title);
      },
      checkApplication(jobId) {
        return request(`/candidate/applications/check/${encodeURIComponent(jobId)}`, authHeaders());
      },
      apply(data) {
        return request("/candidate/applications", { ...authHeaders(), method: "POST", body: data });
      },
      listApplications(params) {
        const query = new URLSearchParams(params || {});
        return request(`/candidate/applications?${query}`, authHeaders());
      },
    },
    company: {
      getProfile() {
        return request("/companies/profile/current", authHeaders());
      },
      saveProfile(data) {
        return request("/companies/profile/current", { ...authHeaders(), method: "PUT", body: data });
      },
      listApplications(companyId) {
        return request(`/companies/${encodeURIComponent(companyId)}/applications`, authHeaders());
      },
      updateApplication(companyId, applicationId, value) {
        return request(`/companies/${encodeURIComponent(companyId)}/applications/${encodeURIComponent(applicationId)}/status`, {
          ...authHeaders(), method: "PUT", body: { status: value },
        });
      },
      downloadCV(id, title) {
        return download(`/candidate/cvs/${encodeURIComponent(id)}/download`, title);
      },
      previewCV(id) {
        return request(`/candidate/cvs/${encodeURIComponent(id)}/download`, {
          ...authHeaders(),
          raw: true,
        });
      },
    },
    admin: {
      getStats() {
        return request("/admin/stats", authHeaders());
      },
      getUsers() {
        return request("/admin/users", authHeaders());
      },
      setUserStatus(userId, isActive) {
        return request(`/admin/users/${encodeURIComponent(userId)}/status`, {
          ...authHeaders(), method: "PUT", body: { is_active: isActive },
        });
      },
      getJobs(approvalStatus) {
        const query = approvalStatus ? `?approval_status=${encodeURIComponent(approvalStatus)}` : "";
        return request(`/admin/jobs${query}`, authHeaders());
      },
      setJobApproval(jobId, approvalStatus) {
        return request(`/admin/jobs/${encodeURIComponent(jobId)}/approval`, {
          ...authHeaders(), method: "PUT", body: { approval_status: approvalStatus },
        });
      },
    },
    ai: {
      analyzeCandidateCV(data) {
        return request("/ai/analyze/candidate", { ...authHeaders(), method: "POST", body: data });
      },
      analyzeApplication(data) {
        return request("/ai/analyze/application", { ...authHeaders(), method: "POST", body: data });
      },
    },
  };
})();