"""
FastAPI Dependencies.

Provides injectable dependencies for database sessions and current user.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import oauth2_scheme, get_current_user


def get_current_active_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the current user from JWT.
    Enforces 2FA verification for admin users on all endpoints except auth/logout/me.

    Usage in routes:
        @router.get("/protected")
        def protected(user: User = Depends(get_current_active_user)):
            ...
    """
    user = get_current_user(db, token)

    # Check 2FA for Admin users (excluding 2FA verification, logout, and profile retrieve).
    if not getattr(user, "iam_id", None) and user.role == "admin" and not user.is_2fa_verified:
        path = request.url.path
        if not (path.endswith("/auth/verify-2fa") or path.endswith("/auth/logout") or path.endswith("/auth/me")):
            from app.core.exceptions import raise_unauthorized
            raise_unauthorized("2FA verification required")

    return user
