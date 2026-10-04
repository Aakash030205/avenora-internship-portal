# Avenora Multi-Domain Internship Portal

A Flask + SQLite learning portal with six starter tracks: Web Development, Python Programming, AI & Data Science, Embedded Systems & IoT, Software Testing, and Electrical & Industrial Automation.

## Included

- Student registration and login with Werkzeug password hashing.
- Multi-course enrollment: students can join several free and paid courses; each enrollment has independent access and progress.
- Track-specific modules, notes, practical tasks, external reading links, video-topic search links, quizzes, progress tracking and per-course project submissions.
- Hardware learning mode for Embedded Systems & IoT and Electrical & Industrial Automation, with diagram-based activities, simulation, fault diagnosis, PLC/ladder logic and lab-report/photo/video evidence links instead of the browser code runner.
- Admin dashboard for track visibility and free/paid mode, per-enrollment manual payment verification, student activation, and project review.
- Paid-course students can submit a transaction reference; the admin can verify payment and unlock that course only.
- Certificate eligibility requires all track lessons completed and the latest project submission approved.
- CSRF token checks for POST forms and HTTP-only/SameSite session cookie settings.
- SQLite schema initialization and additive migration support.

## Important notes before real use

- This is a starter learning portal, not a fully accredited internship or payment platform. Only describe an internship/certificate accurately and ensure supervision, assessment and legal requirements are met.
- Paid mode does **not** collect money or integrate with UPI/payment gateways. Configure `AVENORA_PAYMENT_INSTRUCTIONS` with your official payment instructions. Students submit their transaction reference; verify the payment in your payment app/bank before manually marking the specific enrollment verified in the admin UI. Never ask for a UPI PIN, OTP or banking password.
- YouTube links are topic searches, not endorsements or guaranteed course videos. Review learning resources before recommending them.
- SQLite is suitable for local development and small single-instance testing. For production, use a persistent disk or preferably PostgreSQL, backups, HTTPS, secure environment variables, rate limiting, and a deployment review.
- Do not commit database files, passwords, secret keys, student records, or `.env` files to GitHub.
- The included browser code lab runs HTML/CSS/JavaScript only and is hidden for hardware tracks. Hardware courses use diagrams, reports, troubleshooting, simulators and evidence links. Python, machine learning and embedded code must be run in appropriate local environments or simulators.

## Windows / PowerShell quick start

Open PowerShell in this folder, then:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:AVENORA_ADMIN_EMAIL = "admin@avenora.in"
$env:AVENORA_ADMIN_PASSWORD = "CHOOSE_A_LONG_UNIQUE_PASSWORD"
$env:AVENORA_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
$env:AVENORA_PAYMENT_INSTRUCTIONS = "Pay using the official Avenora UPI details; then submit the UTR in your dashboard."
python app.py
```

Open:

- Student portal: http://127.0.0.1:5000/
- Student registration: http://127.0.0.1:5000/register
- Admin login: http://127.0.0.1:5000/admin
- Admin dashboard: http://127.0.0.1:5000/admin/dashboard

Set the environment variables again in each new PowerShell session. Never share the admin password or secret key.

## Deployment environment variables

Configure these in the host's secret/environment settings, not in source code:

- `AVENORA_SECRET_KEY`: long random secret (stable between restarts).
- `AVENORA_ADMIN_EMAIL`: admin email.
- `AVENORA_ADMIN_PASSWORD`: strong admin password; if provided, it resets the existing admin password at app startup.
- `AVENORA_DB_PATH`: optional absolute path to a persistent SQLite database file.
- `AVENORA_PAYMENT_INSTRUCTIONS`: instructions shown to students for paid courses. Do not put secrets or personal banking credentials in the message.
- `PORT`: hosting platform port if required.
- `AVENORA_HTTPS=1`: set secure session cookies when deployed behind HTTPS.

On first startup the app creates the database and six tracks. The first startup requires `AVENORA_ADMIN_PASSWORD` so an admin account can be created. Existing one-course SQLite databases are migrated to allow multiple enrollments, retaining their existing enrollment. Back up your database before upgrading.

## Git safety check

Before pushing:

```powershell
git status --short
```

Confirm `.env`, `database.db`, `database_backup.db`, `venv/`, and all secret files are not staged.
