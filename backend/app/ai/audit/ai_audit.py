"""
AI Audit Logging Service.

Integrates Pivota AI actions into the system's core audit trails.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def audit_ai_action(
    db: Session,
    user_id: str,
    organization_id: str,
    conversation_id: str,
    data_source_id: str,
    provider: str,
    intent: str,
    sql_generated: Optional[str] = None,
    execution_time: Optional[int] = None,
    row_count: Optional[int] = None,
    success: bool = True,
) -> AuditLog:
    """Record an AI chat action into the audit logs table."""
    details = {
        "conversation_id": conversation_id,
        "data_source_id": data_source_id,
        "provider": provider,
        "intent": intent,
        "sql_generated": sql_generated[:1000] if sql_generated else None, # limit size
        "execution_time_ms": execution_time,
        "row_count": row_count,
        "success": success,
    }

    log = AuditLog(
        action="AI_CHAT_REQUEST",
        resource_type="conversation",
        resource_id=conversation_id,
        details=json.dumps(details),
        user_id=user_id,
        organization_id=organization_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    logger.info(f"Audited AI Chat Request for user {user_id} in conversation {conversation_id}")
    return log
