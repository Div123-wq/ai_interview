// ─── Auth Helpers ──────────────────────────────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem("jwt_token"),
  getUser: () => {
    try { return JSON.parse(localStorage.getItem("user") || "null"); } catch { return null; }
  },
  setSession: (token, user) => {
    localStorage.setItem("jwt_token", token);
    localStorage.setItem("user", JSON.stringify(user));
  },
  clear: () => {
    localStorage.removeItem("jwt_token");
    localStorage.removeItem("user");
  },
  isLoggedIn: () => !!localStorage.getItem("jwt_token"),
  requireAuth: () => {
    if (!localStorage.getItem("jwt_token")) {
      window.location.href = "index.html";
    }
  }
};

// ─── API Client ────────────────────────────────────────────────────────────────
const API = {
  async request(method, path, body = null, isFormData = false) {
    const headers = {};
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!isFormData) headers["Content-Type"] = "application/json";

    const opts = { method, headers };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    try {
      const res = await fetch(`${API_BASE}${path}`, opts);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      return data;
    } catch (err) {
      if (err.message.includes("Failed to fetch")) {
        throw new Error("Cannot connect to server. Make sure the backend is running on port 5000.");
      }
      throw err;
    }
  },
  get: (path) => API.request("GET", path),
  post: (path, body) => API.request("POST", path, body),
  put: (path, body) => API.request("PUT", path, body),
  delete: (path) => API.request("DELETE", path),
  postForm: (path, formData) => API.request("POST", path, formData, true),
};

// ─── Toast Notifications ───────────────────────────────────────────────────────
function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container") || (() => {
    const el = document.createElement("div");
    el.id = "toast-container";
    document.body.appendChild(el);
    return el;
  })();

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icons = { success: "✅", error: "❌", info: "ℹ️", warning: "⚠️" };
  toast.innerHTML = `<span class="toast-icon">${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 400);
  }, duration);
}

// ─── Loading Overlay ───────────────────────────────────────────────────────────
function showLoader(text = "Loading...") {
  let el = document.getElementById("global-loader");
  if (!el) {
    el = document.createElement("div");
    el.id = "global-loader";
    document.body.appendChild(el);
  }
  el.innerHTML = `<div class="loader-box"><div class="loader-spinner"></div><p>${text}</p></div>`;
  el.classList.add("active");
}
function hideLoader() {
  const el = document.getElementById("global-loader");
  if (el) el.classList.remove("active");
}

// ─── Nav User Display ──────────────────────────────────────────────────────────
function initNav() {
  const user = Auth.getUser();
  const nameEl = document.getElementById("nav-user-name");
  const avatarEl = document.getElementById("nav-avatar");
  if (nameEl && user) nameEl.textContent = user.name;
  if (avatarEl && user) avatarEl.textContent = user.name.charAt(0).toUpperCase();

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      Auth.clear();
      window.location.href = "index.html";
    });
  }
}

// ─── Utility Functions ─────────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit", month: "short", year: "numeric"
  });
}

function scoreColor(score) {
  if (score >= 8) return "#10b981";
  if (score >= 6) return "#f59e0b";
  if (score >= 4) return "#f97316";
  return "#ef4444";
}

function gradeLabel(avg) {
  if (avg >= 8) return { grade: "A", label: "Excellent", color: "#10b981" };
  if (avg >= 6) return { grade: "B", label: "Good", color: "#3b82f6" };
  if (avg >= 4) return { grade: "C", label: "Average", color: "#f59e0b" };
  return { grade: "D", label: "Needs Improvement", color: "#ef4444" };
}

function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, "<code>$1</code>")
    .replace(/^### (.*$)/gm, "<h4>$1</h4>")
    .replace(/^## (.*$)/gm, "<h3>$1</h3>")
    .replace(/^# (.*$)/gm, "<h2>$1</h2>")
    .replace(/^\- (.*$)/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul])/gm, "<p>")
    .replace(/<p><\/p>/g, "");
}

document.addEventListener("DOMContentLoaded", initNav);
