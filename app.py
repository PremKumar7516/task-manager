import os
import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Config
app = Flask(__name__, static_folder="static", template_folder="templates")

# Use instance folder path (create if missing)
INSTANCE_FOLDER = os.path.join(app.root_path, "instance")
os.makedirs(INSTANCE_FOLDER, exist_ok=True)

app.config['DATABASE'] = os.path.join(app.root_path, "instance", "taskmanager.db")
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret_key_change_this")

# Ensure instance folder exists
os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

# Database helpers
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

def init_db():
    db = get_db()
    # Create tables if not exists
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

# Decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# Routes
#@app.before_first_request
#def before_first():
#    init_db()

@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    status = request.args.get('status', 'all')  # all / pending / completed
    db = get_db()
    if status == 'pending':
        tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC", (user_id,)).fetchall()
    elif status == 'completed':
        tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? AND status = 'completed' ORDER BY created_at DESC", (user_id,)).fetchall()
    else:
        tasks = db.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    return render_template('index.html', tasks=tasks, username=session.get('username'), filter=status)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        if not username or not password:
            flash("Username and password required.", "danger")
            return redirect(url_for('register'))

        db = get_db()
        try:
            db.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, generate_password_hash(password)))
            db.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password.", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for('add_task'))
        db = get_db()
        db.execute("INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)",
                   (title, description, session['user_id']))
        db.commit()
        flash("Task added.", "success")
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id'])).fetchone()
    if not task:
        flash("Task not found.", "danger")
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        status = request.form.get('status', 'pending')
        if not title:
            flash("Title required.", "danger")
            return redirect(url_for('edit_task', task_id=task_id))
        db.execute("UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ? AND user_id = ?",
                   (title, description, status, task_id, session['user_id']))
        db.commit()
        flash("Task updated.", "success")
        return redirect(url_for('index'))
    return render_template('add_task.html', task=task)

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    db.commit()
    flash("Task deleted.", "info")
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET status = 'completed' WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    db.commit()
    flash("Task marked as completed.", "success")
    return redirect(url_for('index'))

# Small route to show server healthy (useful for deployment)
@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    # create DB if missing (safe)
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=False)
