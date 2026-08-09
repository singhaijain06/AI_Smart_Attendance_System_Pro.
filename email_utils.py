"""
email_utils.py
Sends low-attendance alert emails using Gmail SMTP (or any SMTP server
configured in config.py).
"""

import smtplib
from email.mime.text import MIMEText
import config


def send_low_attendance_email(student_name, roll_no, percentage, to_email):
    """Sends one alert email. Returns (success: bool, message: str)."""
    if not config.SMTP_EMAIL or not config.SMTP_APP_PASSWORD:
        return False, "Email not configured (set SMTP_EMAIL / SMTP_APP_PASSWORD in config.py)."

    if not to_email:
        return False, "This student has no email on file."

    subject = "Low Attendance Alert"
    body = (
        f"Dear {student_name},\n\n"
        f"This is an automated notice from the Smart Attendance System.\n"
        f"Your current attendance is {percentage}%, which is below the "
        f"required 75% threshold.\n\n"
        f"Roll Number: {roll_no}\n\n"
        f"Please ensure regular attendance going forward.\n\n"
        f"— Smart Attendance & Student Monitoring System"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.SMTP_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_EMAIL, config.SMTP_APP_PASSWORD)
            server.sendmail(config.SMTP_EMAIL, [to_email], msg.as_string())
        return True, "Sent."
    except Exception as e:
        return False, str(e)
