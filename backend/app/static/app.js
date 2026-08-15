// Submittery v2 - Frontend Controller & Router
let apiBaseUrl = window.location.origin;

// State Management
let currentToken = localStorage.getItem("token") || null;
let currentUser = null;
let problems = [];
let userSubmissions = [];
let currentProblem = null;
let lastSubmissionId = null;
let editorLoaded = false;
let wsSub = null;
let wsCollab = null;

let isCollaborating = false;
let currentRoomCode = null;
let currentActiveView = "home";
let activeConsoleTab = "result";

// Filter state
let filterDifficulty = "all";

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    // Theme Initializer
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
        const toggleIcon = document.getElementById("theme-toggle-icon");
        if (toggleIcon) toggleIcon.className = "fa-solid fa-moon text-xs";
    }
    
    initMonaco();
    checkAuth();
    loadProblems();
    initDraggableDividers();
    
    // Check if room parameter exists in URL queries
    const urlParams = new URLSearchParams(window.location.search);
    const roomParam = urlParams.get('room');
    if (roomParam) {
        document.getElementById("lobby-join-code-input").value = roomParam;
        navigateTo("collab");
        setTimeout(() => {
            if (currentToken) {
                joinCollaborationRoom(roomParam);
            } else {
                showAuthModal();
            }
        }, 1000);
    }
    
    // Setup AI chat input listener for Enter key
    document.getElementById("wai-chat-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            triggerAIAction("ask");
        }
    });
});

// View Navigation Router
function navigateTo(viewName) {
    // Security Access Guard Redirect
    if (viewName === "admin" && (!currentUser || currentUser.role !== "admin")) {
        viewName = "home";
    }
    
    currentActiveView = viewName;
    
    // Deactivate all sections and header buttons
    const sections = document.querySelectorAll(".view-section");
    sections.forEach(sec => sec.classList.remove("active", "flex"));
    sections.forEach(sec => sec.classList.add("hidden"));
    
    const navButtons = document.querySelectorAll("nav button");
    navButtons.forEach(btn => {
        const isHidden = btn.id === "nav-admin" && (!currentUser || currentUser.role !== "admin");
        if (isHidden) {
            btn.className = "hidden px-3.5 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition";
        } else {
            btn.className = "px-3.5 py-1.5 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition";
        }
    });
    
    // Activate target section
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
        targetSection.classList.remove("hidden");
        targetSection.classList.add("active", "flex");
    }
    
    // Highlight nav button
    const targetNav = document.getElementById(`nav-${viewName}`);
    if (targetNav) {
        const isHidden = targetNav.id === "nav-admin" && (!currentUser || currentUser.role !== "admin");
        if (isHidden) {
            targetNav.className = "hidden px-3.5 py-1.5 rounded-lg text-sm font-semibold text-brand-500 bg-brand-500/10 transition";
        } else {
            targetNav.className = "px-3.5 py-1.5 rounded-lg text-sm font-semibold text-brand-500 bg-brand-500/10 transition";
        }
    }
    
    // Refresh stats if navigating to dashboard
    if (viewName === "dashboard") {
        calculateUserStats();
    }
    // Refresh admin data if navigating to admin
    if (viewName === "admin" && currentUser?.role === "admin") {
        loadAdminSubmissions();
    }
    
    // Trigger Monaco Editor layout update if returning to workspace
    if (viewName === "workspace" && window.editor) {
        setTimeout(() => window.editor.layout(), 100);
    }
}

// Interactive Draggable Dividers (LeetCode-style vertical and horizontal panels)
function initDraggableDividers() {
    const verticalDivider = document.getElementById("vertical-divider");
    const horizontalDivider = document.getElementById("horizontal-divider");
    
    const leftPane = document.getElementById("workspace-left-pane");
    const rightPane = document.getElementById("workspace-right-pane");
    
    const editorPane = document.getElementById("workspace-editor-pane");
    const consolePane = document.getElementById("workspace-console-pane");
    const workspaceContainer = document.getElementById("view-workspace");
    
    // Vertical Divider Dragging
    if (verticalDivider) {
        verticalDivider.addEventListener("mousedown", (e) => {
            e.preventDefault();
            verticalDivider.classList.add("dragging");
            document.addEventListener("mousemove", onMouseMoveVertical);
            document.addEventListener("mouseup", onMouseUpVertical);
        });
    }
    
    function onMouseMoveVertical(e) {
        const containerWidth = workspaceContainer.clientWidth;
        let leftWidth = e.clientX;
        
        // Boundaries: 20% to 80%
        if (leftWidth < containerWidth * 0.2) leftWidth = containerWidth * 0.2;
        if (leftWidth > containerWidth * 0.8) leftWidth = containerWidth * 0.8;
        
        leftPane.style.width = `${leftWidth}px`;
        // Account for vertical handle width (6px)
        rightPane.style.width = `${containerWidth - leftWidth - 6}px`;
        
        if (window.editor) window.editor.layout();
    }
    
    function onMouseUpVertical() {
        verticalDivider.classList.remove("dragging");
        document.removeEventListener("mousemove", onMouseMoveVertical);
        document.removeEventListener("mouseup", onMouseUpVertical);
        if (window.editor) window.editor.layout();
    }
    
    // Horizontal Divider Dragging
    if (horizontalDivider) {
        horizontalDivider.addEventListener("mousedown", (e) => {
            e.preventDefault();
            horizontalDivider.classList.add("dragging");
            document.addEventListener("mousemove", onMouseMoveHorizontal);
            document.addEventListener("mouseup", onMouseUpHorizontal);
        });
    }
    
    function onMouseMoveHorizontal(e) {
        const rightPaneHeight = rightPane.clientHeight;
        const rightPaneRect = rightPane.getBoundingClientRect();
        
        let topHeight = e.clientY - rightPaneRect.top;
        
        // Boundaries: 20% to 80%
        if (topHeight < rightPaneHeight * 0.2) topHeight = rightPaneHeight * 0.2;
        if (topHeight > rightPaneHeight * 0.8) topHeight = rightPaneHeight * 0.8;
        
        editorPane.style.height = `${topHeight}px`;
        // Account for horizontal handle height (6px)
        consolePane.style.height = `${rightPaneHeight - topHeight - 6}px`;
        
        if (window.editor) window.editor.layout();
    }
    
    function onMouseUpHorizontal() {
        horizontalDivider.classList.remove("dragging");
        document.removeEventListener("mousemove", onMouseMoveHorizontal);
        document.removeEventListener("mouseup", onMouseUpHorizontal);
        if (window.editor) window.editor.layout();
    }
}

// Monaco Editor Initialization
function initMonaco() {
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.46.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
        const savedTheme = localStorage.getItem("theme") || "dark";
        window.editor = monaco.editor.create(document.getElementById('monaco-editor-workspace'), {
            value: 'def solve():\n    # Select a problem to start coding\n    pass',
            language: 'python',
            theme: savedTheme === "light" ? 'vs' : 'vs-dark',
            fontFamily: 'JetBrains Mono',
            fontSize: 12,
            automaticLayout: true,
            minimap: { enabled: false }
        });
        editorLoaded = true;
        
        // Broadcast code modifications to peers in collab mode
        window.editor.onDidChangeModelContent((event) => {
            if (isCollaborating && wsCollab && wsCollab.readyState === WebSocket.OPEN) {
                if (!event.isFlush) {
                    const code = window.editor.getValue();
                    wsCollab.send(JSON.stringify({
                        type: "sync-code",
                        code: code
                    }));
                }
            }
        });
    });
}

// Math equations formatting
function formatMathFormulas() {
    if (typeof renderMathInElement === 'function') {
        renderMathInElement(document.getElementById("workspace-description-container"), {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\(', right: '\\)', display: false},
                {left: '\\[', right: '\\[', display: true}
            ],
            throwOnError : false
        });
        
        renderMathInElement(document.getElementById("wai-response-box"), {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false}
            ],
            throwOnError : false
        });
    }
}

// REST helper Client
async function request(endpoint, options = {}) {
    const url = `${apiBaseUrl}/api${endpoint}`;
    const headers = { ...options.headers };
    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }
    
    const requestOptions = {
        ...options,
        headers
    };
    
    const response = await fetch(url, requestOptions);
    
    if (response.status === 401) {
        localStorage.removeItem("token");
        currentToken = null;
        currentUser = null;
        updateUIForAuth();
        showAuthModal();
        throw new Error("Unauthorized");
    }
    
    if (!response.ok) {
        const errText = await response.text();
        let errMsg = "An error occurred";
        try {
            const errJson = JSON.parse(errText);
            errMsg = errJson.detail || errMsg;
        } catch (e) {}
        throw new Error(errMsg);
    }
    
    if (response.status === 204) return null;
    return response.json();
}

// Auth credentials verification
async function checkAuth() {
    if (!currentToken) {
        updateUIForAuth();
        document.getElementById("nav-admin").classList.add("hidden");
        return;
    }
    try {
        currentUser = await request("/auth/me");
        updateUIForAuth();
        
        if (currentUser.role === "admin") {
            document.getElementById("nav-admin").classList.remove("hidden");
            loadAdminSubmissions();
        } else {
            document.getElementById("nav-admin").classList.add("hidden");
        }
        
        calculateUserStats();
    } catch (e) {
        console.error("Auth check failed:", e);
    }
}

// Update Header for Auth State
function updateUIForAuth() {
    const section = document.getElementById("header-auth-box");
    if (currentUser) {
        section.innerHTML = `
            <div class="flex items-center space-x-3 bg-dark-200 border border-slate-800/80 px-3 py-1.5 rounded-xl">
                <img src="${currentUser.avatar_url || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + currentUser.username}" class="h-6 w-6 rounded-full border border-slate-750 bg-slate-800">
                <span class="text-xs font-semibold text-slate-300">${currentUser.username}</span>
                <span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-500 font-mono border border-brand-500/20">${currentUser.role}</span>
                <button onclick="openSettingsModal()" class="text-slate-500 hover:text-brand-500 transition ml-2" title="Profile Settings">
                    <i class="fa-solid fa-gear text-[11px]"></i>
                </button>
                <button onclick="handleLogout()" class="text-slate-500 hover:text-red-400 transition" title="Log Out">
                    <i class="fa-solid fa-power-off text-[11px]"></i>
                </button>
            </div>
        `;
        
        // Update user stats username
        const dashUser = document.getElementById("dash-username");
        if (dashUser) dashUser.innerText = currentUser.username;
        const dashAvatar = document.getElementById("dash-avatar-container");
        if (dashAvatar) {
            dashAvatar.innerHTML = `<img src="${currentUser.avatar_url || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + currentUser.username}" class="h-9 w-9 rounded-full bg-slate-800 border border-slate-700">`;
        }
    } else {
        section.innerHTML = `
            <button onclick="showAuthModal()" class="px-4 py-1.5 text-xs font-bold rounded-lg bg-brand-500 hover:bg-brand-600 text-dark-300 shadow-md shadow-brand-500/10 transition active:scale-95">
                <i class="fa-solid fa-arrow-right-to-bracket mr-1.5"></i>Sign In
            </button>
        `;
    }
}

// Modals
function showAuthModal() {
    const modal = document.getElementById("auth-modal");
    modal.classList.remove("hidden");
    setTimeout(() => {
        modal.classList.remove("opacity-0");
        modal.querySelector("div").classList.remove("scale-95");
    }, 50);
}

function hideAuthModal() {
    const modal = document.getElementById("auth-modal");
    modal.classList.add("opacity-0");
    modal.querySelector("div").classList.add("scale-95");
    setTimeout(() => modal.classList.add("hidden"), 300);
}

function switchAuthTab(tab) {
    const loginTab = document.getElementById("auth-tab-login");
    const signupTab = document.getElementById("auth-tab-signup");
    const formLogin = document.getElementById("form-login");
    const formSignup = document.getElementById("form-signup");
    
    if (tab === "login") {
        loginTab.className = "flex-1 pb-2 border-b-2 border-brand-500 text-brand-500";
        signupTab.className = "flex-1 pb-2 border-b-2 border-transparent text-slate-500 hover:text-slate-350";
        formLogin.classList.remove("hidden");
        formSignup.classList.add("hidden");
    } else {
        signupTab.className = "flex-1 pb-2 border-b-2 border-brand-500 text-brand-500";
        loginTab.className = "flex-1 pb-2 border-b-2 border-transparent text-slate-500 hover:text-slate-350";
        formSignup.classList.remove("hidden");
        formLogin.classList.add("hidden");
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const id = document.getElementById("login-id").value;
    const pass = document.getElementById("login-password").value;
    const formData = new FormData();
    formData.append("username", id);
    formData.append("password", pass);
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) throw new Error("Incorrect credentials");
        const data = await response.json();
        currentToken = data.access_token;
        localStorage.setItem("token", currentToken);
        currentUser = data.user;
        updateUIForAuth();
        hideAuthModal();
        if (currentUser.role === "admin") {
            document.getElementById("nav-admin").classList.remove("hidden");
            loadAdminSubmissions();
        } else {
            document.getElementById("nav-admin").classList.add("hidden");
        }
        loadProblems();
        calculateUserStats();
    } catch (err) {
        alert(err.message);
    }
}

async function handleSignupSubmit(e) {
    e.preventDefault();
    const username = document.getElementById("signup-username").value;
    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    
    try {
        const res = await fetch(`${apiBaseUrl}/api/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, username, password })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Signup failed");
        }
        
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);
        const logRes = await fetch(`${apiBaseUrl}/api/auth/login`, {
            method: "POST",
            body: formData
        });
        
        const data = await logRes.json();
        currentToken = data.access_token;
        localStorage.setItem("token", currentToken);
        currentUser = data.user;
        updateUIForAuth();
        hideAuthModal();
        loadProblems();
        calculateUserStats();
    } catch (err) {
        alert(err.message);
    }
}

async function handleGoogleOAuth() {
    const rand = Math.floor(Math.random() * 10000);
    const mockEmail = `dev_oauth_${rand}@submittery.com`;
    const mockToken = `mock_${mockEmail}_OAuthDev_${encodeURIComponent("https://api.dicebear.com/7.x/bottts/svg?seed=" + rand)}`;
    
    try {
        const data = await request("/auth/google", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: mockToken })
        });
        
        currentToken = data.access_token;
        localStorage.setItem("token", currentToken);
        currentUser = data.user;
        updateUIForAuth();
        hideAuthModal();
        if (currentUser.role === "admin") {
            document.getElementById("nav-admin").classList.remove("hidden");
            loadAdminSubmissions();
        } else {
            document.getElementById("nav-admin").classList.add("hidden");
        }
        loadProblems();
        calculateUserStats();
    } catch (err) {
        alert("Google OAuth: " + err.message);
    }
}

function handleLogout() {
    localStorage.removeItem("token");
    currentToken = null;
    currentUser = null;
    problems = [];
    userSubmissions = [];
    currentProblem = null;
    updateUIForAuth();
    document.getElementById("nav-admin").classList.add("hidden");
    navigateTo("home");
    leaveCollaborationRoom();
}

// Load Problems Catalog
async function loadProblems() {
    if (!currentToken) return;
    try {
        problems = await request("/problems/");
        renderProblemsTable();
        populateLobbySelect();
    } catch (e) {
        console.error("Failed to load problems:", e);
    }
}

// User Dashboard Statistics compiler
async function calculateUserStats() {
    if (!currentToken || problems.length === 0) return;
    
    try {
        // Query recent runs across all problems to compile stats
        const submissionsLog = [];
        // Fetch runs for each problem to synthesize user dashboard
        for (let prob of problems) {
            try {
                const subList = await request(`/submissions/problem/${prob.id}`);
                submissionsLog.push(...subList);
            } catch (err) {}
        }
        
        userSubmissions = submissionsLog.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        renderUserDashboardSubmissions();
        
        // Calculate solved count stats
        const solvedProblemIds = new Set();
        userSubmissions.forEach(sub => {
            if (sub.status === "accepted") {
                solvedProblemIds.add(sub.problem_id);
            }
        });
        
        let easySolved = 0;
        let mediumSolved = 0;
        let hardSolved = 0;
        
        problems.forEach(p => {
            if (solvedProblemIds.has(p.id)) {
                if (p.difficulty === "easy") easySolved++;
                if (p.difficulty === "medium") mediumSolved++;
                if (p.difficulty === "hard") hardSolved++;
            }
        });
        
        const totalSolved = solvedProblemIds.size;
        const totalProblems = problems.length;
        const percentage = totalProblems > 0 ? (totalSolved / totalProblems) * 100 : 0;
        
        document.getElementById("solved-stats-count").innerText = `${totalSolved} / ${totalProblems}`;
        document.getElementById("solved-stats-progressbar").style.width = `${percentage}%`;
        document.getElementById("stats-easy-count").innerText = easySolved;
        document.getElementById("stats-medium-count").innerText = mediumSolved;
        document.getElementById("stats-hard-count").innerText = hardSolved;
        
    } catch (e) {
        console.error("Failed to compute stats:", e);
    }
}

function renderUserDashboardSubmissions() {
    const container = document.getElementById("dash-submissions-log");
    if (userSubmissions.length === 0) {
        container.innerHTML = `<div class="text-slate-500 text-center py-10">No recent submissions found.</div>`;
        return;
    }
    
    // Show latest 6 runs
    const recent = userSubmissions.slice(0, 6);
    container.innerHTML = recent.map(sub => {
        const prob = problems.find(p => p.id === sub.problem_id);
        const name = prob ? prob.title : "Algorithm";
        const dateStr = new Date(sub.created_at).toLocaleDateString();
        
        let statusBadge = "text-red-400 bg-red-500/10 border-red-500/20";
        if (sub.status === "accepted") statusBadge = "text-brand-400 bg-brand-500/10 border-brand-500/20";
        if (sub.status === "wrong_answer") statusBadge = "text-amber-500 bg-amber-500/10 border-amber-500/20";
        
        return `
            <div class="glass-card p-3 rounded-lg border-slate-850 flex items-center justify-between">
                <div>
                    <div class="font-bold text-slate-300 truncate max-w-[150px]">${name}</div>
                    <div class="text-xs text-slate-500 font-mono">${dateStr} | ${sub.language}</div>
                </div>
                <div class="text-xs font-bold uppercase tracking-wider px-2 py-0.5 border rounded ${statusBadge}">
                    ${sub.status.replace("_", " ")}
                </div>
            </div>
        `;
    }).join("");
}

// Problems Explorer filters and renders
function filterProblemsDifficulty(diff) {
    filterDifficulty = diff;
    
    // Toggle active filter styles
    const diffs = ["all", "easy", "medium", "hard"];
    diffs.forEach(d => {
        const btn = document.getElementById(`diff-btn-${d}`);
        if (btn) {
            if (d === diff) {
                btn.className = "px-2.5 py-1 rounded text-xs font-bold uppercase bg-brand-500/10 text-brand-500 border border-brand-500/20";
            } else {
                btn.className = "px-2.5 py-1 rounded text-xs font-bold uppercase text-slate-400 hover:text-slate-205 border border-transparent";
            }
        }
    });
    
    renderProblemsTable();
}

function filterProblemsList() {
    renderProblemsTable();
}

const neetcodeTopicTagMap = {
    "arrays-hashing": ["array", "hash-table"],
    "two-pointers": ["two-pointers"],
    "sliding-window": ["sliding-window"],
    "stack": ["stack"],
    "binary-search": ["binary-search"],
    "linked-list": ["linked-list"],
    "trees": ["trees", "tree"],
    "tries": ["trie", "tries"],
    "heap-priority-queue": ["heap", "priority-queue"],
    "backtracking": ["backtracking"],
    "graphs": ["graph", "graphs"],
    "advanced-graphs": ["advanced-graph", "advanced-graphs"],
    "1d-dp": ["dynamic-programming", "1d-dp"],
    "2d-dp": ["2d-dp"],
    "greedy": ["greedy"],
    "intervals": ["intervals", "interval"],
    "math-geometry": ["math", "geometry"],
    "bit-manipulation": ["bit-manipulation"]
};

function renderProblemsTable() {
    const tbody = document.getElementById("problems-tbody-list");
    const query = document.getElementById("prob-search-input").value.trim().toLowerCase();
    
    let filtered = problems;
    
    // Filter by difficulty
    if (filterDifficulty !== "all") {
        filtered = filtered.filter(p => p.difficulty === filterDifficulty);
    }
    
    // Filter by query
    if (query) {
        filtered = filtered.filter(p => p.title.toLowerCase().includes(query));
    }
    
    // Filter by NeetCode Topic
    const topicSelect = document.getElementById("prob-neetcode-topic-select");
    const selectedTopic = topicSelect ? topicSelect.value : "all";
    if (selectedTopic !== "all") {
        const allowedTags = neetcodeTopicTagMap[selectedTopic] || [];
        filtered = filtered.filter(p => {
            const pTags = p.tags || [];
            return pTags.some(t => allowedTags.includes(t.toLowerCase()));
        });
    }
    
    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-slate-500 text-center py-10">No problems found matching filters.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = filtered.map(p => {
        let diffBadge = "text-brand-400 bg-brand-500/10 border-brand-500/20";
        if (p.difficulty === "medium") diffBadge = "text-amber-400 bg-amber-500/10 border border-amber-500/20";
        if (p.difficulty === "hard") diffBadge = "text-rose-400 bg-rose-500/10 border border-rose-500/20";
        
        const tagsHtml = (p.tags || []).map(t => `<span class="text-[11px] bg-slate-800 border border-slate-700/80 px-1.5 py-0.5 rounded text-slate-450 font-semibold">${t}</span>`).join(" ");
        
        const pIndex = problems.findIndex(prob => prob.id === p.id) + 1;
        
        return `
            <tr class="border-b border-slate-850 hover:bg-slate-900/20 transition group">
                <td class="py-3 px-3 font-bold text-slate-200 group-hover:text-brand-400 transition text-sm">#${pIndex}. ${p.title}</td>
                <td class="py-3 px-3">
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 border rounded ${diffBadge}">${p.difficulty}</span>
                </td>
                <td class="py-3 px-3 flex items-center flex-wrap gap-1.5">${tagsHtml}</td>
                <td class="py-3 px-3 text-right">
                    <button onclick="openWorkspace('${p.slug}')" class="px-3.5 py-1 bg-slate-800 hover:bg-brand-500 hover:text-dark-300 text-slate-300 text-sm font-bold rounded-lg transition active:scale-95 border border-slate-700 hover:border-transparent">
                        Solve
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// --- LEETCODE-STYLE RESIZABLE WORKSPACE CONTROLS ---

async function openWorkspace(slug) {
    try {
        currentProblem = await request(`/problems/${slug}`);
        
        const pIndex = problems.findIndex(prob => prob.id === currentProblem.id) + 1;
        
        // Hide top navigation and other views to maximize workspace area
        navigateTo("workspace");
        
        document.getElementById("workspace-problem-label").innerText = ` / #${pIndex}. ${currentProblem.title}`;
        
        // Render Details
        renderWorkspaceProblemDetails(pIndex);
        
        // Set starter template code
        if (editorLoaded && window.editor) {
            window.editor.setValue(currentProblem.starter_code?.python || "");
        }
        
        resetConsoleWorkspace();
        loadSubmissionHistoryWorkspace();
        loadDiscussionWorkspace();
        
        // Reset left pane tab to description
        switchLeftTab("description");
        
        // Trigger resize layout to ensure editor bounds adapt
        setTimeout(() => {
            if (window.editor) window.editor.layout();
        }, 150);
        
    } catch (e) {
        alert("Failed to load problem: " + e.message);
    }
}

function exitWorkspace() {
    navigateTo("dashboard");
    resetConsoleWorkspace();
    leaveCollaborationRoom();
}

function renderWorkspaceProblemDetails(pIndex) {
    const container = document.getElementById("workspace-description-container");
    let diffBadge = "text-brand-400 bg-brand-500/10 border border-brand-500/20";
    if (currentProblem.difficulty === "medium") diffBadge = "text-amber-400 bg-amber-500/10 border border-amber-500/20";
    if (currentProblem.difficulty === "hard") diffBadge = "text-rose-400 bg-rose-500/10 border border-rose-500/20";
    
    const tagsHtml = (currentProblem.tags || []).map(t => `<span class="text-[11px] bg-slate-800 border border-slate-700/80 px-2 py-0.5 rounded text-slate-400 font-semibold">${t}</span>`).join(" ");
    
    const sampleCases = currentProblem.test_cases.filter(tc => tc.is_sample);
    const sampleCasesHtml = sampleCases.map((tc, idx) => `
        <div class="glass-card rounded-xl p-4 space-y-3 font-mono text-xs border-slate-850 select-text">
            <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span class="font-sans font-bold text-slate-400 text-[11px]">Example ${idx + 1}</span>
            </div>
            <div>
                <div class="text-[11px] text-slate-500 mb-0.5">Input:</div>
                <pre class="bg-black/30 p-2 rounded border border-slate-850 text-slate-350 whitespace-pre overflow-x-auto select-all text-xs">${tc.input}</pre>
            </div>
            <div>
                <div class="text-[11px] text-slate-500 mb-0.5">Expected Output:</div>
                <pre class="bg-black/30 p-2 rounded border border-slate-850 text-brand-400 whitespace-pre overflow-x-auto select-all text-xs">${tc.expected_output}</pre>
            </div>
        </div>
    `).join("");

    container.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <h2 class="text-lg font-bold text-slate-100 font-sans">#${pIndex}. ${currentProblem.title}</h2>
                <span class="text-[10px] uppercase font-bold px-2 py-0.5 border rounded ${diffBadge}">${currentProblem.difficulty}</span>
            </div>
            
            <div class="flex flex-wrap gap-1.5">
                ${tagsHtml}
            </div>
            
            <div class="flex items-center space-x-6 text-[10px] text-slate-500 py-2 border-y border-slate-800/50 font-mono">
                <span>Time Limit: <strong class="text-slate-400">${currentProblem.time_limit}s</strong></span>
                <span>Memory Limit: <strong class="text-slate-400">${currentProblem.memory_limit}MB</strong></span>
            </div>
            
            <div class="prose prose-invert text-sm max-w-none text-slate-350 leading-relaxed space-y-3 font-sans select-text">
                ${renderMarkdownAndMath(currentProblem.description)}
            </div>

            <div class="space-y-3 pt-2">
                <h3 class="font-bold text-slate-300 text-xs">Example Cases</h3>
                ${sampleCasesHtml}
            </div>
        </div>
    `;
}

function resetConsoleWorkspace() {
    document.getElementById("wconsole-default-msg").classList.remove("hidden");
    document.getElementById("wjudge-status-block").classList.add("hidden");
    document.getElementById("wjudge-error-block").classList.add("hidden");
    
    // Clear test cases visualizer
    const testcasesContainer = document.getElementById("wconsole-testcases-container");
    if (testcasesContainer) {
        testcasesContainer.innerHTML = "";
        testcasesContainer.classList.add("hidden");
    }
    
    document.getElementById("wbtn-ai-review").disabled = true;
    document.getElementById("wbtn-ai-review").classList.add("text-slate-500");
    document.getElementById("wbtn-ai-hints").disabled = true;
    document.getElementById("wbtn-ai-hints").classList.add("text-slate-500");
    
    lastSubmissionId = null;
    closeWebSocketSub();
}

// LeetCode-style Run code on samples
async function runCode() {
    if (!currentProblem) return;
    switchConsoleTab("result");
    
    document.getElementById("wconsole-default-msg").classList.add("hidden");
    document.getElementById("wjudge-status-block").classList.remove("hidden");
    document.getElementById("wjudge-error-block").classList.add("hidden");
    
    setVerdictLabelWorkspace("RUNNING SAMPLE CASES", "text-brand-400", "fa-solid fa-spinner animate-spin text-brand-400");
    document.getElementById("wverdict-runtime").innerText = "--";
    document.getElementById("wverdict-memory").innerText = "--";
    
    try {
        const results = await request(`/submissions/run/${currentProblem.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: window.editor.getValue(), language: "python" })
        });
        
        let overallVerdict = "ACCEPTED";
        let colorClass = "text-brand-400";
        let iconClass = "fa-solid fa-circle-check text-brand-400";
        let maxRuntime = 0;
        let maxMemory = 0;
        let errMsg = "";
        
        for (let res of results) {
            maxRuntime = Math.max(maxRuntime, res.runtime || 0);
            maxMemory = Math.max(maxMemory, res.memory || 0);
            
            if (res.status !== "accepted" && overallVerdict === "ACCEPTED") {
                overallVerdict = res.status.toUpperCase().replace("_", " ");
                colorClass = "text-amber-500";
                iconClass = "fa-solid fa-circle-xmark text-amber-500";
                errMsg = res.error || "Execution failed";
            }
        }
        
        const totalCases = results.length;
        const passedCases = results.filter(r => r.status === "accepted").length;
        let label = overallVerdict;
        if (totalCases > 0) {
            label += ` (${passedCases}/${totalCases} Cases Passed)`;
        }
        
        setVerdictLabelWorkspace(label, colorClass, iconClass);
        document.getElementById("wverdict-id").innerText = "Sample Run";
        document.getElementById("wverdict-runtime").innerText = `${maxRuntime.toFixed(3)}s`;
        document.getElementById("wverdict-memory").innerText = `${(maxMemory / 1024).toFixed(1)}MB`;
        
        if (errMsg) {
            document.getElementById("wjudge-error-block").classList.remove("hidden");
            document.getElementById("wjudge-error-text").innerText = errMsg;
        }
        
        // Render LeetCode-style test cases list
        renderTestcasesOutput(results);
    } catch (e) {
        setVerdictLabelWorkspace("RUN ERROR", "text-red-500", "fa-solid fa-circle-exclamation text-red-500");
        document.getElementById("wjudge-error-block").classList.remove("hidden");
        document.getElementById("wjudge-error-text").innerText = e.message;
    }
}

// LeetCode-style Submit code permanently
async function submitCode() {
    if (!currentProblem) return;
    switchConsoleTab("result");
    
    document.getElementById("wconsole-default-msg").classList.add("hidden");
    document.getElementById("wjudge-status-block").classList.remove("hidden");
    document.getElementById("wjudge-error-block").classList.add("hidden");
    
    setVerdictLabelWorkspace("QUEUED", "text-slate-450", "fa-solid fa-spinner animate-spin text-slate-450");
    document.getElementById("wverdict-runtime").innerText = "--";
    document.getElementById("wverdict-memory").innerText = "--";
    
    try {
        const sub = await request(`/submissions/submit/${currentProblem.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: window.editor.getValue(), language: "python" })
        });
        
        lastSubmissionId = sub.id;
        document.getElementById("wverdict-id").innerText = sub.id.substring(0, 8);
        
        listenForSubmissionUpdatesWorkspace(sub.id);
    } catch (e) {
        setVerdictLabelWorkspace("SUBMIT ERROR", "text-red-500", "fa-solid fa-circle-exclamation text-red-500");
        document.getElementById("wjudge-error-block").classList.remove("hidden");
        document.getElementById("wjudge-error-text").innerText = e.message;
    }
}

function setVerdictLabelWorkspace(text, colorClass, iconClass) {
    const label = document.getElementById("wverdict-label");
    const iconContainer = document.getElementById("wverdict-icon");
    
    label.innerText = text;
    label.className = `font-bold text-xs uppercase tracking-wider ${colorClass}`;
    
    iconContainer.innerHTML = `<i class="${iconClass}"></i>`;
    iconContainer.className = `h-9 w-9 rounded-lg flex items-center justify-center text-sm ${colorClass} bg-dark-300 border border-slate-800/40`;
}

function closeWebSocketSub() {
    if (wsSub) {
        wsSub.close();
        wsSub = null;
    }
}

function listenForSubmissionUpdatesWorkspace(submissionId) {
    closeWebSocketSub();
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws/submissions/${submissionId}`;
    
    wsSub = new WebSocket(wsUrl);
    
    wsSub.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const status = data.status;
        
        if (status === "queued") {
            setVerdictLabelWorkspace("QUEUED", "text-slate-450", "fa-solid fa-spinner animate-spin text-slate-455");
        } else if (status === "running") {
            setVerdictLabelWorkspace("RUNNING SUITE", "text-brand-400", "fa-solid fa-spinner animate-spin text-brand-400");
        } else {
            // Completed
            displayFinalVerdictWorkspace(data);
            closeWebSocketSub();
            // Refresh tables and stats
            loadSubmissionHistoryWorkspace();
            calculateUserStats();
        }
    };
}

function displayFinalVerdictWorkspace(data) {
    const status = data.status;
    const runtime = data.runtime;
    const memory = data.memory;
    const error = data.error_message;
    
    document.getElementById("wbtn-ai-review").disabled = false;
    document.getElementById("wbtn-ai-review").classList.remove("text-slate-500");
    
    let colorClass = "text-red-400";
    let iconClass = "fa-solid fa-circle-xmark text-red-400";
    
    const totalCases = data.results ? data.results.length : 0;
    const passedCases = data.results ? data.results.filter(r => r.status === "accepted").length : 0;
    let label = status.toUpperCase().replace("_", " ");
    if (totalCases > 0) {
        label += ` (${passedCases}/${totalCases} Cases Passed)`;
    }
    
    if (status === "accepted") {
        colorClass = "text-brand-400";
        iconClass = "fa-solid fa-circle-check text-brand-400";
        setVerdictLabelWorkspace(label, colorClass, iconClass);
        document.getElementById("wverdict-runtime").innerText = `${runtime}s`;
        document.getElementById("wverdict-memory").innerText = `${(memory / 1024).toFixed(1)}MB`;
    } else {
        document.getElementById("wbtn-ai-hints").disabled = false;
        document.getElementById("wbtn-ai-hints").classList.remove("text-slate-500");
        
        if (status === "wrong_answer") {
            colorClass = "text-amber-500";
            iconClass = "fa-solid fa-circle-xmark text-amber-500";
        }
        
        setVerdictLabelWorkspace(label, colorClass, iconClass);
        document.getElementById("wverdict-runtime").innerText = runtime ? `${runtime}s` : "--";
        document.getElementById("wverdict-memory").innerText = memory ? `${(memory / 1024).toFixed(1)}MB` : "--";
        
        if (error) {
            document.getElementById("wjudge-error-block").classList.remove("hidden");
            document.getElementById("wjudge-error-text").innerText = error;
        }
    }
    
    // Render LeetCode-style test cases list
    renderTestcasesOutput(data.results);
}

// Load Workspace Submission History logs
async function loadSubmissionHistoryWorkspace() {
    if (!currentProblem) return;
    const container = document.getElementById("whistory-list");
    container.innerHTML = `<div class="text-slate-500 text-xs py-4 text-center">Loading logs...</div>`;
    
    try {
        const list = await request(`/submissions/problem/${currentProblem.id}`);
        if (list.length === 0) {
            container.innerHTML = `<div class="text-slate-500 text-xs py-6 text-center">No submissions yet for this problem.</div>`;
            return;
        }
        
        window.historicalSubmissions = list;
        
        container.innerHTML = list.map(sub => {
            let statusColor = "text-red-400";
            if (sub.status === "accepted") statusColor = "text-brand-400";
            if (sub.status === "wrong_answer") statusColor = "text-amber-500";
            
            const timeStr = new Date(sub.created_at).toLocaleString();
            
            return `
                <div onclick="loadHistoricalCode('${sub.id}')" class="glass-card p-3 rounded-lg flex items-center justify-between cursor-pointer border-slate-850 hover:border-brand-500/30 transition">
                    <div class="flex items-center space-x-3">
                        <i class="fa-solid fa-code text-slate-600"></i>
                        <div>
                            <div class="text-xs font-bold ${statusColor} uppercase">${sub.status.replace("_", " ")}</div>
                            <div class="text-[9px] text-slate-500">${timeStr}</div>
                        </div>
                    </div>
                    <div class="text-right text-[10px] space-y-0.5 font-mono">
                        <div class="text-slate-300">${sub.runtime ? sub.runtime + 's' : '--'}</div>
                        <div class="text-slate-500">${sub.memory ? (sub.memory / 1024).toFixed(1) + 'MB' : '--'}</div>
                    </div>
                </div>
            `;
        }).join("");
    } catch (e) {
        container.innerHTML = `<div class="text-red-400 text-xs text-center py-4">Error loading history: ${e.message}</div>`;
    }
}

// Workspace Console Tab switcher
function switchConsoleTab(tab) {
    activeConsoleTab = tab;
    const tabs = ["result", "ai", "discussions"];
    
    tabs.forEach(t => {
        const btn = document.getElementById(`wconsole-tab-${t}`);
        const content = document.getElementById(`wconsole-content-${t}`);
        if (!btn || !content) return;
        
        if (t === tab) {
            btn.className = "px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider border-b-2 border-brand-500 text-brand-500 transition";
            content.classList.remove("hidden");
        } else {
            btn.className = "px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition";
            content.classList.add("hidden");
        }
    });
}

// AI panel integration workspace
async function triggerAIAction(action) {
    if (!currentProblem) return;
    const responseBox = document.getElementById("wai-response-box");
    switchConsoleTab("ai");
    
    responseBox.innerHTML = `
        <div class="flex items-center justify-center py-10 text-brand-400 text-xs">
            <i class="fa-solid fa-spinner animate-spin text-sm mr-2"></i>
            <span>AI Mentor is compiling answer...</span>
        </div>
    `;
    
    try {
        let endpoint = "";
        let body = {};
        
        if (action === "complexity") {
            endpoint = "/ai/analyze-complexity";
            body = {
                code: window.editor.getValue(),
                problem_id: currentProblem.id
            };
        } else if (action === "review") {
            if (!lastSubmissionId) return;
            endpoint = `/ai/code-review/${lastSubmissionId}`;
        } else if (action === "hints") {
            if (!lastSubmissionId) return;
            endpoint = `/ai/debug-hints/${lastSubmissionId}`;
        } else if (action === "ask") {
            const input = document.getElementById("wai-chat-input");
            const question = input.value.trim();
            if (!question) return;
            
            endpoint = "/ai/ask";
            body = {
                question: question,
                problem_id: currentProblem.id
            };
            input.value = "";
        }
        
        const data = await request(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: Object.keys(body).length ? JSON.stringify(body) : null
        });
        
        responseBox.innerHTML = `<div class="prose prose-invert text-sm max-w-none space-y-2 leading-relaxed font-sans select-text">${marked.parse(data.response)}</div>`;
        
        setTimeout(formatMathFormulas, 100);
        
    } catch (e) {
        responseBox.innerHTML = `<div class="text-red-400 text-xs py-4"><i class="fa-solid fa-circle-exclamation mr-2"></i>AI Error: ${e.message}</div>`;
    }
}

// Discussions workspace
async function loadDiscussionWorkspace() {
    const container = document.getElementById("wdiscussions-container");
    container.innerHTML = `<div class="text-slate-500 text-xs py-4 text-center">Loading comments...</div>`;
    
    try {
        const comments = await request(`/discussion/problem/${currentProblem.id}`);
        if (comments.length === 0) {
            container.innerHTML = `<div class="text-slate-500 text-xs py-6 text-center">No comments posted yet.</div>`;
            return;
        }
        
        container.innerHTML = comments.map(c => `
            <div class="glass-card p-3 rounded-lg border-slate-850 space-y-1 text-xs">
                <div class="flex items-center justify-between text-[10px]">
                    <div class="flex items-center space-x-2">
                        <img src="${c.user.avatar_url || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + c.user.username}" class="h-5 w-5 rounded-full bg-slate-800 border border-slate-700">
                        <span class="font-bold text-slate-300">${c.user.username}</span>
                    </div>
                    <span class="text-slate-500 font-mono">${new Date(c.created_at).toLocaleDateString()}</span>
                </div>
                <p class="text-slate-400 pl-7 whitespace-pre-wrap select-text">${c.content}</p>
            </div>
        `).join("");
    } catch (e) {
        container.innerHTML = `<div class="text-red-400 text-xs py-4 text-center">Failed to load: ${e.message}</div>`;
    }
}

async function postComment() {
    const input = document.getElementById("wcomment-input");
    const content = input.value.trim();
    if (!content) return;
    
    try {
        await request(`/discussion/problem/${currentProblem.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content })
        });
        
        input.value = "";
        loadDiscussionWorkspace();
    } catch (e) {
        alert("Comment failed: " + e.message);
    }
}

// --- COLLABORATION LOBBY ENDPOINTS ---

function populateLobbySelect() {
    const select = document.getElementById("lobby-collab-problem-select");
    if (!select) return;
    select.innerHTML = problems.map(p => `
        <option value="${p.slug}">${p.title} (${p.difficulty.toUpperCase()})</option>
    `).join("");
}

function createCollaborationRoom() {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let code = "";
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    const select = document.getElementById("lobby-collab-problem-select");
    const problemSlug = select.value;
    
    connectCollabWS(code, true, problemSlug);
}

function joinCollaborationRoom(code = null) {
    if (!code) {
        code = document.getElementById("lobby-join-code-input").value.trim().toUpperCase();
    }
    
    if (!code || code.length < 4) {
        alert("Please input a valid room code!");
        return;
    }
    
    connectCollabWS(code, false);
}

function connectCollabWS(roomCode, isCreator, problemSlug = null) {
    leaveCollaborationRoom();
    
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws/collaboration/${roomCode}`;
    
    wsCollab = new WebSocket(wsUrl);
    isCollaborating = true;
    currentRoomCode = roomCode;
    
    wsCollab.onopen = () => {
        document.getElementById("lobby-room-code-display").innerText = roomCode;
        document.getElementById("lobby-active-room-card").classList.remove("hidden");
        document.getElementById("ws-collab-active-indicator").classList.remove("hidden");
        
        if (isCreator && problemSlug) {
            openWorkspace(problemSlug);
            setTimeout(() => {
                if (wsCollab && wsCollab.readyState === WebSocket.OPEN) {
                    wsCollab.send(JSON.stringify({
                        type: "sync-problem",
                        slug: problemSlug
                    }));
                }
            }, 1200);
        } else {
            // Wait for creator to sync the problem
            console.log("Connected to room. Waiting for host to broadcast problem context...");
        }
    };
    
    wsCollab.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === "sync-problem") {
                if (!currentProblem || currentProblem.slug !== data.slug) {
                    openWorkspace(data.slug);
                }
            } else if (data.type === "sync-code" && window.editor) {
                const currentVal = window.editor.getValue();
                if (data.code !== currentVal) {
                    const state = window.editor.saveViewState();
                    window.editor.setValue(data.code);
                    if (state) window.editor.restoreViewState(state);
                }
            }
        } catch (e) {
            console.error("Collab sync parse error:", e);
        }
    };
    
    wsCollab.onclose = () => {
        console.log("Collab connection offline");
        if (isCollaborating) {
            leaveCollaborationRoom();
        }
    };
}

function leaveCollaborationRoom() {
    isCollaborating = false;
    currentRoomCode = null;
    if (wsCollab) {
        wsCollab.close();
        wsCollab = null;
    }
    
    document.getElementById("lobby-active-room-card").classList.add("hidden");
    document.getElementById("ws-collab-active-indicator").classList.add("hidden");
}

function copyRoomCode() {
    if (!currentRoomCode) return;
    navigator.clipboard.writeText(currentRoomCode);
    alert("Room code copied: " + currentRoomCode);
}

function copyInviteLink() {
    if (!currentRoomCode) return;
    const shareLink = `${window.location.origin}/?room=${currentRoomCode}`;
    navigator.clipboard.writeText(shareLink);
    alert("Invite URL link copied to clipboard!");
}

// --- ADMIN PANELS ---

async function loadAdminSubmissions() {
    const tbody = document.getElementById("admin-submissions-tbody-log");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="6" class="text-slate-550 text-center py-6">Loading submissions queue...</td></tr>`;
    
    try {
        const subs = await request("/submissions/");
        
        // Update stats summary cards
        document.getElementById("admin-stat-submissions").innerText = subs.length;
        document.getElementById("admin-stat-problems").innerText = problems.length;
        
        if (subs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-slate-500 text-center py-6">No historical runs logged yet.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = subs.map(s => {
            let color = "text-red-400";
            if (s.status === "accepted") color = "text-brand-400";
            if (s.status === "wrong_answer") color = "text-amber-500";
            
            const timeStr = new Date(s.created_at).toLocaleString();
            
            return `
                <tr class="border-b border-slate-850 hover:bg-slate-900/10">
                    <td class="py-2.5 px-3 font-mono font-bold text-slate-350">${s.id.substring(0,8)}</td>
                    <td class="py-2.5 px-3 font-mono text-slate-500">${s.user_id.substring(0,6)}</td>
                    <td class="py-2.5 px-3 font-mono text-slate-500">${s.problem_id.substring(0,6)}</td>
                    <td class="py-2.5 px-3 text-slate-400 font-semibold">${s.language}</td>
                    <td class="py-2.5 px-3 font-bold uppercase tracking-wider ${color}">${s.status.replace("_", " ")}</td>
                    <td class="py-2.5 px-3 text-slate-500 text-right font-mono">${timeStr}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Admin dashboard query failure:", e);
    }
}

// Problem creation helpers
function openCreateProblemModal() {
    const modal = document.getElementById("create-problem-modal");
    modal.classList.remove("hidden");
    setTimeout(() => {
        modal.classList.remove("opacity-0");
        modal.querySelector("div").classList.remove("scale-95");
    }, 50);
}

function hideCreateProblemModal() {
    const modal = document.getElementById("create-problem-modal");
    modal.classList.add("opacity-0");
    modal.querySelector("div").classList.add("scale-95");
    setTimeout(() => modal.classList.add("hidden"), 300);
}

function addTestCaseRow() {
    const container = document.getElementById("testcase-rows-container");
    const div = document.createElement("div");
    div.className = "testcase-row glass-card p-3 rounded-lg border border-slate-800/80 grid grid-cols-12 gap-2 items-center";
    div.innerHTML = `
        <div class="col-span-5">
            <textarea placeholder="Input..." required class="tc-input w-full px-2 py-1 bg-dark-300 border border-slate-800 rounded text-slate-200 font-mono text-[10px]" rows="1"></textarea>
        </div>
        <div class="col-span-5">
            <textarea placeholder="Expected Output..." required class="tc-output w-full px-2 py-1 bg-dark-300 border border-slate-800 rounded text-slate-200 font-mono text-[10px]" rows="1"></textarea>
        </div>
        <div class="col-span-2 text-center flex flex-col items-center">
            <span class="text-[9px] text-slate-500 font-bold mb-0.5">Sample</span>
            <input type="checkbox" class="tc-sample h-4 w-4 text-brand-500 bg-dark-300 rounded border-slate-800 focus:ring-brand-500">
        </div>
    `;
    container.appendChild(div);
}

async function handleCreateProblemSubmit(e) {
    e.preventDefault();
    
    const title = document.getElementById("prob-title").value.trim();
    const difficulty = document.getElementById("prob-difficulty").value;
    const description = document.getElementById("prob-description").value.trim();
    const timeLimit = parseFloat(document.getElementById("prob-timelimit").value);
    const memoryLimit = parseInt(document.getElementById("prob-memlimit").value);
    const tags = document.getElementById("prob-tags").value.split(",").map(t => t.trim()).filter(t => t);
    const starterCode = document.getElementById("prob-starter").value;
    
    // Parse test cases
    const rows = document.querySelectorAll(".testcase-row");
    const testCases = [];
    rows.forEach(r => {
        const input = r.querySelector(".tc-input").value;
        const expectedOutput = r.querySelector(".tc-output").value;
        const isSample = r.querySelector(".tc-sample").checked;
        
        testCases.push({
            input,
            expected_output: expectedOutput,
            is_sample: isSample
        });
    });
    
    const payload = {
        title,
        description,
        difficulty,
        time_limit: timeLimit,
        memory_limit: memoryLimit,
        tags,
        starter_code: { python: starterCode },
        is_public: true,
        test_cases: testCases
    };
    
    try {
        await request("/problems/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        alert("Problem successfully created!");
        hideCreateProblemModal();
        loadProblems();
    } catch (err) {
        alert("Failed to create problem: " + err.message);
    }
}

// -------------------------------------------------------------
// ADVANCED RENDERERS: MATH & LEETCODE TEST CASES VISUALIZER
// -------------------------------------------------------------

function renderMarkdownAndMath(text) {
    if (!text) return "";
    
    const mathBlocks = [];
    let placeholderIndex = 0;
    
    // Extract display math ($$...$$) first to prevent marked corruption
    text = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, math) => {
        const placeholder = `MATHBLOCKDISPLAYXYZ${placeholderIndex}`;
        mathBlocks.push({ placeholder, math: math, display: true });
        placeholderIndex++;
        return placeholder;
    });
    
    // Extract inline math ($...$)
    text = text.replace(/\$([\s\S]+?)\$/g, (match, math) => {
        const placeholder = `MATHBLOCKINLINEXYZ${placeholderIndex}`;
        mathBlocks.push({ placeholder, math: math, display: false });
        placeholderIndex++;
        return placeholder;
    });
    
    // Parse Markdown
    let html = marked.parse(text);
    
    // Render KaTeX and replace placeholders
    mathBlocks.forEach(block => {
        try {
            const mathHtml = katex.renderToString(block.math, {
                displayMode: block.display,
                throwOnError: false
            });
            html = html.replace(block.placeholder, mathHtml);
        } catch (err) {
            console.error("KaTeX error:", err);
            html = html.replace(block.placeholder, block.math);
        }
    });
    
    return html;
}

function renderTestcasesOutput(results) {
    const container = document.getElementById("wconsole-testcases-container");
    if (!container) return;
    container.innerHTML = "";
    container.classList.remove("hidden");
    
    if (!results || results.length === 0) {
        container.classList.add("hidden");
        return;
    }
    
    // Create horizontal tab buttons container
    const tabsRow = document.createElement("div");
    tabsRow.className = "flex space-x-1.5 overflow-x-auto pb-1 border-b border-slate-800/80 shrink-0";
    
    // Details display panel
    const detailsBox = document.createElement("div");
    detailsBox.className = "space-y-3 pt-2 text-xs flex-grow select-text";
    
    function selectCaseTab(idx) {
        // Update selection styling on all tabs
        const tabButtons = tabsRow.querySelectorAll("button");
        tabButtons.forEach((btn, i) => {
            const res = results[i];
            const isPassed = res.status === "accepted";
            if (i === idx) {
                btn.className = `px-3 py-1.5 rounded-lg font-bold uppercase tracking-wider text-[10px] bg-dark-200 border border-brand-500 text-brand-500`;
            } else {
                const statusColor = isPassed ? "text-brand-500 bg-brand-500/5 hover:bg-brand-500/10" : "text-red-400 bg-red-500/5 hover:bg-red-500/10";
                btn.className = `px-3 py-1.5 rounded-lg font-semibold uppercase tracking-wider text-[10px] ${statusColor} border border-transparent transition`;
            }
        });
        
        // Update details view
        const res = results[idx];
        const isPassed = res.status === "accepted";
        const statusBadgeColor = isPassed ? "text-brand-500 bg-brand-500/10 border-brand-500/20" : "text-red-400 bg-red-500/10 border-red-500/20";
        
        // Fetch local input/output match
        const matchedCase = (currentProblem?.test_cases || []).find(tc => tc.id === res.id);
        const inputVal = matchedCase ? matchedCase.input : "[Hidden Test Case]";
        const expectedVal = matchedCase ? matchedCase.expected_output : "[Hidden Test Case]";
        
        let outputSection = "";
        if (res.status === "accepted") {
            outputSection = `
                <div>
                    <div class="text-[10px] text-slate-500 mb-0.5 font-bold uppercase">Stdout Output:</div>
                    <pre class="bg-black/40 p-2.5 rounded border border-slate-850 text-brand-400 font-mono whitespace-pre overflow-x-auto select-all">${expectedVal}</pre>
                </div>
            `;
        } else if (res.status === "wrong_answer") {
            outputSection = `
                <div>
                    <div class="text-[10px] text-slate-500 mb-0.5 font-bold uppercase">Your Output:</div>
                    <pre class="bg-black/40 p-2.5 rounded border border-red-500/10 text-red-400 font-mono whitespace-pre overflow-x-auto select-all">${res.error || "Wrong Answer"}</pre>
                </div>
            `;
        } else {
            outputSection = `
                <div>
                    <div class="text-[10px] text-slate-500 mb-0.5 font-bold uppercase">Traceback Error:</div>
                    <pre class="bg-black/40 p-2.5 rounded border border-red-500/10 text-red-400 font-mono whitespace-pre-wrap overflow-x-auto select-all">${res.error || "Execution Error"}</pre>
                </div>
            `;
        }
        
        detailsBox.innerHTML = `
            <div class="flex items-center justify-between glass-card p-3 rounded-lg border-slate-800">
                <div class="flex items-center space-x-2">
                    <span class="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 border rounded ${statusBadgeColor}">${res.status.replace("_", " ")}</span>
                </div>
                <div class="flex space-x-4 text-[10px] font-mono">
                    <div><span class="text-slate-500">Runtime:</span> <strong class="text-slate-200">${res.runtime ? res.runtime.toFixed(3) + 's' : '--'}</strong></div>
                    <div class="border-l border-slate-800 pl-3"><span class="text-slate-500">Memory:</span> <strong class="text-slate-200">${res.memory ? (res.memory / 1024).toFixed(1) + 'MB' : '--'}</strong></div>
                </div>
            </div>
            
            <div class="space-y-3">
                <div>
                    <div class="text-[10px] text-slate-500 mb-0.5 font-bold uppercase">Input:</div>
                    <pre class="bg-black/40 p-2.5 rounded border border-slate-850 text-slate-350 font-mono whitespace-pre overflow-x-auto select-all">${inputVal}</pre>
                </div>
                <div>
                    <div class="text-[10px] text-slate-500 mb-0.5 font-bold uppercase">Expected Output:</div>
                    <pre class="bg-black/40 p-2.5 rounded border border-slate-850 text-brand-400 font-mono whitespace-pre overflow-x-auto select-all">${expectedVal}</pre>
                </div>
                ${outputSection}
            </div>
        `;
    }
    
    // Generate horizontal case buttons
    results.forEach((res, i) => {
        const btn = document.createElement("button");
        const isPassed = res.status === "accepted";
        const iconClass = isPassed ? "fa-solid fa-circle-check text-brand-500 mr-1" : "fa-solid fa-circle-xmark text-red-500 mr-1";
        btn.innerHTML = `<i class="${iconClass}"></i>Case ${i + 1}`;
        
        btn.addEventListener("click", () => selectCaseTab(i));
        tabsRow.appendChild(btn);
    });
    
    container.appendChild(tabsRow);
    container.appendChild(detailsBox);
    
    // Focus first test case by default
    selectCaseTab(0);
}

function switchLeftTab(tab) {
    activeLeftTab = tab;
    const tabs = ["description", "history", "explain"];
    
    tabs.forEach(t => {
        const btn = document.getElementById(`wleft-tab-${t}`);
        const content = document.getElementById(`wleft-content-${t}`);
        if (!btn || !content) return;
        
        if (t === tab) {
            btn.className = "px-3 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b-2 border-brand-500 text-brand-500 transition";
            content.classList.remove("hidden");
        } else {
            btn.className = "px-3 py-1.5 text-[9px] font-bold uppercase tracking-wider border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition";
            content.classList.add("hidden");
        }
    });
    
    if (tab === "explain") {
        loadQuestionExplanation();
    }
}

function loadHistoricalCode(subId) {
    if (!window.historicalSubmissions) return;
    const sub = window.historicalSubmissions.find(s => s.id === subId);
    if (sub && window.editor) {
        window.editor.setValue(sub.code);
        alert("Loaded submission code into the editor workspace.");
    }
}

async function loadQuestionExplanation() {
    if (!currentProblem) return;
    const container = document.getElementById("wleft-content-explain");
    if (!container) return;
    
    container.innerHTML = `
        <div class="flex items-center justify-center py-20 text-brand-400 text-xs">
            <i class="fa-solid fa-spinner animate-spin text-sm mr-2"></i>
            <span>AI Mentor is explaining the problem...</span>
        </div>
    `;
    
    try {
        const data = await request("/ai/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: "Please explain this problem statement, constraints, example inputs/outputs, and outline the core algorithmic approach to solve it in simple terms.",
                problem_id: currentProblem.id
            })
        });
        
        container.innerHTML = `
            <div class="space-y-4 select-text">
                <h4 class="text-[10px] font-bold text-brand-500 uppercase tracking-widest font-mono"><i class="fa-solid fa-wand-magic-sparkles mr-1.5"></i>AI Explanation</h4>
                <div class="prose prose-invert text-sm max-w-none space-y-3 leading-relaxed font-sans select-text">
                    ${renderMarkdownAndMath(data.response)}
                </div>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `
            <div class="text-red-400 text-xs py-4">
                <i class="fa-solid fa-circle-exclamation mr-2"></i>AI Error: ${e.message}
            </div>
        `;
    }
}

function toggleTheme() {
    const body = document.body;
    const currentTheme = body.classList.contains("light-mode") ? "dark" : "light";
    
    if (currentTheme === "light") {
        body.classList.add("light-mode");
        localStorage.setItem("theme", "light");
        if (window.editor) monaco.editor.setTheme("vs");
        // Update toggle icon to moon
        const toggleIcon = document.getElementById("theme-toggle-icon");
        if (toggleIcon) toggleIcon.className = "fa-solid fa-moon text-xs";
    } else {
        body.classList.remove("light-mode");
        localStorage.setItem("theme", "dark");
        if (window.editor) monaco.editor.setTheme("vs-dark");
        // Update toggle icon to sun
        const toggleIcon = document.getElementById("theme-toggle-icon");
        if (toggleIcon) toggleIcon.className = "fa-solid fa-sun text-xs";
    }
}

function openSettingsModal() {
    if (!currentUser) return;
    const modal = document.getElementById("profile-settings-modal");
    
    document.getElementById("settings-username").value = currentUser.username;
    document.getElementById("settings-email").value = currentUser.email;
    
    let seed = currentUser.username;
    if (currentUser.avatar_url && currentUser.avatar_url.includes("seed=")) {
        const parts = currentUser.avatar_url.split("seed=");
        if (parts.length > 1) {
            seed = decodeURIComponent(parts[1]);
        }
    }
    document.getElementById("settings-avatar-seed").value = seed;
    document.getElementById("settings-password").value = "";
    previewSettingsAvatar();
    
    modal.classList.remove("hidden");
    setTimeout(() => {
        modal.classList.remove("opacity-0");
        modal.querySelector("div").classList.remove("scale-95");
    }, 50);
}

function hideSettingsModal() {
    const modal = document.getElementById("profile-settings-modal");
    modal.classList.add("opacity-0");
    modal.querySelector("div").classList.add("scale-95");
    setTimeout(() => modal.classList.add("hidden"), 300);
}

function previewSettingsAvatar() {
    const seed = document.getElementById("settings-avatar-seed").value.trim() || "submitter";
    const previewContainer = document.getElementById("settings-avatar-preview-container");
    const avatarUrl = `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(seed)}`;
    previewContainer.innerHTML = `<img src="${avatarUrl}" class="h-full w-full rounded-xl">`;
}

async function handleProfileSettingsSubmit(e) {
    e.preventDefault();
    const username = document.getElementById("settings-username").value.trim();
    const email = document.getElementById("settings-email").value.trim();
    const seed = document.getElementById("settings-avatar-seed").value.trim();
    const password = document.getElementById("settings-password").value;
    
    const avatarUrl = `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(seed)}`;
    
    const body = {
        username,
        email,
        avatar_url: avatarUrl
    };
    if (password) {
        body.password = password;
    }
    
    try {
        currentUser = await request("/auth/profile", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        
        updateUIForAuth();
        hideSettingsModal();
    } catch (err) {
        alert("Failed to update profile: " + err.message);
    }
}



