#!/usr/bin/env python3
"""
Dennis-Slot-Checker – Minimal Header Edition
"""

import datetime
import locale
import os
import smtplib
import traceback

import requests
from email.mime.text import MIMEText

# --------------------------------- Konstante(n) ---------------------------------
STUDIO_ID   = 39100
EMPLOYEE_ID = 25902          # Dennis
SERVICE_ID  = 20325          # „Herren kurz“
MAIL_TO     = "lapulga89@gmail.com"

# Deutsche Wochentags- / Datumsformatierung
try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    # Fallback, falls Runner-Container de_DE nicht installiert hat
    pass

# Nur absolut erforderliche Header
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# -------------------------------------------------------------------------------
def send_mail(subject: str, body: str) -> None:
    user = os.environ["GMAIL_USER"]
    pw   = os.environ["GMAIL_PW"]

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = MAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, pw)
        server.send_message(msg)


def fetch_slots():
    today = datetime.date.today()
    payload = {
        "studioId": STUDIO_ID,
        "start": str(today),
        "end":   str(today + datetime.timedelta(days=7)),
        "employeeId": EMPLOYEE_ID,
        "servicePackageId": None,
        "serviceIds": [SERVICE_ID],
    }

    r = requests.post(
        "https://www.studiobookr.com/AppointmentAvailabilities/Get",
        json=payload,
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("availabilities", [])


if __name__ == "__main__":
    try:
        avail = fetch_slots()

        if avail:
            lines = [
                datetime.datetime.fromisoformat(a["start"])
                .strftime("%a, %d.%m. %H:%M Uhr")
                for a in avail
            ]
            send_mail("Dennis: freie Slots!", "\n".join(lines))
        else:
            send_mail("Dennis-Status", "Kein Slot frei.")
    except Exception:
        send_mail("Dennis-Checker Fehler", traceback.format_exc())
