"""
LangGraph Workflow Definition.

Assembles nodes into a compiled state machine graph.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.ai.langgraph.state import PivotaChatState
from app.ai.langgraph.nodes import (
    load_conversation,
    resolve_context,
    retrieve_schema,
    understand_request,
    generate_sql,
    validate_sql,
    permission_check,
    execute_query,
    interpret_result,
    conversational_response,
    final_response,
)

logger = logging.getLogger(__name__)


def route_request(state: PivotaChatState) -> Literal["conversational_response", "generate_sql", "final_response"]:
    """Conditional routing edge based on classified request intent."""
    if state.get("error"):
        return "final_response"

    intent = state.get("intent", "GENERAL_CONVERSATION")
    requires_db = state.get("requires_database", False)

    logger.info(f"Routing check - Intent: {intent}, Requires DB: {requires_db}")

    if requires_db:
        return "generate_sql"
    
    return "conversational_response"


# Initialize the workflow graph
workflow = StateGraph(PivotaChatState)

# Add nodes
workflow.add_node("load_conversation", load_conversation)
workflow.add_node("resolve_context", resolve_context)
workflow.add_node("retrieve_schema", retrieve_schema)
workflow.add_node("understand_request", understand_request)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("validate_sql", validate_sql)
workflow.add_node("permission_check", permission_check)
workflow.add_node("execute_query", execute_query)
workflow.add_node("interpret_result", interpret_result)
workflow.add_node("conversational_response", conversational_response)
workflow.add_node("final_response", final_response)

# Define entry and linear flow
workflow.add_edge(START, "load_conversation")
workflow.add_edge("load_conversation", "resolve_context")
workflow.add_edge("resolve_context", "retrieve_schema")
workflow.add_edge("retrieve_schema", "understand_request")

# Routing based on intent
workflow.add_conditional_edges(
    "understand_request",
    route_request,
    {
        "generate_sql": "generate_sql",
        "conversational_response": "conversational_response",
        "final_response": "final_response"
    }
)

# SQL path execution
workflow.add_edge("generate_sql", "validate_sql")
workflow.add_edge("validate_sql", "permission_check")
workflow.add_edge("permission_check", "execute_query")
workflow.add_edge("execute_query", "interpret_result")
workflow.add_edge("interpret_result", "final_response")

# Conversational path execution
workflow.add_edge("conversational_response", "final_response")

# Final entry before completion
workflow.add_edge("final_response", END)

# Compile graph
compiled_graph = workflow.compile()
