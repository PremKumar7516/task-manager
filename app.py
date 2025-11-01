from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# --------------------------------------------------------------------
# ✅ DATABASE SETUP
# --------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    """Connects to SQLite DB using an absolute path."""
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Creates tables if they do not exist."""
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        password TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    db.commit()
    print("✅ init_db() executed, database tables ready.")


# --------------------------------------------------------------------
# ✅ ROUTES
# --------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password),
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "⚠️ Username already exists. Try a different one."
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        else:
            return "❌ Invalid username or password"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    tasks = db.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("dashboard.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    desc = request.form.get("description", "")

    db = get_db()
    db.execute(
        "INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)",
        (title, desc, session["user_id"]),
    )
    db.commit()
    return redirect(url_for("dashboard"))


@app.route("/update/<int:task_id>", methods=["POST"])
def update_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = request.form["status"]
    db = get_db()
    db.execute(
        "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?",
        (status, task_id, session["user_id"]),
    )
    db.commit()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"]),
    )
    db.commit()
    return redirect(url_for("dashboard"))


# --------------------------------------------------------------------
# ✅ MAIN ENTRY POINT
# --------------------------------------------------------------------
if __name__ == "__main__":
    # Ensure database tables exist before running
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
