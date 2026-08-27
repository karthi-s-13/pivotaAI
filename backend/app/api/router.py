"""
API Router.

Aggregates all v1 API routes into a single router.
"""

from fastapi import APIRouter

from app.api.v1 import auth, data_sources, dashboard, catalog, ai


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(data_sources.router)
api_router.include_router(dashboard.router)
api_router.include_router(catalog.router)
api_router.include_router(ai.router)
