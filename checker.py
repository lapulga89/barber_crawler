# checker.py
import requests, datetime, smtplib, os, traceback

EMPLOYEE_ID = 25902
STUDIO_ID   = 39100
SERVICE_ID  = 20325
MAIL_TO     = "lapulga89@gmail.com"

def send_mail(subject, body):
    user = os.environ["GMAIL_USER"]
    pw   = os.environ["GMAIL_PW"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, MAIL_TO,
                   f"Subject: {subject}\n\n{body}")

def fetch_slots():
    sess = requests.Session()
    salon_url = f"https://www.studiobookr.com/david-fechner-friseur-{STUDIO_ID}"
    html = sess.get(salon_url, timeout=10).text
    token = html.split('anti-forgery-token" value="')[1].split('"')[0]

    today = datetime.date.today()
    payload = {
        "studioId": STUDIO_ID,
        "start": str(today),
        "end":   str(today + datetime.timedelta(days=7)),
        "employeeId": EMPLOYEE_ID,
        "servicePackageId": None,
        "serviceIds": [SERVICE_ID]
    }

    r = sess.post(
        "https://www.studiobookr.com/AppointmentAvailabilities/Get",
        json=payload,
        headers={
            "anti-forgery-token": token,
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://www.studiobookr.com",
            "referer": salon_url
        },
        timeout=10
    )
    r.raise_for_status()
    return r.json().get("availabilities", [])

if __name__ == "__main__":
    try:
        avail = fetch_slots()
        if avail:
            times = "\n".join([a['start'] for a in avail])
            send_mail("✅ Dennis: freie Slots!", times)
        else:
            send_mail("ℹ️ Dennis-Status", "Kein Slot frei.")
    except Exception as e:
        send_mail("❌ Dennis-Checker Fehler",
                  traceback.format_exc())
