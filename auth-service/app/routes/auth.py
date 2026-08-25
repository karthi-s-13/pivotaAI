"""
Auth Pivota Authentication Routes.

Handles login, email OTP sending, and email OTP verification.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
import bcrypt

from app.config import settings
from app.database import get_db
from app.models import User, OTPRecord
from app.schemas import (
    LoginRequest,
    SendOTPRequest,
    VerifyOTPRequest,
    AuthTokenResponse,
    MessageResponse,
)
from app.email_service import create_and_store_otp, verify_otp_code, send_otp_email


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def _create_token(user_id: str, email: str) -> str:
    """Create a JWT session token for the auth service."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "auth_service",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None


@router.post("/login", response_model=AuthTokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.

    Returns a session token for the auth service. The user must
    then verify their email via OTP before accessing TOTP codes.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not _verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    # Check if user has a verified OTP record (email already verified in a previous session)
    has_verified_otp = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.user_id == user.id,
            OTPRecord.is_used == True,
        )
        .first()
    )

    token = _create_token(user.id, user.email)

    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        is_email_verified=has_verified_otp is not None,
    )


@router.post("/send-otp", response_model=MessageResponse)
def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """
    Send a 6-digit OTP to the user's registered email.

    The OTP expires after 5 minutes.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email",
        )

    otp_code = create_and_store_otp(db, user.id, user.email)

    try:
        send_otp_email(user.email, otp_code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}",
        )

    return MessageResponse(
        message=f"Verification code sent to {user.email}",
        success=True,
    )


@router.post("/verify-otp", response_model=MessageResponse)
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify the email OTP code.

    On success, the user's email is considered verified and they can
    access the TOTP code display page.
    """
    is_valid = verify_otp_code(db, request.email, request.otp_code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    return MessageResponse(
        message="Email verified successfully",
        success=True,
    )
