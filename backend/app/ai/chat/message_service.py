"""
AI Message Service.

Manages message persistence and retrieval for AI conversations.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage
from app.schemas.ai import MessageResponse

logger = logging.getLogger(__name__)


def list_messages(
    db: Session,
    conversation_id: str,
) -> List[ConversationMessage]:
    """Retrieve all messages for a conversation, sorted by created_at."""
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )


def save_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    message_type: str = "text",
    metadata_json: Optional[Dict[str, Any]] = None,
) -> ConversationMessage:
    """Save a new message to the database."""
    # Ensure any binary/special values are removed from metadata before JSON storage
    clean_metadata = None
    if metadata_json:
        try:
            # Test serialization
            json.dumps(metadata_json)
            clean_metadata = metadata_json
        except Exception:
            logger.warning("Failed to serialize message metadata, saving without metadata")
            clean_metadata = {"error": "Unserializable metadata"}

    msg = ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_type=message_type,
        metadata_json=clean_metadata,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    logger.debug(f"Saved message {msg.id} ({role}) for conversation {conversation_id}")
    return msg
