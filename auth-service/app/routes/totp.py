"""
Auth Pivota TOTP Routes.

Handles TOTP code generation (for the auth frontend display)
and TOTP code verification (called by Pivota backend).
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from jose import jwt

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import TOTPCodeResponse, TOTPVerifyResponse, VerifyTOTPRequest
from app.totp import generate_totp, verify_totp


router = APIRouter(prefix="/api/totp", tags=["TOTP"])


def _get_current_user_id(authorization: str = Header(...)) -> str:
    """Extract user ID from the auth service JWT token."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


@router.get("/current-code", response_model=TOTPCodeResponse)
def get_current_code(user_id: str = Depends(_get_current_user_id)):
    """
    Get the current 6-digit TOTP code for the authenticated user.

    The code rotates every 30 seconds. The response includes the
    remaining seconds in the current window for countdown display.
    """
    code, remaining = generate_totp(user_id)

    return TOTPCodeResponse(
        code=code,
        remaining_seconds=remaining,
        total_seconds=30,
    )


@router.post("/verify", response_model=TOTPVerifyResponse)
def verify_code(request: VerifyTOTPRequest, db: Session = Depends(get_db)):
    """
    Verify a TOTP code for a given user.

    This endpoint is called by the Pivota backend to validate
    the 6-digit code that the user copied from the Auth Pivota app.
    Accepts codes from the current window and ±1 adjacent windows
    (90-second total tolerance).
    """
    # Verify user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    is_valid = verify_totp(request.user_id, request.totp_code)

    if is_valid:
        # Mark user as 2FA verified
        user.is_2fa_verified = True
        db.commit()

        return TOTPVerifyResponse(
            valid=True,
            message="2FA verification successful",
        )

    return TOTPVerifyResponse(
        valid=False,
        message="Invalid or expired code. Please try again.",
    )
