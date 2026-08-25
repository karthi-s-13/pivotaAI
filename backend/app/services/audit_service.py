"""
Audit Service.

Records auditable events for traceability.
"""

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_event(
    db: Session,
    action: str,
    organization_id: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Record an audit event.

    Args:
        db: Database session.
        action: Event type (e.g., LOGIN, DATA_SOURCE_CREATED).
        organization_id: Tenant ID.
        user_id: Acting user ID.
        resource_type: Type of resource affected.
        resource_id: ID of resource affected.
        details: Additional context as dict (stored as JSON).
        ip_address: Client IP address.

    Returns:
        The created AuditLog record.
    """
    log = AuditLog(
        action=action,
        organization_id=organization_id,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
