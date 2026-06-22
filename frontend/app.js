/**
 * app.js — StudentOS frontend logic
 *
 * IMPORTANT: every fetch() call to the backend MUST include
 * `credentials: "include"`. Without it, the browser will NOT send the
 * Flask session cookie back on each request, and the backend will think
 * every message is a brand new conversation — this was the root cause
 * of the "AI forgets everything" bug.
 *
 * This file must be served from a local server (e.g. VS Code Live Server,
 * http://127.0.0.1:5500), NOT opened directly as a file:// path — some
 * browsers block cookies entirely for file:// origins even with
 * credentials included.
 */

const API = "http://localhost:5000";

// ── Mode configuration ───────────────────────────────────────
const MODES = {
  concept: {
    label: "Concept Explainer",
    tag: "concept",
    desc: "Explains any topic, tailored to your level.",
    suggestions: [
      "Explain recursion call stack mechanics",
      "What is Big O notation conceptually?",
      "How do hash tables resolve slot collisions?"
    ],
    uploadable: false
  },
  exam: {
    label: "Exam Coach",
    tag: "exam",
    desc: "Generates mock quiz questions from a topic or your notes.",
    suggestions: [
      "Quiz me on array sorting algorithms",
      "Verify edge cases in linked lists",
      "Ask me mock questions about OOP principles"
    ],
    uploadable: false
  },
  cv: {
    label: "CV Reviewer",
    tag: "cv",
    desc: "Paste your CV or attach a PDF — get honest, structured feedback.",
    suggestions: [
      "Review this CV — attach the PDF below",
      "How should I structure my personal projects section?"
    ],
    uploadable: true
  },
  intern: {
    label: "Internship Finder",
    tag: "intern",
    desc: "Upload your CV or describe your profile — I'll suggest where and how to look.",
    suggestions: [
      "I'm a 2nd year CS student in Paris",
      "I know Python and React, looking for startups",
      "now give me suggestions"
    ],
    uploadable: true
  }
};

// ── Read mode from URL ───────────────────────────────────────
// NOTE: index.html links must use ?mode=intern, NOT ?mode=internship —
// the key here matches prompts.py exactly.
const params = new URLSearchParams(window.location.search);
const mode   = params.get("mode") || "concept";
const config = MODES[mode] || MODES["concept"];

// ── Markdown renderer ────────────────────────────────────────
function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdown(text) {
  text = text.replace(/```(\w+)?\n?([\s\S]*?)```/g,
    (_, __, code) => `<pre><code>${escapeHtml(code.trim())}</code></pre>`
  );
  text = text.replace(/`([^`]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`);
  text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/^[*-] (.+)$/gm, "<li>$1</li>");
  text = text.replace(/(<li>.*<\/li>\n?)+/g,
    s => `<ul style="padding-left:16px;margin:6px 0">${s}</ul>`
  );
  return text.replace(/\n/g, "<br>");
}

// ── File attachment ──────────────────────────────────────────
function triggerFileSelect() {
  const fileInput = document.getElementById("file-input");
  if (fileInput) fileInput.click();
}

function updateFileIndicator() {
  const fileInput = document.getElementById("file-input");
  const statusDiv = document.getElementById("file-status");
  if (!fileInput || !statusDiv) return;

  if (fileInput.files.length > 0) {
    statusDiv.textContent   = `Attached: ${fileInput.files[0].name}`;
    statusDiv.style.display = "block";
  } else {
    statusDiv.style.display = "none";
  }
}

// ── Page setup ───────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {

  const badge = document.getElementById("mode-badge") || document.getElementById("mode-tag");
  if (badge) {
    badge.textContent = config.label;
    badge.className   = `mode-tag ${config.tag}`;
  }

  const title = document.getElementById("empty-title");
  const desc  = document.getElementById("empty-desc");
  if (title) title.textContent = config.label;
  if (desc)  desc.textContent  = config.desc;

  const sugBox = document.getElementById("suggestions") || document.getElementById("chips");
  if (sugBox && config.suggestions) {
    config.suggestions.forEach(s => {
      const chip       = document.createElement("button");
      chip.className   = "suggestion-chip chip";
      chip.textContent = s;
      chip.onclick     = () => {
        document.getElementById("user-input").value = s;
        sendMessage();
      };
      sugBox.appendChild(chip);
    });
  }

  const fileBtn = document.getElementById("file-btn");
  if (fileBtn) fileBtn.style.display = config.uploadable ? "flex" : "none";

  const fileInput = document.getElementById("file-input");
  if (fileInput) fileInput.addEventListener("change", updateFileIndicator);

  const input = document.getElementById("user-input");
  if (input) {
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });
    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  document.title = `StudentOS — ${config.label}`;
});

// ── Add a chat bubble ────────────────────────────────────────
function addBubble(text, role, asHtml = false) {
  const empty = document.getElementById("empty-state");
  if (empty) empty.remove();

  const messages   = document.getElementById("messages");
  const row        = document.createElement("div");
  row.className    = "message-row";
  const bubble     = document.createElement("div");
  bubble.className = `bubble ${role}`;

  if (asHtml) bubble.innerHTML = text;
  else bubble.textContent = text;

  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

// ── Send message ─────────────────────────────────────────────
async function sendMessage() {
  const input     = document.getElementById("user-input");
  const fileInput = document.getElementById("file-input");
  const btn       = document.getElementById("send-btn");
  const statusDiv = document.getElementById("file-status");

  const text    = input.value.trim();
  const hasFile = fileInput && fileInput.files.length > 0;

  if (!text && !hasFile) return;

  let displayLog = text;
  if (hasFile) {
    displayLog = text
      ? `[Attached: ${fileInput.files[0].name}] — ${text}`
      : `[Attached: ${fileInput.files[0].name}]`;
  }

  addBubble(displayLog, "user");
  input.value        = "";
  input.style.height = "auto";

  const typing = addBubble("Thinking...", "assistant typing");
  btn.disabled = true;

  const formData = new FormData();
  formData.append("message", text);
  formData.append("mode", mode);
  if (hasFile) formData.append("file", fileInput.files[0]);

  try {
    const res = await fetch(`${API}/chat`, {
      method:      "POST",
      credentials: "include",   // <-- REQUIRED: sends the session cookie back
      body:        formData
      // No Content-Type header — the browser sets the multipart boundary automatically
    });

    const data = await res.json();
    typing.innerHTML = renderMarkdown(data.reply || data.error || "Something went wrong.");
    typing.classList.remove("typing");

  } catch {
    typing.textContent = "Could not reach the server. Is the backend running?";
    typing.classList.remove("typing");
  }

  if (fileInput) fileInput.value = "";
  if (statusDiv) statusDiv.style.display = "none";
  btn.disabled = false;
  input.focus();
}

// ── Reset chat ───────────────────────────────────────────────
async function resetChat() {
  try {
    await fetch(`${API}/reset`, { method: "POST", credentials: "include" });
  } catch (e) {
    console.error(e);
  }
  location.reload();
}