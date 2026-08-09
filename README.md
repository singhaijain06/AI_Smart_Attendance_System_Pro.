# AI Smart Attendance & Student Monitoring System

Everything runs through **one browser link** — register students, train
the model, take attendance, and view the monitoring dashboard, all
using your browser's webcam. Installable as a mobile app (PWA), and
deployable to Render with GitHub.

---

## What's included

- Face-recognition attendance (register / train / recognize — all in-browser)
- Monitoring dashboard with **attendance % + trend chart**
- **CSV export** of attendance records
- **Email alerts** for students below 75% attendance
- **Search** students by name/roll number
- **Edit / Delete** student records
- **Admin login** — protects Register, Train, Students, Dashboard, Export

---

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

### Admin Login
Default credentials (change these in `config.py` before submission/demo):
- **Username:** `admin`
- **Password:** `admin123`

You need to log in to access Register Student, Train Model, Students
list, and the Monitoring Dashboard. "Take Attendance" and viewing
today's Attendance list stay open (so students can mark their own
attendance without a login).

### Email Alerts (optional)
To enable the "Send Low Attendance Alerts" button on the dashboard,
edit `config.py`:
```python
SMTP_EMAIL = "youremail@gmail.com"
SMTP_APP_PASSWORD = "your-16-char-app-password"
```
For Gmail: Google Account → Security → 2-Step Verification → App
Passwords → generate one for "Mail". Don't use your normal Gmail
password — it won't work. If you skip this, everything else still
works fine — the alert button will just show a "not configured" message.

---

## ⚠️ Deploying to Render — storage limitation

Render's free tier has **no permanent storage** — `dataset/`,
`trainer/`, and `attendance.db` get wiped on every restart/redeploy.
Fine for a live demo, not for long-term data. See the deployment
steps below.

---

## Deploy to GitHub + Render

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

### 2. Deploy on Render
1. [render.com](https://render.com) → sign in with GitHub.
2. New + → Web Service → select your repo.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app`
5. Deploy. You get a public link like `https://your-app.onrender.com`.

### 3. Install as a mobile app
Open the Render link on your phone browser → menu → **"Add to Home
Screen" / "Install app"**.

---

## Project Structure

```
├── app.py                 # Flask app: pages, API endpoints, admin login
├── face_utils.py            # Face capture / training / recognition
├── database.py                # SQLite DB + all queries
├── email_utils.py               # Low-attendance email alerts
├── config.py                      # Admin login + SMTP settings — EDIT THIS
├── requirements.txt
├── Procfile                         # Render start command
├── dataset/, trainer/                  # Face data + trained model (auto-created)
├── templates/                            # All HTML pages
└── static/                                 # CSS, PWA manifest, icons
```

---

## How It Works (for your report/viva)

1. Browser captures frames via `getUserMedia()` + `<canvas>`, sends as
   base64 JPEG to Flask via `fetch()`.
2. OpenCV Haar Cascade detects the face; LBPH recognizes it against
   the trained model.
3. A match inserts into the `attendance` table (UNIQUE constraint
   prevents duplicate marking per day).
4. Dashboard computes attendance % per student, flags <75%, and
   renders a **Chart.js line chart** of daily present-counts.
5. **Admin login** uses Flask sessions — a `login_required` decorator
   protects sensitive routes.
6. **CSV export** streams a generated CSV file via Flask's `Response`
   object — no temp file needed.
7. **Email alerts** use Python's built-in `smtplib` over Gmail SMTP.

---

## Suggested viva/report points
- Why session-based login instead of a full user-accounts system:
  simple, sufficient for a single-admin final year project scope.
- Why LBPH over deep learning: fast, offline-friendly, small-dataset
  friendly — trade-off is lower accuracy than CNN-based embeddings.
- Database design: `students` + `attendance`, foreign key relation,
  UNIQUE constraint for duplicate-attendance prevention.
- Limitations: Render free-tier storage isn't persistent; no liveness
  check (a photo could fool it); email alerts need SMTP credentials.
