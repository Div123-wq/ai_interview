from backend.app import create_app

# Create and export the Flask app for Vercel
app = create_app()
application = app

if __name__ == "__main__":
    from backend.models.database import init_db
    init_db()
    app.run()
