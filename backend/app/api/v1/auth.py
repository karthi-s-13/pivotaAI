"""
Authentication API Routes.

Handles signup, login, token refresh, user profile, and 2FA verification.
"""

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    Verify2FARequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
    SignupPendingResponse,
)
from app.services import auth_service, audit_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupPendingResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user and organization. Returns pending 2FA status."""
    result = auth_service.signup(db, request)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="SIGNUP",
        organization_id=result.user.organization_id,
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
        details={"email": result.user.email},
    )

    return SignupPendingResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        user=result.user,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return tokens."""
    result = auth_service.login(db, request.email, request.password)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="LOGIN",
        organization_id=result.user.organization_id,
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
    )

    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    return auth_service.refresh_tokens(db, request.refresh_token)


@router.post("/verify-2fa", response_model=MessageResponse)
def verify_2fa(
    request: Verify2FARequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Verify the 6-digit TOTP code from Auth Pivota.

    On success, marks the user as 2FA verified and grants full access.
    Uses the shared TOTP secret key to verify the code locally
    (same algorithm as Auth Pivota service).
    """
    import hmac
    import hashlib
    import struct
    import time
    from app.config import settings

    TOTP_INTERVAL = 30

    def _generate_hmac(secret: str, user_id: str, time_step: int) -> bytes:
        message = f"{user_id}:{time_step}".encode("utf-8")
        key = secret.encode("utf-8")
        return hmac.new(key, message, hashlib.sha256).digest()

    def _truncate_to_6_digits(digest: bytes) -> str:
        offset = digest[-1] & 0x0F
        code_bytes = digest[offset:offset + 4]
        code_int = struct.unpack(">I", code_bytes)[0] & 0x7FFFFFFF
        return str(code_int % 1000000).zfill(6)

    # Check current time step and ±1 window
    current_step = int(time.time()) // TOTP_INTERVAL
    is_valid = False

    for offset in range(-1, 2):
        step = current_step + offset
        digest = _generate_hmac(settings.TOTP_SECRET_KEY, user.id, step)
        expected = _truncate_to_6_digits(digest)
        if hmac.compare_digest(request.code, expected):
            is_valid = True
            break

    if not is_valid:
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("Invalid or expired 2FA code. Please try again.")

    # Mark user as 2FA verified
    user.is_2fa_verified = True
    db.commit()

    # Log audit event
    audit_service.log_event(
        db=db,
        action="2FA_VERIFIED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
    )

    return MessageResponse(message="2FA verification successful. Welcome to Pivota!")


@router.get("/me", response_model=UserResponse)
def get_me(
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    return auth_service.serialize_user_response(db, user)


# --- IAM Helpers ---

def generate_iam_id(db: Session) -> str:
    from app.models.iam_user import IAMUser
    import random
    count = db.query(IAMUser).count()
    for _ in range(10):
        val = 1000 + count + random.randint(1, 99)
        candidate = f"EMP-{val}"
        if not db.query(IAMUser).filter(IAMUser.iam_id == candidate).first():
            return candidate
    return f"EMP-{1000 + count + 1}"


def generate_temp_password() -> str:
    import secrets
    import string
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
    ]
    password += [secrets.choice(chars) for _ in range(9)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def send_iam_credentials_email(
    admin_name: str,
    employee_email: str,
    iam_id: str,
    temp_password: str,
    login_url: str,
) -> bool:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from app.config import settings

    if not settings.SMTP_EMAIL or not settings.SMTP_APP_PASSWORD:
        print(f"[DEV MODE] IAM Email to {employee_email}: ID={iam_id}, Pass={temp_password}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Pivota Access Details"
    msg["From"] = f"Pivota Access Management <{settings.SMTP_EMAIL}>"
    msg["To"] = employee_email

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8f9fa; padding: 40px;">
        <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 40px; border: 1px solid #e0e0e0;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="font-size: 22px; font-weight: 700; color: #1a1a1a; margin: 0;">Pivota Access Granted</h1>
            </div>

            <p style="color: #333; font-size: 15px; line-height: 1.6;">
                Hello,
            </p>
            <p style="color: #333; font-size: 15px; line-height: 1.6;">
                Administrator <strong>{admin_name}</strong> has created an IAM user account for you on Pivota.
            </p>

            <div style="background: #f0f0f0; border-radius: 8px; padding: 20px; margin: 24px 0;">
                <table style="width: 100%; font-size: 14px;">
                    <tr>
                        <td style="color: #666; padding: 4px 0;"><strong>IAM User ID:</strong></td>
                        <td style="color: #000; padding: 4px 0;">{iam_id}</td>
                    </tr>
                    <tr>
                        <td style="color: #666; padding: 4px 0;"><strong>Temporary Password:</strong></td>
                        <td style="color: #000; padding: 4px 0;">{temp_password}</td>
                    </tr>
                    <tr>
                        <td style="color: #666; padding: 4px 0;"><strong>Login URL:</strong></td>
                        <td style="color: #000; padding: 4px 0;"><a href="{login_url}">{login_url}</a></td>
                    </tr>
                </table>
            </div>

            <p style="color: #333; font-size: 15px; line-height: 1.6; font-weight: bold;">
                Instructions for first login:
              </p>
              <ol style="color: #333; font-size: 14px; line-height: 1.6; padding-left: 20px;">
                  <li>Click the login link above.</li>
                  <li>Enter your Email, IAM User ID, and Temporary Password.</li>
                  <li>You will be prompted to choose a new permanent password immediately.</li>
              </ol>

            <p style="color: #999; font-size: 12px; text-align: center; margin-top: 32px;">
                This invitation is sent automatically by Pivota.
            </p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, employee_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send IAM credentials email: {e}")
        raise e


# --- IAM Endpoints ---

from typing import List
from app.models.iam_user import IAMUser
from app.models.iam_policy import IAMPolicy
from app.schemas.auth import (
    IAMLoginRequest,
    IAMResetPasswordRequest,
    IAMUserCreateRequest,
    IAMLoginResponse,
    IAMUserResponse,
    IAMPolicyResponse,
)

@router.get("/iam/policies", response_model=List[IAMPolicyResponse])
def get_iam_policies(
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List available policies for current user's organization."""
    from app.core.authorization import check_permission
    check_permission(user, "modify_policies", db)

    policies = db.query(IAMPolicy).filter(IAMPolicy.organization_id == user.organization_id).all()
    return [IAMPolicyResponse(id=p.id, name=p.name, description=p.description) for p in policies]


@router.get("/iam/users", response_model=List[IAMUserResponse])
def get_iam_users(
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all IAM users for organization."""
    from app.core.authorization import check_permission
    check_permission(user, "manage_iam_users", db)

    iam_users = db.query(IAMUser).filter(IAMUser.organization_id == user.organization_id).all()
    
    response = []
    for u in iam_users:
        policy = db.query(IAMPolicy).filter(IAMPolicy.id == u.policy_id).first()
        policy_name = policy.name if policy else "Unknown"
        response.append(IAMUserResponse(
            id=u.id,
            iam_id=u.iam_id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            status=u.status,
            policy_id=u.policy_id,
            policy_name=policy_name,
            created_at=u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
        ))
    return response


@router.post("/iam/users", response_model=IAMUserResponse)
def create_iam_user(
    request: IAMUserCreateRequest,
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new IAM user account and generate random password."""
    from app.core.authorization import check_permission
    check_permission(user, "manage_iam_users", db)

    from app.models.user import User
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        from app.core.exceptions import raise_conflict
        raise_conflict("An account with this email already exists.")

    existing_iam = db.query(IAMUser).filter(IAMUser.email == request.email).first()
    if existing_iam:
        from app.core.exceptions import raise_conflict
        raise_conflict("An IAM user with this email already exists.")

    policy = db.query(IAMPolicy).filter(IAMPolicy.id == request.policy_id, IAMPolicy.organization_id == user.organization_id).first()
    if not policy:
        from app.core.exceptions import raise_not_found
        raise_not_found("Specified policy not found.")

    iam_id = generate_iam_id(db)
    temp_password = generate_temp_password()
    from app.core.security import hash_password

    iam_user = IAMUser(
        iam_id=iam_id,
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(temp_password),
        status="INVITED",
        is_active=True,
        organization_id=user.organization_id,
        policy_id=request.policy_id,
        created_by_id=user.id,
    )
    db.add(iam_user)
    db.commit()
    db.refresh(iam_user)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="IAM_USER_CREATED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="iam_user",
        resource_id=iam_user.id,
        details={"iam_id": iam_id, "email": request.email},
    )

    return IAMUserResponse(
        id=iam_user.id,
        iam_id=iam_user.iam_id,
        email=iam_user.email,
        full_name=iam_user.full_name,
        is_active=iam_user.is_active,
        status=iam_user.status,
        policy_id=iam_user.policy_id,
        policy_name=policy.name,
        created_at=iam_user.created_at.strftime("%Y-%m-%d %H:%M:%S") if iam_user.created_at else "",
    )


@router.post("/iam/users/{user_id}/send-details", response_model=MessageResponse)
def send_iam_user_details(
    user_id: str,
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerates a secure random temporary password and sends access details email to the employee."""
    from app.core.authorization import check_permission
    check_permission(user, "manage_iam_users", db)

    iam_user = db.query(IAMUser).filter(IAMUser.id == user_id, IAMUser.organization_id == user.organization_id).first()
    if not iam_user:
        from app.core.exceptions import raise_not_found
        raise_not_found("IAM user not found.")

    temp_password = generate_temp_password()
    from app.core.security import hash_password
    iam_user.hashed_password = hash_password(temp_password)
    iam_user.status = "INVITED"
    db.commit()

    login_url = "http://localhost:3000/iam/login"
    try:
        send_iam_credentials_email(
            admin_name=user.full_name,
            employee_email=iam_user.email,
            iam_id=iam_user.iam_id,
            temp_password=temp_password,
            login_url=login_url,
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"SMTP Email Send Failed: {str(e)}")

    # Log audit event
    audit_service.log_event(
        db=db,
        action="IAM_DETAILS_SENT",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="iam_user",
        resource_id=iam_user.id,
        details={"iam_id": iam_user.iam_id},
    )

    return MessageResponse(message=f"Access details email successfully sent to {iam_user.email}.")


@router.delete("/iam/users/{user_id}", response_model=MessageResponse)
def delete_iam_user(
    user_id: str,
    user = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an IAM user account."""
    from app.core.authorization import check_permission
    check_permission(user, "manage_iam_users", db)

    iam_user = db.query(IAMUser).filter(IAMUser.id == user_id, IAMUser.organization_id == user.organization_id).first()
    if not iam_user:
        from app.core.exceptions import raise_not_found
        raise_not_found("IAM user not found.")

    db.delete(iam_user)
    db.commit()

    # Log audit event
    audit_service.log_event(
        db=db,
        action="IAM_USER_DELETED",
        organization_id=user.organization_id,
        user_id=user.id,
        resource_type="iam_user",
        resource_id=user_id,
    )

    return MessageResponse(message="IAM user account deleted successfully.")


@router.post("/iam/login", response_model=IAMLoginResponse)
def iam_login(
    request: IAMLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate an IAM user.

    If they need to perform a first-time password reset:
    - Returns password_change_required=True and a temporary reset token.
    If they are already active:
    - Returns full session access and refresh tokens.
    """
    iam_user = db.query(IAMUser).filter(IAMUser.iam_id == request.iam_id).first()
    if not iam_user or iam_user.email != request.email:
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("Invalid Email, IAM User ID, or Password.")

    from app.core.security import verify_password
    if not verify_password(request.password, iam_user.hashed_password):
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("Invalid Email, IAM User ID, or Password.")

    if not iam_user.is_active:
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("IAM user account is deactivated.")

    # Check status
    if iam_user.status in ("INVITED", "FIRST_LOGIN", "PASSWORD_CHANGE_REQUIRED"):
        iam_user.status = "FIRST_LOGIN"
        db.commit()

        # Generate short-lived temp token only for password reset
        from app.core.security import settings
        from datetime import datetime, timezone, timedelta
        from jose import jwt

        temp_data = {
            "sub": iam_user.id,
            "org": iam_user.organization_id,
            "type": "iam_temp_reset",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        temp_token = jwt.encode(temp_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        return IAMLoginResponse(
            message="Password change required for first-time login.",
            password_change_required=True,
            temp_token=temp_token,
        )

    # Generate standard active tokens
    token_data = {
        "sub": iam_user.id,
        "org": iam_user.organization_id,
        "role": "iam",
        "is_iam": True,
    }
    
    # Create iam_access token type
    from app.core.security import settings
    from datetime import datetime, timezone, timedelta
    from jose import jwt
    
    access_data = token_data.copy()
    access_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "iam_access"
    })
    access_token = jwt.encode(access_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    refresh_data = token_data.copy()
    refresh_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    })
    refresh_token = jwt.encode(refresh_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return IAMLoginResponse(
        message="Login successful.",
        password_change_required=False,
        access_token=access_token,
        refresh_token=refresh_token,
        user=auth_service.serialize_user_response(db, iam_user),
    )


@router.post("/iam/reset-password", response_model=TokenResponse)
def iam_reset_password(
    request: IAMResetPasswordRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    """Mandatory first-time password reset flow using the temp token."""
    from app.core.security import decode_token
    from fastapi import Header
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
    except Exception:
        payload = None

    if not payload or payload.get("type") != "iam_temp_reset":
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("Invalid or expired password reset session.")

    user_id = payload.get("sub")
    iam_user = db.query(IAMUser).filter(IAMUser.id == user_id).first()
    if not iam_user:
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("IAM user not found.")

    from app.core.security import verify_password
    if not verify_password(request.temp_password, iam_user.hashed_password):
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("Provided current temporary password is incorrect.")

    if request.new_password != request.confirm_password:
        from app.core.exceptions import raise_unauthorized
        raise_unauthorized("New passwords do not match.")

    from app.core.security import hash_password
    iam_user.hashed_password = hash_password(request.new_password)
    iam_user.status = "ACTIVE"
    db.commit()

    # Generate standard active tokens
    token_data = {
        "sub": iam_user.id,
        "org": iam_user.organization_id,
        "role": "iam",
        "is_iam": True,
    }
    
    from app.core.security import settings
    from datetime import datetime, timezone, timedelta
    from jose import jwt
    
    access_data = token_data.copy()
    access_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "iam_access"
    })
    access_token = jwt.encode(access_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    refresh_data = token_data.copy()
    refresh_data.update({
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    })
    refresh_token = jwt.encode(refresh_data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Log audit event
    audit_service.log_event(
        db=db,
        action="IAM_PASSWORD_CHANGED",
        organization_id=iam_user.organization_id,
        user_id=iam_user.id,
        resource_type="iam_user",
        resource_id=iam_user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=auth_service.serialize_user_response(db, iam_user),
    )

