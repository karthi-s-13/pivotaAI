"""
AI Conversation Database Models.

Represents conversations and messages for the Pivota AI chat system.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class Conversation(Base):
    """Represents an AI chat conversation."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User context (supports both admin and IAM users)
    user_id = Column(String(36), nullable=False, index=True)
    user_type = Column(String(20), default="admin", nullable=False)  # admin, iam

    # Data context
    data_source_id = Column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    provider = Column(String(50), nullable=False)  # postgresql, mysql, mongodb, supabase
    database_name = Column(String(255), nullable=False)
    schema_name = Column(String(255), nullable=True)  # NULL for MongoDB

    # Conversation metadata
    title = Column(String(500), default="New Conversation", nullable=False)
    organization_id = Column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
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
    data_source = relationship("DataSource")
    organization = relationship("Organization")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )


class ConversationMessage(Base):
    """Represents a single message in an AI conversation."""

    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)  # text, sql, query_result, error

    # Structured metadata (sql, execution_time_ms, row_count, etc.)
    # Never stores credentials
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
