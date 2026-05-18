from backend.app import app

# Some deployment platforms expect a top-level Flask app variable named `app`.
# This file re-exports the app created in backend/app.py.
application = app

if __name__ == "__main__":
    from backend.models.database import init_db
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
