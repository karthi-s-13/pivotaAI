"""
Auth Pivota Pydantic Schemas.

Request/response models for auth service endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# --- Requests ---

class LoginRequest(BaseModel):
    """Login with email + password."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class SendOTPRequest(BaseModel):
    """Request to send OTP to user's email."""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Verify the email OTP code."""
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6)


class VerifyTOTPRequest(BaseModel):
    """Verify a TOTP code (called by Pivota backend)."""
    user_id: str
    totp_code: str = Field(..., min_length=6, max_length=6)


# --- Responses ---

class AuthTokenResponse(BaseModel):
    """Auth service session token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    is_email_verified: bool


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class TOTPCodeResponse(BaseModel):
    """Current TOTP code response."""
    code: str
    remaining_seconds: int
    total_seconds: int = 30


class TOTPVerifyResponse(BaseModel):
    """Result of TOTP code verification."""
    valid: bool
    message: str
