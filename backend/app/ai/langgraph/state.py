"""
Pivota AI Chat State.

Typed state definition for the LangGraph workflow.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class PivotaChatState(TypedDict, total=False):
    """Typed state for the Pivota AI LangGraph workflow."""

    # Context identifiers
    conversation_id: str
    user_id: str
    organization_id: str
    data_source_id: str

    # Database context
    provider: str  # postgresql, mysql, mongodb, supabase
    database: str
    schema: Optional[str]

    # User input
    user_message: str

    # Conversation history (recent messages)
    conversation_history: List[Dict[str, str]]  # [{"role": "user", "content": "..."}, ...]

    # Schema retrieval
    retrieved_schema: str  # Formatted schema context for LLM
    available_tables: List[str]

    # Intent classification
    intent: str  # GENERAL_CONVERSATION, DATABASE_METADATA, DATA_QUERY, SQL_GENERATION, SQL_EXPLANATION, AMBIGUOUS
    requires_database: bool
    requires_sql: bool
    intent_confidence: float

    # Query generation
    generated_query: Optional[str]  # SQL string or JSON string for MongoDB
    query_type: Optional[str]  # SQL_QUERY, MONGO_QUERY

    # Query validation
    validated_query: Optional[str]
    validation_error: Optional[str]

    # Query execution
    query_result: Optional[Dict[str, Any]]  # {columns, rows, row_count, execution_time_ms, truncated}
    query_error: Optional[str]

    # Response
    final_response: str

    # Streaming events (accumulated during processing)
    stream_events: List[Dict[str, Any]]

    # Error handling
    error: Optional[str]
