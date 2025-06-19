import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

REPORT_TXT = "reports/leads_summary.txt"
ALERTS_TXT = "reports/alerts_summary.txt"
FROM_EMAIL = os.getenv("GMAIL_ADDRESS")
TO_EMAIL = os.getenv("REPORT_RECIPIENT_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email(subject, body, from_email, to_email, app_password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, [to_email], msg.as_string())

if os.path.exists(REPORT_TXT):
    with open(REPORT_TXT) as f:
        body = f.read()
    if os.path.exists(ALERTS_TXT):
        with open(ALERTS_TXT) as f2:
            body += "\n\n" + f2.read()
    send_email(
        subject="Daily Lead Generation Report & Alerts",
        body=body,
        from_email=FROM_EMAIL,
        to_email=TO_EMAIL,
        app_password=APP_PASSWORD
    )
    print("Report and alerts emailed successfully.")
else:
    print("No report found to email.")
