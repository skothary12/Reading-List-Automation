# Umbrella Notifier

This repository contains a small script and GitHub Actions workflow that checks the weather using the OpenWeather One Call 3 API and emails you at 7:00 local time with a recommendation whether to bring an umbrella.

Files added:
- `scripts/check_umbrella.py` — main Python script that fetches weather and sends email via SMTP.
- `requirements.txt` — dependencies (`requests`, `pytz`).
- `.github/workflows/umbrella.yml` — GitHub Actions workflow that runs the script on a schedule.

Required GitHub Secrets
Set the following repository secrets (Settings → Secrets & variables → Actions) before enabling the workflow:

- `OPENWEATHER_API_KEY` — your OpenWeather API key (One Call 3)
- `LAT` — latitude for your location (e.g. `37.7749`)
- `LON` — longitude for your location (e.g. `-122.4194`)
- `EMAIL_SMTP_HOST` — SMTP host (e.g. `smtp.gmail.com`)
- `EMAIL_SMTP_PORT` — SMTP port (e.g. `587` for STARTTLS or `465` for SSL)
- `EMAIL_USERNAME` — SMTP username (usually your email address)
- `EMAIL_PASSWORD` — SMTP password or app-specific password. For Gmail, create an App Password if using 2FA.
- `EMAIL_FROM` — From address to use in the email
- `EMAIL_TO` — Recipient address (can be same as `EMAIL_FROM`)
- `TIMEZONE` — IANA timezone string, e.g. `America/Los_Angeles`. Default is `UTC` if not set.
- `PRECIP_THRESHOLD` — (optional) decimal probability threshold (0-1) to trigger umbrella recommendation; default `0.3`.

Security notes
- The workflow uses your SMTP credentials to log in and send mail from your account. Use an app password when possible (Gmail, Outlook). Do not commit credentials to the repository.

Local testing
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export environment variables locally (or set them in your shell). For testing you can set `FORCE_SEND=1` to bypass the 07:00 check:

```bash
export OPENWEATHER_API_KEY=your_api_key
export LAT=37.7749
export LON=-122.4194
export EMAIL_SMTP_HOST=smtp.gmail.com
export EMAIL_SMTP_PORT=587
export EMAIL_USERNAME=your.email@example.com
export EMAIL_PASSWORD=your_smtp_password_or_app_password
export EMAIL_FROM=your.email@example.com
export EMAIL_TO=recipient@example.com
export TIMEZONE=America/Los_Angeles
export FORCE_SEND=1
python scripts/check_umbrella.py
```

If you get authentication errors with Gmail, ensure you use an App Password and that your account has 2FA enabled (recommended).

How it works
- The action runs every 30 minutes. The script checks the local time for `TIMEZONE` and will only send an email at 07:00 local time (unless `FORCE_SEND=1`).
- The script fetches forecast data and looks at daily and hourly precipitation probability and volumes to decide whether to recommend bringing an umbrella.

Next steps / optional improvements
- Add retry/backoff for network calls.
- Add unit tests for the decision logic.
- Improve email formatting (HTML) or add a daily summary calendar event.
