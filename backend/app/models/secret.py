"""
Secret SQLAlchemy Model.

Represents an encrypted database credential stored in a separate table.
"""

import uuid

from sqlalchemy import Column, String, Text

from app.db.base import Base


class Secret(Base):
    """Stores encrypted database credentials mapped to a unique ID reference."""

    __tablename__ = "secrets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    encrypted_value = Column(Text, nullable=False)
