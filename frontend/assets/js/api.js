/**
 * UNICAREER API CLIENT - TÍCH HỢP TOÀN BỘ CÁC MODULE HỆ THỐNG
 * Hỗ trợ phân hệ: Tài khoản (Auth), Ứng viên (Candidate), Doanh nghiệp (Company),
 * Việc làm (Jobs), Ứng tuyển (Applications), Quản trị (Admin)
 * Chuẩn UniCareer - Nhóm 8 (Task T05FEB0)
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.UniCareerAPI = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {

  const BASE_URL = (typeof window !== "undefined" && window.location.protocol && window.location.protocol.startsWith("http"))
    ? `${window.location.origin}/api`
    : "http://localhost:8000/api";

  const STORAGE_KEY_USER = "unicareer_user";
  const STORAGE_KEY_TOKEN = "unicareer_token";

  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const token = getCurrentToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorDetail = (data && data.detail)
          ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
          : `Lỗi kết nối máy chủ (${response.status})`;
        const error = new Error(errorDetail);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.warn(`[UniCareerAPI] Error calling ${endpoint}:`, err.message);
      throw err;
    }
  }

  function getCurrentUser() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY_USER);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function getCurrentToken() {
    try {
      return localStorage.getItem(STORAGE_KEY_TOKEN) || null;
    } catch (e) {
      return null;
    }
  }

  function setCurrentSession(user, token) {
    if (user) localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
    if (token) localStorage.setItem(STORAGE_KEY_TOKEN, token);
  }

  function clearSession() {
    localStorage.removeItem(STORAGE_KEY_USER);
    localStorage.removeItem(STORAGE_KEY_TOKEN);
  }

  return {
    BASE_URL,
    getCurrentUser,
    getCurrentToken,
    setCurrentSession,
    clearSession,

    // 1. Phân hệ Xác thực & Tài khoản
    auth: {
      async register(data) {
        return await request("/auth/register", {
          method: "POST",
          body: JSON.stringify(data)
        });
      },
      async login(email, password) {
        const res = await request("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password })
        });
        if (res && res.user) {
          setCurrentSession(res.user, res.access_token);
        }
        return res;
      },
      logout() {
        clearSession();
      },
      async getMe(userId) {
        return await request(`/auth/me?user_id=${userId}`);
      }
    },

    // 2. Phân hệ Sinh viên / Ứng viên
    candidate: {
      async getProfile(userId) {
        return await request(`/candidates/profile?user_id=${userId}`);
      },
      async updateProfile(userId, data) {
        return await request(`/candidates/profile?user_id=${userId}`, {
          method: "PUT",
          body: JSON.stringify(data)
        });
      },
      async apply(jobId, candidateId, coverLetter = "") {
        return await request(`/candidates/apply?user_id=${candidateId}`, {
          method: "POST",
          body: JSON.stringify({
            job_id: jobId,
            candidate_id: candidateId,
            cover_letter: coverLetter
          })
        });
      },
      async getApplications(candidateId) {
        return await request(`/candidates/applications?user_id=${candidateId}`);
      }
    },

    // 3. Phân hệ Việc làm & Tìm kiếm
    jobs: {
      async list(params = {}) {
        const query = new URLSearchParams();
        if (params.search) query.append("search", params.search);
        if (params.status) query.append("status", params.status);
        if (params.job_type) query.append("job_type", params.job_type);
        if (params.location) query.append("location", params.location);
        const qStr = query.toString() ? `?${query.toString()}` : "";
        return await request(`/jobs${qStr}`);
      },
      async get(jobId) {
        return await request(`/jobs/${jobId}`);
      },
      async create(jobData) {
        return await request("/jobs", {
          method: "POST",
          body: JSON.stringify(jobData)
        });
      },
      async update(jobId, jobData) {
        return await request(`/jobs/${jobId}`, {
          method: "PUT",
          body: JSON.stringify(jobData)
        });
      },
      async updateStatus(jobId, status) {
        return await request(`/jobs/${jobId}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status })
        });
      }
    },

    // 4. Phân hệ Doanh nghiệp
    company: {
      async get(companyId) {
        return await request(`/companies/${companyId}`);
      },
      async update(companyId, data) {
        return await request(`/companies/${companyId}`, {
          method: "PUT",
          body: JSON.stringify(data)
        });
      },
      async getApplications(companyId) {
        return await request(`/companies/${companyId}/applications`);
      },
      async updateApplicationStatus(companyId, applicationId, status) {
        return await request(`/companies/${companyId}/applications/${applicationId}/status`, {
          method: "PUT",
          body: JSON.stringify({ status })
        });
      }
    },

    // 5. Phân hệ Quản trị (Admin)
    admin: {
      async getStats() {
        return await request("/admin/stats");
      },
      async getUsers() {
        return await request("/admin/users");
      },
      async toggleUserStatus(userId, isActive) {
        return await request(`/admin/users/${userId}/status`, {
          method: "PUT",
          body: JSON.stringify({ is_active: isActive })
        });
      },
      async getJobs(approvalStatus = null) {
        const q = approvalStatus ? `?approval_status=${approvalStatus}` : "";
        return await request(`/admin/jobs${q}`);
      },
      async setJobApproval(jobId, approvalStatus) {
        return await request(`/admin/jobs/${jobId}/approval`, {
          method: "PUT",
          body: JSON.stringify({ approval_status: approvalStatus })
        });
      }
    }
  };
});
