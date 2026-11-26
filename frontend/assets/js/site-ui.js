document.addEventListener("DOMContentLoaded", () => {
  initializeCandidatePortal();
  initializeCompanyAccessGuard();
  document.querySelectorAll(".crumbs").forEach((crumbs) => {
    if (!crumbs.hasAttribute("aria-label")) crumbs.setAttribute("aria-label", "Đường dẫn");
  });
  document.querySelectorAll(".nav-emoji").forEach((icon) => {
    icon.setAttribute("aria-hidden", "true");
  });
  initializeSiteNavigation();
  initializePortalNavigation();
  initializePortalSPA();
  initializeCandidateSearch();
  initializePortalTableFilters();
  initializeApplicationDetails();
  initializeJobEditor();
  initializeAuthenticationNavigation();
  document.body.classList.add("ui-ready");
});

document.addEventListener("unicareer:page-loaded", () => {
  initializeCandidatePortal();
  document.querySelectorAll(".crumbs").forEach((crumbs) => {
    if (!crumbs.hasAttribute("aria-label")) crumbs.setAttribute("aria-label", "Đường dẫn");
  });
  initializeCandidateSearch();
  initializePortalTableFilters();
  initializeApplicationDetails();
  initializeJobEditor();
});

function renderPortalPagination(container, page, total, pageSize, onPageChange) {
  if (!container) return;
  const pageCount = Math.ceil(total / pageSize);
  container.replaceChildren();
  container.hidden = pageCount <= 1;
  if (pageCount <= 1) return;

  const addButton = (label, targetPage, options = {}) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `portal-page-button${options.active ? " is-active" : ""}`;
    button.textContent = label;
    button.disabled = Boolean(options.disabled);
    if (options.active) button.setAttribute("aria-current", "page");
    if (options.label) button.setAttribute("aria-label", options.label);
    button.addEventListener("click", () => onPageChange(targetPage));
    container.append(button);
  };

  addButton("‹ Trước", page - 1, { disabled: page <= 1, label: "Trang trước" });
  const pages = Array.from(new Set([
    1,
    page - 1,
    page,
    page + 1,
    pageCount,
  ])).filter((value) => value >= 1 && value <= pageCount).sort((a, b) => a - b);
  let previousPage = 0;
  pages.forEach((value) => {
    if (previousPage && value - previousPage > 1) {
      const ellipsis = document.createElement("span");
      ellipsis.className = "portal-page-ellipsis";
      ellipsis.textContent = "…";
      ellipsis.setAttribute("aria-hidden", "true");
      container.append(ellipsis);
    }
    addButton(String(value), value, {
      active: value === page,
      label: `Trang ${value}`,
    });
    previousPage = value;
  });
  addButton("Sau ›", page + 1, {
    disabled: page >= pageCount,
    label: "Trang tiếp theo",
  });
  const summary = document.createElement("span");
  summary.className = "portal-pagination-summary";
  summary.textContent = `Trang ${page}/${pageCount} · ${total} mục`;
  container.append(summary);
}
window.renderPortalPagination = renderPortalPagination;

function initializeCandidatePortal() {
  if (!window.location.pathname.includes("/pages/candidate/")) return;
  const existingLayout = document.querySelector(".portal-layout");
  if (existingLayout) {
    syncCandidatePortal(existingLayout);
    return;
  }
  const page = document.querySelector("body > main");
  if (!page) return;

  const pageName = window.location.pathname.split("/").pop();
  const activePage = pageName === "my-applications.html" ? "applications"
    : pageName === "cv-manage.html" ? "cv"
      : pageName === "profile.html" ? "profile" : "jobs";
  const layout = document.createElement("div");
  layout.className = "portal-layout";
  layout.innerHTML = `
    <aside class="portal-sidebar">
      <a class="portal-brand" href="../../index.html"><span class="brand-mark">U</span><span>UniCareer</span></a>
      <div class="portal-subtitle">SINH VIÊN</div>
      <nav class="portal-menu" aria-label="Điều hướng sinh viên">
        <a href="index.html" data-candidate-page="jobs"><span class="nav-emoji">⌕</span><span>Tìm việc làm</span></a>
        <a href="my-applications.html" data-candidate-page="applications"><span class="nav-emoji">▤</span><span>Đơn ứng tuyển</span></a>
        <a href="cv-manage.html" data-candidate-page="cv"><span class="nav-emoji">▥</span><span>Hồ sơ / CV</span></a>
        <a href="profile.html" data-candidate-page="profile"><span class="nav-emoji">♙</span><span>Hồ sơ cá nhân</span></a>
        <a href="ai-matching.html" data-candidate-page="ai"><span class="nav-emoji">✧</span><span>Phân tích CV</span></a>
        <div class="portal-menu-spacer"></div>
        <a href="../../index.html"><span class="nav-emoji">↗</span><span>Về trang chủ</span></a>
      </nav>
      <div class="portal-sidebottom"><span class="portal-avatar">U</span><div><strong>Ứng viên</strong><small>Sinh viên</small></div></div>
    </aside>
    <div class="portal-main">
      <header class="portal-topbar">
        <div class="portal-topbar-left"><a class="brand" href="../../index.html"><span class="brand-mark">U</span>UniCareer</a><span>Candidate Workspace</span></div>
        <div class="portal-topbar-right"><span class="portal-demo">KHÔNG GIAN ỨNG VIÊN</span><a class="portal-topbar__link" href="index.html">Khám phá việc làm ↗</a></div>
      </header>
    </div>`;

  layout.querySelector(`[data-candidate-page="${activePage}"]`)?.setAttribute("aria-current", "page");
  const portalMain = layout.querySelector(".portal-main");
  page.classList.add("candidate-workspace-content");
  portalMain.append(page);

  const oldHeader = document.querySelector("body > header.site-header");
  const oldFooter = document.querySelector("body > footer.site-footer");
  oldHeader?.remove();
  oldFooter?.remove();
  document.body.replaceChildren(layout);
  document.body.classList.add("candidate-workspace");

  syncCandidatePortal(layout);
}

function initializePortalSPA() {
  const portalPath = getPortalPath(window.location.pathname);
  if (!portalPath) return;
  const navigation = document.querySelector(".portal-menu");
  if (!navigation || navigation.dataset.spaInitialized) return;
  navigation.dataset.spaInitialized = "true";

  navigation.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || link.closest(".portal-menu") !== navigation) return;
    const target = new URL(link.href, window.location.href);
    if (target.origin !== window.location.origin || !canNavigatePortal(target.pathname)) return;
    event.preventDefault();
    if (target.href === window.location.href) return;
    void navigatePortalPage(target, true);
  });

  window.addEventListener("popstate", () => {
    if (canNavigatePortal(window.location.pathname)) {
      void navigatePortalPage(new URL(window.location.href), false);
    }
  });
}

function canNavigatePortal(pathname) {
  const currentPath = window.location.pathname;
  const currentPortal = getPortalPath(currentPath);
  const targetPortal = getPortalPath(pathname);
  if (!targetPortal) return false;
  if (targetPortal === currentPortal) return true;

  let user;
  try {
    user = JSON.parse(localStorage.getItem("unicareer_user") || "null");
  } catch (_) {
    localStorage.removeItem("unicareer_user");
  }
  const isAdminWorkspacePage = (path) =>
    /\/pages\/admin\//.test(path) || /\/pages\/candidate\/index\.html$/.test(path);
  return user?.role === "admin"
    && isAdminWorkspacePage(currentPath)
    && isAdminWorkspacePage(pathname);
}

function getPortalPath(pathname) {
  return pathname.match(/^(.*\/pages\/(?:candidate|company|admin)\/)/)?.[0] || "";
}

let portalNavigationRequest = 0;

async function navigatePortalPage(target, addHistoryEntry) {
  const requestId = ++portalNavigationRequest;
  try {
    const response = await fetch(target.href, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (!response.ok) throw new Error(`Không thể tải trang (${response.status}).`);

    const html = await response.text();
    const nextDocument = new DOMParser().parseFromString(html, "text/html");
    const nextContent = nextDocument.querySelector(".portal-content")
      || nextDocument.querySelector("main.page")
      || nextDocument.querySelector("body > main");
    if (!nextContent) throw new Error("Trang đích không có nội dung để hiển thị.");

    await loadPortalStyles(nextDocument, target);
    await loadPortalScripts(nextDocument, target);
    if (requestId !== portalNavigationRequest) return;

    const portalMain = document.querySelector(".portal-main");
    if (!portalMain) throw new Error("Không tìm thấy vùng nội dung ứng viên.");
    Array.from(portalMain.children)
      .filter((child) => !child.matches(".portal-topbar"))
      .forEach((child) => child.remove());
    const importedContent = document.importNode(nextContent, true);
    if (importedContent.matches("main.page")) {
      importedContent.classList.add("candidate-workspace-content");
    }
    portalMain.append(importedContent);

    document.title = nextDocument.title || "UniCareer";
    updatePortalTopbar(nextDocument, target);
    updatePortalActivePage(target);
    if (addHistoryEntry) history.pushState({}, "", target.href);
    document.dispatchEvent(new CustomEvent("unicareer:page-loaded"));
    window.scrollTo(0, 0);
  } catch (error) {
    if (requestId !== portalNavigationRequest) return;
    const content = document.querySelector(".portal-main");
    if (!content) throw error;
    let status = content.querySelector(".candidate-navigation-error");
    if (!status) {
      status = document.createElement("p");
      status.className = "candidate-navigation-error portal-help is-error";
      status.setAttribute("role", "alert");
      content.append(status);
    }
    status.textContent = `Không thể chuyển trang: ${error.message}`;
  }
}

function updatePortalTopbar(nextDocument, target) {
  const currentActions = document.querySelector(".portal-topbar-right");
  if (!currentActions) return;

  const nextActions = nextDocument.querySelector(".portal-topbar-right");
  if (nextActions) {
    currentActions.replaceChildren(...Array.from(nextActions.childNodes, (node) =>
      document.importNode(node, true)));
    return;
  }

  if (getPortalPath(target.pathname).includes("/candidate/")) {
    currentActions.innerHTML = '<span class="portal-demo">KHÔNG GIAN ỨNG VIÊN</span><a class="portal-topbar__link" href="index.html">Khám phá việc làm ↗</a>';
  }
}

async function loadPortalStyles(nextDocument, target) {
  const stylesheets = Array.from(nextDocument.querySelectorAll('link[rel="stylesheet"][href]'));
  await Promise.all(stylesheets.map((source) => {
    const href = new URL(source.getAttribute("href"), target).href;
    const exists = Array.from(document.querySelectorAll('link[rel="stylesheet"][href]'))
      .some((loaded) => new URL(loaded.href).href === href);
    if (exists) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.onload = resolve;
      link.onerror = () => reject(new Error(`Không tải được kiểu giao diện: ${href}`));
      document.head.append(link);
    });
  }));
}

async function loadPortalScripts(nextDocument, target) {
  const scripts = Array.from(nextDocument.querySelectorAll('script[src]'))
    .map((script) => new URL(script.getAttribute("src"), target))
    .filter((script) =>
      /\/(?:ai-matching|candidate|company|admin)\.js$/.test(script.pathname));

  await Promise.all(scripts.map((source) => {
    const exists = Array.from(document.querySelectorAll("script[src]"))
      .some((loaded) => new URL(loaded.src).pathname === source.pathname);
    if (exists) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = source.href;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Không tải được chức năng trang: ${source.pathname}`));
      document.head.append(script);
    });
  }));
}

function updatePortalActivePage(target) {
  document.querySelectorAll(".portal-menu a[href]").forEach((link) => {
    const linkPath = new URL(link.href, target).pathname;
    if (linkPath === target.pathname) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

function syncCandidatePortal(layout) {
  document.body.classList.add("candidate-workspace");
  let user;
  try {
    user = JSON.parse(localStorage.getItem("unicareer_user") || "null");
  } catch (_) {
    localStorage.removeItem("unicareer_user");
  }
  const savedName = user?.full_name?.trim()
    || localStorage.getItem("unicareer_full_name")
    || user?.name?.trim();
  const displayName = savedName || "Ứng viên";
  const roleLabels = {
    candidate: { role: "Sinh viên", subtitle: "SINH VIÊN", workspace: "Candidate Workspace" },
    employer: { role: "Nhà tuyển dụng", subtitle: "NHÀ TUYỂN DỤNG", workspace: "Employer Workspace" },
    admin: { role: "Quản trị viên", subtitle: "QUẢN TRỊ HỆ THỐNG", workspace: "Admin Workspace" },
  };
  const identity = roleLabels[user?.role] || roleLabels.candidate;
  document.body.dataset.portalRole = user?.role || "candidate";
  if (savedName) updateCandidateIdentity(savedName);
  layout.querySelector(".portal-sidebottom strong").textContent = displayName;
  layout.querySelector(".portal-sidebottom small").textContent = identity.role;
  layout.querySelector(".portal-subtitle").textContent = identity.subtitle;
  layout.querySelector(".portal-topbar-left > span").textContent = identity.workspace;
  layout.querySelector(".portal-menu").setAttribute(
    "aria-label",
    `Điều hướng ${identity.role.toLocaleLowerCase("vi")}`,
  );
  const roleBadge = layout.querySelector(".portal-demo");
  if (roleBadge) roleBadge.textContent = user?.role === "admin" ? "ADMIN" : identity.subtitle;

  if (user?.role === "admin") {
    const navigation = layout.querySelector(".portal-menu");
    navigation.setAttribute("aria-label", "Điều hướng quản trị viên");
    navigation.innerHTML = `
      <a href="../admin/dashboard.html"><span class="nav-emoji">◫</span><span>Tổng quan</span></a>
      <a href="../admin/users.html"><span class="nav-emoji">♙</span><span>Quản lý người dùng</span></a>
      <a href="../admin/approve-jobs.html"><span class="nav-emoji">▣</span><span>Kiểm duyệt tin</span></a>
      <a href="../candidate/index.html" aria-current="page"><span class="nav-emoji">⌕</span><span>Tin tuyển dụng</span></a>
      <div class="portal-menu-spacer"></div>
      <a href="../../index.html"><span class="nav-emoji">↗</span><span>Về trang chủ</span></a>`;

    const topbarLink = layout.querySelector(".portal-topbar__link");
    if (topbarLink) {
      topbarLink.href = "../admin/dashboard.html";
      topbarLink.textContent = "Bảng điều khiển ↗";
    }

    const hero = document.querySelector(".hero");
    if (hero) {
      const eyebrow = hero.querySelector(".eyebrow");
      const heading = hero.querySelector("h1");
      const description = hero.querySelector("p");
      const searchButton = hero.querySelector(".hero-search button");
      if (eyebrow) eyebrow.textContent = "QUẢN TRỊ HỆ THỐNG · TIN TUYỂN DỤNG";
      if (heading) heading.textContent = "Tin tuyển dụng";
      if (description) description.textContent = "Xem các tin tuyển dụng đã được công khai và lọc theo từ khóa, địa điểm hoặc loại hình công việc.";
      if (searchButton) searchButton.textContent = "Lọc tin";
      hero.querySelector(".hero-stats")?.remove();
    }
    const jobsTitle = document.querySelector(".jobs-title");
    if (jobsTitle) {
      const heading = jobsTitle.querySelector("h2");
      const description = jobsTitle.querySelector("p");
      if (heading) heading.textContent = "Danh sách tin tuyển dụng";
      if (description) description.textContent = "Các tin đã được duyệt và đang hiển thị trên UniCareer.";
    }
    const filterHeading = document.querySelector(".filter-heading h3");
    if (filterHeading) filterHeading.textContent = "Lọc tin tuyển dụng";
    document.title = "Tin tuyển dụng | UniCareer";
  } else if (user?.role === "employer") {
    layout.querySelectorAll('[data-candidate-page="applications"], [data-candidate-page="cv"], [data-candidate-page="profile"], .portal-menu a[href="ai-matching.html"]')
      .forEach((link) => link.remove());
    document.querySelectorAll('a[href*="apply-job.html"]').forEach((link) => link.remove());
    const dashboard = document.createElement("a");
    dashboard.href = "../company/dashboard.html";
    dashboard.innerHTML = '<span class="nav-emoji">◫</span><span>Quản lý doanh nghiệp</span>';
    layout.querySelector(".portal-menu").prepend(dashboard);
  }

  const token = localStorage.getItem("access_token")
    || localStorage.getItem("unicareer_access_token");
  if (token) {
    addPortalLogoutButton(layout.querySelector(".portal-sidebottom"));
  } else {
    const actions = layout.querySelector(".portal-topbar-right");
    if (actions && !actions.querySelector(".candidate-session-action")) {
      const action = document.createElement("a");
      action.className = "btn btn-outline btn-sm candidate-session-action";
      action.href = "../auth/login.html";
      action.textContent = "Đăng nhập";
      actions.append(action);
    }
  }
}

function updateCandidateIdentity(fullName) {
  const displayName = typeof fullName === "string" ? fullName.trim() : "";
  if (!displayName) return;

  localStorage.setItem("unicareer_full_name", displayName);
  let user;
  try {
    user = JSON.parse(localStorage.getItem("unicareer_user") || "null");
    if (user?.role === "candidate") {
      user.full_name = displayName;
      localStorage.setItem("unicareer_user", JSON.stringify(user));
    }
  } catch (_) {
    localStorage.removeItem("unicareer_user");
  }

  const initials = displayName.split(/\s+/).slice(-2)
    .map((part) => part.slice(0, 1)).join("").toLocaleUpperCase("vi");
  document.querySelectorAll(".portal-sidebottom strong, #candidate-display-name, #apply-candidate-name")
    .forEach((element) => {
      element.textContent = displayName;
    });
  document.querySelectorAll(".portal-sidebottom .portal-avatar, #candidate-avatar")
    .forEach((element) => {
      element.textContent = initials || "U";
    });
  if (user?.role === "candidate") {
    document.querySelectorAll(".nav-side .demo-label").forEach((label) => {
      label.textContent = `${displayName} · Sinh viên`;
    });
  }
}

function initializeCompanyAccessGuard() {
  const path = window.location.pathname;
  const isCompanyPage = path.includes("/pages/company/");
  const isAdminPage = path.includes("/pages/admin/");
  const isCandidateOnlyPage = /\/pages\/candidate\/(my-applications|profile|cv-manage|apply-job|ai-matching)\.html$/.test(path);
  if (!isCompanyPage && !isAdminPage && !isCandidateOnlyPage) return;
  if (isCompanyPage) {
    document.querySelectorAll(".portal-demo").forEach((label) => label.remove());
  }
  if (isAdminPage) {
    document.querySelectorAll(".portal-sidebottom small").forEach((label) => {
      label.textContent = "Quản trị hệ thống";
    });
  }

  const token = localStorage.getItem("access_token")
    || localStorage.getItem("unicareer_access_token");
  const companyDashboardUrl = new URL("../company/dashboard.html", window.location.href);
  const adminDashboardUrl = new URL("../admin/dashboard.html", window.location.href);
  const candidateDashboardUrl = new URL("../candidate/index.html", window.location.href);
  const loginUrl = new URL(`../auth/login.html?next=${encodeURIComponent(path + window.location.search)}`, window.location.href);

  const redirectByRole = (role) => {
    const target = role === "employer" ? companyDashboardUrl
      : role === "admin" ? adminDashboardUrl : candidateDashboardUrl;
    window.location.replace(target.href);
  };
  const roleMatchesPage = (role) =>
    (isCompanyPage && role === "employer")
    || (isAdminPage && role === "admin")
    || (isCandidateOnlyPage && role === "candidate");

  if (!token) {
    window.location.replace(loginUrl.href);
    return;
  }

  if (isCompanyPage || isAdminPage || isCandidateOnlyPage) {
    addPortalLogoutButton(document.querySelector(".portal-sidebottom"));
  }

  let user;
  try {
    user = JSON.parse(localStorage.getItem("unicareer_user") || "null");
  } catch (_) {
    localStorage.removeItem("unicareer_user");
  }
  if (user?.role) {
    if (!roleMatchesPage(user.role)) redirectByRole(user.role);
    return;
  }

  document.documentElement.style.visibility = "hidden";
  UniCareerAPI.getMe().then((currentUser) => {
    localStorage.setItem("unicareer_user", JSON.stringify(currentUser));
    if (!roleMatchesPage(currentUser.role)) {
      redirectByRole(currentUser.role);
      return;
    }
    document.documentElement.style.visibility = "";
  }).catch(() => {
    window.location.replace(loginUrl.href);
  });
}

function addPortalLogoutButton(sidebottom) {
  if (!sidebottom || sidebottom.querySelector(".portal-logout")) return;

  const loginUrl = new URL("../auth/login.html", window.location.href);
  const button = document.createElement("button");
  button.className = "portal-logout";
  button.type = "button";
  button.title = "Đăng xuất";
  button.setAttribute("aria-label", "Đăng xuất");
  button.textContent = "⏻";
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await UniCareerAPI.logout();
    } catch (error) {
      console.warn("Server-side logout failed; clearing the local session.", error);
    }
    UniCareerAPI.signOut();
    window.location.replace(loginUrl.href);
  });
  sidebottom.append(button);
}

function initializeAuthenticationNavigation() {
  const token = localStorage.getItem("access_token")
    || localStorage.getItem("unicareer_access_token");
  const navSide = document.querySelector(".nav-side");
  if (!navSide) return;

  const loginLink = navSide.querySelector('a[href*="login.html"]');
  const loginHref = loginLink?.getAttribute("href")
    || (window.location.pathname.includes("/pages/")
      ? "../auth/login.html"
      : "pages/auth/login.html");

  if (!token) {
    setHomeGuestContentVisible(true);
    navSide.querySelector(".demo-label")?.remove();
    if (!navSide.querySelector('a[href*="login.html"]')) {
      const login = document.createElement("a");
      login.className = "btn btn-outline";
      login.href = loginHref;
      login.textContent = "Đăng nhập";
      navSide.append(login);
    }
    return;
  }

  setHomeGuestContentVisible(false);

  const applyAuthenticatedNavigation = (user) => {
    setHomeGuestContentVisible(false);
    navSide.innerHTML = "";

    const roleNames = {
      candidate: "Ứng viên",
      employer: "Nhà tuyển dụng",
      admin: "Quản trị viên"
    };
    const displayName = user?.full_name
      || localStorage.getItem("unicareer_full_name")
      || user?.name
      || "Người dùng";
    const displayRole = roleNames[user?.role] || "Người dùng";

    if (user?.role === "employer") {
      const dashboardLink = document.createElement("a");
      dashboardLink.className = "btn btn-outline";
      dashboardLink.href = getCompanyDashboardHref();
      dashboardLink.textContent = "Quản lý doanh nghiệp";
      navSide.append(dashboardLink);
      configureEmployerNavigation();
    } else if (user?.role === "admin") {
      configureAdminNavigation();
      const dashboardLink = document.createElement("a");
      dashboardLink.className = "btn btn-outline";
      dashboardLink.href = getAdminDashboardHref();
      dashboardLink.textContent = "Quản trị hệ thống";
      navSide.append(dashboardLink);
    } else {
      configureCandidateNavigation();
    }

    const label = document.createElement("span");
    label.className = "demo-label";
    label.textContent = `${displayName} · ${displayRole}`;
    navSide.append(label);

    const logout = document.createElement("button");
    logout.className = "btn btn-outline";
    logout.type = "button";
    logout.textContent = "Đăng xuất";
    logout.addEventListener("click", async () => {
      try {
        await UniCareerAPI.logout();
      } catch (_) {
        // Local logout still succeeds if the API is temporarily unavailable.
      }
      localStorage.removeItem("access_token");
      localStorage.removeItem("unicareer_access_token");
      localStorage.removeItem("unicareer_user");
      localStorage.removeItem("unicareer_full_name");
      window.location.href = loginHref;
    });
    navSide.append(logout);
  };

  const storedUser = localStorage.getItem("unicareer_user");
  if (storedUser) {
    try {
      applyAuthenticatedNavigation(JSON.parse(storedUser));
      return;
    } catch (_) {
      localStorage.removeItem("unicareer_user");
    }
  }

  UniCareerAPI.getMe().then((user) => {
    const storedUser = JSON.parse(localStorage.getItem("unicareer_user") || "{}");
    const mergedUser = { ...user, full_name: user.full_name || storedUser.full_name };
    if (mergedUser.full_name) {
      localStorage.setItem("unicareer_full_name", mergedUser.full_name);
    }
    localStorage.setItem("unicareer_user", JSON.stringify(mergedUser));
    applyAuthenticatedNavigation(mergedUser);
  }).catch(() => {
    setHomeGuestContentVisible(true);
    localStorage.removeItem("access_token");
    localStorage.removeItem("unicareer_access_token");
    localStorage.removeItem("unicareer_user");
    localStorage.removeItem("unicareer_full_name");
    navSide.innerHTML = "";
    const login = document.createElement("a");
    login.className = "btn btn-outline";
    login.href = loginHref;
    login.textContent = "Đăng nhập";
    navSide.append(login);
  });
}

function setHomeGuestContentVisible(isVisible) {
  const employerSection = document.getElementById("employers");
  if (!employerSection) return;

  [
    employerSection,
    document.querySelector(".home-demo-note"),
    document.querySelector('a[href="#employers"]'),
    document.querySelector('.home-hero a[href*="register.html"]')
  ].filter(Boolean).forEach((element) => {
    element.hidden = !isVisible;
    element.style.display = isVisible ? "" : "none";
  });
}

function getCompanyDashboardHref() {
  return new URL(
    window.location.pathname.includes("/pages/")
      ? "../company/dashboard.html"
      : "pages/company/dashboard.html",
    window.location.href
  ).href;
}

function getAdminDashboardHref() {
  return new URL(
    window.location.pathname.includes("/pages/")
      ? "../admin/dashboard.html"
      : "pages/admin/dashboard.html",
    window.location.href
  ).href;
}

function configureEmployerNavigation() {
  document.querySelectorAll(
    'a[href*="my-applications.html"], a[href*="cv-manage.html"], a[href*="profile.html"], a[href*="apply-job.html"]'
  ).forEach((link) => {
    setLinkVisibility(link, false);
  });

  const candidateLink = document.querySelector('.nav-main a[href*="candidate/"]');
  if (candidateLink) setLinkVisibility(candidateLink, false);

  const businessLink = document.querySelector('.nav-main a[href="#employers"]');
  if (businessLink) {
    businessLink.href = getCompanyDashboardHref();
    businessLink.textContent = "Quản lý doanh nghiệp";
    setLinkVisibility(businessLink, true);
  }

  const homeJobLink = document.querySelector('.home-hero a[href*="candidate/"]');
  if (homeJobLink) {
    homeJobLink.href = getCompanyDashboardHref();
    homeJobLink.textContent = "Quản lý doanh nghiệp";
  }

  const footerJobLink = document.querySelector('.footer-links a[href*="candidate/"]');
  if (footerJobLink) setLinkVisibility(footerJobLink, false);
  hideFooterLoginLink();
  addFooterCompanyDashboardLink();
}

function configureCandidateNavigation() {
  document.querySelectorAll('a[href*="company/"]').forEach((link) => {
    setLinkVisibility(link, false);
  });
  hideFooterLoginLink();
}

function configureAdminNavigation() {
  document.querySelectorAll('a[href*="candidate/index.html"]').forEach((link) => {
    link.textContent = "Tin tuyển dụng";
  });
}

function hideFooterLoginLink() {
  document.querySelectorAll('.footer-links a[href*="login.html"]').forEach((link) => {
    setLinkVisibility(link, false);
  });
}

function addFooterCompanyDashboardLink() {
  const footerLinks = document.querySelector(".footer-links");
  if (!footerLinks || footerLinks.querySelector('a[href*="/company/dashboard.html"]')) return;

  const dashboardLink = document.createElement("a");
  dashboardLink.href = getCompanyDashboardHref();
  dashboardLink.textContent = "Quản lý doanh nghiệp";
  footerLinks.append(dashboardLink);
}

function setLinkVisibility(link, isVisible) {
  link.hidden = !isVisible;
  link.style.display = isVisible ? "" : "none";
}

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
  if (window.UniCareerAPI) return;
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
      const salaryText = Array.from(card.querySelectorAll(".job-meta span"))
        .map((item) => item.textContent.toLocaleLowerCase("vi"))
        .find((value) => value.includes("triệu/tháng") || value.includes("thỏa thuận")) || "";
      const matchesSalary = !salary
        || (salary === "paid" ? salaryText.includes("triệu/tháng") : salaryText.includes("thỏa thuận"));
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
  if (window.UniCareerAPI) return;
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
        ? `${visibleCount} kết quả phù hợp.`
        : "Không tìm thấy kết quả phù hợp.";
    };

    controls.forEach((control) => {
      control.addEventListener(control.matches("select") ? "change" : "input", applyFilters);
    });
  });
}

function initializeApplicationDetails() {
  if (window.UniCareerAPI) return;
  const title = document.getElementById("apply-job-title");
  if (!title) return;

  const jobs = {
    backend: {
      title: "Backend Developer Intern",
      company: "Công ty TNHH Công nghệ Mây Việt",
      location: "TP. Hồ Chí Minh",
      salary: "5–7 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail.html",
      logo: "M",
    },
    frontend: {
      title: "Frontend Developer Intern",
      company: "Công ty Cổ phần Sản phẩm số Hướng Dương",
      location: "TP. Hồ Chí Minh · Hybrid",
      salary: "4–6 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail-frontend.html",
      logo: "H",
    },
    data: {
      title: "Data Analyst Intern",
      company: "Công ty TNHH Phân tích dữ liệu An Bình",
      location: "Hà Nội",
      salary: "5–7 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail-data.html",
      logo: "A",
    },
    business: {
      title: "Business Analyst Intern",
      company: "Công ty Cổ phần Giải pháp Vận hành Minh Tâm",
      location: "TP. Hồ Chí Minh",
      salary: "4–6 triệu/tháng",
      type: "Thực tập",
      detail: "job-detail-business.html",
      logo: "M",
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
  if (window.UniCareerAPI) return;
  const form = document.getElementById("edit-job-form");
  if (!form) return;

  const jobs = {
    backend: {
      title: "Backend Developer Intern",
      type: "Thực tập",
      location: "TP. Hồ Chí Minh",
      salary: "5–7 triệu/tháng",
      deadline: "2026-12-20",
      experience: "Không yêu cầu",
      description: "Tham gia phát triển và kiểm thử REST API bằng Python, phối hợp với nhóm sản phẩm để cải thiện hiệu năng và độ ổn định của dịch vụ.",
      requirements: "Nắm kiến thức Python cơ bản; có hiểu biết về SQL, Git và mong muốn học FastAPI.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    frontend: {
      title: "Frontend Developer Intern",
      type: "Thực tập",
      location: "TP. Hồ Chí Minh · Hybrid",
      salary: "4–6 triệu/tháng",
      deadline: "2026-12-25",
      experience: "Không yêu cầu",
      description: "Phát triển giao diện web responsive, kết nối API và phối hợp với nhóm thiết kế để hoàn thiện trải nghiệm người dùng.",
      requirements: "Có kiến thức HTML, CSS, JavaScript; biết React là lợi thế.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    data: {
      title: "Data Analyst Intern",
      type: "Thực tập",
      location: "Hà Nội",
      salary: "5–7 triệu/tháng",
      deadline: "2026-12-28",
      experience: "Không yêu cầu",
      description: "Làm sạch dữ liệu, xây dựng báo cáo định kỳ và hỗ trợ nhóm kinh doanh theo dõi các chỉ số vận hành.",
      requirements: "Sử dụng được Excel; có kiến thức SQL cơ bản. Biết Power BI là lợi thế.",
      status: "Đang tuyển",
      statusClass: "status--success",
    },
    business: {
      title: "Business Analyst Intern",
      type: "Thực tập",
      location: "TP. Hồ Chí Minh",
      salary: "4–6 triệu/tháng",
      deadline: "2026-12-31",
      experience: "Không yêu cầu",
      description: "Thu thập yêu cầu nghiệp vụ, mô hình hóa quy trình và phối hợp với nhóm sản phẩm để xác nhận phạm vi giải pháp.",
      requirements: "Giao tiếp và trình bày rõ ràng; sử dụng được Excel. Biết viết user story là lợi thế.",
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
