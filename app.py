from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"
UPLOAD_FOLDER = "uploads"

# ── Database setup ──────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        image_path TEXT NOT NULL,
        extracted_text TEXT,
        event_name TEXT,
        status TEXT DEFAULT "pending",
        points INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

# ── Routes ───────────────────────────────────────────────────
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    # TODO: check credentials, set session
    return render_template("login.html")

@app.route("/student/dashboard")
def student_dashboard():
    # TODO: fetch student's certificates and points
    return render_template("student_dashboard.html")

@app.route("/student/upload", methods=["GET", "POST"])
def upload_certificate():
    if request.method == "POST":
        file = request.files["certificate"]
        # TODO: call ocr.py here
        # TODO: save to database
        pass
    return render_template("upload_certificate.html")

@app.route("/mentor/dashboard")
def mentor_dash