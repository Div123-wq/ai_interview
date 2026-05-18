from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.database import (
    create_session, get_session, save_question_answer,
    finish_session, get_session_questions, get_user_sessions, get_user_stats
)
from backend.services.ai_engine import generate_questions, evaluate_answer
import json
import os

interview_bp = Blueprint("interview", __name__)

# ─── Start Session ─────────────────────────────────────────────────────────────

@interview_bp.route("/start", methods=["POST"])
@jwt_required()
def start_interview():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    role = data.get("role", "Software Engineer")
    difficulty = data.get("difficulty", "intermediate")
    interview_type = data.get("interview_type", "mixed")
    total_questions = int(data.get("total_questions", 5))
    total_questions = max(3, min(10, total_questions))

    questions = generate_questions(role, difficulty, interview_type, total_questions)
    session_id = create_session(user_id, role, difficulty, interview_type, total_questions)

    return jsonify({
        "session_id": session_id,
        "questions": questions,
        "total_questions": total_questions,
        "role": role,
        "difficulty": difficulty,
        "interview_type": interview_type
    }), 201

# ─── Submit Answer ─────────────────────────────────────────────────────────────

@interview_bp.route("/answer", methods=["POST"])
@jwt_required()
def submit_answer():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    session_id = data.get("session_id")
    question_number = data.get("question_number", 1)
    question = data.get("question", "")
    question_type = data.get("question_type", "technical")
    user_answer = data.get("answer", "")
    time_taken = int(data.get("time_taken", 0))

    session = get_session(session_id)
    if not session or session["user_id"] != user_id:
        return jsonify({"error": "Session not found."}), 404

    evaluation = evaluate_answer(
        session["role"], session["difficulty"],
        question, question_type, user_answer, time_taken
    )

    # Handle optional webcam image (base64) sent from frontend
    webcam_b64 = data.get("webcam_image")
    webcam_path = ""
    if webcam_b64:
        try:
            # Expect data URI like 'data:image/png;base64,....'
            header, b64 = webcam_b64.split(',', 1) if ',' in webcam_b64 else (None, webcam_b64)
            import base64, uuid
            img_data = base64.b64decode(b64)
            uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filename = f"webcam_{session_id}_{question_number}_{uuid.uuid4().hex}.png"
            path = os.path.join(uploads_dir, filename)
            with open(path, 'wb') as f:
                f.write(img_data)
            webcam_path = path
        except Exception:
            webcam_path = ""

    # Determine confidence: prefer evaluation field, otherwise map from score
    confidence = evaluation.get('confidence') if isinstance(evaluation.get('confidence'), str) else None
    try:
        if not confidence:
            sc = float(evaluation.get('score', 0))
            if sc >= 8: confidence = 'high'
            elif sc >= 5: confidence = 'medium'
            else: confidence = 'low'
    except Exception:
        confidence = 'medium'

    save_question_answer(
        session_id, question_number, question, question_type,
        user_answer,
        evaluation.get("feedback", ""),
        evaluation.get("score", 0),
        json.dumps(evaluation.get("strengths", [])),
        json.dumps(evaluation.get("improvements", [])),
        evaluation.get("follow_up", ""),
        time_taken,
        confidence,
        webcam_path
    )

    return jsonify({
        "evaluation": evaluation,
        "question_number": question_number
    }), 200

# ─── Finish Session ────────────────────────────────────────────────────────────

@interview_bp.route("/finish", methods=["POST"])
@jwt_required()
def finish_interview():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    session_id = data.get("session_id")

    session = get_session(session_id)
    if not session or session["user_id"] != user_id:
        return jsonify({"error": "Session not found."}), 404

    questions = get_session_questions(session_id)
    if not questions:
        return jsonify({"error": "No questions found for this session."}), 400

    scores = [q["score"] for q in questions]
    total_score = sum(scores)
    avg_score = total_score / len(scores) if scores else 0
    completed = len(questions)

    finish_session(session_id, total_score, round(avg_score, 2), completed)

    # Build report
    report = []
    for q in questions:
        try:
            strengths = json.loads(q.get("strengths", "[]"))
            improvements = json.loads(q.get("improvements", "[]"))
        except Exception:
            strengths = []
            improvements = []
        report.append({
            "question_number": q["question_number"],
            "question": q["question"],
            "question_type": q["question_type"],
            "answer": q["user_answer"],
            "score": q["score"],
            "feedback": q["ai_feedback"],
            "strengths": strengths,
            "improvements": improvements,
            "follow_up": q["follow_up"],
            "time_taken": q["time_taken"]
        })

    grade = "A" if avg_score >= 8 else "B" if avg_score >= 6 else "C" if avg_score >= 4 else "D"
    return jsonify({
        "session_id": session_id,
        "total_questions": completed,
        "total_score": round(total_score, 2),
        "avg_score": round(avg_score, 2),
        "grade": grade,
        "report": report,
        "role": session["role"],
        "difficulty": session["difficulty"],
        "interview_type": session["interview_type"]
    }), 200

# ─── Session Report ────────────────────────────────────────────────────────────

@interview_bp.route("/session/<int:session_id>", methods=["GET"])
@jwt_required()
def get_session_report(session_id):
    user_id = int(get_jwt_identity())
    session = get_session(session_id)
    if not session or session["user_id"] != user_id:
        return jsonify({"error": "Session not found."}), 404
    questions = get_session_questions(session_id)
    return jsonify({"session": session, "questions": questions}), 200

# ─── History & Stats ───────────────────────────────────────────────────────────

@interview_bp.route("/history", methods=["GET"])
@jwt_required()
def interview_history():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get("limit", 10))
    sessions = get_user_sessions(user_id, limit)
    return jsonify({"sessions": sessions}), 200

@interview_bp.route("/stats", methods=["GET"])
@jwt_required()
def interview_stats():
    user_id = int(get_jwt_identity())
    stats = get_user_stats(user_id)
    return jsonify(stats), 200
