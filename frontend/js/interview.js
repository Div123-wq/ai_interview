// Interview State Machine
let state = {
  sessionId: null,
  questions: [],
  currentIndex: 0,
  answers: [],
  timerInterval: null,
  secondsElapsed: 0,
  isRecording: false,
  recognition: null,
  stream: null,
  sessionConfig: {}
};

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();
  initSetupPanel();
  initVoice();
  // Auto-start when query params are present (role,difficulty,type,count)
  try {
    const params = new URLSearchParams(window.location.search);
    const role = params.get('role');
    if (role) {
      // Trigger server-side start and initialize interview state
      (async () => {
        const difficulty = params.get('difficulty') || 'intermediate';
        const type = params.get('type') || 'mixed';
        const count = parseInt(params.get('count') || '5', 10);
        showLoader('Generating your interview questions...');
        try {
          const data = await API.post('/api/interview/start', { role, difficulty, interview_type: type, total_questions: count });
          const questions = Array.isArray(data.questions)
            ? data.questions.map((q, idx) => normalizeQuestion(q, idx, type === 'behavioral' ? 'behavioral' : 'technical'))
            : [];
          if (!questions.length) { hideLoader(); showToast('No questions generated', 'error'); return; }
          state.sessionId = data.session_id;
          state.questions = questions;
          state.currentIndex = 0;
          state.answers = [];
          state.sessionConfig = { role, difficulty, type, count, total_questions: data.total_questions || count };
          hideLoader();
          // Switch to interview panel and initialize
          showPanel("interview-panel");
          initWebcam();
          renderQuestion();
          startTimer();
          updateScoreSidebar();
          showToast('Interview started! Good luck 🎯', 'success');
        } catch (err) { hideLoader(); showToast('Unable to start interview', 'error'); }
      })();
    }
  } catch (e) {}
});

// ── Setup Panel ────────────────────────────────────────────────────────────────
function initSetupPanel() {
  const form = document.getElementById("setup-form");
  if (form) form.addEventListener("submit", startInterview);
}

function normalizeQuestion(question, index, defaultType) {
  if (!question || typeof question !== "object") {
    return {
      question: `Answer a core ${defaultType} interview question about your experience.`,
      type: defaultType,
      hint: "Share a clear example and explain your thought process."
    };
  }
  return {
    question: question.question || `Answer a ${defaultType} interview question.`,
    type: question.type || defaultType,
    hint: question.hint || "Share your reasoning, structure, and outcome."
  };
}

async function startInterview(e) {
  if (e && e.preventDefault) e.preventDefault();
  
  const role = document.getElementById("role-select")?.value || "Software Engineer";
  const difficulty = document.getElementById("difficulty-select")?.value || "intermediate";
  const type = document.getElementById("type-select")?.value || "technical";
  const count = parseInt(document.getElementById("count-select")?.value || "5", 10);
  
  console.log("startInterview called with:", { role, difficulty, type, count });
  
  // Always redirect to interview.html with params for a fresh page start
  const qs = new URLSearchParams({ role, difficulty, type, count });
  const redirectUrl = `interview.html?${qs.toString()}`;
  console.log("Redirecting to:", redirectUrl);
  window.location.href = redirectUrl;
}

// ── Question Rendering ─────────────────────────────────────────────────────────
function renderQuestion() {
  const q = state.questions[state.currentIndex];
  if (!q) return;

  const total = state.questions.length;
  const num = state.currentIndex + 1;

  document.getElementById("q-number").textContent = `Question ${num} of ${total}`;
  document.getElementById("q-type-badge").textContent = q.type || "technical";
  document.getElementById("q-type-badge").className = `badge ${q.type === "behavioral" ? "badge-warning" : "badge-primary"}`;
  document.getElementById("q-text").textContent = q.question;
  document.getElementById("q-hint").textContent = q.hint || "";
  document.getElementById("q-progress").style.width = `${((num-1)/total)*100}%`;
  document.getElementById("answer-input").value = "";
  document.getElementById("feedback-area").classList.add("hidden");
  document.getElementById("submit-btn").disabled = false;
  document.getElementById("next-btn").classList.add("hidden");

  // TTS: read question aloud
  if (document.getElementById("tts-toggle")?.checked) speakText(q.question);

  startTimer();
}

// ── Timer ──────────────────────────────────────────────────────────────────────
function startTimer() {
  clearInterval(state.timerInterval);
  state.secondsElapsed = 0;
  updateTimerDisplay();
  state.timerInterval = setInterval(() => {
    state.secondsElapsed++;
    updateTimerDisplay();
  }, 1000);
}

function stopTimer() {
  clearInterval(state.timerInterval);
}

function updateTimerDisplay() {
  const el = document.getElementById("timer-display");
  if (!el) return;
  const m = Math.floor(state.secondsElapsed / 60);
  const s = state.secondsElapsed % 60;
  el.textContent = `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
  el.className = "timer";
  if (state.secondsElapsed > 180) el.classList.add("warning");
  if (state.secondsElapsed > 300) { el.classList.remove("warning"); el.classList.add("danger"); }
}

// ── Submit Answer ──────────────────────────────────────────────────────────────
async function submitAnswer() {
  const answer = document.getElementById("answer-input").value.trim();
  if (!answer) { showToast("Please type or speak your answer first.", "warning"); return; }

  stopTimer();
  const q = state.questions[state.currentIndex];
  document.getElementById("submit-btn").disabled = true;
  showLoader("Analyzing your answer...");

  try {
    // Capture webcam snapshot (if available) and include it with the answer
    let webcam_image = null;
    try {
      if (state.stream) {
        const video = document.getElementById('webcam-video');
        if (video && video.videoWidth > 0) {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          webcam_image = canvas.toDataURL('image/png');
        }
      }
    } catch (e) {
      console.warn('Could not capture webcam snapshot', e);
      webcam_image = null;
    }

    const data = await API.post("/api/interview/answer", {
      session_id: state.sessionId,
      question_number: state.currentIndex + 1,
      question: q.question,
      question_type: q.type,
      answer,
      time_taken: state.secondsElapsed,
      webcam_image: webcam_image
    });
    
    // Ensure evaluation is a valid object
    let ev = data.evaluation || {};
    if (typeof ev !== 'object' || ev === null) {
      ev = {};
    }
    
    // Provide defaults for all expected fields
    if (!ev.score) ev.score = 5;
    if (!ev.feedback) ev.feedback = "Answer received.";
    if (!Array.isArray(ev.strengths)) ev.strengths = [];
    if (!Array.isArray(ev.improvements)) ev.improvements = [];
    if (!ev.follow_up) ev.follow_up = "";
    if (!ev.star_analysis) ev.star_analysis = "";
    if (!ev.confidence) ev.confidence = "medium";
    
    state.answers.push({ ...q, answer, evaluation: ev, time_taken: state.secondsElapsed });
    renderFeedback(ev);
    document.getElementById("next-btn").classList.remove("hidden");

    const scoreLabel = ev.score >= 7 ? "success" : ev.score >= 4 ? "warning" : "error";
    const feedbackText = String(ev.feedback || "Answer received.").slice(0,60);
    showToast(`Score: ${ev.score}/10 — ${feedbackText}...`, scoreLabel);
  } catch (err) {
    console.error("Submit answer error:", err);
    showToast(`Error: ${err.message || "Unable to evaluate answer. Please try again."}`, "error");
    document.getElementById("submit-btn").disabled = false;
  } finally {
    hideLoader();
  }
}

// Capture a single webcam snapshot (returns dataURL) — exposed for testing
window.captureWebcamSnapshot = async function() {
  try {
    if (!state.stream) return null;
    const video = document.getElementById('webcam-video');
    if (!video || video.videoWidth === 0) return null;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/png');
  } catch (e) { return null; }
}

function renderFeedback(ev) {
  const area = document.getElementById("feedback-area");
  const grade = ev.score >= 7 ? "good" : ev.score >= 4 ? "average" : "poor";
  const feedback = ev.feedback || "No feedback available.";
  const strengths = Array.isArray(ev.strengths) ? ev.strengths : [];
  const improvements = Array.isArray(ev.improvements) ? ev.improvements : [];
  const starAnalysis = ev.star_analysis || "";
  const followUp = ev.follow_up || "";
  const confidence = ev.confidence || ev.confidence_level || "medium";
  
  area.innerHTML = `
    <div class="feedback-card ${grade}">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <span class="section-title" style="margin:0">AI Feedback</span>
        <span style="font-size:24px;font-weight:800;color:${scoreColor(ev.score)}">${ev.score}/10</span>
      </div>
      <p style="color:var(--text2);font-size:14px;margin-bottom:16px">${feedback}</p>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
        <div style="font-size:12px;color:var(--text3)">Confidence:</div>
        <div style="font-weight:700;color:${confidence==='high'?'#10b981':confidence==='low'?'#ef4444':'#f59e0b'}">${confidence}</div>
      </div>
      ${strengths.length ? `<p style="font-size:13px;font-weight:600;color:var(--success);margin-bottom:6px">✅ Strengths</p><ul class="points-list strengths">${strengths.map(s=>`<li>${s}</li>`).join("")}</ul>` : ""}
      ${improvements.length ? `<p style="font-size:13px;font-weight:600;color:var(--warning);margin:12px 0 6px">💡 Improvements</p><ul class="points-list improvements">${improvements.map(i=>`<li>${i}</li>`).join("")}</ul>` : ""}
      ${starAnalysis ? `<p style="font-size:13px;color:var(--text2);margin-top:12px"><strong>STAR:</strong> ${starAnalysis}</p>` : ""}
      ${followUp ? `<div style="background:var(--bg);border-radius:8px;padding:12px;margin-top:14px;font-size:13px;color:var(--accent)">🔄 Follow-up: ${followUp}</div>` : ""}
    </div>`;
  area.classList.remove("hidden");
}

function nextQuestion() {
  state.currentIndex++;
  if (state.currentIndex >= state.questions.length) {
    finishInterview();
  } else {
    renderQuestion();
  }
}

// ── Finish & Report ────────────────────────────────────────────────────────────
async function finishInterview() {
  stopTimer();
  stopRecording();
  if (state.stream) {
    try {
      state.stream.getTracks().forEach(track => track.stop());
    } catch (e) {}
    state.stream = null;
  }
  showLoader("Generating your final report...");
  try {
    const data = await API.post("/api/interview/finish", { session_id: state.sessionId });
    showPanel("report-panel");
    renderReport(data);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    hideLoader();
  }
}

function renderReport(data) {
  const { grade, avg_score, total_score, total_questions, report, role, difficulty } = data;
  const gradeInfo = gradeLabel(avg_score);

  document.getElementById("report-container").innerHTML = `
    <div class="report-card card fade-in" style="overflow:hidden">
      <div class="report-header">
        <div class="report-grade">${grade}</div>
        <div class="report-score">${avg_score.toFixed(1)} / 10 Average</div>
        <p style="opacity:0.85;margin-top:8px">${gradeInfo.label} • ${role} • ${difficulty}</p>
      </div>
      <div style="padding:24px">
        <div class="grid-3" style="margin-bottom:24px">
          <div class="stat-card"><div class="stat-value">${total_questions}</div><div class="stat-label">Questions</div></div>
          <div class="stat-card"><div class="stat-value" style="font-size:28px">${total_score.toFixed(1)}</div><div class="stat-label">Total Score</div></div>
          <div class="stat-card"><div class="stat-value" style="color:${gradeInfo.color};-webkit-text-fill-color:${gradeInfo.color}">${gradeInfo.label}</div><div class="stat-label">Rating</div></div>
        </div>
        <div class="section-title">📝 Detailed Breakdown</div>
        ${report.map(q => renderQResult(q)).join("")}
        <div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap">
          <button class="btn btn-primary btn-lg" onclick="location.reload()">🔄 New Interview</button>
          <button class="btn btn-secondary btn-lg" onclick="window.location.href='dashboard.html'">📊 Dashboard</button>
          <button class="btn btn-secondary btn-lg" onclick="window.location.href='mentor.html'">🧭 Career Mentor</button>
        </div>
      </div>
    </div>`;
}

function renderQResult(q) {
  const color = scoreColor(q.score);
  const strengths = Array.isArray(q.strengths) ? q.strengths : [];
  const improvements = Array.isArray(q.improvements) ? q.improvements : [];
  return `
    <div class="q-result-card">
      <div class="q-result-header">
        <span class="badge ${q.question_type==="behavioral"?"badge-warning":"badge-primary"}">${q.question_type}</span>
        <span class="score-pill" style="background:${color}22;color:${color}">${q.score}/10</span>
      </div>
      <p style="font-weight:600;margin-bottom:8px;font-size:15px">${q.question}</p>
      <p style="font-size:13px;color:var(--text2);background:var(--bg);padding:10px;border-radius:6px;margin-bottom:10px">${q.feedback}</p>
      ${strengths.length ? `<ul class="points-list strengths">${strengths.map(s=>`<li>${s}</li>`).join("")}</ul>` : ""}
      ${improvements.length ? `<ul class="points-list improvements" style="margin-top:6px">${improvements.map(i=>`<li>${i}</li>`).join("")}</ul>` : ""}
    </div>`;
}

// ── Panel Switching ────────────────────────────────────────────────────────────
function showPanel(id) {
  document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
  document.getElementById(id)?.classList.remove("hidden");
}

// ── TTS ───────────────────────────────────────────────────────────────────────
function speakText(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.95; utter.pitch = 1;
  window.speechSynthesis.speak(utter);
}

// ── STT ───────────────────────────────────────────────────────────────────────
function initVoice() {
  if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  state.recognition = new SR();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.lang = "en-US";

  state.recognition.onresult = (e) => {
    let transcript = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      transcript += e.results[i][0].transcript;
    }
    const ta = document.getElementById("answer-input");
    if (ta) ta.value = transcript;
  };

  state.recognition.onerror = () => {
    showToast("Voice recognition error. Try typing instead.", "warning");
    stopRecording();
  };
}

function toggleRecording() {
  if (state.isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

function startRecording() {
  if (!state.recognition) { showToast("Speech recognition not supported.", "warning"); return; }
  state.recognition.start();
  state.isRecording = true;
  document.getElementById("voice-btn")?.classList.add("recording");
  document.getElementById("voice-btn-text")?.textContent && (document.getElementById("voice-btn-text").textContent = "Stop");
  showToast("🎤 Listening... Speak your answer", "info");
}

function stopRecording() {
  state.recognition?.stop();
  state.isRecording = false;
  document.getElementById("voice-btn")?.classList.remove("recording");
  if (document.getElementById("voice-btn-text")) document.getElementById("voice-btn-text").textContent = "Voice";
}

// ── Webcam ────────────────────────────────────────────────────────────────────
async function initWebcam() {
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = document.getElementById("webcam-video");
    if (video) { video.srcObject = state.stream; video.play(); }
    document.getElementById("webcam-status")?.textContent && (document.getElementById("webcam-status").textContent = "📷 Camera active");
  } catch {
    const el = document.getElementById("webcam-box");
    if (el) el.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text3);font-size:14px;text-align:center;padding:16px">Camera not available</div>`;
  }
}

// ── Expose globals ─────────────────────────────────────────────────────────────
window.startInterview = startInterview;
window.submitAnswer = submitAnswer;
window.nextQuestion = nextQuestion;
window.finishInterview = finishInterview;
window.toggleRecording = toggleRecording;
window.speakText = speakText;
