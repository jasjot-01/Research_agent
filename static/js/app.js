/* ================================================================
   AI Research Agent – Frontend JavaScript
   Chat · Literature · Summarizer · Citations · Draft · Ideas · Projects
================================================================ */

"use strict";

// ── Session ID ──────────────────────────────────────────────
const SESSION_ID = "sess_" + Math.random().toString(36).slice(2, 11);

// ── DOM refs ────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const chatMessages    = $("chatMessages");
const chatInput       = $("chatInput");
const sendBtn         = $("sendBtn");
const charCounter     = $("charCounter");
const clearHistoryBtn = $("clearHistoryBtn");
const loadingOverlay  = $("loadingOverlay");
const loadingText     = $("loadingText");
const statusDot       = $("statusDot");
const themeToggle     = $("themeToggle");
const themeIcon       = $("themeIcon");
const topbarTitle     = $("topbarTitle");
const sidebarEl       = $("sidebar");
const sidebarOpen     = $("sidebarOpen");
const sidebarClose    = $("sidebarClose");

// ── Theme ───────────────────────────────────────────────────
let darkMode = localStorage.getItem("theme") !== null ? localStorage.getItem("theme") === "dark" : true;
applyTheme();

function applyTheme() {
  document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
  themeIcon.className = darkMode ? "bi bi-sun-fill" : "bi bi-moon-fill";
}

themeToggle.addEventListener("click", () => {
  darkMode = !darkMode;
  localStorage.setItem("theme", darkMode ? "dark" : "light");
  applyTheme();
});

// ── Sidebar mobile toggle ────────────────────────────────────
let overlay = null;

function openSidebar() {
  sidebarEl.classList.add("open");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "sidebar-overlay";
    document.body.appendChild(overlay);
    overlay.addEventListener("click", closeSidebar);
  }
  overlay.classList.add("visible");
}

function closeSidebar() {
  sidebarEl.classList.remove("open");
  if (overlay) overlay.classList.remove("visible");
}

sidebarOpen?.addEventListener("click", openSidebar);
sidebarClose?.addEventListener("click", closeSidebar);

// ── Tab Navigation ──────────────────────────────────────────
const tabTitles = {
  chat:       '<i class="bi bi-chat-dots-fill me-2"></i>Research Chat',
  literature: '<i class="bi bi-journals me-2"></i>Literature Search',
  summarize:  '<i class="bi bi-file-text-fill me-2"></i>Paper Summarizer',
  citations:  '<i class="bi bi-bookmark-star-fill me-2"></i>Citations',
  draft:      '<i class="bi bi-pencil-square me-2"></i>Draft Section',
  ideas:      '<i class="bi bi-lightbulb-fill me-2"></i>Research Ideas',
  projects:   '<i class="bi bi-folder2-open me-2"></i>Projects',
};

document.querySelectorAll(".nav-item").forEach((navItem) => {
  navItem.addEventListener("click", (e) => {
    e.preventDefault();
    const tab = navItem.dataset.tab;

    // Update nav active
    document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
    navItem.classList.add("active");

    // Switch pane
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
    const pane = $("tab-" + tab);
    if (pane) pane.classList.add("active");

    // Update topbar title
    topbarTitle.innerHTML = tabTitles[tab] || tab;

    // Lazy-load data for certain tabs
    if (tab === "citations") loadCitations();
    if (tab === "projects") loadProjects();

    // Close sidebar on mobile
    closeSidebar();
  });
});

// ── Utility: API fetch ───────────────────────────────────────
async function apiFetch(url, body = null) {
  const opts = {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify({ ...body, session_id: SESSION_ID });
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

// ── Utility: show/hide loading ───────────────────────────────
function showLoading(msg = "Thinking…") {
  loadingText.textContent = msg;
  loadingOverlay.classList.add("visible");
  statusDot.className = "status-dot loading";
}

function hideLoading() {
  loadingOverlay.classList.remove("visible");
  statusDot.className = "status-dot";
}

// ── Utility: toast ───────────────────────────────────────────
function showToast(msg, type = "info") {
  const toastEl  = $("appToast");
  const toastBody = $("toastBody");
  toastBody.textContent = msg;
  toastEl.className = "toast align-items-center border-0 text-bg-"
    + (type === "error" ? "danger" : type === "success" ? "success" : "dark");
  const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3200 });
  toast.show();
}

// ── Utility: copy text ──────────────────────────────────────
function copyToClipboard(text, btn = null) {
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!", "success");
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-check2"></i> Copied';
      setTimeout(() => (btn.innerHTML = orig), 2000);
    }
  });
}

// ── Utility: render markdown ─────────────────────────────────
function renderMd(text) {
  try {
    return marked.parse(text || "");
  } catch {
    return text || "";
  }
}

// ── Utility: result box ──────────────────────────────────────
function showResult(boxEl, htmlContent) {
  boxEl.innerHTML =
    `<button class="copy-result-btn" onclick="copyToClipboard(this.closest('.result-box').innerText, this)">
       <i class="bi bi-clipboard"></i> Copy
     </button>` + renderMd(htmlContent);
  boxEl.classList.add("visible");
  boxEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── Quick prompts ────────────────────────────────────────────
document.getElementById("quickPrompts")?.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.dataset.msg));
});

// ═══════════════════════════════════════════════════════════
//  CHAT
// ═══════════════════════════════════════════════════════════

// Auto-resize textarea
chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
  charCounter.textContent = chatInput.value.length + " / 4000";
});

// Enter to send
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", () => sendMessage());

function appendMessage(role, content) {
  // Remove welcome card on first real message
  const welcome = chatMessages.querySelector(".welcome-card");
  if (welcome) welcome.remove();

  const isUser = role === "user";
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const msgEl = document.createElement("div");
  msgEl.className = `msg msg-${isUser ? "user" : "bot"}`;
  msgEl.innerHTML = `
    <div class="msg-avatar">${isUser ? "U" : '<i class="bi bi-cpu-fill"></i>'}</div>
    <div>
      <div class="msg-bubble">${isUser ? escapeHtml(content) : renderMd(content)}</div>
      <div class="msg-meta">
        <span>${now}</span>
        ${!isUser ? `<button class="msg-copy-btn" title="Copy" onclick="copyToClipboard(this.closest('.msg').querySelector('.msg-bubble').innerText)">
          <i class="bi bi-clipboard"></i>
        </button>` : ""}
      </div>
    </div>
  `;
  chatMessages.appendChild(msgEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msgEl;
}

function appendTypingIndicator() {
  const el = document.createElement("div");
  el.className = "msg msg-bot typing-indicator";
  el.id = "typingIndicator";
  el.innerHTML = `
    <div class="msg-avatar"><i class="bi bi-cpu-fill"></i></div>
    <div>
      <div class="msg-bubble">
        <div class="dot"></div><div class="dot"></div><div class="dot"></div>
      </div>
    </div>
  `;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  $("typingIndicator")?.remove();
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function sendMessage(overrideMsg = null) {
  const text = (overrideMsg || chatInput.value).trim();
  if (!text) return;

  chatInput.value = "";
  chatInput.style.height = "auto";
  charCounter.textContent = "0 / 4000";
  sendBtn.disabled = true;

  appendMessage("user", text);
  appendTypingIndicator();

  try {
    const data = await apiFetch("/api/chat", { message: text });
    removeTypingIndicator();
    appendMessage("bot", data.reply);
  } catch (err) {
    removeTypingIndicator();
    appendMessage("bot", `⚠️ **Error:** ${err.message}\n\nPlease check your API key and watsonx.ai configuration.`);
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

clearHistoryBtn.addEventListener("click", async () => {
  try {
    await apiFetch("/api/clear_history", {});
    chatMessages.innerHTML = "";
    // Re-add welcome card
    const welcome = document.createElement("div");
    welcome.className = "welcome-card";
    welcome.innerHTML = `
      <div class="welcome-icon"><i class="bi bi-robot"></i></div>
      <h2>Chat history cleared</h2>
      <p>Start a new research conversation.</p>`;
    chatMessages.appendChild(welcome);
    showToast("Chat history cleared", "success");
  } catch (err) {
    showToast("Failed to clear history: " + err.message, "error");
  }
});

// ═══════════════════════════════════════════════════════════
//  LITERATURE SEARCH
// ═══════════════════════════════════════════════════════════
$("litSearchBtn").addEventListener("click", async () => {
  const query  = $("litQuery").value.trim();
  const domain = $("litDomain").value;
  const yFrom  = $("litYearFrom").value;
  const yTo    = $("litYearTo").value;

  if (!query) { showToast("Please enter a search query", "error"); return; }

  showLoading("Searching literature…");
  $("litSearchBtn").disabled = true;

  try {
    const data = await apiFetch("/api/literature_search", {
      query, domain,
      year_from: yFrom,
      year_to:   yTo,
    });
    showResult($("litResults"), data.results);
  } catch (err) {
    showToast("Search failed: " + err.message, "error");
  } finally {
    hideLoading();
    $("litSearchBtn").disabled = false;
  }
});

// ── Enter in query field
$("litQuery").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("litSearchBtn").click();
});

// ═══════════════════════════════════════════════════════════
//  SUMMARIZER
// ═══════════════════════════════════════════════════════════
$("sumBtn").addEventListener("click", async () => {
  const text    = $("sumText").value.trim();
  const style   = $("sumStyle").value;
  const purpose = $("sumPurpose").value;

  if (!text) { showToast("Please paste paper text to summarize", "error"); return; }

  showLoading("Summarizing paper…");
  $("sumBtn").disabled = true;

  try {
    const data = await apiFetch("/api/summarize", { text, style, purpose });
    showResult($("sumResults"), data.summary);
  } catch (err) {
    showToast("Summarization failed: " + err.message, "error");
  } finally {
    hideLoading();
    $("sumBtn").disabled = false;
  }
});

// ═══════════════════════════════════════════════════════════
//  CITATIONS
// ═══════════════════════════════════════════════════════════
$("citGenBtn").addEventListener("click", async () => {
  const source = $("citSource").value.trim();
  const style  = $("citStyle").value;

  if (!source) { showToast("Please enter source information", "error"); return; }

  showLoading("Generating citation…");
  $("citGenBtn").disabled = true;

  try {
    const data = await apiFetch("/api/generate_citation", { source, style });
    showResult($("citResult"), data.citation);
    await loadCitations();
    showToast("Citation saved!", "success");
  } catch (err) {
    showToast("Citation generation failed: " + err.message, "error");
  } finally {
    hideLoading();
    $("citGenBtn").disabled = false;
  }
});

async function loadCitations() {
  try {
    const data = await fetch(`/api/get_citations?session_id=${SESSION_ID}`).then((r) => r.json());
    renderCitations(data.citations || []);
  } catch {
    // silent fail
  }
}

function renderCitations(citations) {
  const list = $("citationsList");
  if (!citations.length) {
    list.innerHTML = '<p class="text-muted fst-italic">No citations saved yet.</p>';
    return;
  }
  list.innerHTML = citations
    .map(
      (c, i) => `
      <div class="citation-item">
        <div class="cit-style">${c.style}</div>
        <div class="cit-text">${renderMd(c.citation)}</div>
        <div class="cit-added"><i class="bi bi-clock me-1"></i>${new Date(c.added).toLocaleString()}</div>
      </div>`
    )
    .join("");
}

$("copyCitationsBtn").addEventListener("click", () => {
  const items = document.querySelectorAll(".citation-item .cit-text");
  if (!items.length) { showToast("No citations to copy", "error"); return; }
  const text = Array.from(items).map((el) => el.innerText).join("\n\n");
  copyToClipboard(text, $("copyCitationsBtn"));
});

// ═══════════════════════════════════════════════════════════
//  DRAFT SECTION
// ═══════════════════════════════════════════════════════════
$("draftBtn").addEventListener("click", async () => {
  const section    = $("draftSection").value;
  const topic      = $("draftTopic").value.trim();
  const context    = $("draftContext").value.trim();
  const word_count = parseInt($("draftWordCount").value) || 300;

  if (!topic) { showToast("Please enter a paper topic", "error"); return; }

  showLoading("Drafting section…");
  $("draftBtn").disabled = true;

  try {
    const data = await apiFetch("/api/draft_section", { section, topic, context, word_count });
    showResult($("draftResult"), data.draft);
  } catch (err) {
    showToast("Draft failed: " + err.message, "error");
  } finally {
    hideLoading();
    $("draftBtn").disabled = false;
  }
});

// ═══════════════════════════════════════════════════════════
//  RESEARCH IDEAS
// ═══════════════════════════════════════════════════════════
$("ideasBtn").addEventListener("click", async () => {
  const topic = $("ideasTopic").value.trim();
  const level = $("ideasLevel").value;

  if (!topic) { showToast("Please enter a research topic", "error"); return; }

  showLoading("Generating ideas…");
  $("ideasBtn").disabled = true;

  try {
    const data = await apiFetch("/api/research_ideas", { topic, level });
    showResult($("ideasResult"), data.ideas);
  } catch (err) {
    showToast("Idea generation failed: " + err.message, "error");
  } finally {
    hideLoading();
    $("ideasBtn").disabled = false;
  }
});

$("ideasTopic").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("ideasBtn").click();
});

// ═══════════════════════════════════════════════════════════
//  PROJECTS
// ═══════════════════════════════════════════════════════════
$("createProjectBtn").addEventListener("click", createProject);
$("projectTitle").addEventListener("keydown", (e) => {
  if (e.key === "Enter") createProject();
});

async function createProject() {
  const title = $("projectTitle").value.trim();
  const desc  = $("projectDesc").value.trim();

  if (!title) { showToast("Please enter a project title", "error"); return; }

  showLoading("Creating project…");
  $("createProjectBtn").disabled = true;

  try {
    await apiFetch("/api/project", { title, description: desc });
    $("projectTitle").value = "";
    $("projectDesc").value = "";
    await loadProjects();
    showToast("Project created!", "success");
  } catch (err) {
    showToast("Failed to create project: " + err.message, "error");
  } finally {
    hideLoading();
    $("createProjectBtn").disabled = false;
  }
}

async function loadProjects() {
  try {
    const data = await fetch(`/api/projects?session_id=${SESSION_ID}`).then((r) => r.json());
    renderProjects(data.projects || []);
  } catch {
    // silent
  }
}

function renderProjects(projects) {
  const list = $("projectsList");
  if (!projects.length) {
    list.innerHTML = '<p class="text-muted fst-italic">No projects yet. Create one above.</p>';
    return;
  }
  list.innerHTML = projects
    .map(
      (p) => `
      <div class="project-card" id="proj-${p.id}">
        <div class="project-title"><i class="bi bi-folder2 me-2 text-accent"></i>${escapeHtml(p.title)}</div>
        <div class="project-desc">${escapeHtml(p.description || "")}</div>
        <div class="project-meta">
          <span><i class="bi bi-calendar3 me-1"></i>${new Date(p.created).toLocaleDateString()}</span>
          <span><i class="bi bi-sticky me-1"></i>${p.notes.length} notes</span>
        </div>
        <div class="project-notes">
          ${p.notes.map((n) => `<div class="note-item"><i class="bi bi-dot"></i> ${escapeHtml(n.text)}</div>`).join("")}
          <div class="add-note-area">
            <input type="text" placeholder="Add a note…" id="note-input-${p.id}"
                   onkeydown="if(event.key==='Enter') addNote('${p.id}')" />
            <button class="btn-outline-sm" onclick="addNote('${p.id}')">
              <i class="bi bi-plus-lg"></i>
            </button>
          </div>
        </div>
      </div>`
    )
    .join("");
}

async function addNote(pid) {
  const input = $(`note-input-${pid}`);
  const note  = input?.value.trim();
  if (!note) return;

  try {
    const data = await apiFetch(`/api/project/${pid}/note`, { note });
    renderProjects([data.project, ...Array.from(document.querySelectorAll(".project-card"))
      .filter((el) => el.id !== `proj-${pid}`)
      .map((el) => ({ id: el.id.replace("proj-", ""), title: "", description: "", notes: [], created: "" }))]);
    await loadProjects();
  } catch (err) {
    showToast("Failed to add note: " + err.message, "error");
  }
}

// ── Health check on load ─────────────────────────────────────
(async function healthCheck() {
  try {
    await fetch("/api/health");
    statusDot.className = "status-dot";
  } catch {
    statusDot.className = "status-dot offline";
    showToast("Cannot connect to the Research Agent backend.", "error");
  }
})();
