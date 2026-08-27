"""
AI Chat Service.

Orchestrates the LangGraph execution, accumulates events, streams response tokens to SSE,
and persists both user and assistant message records to the database.
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.ai.langgraph.graph import compiled_graph
from app.ai.chat.conversation_service import (
    get_conversation,
    update_conversation_title_from_message,
)
from app.ai.chat.message_service import save_message, list_messages
from app.ai.audit.ai_audit import audit_ai_action

logger = logging.getLogger(__name__)


async def send_chat_message_stream(
    user_id: str,
    user_type: str,
    organization_id: str,
    conversation_id: str,
    message: str,
) -> AsyncGenerator[str, None]:
    """
    Execute the AI graph workflow and yield SSE events to stream output to the UI.
    
    Yields stringified SSE data lines.
    """
    db: Session = SessionLocal()
    
    # 1. Verify access to conversation and load it
    try:
        conv = get_conversation(db, conversation_id, user_id, organization_id)
    except Exception as e:
        logger.error(f"Failed to load conversation: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        db.close()
        return

    # 2. Check if this is the first user message, to trigger title updates later
    is_first_message = len(conv.messages) == 0

    # 3. Persist the user's message
    user_msg_record = save_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=message,
        message_type="text",
    )

    # 4. Load recent conversation history (max 10 messages for state context)
    history_records = list_messages(db, conversation_id)[:-1] # exclude the current user message just saved
    history = [
        {"role": r.role, "content": r.content}
        for r in history_records[-10:]
    ]

    # Initialize graph state input
    initial_state = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "organization_id": organization_id,
        "data_source_id": conv.data_source_id,
        "provider": conv.provider,
        "database": conv.database_name,
        "schema": conv.schema_name,
        "user_message": message,
        "conversation_history": history,
        "stream_events": [],
    }

    # Yield message start event immediately
    yield f"data: {json.dumps({'type': 'message_start'})}\n\n"

    # Start tracking steps and state updates
    final_state: Dict[str, Any] = {}
    
    try:
        # 5. Run the Compiled LangGraph Workflow
        # For Mode 1, we execute the graph step-by-step or stream graph state updates
        async for event in compiled_graph.astream(
            initial_state,
            stream_mode="updates"
        ):
            # Check for node output updates
            for node_name, node_update in event.items():
                logger.debug(f"Graph Node '{node_name}' completed.")
                
                # Capture final state reference
                if node_update and isinstance(node_update, dict):
                    final_state.update(node_update)

                    # Fetch and emit any new stream events from this node execution
                    events: List[Dict[str, Any]] = node_update.get("stream_events", [])
                    
                    # Check for specific structural updates we want to push to UI
                    # E.g. sql_generated, query_started, query_completed
                    for s_evt in events:
                        # Deduplicate or push directly
                        yield f"data: {json.dumps(s_evt)}\n\n"

        # 6. Stream final response text token by token (or chunk response if already constructed by LLM)
        final_response_text = final_state.get("final_response", "")
        error_msg = final_state.get("error", None)

        if error_msg:
            # Yield error event
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            # Save error message record
            save_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=f"❌ {error_msg}",
                message_type="error",
            )
        else:
            # For Mode 1, since we don't have token-level streaming directly wired from langchain-ollama,
            # we simulate word-by-word streaming of the final interpreted answer for conversational response.
            # If the LLM generates a SQL block as part of state, it has already been pushed via `sql_generated`.
            words = final_response_text.split(" ")
            # Batch tokens slightly
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i+chunk_size])
                if i > 0:
                    chunk = " " + chunk
                yield f"data: {json.dumps({'type': 'text_delta', 'content': chunk})}\n\n"
            
            # Save assistant's final message in database
            # Extract metadata (SQL/Query info) if present to store with message
            msg_type = "text"
            msg_metadata = None
            
            if final_state.get("validated_query"):
                msg_type = "sql"
                msg_metadata = {
                    "sql": final_state.get("validated_query"),
                    "query_type": final_state.get("query_type"),
                    "row_count": final_state.get("query_result", {}).get("row_count", 0),
                    "execution_time_ms": final_state.get("query_result", {}).get("execution_time_ms", 0),
                }

            assistant_msg_record = save_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=final_response_text,
                message_type=msg_type,
                metadata_json=msg_metadata,
            )

            # Yield message complete event with the saved database record ID
            yield f"data: {json.dumps({'type': 'message_complete', 'message_id': assistant_msg_record.id})}\n\n"

        # 7. Generate conversation title asynchronously if this was the first message
        if is_first_message:
            try:
                await update_conversation_title_from_message(db, conversation_id, message)
            except Exception as e:
                logger.warning(f"Failed to auto-update conversation title: {e}")

        # 8. Record AI action in audit logs
        try:
            audit_ai_action(
                db=db,
                user_id=user_id,
                organization_id=organization_id,
                conversation_id=conversation_id,
                data_source_id=conv.data_source_id,
                provider=conv.provider,
                intent=final_state.get("intent", "UNKNOWN"),
                sql_generated=final_state.get("validated_query"),
                execution_time=final_state.get("query_result", {}).get("execution_time_ms"),
                row_count=final_state.get("query_result", {}).get("row_count"),
                success=not bool(error_msg),
            )
        except Exception as e:
            logger.warning(f"Failed to audit AI action: {e}")

    except Exception as e:
        logger.error(f"Exception in AI chat processing: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': f'Internal Server Error: {str(e)}'})}\n\n"
    finally:
        db.close()
