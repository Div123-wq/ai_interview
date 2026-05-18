import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from backend.models.database import init_db
from backend.routes.auth import auth_bp
from backend.routes.interview import interview_bp
from backend.routes.mentor import mentor_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    # ── Config ──────────────────────────────────────────────────────────────
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False   # tokens don't expire in dev
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit

    # ── Extensions ──────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True)
    JWTManager(app)

    # ── Blueprints ───────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp,      url_prefix="/api/auth")
    app.register_blueprint(interview_bp, url_prefix="/api/interview")
    app.register_blueprint(mentor_bp,    url_prefix="/api/mentor")

    # ── Root & Health Check ────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return jsonify({
            "status": "ok",
            "message": "AI Interview Coach backend is running.",
            "health_check": "/api/health"
        }), 200

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "AI Interview Coach API is running!"}), 200

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large. Maximum size is 10MB."}), 413

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error.", "details": str(e)}), 500

    return app


# Expose the Flask app for deployment targets that expect a top-level app variable.
app = create_app()


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized.")
    print("🚀 Starting AI Interview Coach API on http://localhost:5000")
    print("📋 API Endpoints:")
    print("   POST /api/auth/register")
    print("   POST /api/auth/login")
    print("   GET  /api/auth/profile")
    print("   POST /api/interview/start")
    print("   POST /api/interview/answer")
    print("   POST /api/interview/finish")
    print("   GET  /api/interview/history")
    print("   POST /api/mentor/chat")
    print("   POST /api/mentor/skill-gap")
    print("   POST /api/mentor/roadmap")
    print("   GET  /api/mentor/insights")
    print("   POST /api/mentor/resume")
    print("   POST /api/mentor/linkedin-tips")
    app.run(debug=True, host="0.0.0.0", port=5000)
