"""
Database session management.

Provides the get_db dependency for FastAPI route injection.
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.db.base import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Yields a session and ensures it is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
