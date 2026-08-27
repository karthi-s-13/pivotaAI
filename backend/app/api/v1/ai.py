"""
AI API Endpoints.

Provides REST operations for managing conversations, retrieving message logs,
fetching data contexts, and executing streaming chat via Server-Sent Events (SSE).
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.iam_user import IAMUser
from app.core.exceptions import raise_forbidden, raise_not_found
from app.ai.config import ai_settings
from app.ai.providers.llm.ollama_provider import get_llm_provider
from app.ai.providers.embeddings import get_embedding_provider
from app.ai.providers.vector_store.pgvector_store import get_vector_store
from app.ai.chat.conversation_service import (
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
)
from app.ai.chat.message_service import list_messages
from app.ai.chat.chat_service import send_chat_message_stream
from app.ai.schema.schema_indexer import index_data_source_schema
from app.ai.security.ai_authorization import verify_ai_access, verify_data_source_access
from app.schemas.ai import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ChatRequest,
    MessageResponse,
    MessageListResponse,
    DataContextResponse,
    DataSourceContextItem,
    DatabaseContextItem,
    AIHealthResponse,
    SchemaIndexResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


@router.post("/conversations", response_model=ConversationResponse)
def api_create_conversation(
    req: ConversationCreate,
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new AI chat conversation."""
    verify_ai_access(user, db)
    
    user_type = "iam" if getattr(user, "iam_id", None) is not None else "admin"
    conv = create_conversation(
        db=db,
        req=req,
        user_id=user.id,
        user_type=user_type,
        organization_id=user.organization_id,
    )
    
    # Resolve datasource name for response representation
    from app.models.data_source import DataSource
    ds = db.query(DataSource).filter(DataSource.id == conv.data_source_id).first()
    ds_name = ds.name if ds else "Unknown"

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        provider=conv.provider,
        database_name=conv.database_name,
        schema_name=conv.schema_name,
        data_source_id=conv.data_source_id,
        data_source_name=ds_name,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.get("/conversations", response_model=ConversationListResponse)
def api_list_conversations(
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all AI conversations for the logged in user."""
    verify_ai_access(user, db)
    
    conversations = list_conversations(db, user.id, user.organization_id)
    
    responses = []
    for c in conversations:
        # Load message count and last message preview
        msg_count = len(c.messages)
        last_msg = c.messages[-1].content if msg_count > 0 else None
        
        # Get datasource name
        from app.models.data_source import DataSource
        ds = db.query(DataSource).filter(DataSource.id == c.data_source_id).first()
        ds_name = ds.name if ds else "Unknown"
        
        responses.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                provider=c.provider,
                database_name=c.database_name,
                schema_name=c.schema_name,
                data_source_id=c.data_source_id,
                data_source_name=ds_name,
                created_at=c.created_at,
                updated_at=c.updated_at,
                last_message=last_msg,
                message_count=msg_count,
            )
        )
        
    return ConversationListResponse(conversations=responses, total=len(responses))


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def api_get_conversation(
    conversation_id: str = Path(...),
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a single conversation record."""
    verify_ai_access(user, db)
    
    c = get_conversation(db, conversation_id, user.id, user.organization_id)
    msg_count = len(c.messages)
    last_msg = c.messages[-1].content if msg_count > 0 else None
    
    from app.models.data_source import DataSource
    ds = db.query(DataSource).filter(DataSource.id == c.data_source_id).first()
    ds_name = ds.name if ds else "Unknown"
    
    return ConversationResponse(
        id=c.id,
        title=c.title,
        provider=c.provider,
        database_name=c.database_name,
        schema_name=c.schema_name,
        data_source_id=c.data_source_id,
        data_source_name=ds_name,
        created_at=c.created_at,
        updated_at=c.updated_at,
        last_message=last_msg,
        message_count=msg_count,
    )


@router.delete("/conversations/{conversation_id}")
def api_delete_conversation(
    conversation_id: str = Path(...),
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation history."""
    verify_ai_access(user, db)
    delete_conversation(db, conversation_id, user.id, user.organization_id)
    return {"status": "success", "message": "Conversation deleted."}


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def api_list_messages(
    conversation_id: str = Path(...),
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all persisted messages in a conversation."""
    verify_ai_access(user, db)
    
    # Verify ownership first
    get_conversation(db, conversation_id, user.id, user.organization_id)
    
    messages = list_messages(db, conversation_id)
    responses = [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            metadata_json=m.metadata_json,
            created_at=m.created_at,
        )
        for m in messages
    ]
    
    return MessageListResponse(messages=responses, conversation_id=conversation_id)


@router.post("/chat")
async def api_chat_stream(
    req: ChatRequest,
    user = Depends(get_current_active_user),
):
    """Send a chat message and stream responses using Server-Sent Events (SSE)."""
    user_type = "iam" if getattr(user, "iam_id", None) is not None else "admin"
    
    # Returns SSE streaming response
    return StreamingResponse(
        send_chat_message_stream(
            user_id=user.id,
            user_type=user_type,
            organization_id=user.organization_id,
            conversation_id=req.conversation_id,
            message=req.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/context", response_model=DataContextResponse)
def api_get_context(
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all connected database/schema context options available for the user."""
    verify_ai_access(user, db)
    
    # Query all active data sources
    from app.models.data_source import DataSource
    sources = (
        db.query(DataSource)
        .filter(
            DataSource.organization_id == user.organization_id,
            DataSource.status != "deleted",
        )
        .all()
    )
    
    data_sources_list = []
    for s in sources:
        # Construct database mapping from the schema metadata tables
        from app.models.metadata import DatabaseMetadata, SchemaMetadata
        dbs = (
            db.query(DatabaseMetadata)
            .filter(DatabaseMetadata.data_source_id == s.id)
            .all()
        )
        
        databases_list = []
        for d in dbs:
            schemas = (
                db.query(SchemaMetadata.name)
                .filter(SchemaMetadata.database_id == d.id)
                .all()
            )
            schema_names = [sch[0] for sch in schemas]
            databases_list.append(
                DatabaseContextItem(name=d.name, schemas=schema_names)
            )
            
        # Fallback if metadata sync hasn't run yet (directly parse config)
        if not databases_list and s.provider_config:
            dbname = s.provider_config.get("database_name") or s.database_name or "default"
            databases_list.append(
                DatabaseContextItem(name=dbname, schemas=["public"])
            )

        data_sources_list.append(
            DataSourceContextItem(
                id=s.id,
                name=s.name,
                provider=s.provider,
                health_status=s.health_status,
                databases=databases_list,
            )
        )
        
    return DataContextResponse(data_sources=data_sources_list)


@router.get("/health", response_model=AIHealthResponse)
async def api_ai_health():
    """Verify health of local Ollama, huggingface embedding model, and pgVector connection."""
    llm = get_llm_provider()
    embed = get_embedding_provider()
    
    llm_ok = await llm.health_check()
    embed_ok = embed.health_check()
    
    # Check vector store table presence
    from sqlalchemy import text
    from app.db.base import engine
    vector_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM schema_embeddings LIMIT 1;"))
            vector_ok = True
    except Exception:
        # extension might not be loaded yet, index_data_source_schema handles loading it
        pass

    status = "ready"
    msg = None
    if not llm_ok or not embed_ok:
        status = "degraded"
        msg = "Local LLM service (Ollama) or Embedding provider is not fully operational."
    if not llm_ok and not embed_ok:
        status = "unavailable"
        
    return AIHealthResponse(
        status=status,
        llm_available=llm_ok,
        llm_model=ai_settings.LLM_MODEL,
        embedding_available=embed_ok,
        embedding_model=ai_settings.EMBEDDING_MODEL,
        vector_store_available=vector_ok,
        message=msg,
    )


@router.post("/index/{data_source_id}", response_model=SchemaIndexResponse)
def api_index_schema(
    data_source_id: str = Path(...),
    database: Optional[str] = Query(None),
    schema_name: Optional[str] = Query(None),
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Trigger embedding indexing of a specific data source's metadata schema."""
    verify_ai_access(user, db)
    verify_data_source_access(user, db, data_source_id)

    try:
        count = index_data_source_schema(
            db=db,
            data_source_id=data_source_id,
            organization_id=user.organization_id,
            database_name=database,
            schema_name=schema_name,
        )
        return SchemaIndexResponse(
            status="success",
            documents_indexed=count,
            message="Schema indexing completed successfully.",
        )
    except Exception as e:
        logger.error(f"Manual schema indexing failed: {e}")
        return SchemaIndexResponse(
            status="failed",
            documents_indexed=0,
            message=f"Schema indexing failed: {str(e)}",
        )
