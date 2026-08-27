"""
AI Authorization Service.

Validates user access to data sources and conversations
for AI operations, using existing Pivota IAM infrastructure.
"""

import logging
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.conversation import Conversation
from app.core.authorization import check_permission
from app.core.exceptions import raise_forbidden, raise_not_found

logger = logging.getLogger(__name__)


def verify_ai_access(user, db: Session) -> None:
    """
    Verify that the user has permission to use Pivota AI.

    Requires 'run_select_queries' permission (same as query editor).
    """
    check_permission(user, "run_select_queries", db)


def verify_data_source_access(
    user,
    db: Session,
    data_source_id: str,
) -> DataSource:
    """
    Verify the user has access to a specific data source.

    Returns the DataSource if access is granted.
    """
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == data_source_id,
            DataSource.organization_id == user.organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        raise_not_found("Data source not found or access denied.")
    return ds


def verify_conversation_ownership(
    user,
    db: Session,
    conversation_id: str,
) -> Conversation:
    """
    Verify the user owns a specific conversation.

    Returns the Conversation if ownership is confirmed.
    """
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.organization_id == user.organization_id,
        )
        .first()
    )
    if not conv:
        raise_not_found("Conversation not found.")
    return conv
