"""
Authentication Pydantic Schemas.

Request/response models for login, signup, and token operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# --- Requests ---

class SignupRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    organization_name: str = Field(..., min_length=2, max_length=255)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class Verify2FARequest(BaseModel):
    """2FA verification request with the 6-digit TOTP code."""
    code: str = Field(..., min_length=6, max_length=6)


class IAMLoginRequest(BaseModel):
    """IAM User login request."""
    email: EmailStr
    iam_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class IAMResetPasswordRequest(BaseModel):
    """Mandatory first-time password reset request for IAM user."""
    temp_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)


class IAMUserCreateRequest(BaseModel):
    """Admin request to create an IAM User."""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    policy_id: str = Field(..., min_length=36, max_length=36)


# --- Responses ---

class UserResponse(BaseModel):
    """User data returned in API responses."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    is_2fa_verified: bool = False
    is_iam: bool = False
    iam_id: Optional[str] = None
    permissions: Optional[dict] = None
    organization_id: str
    organization_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class IAMLoginResponse(BaseModel):
    """IAM user specific login response (supports password reset redirect)."""
    message: str
    password_change_required: bool = False
    temp_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[UserResponse] = None


class IAMUserResponse(BaseModel):
    """IAM User representation for admin page list."""
    id: str
    iam_id: str
    email: str
    full_name: str
    is_active: bool
    status: str
    policy_id: str
    policy_name: str
    created_at: str


class IAMPolicyResponse(BaseModel):
    """IAM Access Policy description for dropdown lists."""
    id: str
    name: str
    description: Optional[str] = None


class SignupPendingResponse(BaseModel):
    """Response after signup — user must complete 2FA before access."""
    message: str = "Account created. Please complete 2FA verification."
    pending_2fa: bool = True
    auth_url: str = "http://localhost:3001"
    access_token: str
    refresh_token: str
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

