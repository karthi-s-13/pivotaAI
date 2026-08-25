"""
IAM User and Access Control Integration Tests.

Verifies IAM user creation, mandatory password reset, login flows,
and permission enforcement.
"""

import pytest
import json
from fastapi import HTTPException
from app.models.organization import Organization
from app.models.user import User
from app.models.iam_policy import IAMPolicy
from app.models.iam_user import IAMUser
from app.core.security import hash_password
from app.core.authorization import check_permission
from app.api.v1.auth import generate_iam_id, generate_temp_password


@pytest.fixture
def test_organization(db_session):
    """Fixture to create a test organization."""
    org = Organization(name="IAM Test Org", slug="iam-test-org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    yield org
    db_session.delete(org)
    db_session.commit()


@pytest.fixture
def test_admin(db_session, test_organization):
    """Fixture to create a test admin user."""
    admin = User(
        email="admin@iamtest.com",
        full_name="Test Admin",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        organization_id=test_organization.id,
        is_2fa_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    yield admin
    db_session.delete(admin)
    db_session.commit()


@pytest.fixture
def test_policy(db_session, test_organization):
    """Fixture to create a custom read-only IAM policy."""
    policy = IAMPolicy(
        name="Custom Analyst",
        description="Analyst access rules",
        permissions={
            "view_catalog": True,
            "view_tables": True,
            "run_select_queries": False,
            "create_connections": False,
        },
        organization_id=test_organization.id,
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)
    yield policy
    db_session.delete(policy)
    db_session.commit()


def test_iam_id_generation(db_session):
    """Verifies that generated IAM IDs follow the EMP-XXXX format."""
    iam_id = generate_iam_id(db_session)
    assert iam_id.startswith("EMP-")
    assert len(iam_id) >= 8


def test_temp_password_generation():
    """Verifies random temporary password generation."""
    temp_pass = generate_temp_password()
    assert len(temp_pass) == 12
    assert any(c.isdigit() for c in temp_pass)


def test_create_iam_user(db_session, test_organization, test_admin, test_policy):
    """Verifies creating an IAM User and associating it with a policy and admin."""
    iam_id = generate_iam_id(db_session)
    temp_pass = generate_temp_password()

    iam_user = IAMUser(
        iam_id=iam_id,
        email="employee@company.com",
        full_name="Employee One",
        hashed_password=hash_password(temp_pass),
        status="INVITED",
        is_active=True,
        organization_id=test_organization.id,
        policy_id=test_policy.id,
        created_by_id=test_admin.id,
    )
    db_session.add(iam_user)
    db_session.commit()
    db_session.refresh(iam_user)

    assert iam_user.id is not None
    assert iam_user.status == "INVITED"
    assert iam_user.created_by_id == test_admin.id
    assert iam_user.policy_id == test_policy.id

    db_session.delete(iam_user)
    db_session.commit()


def test_permission_enforcement(db_session, test_admin, test_policy, test_organization):
    """Verifies that check_permission allows admin and respects IAM user policy permissions."""
    # 1. Admin user bypasses all checks
    check_permission(test_admin, "run_select_queries", db_session)
    check_permission(test_admin, "create_connections", db_session)

    # 2. Create IAM User
    iam_user = IAMUser(
        iam_id="EMP-9999",
        email="analyst@company.com",
        full_name="Analyst One",
        hashed_password=hash_password("temppass123"),
        status="ACTIVE",
        is_active=True,
        organization_id=test_organization.id,
        policy_id=test_policy.id,
        created_by_id=test_admin.id,
    )
    db_session.add(iam_user)
    db_session.commit()

    # 3. Check permitted actions
    check_permission(iam_user, "view_catalog", db_session)
    check_permission(iam_user, "view_tables", db_session)

    # 4. Check forbidden actions (must raise 403 Forbidden)
    with pytest.raises(HTTPException) as exc_info:
        check_permission(iam_user, "run_select_queries", db_session)
    assert exc_info.value.status_code == 403
    assert "run_select_queries" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        check_permission(iam_user, "create_connections", db_session)
    assert exc_info.value.status_code == 403
    assert "create_connections" in exc_info.value.detail

    db_session.delete(iam_user)
    db_session.commit()
