"""
Dashboard Service.

Aggregates statistics and recent activity for the dashboard.
"""

from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.data_source import DataSource
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.dashboard import (
    DashboardStats,
    RecentActivityItem,
    DataSourceHealthItem,
    DashboardResponse,
)


def get_dashboard(db: Session, organization_id: str) -> DashboardResponse:
    """Get full dashboard data for an organization."""
    stats = _get_stats(db, organization_id)
    activity = _get_recent_activity(db, organization_id)
    health = _get_data_source_health(db, organization_id)

    return DashboardResponse(
        stats=stats,
        recent_activity=activity,
        data_source_health=health,
    )


def _get_stats(db: Session, organization_id: str) -> DashboardStats:
    """Calculate aggregated statistics."""
    active_sources = (
        db.query(DataSource)
        .filter(
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .all()
    )

    data_sources_count = len(active_sources)
    databases_count = sum(s.databases_count for s in active_sources)
    tables_count = sum(s.tables_count for s in active_sources)
    columns_count = sum(s.columns_count for s in active_sources)
    connected_count = sum(1 for s in active_sources if s.connection_status == "connected")
    error_count = sum(1 for s in active_sources if s.connection_status == "error")

    return DashboardStats(
        data_sources_count=data_sources_count,
        databases_count=databases_count,
        tables_count=tables_count,
        columns_count=columns_count,
        connected_count=connected_count,
        error_count=error_count,
    )


def _get_recent_activity(
    db: Session, organization_id: str, limit: int = 10
) -> List[RecentActivityItem]:
    """Get recent audit log entries."""
    logs = (
        db.query(AuditLog, User.full_name)
        .outerjoin(User, AuditLog.user_id == User.id)
        .filter(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    items = []
    for log, user_name in logs:
        items.append(
            RecentActivityItem(
                id=log.id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                user_name=user_name,
                timestamp=log.timestamp,
            )
        )

    return items


def _get_data_source_health(
    db: Session, organization_id: str
) -> List[DataSourceHealthItem]:
    """Get health status of all data sources."""
    sources = (
        db.query(DataSource)
        .filter(
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .order_by(DataSource.name)
        .all()
    )

    return [
        DataSourceHealthItem(
            id=s.id,
            name=s.name,
            provider_type=s.provider_type,
            connection_status=s.connection_status,
            last_tested_at=s.last_tested_at,
            environment=s.environment,
        )
        for s in sources
    ]
