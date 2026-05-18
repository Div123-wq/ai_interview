import sys
import traceback

try:
    from backend.app import create_app
    
    # Create and export the Flask app for Vercel
    app = create_app()
    application = app  # Some WSGI servers look for `application`
    
except Exception as e:
    # Log initialization error
    print(f"ERROR initializing Flask app: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    
    # Create a minimal fallback app that returns an error
    from flask import Flask, jsonify
    app = Flask(__name__)
    application = app
    
    @app.route("/")
    def error():
        return jsonify({"error": "App initialization failed", "details": str(e)}), 500
    
    @app.route("/api/health")
    def health():
        return jsonify({"error": "App initialization failed"}), 500

if __name__ == "__main__":
    from backend.models.database import init_db
    init_db()
    app.run()
