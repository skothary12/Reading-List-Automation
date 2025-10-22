#!/usr/bin/env python3
"""Check weather via OpenWeather One Call 3 and email an umbrella recommendation.

Environment variables (set these in GitHub Secrets for automation):
  OPENWEATHER_API_KEY - your OpenWeather API key
  LAT - latitude of the location to check
  LON - longitude of the location to check
  EMAIL_SMTP_HOST - SMTP server host (e.g. smtp.gmail.com)
  EMAIL_SMTP_PORT - SMTP server port (e.g. 587 or 465)
  EMAIL_USERNAME - SMTP login username (usually your email)
  EMAIL_PASSWORD - SMTP login password or app password
  EMAIL_FROM - email From header
  EMAIL_TO - recipient email (can be same as from)
  TIMEZONE - IANA timezone string (e.g. America/Los_Angeles). Default: UTC
  PRECIP_THRESHOLD - float 0..1 threshold for precipitation probability (default 0.3)
  FORCE_SEND - if set to '1', bypass the 7:00 check (useful for manual tests)

This script is written to be executed hourly by GitHub Actions. It will only send
an email when the local time in TIMEZONE is 07:00 (7am) unless FORCE_SEND=1.
"""

import os
import sys
import requests
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timezone

try:
    # Python 3.9+ has zoneinfo; prefer that if available
    from zoneinfo import ZoneInfo
    HAVE_ZONEINFO = True
except Exception:
    HAVE_ZONEINFO = False
    try:
        import pytz
    except Exception:
        pytz = None


OPENWEATHER_URL = "https://api.openweathermap.org/data/3.0/onecall"


def get_env(name, required=True, default=None):
    v = os.getenv(name)
    if v is None:
        if required and default is None:
            print(f"Missing required environment variable: {name}")
            sys.exit(2)
        return default
    return v


def load_config():
    cfg = {}
    cfg['api_key'] = get_env('OPENWEATHER_API_KEY')
    cfg['lat'] = get_env('LAT')
    cfg['lon'] = get_env('LON')
    cfg['smtp_host'] = get_env('EMAIL_SMTP_HOST')
    cfg['smtp_port'] = int(get_env('EMAIL_SMTP_PORT'))
    cfg['smtp_user'] = get_env('EMAIL_USERNAME')
    cfg['smtp_pass'] = get_env('EMAIL_PASSWORD')
    cfg['email_from'] = get_env('EMAIL_FROM')
    cfg['email_to'] = get_env('EMAIL_TO')
    cfg['timezone'] = get_env('TIMEZONE', required=False, default='UTC')
    cfg['threshold'] = float(get_env('PRECIP_THRESHOLD', required=False, default='0.3'))
    cfg['force'] = os.getenv('FORCE_SEND', '0') == '1'
    return cfg


def local_now(tz_name: str):
    if HAVE_ZONEINFO:
        try:
            tz = ZoneInfo(tz_name)
            return datetime.now(tz)
        except Exception as e:
            print(f"zoneinfo timezone error: {e}")
    # fallback to pytz if available
    if 'pytz' in globals() and pytz is not None:
        try:
            tz = pytz.timezone(tz_name)
            return datetime.now(tz)
        except Exception as e:
            print(f"pytz timezone error: {e}")
    print(f"Invalid timezone '{tz_name}' or missing zoneinfo/pytz; using UTC")
    return datetime.now(timezone.utc)


def fetch_weather(api_key, lat, lon, units='metric'):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': units,
        'exclude': 'minutely,alerts'
    }
    r = requests.get(OPENWEATHER_URL, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def should_bring_umbrella(data: dict, threshold: float = 0.3):
    """Decide whether to bring an umbrella.

    Logic:
      - Check daily[0].pop and daily[0].rain/snow.
      - Check hourly probabilities for the next 12 hours.
      - If any indicate precipitation probability >= threshold or rain/snow > 0, recommend umbrella.
    """
    reasons = []

    daily = data.get('daily', [])
    if daily:
        today = daily[0]
        pop = today.get('pop', 0)
        rain = today.get('rain', 0)
        snow = today.get('snow', 0)
        if pop >= threshold:
            reasons.append(f"Daily precipitation probability {pop:.0%} >= {threshold:.0%}")
        if rain and rain > 0:
            reasons.append(f"Daily rain volume {rain} mm")
        if snow and snow > 0:
            reasons.append(f"Daily snow volume {snow} mm")

    hourly = data.get('hourly', [])
    hours_to_check = min(len(hourly), 12)
    for i in range(hours_to_check):
        h = hourly[i]
        pop = h.get('pop', 0)
        if pop >= threshold:
            reasons.append(f"Hour+{i}: pop {pop:.0%}")
        if isinstance(h.get('rain'), dict) and any(v > 0 for v in h['rain'].values()):
            reasons.append(f"Hour+{i}: rain: {h['rain']}")
        if isinstance(h.get('snow'), dict) and any(v > 0 for v in h['snow'].values()):
            reasons.append(f"Hour+{i}: snow: {h['snow']}")

    if reasons:
        return True, '\n'.join(reasons)
    return False, 'No significant precipitation expected.'


def compose_email(from_addr: str, to_addr: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.set_content(body)
    return msg


def send_email(cfg, msg: EmailMessage):
    host = cfg['smtp_host']
    port = cfg['smtp_port']
    user = cfg['smtp_user']
    password = cfg['smtp_pass']

    if port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)


def main():
    cfg = load_config()

    now = local_now(cfg['timezone'])
    print(f"Local time in {cfg['timezone']}: {now.isoformat()}")

    if not cfg['force']:
        if now.hour != 7 or now.minute != 0:
            print('Not 07:00 local time; exiting without sending email.')
            return

    try:
        data = fetch_weather(cfg['api_key'], cfg['lat'], cfg['lon'])
    except Exception as e:
        print(f"Failed to fetch weather: {e}")
        raise

    want_umbrella, reason = should_bring_umbrella(data, cfg['threshold'])

    if want_umbrella:
        subject = 'Umbrella Alert: Bring an umbrella ☔'
        body = f"Recommendation: Bring an umbrella.\n\nReasons:\n{reason}\n\nDaily summary:\n{data.get('daily',[{}])[0]}"
    else:
        subject = 'No umbrella needed today ✅'
        body = f"Recommendation: No umbrella needed.\n\nReason: {reason}\n\nDaily summary:\n{data.get('daily',[{}])[0]}"

    msg = compose_email(cfg['email_from'], cfg['email_to'], subject, body)

    try:
        send_email(cfg, msg)
        print('Email sent successfully')
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


if __name__ == '__main__':
    main()
