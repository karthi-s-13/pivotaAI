"""
LangGraph Nodes for Pivota AI Chat Workflow.

Defines the individual steps/computations in the conversation graph.
"""

import json
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.ai.config import ai_settings
from app.ai.providers.llm.ollama_provider import get_llm_provider
from app.ai.schema.schema_service import (
    get_schema_for_data_source,
    format_schema_for_llm,
    get_table_names_for_data_source,
)
from app.ai.schema.schema_retriever import retrieve_relevant_schemas
from app.ai.query.query_validator import validate_sql_query, validate_mongo_query
from app.ai.query.query_executor import execute_read_query, execute_mongo_query
from app.ai.security.ai_authorization import verify_ai_access, verify_data_source_access
from app.ai.security.prompt_security import sanitize_query_results, check_for_injection
from app.ai.prompts import system_prompt
from app.ai.langgraph.state import PivotaChatState

logger = logging.getLogger(__name__)


async def load_conversation(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Load conversation context and initialize history."""
    logger.info("Node: load_conversation")
    # In a full deployment, this node would load conversation history from the DB.
    # The history is passed in from the chat service, so we ensure it's in the state.
    history = state.get("conversation_history", [])
    
    # Verify AI access first
    db: Session = SessionLocal()
    try:
        from app.models.user import User
        # Resolve user
        user = db.query(User).filter(User.id == state["user_id"]).first()
        if not user:
            from app.models.iam_user import IAMUser
            user = db.query(IAMUser).filter(IAMUser.id == state["user_id"]).first()
        
        if user:
            verify_ai_access(user, db)
    except Exception as e:
        logger.error(f"AI access check failed: {e}")
        return {"error": f"Access Denied: {str(e)}"}
    finally:
        db.close()

    # Get database table names directly to help classification
    db = SessionLocal()
    try:
        tables = get_table_names_for_data_source(
            db, state["data_source_id"], state["organization_id"]
        )
    except Exception as e:
        logger.warning(f"Failed to fetch table list: {e}")
        tables = []
    finally:
        db.close()

    return {
        "conversation_history": history,
        "available_tables": tables,
        "stream_events": [{"type": "conversation_loaded"}]
    }


async def resolve_context(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Verify database connection and access permissions."""
    logger.info("Node: resolve_context")
    if state.get("error"):
        return {}

    db: Session = SessionLocal()
    try:
        from app.models.user import User
        user = db.query(User).filter(User.id == state["user_id"]).first()
        if not user:
            from app.models.iam_user import IAMUser
            user = db.query(IAMUser).filter(IAMUser.id == state["user_id"]).first()
            
        if not user:
            return {"error": "User not found"}

        # Verify data source ownership/permissions
        ds = verify_data_source_access(user, db, state["data_source_id"])
        
        return {
            "provider": ds.provider,
            "database": state.get("database") or ds.database_name or "",
            "schema": state.get("schema") or "public",
            "stream_events": state.get("stream_events", []) + [{"type": "context_resolved"}]
        }
    except Exception as e:
        logger.error(f"Context resolution failed: {e}")
        return {"error": f"Failed to resolve data context: {str(e)}"}
    finally:
        db.close()


async def retrieve_schema(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Semantic schema retrieval using pgVector."""
    logger.info("Node: retrieve_schema")
    if state.get("error"):
        return {}

    user_msg = state["user_message"]
    data_source_id = state["data_source_id"]

    try:
        # Perform similarity search to find top matching tables/metadata
        search_results = retrieve_relevant_schemas(user_msg, data_source_id, top_k=5)
        
        # If no results (not indexed yet), fallback to loading full schema
        relevant_tables = []
        if search_results:
            relevant_tables = [r.metadata.get("table") for r in search_results if r.metadata.get("table")]
            relevant_tables = list(set(relevant_tables)) # Deduplicate

        # Fetch actual schema definitions from metadata DB for these tables
        db: Session = SessionLocal()
        try:
            schema_data = get_schema_for_data_source(
                db=db,
                data_source_id=data_source_id,
                organization_id=state["organization_id"],
                database_name=state["database"],
                schema_name=state["schema"]
            )
            
            # Format context block
            formatted_schema = format_schema_for_llm(schema_data, relevant_tables=relevant_tables if relevant_tables else None)
            
            return {
                "retrieved_schema": formatted_schema,
                "stream_events": state.get("stream_events", []) + [
                    {
                        "type": "schema_retrieved",
                        "tables": relevant_tables
                    }
                ]
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        # Soft fallback: continue without schema (understand_request might fail or guide query editor)
        return {
            "retrieved_schema": "Schema details temporarily unavailable.",
            "stream_events": state.get("stream_events", []) + [{"type": "schema_failed", "error": str(e)}]
        }


async def understand_request(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Classify intent using the LLM with structured output."""
    logger.info("Node: understand_request")
    if state.get("error"):
        return {}

    llm = get_llm_provider()
    
    # Format chat history
    history_lines = []
    for msg in state.get("conversation_history", [])[-5:]:
        history_lines.append(f"{msg['role'].upper()}: {msg['content']}")
    history_context = "\n".join(history_lines) if history_lines else "None"

    tables_str = ", ".join(state.get("available_tables", [])) or "None"

    # Call LLM for classification
    prompt = system_prompt.CLASSIFICATION_PROMPT.format(
        user_message=state["user_message"],
        conversation_context=history_context,
        available_tables=tables_str
    )

    try:
        # Request JSON output
        response_text = await llm.generate_structured(
            prompt=prompt,
            system_prompt="You are an intent classification system. Respond with ONLY valid JSON.",
            temperature=0.0
        )
        
        # Parse JSON
        result = json.loads(response_text)
        intent = result.get("intent", "AMBIGUOUS")
        requires_db = result.get("requires_database", False)
        requires_sql = result.get("requires_sql", False)
        confidence = result.get("confidence", 0.5)

        logger.info(f"Classified intent: {intent} (requires_db={requires_db}, requires_sql={requires_sql})")

        return {
            "intent": intent,
            "requires_database": requires_db,
            "requires_sql": requires_sql,
            "intent_confidence": confidence,
            "stream_events": state.get("stream_events", []) + [
                {
                    "type": "intent_classified",
                    "intent": intent,
                    "requires_database": requires_db
                }
            ]
        }
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        # Default fallback: Treat as general conversation if classification fails
        return {
            "intent": "GENERAL_CONVERSATION",
            "requires_database": False,
            "requires_sql": False,
            "intent_confidence": 1.0,
            "stream_events": state.get("stream_events", []) + [{"type": "classification_failed"}]
        }


async def generate_sql(state: PivotaChatState) -> Dict[str, Any]:
    """Node: LLM generates a read-only query (SQL or MongoDB JSON)."""
    logger.info("Node: generate_sql")
    if state.get("error"):
        return {}

    llm = get_llm_provider()
    provider = state["provider"]

    # Format history
    history_lines = []
    for msg in state.get("conversation_history", [])[-5:]:
        history_lines.append(f"{msg['role'].upper()}: {msg['content']}")
    history_context = "\n".join(history_lines) if history_lines else "None"

    if provider == "mongodb":
        # Generate MongoDB query (JSON)
        prompt = system_prompt.MONGO_GENERATION_PROMPT.format(
            schema_context=state["retrieved_schema"],
            user_message=state["user_message"],
            conversation_context=history_context
        )
        try:
            response_text = await llm.generate_structured(prompt, temperature=0.1)
            # Ensure it is valid JSON
            query_data = json.loads(response_text)
            return {
                "generated_query": json.dumps(query_data),
                "query_type": "MONGO_QUERY",
                "stream_events": state.get("stream_events", []) + [
                    {
                        "type": "sql_generated",
                        "sql": json.dumps(query_data, indent=2),
                        "query_type": "MONGO_QUERY"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"MongoDB query generation failed: {e}")
            return {"error": "Failed to generate a valid MongoDB query."}
    else:
        # Generate SQL
        prompt = system_prompt.SQL_GENERATION_PROMPT.format(
            schema_context=state["retrieved_schema"],
            user_message=state["user_message"],
            conversation_context=history_context,
            provider=provider
        )
        try:
            sql = await llm.generate(
                prompt=prompt,
                system_prompt="You are a SQL generation service. Return ONLY the raw SQL query. No markdown formatting, no explanations, no backticks.",
                temperature=0.1
            )
            # Clean up SQL
            sql_clean = sql.strip()
            if sql_clean.startswith("```sql"):
                sql_clean = sql_clean[6:]
            if sql_clean.startswith("```"):
                sql_clean = sql_clean[3:]
            if sql_clean.endswith("```"):
                sql_clean = sql_clean[:-3]
            sql_clean = sql_clean.strip()

            return {
                "generated_query": sql_clean,
                "query_type": "SQL_QUERY",
                "stream_events": state.get("stream_events", []) + [
                    {
                        "type": "sql_generated",
                        "sql": sql_clean,
                        "query_type": "SQL_QUERY"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return {"error": f"Failed to generate SQL query: {str(e)}"}


async def validate_sql(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Enforce read-only and prevent SQL injection or destructive operations."""
    logger.info("Node: validate_sql")
    if state.get("error"):
        return {}

    query_str = state["generated_query"]
    query_type = state["query_type"]

    if query_type == "MONGO_QUERY":
        try:
            query_dict = json.loads(query_str)
            validation = validate_mongo_query(query_dict)
        except Exception as e:
            return {"error": f"Invalid MongoDB query JSON generated: {e}"}
    else:
        validation = validate_sql_query(query_str)

    if not validation.is_safe:
        logger.warning(f"Query validation rejected: {validation.message}")
        return {
            "validation_error": validation.message,
            "error": f"Query Safety Violation: {validation.message}",
            "stream_events": state.get("stream_events", []) + [
                {
                    "type": "validation_failed",
                    "message": validation.message
                }
            ]
        }

    return {
        "validated_query": validation.sanitized_query or query_str,
        "stream_events": state.get("stream_events", []) + [{"type": "query_validated"}]
    }


async def permission_check(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Verify IAM permission of the user requesting the data query."""
    logger.info("Node: permission_check")
    if state.get("error"):
        return {}

    db: Session = SessionLocal()
    try:
        from app.models.user import User
        user = db.query(User).filter(User.id == state["user_id"]).first()
        if not user:
            from app.models.iam_user import IAMUser
            user = db.query(IAMUser).filter(IAMUser.id == state["user_id"]).first()

        if not user:
            return {"error": "User not found"}

        # Validate that the user can execute SELECT queries
        verify_ai_access(user, db)
        
        return {
            "stream_events": state.get("stream_events", []) + [{"type": "permission_checked"}]
        }
    except Exception as e:
        logger.error(f"Permission validation failed: {e}")
        return {"error": f"Authorization Error: {str(e)}"}
    finally:
        db.close()


async def execute_query(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Run the query against the connector and fetch rows."""
    logger.info("Node: execute_query")
    if state.get("error"):
        return {}

    query_str = state["validated_query"]
    query_type = state["query_type"]
    data_source_id = state["data_source_id"]
    org_id = state["organization_id"]
    provider = state["provider"]

    db: Session = SessionLocal()
    try:
        # Emit query start event
        events = state.get("stream_events", []) + [{"type": "query_started"}]

        if query_type == "MONGO_QUERY":
            query_dict = json.loads(query_str)
            res = execute_mongo_query(
                db=db,
                data_source_id=data_source_id,
                organization_id=org_id,
                query=query_dict,
                max_rows=ai_settings.AI_MAX_ROWS
            )
        else:
            res = execute_read_query(
                db=db,
                data_source_id=data_source_id,
                organization_id=org_id,
                query=query_str,
                provider=provider,
                max_rows=ai_settings.AI_MAX_ROWS
            )

        if not res.success:
            logger.error(f"Database query execution failed: {res.error}")
            return {
                "query_error": res.error,
                "error": f"Database Execution Error: {res.error}",
                "stream_events": events + [{"type": "query_failed", "error": res.error}]
            }

        # Apply prompt security injection check on retrieved row contents
        # Treats database contents as untrusted data
        rows_str = json.dumps(res.rows)
        if check_for_injection(rows_str):
            return {
                "error": "Security Alert: Possible prompt injection attempt detected inside database records.",
                "stream_events": events + [{"type": "query_failed", "error": "Security check failed on retrieved data"}]
            }

        # Sanitize sensitive fields (e.g. passwords) and truncate long columns
        sanitized_rows = sanitize_query_results(res.columns, res.rows)

        # Build execution summary metadata
        query_result = {
            "columns": res.columns,
            "rows": sanitized_rows,
            "row_count": len(sanitized_rows),
            "execution_time_ms": res.execution_time_ms,
            "truncated": res.truncated
        }

        return {
            "query_result": query_result,
            "stream_events": events + [
                {
                    "type": "query_completed",
                    "row_count": query_result["row_count"],
                    "columns": query_result["columns"],
                    "rows": query_result["rows"],
                    "execution_time_ms": query_result["execution_time_ms"]
                }
            ]
        }
    except Exception as e:
        logger.error(f"Execute query node failed: {e}")
        return {"error": f"Database Error: {str(e)}"}
    finally:
        db.close()


async def interpret_result(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Give execution results to the LLM to format response."""
    logger.info("Node: interpret_result")
    if state.get("error"):
        return {}

    llm = get_llm_provider()
    query_result = state["query_result"]
    
    # Format rows/columns into compact layout for LLM
    rows = query_result["rows"]
    cols = query_result["columns"]
    row_count = query_result["row_count"]
    truncated = query_result["truncated"]
    
    # Keep result representation tiny to avoid blowing prompt window
    sample_rows = rows[:15]
    result_str_lines = []
    if sample_rows:
        result_str_lines.append(" | ".join(cols))
        result_str_lines.append("-" * 30)
        for r in sample_rows:
            result_str_lines.append(" | ".join(str(r.get(c, "")) for c in cols))
    result_data = "\n".join(result_str_lines) if sample_rows else "No rows returned."

    prompt = system_prompt.RESULT_INTERPRETATION_PROMPT.format(
        user_message=state["user_message"],
        query=state["validated_query"],
        row_count=row_count,
        truncated_notice=" (Results truncated to show top sample)" if truncated else "",
        result_data=result_data
    )

    try:
        final_ans = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt.SYSTEM_PROMPT,
            temperature=0.2
        )
        return {
            "final_response": final_ans,
            "stream_events": state.get("stream_events", []) + [{"type": "result_interpreted"}]
        }
    except Exception as e:
        logger.error(f"Interpretation failed: {e}")
        return {"error": f"Failed to interpret results: {str(e)}"}


async def conversational_response(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Answer general conversation or schema inquiries directly."""
    logger.info("Node: conversational_response")
    if state.get("error"):
        return {}

    llm = get_llm_provider()
    intent = state["intent"]
    
    if intent == "SQL_EXPLANATION":
        # Extract SQL block from user message or history
        import re
        sql_match = re.search(r"select\s+.*", state["user_message"], re.IGNORECASE | re.DOTALL)
        sql_query = sql_match.group(0) if sql_match else "SELECT * FROM data;"
        
        prompt = system_prompt.SQL_EXPLANATION_PROMPT.format(sql_query=sql_query)
    elif intent == "DATABASE_METADATA":
        # System instructions with table lists and context
        prompt = f"""Based on the schema context below, answer the user's questions about the database metadata.
        
        Schema Context:
        {state["retrieved_schema"]}
        
        User Inquiry:
        {state["user_message"]}"""
    else:
        # General conversation fallback
        tables_str = ", ".join(state.get("available_tables", [])) or "None"
        prompt = system_prompt.CONVERSATIONAL_PROMPT.format(
            provider=state.get("provider", "unknown"),
            database=state.get("database", "unknown"),
            schema=state.get("schema", "unknown"),
            available_tables=tables_str
        )

    try:
        ans = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt.SYSTEM_PROMPT,
            temperature=0.2
        )
        return {
            "final_response": ans,
            "stream_events": state.get("stream_events", []) + [{"type": "conversational_completed"}]
        }
    except Exception as e:
        logger.error(f"Conversational generation failed: {e}")
        return {"error": f"Failed to generate response: {str(e)}"}


async def final_response(state: PivotaChatState) -> Dict[str, Any]:
    """Node: Format final response payload (handles errors)."""
    logger.info("Node: final_response")
    events = state.get("stream_events", [])

    if state.get("error"):
        err_msg = state["error"]
        events.append({"type": "error", "message": err_msg})
        return {
            "final_response": f"❌ {err_msg}",
            "stream_events": events
        }

    events.append({"type": "message_complete"})
    return {
        "stream_events": events
    }
