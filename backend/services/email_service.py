import secrets
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging

logger = logging.getLogger(__name__)

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@example.com")
SENDER_NAME = os.getenv("SENDER_NAME", "Small Voice")

def send_invitation_email(email, token):
    """招待メール送信（環境に応じて分岐）"""
    invitation_link = f"http://localhost:3000/invite?token={token}"
    subject = "Small Voice 招待のお知らせ"
    body = f"""
    <p>以下のリンクからパスワードを設定してログインしてください。</p>
    <p><a href="{invitation_link}">{invitation_link}</a></p>
    <p>(有効期限: 24時間)</p>
    """
    text_body = f"以下のリンクからパスワードを設定してログインしてください。\n{invitation_link}\n(有効期限: 24時間)"

    return _send_email(email, subject, body, text_body, "MOCK INVITATION EMAIL")

def generate_reset_token():
    return secrets.token_urlsafe(32)

def send_reset_email(email, token):
    """パスワードリセットメール送信（環境に応じて分岐）"""
    reset_link = f"http://localhost:3000/invite?token={token}"
    subject = "パスワードリセットのご案内"
    body = f"""
    <p>以下のリンクからパスワードを再設定してください。</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>(有効期限: 1時間)</p>
    """
    text_body = f"以下のリンクからパスワードを再設定してください。\n{reset_link}\n(有効期限: 1時間)"

    return _send_email(email, subject, body, text_body, "MOCK RESET EMAIL")

def _send_email(to_email, subject, html_body, text_body, mock_title):
    """メール送信の共通内部関数"""
    if ENVIRONMENT == "production":
        # Production: Send via SMTP
        if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.error("SMTP configuration is missing. Cannot send email.")
            return False
            
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
            msg["To"] = to_email

            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Use SMTP_SSL if port is 465, otherwise assume STARTTLS with 587 or similar
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    else:
        # Local: Mock Output
        print(f"--- [{mock_title}] To: {to_email} ---")
        print(f"Subject: {subject}")
        print(f"Body: {text_body}")
        print("--------------------------------")
        return True
