"""
AI Conversation Service.

Manages CRUD operations for chat conversations, verifying ownership and organization bounds.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage
from app.models.data_source import DataSource
from app.schemas.ai import ConversationCreate, ConversationResponse
from app.core.exceptions import raise_forbidden, raise_not_found
from app.ai.providers.llm.ollama_provider import get_llm_provider
from app.ai.prompts import system_prompt

logger = logging.getLogger(__name__)


def create_conversation(
    db: Session,
    req: ConversationCreate,
    user_id: str,
    user_type: str,
    organization_id: str,
) -> Conversation:
    """Create a new AI conversation after verifying data source access."""
    # Verify data source exists and belongs to the user's organization
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == req.data_source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found or access denied.")

    # Create the conversation
    conv = Conversation(
        user_id=user_id,
        user_type=user_type,
        data_source_id=req.data_source_id,
        provider=ds.provider,
        database_name=req.database,
        schema_name=req.schema_name,
        title="New Conversation",
        organization_id=organization_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    
    logger.info(f"Created conversation {conv.id} for user {user_id}")
    return conv


def list_conversations(
    db: Session,
    user_id: str,
    organization_id: str,
) -> List[Conversation]:
    """List all conversations for a user, sorted by updated_at desc."""
    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.organization_id == organization_id,
        )
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def get_conversation(
    db: Session,
    conversation_id: str,
    user_id: str,
    organization_id: str,
) -> Conversation:
    """Get a single conversation, verifying ownership."""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.organization_id == organization_id,
        )
        .first()
    )
    if not conv:
        raise_not_found("Conversation not found.")
    return conv


def delete_conversation(
    db: Session,
    conversation_id: str,
    user_id: str,
    organization_id: str,
) -> None:
    """Delete a conversation, verifying ownership."""
    conv = get_conversation(db, conversation_id, user_id, organization_id)
    db.delete(conv)
    db.commit()
    logger.info(f"Deleted conversation {conversation_id}")


async def update_conversation_title_from_message(
    db: Session,
    conversation_id: str,
    first_message: str,
) -> str:
    """Generate and update a conversation's title using the LLM based on its first message."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        return "New Conversation"

    # Default fallback title
    title = first_message[:30] + "..." if len(first_message) > 30 else first_message
    
    try:
        llm = get_llm_provider()
        prompt = system_prompt.TITLE_GENERATION_PROMPT.format(first_message=first_message)
        
        # Check if LLM is online
        if await llm.health_check():
            generated = await llm.generate(
                prompt=prompt,
                system_prompt="You are a title generation utility. Respond with ONLY the generated title.",
                max_tokens=20
            )
            generated = generated.strip().strip('"').strip("'")
            if generated and "error" not in generated.lower():
                title = generated
    except Exception as e:
        logger.warning(f"Failed to generate conversation title: {e}")

    conv.title = title
    db.commit()
    db.refresh(conv)
    logger.info(f"Updated conversation {conversation_id} title to: '{title}'")
    return title
