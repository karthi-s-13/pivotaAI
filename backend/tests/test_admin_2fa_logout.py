import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from app.models.user import User
from app.models.organization import Organization
from app.services.auth_service import login
from app.core.security import hash_password
from app.dependencies import get_current_active_user
from fastapi import Request
from fastapi.exceptions import HTTPException

def test_admin_login_resets_2fa_verified(db_session: Session):
    """Verifies that an admin login resets is_2fa_verified to False."""
    # 1. Create a test organization
    org = Organization(name="Test 2FA Org", slug="test-2fa-org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # 2. Create a test admin user with is_2fa_verified=True
    admin = User(
        email="admin@test2fa.com",
        full_name="Test Admin 2FA",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        organization_id=org.id,
        is_2fa_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    assert admin.is_2fa_verified is True

    # 3. Log in the admin user using the login function
    response = login(db_session, "admin@test2fa.com", "adminpass123")

    # 4. Verify that the login response returns is_2fa_verified as False
    assert response.user.is_2fa_verified is False

    # 5. Verify that in the database, is_2fa_verified is now False
    db_session.refresh(admin)
    assert admin.is_2fa_verified is False

    # Cleanup
    db_session.delete(admin)
    db_session.delete(org)
    db_session.commit()


def test_admin_2fa_dependency_blocking(db_session: Session):
    """Verifies that the get_current_active_user dependency blocks unverified admins on non-exempt paths."""
    # Create an admin user who is NOT 2FA verified
    admin = User(
        email="unverified@test2fa.com",
        full_name="Unverified Admin",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        organization_id="org-123",
        is_2fa_verified=False,
    )

    with patch("app.dependencies.get_current_user", return_value=admin):
        # A. Test for a protected path
        mock_request_protected = MagicMock(spec=Request)
        mock_request_protected.url.path = "/api/v1/catalog/databases"

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(request=mock_request_protected, token="fake-token", db=db_session)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "2FA verification required"

        # B. Test for exempt paths: /auth/me, /auth/verify-2fa, /auth/logout
        for path in ["/api/v1/auth/me", "/api/v1/auth/verify-2fa", "/api/v1/auth/logout"]:
            mock_request_exempt = MagicMock(spec=Request)
            mock_request_exempt.url.path = path

            # Should not raise HTTPException
            user = get_current_active_user(request=mock_request_exempt, token="fake-token", db=db_session)
            assert user == admin
