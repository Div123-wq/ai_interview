import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_model = genai.GenerativeModel("gemini-2.5-flash")

def _call(prompt: str, json_output: bool = False) -> str:
    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        if json_output:
            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return text
    except Exception as e:
        if json_output:
            return json.dumps({"error": str(e)})
        return f"I'm experiencing a technical issue. Please try again. ({e})"

# ─── Interview Question Generation ────────────────────────────────────────────

def generate_questions(role: str, difficulty: str, interview_type: str, count: int = 5) -> list:
    prompt = f"""You are an expert interviewer at a top tech company.
Generate exactly {count} interview questions for a {difficulty}-level {role} position.
Interview type: {interview_type} (technical/behavioral/mixed).

Rules:
- For technical: include coding concepts, system design, or domain-specific knowledge
- For behavioral: use STAR-method scenarios
- For mixed: alternate between technical and behavioral
- Vary question difficulty progressively
- Return ONLY a JSON array like:
[
  {{"question": "...", "type": "technical", "hint": "Key concepts to cover: ..."}},
  ...
]
No extra text outside the JSON."""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return [{"question": f"Tell me about your experience with {role}.", "type": "behavioral", "hint": "Be specific with examples."}]

# ─── Answer Evaluation ────────────────────────────────────────────────────────

def evaluate_answer(role: str, difficulty: str, question: str, q_type: str, user_answer: str, time_taken: int) -> dict:
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            "score": 0, "feedback": "No answer was provided.",
            "strengths": [], "improvements": ["Provide a complete answer to the question."],
            "follow_up": f"Let's try again: {question}", "confidence": "low"
        }

    time_note = ""
    if time_taken < 20:
        time_note = "Answer was very brief (under 20 seconds). "
    elif time_taken > 300:
        time_note = "Answer was quite long (over 5 minutes). "

    prompt = f"""You are a senior {role} interviewer evaluating a candidate's answer.

Question: {question}
Question type: {q_type}
Difficulty: {difficulty}
Candidate's answer: {user_answer}
Time taken: {time_taken} seconds. {time_note}

Evaluate the answer and return ONLY this JSON (no extra text):
{{
  "score": <number 0-10>,
  "feedback": "<2-3 sentence overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"],
  "follow_up": "<one follow-up question based on their answer>",
  "confidence": "<low|medium|high based on answer quality>",
  "star_analysis": "<for behavioral: brief STAR method assessment, else empty string>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        result = json.loads(raw)
        result["score"] = max(0, min(10, float(result.get("score", 5))))
        return result
    except:
        return {
            "score": 5, "feedback": "Answer received. Keep practicing for more detailed feedback.",
            "strengths": ["Attempted the question"], "improvements": ["Provide more detail"],
            "follow_up": "Can you elaborate further?", "confidence": "medium", "star_analysis": ""
        }

# ─── Mentor Chat ──────────────────────────────────────────────────────────────

def mentor_chat(user_message: str, history: list, user_profile: dict) -> str:
    profile_context = f"""
User Profile:
- Name: {user_profile.get('name', 'Student')}
- Skills: {user_profile.get('skills', 'Not specified')}
- Experience: {user_profile.get('experience', 'Fresher')}
- Target Role: {user_profile.get('target_role', 'Software Engineer')}
"""
    system_prompt = f"""You are an expert AI Career Mentor and Coach with 15+ years of experience in tech hiring.
{profile_context}
Your role is to:
- Provide specific, actionable career advice
- Help with interview preparation strategies
- Guide on skill development and learning paths
- Share industry insights and salary benchmarks
- Be encouraging but realistic
- Give concrete examples and resources when relevant
Keep responses focused, warm, and professional. Use bullet points for clarity when listing items."""

    history_text = ""
    for msg in history[-10:]:
        role = "User" if msg["role"] == "user" else "Mentor"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"{system_prompt}\n\nConversation History:\n{history_text}\nUser: {user_message}\nMentor:"
    return _call(prompt)

# ─── Skill Gap Analysis ───────────────────────────────────────────────────────

def analyze_skill_gap(current_skills: str, target_role: str, experience: str) -> dict:
    prompt = f"""You are a senior tech hiring manager and career coach.
Analyze the skill gap for this candidate:
- Current Skills: {current_skills}
- Target Role: {target_role}
- Experience Level: {experience}

Return ONLY this JSON:
{{
  "required_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "present_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2", "skill3"],
  "gap_score": <0-100, where 100 means fully ready>,
  "priority_skills": [
    {{"skill": "...", "importance": "critical|high|medium", "time_to_learn": "...", "resources": ["resource1", "resource2"]}}
  ],
  "summary": "<2-3 sentence summary of the candidate's readiness>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not analyze skill gap. Please try again."}

# ─── Learning Roadmap ─────────────────────────────────────────────────────────

def generate_roadmap(target_role: str, missing_skills: list, experience: str, weeks: int = 8) -> dict:
    skills_str = ", ".join(missing_skills) if missing_skills else "general skills"
    prompt = f"""Create a detailed {weeks}-week learning roadmap for a {experience}-level candidate targeting a {target_role} role.
Focus on these missing skills: {skills_str}

Return ONLY this JSON:
{{
  "title": "...",
  "total_weeks": {weeks},
  "weekly_hours": <recommended hours per week>,
  "weeks": [
    {{
      "week": 1,
      "theme": "...",
      "topics": ["topic1", "topic2"],
      "resources": [{{"name": "...", "type": "course|book|practice|video", "url_hint": "..."}}],
      "project": "...",
      "milestone": "..."
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "final_goal": "..."
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not generate roadmap. Please try again."}

# ─── Industry Insights ────────────────────────────────────────────────────────

def get_industry_insights(role: str) -> dict:
    prompt = f"""Provide comprehensive industry insights for a {role} position in 2024-2025.

Return ONLY this JSON:
{{
  "role": "{role}",
  "demand_level": "high|medium|low",
  "avg_salary": {{"fresher": "...", "mid": "...", "senior": "..."}},
  "top_companies": ["company1", "company2", "company3", "company4", "company5"],
  "in_demand_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "emerging_trends": ["trend1", "trend2", "trend3"],
  "interview_topics": ["topic1", "topic2", "topic3", "topic4"],
  "career_paths": ["path1", "path2", "path3"],
  "remote_friendly": true,
  "growth_rate": "...",
  "job_market_summary": "<2-3 sentence market analysis>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not fetch industry insights. Please try again."}

# ─── Resume Review ────────────────────────────────────────────────────────────

def review_resume(resume_text: str, target_role: str) -> dict:
    prompt = f"""You are an ATS expert and senior recruiter. Review this resume for a {target_role} position.

Resume text:
{resume_text[:3000]}

Return ONLY this JSON:
{{
  "ats_score": <0-100>,
  "overall_rating": "excellent|good|average|needs_improvement",
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "missing_keywords": ["keyword1", "keyword2", "keyword3"],
  "suggestions": [
    {{"section": "Summary|Experience|Skills|Education|Format", "suggestion": "..."}}
  ],
  "linkedin_tips": ["tip1", "tip2", "tip3"],
  "action_items": ["item1", "item2", "item3"]
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not analyze resume. Please try again."}

# ─── Job Search Strategy ──────────────────────────────────────────────────────

def get_job_search_strategy(role: str, experience: str, skills: str) -> dict:
    prompt = f"""Create a comprehensive job search strategy for:
- Role: {role}
- Experience: {experience}
- Skills: {skills}

Return ONLY this JSON:
{{
  "platforms": [{{"name": "...", "strategy": "...", "priority": "high|medium|low"}}],
  "networking_tips": ["tip1", "tip2", "tip3"],
  "cold_outreach_template": "...",
  "application_tips": ["tip1", "tip2", "tip3"],
  "interview_prep_timeline": "...",
  "weekly_action_plan": ["action1", "action2", "action3", "action4", "action5"],
  "dos_and_donts": {{"dos": ["do1", "do2", "do3"], "donts": ["dont1", "dont2", "dont3"]}}
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not generate job search strategy."}

# ─── Interview Prep Schedule ──────────────────────────────────────────────────

def generate_prep_schedule(role: str, interview_date: str, current_skills: str) -> dict:
    prompt = f"""Create a personalized interview preparation schedule for:
- Role: {role}
- Interview Date: {interview_date}
- Current Skills: {current_skills}

Return ONLY this JSON:
{{
  "total_days": <number>,
  "daily_hours": <recommended hours>,
  "phases": [
    {{
      "phase": "Phase 1: Foundation",
      "days": "Day 1-X",
      "focus": "...",
      "daily_tasks": ["task1", "task2"],
      "resources": ["resource1", "resource2"]
    }}
  ],
  "mock_interview_schedule": ["Day X: ...", "Day Y: ..."],
  "revision_strategy": "...",
  "day_before_tips": ["tip1", "tip2", "tip3"],
  "interview_day_tips": ["tip1", "tip2", "tip3"]
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except:
        return {"error": "Could not generate prep schedule."}
