"""
FastAPI Dependencies.

Provides injectable dependencies for database sessions and current user.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import oauth2_scheme, get_current_user


def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the current user from JWT.

    Usage in routes:
        @router.get("/protected")
        def protected(user: User = Depends(get_current_active_user)):
            ...
    """
    return get_current_user(db, token)
