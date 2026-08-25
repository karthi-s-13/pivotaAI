"""
Authentication Service.

Handles user signup, login, token generation, and user retrieval.
"""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import SignupRequest, UserResponse, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import raise_unauthorized, raise_conflict, raise_not_found


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


def signup(db: Session, request: SignupRequest) -> TokenResponse:
    """
    Register a new user and create their organization.

    Returns tokens so the user is immediately authenticated.
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise_conflict("A user with this email already exists")

    # Create organization
    org = Organization(
        name=request.organization_name,
        slug=_slugify(request.organization_name),
    )
    db.add(org)
    db.flush()  # Get org.id

    # Create user
    user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role="admin",  # First user in org is admin
        organization_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    # Generate tokens
    token_data = {"sub": user.id, "org": org.id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            organization_id=org.id,
            organization_name=org.name,
        ),
    )


def login(db: Session, email: str, password: str) -> TokenResponse:
    """
    Authenticate a user and return tokens.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise_unauthorized("Invalid email or password")

    if not user.is_active:
        raise_unauthorized("Account is deactivated")

    # Load organization
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    # Generate tokens
    token_data = {"sub": user.id, "org": user.organization_id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            organization_id=user.organization_id,
            organization_name=org.name if org else None,
        ),
    )


def refresh_tokens(db: Session, refresh_token_str: str) -> TokenResponse:
    """
    Validate a refresh token and issue new tokens.
    """
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise_unauthorized("Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise_unauthorized("User not found or inactive")

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    # Issue new tokens
    token_data = {"sub": user.id, "org": user.organization_id, "role": user.role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            organization_id=user.organization_id,
            organization_name=org.name if org else None,
        ),
    )


def get_current_user(db: Session, token: str) -> User:
    """
    Extract and validate the current user from a JWT token.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise_unauthorized()

    user_id = payload.get("sub")
    if not user_id:
        raise_unauthorized()

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise_unauthorized("User not found or inactive")

    return user
