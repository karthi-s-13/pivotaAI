"""
Pivota Authorization System.

Handles permission verification for standard and IAM users.
"""

from sqlalchemy.orm import Session
from app.core.exceptions import raise_forbidden
from app.models.user import User
from app.models.iam_user import IAMUser
from app.models.iam_policy import IAMPolicy


def check_permission(user: User | IAMUser, permission_name: str, db: Session) -> None:
    """
    Verify if the user has the required permission.
    Raises a 403 Forbidden HTTP exception if permission is denied.
    """
    # Check if this is an IAM user
    is_iam = getattr(user, "iam_id", None) is not None
    
    if not is_iam:
        # Standard admin users bypass all checks (always permitted)
        if getattr(user, "role", None) == "admin":
            return
        return

    # For IAM users, verify they have the required permission in their policy
    if not user.policy_id:
        raise_forbidden("No access policy assigned to this IAM account.")

    policy = db.query(IAMPolicy).filter(IAMPolicy.id == user.policy_id).first()
    if not policy:
        raise_forbidden("Assigned access policy not found.")

    import json
    try:
        perms = policy.permissions if isinstance(policy.permissions, dict) else json.loads(policy.permissions)
    except Exception:
        perms = {}

    if not perms.get(permission_name, False):
        raise_forbidden(f"Access denied: You do not have the required permission ({permission_name}).")
