document.addEventListener("DOMContentLoaded", initializeHomePage);

function initializeHomePage() {
  const form = document.getElementById("home-search");
  const list = document.getElementById("home-job-list");
  const status = document.getElementById("home-job-status");
  const keyword = document.getElementById("home-keyword");
  const locationSelect = document.getElementById("home-location");
  if (!form || !list || !status || !keyword || !locationSelect) return;

  let activeRequest;

  async function loadJobs(filters = {}) {
    activeRequest?.abort();
    const requestController = new AbortController();
    activeRequest = requestController;
    list.replaceChildren();
    status.classList.remove("is-error");
    status.textContent = "Đang tìm cơ hội phù hợp...";

    try {
      const result = await UniCareerAPI.jobs.listPublic({
        keyword: filters.keyword ?? keyword.value.trim(),
        location: filters.location ?? locationSelect.value,
        job_type: filters.jobType || "",
        sort: "latest",
        limit: 6,
        skip: 0,
      }, { signal: requestController.signal });
      if (activeRequest !== requestController) return;

      result.items.forEach((job) => list.append(createHomeJobCard(job)));
      status.textContent = result.total
        ? `Đang hiển thị ${result.items.length} trong ${result.total} cơ hội phù hợp.`
        : "Chưa tìm thấy cơ hội phù hợp. Thử từ khóa hoặc địa điểm khác nhé.";
    } catch (error) {
      if (error.name === "AbortError" || activeRequest !== requestController) return;
      status.textContent = `Không tải được việc làm: ${error.message}`;
      status.classList.add("is-error");
    } finally {
      if (activeRequest === requestController) activeRequest = null;
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadJobs();
  });

  document.querySelectorAll("[data-home-keyword], [data-home-type]").forEach((button) => {
    button.addEventListener("click", () => {
      keyword.value = button.dataset.homeKeyword || "";
      loadJobs({
        keyword: keyword.value,
        location: locationSelect.value,
        jobType: button.dataset.homeType || "",
      });
      document.getElementById("home-jobs")?.scrollIntoView({ behavior: "smooth" });
    });
  });

  loadJobs({ keyword: "", location: "" });
}

function createHomeJobCard(job) {
  const card = document.createElement("article");
  card.className = "home-job-card";

  const company = document.createElement("div");
  company.className = "home-job-company";
  const mark = document.createElement("span");
  mark.className = "home-job-company-mark";
  mark.textContent = (job.company_name || "U").trim().slice(0, 1).toLocaleUpperCase("vi");
  const companyName = document.createElement("span");
  companyName.textContent = job.company_name || "Doanh nghiệp";
  company.append(mark, companyName);

  const title = document.createElement("h3");
  const titleLink = document.createElement("a");
  titleLink.href = `pages/candidate/job-detail.html?id=${encodeURIComponent(job.job_id)}`;
  titleLink.textContent = job.title;
  title.append(titleLink);

  const typeNames = {
    FULL_TIME: "Toàn thời gian",
    PART_TIME: "Bán thời gian",
    INTERNSHIP: "Thực tập",
  };
  const meta = document.createElement("div");
  meta.className = "home-job-meta";
  const type = document.createElement("span");
  type.className = "home-job-type";
  type.textContent = typeNames[job.job_type] || "Việc làm";
  const location = document.createElement("span");
  location.textContent = `⌖ ${job.location || "Chưa cập nhật địa điểm"}`;
  const deadline = document.createElement("span");
  deadline.textContent = `Hạn ứng tuyển: ${formatHomeDate(job.deadline)}`;
  meta.append(type, location, deadline);

  const bottom = document.createElement("div");
  bottom.className = "home-job-bottom";
  const salary = document.createElement("span");
  salary.className = "home-job-salary";
  salary.textContent = job.salary_range || "Thỏa thuận";
  const detail = document.createElement("a");
  detail.className = "home-job-detail";
  detail.href = titleLink.href;
  detail.textContent = "Xem chi tiết →";
  bottom.append(salary, detail);

  card.append(company, title, meta, bottom);
  return card;
}

function formatHomeDate(value) {
  if (!value) return "Chưa xác định";
  const [year, month, day] = String(value).slice(0, 10).split("-");
  if (!year || !month || !day) return "Chưa xác định";
  return `${day}/${month}/${year}`;
}
