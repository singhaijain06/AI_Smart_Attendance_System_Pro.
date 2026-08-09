"""
database.py
Handles all SQLite database operations for the Smart Attendance System.
Tables:
  - students   (id, name, roll_no, course, email, registered_on)
  - attendance (id, student_id, date, time, status)
"""

import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            course TEXT,
            email TEXT,
            registered_on TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, date)
        )
    """)

    conn.commit()
    conn.close()


def add_student(name, roll_no, course, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO students (name, roll_no, course, email, registered_on) VALUES (?, ?, ?, ?, ?)",
        (name, roll_no, course, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    student_id = cur.lastrowid
    conn.close()
    return student_id


def get_all_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_by_id(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_attendance(student_id, status="Present"):
    """Marks attendance for today. Ignores duplicate marks for same day."""
    conn = get_connection()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")
    try:
        cur.execute(
            "INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)",
            (student_id, today, now_time, status),
        )
        conn.commit()
        marked = True
    except sqlite3.IntegrityError:
        # Already marked today
        marked = False
    conn.close()
    return marked


def get_attendance_by_date(date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, s.name, s.roll_no, s.course, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time
    """, (date,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_summary():
    """Returns attendance percentage per student (monitoring feature)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT date) as total_days FROM attendance")
    total_days_row = cur.fetchone()
    total_days = total_days_row["total_days"] or 1

    cur.execute("""
        SELECT s.id, s.name, s.roll_no, s.course,
               COUNT(a.id) as present_days
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        ORDER BY s.name
    """)
    rows = cur.fetchall()
    conn.close()

    summary = []
    for r in rows:
        d = dict(r)
        percentage = round((d["present_days"] / total_days) * 100, 2) if total_days else 0
        d["total_days"] = total_days
        d["percentage"] = percentage
        d["low_attendance"] = percentage < 75
        summary.append(d)
    return summary


def get_attendance_history(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, time, status FROM attendance
        WHERE student_id = ? ORDER BY date DESC
    """, (student_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_student(student_id, name, roll_no, course, email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE students SET name=?, roll_no=?, course=?, email=? WHERE id=?",
        (name, roll_no, course, email, student_id),
    )
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def get_all_attendance_records():
    """Every attendance record ever, joined with student info — for CSV export."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name, s.roll_no, s.course, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_attendance_dates():
    """Distinct dates attendance has been taken on — used for the trend chart."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT date FROM attendance ORDER BY date")
    rows = cur.fetchall()
    conn.close()
    return [r["date"] for r in rows]


def get_daily_present_counts():
    """Number of students present on each date — used for the trend chart."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, COUNT(*) as present_count
        FROM attendance
        GROUP BY date
        ORDER BY date
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
