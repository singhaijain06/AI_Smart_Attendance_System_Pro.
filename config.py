"""
config.py
Admin login credentials and email (SMTP) settings.

IMPORTANT: change ADMIN_USERNAME / ADMIN_PASSWORD before your demo/submission.
For email alerts, fill in SMTP_EMAIL and SMTP_APP_PASSWORD — for Gmail you
need an "App Password" (not your normal password): Google Account ->
Security -> 2-Step Verification -> App Passwords.
If you don't want to set up email, just leave SMTP_EMAIL blank — the
"Send Low Attendance Alerts" button will show an error instead of crashing.
"""

import os

# Admin login (protects Register / Train / Dashboard / Edit / Delete / Export)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Flask session secret — change this to any random string for real deployments
SECRET_KEY = "change-this-secret-key-before-deploying"

# Email (SMTP) settings for low-attendance alerts — optional
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = ""          # e.g. "youremail@gmail.com" — leave blank to disable email alerts
SMTP_APP_PASSWORD = ""   # Gmail App Password (16 characters, no spaces)
