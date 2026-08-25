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


# --- Responses ---

class UserResponse(BaseModel):
    """User data returned in API responses."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    organization_id: str
    organization_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
