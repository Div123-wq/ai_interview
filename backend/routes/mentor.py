from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import (
    save_mentor_message, get_mentor_history, clear_mentor_history,
    get_user_by_id, create_goal, get_user_goals, update_goal_progress, delete_goal
)
from backend.services.ai_engine import (
    mentor_chat, analyze_skill_gap, generate_roadmap,
    get_industry_insights, review_resume, get_job_search_strategy,
    generate_prep_schedule, get_linkedin_tips
)
from backend.services.resume_parser import extract_text_from_file

mentor_bp = Blueprint("mentor", __name__)

# ─── Mentor Chat ──────────────────────────────────────────────────────────────

@mentor_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    user = get_user_by_id(user_id)
    history = get_mentor_history(user_id, limit=20)
    save_mentor_message(user_id, "user", user_message)

    response = mentor_chat(user_message, history, user or {})
    save_mentor_message(user_id, "assistant", response)

    return jsonify({"response": response}), 200

@mentor_bp.route("/chat/history", methods=["GET"])
@jwt_required()
def chat_history():
    user_id = int(get_jwt_identity())
    history = get_mentor_history(user_id, limit=50)
    return jsonify({"history": history}), 200

@mentor_bp.route("/chat/clear", methods=["DELETE"])
@jwt_required()
def clear_chat():
    user_id = int(get_jwt_identity())
    clear_mentor_history(user_id)
    return jsonify({"message": "Chat history cleared."}), 200

# ─── Skill Gap Analysis ───────────────────────────────────────────────────────

@mentor_bp.route("/skill-gap", methods=["POST"])
@jwt_required()
def skill_gap():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    current_skills = data.get("current_skills", "")
    target_role = data.get("target_role", "Software Engineer")
    experience = data.get("experience", "fresher")

    if not current_skills:
        user = get_user_by_id(user_id)
        if user:
            current_skills = user.get("skills", "")
            experience = user.get("experience", experience)

    result = analyze_skill_gap(current_skills, target_role, experience)
    return jsonify(result), 200

# ─── Learning Roadmap ─────────────────────────────────────────────────────────

@mentor_bp.route("/roadmap", methods=["POST"])
@jwt_required()
def roadmap():
    data = request.get_json()
    target_role = data.get("target_role", "Software Engineer")
    missing_skills = data.get("missing_skills", [])
    experience = data.get("experience", "fresher")
    weeks = int(data.get("weeks", 8))
    weeks = max(4, min(16, weeks))

    result = generate_roadmap(target_role, missing_skills, experience, weeks)
    return jsonify(result), 200

# ─── Industry Insights ────────────────────────────────────────────────────────

@mentor_bp.route("/insights", methods=["GET"])
@jwt_required()
def insights():
    role = request.args.get("role", "Software Engineer")
    result = get_industry_insights(role)
    return jsonify(result), 200

# ─── Resume Review ────────────────────────────────────────────────────────────

@mentor_bp.route("/resume", methods=["POST"])
@jwt_required()
def resume_review():
    data = request.get_json()
    resume_text = (data.get("resume_text") or "").strip()
    target_role = data.get("target_role", "Software Engineer")

    if not resume_text:
        return jsonify({"error": "Resume text is required."}), 400
    if len(resume_text) < 50:
        return jsonify({"error": "Resume text too short. Please paste your full resume."}), 400

    result = review_resume(resume_text, target_role)
    return jsonify(result), 200

@mentor_bp.route("/resume/upload", methods=["POST"])
@jwt_required()
def resume_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["file"]
    target_role = request.form.get("target_role", "Software Engineer")
    resume_text = extract_text_from_file(file)
    if not resume_text or len(resume_text) < 50:
        return jsonify({"error": "Could not extract text from file. Try pasting your resume instead."}), 400
    result = review_resume(resume_text, target_role)
    return jsonify(result), 200

# ─── Job Search Strategy ──────────────────────────────────────────────────────

@mentor_bp.route("/job-strategy", methods=["POST"])
@jwt_required()
def job_strategy():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    role = data.get("target_role", "Software Engineer")
    experience = data.get("experience", "fresher")
    skills = data.get("skills", "")

    if not skills:
        user = get_user_by_id(user_id)
        if user:
            skills = user.get("skills", "")
            experience = user.get("experience", experience)

    result = get_job_search_strategy(role, experience, skills)
    return jsonify(result), 200

# ─── Interview Prep Schedule ──────────────────────────────────────────────────

@mentor_bp.route("/prep-schedule", methods=["POST"])
@jwt_required()
def prep_schedule():
    data = request.get_json()
    role = data.get("role", "Software Engineer")
    interview_date = data.get("interview_date", "2 weeks from now")
    current_skills = data.get("current_skills", "")
    result = generate_prep_schedule(role, interview_date, current_skills)
    return jsonify(result), 200

# ─── LinkedIn Tips ────────────────────────────────────────────────────────────

@mentor_bp.route("/linkedin-tips", methods=["POST"])
@jwt_required()
def linkedin_tips():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    role = data.get("target_role", "Software Engineer")
    skills = data.get("skills", "")
    experience = data.get("experience", "fresher")

    if not skills:
        user = get_user_by_id(user_id)
        if user:
            skills = user.get("skills", "")
            experience = user.get("experience", experience)

    result = get_linkedin_tips(role, skills, experience)
    return jsonify(result), 200

# ─── Goals ────────────────────────────────────────────────────────────────────

@mentor_bp.route("/goals", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = int(get_jwt_identity())
    goals = get_user_goals(user_id)
    return jsonify({"goals": goals}), 200

@mentor_bp.route("/goals", methods=["POST"])
@jwt_required()
def add_goal():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = (data.get("title") or "").strip()
    description = data.get("description", "")
    target_date = data.get("target_date", "")
    if not title:
        return jsonify({"error": "Goal title is required."}), 400
    goal_id = create_goal(user_id, title, description, target_date)
    return jsonify({"goal_id": goal_id, "message": "Goal created!"}), 201

@mentor_bp.route("/goals/<int:goal_id>", methods=["PUT"])
@jwt_required()
def update_goal(goal_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    progress = int(data.get("progress", 0))
    status = data.get("status", "active")
    update_goal_progress(goal_id, user_id, progress, status)
    return jsonify({"message": "Goal updated!"}), 200

@mentor_bp.route("/goals/<int:goal_id>", methods=["DELETE"])
@jwt_required()
def remove_goal(goal_id):
    user_id = int(get_jwt_identity())
    delete_goal(goal_id, user_id)
    return jsonify({"message": "Goal deleted."}), 200
