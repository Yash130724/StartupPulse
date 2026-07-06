import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from startup_pulse.core import config


def send_email(subject: str, html_body: str) -> bool:
    """Send an HTML email via Gmail SMTP. Returns True on success."""
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD or not config.RECIPIENT_EMAIL:
        print("Error: Email credentials not configured. Check your .env file.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_ADDRESS
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_ADDRESS, config.RECIPIENT_EMAIL, msg.as_string())
        print(f"Digest email sent to {config.RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
