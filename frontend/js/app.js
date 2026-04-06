/* ═══════════════════════════════════════════════════════════════════════════
   AuditX — Frontend Application v2.1
   Production-quality SPA logic
   ═══════════════════════════════════════════════════════════════════════════ */

// ── State ────────────────────────────────────────────────────────────────────
let currentScanId = null;
let currentIssues = [];
let currentData = null;
let authToken = localStorage.getItem("auditx_token");
let authUsername = localStorage.getItem("auditx_user");
let authMode = "login";
let agentInterval = null;

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    updateAuthUI();
    loadHistory();

    // Enter key triggers scan
    document.getElementById("urlInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") startScan();
    });

    // Keyboard shortcut: "/" to focus URL input
    document.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement.tagName !== "INPUT") {
            e.preventDefault();
            document.getElementById("urlInput").focus();
        }
        if (e.key === "Escape") {
            hideAuthModal();
            const sidebar = document.getElementById("historySidebar");
            if (!sidebar.classList.contains("hidden")) sidebar.classList.add("hidden");
        }
    });

    // Close modal on overlay click
    document.getElementById("authModal").addEventListener("click", (e) => {
        if (e.target === document.getElementById("authModal")) hideAuthModal();
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════════════

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    const icons = { success: "✅", error: "❌", info: "ℹ️", warning: "⚠️" };
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || "ℹ️"}</span>
        <span class="toast-msg">${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("toast-visible"));

    setTimeout(() => {
        toast.classList.remove("toast-visible");
        setTimeout(() => toast.remove(), 350);
    }, 3500);
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════════════════════

function showAuthModal(mode) {
    authMode = mode;
    const modal = document.getElementById("authModal");
    const title = document.getElementById("authModalTitle");
    const submitBtn = document.getElementById("authSubmitBtn");
    const switchEl = document.getElementById("authSwitch");
    const errorEl = document.getElementById("authError");

    errorEl.classList.add("hidden");
    document.getElementById("authForm").reset();

    if (mode === "login") {
        title.textContent = "Welcome Back";
        submitBtn.textContent = "Login";
        switchEl.innerHTML = `Don't have an account? <a onclick="showAuthModal('register')">Sign Up</a>`;
    } else {
        title.textContent = "Create Account";
        submitBtn.textContent = "Sign Up";
        switchEl.innerHTML = `Already have an account? <a onclick="showAuthModal('login')">Login</a>`;
    }

    modal.classList.remove("hidden");
    setTimeout(() => document.getElementById("authUsername").focus(), 100);
}

function hideAuthModal() {
    document.getElementById("authModal").classList.add("hidden");
}

async function handleAuth(e) {
    e.preventDefault();
    const username = document.getElementById("authUsername").value.trim();
    const password = document.getElementById("authPassword").value;
    const errorEl = document.getElementById("authError");
    const submitBtn = document.getElementById("authSubmitBtn");

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-sm"></span> Please wait...`;
    errorEl.classList.add("hidden");

    const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";

    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Authentication failed");
        }

        authToken = data.access_token;
        authUsername = data.username;
        localStorage.setItem("auditx_token", authToken);
        localStorage.setItem("auditx_user", authUsername);

        updateAuthUI();
        hideAuthModal();
        loadHistory();
        showToast(`Welcome, ${authUsername}! 👋`, "success");
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.remove("hidden");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = authMode === "login" ? "Login" : "Sign Up";
    }
}

function logout() {
    authToken = null;
    authUsername = null;
    localStorage.removeItem("auditx_token");
    localStorage.removeItem("auditx_user");
    updateAuthUI();
    loadHistory();
    showToast("Logged out successfully", "info");
}

function updateAuthUI() {
    const authSection = document.getElementById("authSection");
    const userSection = document.getElementById("userSection");
    const userBadge = document.getElementById("userBadge");

    if (authToken && authUsername) {
        authSection.classList.add("hidden");
        userSection.classList.remove("hidden");
        userBadge.textContent = `👤 ${authUsername}`;
    } else {
        authSection.classList.remove("hidden");
        userSection.classList.add("hidden");
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SCAN
// ═══════════════════════════════════════════════════════════════════════════

async function startScan(urlOverride) {
    const urlInput = document.getElementById("urlInput");
    let url = (urlOverride || urlInput.value).trim();

    if (!url) {
        urlInput.focus();
        showToast("Please enter a URL to analyze", "warning");
        return;
    }

    // Auto-prepend https if missing
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = "https://" + url;
    }

    urlInput.value = url;

    // Show loading
    showSection("loading");
    document.getElementById("loadingUrl").textContent = url;
    startAgentAnimation();

    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    try {
        const res = await fetch("/api/analyze", {
            method: "POST",
            headers,
            body: JSON.stringify({ url }),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Scan failed");
        }

        stopAgentAnimation();
        currentScanId = data.scan_id;
        currentIssues = data.issues || [];
        currentData = data;

        renderDashboard(data);
        showSection("dashboard");
        loadHistory();
        showToast(`Scan complete — ${data.total_issues} issues found`, data.total_issues > 0 ? "warning" : "success");
    } catch (err) {
        stopAgentAnimation();
        showToast("Scan failed: " + err.message, "error");
        showSection("hero");
    }
}

function startAgentAnimation() {
    const steps = document.querySelectorAll(".agent-step");
    steps.forEach((s) => s.classList.remove("active", "done"));

    let i = 0;
    agentInterval = setInterval(() => {
        if (i > 0 && i <= steps.length) {
            steps[i - 1].classList.remove("active");
            steps[i - 1].classList.add("done");
        }
        if (i < steps.length) {
            steps[i].classList.add("active");
        } else {
            clearInterval(agentInterval);
            agentInterval = null;
        }
        i++;
    }, 2800);
}

function stopAgentAnimation() {
    if (agentInterval) {
        clearInterval(agentInterval);
        agentInterval = null;
    }
    document.querySelectorAll(".agent-step").forEach((s) => {
        s.classList.remove("active");
        s.classList.add("done");
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD RENDERING
// ═══════════════════════════════════════════════════════════════════════════

function renderDashboard(data) {
    document.getElementById("dashUrl").textContent = data.url;

    // Runtime badge
    const runtimeEl = document.getElementById("dashRuntime");
    if (runtimeEl) runtimeEl.textContent = `⏱ ${data.runtime}s`;

    renderScoreCards(data.scores);
    renderSeverityBars(data.severity_counts, data.total_issues);
    renderIssueCards(data.issues);

    // Reset filter to All
    document.querySelectorAll(".filter-tab").forEach((t) =>
        t.classList.toggle("active", t.dataset.filter === "all")
    );
}

function renderScoreCards(scores) {
    const grid = document.getElementById("scoreGrid");
    const categories = [
        { key: "overall", label: "Overall", icon: "🏆" },
        { key: "security", label: "Security", icon: "🔒" },
        { key: "seo", label: "SEO", icon: "📈" },
        { key: "performance", label: "Performance", icon: "⚡" },
        { key: "content", label: "Content", icon: "📝" },
    ];

    grid.innerHTML = categories
        .map((cat) => {
            const score = scores[cat.key] ?? 0;
            const color = getScoreColor(score);
            const grade = getGrade(score);
            const circumference = 2 * Math.PI * 42;
            const offset = circumference - (score / 100) * circumference;
            const isOverall = cat.key === "overall";

            return `
                <div class="score-card ${isOverall ? "overall" : ""}" id="card-${cat.key}">
                    <div class="score-label">${cat.icon} ${cat.label}</div>
                    <div class="score-gauge">
                        <svg viewBox="0 0 100 100">
                            <circle class="bg-ring" cx="50" cy="50" r="42" />
                            <circle
                                class="score-ring"
                                cx="50" cy="50" r="42"
                                stroke="${color}"
                                stroke-dasharray="${circumference}"
                                stroke-dashoffset="${circumference}"
                                data-target="${offset}"
                            />
                        </svg>
                        <div class="score-value" style="color: ${color}" data-final="${score}">0</div>
                    </div>
                    <div class="score-grade" style="color: ${color}">Grade: <strong>${grade}</strong></div>
                </div>
            `;
        })
        .join("");

    // Animate after render
    requestAnimationFrame(() => {
        setTimeout(() => {
            grid.querySelectorAll(".score-ring").forEach((ring) => {
                ring.style.strokeDashoffset = ring.dataset.target;
            });

            grid.querySelectorAll(".score-value").forEach((el) => {
                const final = parseFloat(el.dataset.final) || 0;
                animateNumber(el, 0, final, 1400);
            });
        }, 120);
    });
}

function renderSeverityBars(counts, total) {
    const container = document.getElementById("severityBars");
    const max = Math.max(counts.HIGH || 0, counts.MEDIUM || 0, counts.LOW || 0, 1);

    const bars = [
        { key: "HIGH", label: "🔴 HIGH", cls: "sev-high" },
        { key: "MEDIUM", label: "🟡 MEDIUM", cls: "sev-medium" },
        { key: "LOW", label: "🔵 LOW", cls: "sev-low" },
    ];

    container.innerHTML = bars.map(({ key, label, cls }) => `
        <div class="sev-bar-card ${cls}">
            <div class="sev-bar-header">
                <span class="sev-bar-label">${label}</span>
                <span class="sev-bar-count" data-final="${counts[key] || 0}">0</span>
            </div>
            <div class="sev-bar-track">
                <div class="sev-bar-fill" data-width="${((counts[key] || 0) / max) * 100}"></div>
            </div>
        </div>
    `).join("");

    requestAnimationFrame(() => {
        setTimeout(() => {
            container.querySelectorAll(".sev-bar-fill").forEach((bar) => {
                bar.style.width = bar.dataset.width + "%";
            });
            container.querySelectorAll(".sev-bar-count").forEach((el) => {
                animateNumber(el, 0, parseInt(el.dataset.final) || 0, 900);
            });
        }, 200);
    });
}

let activeFilter = "all";

function renderIssueCards(issues) {
    const grid = document.getElementById("issuesGrid");
    const totalEl = document.getElementById("issueCount");
    if (totalEl) totalEl.textContent = issues ? issues.length : 0;

    if (!issues || issues.length === 0) {
        grid.innerHTML = `
            <div class="empty-result">
                <div class="empty-icon">✅</div>
                <div class="empty-title">No Issues Found</div>
                <div class="empty-sub">Great job! This site looks clean.</div>
            </div>`;
        return;
    }

    // Sort: HIGH → MEDIUM → LOW
    const sorted = [...issues].sort((a, b) => {
        const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
        return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
    });

    grid.innerHTML = sorted.map((issue, idx) => `
        <div class="issue-card" data-severity="${issue.severity}" style="animation-delay: ${idx * 30}ms">
            <div class="issue-card-header">
                <div class="issue-title">${escapeHtml(issue.title)}</div>
                <span class="severity-badge ${(issue.severity || "low").toLowerCase()}">${issue.severity}</span>
            </div>
            <div class="issue-meta-row">
                <span class="issue-category">${escapeHtml(issue.category)}</span>
                ${issue.location ? `<span class="issue-location" title="Location">${escapeHtml(issue.location)}</span>` : ""}
            </div>
            <div class="issue-description">${escapeHtml(String(issue.description || "").substring(0, 220))}</div>
            <div class="issue-impact">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
                ${escapeHtml(issue.impact || "")}
            </div>
            <div class="issue-fix">
                <span class="issue-fix-icon">💡</span>
                <span>${escapeHtml(issue.suggestion || "")}</span>
            </div>
        </div>
    `).join("");
}

// ═══════════════════════════════════════════════════════════════════════════
// FILTERS
// ═══════════════════════════════════════════════════════════════════════════

function filterIssues(severity) {
    activeFilter = severity;

    document.querySelectorAll(".filter-tab").forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.filter === severity);
    });

    const cards = document.querySelectorAll(".issue-card");
    const grid = document.getElementById("issuesGrid");

    let visible = 0;
    cards.forEach((card) => {
        const show = severity === "all" || card.dataset.severity === severity;
        card.style.display = show ? "" : "none";
        if (show) visible++;
    });

    // Show empty state if no matches
    const existingEmpty = grid.querySelector(".filter-empty");
    if (existingEmpty) existingEmpty.remove();

    if (visible === 0) {
        const empty = document.createElement("div");
        empty.className = "filter-empty empty-result";
        empty.innerHTML = `
            <div class="empty-icon">🔍</div>
            <div class="empty-title">No ${severity} issues</div>
            <div class="empty-sub">No issues at this severity level.</div>
        `;
        grid.appendChild(empty);
    }

    const countEl = document.getElementById("issueCount");
    if (countEl) countEl.textContent = visible;
}

// ═══════════════════════════════════════════════════════════════════════════
// DOWNLOADS
// ═══════════════════════════════════════════════════════════════════════════

function downloadJSON() {
    if (!currentScanId) {
        showToast("No scan available to download", "warning");
        return;
    }
    window.open(`/api/download/json/${currentScanId}`, "_blank");
}

function downloadPDF() {
    if (!currentScanId) {
        showToast("No scan available to download", "warning");
        return;
    }
    showToast("Generating PDF report...", "info");
    window.open(`/api/download/pdf/${currentScanId}`, "_blank");
}

// ═══════════════════════════════════════════════════════════════════════════
// HISTORY
// ═══════════════════════════════════════════════════════════════════════════

function toggleHistory() {
    const sidebar = document.getElementById("historySidebar");
    const isHidden = sidebar.classList.contains("hidden");
    sidebar.classList.toggle("hidden", !isHidden);
    if (isHidden) loadHistory();
}

async function loadHistory() {
    const listEl = document.getElementById("historyList");
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    try {
        const res = await fetch("/api/history?limit=20", { headers });
        if (!res.ok) throw new Error("Failed to load");
        const data = await res.json();

        if (!data.scans || data.scans.length === 0) {
            listEl.innerHTML = `<p class="empty-state">No scans yet.<br/>Analyze a URL to get started.</p>`;
            return;
        }

        listEl.innerHTML = data.scans.map((scan) => `
            <div class="history-card" onclick="loadFromHistory('${escapeHtml(scan.url)}')" title="Re-scan ${escapeHtml(scan.url)}">
                <div class="history-url">${escapeHtml(truncateUrl(scan.url, 48))}</div>
                <div class="history-meta">
                    <span class="history-score-badge" style="color: ${getScoreColor(scan.overall_score)}">${scan.overall_score}/100</span>
                    <span class="history-issues">
                        ${scan.high_count > 0 ? `<span class="hist-tag high">${scan.high_count}H</span>` : ""}
                        ${scan.medium_count > 0 ? `<span class="hist-tag medium">${scan.medium_count}M</span>` : ""}
                        ${scan.low_count > 0 ? `<span class="hist-tag low">${scan.low_count}L</span>` : ""}
                    </span>
                    <span class="history-date">${formatDate(scan.created_at)}</span>
                </div>
            </div>
        `).join("");
    } catch (err) {
        listEl.innerHTML = `<p class="empty-state">Failed to load history</p>`;
    }
}

function loadFromHistory(url) {
    // Close sidebar
    document.getElementById("historySidebar").classList.add("hidden");
    // Set the input value and trigger scan
    document.getElementById("urlInput").value = url;
    startScan(url);
}

// ═══════════════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════

function showSection(section) {
    document.getElementById("heroSection").classList.toggle("hidden", section !== "hero");
    document.getElementById("loadingSection").classList.toggle("hidden", section !== "loading");
    document.getElementById("dashboard").classList.toggle("hidden", section !== "dashboard");
    document.getElementById("footer").classList.toggle("hidden", section === "loading");
}

function newScan() {
    currentScanId = null;
    currentIssues = [];
    currentData = null;
    document.getElementById("urlInput").value = "";
    showSection("hero");
    setTimeout(() => document.getElementById("urlInput").focus(), 200);
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

function getScoreColor(score) {
    if (score >= 80) return "#22c55e";
    if (score >= 60) return "#f59e0b";
    if (score >= 40) return "#f97316";
    return "#ef4444";
}

function getGrade(score) {
    if (score >= 90) return "A+";
    if (score >= 80) return "A";
    if (score >= 70) return "B";
    if (score >= 60) return "C";
    if (score >= 50) return "D";
    return "F";
}

function animateNumber(el, from, to, duration) {
    const start = performance.now();
    const isFloat = !Number.isInteger(to);
    const update = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = from + (to - from) * eased;
        el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
        if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
}

function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
}

function formatDate(isoStr) {
    if (!isoStr) return "";
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch {
        return "";
    }
}

function truncateUrl(url, max) {
    if (!url) return "";
    try {
        const u = new URL(url);
        const display = u.hostname + u.pathname;
        return display.length > max ? display.substring(0, max) + "…" : display;
    } catch {
        return url.length > max ? url.substring(0, max) + "…" : url;
    }
}
