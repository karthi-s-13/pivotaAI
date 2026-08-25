"""
User SQLAlchemy Model.

Represents a Pivota platform user belonging to an organization.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """Represents a user of the Pivota platform."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="admin", nullable=False)  # admin, manager, analyst, viewer

    # Organization
    organization_id = Column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    data_sources = relationship("DataSource", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
