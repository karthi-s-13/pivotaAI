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
        is_2fa_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    # Pre-populate default policies for the organization
    create_default_policies(db, org.id)

    # Generate tokens
    token_data = {"sub": user.id, "org": org.id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=serialize_user_response(db, user),
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
        user=serialize_user_response(db, user),
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
    if not user:
        from app.models.iam_user import IAMUser
        user = db.query(IAMUser).filter(IAMUser.id == user_id).first()

    if not user or not user.is_active:
        raise_unauthorized("User not found or inactive")

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    # Issue new tokens
    is_iam = getattr(user, "iam_id", None) is not None
    token_data = {
        "sub": user.id,
        "org": user.organization_id,
        "role": getattr(user, "role", "iam"),
        "is_iam": is_iam,
    }
    # For access token, use appropriate type
    access_token_type = "iam_access" if is_iam else "access"
    
    from app.core.security import settings
    from datetime import datetime, timezone, timedelta
    from jose import jwt
    
    # Generate access token with correct type
    access_data = token_data.copy()
    access_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": access_token_type
    })
    access_token = jwt.encode(access_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    # Generate refresh token
    refresh_data = token_data.copy()
    refresh_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    })
    new_refresh_token = jwt.encode(refresh_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=serialize_user_response(db, user),
    )


def get_current_user(db: Session, token: str):
    """
    Extract and validate the current user from a JWT token.
    Supports standard users and IAM users.
    """
    payload = decode_token(token)
    if not payload or payload.get("type") not in ("access", "iam_access"):
        raise_unauthorized()

    user_id = payload.get("sub")
    if not user_id:
        raise_unauthorized()

    if payload.get("type") == "iam_access":
        from app.models.iam_user import IAMUser
        user = db.query(IAMUser).filter(IAMUser.id == user_id).first()
        if not user or not user.is_active:
            raise_unauthorized("IAM user not found or inactive")
        if user.status != "ACTIVE":
            raise_unauthorized("IAM user must complete password reset first")
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise_unauthorized("User not found or inactive")

    return user


def serialize_user_response(db: Session, user) -> UserResponse:
    """Helper to convert User or IAMUser into a unified UserResponse."""
    from app.models.organization import Organization
    from app.models.iam_policy import IAMPolicy
    import json

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    org_name = org.name if org else None

    is_iam = getattr(user, "iam_id", None) is not None

    if is_iam:
        # Load IAM permissions
        policy = db.query(IAMPolicy).filter(IAMPolicy.id == user.policy_id).first()
        permissions = {}
        if policy:
            try:
                permissions = policy.permissions if isinstance(policy.permissions, dict) else json.loads(policy.permissions)
            except Exception:
                permissions = {}

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role="iam",
            is_active=user.is_active,
            is_2fa_verified=True,  # IAM users bypass 2FA
            is_iam=True,
            iam_id=user.iam_id,
            permissions=permissions,
            organization_id=user.organization_id,
            organization_name=org_name,
        )
    else:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_2fa_verified=getattr(user, "is_2fa_verified", False),
            is_iam=False,
            iam_id=None,
            permissions=None,  # Standard user bypasses IAM checks
            organization_id=user.organization_id,
            organization_name=org_name,
        )


def create_default_policies(db: Session, organization_id: str) -> None:
    """Pre-populate default IAM policies for a newly registered organization."""
    from app.models.iam_policy import IAMPolicy

    default_policies = [
        {
            "name": "Data Analyst",
            "description": "Read-only access to catalog, object details, and running SELECT queries.",
            "permissions": {
                "view_catalog": True,
                "view_tables": True,
                "run_select_queries": True,
                "view_data_map": True,
                "create_connections": False,
                "delete_data_sources": False,
                "manage_iam_users": False,
                "modify_policies": False,
            }
        },
        {
            "name": "Data Engineer",
            "description": "Full access to data map, catalog, and managing database connections.",
            "permissions": {
                "view_catalog": True,
                "view_tables": True,
                "run_select_queries": True,
                "view_data_map": True,
                "create_connections": True,
                "delete_data_sources": False,
                "manage_iam_users": False,
                "modify_policies": False,
            }
        },
        {
            "name": "Viewer",
            "description": "Read-only access to catalog and data map. Cannot run queries.",
            "permissions": {
                "view_catalog": True,
                "view_tables": True,
                "run_select_queries": False,
                "view_data_map": True,
                "create_connections": False,
                "delete_data_sources": False,
                "manage_iam_users": False,
                "modify_policies": False,
            }
        },
        {
            "name": "Admin",
            "description": "Full administrative permissions across all system resources and IAM settings.",
            "permissions": {
                "view_catalog": True,
                "view_tables": True,
                "run_select_queries": True,
                "view_data_map": True,
                "create_connections": True,
                "delete_data_sources": True,
                "manage_iam_users": True,
                "modify_policies": True,
            }
        }
    ]

    for p in default_policies:
        # Check if policy already exists
        exists = db.query(IAMPolicy).filter(
            IAMPolicy.name == p["name"],
            IAMPolicy.organization_id == organization_id
        ).first()
        if not exists:
            policy = IAMPolicy(
                name=p["name"],
                description=p["description"],
                permissions=p["permissions"],
                organization_id=organization_id,
            )
            db.add(policy)
    db.commit()
