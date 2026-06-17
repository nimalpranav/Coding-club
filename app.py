from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:nimalpranav@db.dwannxymrzkeyoqersts.supabase.co:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        sid = request.form["student_id"]
        pwd = generate_password_hash(request.form["password"])
        if Student.query.filter_by(student_id=sid).first():
            return "Student ID already exists"
        db.session.add(Student(student_id=sid, password_hash=pwd))
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        sid = request.form["student_id"]
        pwd = request.form["password"]
        s = Student.query.filter_by(student_id=sid).first()
        if s and check_password_hash(s.password_hash, pwd):
            session["student"] = sid
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect(url_for("login"))
    files = File.query.all()
    return render_template("dashboard.html", files=files)

@app.route("/download/<filename>")
def download(filename):
    if "student" not in session:
        return redirect(url_for("login"))
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
    return render_template("admin_login.html")

@app.route("/admin/panel", methods=["GET","POST"])
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        f = request.files["file"]
        name = secure_filename(f.filename)
        f.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
        db.session.add(File(filename=name))
        db.session.commit()
    files = File.query.all()
    return render_template("admin.html", files=files)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
