
import secrets

def send_invitation_email(email, token):
    """招待メール送信（モック: ログとUIに表示）"""
    # 実際にはここにメール送信処理 (SendGrid, SES, SMTP等) を実装
    invitation_link = f"http://localhost:3000/invite?token={token}"
    print(f"--- [MOCK INVITATION EMAIL] To: {email} ---")
    print(f"Subject: Small Voice 招待のお知らせ")
    print(f"Body: 以下のリンクからパスワードを設定してログインしてください。")
    print(f"{invitation_link}")
    print(f"(有効期限: 24時間)")
    print("--------------------------------")
    return True

def generate_reset_token():
    return secrets.token_urlsafe(32)

def send_reset_email(email, token):
    """パスワードリセットメール送信（モック）"""
    reset_link = f"http://localhost:3000/invite?token={token}"
    print(f"--- [MOCK RESET EMAIL] To: {email} ---")
    print(f"Subject: パスワードリセットのご案内")
    print(f"Body: 以下のリンクからパスワードを再設定してください。")
    print(f"{reset_link}")
    print(f"(有効期限: 1時間)")
    print("---------------------------------------")
    return True
