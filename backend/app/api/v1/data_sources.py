"""
Data Sources API Routes.

Handles data source CRUD, connection testing, and metadata discovery endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.data_source import (
    ConnectionTestRequest,
    ConnectionTestResult,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
)
from app.services import audit_service, data_source_service
from app.core.authorization import check_permission

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all registered data sources for the user's organization."""
    check_permission(user, "view_catalog", db)
    return data_source_service.list_data_sources(db, user.organization_id)


@router.post("", response_model=DataSourceResponse, status_code=201)
def create_data_source(
    request: DataSourceCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Register a new data source."""
    check_permission(user, "create_connections", db)
    result = data_source_service.create_data_source(db, request, user)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_CREATED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=result.identity.id,
        details={"name": result.identity.name, "provider": result.identity.provider},
    )

    return result


@router.get("/{source_id}", response_model=DataSourceResponse)
def get_data_source(
    source_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get details of a registered data source by ID."""
    check_permission(user, "view_catalog", db)
    return data_source_service.get_data_source(db, source_id, user.organization_id)


@router.put("/{source_id}", response_model=DataSourceResponse)
def update_data_source(
    source_id: str,
    request: DataSourceUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a registered data source configuration."""
    check_permission(user, "create_connections", db)
    result = data_source_service.update_data_source(
        db, source_id, request, user.organization_id
    )

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_UPDATED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
        details={"name": result.identity.name},
    )

    return result


@router.delete("/{source_id}", status_code=204)
def delete_data_source(
    source_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a data source (soft delete)."""
    check_permission(user, "delete_data_sources", db)
    data_source_service.delete_data_source(db, source_id, user.organization_id)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_DELETED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
    )


@router.post("/{source_id}/test", response_model=ConnectionTestResult)
def test_source_connection(
    source_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Test connection for an existing registered data source."""
    check_permission(user, "create_connections", db)
    result = data_source_service.test_connection_for_source(
        db, source_id, user.organization_id
    )

    # Log audit event
    audit_service.log_event(
        db=db,
        action="CONNECTION_TESTED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
        details={"success": result.success, "latency_ms": result.latency_ms},
    )

    return result


@router.post("/test-connection", response_model=ConnectionTestResult)
def test_connection(
    request: ConnectionTestRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Test a connection configuration without registering it."""
    check_permission(user, "create_connections", db)
    return data_source_service.test_connection_unsaved(request)


@router.post("/{source_id}/discover", response_model=DataSourceResponse)
def discover_metadata(
    source_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Manually trigger metadata auto-discovery in the background for a registered data source."""
    check_permission(user, "create_connections", db)
    # Get direct DB record to modify
    from app.models.data_source import DataSource
    db_ds = db.query(DataSource).filter(DataSource.id == source_id, DataSource.organization_id == user.organization_id).first()
    if db_ds:
        db_ds.health_status = "syncing"
        db.commit()

    background_tasks.add_task(
        data_source_service.sync_data_source_background,
        source_id,
        user.organization_id,
        user.id
    )

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_DISCOVERY_STARTED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
    )

    return data_source_service.get_data_source(db, source_id, user.organization_id)


@router.post("/{source_id}/connect", response_model=DataSourceResponse)
def connect_datasource(
    source_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Explicitly establish active connection status for a data source."""
    check_permission(user, "create_connections", db)
    result = data_source_service.connect_source(db, source_id, user.organization_id)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_CONNECTED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
    )

    return result


@router.post("/{source_id}/disconnect", response_model=DataSourceResponse)
def disconnect_datasource(
    source_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Explicitly disconnect a data source."""
    check_permission(user, "create_connections", db)
    result = data_source_service.disconnect_source(db, source_id, user.organization_id)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="DATA_SOURCE_DISCONNECTED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="data_source",
        resource_id=source_id,
    )

    return result
