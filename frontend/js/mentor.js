// Mentor page JS
document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();
  loadChatHistory();
  setupChatInput();
  setupToolButtons();
  loadGoals();
});

// ── Chat ──────────────────────────────────────────────────────────────────────
async function loadChatHistory() {
  try {
    const data = await API.get("/api/mentor/chat/history");
    const msgs = data.history || [];
    msgs.forEach(m => appendBubble(m.role, m.content, false));
    if (msgs.length === 0) appendBubble("assistant", "👋 Hi! I'm your AI Career Mentor. I can help you with skill gaps, roadmaps, resume tips, industry insights, and job search strategies. What would you like to work on today?", false);
    scrollChat();
  } catch { }
}

function setupChatInput() {
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  if (sendBtn) sendBtn.addEventListener("click", sendMessage);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  }
  const clearBtn = document.getElementById("clear-chat-btn");
  if (clearBtn) clearBtn.addEventListener("click", clearChat);
}

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const message = input?.value.trim();
  if (!message) return;

  input.value = "";
  appendBubble("user", message);
  showTyping();
  scrollChat();

  try {
    const data = await API.post("/api/mentor/chat", { message });
    removeTyping();
    appendBubble("assistant", data.response);
    scrollChat();
  } catch (err) {
    removeTyping();
    appendBubble("assistant", `❌ Error: ${err.message}`);
  }
}

function appendBubble(role, content, animate = true) {
  const msgs = document.getElementById("chat-messages");
  if (!msgs) return;
  const div = document.createElement("div");
  div.className = `chat-bubble ${role}${animate ? " fade-in" : ""}`;
  div.innerHTML = renderMarkdown(content);
  msgs.appendChild(div);
}

function showTyping() {
  const msgs = document.getElementById("chat-messages");
  if (!msgs) return;
  const div = document.createElement("div");
  div.id = "typing-indicator";
  div.className = "chat-bubble assistant typing";
  div.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  msgs.appendChild(div);
}
function removeTyping() { document.getElementById("typing-indicator")?.remove(); }
function scrollChat() { const m = document.getElementById("chat-messages"); if (m) m.scrollTop = m.scrollHeight; }

async function clearChat() {
  if (!confirm("Clear all chat history?")) return;
  await API.delete("/api/mentor/chat/clear");
  const msgs = document.getElementById("chat-messages");
  if (msgs) msgs.innerHTML = "";
  appendBubble("assistant", "Chat cleared! How can I help you today?");
}

// ── Tool Buttons ──────────────────────────────────────────────────────────────
function setupToolButtons() {
  document.querySelectorAll("[data-tool]").forEach(btn => {
    btn.addEventListener("click", () => openTool(btn.dataset.tool));
  });
}

async function openTool(tool) {
  const panel = document.getElementById("tool-panel");
  const content = document.getElementById("tool-content");
  if (!panel || !content) return;
  panel.classList.remove("hidden");
  content.innerHTML = `<div style="text-align:center;padding:40px"><div class="loader-spinner" style="margin:0 auto 16px"></div><p>Loading ${tool}...</p></div>`;

  const user = Auth.getUser();
  try {
    let html = "";
    if (tool === "skill-gap") html = await renderSkillGap(user);
    else if (tool === "roadmap") html = await renderRoadmap(user);
    else if (tool === "insights") html = await renderInsights(user);
    else if (tool === "resume") html = renderResumeForm(user);
    else if (tool === "job-strategy") html = await renderJobStrategy(user);
    else if (tool === "linkedin") html = await renderLinkedin(user);
    else if (tool === "prep-schedule") html = renderPrepForm();
    else if (tool === "goals") html = renderGoalsPanel();
    content.innerHTML = html;
    if (tool === "goals") bindGoalEvents();
    if (tool === "resume") bindResumeForm(user);
    if (tool === "prep-schedule") bindPrepForm(user);
  } catch (err) {
    content.innerHTML = `<p style="color:var(--danger)">Error: ${err.message}</p>`;
  }
}

function closeTool() { document.getElementById("tool-panel")?.classList.add("hidden"); }
window.closeTool = closeTool;

// ── Skill Gap ─────────────────────────────────────────────────────────────────
async function renderSkillGap(user) {
  const d = await API.post("/api/mentor/skill-gap", {
    current_skills: user?.skills || "", target_role: user?.target_role || "Software Engineer", experience: user?.experience || "fresher"
  });
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  const bar = `<div class="progress-bar" style="margin:12px 0"><div class="progress-fill" style="width:${d.gap_score}%"></div></div>`;
  const chips = (arr, cls) => (arr||[]).map(s=>`<span class="skill-chip ${cls}">${s}</span>`).join("");
  return `
    <h3 style="margin-bottom:8px">🎯 Skill Gap Analysis</h3>
    <p style="color:var(--text2);margin-bottom:16px">${d.summary}</p>
    <div style="margin-bottom:16px"><span style="font-size:14px;font-weight:600">Readiness: ${d.gap_score}%</span>${bar}</div>
    <div style="margin-bottom:16px"><p class="section-title" style="font-size:14px">✅ Present Skills</p>${chips(d.present_skills,"skill-present")}</div>
    <div style="margin-bottom:16px"><p class="section-title" style="font-size:14px">❌ Missing Skills</p>${chips(d.missing_skills,"skill-missing")}</div>
    <div><p class="section-title" style="font-size:14px">⭐ Priority Skills</p>
    ${(d.priority_skills||[]).map(p=>`<div style="background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <strong>${p.skill}</strong>
        <span class="badge ${p.importance==="critical"?"badge-danger":p.importance==="high"?"badge-warning":"badge-primary"}">${p.importance}</span>
      </div>
      <p style="font-size:12px;color:var(--text2)">⏱ ${p.time_to_learn} | 📚 ${(p.resources||[]).join(", ")}</p>
    </div>`).join("")}</div>`;
}

// ── Roadmap ───────────────────────────────────────────────────────────────────
async function renderRoadmap(user) {
  const d = await API.post("/api/mentor/roadmap", {
    target_role: user?.target_role || "Software Engineer",
    missing_skills: [], experience: user?.experience || "fresher", weeks: 8
  });
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  return `
    <h3 style="margin-bottom:4px">🗺 ${d.title}</h3>
    <p style="color:var(--text2);margin-bottom:24px">${d.total_weeks} weeks · ~${d.weekly_hours}h/week</p>
    ${(d.weeks||[]).map(w=>`
      <div class="roadmap-week">
        <div class="week-label">Week ${w.week}</div>
        <div class="week-theme">${w.theme}</div>
        <p style="font-size:13px;color:var(--text2);margin-bottom:6px">📌 ${(w.topics||[]).join(" · ")}</p>
        <p style="font-size:13px;color:var(--text2)">🎯 Milestone: ${w.milestone}</p>
        <p style="font-size:13px;color:var(--accent);margin-top:4px">🛠 Project: ${w.project}</p>
      </div>`).join("")}
    ${d.certifications?.length ? `<div style="background:var(--bg3);border-radius:8px;padding:16px;margin-top:8px"><p style="font-weight:600;margin-bottom:8px">🏆 Recommended Certifications</p>${d.certifications.map(c=>`<span class="skill-chip skill-required">${c}</span>`).join("")}</div>` : ""}`;
}

// ── Industry Insights ─────────────────────────────────────────────────────────
async function renderInsights(user) {
  const role = user?.target_role || "Software Engineer";
  const d = await API.get(`/api/mentor/insights?role=${encodeURIComponent(role)}`);
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  const demandColor = d.demand_level==="high"?"var(--success)":d.demand_level==="medium"?"var(--warning)":"var(--danger)";
  return `
    <h3 style="margin-bottom:4px">📊 Industry Insights: ${d.role}</h3>
    <p style="color:var(--text2);margin-bottom:20px">${d.job_market_summary}</p>
    <div class="grid-2" style="margin-bottom:20px;gap:12px">
      <div style="background:var(--bg3);border-radius:8px;padding:14px">
        <p style="font-size:12px;color:var(--text2)">Demand Level</p>
        <p style="font-size:20px;font-weight:800;color:${demandColor}">${d.demand_level?.toUpperCase()}</p>
      </div>
      <div style="background:var(--bg3);border-radius:8px;padding:14px">
        <p style="font-size:12px;color:var(--text2)">Growth Rate</p>
        <p style="font-size:20px;font-weight:800;color:var(--accent)">${d.growth_rate}</p>
      </div>
    </div>
    <div style="background:var(--bg3);border-radius:8px;padding:14px;margin-bottom:16px">
      <p style="font-weight:600;margin-bottom:10px">💰 Salary Benchmarks</p>
      ${Object.entries(d.avg_salary||{}).map(([k,v])=>`<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--glass-border);font-size:14px"><span style="color:var(--text2);text-transform:capitalize">${k}</span><span style="font-weight:600;color:var(--success)">${v}</span></div>`).join("")}
    </div>
    <p class="section-title" style="font-size:14px">🔥 In-Demand Skills</p>
    <div style="margin-bottom:16px">${(d.in_demand_skills||[]).map(s=>`<span class="skill-chip skill-required">${s}</span>`).join("")}</div>
    <p class="section-title" style="font-size:14px">🚀 Emerging Trends</p>
    <ul style="margin-bottom:16px">${(d.emerging_trends||[]).map(t=>`<li style="font-size:13px;color:var(--text2);padding:4px 0">• ${t}</li>`).join("")}</ul>
    <p class="section-title" style="font-size:14px">🏢 Top Hiring Companies</p>
    <div>${(d.top_companies||[]).map(c=>`<span class="skill-chip skill-present">${c}</span>`).join("")}</div>`;
}

// ── Resume ────────────────────────────────────────────────────────────────────
function renderResumeForm(user) {
  return `
    <h3 style="margin-bottom:16px">📄 Resume Review</h3>
    <div class="input-group">
      <label>Target Role</label>
      <input id="resume-role" class="input-field" value="${user?.target_role||"Software Engineer"}" placeholder="Target Job Role">
    </div>
    <div class="input-group">
      <label>Paste Your Resume Text</label>
      <textarea id="resume-text" class="input-field" style="min-height:200px" placeholder="Paste your full resume content here..."></textarea>
    </div>
    <button class="btn btn-primary" id="analyze-resume-btn">🔍 Analyze Resume</button>
    <div id="resume-result" style="margin-top:20px"></div>`;
}

function bindResumeForm(user) {
  document.getElementById("analyze-resume-btn")?.addEventListener("click", async () => {
    const text = document.getElementById("resume-text")?.value.trim();
    const role = document.getElementById("resume-role")?.value.trim();
    if (!text) { showToast("Please paste your resume text.", "warning"); return; }
    showLoader("Analyzing resume...");
    try {
      const d = await API.post("/api/mentor/resume", { resume_text: text, target_role: role });
      document.getElementById("resume-result").innerHTML = renderResumeResult(d);
    } catch (err) { showToast(err.message, "error"); } finally { hideLoader(); }
  });
}

function renderResumeResult(d) {
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  const scoreColor2 = d.ats_score >= 70 ? "var(--success)" : d.ats_score >= 50 ? "var(--warning)" : "var(--danger)";
  return `
    <div style="background:var(--bg3);border-radius:12px;padding:20px">
      <div style="text-align:center;margin-bottom:20px">
        <div style="font-size:48px;font-weight:900;color:${scoreColor2}">${d.ats_score}</div>
        <p style="color:var(--text2)">ATS Score / 100 · ${d.overall_rating?.replace("_"," ")}</p>
      </div>
      <p class="section-title" style="font-size:14px">✅ Strengths</p>
      <ul class="points-list strengths" style="margin-bottom:14px">${(d.strengths||[]).map(s=>`<li>${s}</li>`).join("")}</ul>
      <p class="section-title" style="font-size:14px">⚠️ Weaknesses</p>
      <ul class="points-list improvements" style="margin-bottom:14px">${(d.weaknesses||[]).map(w=>`<li>${w}</li>`).join("")}</ul>
      <p class="section-title" style="font-size:14px">🔑 Missing Keywords</p>
      <div style="margin-bottom:14px">${(d.missing_keywords||[]).map(k=>`<span class="skill-chip skill-missing">${k}</span>`).join("")}</div>
      <p class="section-title" style="font-size:14px">💡 Suggestions</p>
      ${(d.suggestions||[]).map(s=>`<div style="background:var(--bg);border-radius:6px;padding:10px;margin-bottom:6px;font-size:13px"><strong>${s.section}:</strong> ${s.suggestion}</div>`).join("")}
    </div>`;
}

// ── Job Strategy ──────────────────────────────────────────────────────────────
async function renderJobStrategy(user) {
  const d = await API.post("/api/mentor/job-strategy", {
    target_role: user?.target_role || "Software Engineer",
    experience: user?.experience || "fresher",
    skills: user?.skills || ""
  });
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  return `
    <h3 style="margin-bottom:16px">🎯 Job Search Strategy</h3>
    <p class="section-title" style="font-size:14px">📱 Job Platforms</p>
    ${(d.platforms||[]).map(p=>`<div style="background:var(--bg3);border-radius:8px;padding:12px;margin-bottom:8px;display:flex;gap:12px;align-items:flex-start"><span class="badge ${p.priority==="high"?"badge-success":p.priority==="medium"?"badge-warning":"badge-primary"}">${p.priority}</span><div><strong style="font-size:14px">${p.name}</strong><p style="font-size:13px;color:var(--text2);margin-top:2px">${p.strategy}</p></div></div>`).join("")}
    <p class="section-title" style="font-size:14px;margin-top:16px">🤝 Networking Tips</p>
    <ul style="margin-bottom:16px">${(d.networking_tips||[]).map(t=>`<li style="font-size:13px;color:var(--text2);padding:4px 0">• ${t}</li>`).join("")}</ul>
    <p class="section-title" style="font-size:14px">📧 Cold Outreach Template</p>
    <div style="background:var(--bg3);border-radius:8px;padding:14px;font-size:13px;color:var(--text2);white-space:pre-wrap;margin-bottom:16px">${d.cold_outreach_template}</div>
    <p class="section-title" style="font-size:14px">📅 Weekly Action Plan</p>
    <ul>${(d.weekly_action_plan||[]).map((a,i)=>`<li style="font-size:13px;color:var(--text2);padding:6px 0;border-bottom:1px solid var(--glass-border)"><span style="color:var(--primary);font-weight:600">Day ${i+1}:</span> ${a}</li>`).join("")}</ul>`;
}

// ── LinkedIn ──────────────────────────────────────────────────────────────────
async function renderLinkedin(user) {
  const d = await API.post("/api/mentor/linkedin-tips", {
    target_role: user?.target_role || "Software Engineer",
    skills: user?.skills || "", experience: user?.experience || "fresher"
  });
  if (d.error) return `<p style="color:var(--danger)">${d.error}</p>`;
  return `
    <h3 style="margin-bottom:16px">💼 LinkedIn Profile Optimization</h3>
    <p class="section-title" style="font-size:14px">✍️ Headline Examples</p>
    ${(d.headline_examples||[]).map(h=>`<div style="background:var(--bg3);border-radius:6px;padding:10px;margin-bottom:6px;font-size:13px;font-style:italic">"${h}"</div>`).join("")}
    <p class="section-title" style="font-size:14px;margin-top:16px">🔑 Keywords to Include</p>
    <div style="margin-bottom:16px">${(d.keywords_to_include||[]).map(k=>`<span class="skill-chip skill-required">${k}</span>`).join("")}</div>
    <p class="section-title" style="font-size:14px">🛠 Skills to Add</p>
    <div style="margin-bottom:16px">${(d.skills_to_add||[]).map(s=>`<span class="skill-chip skill-present">${s}</span>`).join("")}</div>
    <p class="section-title" style="font-size:14px">📣 Content Ideas</p>
    <ul>${(d.content_ideas||[]).map(i=>`<li style="font-size:13px;color:var(--text2);padding:4px 0">• ${i}</li>`).join("")}</ul>
    <p class="section-title" style="font-size:14px;margin-top:16px">🤝 Connection Strategy</p>
    <ul>${(d.connection_strategy||[]).map(c=>`<li style="font-size:13px;color:var(--text2);padding:4px 0">• ${c}</li>`).join("")}</ul>`;
}

// ── Prep Schedule Form ────────────────────────────────────────────────────────
function renderPrepForm() {
  return `
    <h3 style="margin-bottom:16px">📅 Interview Prep Schedule</h3>
    <div class="input-group"><label>Target Role</label><input id="prep-role" class="input-field" placeholder="e.g. Software Engineer"></div>
    <div class="input-group"><label>Interview Date</label><input id="prep-date" class="input-field" type="date"></div>
    <div class="input-group"><label>Current Skills</label><input id="prep-skills" class="input-field" placeholder="Python, DSA, System Design..."></div>
    <button class="btn btn-primary" id="gen-schedule-btn">📋 Generate Schedule</button>
    <div id="schedule-result" style="margin-top:20px"></div>`;
}

function bindPrepForm(user) {
  const roleEl = document.getElementById("prep-role");
  const skillsEl = document.getElementById("prep-skills");
  if (roleEl) roleEl.value = user?.target_role || "";
  if (skillsEl) skillsEl.value = user?.skills || "";
  document.getElementById("gen-schedule-btn")?.addEventListener("click", async () => {
    const role = document.getElementById("prep-role")?.value.trim();
    const date = document.getElementById("prep-date")?.value;
    const skills = document.getElementById("prep-skills")?.value.trim();
    showLoader("Generating your prep schedule...");
    try {
      const d = await API.post("/api/mentor/prep-schedule", {
        role: role||"Software Engineer", interview_date: date||"2 weeks from now", current_skills: skills
      });
      const el = document.getElementById("schedule-result");
      if (d.error) { el.innerHTML = `<p style="color:var(--danger)">${d.error}</p>`; return; }
      el.innerHTML = `
        <div style="background:var(--bg3);border-radius:12px;padding:20px">
          <div class="grid-2" style="margin-bottom:20px;gap:12px">
            <div style="background:var(--bg);border-radius:8px;padding:12px;text-align:center"><div style="font-size:28px;font-weight:800;color:var(--primary)">${d.total_days}</div><div style="font-size:12px;color:var(--text2)">Days Plan</div></div>
            <div style="background:var(--bg);border-radius:8px;padding:12px;text-align:center"><div style="font-size:28px;font-weight:800;color:var(--accent)">${d.daily_hours}h</div><div style="font-size:12px;color:var(--text2)">Daily Study</div></div>
          </div>
          ${(d.phases||[]).map(p=>`<div class="roadmap-week"><div class="week-label">${p.days}</div><div class="week-theme">${p.phase}</div><p style="font-size:13px;color:var(--text2);margin-bottom:6px">Focus: ${p.focus}</p><ul>${(p.daily_tasks||[]).map(t=>`<li style="font-size:12px;color:var(--text3)">• ${t}</li>`).join("")}</ul></div>`).join("")}
          ${d.day_before_tips?.length?`<p class="section-title" style="font-size:14px;margin-top:16px">🌙 Day Before</p><ul>${d.day_before_tips.map(t=>`<li style="font-size:13px;color:var(--text2);padding:2px 0">• ${t}</li>`).join("")}</ul>`:""}
        </div>`;
    } catch (err) { showToast(err.message, "error"); } finally { hideLoader(); }
  });
}

// ── Goals ─────────────────────────────────────────────────────────────────────
function renderGoalsPanel() {
  return `
    <h3 style="margin-bottom:16px">🎯 Goal Tracker</h3>
    <div style="display:flex;gap:12px;margin-bottom:20px">
      <input id="new-goal-title" class="input-field" placeholder="Add a new goal..." style="flex:1">
      <input id="new-goal-date" class="input-field" type="date" style="width:160px">
      <button class="btn btn-primary" id="add-goal-btn">+ Add</button>
    </div>
    <div id="goals-list"></div>`;
}

async function loadGoals() {
  try {
    const d = await API.get("/api/mentor/goals");
    const panel = document.getElementById("goals-list");
    if (!panel) return;
    renderGoalList(d.goals || [], panel);
  } catch { }
}

function renderGoalList(goals, container) {
  if (!goals.length) {
    container.innerHTML = `<p style="color:var(--text3);text-align:center;padding:24px">No goals yet. Add your first goal above!</p>`;
    return;
  }
  container.innerHTML = goals.map(g => `
    <div class="goal-item">
      <div class="goal-progress" style="flex:1">
        <div class="goal-title">${g.title}</div>
        <div class="goal-meta">📅 ${g.target_date||"No deadline"} · <span style="color:${g.status==="completed"?"var(--success)":"var(--primary)"}">${g.status}</span></div>
        <div class="progress-bar" style="margin-top:8px"><div class="progress-fill" style="width:${g.progress}%"></div></div>
        <div style="font-size:11px;color:var(--text3);margin-top:4px">${g.progress}% complete</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <input type="range" min="0" max="100" value="${g.progress}" style="width:80px" onchange="updateGoal(${g.id}, this.value, '${g.status}')">
        <button class="btn btn-sm btn-danger" onclick="deleteGoal(${g.id})">🗑</button>
      </div>
    </div>`).join("");
}

function bindGoalEvents() {
  loadGoals();
  document.getElementById("add-goal-btn")?.addEventListener("click", async () => {
    const title = document.getElementById("new-goal-title")?.value.trim();
    const date = document.getElementById("new-goal-date")?.value;
    if (!title) { showToast("Enter a goal title.", "warning"); return; }
    try {
      await API.post("/api/mentor/goals", { title, target_date: date });
      document.getElementById("new-goal-title").value = "";
      showToast("Goal added!", "success");
      loadGoals();
    } catch (err) { showToast(err.message, "error"); }
  });
}

async function updateGoal(id, progress, status) {
  try { await API.put(`/api/mentor/goals/${id}`, { progress: parseInt(progress), status }); }
  catch { }
}

async function deleteGoal(id) {
  if (!confirm("Delete this goal?")) return;
  try {
    await API.delete(`/api/mentor/goals/${id}`);
    showToast("Goal deleted.", "info");
    loadGoals();
  } catch (err) { showToast(err.message, "error"); }
}

window.updateGoal = updateGoal;
window.deleteGoal = deleteGoal;
window.openTool = openTool;
window.sendMessage = sendMessage;
