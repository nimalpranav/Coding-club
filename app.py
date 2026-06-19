from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ==========================

# APP CONFIG

# ==========================

app = Flask(__name__)

app.secret_key = "CHANGE_THIS_SECRET_KEY"

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres.dwannxymrzkeyoqersts:nimalpranav@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
"connect_args": {
"sslmode": "require"
}
}

db = SQLAlchemy(app)

# ==========================

# ADMIN SETTINGS

# ==========================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "CodingClub123"

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==========================

# DATABASE MODELS

# ==========================

class Student(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class File(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    filepath = db.Column(
        db.String(500),
        nullable=False
    )

    downloads = db.Column(
        db.Integer,
        default=0
    )

    upload_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# ==========================

# HOME

# ==========================

@app.route("/")
def home():
    return redirect(url_for("login"))

# ==========================

# REGISTER

# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing = Student.query.filter_by(
            username=username
        ).first()

        if existing:
            flash("Username already exists")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        student = Student(
            username=username,
            password_hash=hashed_password
        )

        db.session.add(student)
        db.session.commit()

        flash("Account created successfully")

        return redirect(url_for("login"))

    return render_template("register.html")

# ==========================

# STUDENT LOGIN

# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        student = Student.query.filter_by(username=username).first()

        if student and check_password_hash(student.password_hash, password):
            session["student"] = student.username
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")

# ==========================

# LOGOUT

# ==========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    students = Student.query.all()
    files = File.query.all()

    total_downloads = sum(file.downloads for file in files)

    return render_template(
        "admin_dashboard.html",
        students=students,
        files=files,
        total_downloads=total_downloads
    )
# ADMIN LOGIN


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if (
            username == ADMIN_USERNAME and
            password == ADMIN_PASSWORD
        ):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials")

    return render_template("admin_login.html")


# ==========================

# STUDENT DASHBOARD

# ==========================

@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect(url_for("login"))

    files = File.query.order_by(File.upload_date.desc()).all()
    total = len(files)

    return render_template("dashboard.html", files=files, total=total)

from flask import send_file
from werkzeug.utils import secure_filename

# ==========================

# UPLOAD FILE

# ==========================

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "admin" not in session:
        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":
        uploaded_file = request.files["file"]

        if uploaded_file.filename != "":
            filename = secure_filename(
                uploaded_file.filename
            )

            filepath = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            uploaded_file.save(filepath)

            new_file = File(
                filename=filename,
                filepath=filepath
            )

            db.session.add(new_file)
            db.session.commit()

            flash("File uploaded successfully")

            return redirect(
                url_for("admin_dashboard")
            )

    return render_template(
        "upload.html"
    )

# ==========================

# DOWNLOAD FILE

# ==========================

@app.route("/download/<int:file_id>")
def download(file_id):
    if "student" not in session:
        return redirect(
            url_for("login")
        )

    file = File.query.get_or_404(
        file_id
    )

    file.downloads += 1
    db.session.commit()

    return send_file(
        file.filepath,
        as_attachment=True
    )

# ==========================

# DELETE FILE

# ==========================

@app.route("/delete-file/<int:file_id>")
def delete_file(file_id):
    if "admin" not in session:
        return redirect(
            url_for("admin_login")
        )

    file = File.query.get_or_404(
        file_id
    )

    try:
        os.remove(file.filepath)
    except:
        pass

    db.session.delete(file)
    db.session.commit()

    flash("File deleted")

    return redirect(
        url_for("admin_dashboard")
    )

# ==========================

# CREATE TABLES

# ==========================

with app.app_context():
    db.create_all()

# ==========================

# RUN APP

# ==========================

if __name__ == "__main__":
    print(app.url_map)
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

