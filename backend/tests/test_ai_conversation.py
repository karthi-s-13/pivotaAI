"""
Integration Tests for AI Conversations REST API.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        role="admin",
        organization_id="test-org-123",
        is_active=True,
    )


@pytest.fixture
def client(mock_user):
    """Override user authentication dependency and return TestClient."""
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_active_user, None)


@patch("app.api.v1.ai.create_conversation")
def test_api_create_conversation_endpoint(mock_create, client):
    """Test POST /api/v1/ai/conversations endpoint."""
    mock_conv = MagicMock()
    mock_conv.id = "conv-999"
    mock_conv.title = "New Conversation"
    mock_conv.provider = "postgresql"
    mock_conv.database_name = "sales"
    mock_conv.schema_name = "public"
    mock_conv.data_source_id = "ds-111"
    mock_conv.created_at.isoformat.return_value = "2026-08-26T12:00:00"
    mock_conv.updated_at.isoformat.return_value = "2026-08-26T12:00:00"
    
    mock_create.return_value = mock_conv

    response = client.post(
        "/api/v1/ai/conversations",
        json={
            "data_source_id": "ds-111",
            "database": "sales",
            "schema_name": "public",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "conv-999"
    assert data["database_name"] == "sales"
    assert data["provider"] == "postgresql"
