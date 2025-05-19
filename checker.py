#!/usr/bin/env python3
import datetime, locale, os, smtplib, traceback, dateutil.parser, requests
from email.mime.text import MIMEText

# IDs – anonym
STUDIO_ID   = 39100
EMPLOYEE_ID = 25902
SERVICE_ID  = 20325
URL         = "https://www.studiobookr.com/AppointmentAvailabilities/Get"

HEADERS = {  # unverändert
    "accept":"application/json, text/plain, */*",
    "accept-language":"de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "anti-forgery-token":"cwhTliQgsxmtSh7i1tgIPc4-N5XdTe_LLF__nEFPlYGKrz_6mI17FLmwHrNAdGyJMmQlWBbPFrq1CzmpAgKCmw==",
    "baggage":"sentry-environment=production,sentry-release=2.6.0,sentry-public_key=890ef2862fc2937c08d2a1daebc40f62, …",
    "content-type":"application/json",
    "cookie":"_ga=GA1.2.2037571814.1712820656; _gid=GA1.2.2129895147.1712820656; _ga_RR5GT82TKM=GS1.2.1712820656.1.1.1712820831.0.0.0",
    "current-site":"https://www.studiobookr.com/david-fechner-friseur-39100",
    "origin":"https://www.studiobookr.com",
    "referer":"https://www.studiobookr.com/david-fechner-friseur-39100?dcc=1",
    "sec-ch-ua":"\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":"\"macOS\"",
    "sec-fetch-dest":"empty",
    "sec-fetch-mode":"cors",
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except locale.Error:
    pass

# --------------------- Helfer ------------------------------------------------
def send_mail(subject, body):
    user, pw, rcpt = os.environ["GMAIL_USER"], os.environ["GMAIL_PW"], os.environ["NOTIFY_EMAIL"]
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, user, rcpt
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.send_message(msg)

def iso(inp, fallback):
    return dateutil.parser.parse(inp).date().isoformat() if inp else str(fallback)

def call_api(start_iso, end_iso):
    payload = {
        "studioId": STUDIO_ID,
        "start":    start_iso,
        "end":      end_iso,
        "employeeId": EMPLOYEE_ID,
        "servicePackageId": None,
        "serviceIds": [SERVICE_ID],
    }
    r = requests.post(URL, json=payload, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return [
        a for a in r.json().get("availabilities", [])
        if any(s["employeeId"] == EMPLOYEE_ID for s in a.get("splits", []))
    ]

# --------------------- Hauptablauf ------------------------------------------
if __name__ == "__main__":
    try:
        today = datetime.date.today()
        start_date = dateutil.parser.parse(os.getenv("START_DATE") or str(today)).date()
        final_date = dateutil.parser.parse(os.getenv("END_DATE")   or str(today + datetime.timedelta(days=13))).date()

        # Schönes Log
        nice = f"{start_date.strftime('%-d. %B')} bis {final_date.strftime('%-d. %B %Y') if start_date.year!=final_date.year else final_date.strftime('%-d. %B')}"
        print(f"📅 Suche freie Slots für: {nice}")

        all_slots = []
        current = start_date
        while current <= final_date:
            block_end = min(current + datetime.timedelta(days=6), final_date)
            print(f"  → API-Call {current} – {block_end}")
            all_slots.extend(call_api(str(current), str(block_end)))
            current += datetime.timedelta(days=7)

        if all_slots:
            times = [
                datetime.datetime.fromisoformat(a["start"]).strftime("%a, %d.%m. %H:%M")
                for a in sorted(all_slots, key=lambda x: x["start"])
            ]
            send_mail(f"{len(all_slots)} freie Friseur-Slots", "\n".join(times))
        else:
            print("Keine passenden Slots.")
    except Exception:
        traceback.print_exc()
        raise
