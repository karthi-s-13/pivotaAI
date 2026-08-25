"""
IAMPolicy SQLAlchemy Model.

Represents an access policy with granular permissions for IAM users.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class IAMPolicy(Base):
    """Represents an access policy containing permission rules."""

    __tablename__ = "iam_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, nullable=False)  # Dict of permission flags

    # Organization association
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
    organization = relationship("Organization", back_populates="iam_policies")
    iam_users = relationship("IAMUser", back_populates="policy")
