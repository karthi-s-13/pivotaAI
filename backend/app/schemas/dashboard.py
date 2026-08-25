"""
Dashboard Pydantic Schemas.

Response models for dashboard statistics and activity.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""
    data_sources_count: int = 0
    databases_count: int = 0
    tables_count: int = 0
    columns_count: int = 0
    connected_count: int = 0
    error_count: int = 0


class RecentActivityItem(BaseModel):
    """A single recent activity entry."""
    id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    user_name: Optional[str] = None
    timestamp: datetime


class RecentActivityResponse(BaseModel):
    """Recent activity list."""
    items: List[RecentActivityItem] = []


class DataSourceHealthItem(BaseModel):
    """Health status of a data source."""
    id: str
    name: str
    provider_type: str
    connection_status: str
    last_tested_at: Optional[datetime] = None
    environment: str


class DashboardResponse(BaseModel):
    """Full dashboard response."""
    stats: DashboardStats
    recent_activity: List[RecentActivityItem] = []
    data_source_health: List[DataSourceHealthItem] = []
