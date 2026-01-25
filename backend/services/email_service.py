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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@example.com")
SENDER_NAME = os.getenv("SENDER_NAME", "Small Voice")

def send_invitation_email(email, token):
    """招待メール送信（環境に応じて分岐）"""
    invitation_link = f"{FRONTEND_URL}/invite?token={token}"
    subject = "【Small Voice】アカウント招待のお知らせ"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Small Voice へようこそ</h2>
            <p>Small Voice システムへの招待が届きました。</p>
            <p>以下のボタンをクリックして、パスワードを設定してください。</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{invitation_link}" 
                   style="background-color: #3498db; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    パスワードを設定する
                </a>
            </div>
            <p style="color: #7f8c8d; font-size: 14px;">
                ※ このリンクの有効期限は24時間です。<br>
                ※ ボタンが機能しない場合は、以下のURLをコピーしてブラウザに貼り付けてください：<br>
                <a href="{invitation_link}" style="color: #3498db;">{invitation_link}</a>
            </p>
            <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
            <p style="color: #95a5a6; font-size: 12px;">
                このメールに心当たりがない場合は、お手数ですが破棄してください。<br>
                Small Voice System - {FRONTEND_URL}
            </p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Small Voice へようこそ

Small Voice システムへの招待が届きました。
以下のリンクからパスワードを設定してください。

{invitation_link}

※ このリンクの有効期限は24時間です。

---
このメールに心当たりがない場合は、お手数ですが破棄してください。
Small Voice System - {FRONTEND_URL}
    """

    return _send_email(email, subject, html_body, text_body, "MOCK INVITATION EMAIL")

def generate_reset_token():
    return secrets.token_urlsafe(32)

def send_reset_email(email, token):
    """パスワードリセットメール送信（環境に応じて分岐）"""
    reset_link = f"{FRONTEND_URL}/invite?token={token}"
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
