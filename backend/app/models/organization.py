"""
Organization SQLAlchemy Model.

Each organization is an isolated tenant in Pivota.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class Organization(Base):
    """Represents a tenant organization in Pivota."""

    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
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
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    iam_users = relationship("IAMUser", back_populates="organization", cascade="all, delete-orphan")
    iam_policies = relationship("IAMPolicy", back_populates="organization", cascade="all, delete-orphan")
