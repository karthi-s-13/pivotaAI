"""
AI Pydantic Schemas.

Request/response models for the Pivota AI chat API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    """Request to create a new AI conversation."""
    data_source_id: str
    database: str
    schema_name: Optional[str] = None  # NULL for MongoDB


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: str
    title: str
    provider: str
    database_name: str
    schema_name: Optional[str] = None
    data_source_id: str
    data_source_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: List[ConversationResponse] = []
    total: int = 0


# --- Chat Schemas ---

class ChatRequest(BaseModel):
    """Request to send a chat message."""
    conversation_id: str
    message: str = Field(..., min_length=1, max_length=10000)


class ChatStreamEvent(BaseModel):
    """A single event in the chat stream (SSE)."""
    type: str  # message_start, text_delta, sql_generated, query_started, query_completed, message_complete, error
    content: Optional[str] = None
    sql: Optional[str] = None
    query_type: Optional[str] = None  # SQL_QUERY, MONGO_QUERY
    row_count: Optional[int] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[int] = None
    message: Optional[str] = None  # For error type
    message_id: Optional[str] = None


# --- Message Schemas ---

class MessageResponse(BaseModel):
    """Response for a single message."""
    id: str
    role: str
    content: str
    message_type: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """Response for listing messages."""
    messages: List[MessageResponse] = []
    conversation_id: str


# --- Data Context Schemas ---

class DatabaseContextItem(BaseModel):
    """A single database within a data source."""
    name: str
    schemas: List[str] = []


class DataSourceContextItem(BaseModel):
    """A data source with its databases."""
    id: str
    name: str
    provider: str
    health_status: str
    databases: List[DatabaseContextItem] = []


class DataContextResponse(BaseModel):
    """Available data contexts for the current user."""
    data_sources: List[DataSourceContextItem] = []


# --- Health Schemas ---

class AIHealthResponse(BaseModel):
    """AI system health status."""
    status: str  # ready, degraded, unavailable
    llm_available: bool
    llm_model: str
    embedding_available: bool
    embedding_model: str
    vector_store_available: bool
    message: Optional[str] = None


# --- Schema Indexing ---

class SchemaIndexRequest(BaseModel):
    """Request to index a data source's schema."""
    data_source_id: str


class SchemaIndexResponse(BaseModel):
    """Response for schema indexing."""
    status: str  # success, failed
    documents_indexed: int = 0
    message: Optional[str] = None
