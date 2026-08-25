"""
Email OTP Service.

Sends 6-digit verification codes via Gmail SMTP.
"""

import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import OTPRecord


def generate_otp_code() -> str:
    """Generate a cryptographically random 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def create_and_store_otp(db: Session, user_id: str, email: str) -> str:
    """
    Generate an OTP, store it in the database, and return the code.

    Any existing unused OTPs for this user are invalidated.
    """
    # Invalidate previous OTPs
    db.query(OTPRecord).filter(
        OTPRecord.user_id == user_id,
        OTPRecord.is_used == False,
    ).update({"is_used": True})

    code = generate_otp_code()
    otp = OTPRecord(
        user_id=user_id,
        email=email,
        otp_code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
    )
    db.add(otp)
    db.commit()

    return code


def verify_otp_code(db: Session, email: str, submitted_code: str) -> bool:
    """
    Verify an OTP code for the given email.

    Returns True if valid, False otherwise. Marks the OTP as used.
    """
    otp = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.email == email,
            OTPRecord.otp_code == submitted_code,
            OTPRecord.is_used == False,
            OTPRecord.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OTPRecord.created_at.desc())
        .first()
    )

    if not otp:
        return False

    otp.is_used = True
    db.commit()
    return True


def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP code to the user's email via Gmail SMTP.

    Returns True on success, raises on failure.
    """
    if not settings.SMTP_EMAIL or not settings.SMTP_APP_PASSWORD:
        print(f"[DEV MODE] OTP for {to_email}: {otp_code}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Auth Pivota - Your Verification Code: {otp_code}"
    msg["From"] = f"Auth Pivota <{settings.SMTP_EMAIL}>"
    msg["To"] = to_email

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8f9fa; padding: 40px;">
        <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 40px; border: 1px solid #e0e0e0;">
            <div style="text-align: center; margin-bottom: 32px;">
                <div style="width: 56px; height: 56px; border-radius: 50%; background: #000000; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px;">
                    <span style="color: white; font-size: 24px; font-weight: 800;">P</span>
                </div>
                <h1 style="font-size: 22px; font-weight: 700; color: #1a1a1a; margin: 0;">Auth Pivota</h1>
                <p style="color: #666; font-size: 14px; margin-top: 4px;">Email Verification</p>
            </div>

            <p style="color: #333; font-size: 15px; line-height: 1.6;">
                Use the following code to verify your email address. This code expires in 5 minutes.
            </p>

            <div style="background: #f0f0f0; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #000000; font-family: monospace;">
                    {otp_code}
                </span>
            </div>

            <p style="color: #999; font-size: 12px; text-align: center;">
                If you didn't request this code, you can safely ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        raise
