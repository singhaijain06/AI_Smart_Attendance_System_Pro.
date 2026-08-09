"""
app.py
Single Flask web app for the AI Smart Attendance & Student Monitoring System.
Everything -- registration, training, live attendance, dashboard, CSV
export, email alerts, and admin login -- works through the browser at
http://127.0.0.1:5000.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session
from datetime import datetime
from functools import wraps
import csv
import io

import database as db
import face_utils
import email_utils
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.before_request
def setup():
    db.init_db()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


# ---------- Auth ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        print("DEBUG username:", repr(username), "| password:", repr(password))
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            session["logged_in"] = True
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))


# ---------- Public pages ----------

@app.route("/")
def index():
    students = db.get_all_students()
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = db.get_attendance_by_date(today)
    return render_template(
        "index.html",
        total_students=len(students),
        present_today=len(today_attendance),
        today=today,
        logged_in=session.get("logged_in", False),
    )


@app.route("/take-attendance")
def take_attendance_page():
    return render_template("take_attendance.html", logged_in=session.get("logged_in", False))


@app.route("/attendance")
def attendance():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    records = db.get_attendance_by_date(date)
    return render_template("attendance.html", records=records, selected_date=date,
                            logged_in=session.get("logged_in", False))


# ---------- Admin-only pages ----------

@app.route("/register")
@login_required
def register_page():
    return render_template("register.html", logged_in=True)


@app.route("/train")
@login_required
def train_page():
    return render_template("train.html", logged_in=True)


@app.route("/students")
@login_required
def students():
    all_students = db.get_all_students()
    return render_template("students.html", students=all_students, logged_in=True)


@app.route("/dashboard")
@login_required
def dashboard():
    summary = db.get_attendance_summary()
    low_attendance_students = [s for s in summary if s["low_attendance"]]
    daily_counts = db.get_daily_present_counts()
    return render_template(
        "dashboard.html",
        summary=summary,
        low_attendance_count=len(low_attendance_students),
        chart_labels=[d["date"] for d in daily_counts],
        chart_values=[d["present_count"] for d in daily_counts],
        logged_in=True,
    )


@app.route("/student/<int:student_id>")
@login_required
def student_detail(student_id):
    student = db.get_student_by_id(student_id)
    history = db.get_attendance_history(student_id)
    return render_template("student_detail.html", student=student, history=history, logged_in=True)


@app.route("/student/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_edit(student_id):
    student = db.get_student_by_id(student_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        course = request.form.get("course", "").strip()
        email = request.form.get("email", "").strip()
        db.update_student(student_id, name, roll_no, course, email)
        return redirect(url_for("students"))
    return render_template("edit_student.html", student=student, logged_in=True)


@app.route("/student/<int:student_id>/delete", methods=["POST"])
@login_required
def student_delete(student_id):
    db.delete_student(student_id)
    return redirect(url_for("students"))


@app.route("/export/attendance.csv")
@login_required
def export_attendance_csv():
    records = db.get_all_attendance_records()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Roll Number", "Course", "Date", "Time", "Status"])
    for r in records:
        writer.writerow([r["name"], r["roll_no"], r["course"], r["date"], r["time"], r["status"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"},
    )


@app.route("/api/send_alerts", methods=["POST"])
@login_required
def api_send_alerts():
    summary = db.get_attendance_summary()
    low_students = [s for s in summary if s["low_attendance"]]

    sent = 0
    failed = []
    for s in low_students:
        student = db.get_student_by_id(s["id"])
        success, message = email_utils.send_low_attendance_email(
            student["name"], student["roll_no"], s["percentage"], student["email"]
        )
        if success:
            sent += 1
        else:
            failed.append(f"{student['name']}: {message}")

    return jsonify({
        "success": True,
        "sent": sent,
        "total_low": len(low_students),
        "failed": failed,
    })


# ---------- API endpoints (browser JavaScript) ----------

@app.route("/api/register_student", methods=["POST"])
@login_required
def api_register_student():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    roll_no = (data.get("roll_no") or "").strip()
    course = (data.get("course") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not roll_no:
        return jsonify({"success": False, "message": "Name and roll number are required."}), 400

    try:
        student_id = db.add_student(name, roll_no, course, email)
    except Exception:
        return jsonify({"success": False, "message": "Roll number already registered."}), 400

    return jsonify({"success": True, "student_id": student_id, "roll_no": roll_no})


@app.route("/api/capture_face", methods=["POST"])
@login_required
def api_capture_face():
    data = request.get_json()
    image_data = data.get("image")
    student_id = data.get("student_id")
    roll_no = data.get("roll_no")
    sample_index = data.get("sample_index", 1)

    if not image_data or not student_id or not roll_no:
        return jsonify({"success": False, "message": "Missing data."}), 400

    saved = face_utils.save_face_sample(image_data, student_id, roll_no, sample_index)
    if saved:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "No face detected in frame."})


@app.route("/api/train", methods=["POST"])
@login_required
def api_train():
    success, message = face_utils.train_model()
    return jsonify({"success": success, "message": message})


@app.route("/api/recognize", methods=["POST"])
def api_recognize():
    data = request.get_json()
    image_data = data.get("image")
    if not image_data:
        return jsonify({"success": False, "message": "No image provided."}), 400

    student_id, confidence = face_utils.recognize_face(image_data)

    if student_id is None:
        return jsonify({"success": False, "message": "No match found."})

    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({"success": False, "message": "Unknown face."})

    marked = db.mark_attendance(student_id)
    return jsonify({
        "success": True,
        "name": student["name"],
        "roll_no": student["roll_no"],
        "already_marked": not marked,
    })


if __name__ == "__main__":
    app.run(debug=True)
