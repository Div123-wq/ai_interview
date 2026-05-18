import os
import json
import re
import google.generativeai as genai
import requests
from dotenv import load_dotenv

load_dotenv()

# Support either Google Gemini or GitHub Models via env vars.
# If `GITHUB_MODELS_KEY` is present we will prefer that and use
# a lightweight requests-based call to the GitHub Models endpoint.
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GITHUB_KEY = os.getenv("GITHUB_MODELS_KEY", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "github-code")

if GITHUB_KEY:
    PROVIDER = "github"
else:
    PROVIDER = "gemini"
    genai.configure(api_key=GEMINI_KEY)
    _model = genai.GenerativeModel("gemini-2.5-flash")

def _call(prompt: str, json_output: bool = False) -> str:
    try:
        # Use GitHub Models API if configured
        if PROVIDER == "github":
            headers = {
                "Authorization": f"Bearer {GITHUB_KEY}",
                "Content-Type": "application/json"
            }
            # Use OpenAI-compatible endpoint (Azure Models Inference)
            payload = {
                "model": GITHUB_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2048
            }
            try:
                r = requests.post("https://models.inference.ai.azure.com/chat/completions", headers=headers, json=payload, timeout=30)
                r.raise_for_status()
                body = r.json()
                # Parse OpenAI-compatible response format
                if isinstance(body, dict):
                    if "choices" in body and isinstance(body["choices"], list) and body["choices"]:
                        choice = body["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            text = choice["message"]["content"]
                        elif "text" in choice:
                            text = choice["text"]
                        else:
                            text = str(choice)
                    else:
                        text = json.dumps(body)
                else:
                    text = str(body)
            except Exception as e:
                raise
        else:
            response = _model.generate_content(prompt)
            text = response.text.strip()
        if json_output:
            # If wrapped in markdown code block, extract it
            match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()
            else:
                # Otherwise, try to find the outermost JSON structure
                start_array = text.find('[')
                start_obj = text.find('{')
                end_array = text.rfind(']')
                end_obj = text.rfind('}')
                
                start = start_array if start_array != -1 and (start_obj == -1 or start_array < start_obj) else start_obj
                end = end_array if end_array != -1 and (end_obj == -1 or end_array > end_obj) else end_obj
                
                if start != -1 and end != -1:
                    text = text[start:end+1]
        return text
    except Exception as e:
        error_msg = str(e)
        # Check for quota exceeded error
        if "429" in error_msg or "quota" in error_msg.lower():
            # Provide a provider-aware quota message
            if PROVIDER == "github":
                return json.dumps({"error": "API quota exceeded. Please check your GitHub Models plan and billing details."}) if json_output else "API quota exceeded. Please check your GitHub Models plan."
            else:
                return json.dumps({"error": "API quota exceeded. Please check your Gemini API plan and billing details at https://ai.google.dev/pricing"}) if json_output else "API quota exceeded. Please upgrade your Gemini API plan."
        return json.dumps({"error": str(e)}) if json_output else f"Error: {e}"

# ─── Fallback Questions (when API fails) ────────────────────────────────────

def get_fallback_questions(role: str, difficulty: str, interview_type: str, count: int = 5) -> list:
    """Provide quality fallback questions when API is unavailable"""
    fallback_db = {
        "Software Engineer": {
            "technical": [
                {"question": "Explain the difference between SQL and NoSQL databases. When would you use each?", "type": "technical", "hint": "Discuss ACID properties, scalability, use cases (e.g., MongoDB vs PostgreSQL)"},
                {"question": "How would you design a system to handle 1 million requests per second?", "type": "technical", "hint": "Consider load balancing, caching, database sharding, microservices"},
                {"question": "What is the time and space complexity of binary search? Why is it faster than linear search?", "type": "technical", "hint": "O(log n) time, divide-and-conquer approach, sorted array requirement"},
                {"question": "Explain the concept of RESTful APIs. What are the main HTTP methods and when to use each?", "type": "technical", "hint": "GET, POST, PUT, DELETE, PATCH - idempotency, caching, security"},
                {"question": "How do you optimize a slow database query? What techniques would you use?", "type": "technical", "hint": "Indexing, query optimization, explain plans, denormalization"},
            ],
            "behavioral": [
                {"question": "Tell me about a time you failed in a project. How did you handle it?", "type": "behavioral", "hint": "Use STAR method - Situation, Task, Action, Result. Show learning and growth."},
                {"question": "Describe a situation where you had to work with a difficult team member. How did you resolve it?", "type": "behavioral", "hint": "Communication, empathy, problem-solving skills"},
                {"question": "Tell me about your greatest achievement in your career.", "type": "behavioral", "hint": "Be specific, quantifiable, and show impact on the team/company"},
                {"question": "How do you stay updated with new technologies and trends?", "type": "behavioral", "hint": "Blogs, conferences, courses, side projects, community"},
                {"question": "Tell me about a time you had to learn something completely new to complete a task.", "type": "behavioral", "hint": "Learning ability, problem-solving, determination"},
            ]
        },
        "Data Analyst": {
            "technical": [
                {"question": "Write a SQL query to find the top 5 customers by revenue in the last 12 months.", "type": "technical", "hint": "JOIN, GROUP BY, ORDER BY, WHERE with date filters"},
                {"question": "How would you handle missing values in a dataset?", "type": "technical", "hint": "Deletion, imputation, prediction models, domain knowledge"},
                {"question": "Explain what A/B testing is and how you would design one for an e-commerce website.", "type": "technical", "hint": "Hypothesis, sample size, statistical significance, control groups"},
                {"question": "What is the difference between correlation and causation?", "type": "technical", "hint": "Examples, confounding variables, why it matters"},
                {"question": "How would you identify outliers in a dataset and what would you do with them?", "type": "technical", "hint": "Statistical methods, visualization, domain context"},
            ],
            "behavioral": [
                {"question": "Tell me about a time you had to present complex data to a non-technical audience.", "type": "behavioral", "hint": "Simplification, visualization, storytelling"},
                {"question": "Describe a project where your analysis led to an important business decision.", "type": "behavioral", "hint": "Impact, communication, actionable insights"},
                {"question": "How do you ensure data quality and accuracy in your analysis?", "type": "behavioral", "hint": "Validation, testing, documentation, verification"},
                {"question": "Tell me about a time you discovered something unexpected in the data.", "type": "behavioral", "hint": "Curiosity, investigation, impact"},
                {"question": "How do you prioritize multiple analysis requests with limited time?", "type": "behavioral", "hint": "Prioritization, communication, time management"},
            ]
        },
        "Product Manager": {
            "technical": [
                {"question": "Walk me through how you would approach building a new feature for a mobile app.", "type": "technical", "hint": "User research, market analysis, MVP, metrics"},
                {"question": "How would you measure the success of a new product feature?", "type": "technical", "hint": "KPIs, metrics, user engagement, business impact"},
                {"question": "Explain the product development lifecycle and your role in each phase.", "type": "technical", "hint": "Discovery, design, development, launch, iteration"},
                {"question": "How do you prioritize features when you have more ideas than engineering capacity?", "type": "technical", "hint": "Impact vs effort matrix, user feedback, business goals"},
                {"question": "Tell me about a product you've launched and how you iterated based on user feedback.", "type": "technical", "hint": "Data-driven decisions, user research, agility"},
            ],
            "behavioral": [
                {"question": "Tell me about a time you disagreed with a stakeholder. How did you handle it?", "type": "behavioral", "hint": "Diplomacy, data-driven arguments, consensus building"},
                {"question": "Describe a time when you had to pivot your product strategy.", "type": "behavioral", "hint": "Adaptability, learning, impact"},
                {"question": "How do you gather and incorporate user feedback into your product decisions?", "type": "behavioral", "hint": "Customer research, user interviews, analytics"},
                {"question": "Tell me about a product failure you experienced and what you learned from it.", "type": "behavioral", "hint": "Resilience, learning, accountability"},
                {"question": "How do you stay aligned with engineering and design teams?", "type": "behavioral", "hint": "Communication, collaboration, empathy"},
            ]
        }
    }
    
    # Get questions for the role, or use Software Engineer as default
    questions_pool = fallback_db.get(role, fallback_db.get("Software Engineer", {}))
    
    # Determine which question types to use
    if interview_type == "technical":
        pool = questions_pool.get("technical", [])
    elif interview_type == "behavioral":
        pool = questions_pool.get("behavioral", [])
    else:  # mixed
        pool = questions_pool.get("technical", []) + questions_pool.get("behavioral", [])
    
    # Return the requested number of questions, cycling if needed
    result = []
    for i in range(min(count, len(pool))):
        result.append(pool[i])
    
    # If we need more questions than available, cycle through
    while len(result) < count and pool:
        result.append(pool[len(result) % len(pool)])
    
    return result or [{"question": f"Tell me about your experience with {role}.", "type": "behavioral", "hint": "Share specific projects and skills"}]

# ─── Question Generation ───────────────────────────────────────────────────────

def generate_questions(role: str, difficulty: str, interview_type: str, count: int = 5) -> list:
    prompt = f"""You are an expert interviewer at a top tech company.
Generate exactly {count} interview questions for a {difficulty}-level {role} position.
Interview type: {interview_type}.

Rules:
- Technical: coding, system design, domain knowledge
- Behavioral: STAR-method situational questions
- Mixed: alternate between technical and behavioral
- Increase difficulty progressively

Return ONLY a valid JSON array (no extra text):
[
  {{"question": "...", "type": "technical|behavioral", "hint": "Key points to cover: ..."}},
  ...
]"""
    raw = _call(prompt, json_output=True)
    try:
        result = json.loads(raw)
        if isinstance(result, dict):
            if "questions" in result:
                return result["questions"]
            else:
                raise ValueError("Expected list but got dict")
        return result
    except Exception:
        # API failed or quota exceeded - return high-quality fallback questions
        return get_fallback_questions(role, difficulty, interview_type, count)

# ─── Answer Evaluation ────────────────────────────────────────────────────────

def evaluate_answer(role: str, difficulty: str, question: str, q_type: str, user_answer: str, time_taken: int) -> dict:
    if not user_answer or len(user_answer.strip()) < 5:
        return {
            "score": 0, "feedback": "No answer was provided. Practice responding even with partial knowledge.",
            "strengths": [], "improvements": ["Provide a complete answer to the question."],
            "follow_up": f"Let's retry: {question}", "confidence": "low", "star_analysis": ""
        }

    time_note = ""
    if time_taken < 15:
        time_note = "Very brief response (under 15 seconds). Needs elaboration. "
    elif time_taken > 360:
        time_note = "Very long response (over 6 minutes). Focus on conciseness. "

    prompt = f"""You are a senior {role} interviewer evaluating a candidate.

Question: {question}
Type: {q_type} | Difficulty: {difficulty}
Answer: {user_answer}
Time: {time_taken}s. {time_note}

Return ONLY valid JSON (no extra text):
{{
  "score": <0-10>,
  "feedback": "<2-3 sentence overall assessment>",
  "strengths": ["<point 1>", "<point 2>"],
  "improvements": ["<point 1>", "<point 2>"],
  "follow_up": "<one targeted follow-up question>",
  "confidence": "low|medium|high",
  "star_analysis": "<STAR breakdown if behavioral, else empty string>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        result = json.loads(raw)
        result["score"] = max(0.0, min(10.0, float(result.get("score", 5))))
        return result
    except Exception:
        return {
            "score": 5.0, "feedback": "Answer received. Keep practicing for deeper feedback.",
            "strengths": ["Attempted the question"], "improvements": ["Provide more structure and depth"],
            "follow_up": "Can you elaborate on that point?", "confidence": "medium", "star_analysis": ""
        }

# ─── Mentor Chat ──────────────────────────────────────────────────────────────

def mentor_chat(user_message: str, history: list, user_profile: dict) -> str:
    profile = f"""User: {user_profile.get('name','Student')} | Skills: {user_profile.get('skills','N/A')} | Experience: {user_profile.get('experience','fresher')} | Target: {user_profile.get('target_role','Software Engineer')}"""
    system = f"""You are an expert AI Career Mentor with 15+ years of tech hiring experience.
{profile}
Provide specific, actionable career advice. Use bullet points for lists. Be warm and encouraging."""

    history_text = "\n".join([f"{'User' if m['role']=='user' else 'Mentor'}: {m['content']}" for m in history[-10:]])
    prompt = f"{system}\n\nHistory:\n{history_text}\n\nUser: {user_message}\nMentor:"
    response = _call(prompt)
    
    # If API quota exceeded, return fallback response
    if "quota" in response.lower() or "error" in response.lower():
        return f"""I appreciate your question! Due to API quota limits, I'm currently unable to provide personalized advice.

However, here are some general tips:
- **For Certifications:** AWS, GCP, Azure, Kubernetes, and specialized certs (AWS Solutions Architect, CKA) boost your profile
- **For Interviews:** Practice DSA, system design, and behavioral questions
- **For Growth:** Contribute to open source, write technical blogs, and build side projects
- **For Networking:** LinkedIn outreach, tech conferences, and community engagement

Please check back later when the API is available for more personalized guidance!"""
    
    return response

# ─── Skill Gap Analysis ───────────────────────────────────────────────────────

def analyze_skill_gap(current_skills: str, target_role: str, experience: str) -> dict:
    prompt = f"""Analyze skill gap for:
- Skills: {current_skills}
- Target Role: {target_role}
- Experience: {experience}

Return ONLY valid JSON:
{{
  "required_skills": ["s1","s2","s3","s4","s5"],
  "present_skills": ["s1","s2"],
  "missing_skills": ["s1","s2","s3"],
  "gap_score": <0-100>,
  "priority_skills": [
    {{"skill":"...","importance":"critical|high|medium","time_to_learn":"...","resources":["r1","r2"]}}
  ],
  "summary": "<2-3 sentence readiness assessment>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not analyze skill gap. Please try again."}

# ─── Learning Roadmap ─────────────────────────────────────────────────────────

def generate_roadmap(target_role: str, missing_skills: list, experience: str, weeks: int = 8) -> dict:
    skills_str = ", ".join(missing_skills) if missing_skills else "core fundamentals"
    prompt = f"""Create a {weeks}-week learning roadmap for {experience} targeting {target_role}.
Focus skills: {skills_str}

Return ONLY valid JSON:
{{
  "title": "...",
  "total_weeks": {weeks},
  "weekly_hours": <number>,
  "weeks": [
    {{
      "week": 1,
      "theme": "...",
      "topics": ["t1","t2"],
      "resources": [{{"name":"...","type":"course|book|practice|video","url_hint":"..."}}],
      "project": "...",
      "milestone": "..."
    }}
  ],
  "certifications": ["c1","c2"],
  "final_goal": "..."
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not generate roadmap. Please try again."}

# ─── Industry Insights ────────────────────────────────────────────────────────

def get_industry_insights(role: str) -> dict:
    prompt = f"""Provide 2024-2025 industry insights for: {role}

Return ONLY valid JSON:
{{
  "role": "{role}",
  "demand_level": "high|medium|low",
  "avg_salary": {{"fresher": "...","mid": "...","senior": "..."}},
  "top_companies": ["c1","c2","c3","c4","c5"],
  "in_demand_skills": ["s1","s2","s3","s4","s5"],
  "emerging_trends": ["t1","t2","t3"],
  "interview_topics": ["t1","t2","t3","t4"],
  "career_paths": ["p1","p2","p3"],
  "remote_friendly": true,
  "growth_rate": "...",
  "job_market_summary": "<2-3 sentences>"
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not fetch insights. Please try again."}

# ─── Resume Review ────────────────────────────────────────────────────────────

def review_resume(resume_text: str, target_role: str) -> dict:
    prompt = f"""You are an ATS expert and senior recruiter. Review this resume for {target_role}:

{resume_text[:3000]}

Return ONLY valid JSON:
{{
  "ats_score": <0-100>,
  "overall_rating": "excellent|good|average|needs_improvement",
  "strengths": ["s1","s2","s3"],
  "weaknesses": ["w1","w2","w3"],
  "missing_keywords": ["k1","k2","k3"],
  "suggestions": [{{"section":"Summary|Experience|Skills|Education|Format","suggestion":"..."}}],
  "linkedin_tips": ["t1","t2","t3"],
  "action_items": ["a1","a2","a3"]
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not analyze resume. Please try again."}

# ─── Job Search Strategy ──────────────────────────────────────────────────────

def get_job_search_strategy(role: str, experience: str, skills: str) -> dict:
    prompt = f"""Job search strategy for {experience} targeting {role} with skills: {skills}

Return ONLY valid JSON:
{{
  "platforms": [{{"name":"...","strategy":"...","priority":"high|medium|low"}}],
  "networking_tips": ["t1","t2","t3"],
  "cold_outreach_template": "...",
  "application_tips": ["t1","t2","t3"],
  "weekly_action_plan": ["a1","a2","a3","a4","a5"],
  "dos_and_donts": {{"dos":["d1","d2","d3"],"donts":["d1","d2","d3"]}}
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not generate strategy."}

# ─── Interview Prep Schedule ──────────────────────────────────────────────────

def generate_prep_schedule(role: str, interview_date: str, current_skills: str) -> dict:
    prompt = f"""Interview prep schedule for {role}, interview on {interview_date}, current skills: {current_skills}

Return ONLY valid JSON:
{{
  "total_days": <number>,
  "daily_hours": <number>,
  "phases": [
    {{
      "phase": "...",
      "days": "Day 1-X",
      "focus": "...",
      "daily_tasks": ["t1","t2"],
      "resources": ["r1","r2"]
    }}
  ],
  "mock_interview_schedule": ["Day X: ..."],
  "revision_strategy": "...",
  "day_before_tips": ["t1","t2","t3"],
  "interview_day_tips": ["t1","t2","t3"]
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not generate prep schedule."}

# ─── LinkedIn Tips ────────────────────────────────────────────────────────────

def get_linkedin_tips(role: str, skills: str, experience: str) -> dict:
    prompt = f"""LinkedIn profile optimization tips for {experience} targeting {role} with skills: {skills}

Return ONLY valid JSON:
{{
  "headline_examples": ["h1","h2","h3"],
  "summary_tips": ["t1","t2","t3"],
  "skills_to_add": ["s1","s2","s3","s4","s5"],
  "connection_strategy": ["c1","c2","c3"],
  "content_ideas": ["i1","i2","i3"],
  "profile_checklist": [{{"item":"...","importance":"high|medium"}}],
  "keywords_to_include": ["k1","k2","k3","k4","k5"]
}}"""
    raw = _call(prompt, json_output=True)
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Could not generate LinkedIn tips."}
