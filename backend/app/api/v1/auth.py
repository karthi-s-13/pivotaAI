"""
Authentication API Routes.

Handles signup, login, token refresh, and user profile endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.services import auth_service, audit_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user and organization."""
    result = auth_service.signup(db, request)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="SIGNUP",
        organization_id=result.user.organization_id,
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
        details={"email": result.user.email},
    )

    return result


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return tokens."""
    result = auth_service.login(db, request.email, request.password)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="LOGIN",
        organization_id=result.user.organization_id,
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
    )

    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    return auth_service.refresh_tokens(db, request.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    from app.models.organization import Organization

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        organization_id=user.organization_id,
        organization_name=org.name if org else None,
    )
