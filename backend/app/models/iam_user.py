"""
IAMUser SQLAlchemy Model.

Represents an IAM account created by an administrator for an employee.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class IAMUser(Base):
    """Represents an IAM user belonging to an organization and policy."""

    __tablename__ = "iam_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    iam_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., EMP-1042
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # INVITED, FIRST_LOGIN, PASSWORD_CHANGE_REQUIRED, ACTIVE
    status = Column(String(50), default="INVITED", nullable=False)

    # Relationships
    organization_id = Column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    policy_id = Column(
        String(36), ForeignKey("iam_policies.id"), nullable=False, index=True
    )
    created_by_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
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
    organization = relationship("Organization", back_populates="iam_users")
    policy = relationship("IAMPolicy", back_populates="iam_users")
    created_by_user = relationship("User", foreign_keys=[created_by_id])
