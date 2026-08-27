"""
Unit Tests for AI Authorization Services.
"""

import pytest
from unittest.mock import MagicMock

from app.core.exceptions import HTTPException
from app.ai.security.ai_authorization import (
    verify_ai_access,
    verify_data_source_access,
    verify_conversation_ownership,
)
from app.models.user import User
from app.models.data_source import DataSource
from app.models.conversation import Conversation


def test_verify_ai_access_admin():
    """Verify that admin users bypass IAM checks and have access."""
    db_mock = MagicMock()
    user = User(id="user-1", role="admin", organization_id="org-1")
    
    # Should run without raising exceptions
    verify_ai_access(user, db_mock)


def test_verify_ai_access_iam_allowed():
    """Verify that IAM users with run_select_queries permission have access."""
    db_mock = MagicMock()
    
    # Mock IAM User and Policy
    user = MagicMock()
    user.id = "iam-1"
    user.iam_id = "EMP-100"
    user.policy_id = "policy-1"
    user.organization_id = "org-1"
    
    policy_mock = MagicMock()
    policy_mock.permissions = {"run_select_queries": True}
    
    db_mock.query().filter().first.return_value = policy_mock
    
    # Should run successfully
    verify_ai_access(user, db_mock)


def test_verify_ai_access_iam_denied():
    """Verify that IAM users without run_select_queries permission are blocked."""
    db_mock = MagicMock()
    
    # Mock IAM User and Policy
    user = MagicMock()
    user.id = "iam-1"
    user.iam_id = "EMP-100"
    user.policy_id = "policy-1"
    user.organization_id = "org-1"
    
    policy_mock = MagicMock()
    policy_mock.permissions = {"run_select_queries": False}
    
    db_mock.query().filter().first.return_value = policy_mock
    
    # Should raise HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        verify_ai_access(user, db_mock)
    assert exc_info.value.status_code == 403


def test_verify_data_source_access_success():
    """Verify access is granted to owning organization's data source."""
    db_mock = MagicMock()
    user = User(id="user-1", role="admin", organization_id="org-1")
    
    ds = DataSource(id="ds-1", organization_id="org-1", status="active")
    db_mock.query().filter().first.return_value = ds
    
    resolved = verify_data_source_access(user, db_mock, "ds-1")
    assert resolved.id == "ds-1"


def test_verify_data_source_access_isolation():
    """Verify access is denied if the data source belongs to another organization."""
    db_mock = MagicMock()
    user = User(id="user-1", role="admin", organization_id="org-1")
    
    # Data source belongs to org-2
    db_mock.query().filter().first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        verify_data_source_access(user, db_mock, "ds-2")
    assert exc_info.value.status_code == 404


def test_verify_conversation_ownership_success():
    """Verify conversation access is granted to the owner."""
    db_mock = MagicMock()
    user = User(id="user-1", role="admin", organization_id="org-1")
    
    conv = Conversation(id="conv-1", user_id="user-1", organization_id="org-1")
    db_mock.query().filter().first.return_value = conv
    
    resolved = verify_conversation_ownership(user, db_mock, "conv-1")
    assert resolved.id == "conv-1"


def test_verify_conversation_ownership_isolation():
    """Verify conversation access is denied if it belongs to another user."""
    db_mock = MagicMock()
    user = User(id="user-1", role="admin", organization_id="org-1")
    
    # Query returns None because filter user_id="user-1" fails
    db_mock.query().filter().first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        verify_conversation_ownership(user, db_mock, "conv-2")
    assert exc_info.value.status_code == 404
