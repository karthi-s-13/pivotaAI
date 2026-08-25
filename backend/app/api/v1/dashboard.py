"""
Dashboard API Routes.

Provides aggregated statistics and recent activity.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get dashboard overview with stats, activity, and health."""
    return dashboard_service.get_dashboard(db, user.organization_id)
