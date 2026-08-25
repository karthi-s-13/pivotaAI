"""
AuditLog SQLAlchemy Model.

Records important actions for traceability.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    """Records an auditable event in the system."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(100), nullable=False, index=True)  # LOGIN, DATA_SOURCE_CREATED, etc.
    resource_type = Column(String(100), nullable=True)  # data_source, user, etc.
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)  # JSON string with extra context
    ip_address = Column(String(45), nullable=True)

    # User & Organization
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")
