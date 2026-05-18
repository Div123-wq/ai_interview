import sqlite3
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_PATH = DATABASE_URL
else:
    temp_dir = os.getenv("TMPDIR") or os.getenv("TEMP") or os.getenv("TMP") or "/tmp"
    if os.path.isdir(temp_dir):
        DATABASE_PATH = os.path.join(temp_dir, "interview.db")
    else:
        DATABASE_PATH = "interview.db"


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            skills TEXT DEFAULT '',
            experience TEXT DEFAULT 'fresher',
            target_role TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            interview_type TEXT NOT NULL,
            total_questions INTEGER DEFAULT 5,
            completed_questions INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0,
            avg_score REAL DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS session_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question TEXT NOT NULL,
            question_type TEXT DEFAULT 'technical',
            user_answer TEXT DEFAULT '',
            ai_feedback TEXT DEFAULT '',
            score REAL DEFAULT 0,
            strengths TEXT DEFAULT '',
            improvements TEXT DEFAULT '',
            follow_up TEXT DEFAULT '',
            time_taken INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS mentor_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'user',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            target_date TEXT,
            status TEXT DEFAULT 'active',
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    # Ensure new columns exist for confidence and webcam image path (migration-safe)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(session_questions)").fetchall()]
        if 'confidence' not in cols:
            conn.execute("ALTER TABLE session_questions ADD COLUMN confidence TEXT DEFAULT ''")
        if 'webcam_image_path' not in cols:
            conn.execute("ALTER TABLE session_questions ADD COLUMN webcam_image_path TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        # If PRAGMA or ALTER fails, ignore (best-effort migration)
        pass
    conn.close()

# ─── User Helpers ──────────────────────────────────────────────────────────────

def create_user(name, email, password_hash, skills="", experience="fresher", target_role=""):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, skills, experience, target_role) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, password_hash, skills, experience, target_role)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_profile(user_id, skills, experience, target_role):
    conn = get_db()
    conn.execute(
        "UPDATE users SET skills=?, experience=?, target_role=? WHERE id=?",
        (skills, experience, target_role, user_id)
    )
    conn.commit()
    conn.close()

# ─── Interview Session Helpers ─────────────────────────────────────────────────

def create_session(user_id, role, difficulty, interview_type, total_questions):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO interview_sessions (user_id, role, difficulty, interview_type, total_questions) VALUES (?, ?, ?, ?, ?)",
        (user_id, role, difficulty, interview_type, total_questions)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_session(session_id):
    conn = get_db()
    session = conn.execute("SELECT * FROM interview_sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return dict(session) if session else None

def save_question_answer(session_id, q_num, question, q_type, answer, feedback, score, strengths, improvements, follow_up, time_taken, confidence='', webcam_image_path=''):
    conn = get_db()
    conn.execute(
        """INSERT INTO session_questions
           (session_id, question_number, question, question_type, user_answer,
            ai_feedback, score, strengths, improvements, follow_up, time_taken, confidence, webcam_image_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, q_num, question, q_type, answer, feedback, score,
         str(strengths), str(improvements), follow_up, time_taken, confidence, webcam_image_path)
    )
    conn.commit()
    conn.close()

def finish_session(session_id, total_score, avg_score, completed):
    conn = get_db()
    conn.execute(
        "UPDATE interview_sessions SET status='completed', total_score=?, avg_score=?, completed_questions=?, completed_at=? WHERE id=?",
        (total_score, avg_score, completed, datetime.utcnow().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

def get_session_questions(session_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM session_questions WHERE session_id=? ORDER BY question_number", (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_sessions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM interview_sessions WHERE user_id=? ORDER BY started_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_stats(user_id):
    conn = get_db()
    stats = conn.execute("""
        SELECT
            COUNT(*) as total_sessions,
            COALESCE(AVG(avg_score), 0) as overall_avg,
            COALESCE(MAX(avg_score), 0) as best_score,
            COUNT(CASE WHEN status='completed' THEN 1 END) as completed_sessions
        FROM interview_sessions WHERE user_id=?
    """, (user_id,)).fetchone()
    conn.close()
    return dict(stats) if stats else {}

# ─── Mentor Chat Helpers ───────────────────────────────────────────────────────

def save_mentor_message(user_id, role, content):
    conn = get_db()
    conn.execute("INSERT INTO mentor_chats (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

def get_mentor_history(user_id, limit=20):
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content FROM mentor_chats WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))

def clear_mentor_history(user_id):
    conn = get_db()
    conn.execute("DELETE FROM mentor_chats WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ─── Goal Helpers ──────────────────────────────────────────────────────────────

def create_goal(user_id, title, description, target_date):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO goals (user_id, title, description, target_date) VALUES (?, ?, ?, ?)",
        (user_id, title, description, target_date)
    )
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return goal_id

def get_user_goals(user_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM goals WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_goal_progress(goal_id, user_id, progress, status):
    conn = get_db()
    conn.execute(
        "UPDATE goals SET progress=?, status=? WHERE id=? AND user_id=?",
        (progress, status, goal_id, user_id)
    )
    conn.commit()
    conn.close()

def delete_goal(goal_id, user_id):
    conn = get_db()
    conn.execute("DELETE FROM goals WHERE id=? AND user_id=?", (goal_id, user_id))
    conn.commit()
    conn.close()
