"""
Pivota Backend Test Configuration.

Provides shared fixtures and ensures the app module is importable
without sys.path hacks.
"""

import pytest
from app.db.base import SessionLocal


@pytest.fixture
def db_session():
    """Provide a database session that auto-closes after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
