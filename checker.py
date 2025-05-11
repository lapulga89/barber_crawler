#!/usr/bin/env python3
"""
Dennis-Slot-Checker – statischer Header-Call
Sucht alle 10 Minuten nach freien Terminen (heute → +7 Tage)
und mailt nur, wenn Slots gefunden werden.
"""

import datetime
import locale
import os
import smtplib
import traceback
from email.mime.text import MIMEText

import requests

# --------------------------------------------------------------------------- #
#  KONSTANTEN
# --------------------------------------------------------------------------- #
STUDIO_ID   = 39100
EMPLOYEE_ID = 25902          # Dennis
SERVICE_ID  = 20325
MAIL_TO     = "lapulga89@gmail.com"

# deutsche Datums­formatierung, wenn verfügbar
try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    pass

# ----- feste Header aus deinem funktionierenden Curl ----------------------- #
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "anti-forgery-token": "cwhTliQgsxmtSh7i1tgIPc4-N5XdTe_LLF__nEFPlYGKrz_6mI17FLmwHrNAdGyJMmQlWBbPFrq1CzmpAgKCmw==",
    "baggage": "sentry-environment=production,sentry-release=2.6.0,sentry-public_key=890ef2862fc2937c08d2a1daebc40f62,sentry-trace_id=ec3fc740789f43e69246c2603dcb5834,sentry-sample_rate=0.2,sentry-transaction=POST%20%2FAppointmentAvailabilities%2FGet,sentry-sampled=false",
    "content-type": "application/json",
    "cookie": "_ga=GA1.2.2037571814.1712820656; _gid=GA1.2.2129895147.1712820656; _ga_RR5GT82TKM=GS1.2.1712820656.1.1.1712820831.0.0.0",
    "current-site": "https://www.studiobookr.com/david-fechner-friseur-39100",
    "origin": "https://www.studiobookr.com",
    "page-call-time": "2024-04-11T09:33:51",
    "referer": "https://www.studiobookr.com/david-fechner-friseur-39100?dcc=1",
    "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sentry-trace": "ec3fc740789f43e69246c2603dcb5834-8e17ba999487adaf-0",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

URL = "https://www.studiobookr.com/AppointmentAvailabilities/Get"

# --------------------------------------------------------------------------- #
#  HILFSFUNKTIONEN
# --------------------------------------------------------------------------- #
def send_mail(subject: str, body: str) -> None:
    user = os.environ["GMAIL_USER"]
    pw   = os.environ["GMAIL_PW"]

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = MAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.send_message(msg)

def fetch_slots():
    today = datetime.date.today()
    payload = {
        "studioId": STUDIO_ID,
        "start": str(today),
        "end":   str(today + datetime.timedelta(days=7)),
        "employeeId": EMPLOYEE_ID,
        "servicePackageId": None,
        "serviceIds": [SERVICE_ID]
    }

    r = requests.post(URL, json=payload, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("availabilities", [])

# --------------------------------------------------------------------------- #
#  HAUPTLOGIK
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        avail = fetch_slots()

        if avail:
            times = [
                datetime.datetime.fromisoformat(a["start"])
                .strftime("%a, %d.%m. %H:%M Uhr")
                for a in avail
            ]
            send_mail("Dennis: freie Slots!", "\n".join(times))
        else:
            print("Kein Slot frei.")
    except Exception:
        # Fehler nur ins Actions-Log schreiben
        traceback.print_exc()
        raise
