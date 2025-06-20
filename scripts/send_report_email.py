import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables with relative path
load_dotenv(dotenv_path='config/.env')

REPORT_TXT = "reports/leads_summary.txt"
ALERTS_TXT = "reports/alerts_summary.txt"
FROM_EMAIL = os.getenv("GMAIL_ADDRESS")
TO_EMAIL = os.getenv("REPORT_RECIPIENT_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email(subject, body, from_email, to_email, app_password):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, app_password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    # Check if email credentials are configured
    if not all([FROM_EMAIL, TO_EMAIL, APP_PASSWORD]):
        print("Email credentials not configured. Skipping email notification.")
        print("To enable email notifications, set GMAIL_ADDRESS, REPORT_RECIPIENT_EMAIL, and GMAIL_APP_PASSWORD in config/.env")
        return
    
    if os.path.exists(REPORT_TXT):
        with open(REPORT_TXT) as f:
            body = f.read()
        
        # Append alerts if available
        if os.path.exists(ALERTS_TXT):
            with open(ALERTS_TXT) as f2:
                body += "\n\n" + f2.read()
        
        success = send_email(
            subject="Daily Lead Generation Report & Alerts",
            body=body,
            from_email=FROM_EMAIL,
            to_email=TO_EMAIL,
            app_password=APP_PASSWORD
        )
        
        if success:
            print("Report and alerts emailed successfully.")
        else:
            print("Failed to send email report.")
    else:
        print(f"No report found at {REPORT_TXT} to email.")

if __name__ == "__main__":
    main()
