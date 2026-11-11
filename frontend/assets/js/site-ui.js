document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".crumbs").forEach((crumbs) => {
    if (!crumbs.hasAttribute("aria-label")) crumbs.setAttribute("aria-label", "Đường dẫn");
  });
  document.querySelectorAll(".nav-emoji").forEach((icon) => {
    icon.setAttribute("aria-hidden", "true");
  });
  initializeSiteNavigation();
  initializePortalNavigation();
  initializeCandidateSearch();
  initializePortalTableFilters();
  initializeApplicationDetails();
  initializeJobEditor();
  document.body.classList.add("ui-ready");
});

function initializeSiteNavigation() {
  document.querySelectorAll(".nav-wrap").forEach((header, index) => {
    const navigation = header.querySelector(".nav-main");
    if (!navigation) return;

    if (!navigation.id) navigation.id = `site-navigation-${index + 1}`;
    if (!navigation.hasAttribute("aria-label")) {
      navigation.setAttribute("aria-label", "Điều hướng chính");
    }

    let toggle = header.querySelector(".nav-menu-btn");
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.className = "nav-menu-btn";
      toggle.type = "button";
      toggle.textContent = "☰";
      toggle.setAttribute("aria-label", "Mở menu");
      header.insertBefore(toggle, navigation);
    }

    toggle.setAttribute("aria-controls", navigation.id);
    toggle.setAttribute("aria-expanded", "false");
    toggle.addEventListener("click", () => {
      const isOpen = navigation.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Đóng menu" : "Mở menu");
    });

    navigation.addEventListener("click", (event) => {
      if (!event.target.closest("a")) return;
      navigation.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Mở menu");
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!navigation.classList.contains("is-open")) return;
      navigation.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Mở menu");
      toggle.focus();
    });
  });
}

function initializePortalNavigation() {
  const layout = document.querySelector(".portal-layout");
  const sidebar = layout?.querySelector(".portal-sidebar");
  if (!layout || !sidebar) return;

  let toggle = layout.querySelector(".portal-menu-toggle");
  if (!toggle) {
    const topbarLeft = layout.querySelector(".portal-topbar-left");
    if (!topbarLeft) return;
    toggle = document.createElement("button");
    toggle.className = "portal-menu-toggle";
    toggle.type = "button";
    toggle.textContent = "☰";
    topbarLeft.prepend(toggle);
  }

  sidebar.id ||= "portal-sidebar";
  sidebar.inert = window.innerWidth <= 830;
  sidebar.setAttribute("aria-hidden", String(window.innerWidth <= 830));
  const portalNavigation = sidebar.querySelector(".portal-menu");
  if (portalNavigation && !portalNavigation.hasAttribute("aria-label")) {
    const role = layout.querySelector(".portal-subtitle")?.textContent.trim().toLocaleLowerCase("vi");
    portalNavigation.setAttribute("aria-label", role ? `Điều hướng ${role}` : "Điều hướng");
  }
  toggle.setAttribute("aria-controls", sidebar.id);
  toggle.setAttribute("aria-expanded", "false");
  toggle.setAttribute("aria-label", "Mở điều hướng");

  let backdrop = layout.querySelector(".portal-backdrop");
  if (!backdrop) {
    backdrop = document.createElement("button");
    backdrop.className = "portal-backdrop";
    backdrop.type = "button";
    backdrop.setAttribute("aria-label", "Đóng điều hướng");
    backdrop.setAttribute("aria-hidden", "true");
    backdrop.tabIndex = -1;
    layout.prepend(backdrop);
  }

  const closeMenu = () => {
    sidebar.classList.remove("is-open");
    const isCollapsed = window.innerWidth <= 830;
    sidebar.inert = isCollapsed;
    sidebar.setAttribute("aria-hidden", String(isCollapsed));
    backdrop.classList.remove("is-visible");
    backdrop.setAttribute("aria-hidden", "true");
    backdrop.tabIndex = -1;
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Mở điều hướng");
    document.body.classList.remove("portal-menu-open");
  };

  toggle.addEventListener("click", () => {
    const isOpen = sidebar.classList.toggle("is-open");
    sidebar.inert = !isOpen;
    sidebar.setAttribute("aria-hidden", String(!isOpen));
    backdrop.classList.toggle("is-visible", isOpen);
    backdrop.setAttribute("aria-hidden", String(!isOpen));
    backdrop.tabIndex = isOpen ? 0 : -1;
    toggle.setAttribute("aria-expanded", String(isOpen));
    toggle.setAttribute("aria-label", isOpen ? "Đóng điều hướng" : "Mở điều hướng");
    document.body.classList.toggle("portal-menu-open", isOpen);
  });

  backdrop.addEventListener("click", closeMenu);
  sidebar.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
      closeMenu();
      toggle.focus();
    }
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 830) closeMenu();
  });
}

function initializeCandidateSearch() {
  const searchForm = document.querySelector(".hero-search");
  const jobList = document.querySelector(".job-list");
  if (!searchForm || !jobList) return;

  const cards = Array.from(jobList.querySelectorAll(".job-card"));
  const queryInput = searchForm.querySelector('input[type="search"]');
  const heroLocation = searchForm.querySelector("select");
  const typeFilter = document.getElementById("job-type");
  const placeFilter = document.getElementById("job-place");
  const salaryFilter = document.getElementById("job-salary");
  const sortSelect = document.getElementById("job-sort");
  const counter = document.querySelector("[data-job-count]");
  const emptyMessage = jobList.querySelector(".jobs-empty");
  const filterToggle = document.querySelector(".mobile-filter-trigger");
  const filters = document.querySelector(".filters");

  const applyFilters = () => {
    const query = queryInput?.value.trim().toLocaleLowerCase("vi") ?? "";
    const locations = [heroLocation?.value, placeFilter?.value]
      .filter((value) => value && !value.startsWith("Tất cả"));
    const type = typeFilter?.value;
    const salary = salaryFilter?.value;

    const visibleCards = cards.filter((card) => {
      const text = card.textContent.toLocaleLowerCase("vi");
      const matchesQuery = !query || text.includes(query);
      const matchesLocations = locations.every((location) =>
        text.includes(location.toLocaleLowerCase("vi"))
      );
      const matchesType = !type || type.startsWith("Tất cả") ||
        text.includes(type.toLocaleLowerCase("vi"));
      const matchesSalary = !salary || salary.startsWith("Tất cả") ||
        (salary === "Dưới 5 triệu"
          ? text.includes("triệu/tháng")
          : text.includes(salary.toLocaleLowerCase("vi")));
      return matchesQuery && matchesLocations && matchesType && matchesSalary;
    });

    if (sortSelect?.selectedIndex === 1) {
      visibleCards.sort((first, second) => deadlineDate(first) - deadlineDate(second));
    }

    visibleCards.forEach((card) => jobList.append(card));
    cards.forEach((card) => {
      card.hidden = !visibleCards.includes(card);
    });

    if (counter) counter.textContent = `${visibleCards.length} cơ hội đang tuyển`;
    if (emptyMessage) emptyMessage.hidden = visibleCards.length > 0;
  };

  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    applyFilters();
    document.getElementById("job-list")?.scrollIntoView({ behavior: "smooth" });
  });

  const syncLocation = (source, target) => {
    if (!source || !target) return;
    const optionExists = Array.from(target.options).some((option) => option.value === source.value);
    target.value = optionExists ? source.value : target.options[0].value;
    applyFilters();
  };

  heroLocation?.addEventListener("change", () => syncLocation(heroLocation, placeFilter));
  placeFilter?.addEventListener("change", () => syncLocation(placeFilter, heroLocation));

  [queryInput, typeFilter, salaryFilter, sortSelect]
    .filter(Boolean)
    .forEach((control) => {
      control.addEventListener(control === queryInput ? "input" : "change", applyFilters);
    });

  filterToggle?.addEventListener("click", () => {
    const isOpen = filters.classList.toggle("is-open");
    filterToggle.setAttribute("aria-expanded", String(isOpen));
  });

  applyFilters();
}

function deadlineDate(card) {
  const match = card.querySelector(".deadline")?.textContent.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  return match ? new Date(`${match[3]}-${match[2]}-${match[1]}`) : new Date(8640000000000000);
}

function initializePortalTableFilters() {
  document.querySelectorAll(".portal-toolbar").forEach((toolbar) => {
    const panel = toolbar.closest(".portal-panel");
    const table = panel?.querySelector(".portal-table");
    const rows = table ? Array.from(table.querySelectorAll("tbody tr")) : [];
    const controls = Array.from(toolbar.querySelectorAll('input[type="search"], select'));
    if (!rows.length || !controls.length) return;

    let status = toolbar.nextElementSibling;
    if (!status?.classList.contains("portal-filter-status")) {
      status = document.createElement("p");
      status.className = "portal-filter-status";
      status.setAttribute("role", "status");
      status.setAttribute("aria-live", "polite");
      toolbar.insertAdjacentElement("afterend", status);
    }

    const applyFilters = () => {
      const activeFilters = controls
        .map((control) => ({
          value: control.matches("select")
            ? (control.selectedIndex === 0 ? "" : control.value)
            : control.value.trim(),
        }))
        .filter((filter) => filter.value)
        .map((filter) => filter.value.toLocaleLowerCase("vi"));
      let visibleCount = 0;

      rows.forEach((row) => {
        const rowText = row.textContent.toLocaleLowerCase("vi");
        const visible = activeFilters.every((filter) => rowText.includes(filter));
        row.hidden = !visible;
        if (visible) visibleCount += 1;
      });

      status.textContent = visibleCount
        ? `${visibleCount} kết quả trong dữ liệu mẫu.`
        : "Không tìm thấy kết quả phù hợp.";
    };

    controls.forEach((control) => {
      control.addEventListener(control.matches("select") ? "change" : "input", applyFilters);
    });
  });
}

function initializeApplicationDetails() {
  const title = document.getElementById("apply-job-title");
  if (!title) return;

  const jobs = {
    backend: {
      title: "Backend Developer Intern",
      company: "TechNova",
      location: "TP. Hồ Chí Minh",
      salary: "3–5 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail.html",
      logo: "T",
    },
    frontend: {
      title: "Frontend Developer Intern",
      company: "BluePeak Digital",
      location: "Hybrid",
      salary: "Lương thỏa thuận",
      type: "Thực tập",
      detail: "job-detail-frontend.html",
      logo: "B",
    },
    data: {
      title: "Data Analyst Intern",
      company: "NextStep Labs",
      location: "Hà Nội",
      salary: "3–5 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail-data.html",
      logo: "N",
    },
    business: {
      title: "Business Analyst Intern",
      company: "CloudBridge",
      location: "TP. Hồ Chí Minh",
      salary: "3–5 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail-business.html",
      logo: "C",
    },
  };

  const job = jobs[new URLSearchParams(window.location.search).get("job")] ?? jobs.backend;
  title.textContent = `Ứng tuyển ${job.title}`;
  document.title = `Ứng tuyển ${job.title} | UniCareer`;
  document.getElementById("apply-job-breadcrumb")?.setAttribute("href", job.detail);
  document.getElementById("apply-job-position").textContent = job.title;
  document.getElementById("apply-job-company").textContent = job.company;
  document.getElementById("apply-job-company-location").textContent =
    `${job.company} · ${job.location}`;
  document.getElementById("apply-job-meta").textContent = `${job.type} · ${job.salary}`;
  document.getElementById("apply-job-logo").textContent = job.logo;
  document.getElementById("apply-job-view-link")?.setAttribute("href", job.detail);
}

function initializeJobEditor() {
  const form = document.getElementById("edit-job-form");
  if (!form) return;

  const jobs = {
    backend: {
      title: "Backend Developer Intern",
      type: "Thực tập",
      location: "TP. Hồ Chí Minh",
      salary: "3–5 triệu/tháng",
      deadline: "2026-11-30",
      experience: "Không yêu cầu",
      description: "Tham gia phát triển backend và REST API cho sản phẩm của doanh nghiệp.",
      requirements: "Kiến thức Python cơ bản, quan tâm FastAPI và MySQL.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    frontend: {
      title: "Frontend Developer Intern",
      type: "Thực tập",
      location: "Hybrid",
      salary: "Lương thỏa thuận",
      deadline: "2026-12-15",
      experience: "Không yêu cầu",
      description: "Tham gia xây dựng giao diện web thân thiện và dễ sử dụng.",
      requirements: "Có kiến thức HTML, CSS, JavaScript cơ bản.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    data: {
      title: "Data Analyst Intern",
      type: "Thực tập",
      location: "Hà Nội",
      salary: "3–5 triệu/tháng",
      deadline: "2026-12-20",
      experience: "Không yêu cầu",
      description: "Hỗ trợ phân tích dữ liệu và trực quan hóa thông tin kinh doanh.",
      requirements: "Có kiến thức SQL, Excel cơ bản.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    business: {
      title: "Business Analyst Intern",
      type: "Thực tập",
      location: "TP. Hồ Chí Minh",
      salary: "3–5 triệu/tháng",
      deadline: "2026-12-22",
      experience: "Không yêu cầu",
      description: "Hỗ trợ thu thập yêu cầu và phối hợp với nhóm phát triển.",
      requirements: "Kỹ năng giao tiếp, tư duy phân tích và sử dụng Excel.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
  };

  const job = jobs[new URLSearchParams(window.location.search).get("job")] ?? jobs.backend;
  const values = {
    "job-title": job.title,
    "job-type": job.type,
    "job-location": job.location,
    "job-salary": job.salary,
    "job-deadline": job.deadline,
    "job-experience": job.experience,
    "job-description": job.description,
    "job-requirements": job.requirements,
  };

  Object.entries(values).forEach(([id, value]) => {
    const field = document.getElementById(id);
    if (field) field.value = value;
  });

  document.getElementById("edit-job-title").textContent = `Chỉnh sửa ${job.title}`;
  document.getElementById("edit-job-summary").textContent = `Cập nhật nội dung tin ${job.title}.`;
  const status = document.getElementById("edit-job-status");
  status.textContent = job.status;
  status.className = `status ${job.statusClass}`;
  document.title = `Chỉnh sửa ${job.title} | UniCareer`;
}
