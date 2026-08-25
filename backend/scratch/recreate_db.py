"""
Database Re-creation Script.

Drops existing tables and recreates them to register the updated schema.
"""

import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.db.base import Base, engine
import app.models  # noqa: F401


def recreate_tables():
    """Drop and recreate all database tables."""
    print("Dropping all existing database tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully!")


if __name__ == "__main__":
    recreate_tables()
