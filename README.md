# 🧠 Task Manager (Flask)

A simple Flask-based Task Manager web app where users can register, log in, and manage their tasks.

---

## ⚙️ Features
- User authentication (register/login)
- Add, view, and delete tasks
- SQLite database for local storage
- Responsive design using HTML & CSS
- Flask backend (can connect to React frontend)

---

## 🏗️ Project Structure
```bash
task-manager/
├── app.py
├── requirements.txt
├── Procfile
├── templates/
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ └── add_task.html
├── static/
│ └── style.css
└── instance/
└── taskmanager.db
```

---

## 🚀 Setup & Run (Locally)

1. Clone the repo:
   ```bash
   git clone https://github.com/PremKumar7516/task-manager.git
   cd task-manager

2. Create a virtual environment:
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Run the Flask app:
   python app.py

App will run at: http://127.0.0.1:5000/