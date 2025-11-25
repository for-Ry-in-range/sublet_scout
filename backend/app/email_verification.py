import os
import bcrypt
import resend
from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "no-reply@example.com")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="email-verify")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def make_verification_link(email: str, name: str | None, password_hash: str) -> str:
    token = serializer.dumps({"email": email, "name": name, "password_hash": password_hash})
    return f"{APP_URL}/verify?token={token}"

def send_verification_email(to_email: str, verify_url: str):
    html = f"""
      <div style="font-family:system-ui,-apple-system,Arial,sans-serif">
        <h2>Verify your email</h2>
        <p>Click the link below to verify your email and complete signup:</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>This link expires in 24 hours.</p>
      </div>
    """
    return resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Verify your email",
        "html": html,
    })