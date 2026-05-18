from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models.database import create_user, get_user_by_email, get_user_by_id, update_user_profile

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    skills = data.get("skills", "")
    experience = data.get("experience", "fresher")
    target_role = data.get("target_role", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    password_hash = generate_password_hash(password)
    success = create_user(name, email, password_hash, skills, experience, target_role)
    if not success:
        return jsonify({"error": "Email already registered. Please login."}), 409

    user = get_user_by_email(email)
    token = create_access_token(identity=str(user["id"]))
    return jsonify({
        "message": "Account created successfully!",
        "token": token,
        "user": {
            "id": user["id"], "name": user["name"], "email": user["email"],
            "skills": user["skills"], "experience": user["experience"],
            "target_role": user["target_role"]
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    token = create_access_token(identity=str(user["id"]))
    return jsonify({
        "message": "Login successful!",
        "token": token,
        "user": {
            "id": user["id"], "name": user["name"], "email": user["email"],
            "skills": user["skills"], "experience": user["experience"],
            "target_role": user["target_role"]
        }
    }), 200

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    user.pop("password_hash", None)
    return jsonify(user), 200

@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    skills = data.get("skills", "")
    experience = data.get("experience", "fresher")
    target_role = data.get("target_role", "")
    update_user_profile(user_id, skills, experience, target_role)
    return jsonify({"message": "Profile updated successfully!"}), 200
