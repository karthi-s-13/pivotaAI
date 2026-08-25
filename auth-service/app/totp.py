"""
TOTP (Time-based One-Time Password) Generator.

Generates deterministic 6-digit codes that rotate every 30 seconds.
Uses HMAC-SHA256 with a shared secret key + user ID + time window.
Both Auth Pivota and Pivota Backend share the same secret for verification.
"""

import hmac
import hashlib
import struct
import time

from app.config import settings


TOTP_INTERVAL = 30  # seconds


def _get_time_step() -> int:
    """Get the current 30-second time window index."""
    return int(time.time()) // TOTP_INTERVAL


def _generate_hmac(secret: str, user_id: str, time_step: int) -> bytes:
    """Generate HMAC-SHA256 digest for the given inputs."""
    message = f"{user_id}:{time_step}".encode("utf-8")
    key = secret.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).digest()


def _truncate_to_6_digits(digest: bytes) -> str:
    """Dynamic truncation to extract a 6-digit code from HMAC digest."""
    # Use last nibble to determine offset (standard HOTP truncation)
    offset = digest[-1] & 0x0F
    # Extract 4 bytes from the offset
    code_bytes = digest[offset:offset + 4]
    # Convert to integer, mask MSB, take modulo 10^6
    code_int = struct.unpack(">I", code_bytes)[0] & 0x7FFFFFFF
    code = code_int % 1000000
    return str(code).zfill(6)


def generate_totp(user_id: str) -> tuple[str, int]:
    """
    Generate the current TOTP code for a user.

    Returns:
        Tuple of (6-digit code string, remaining seconds in this window).
    """
    current_time = time.time()
    time_step = int(current_time) // TOTP_INTERVAL
    remaining = TOTP_INTERVAL - (int(current_time) % TOTP_INTERVAL)

    digest = _generate_hmac(settings.TOTP_SECRET_KEY, user_id, time_step)
    code = _truncate_to_6_digits(digest)

    return code, remaining


def verify_totp(user_id: str, submitted_code: str, window: int = 1) -> bool:
    """
    Verify a TOTP code with a tolerance window.

    Checks the current time step and ±window adjacent steps to account
    for slight clock drift or user delay.

    Args:
        user_id: The user's unique identifier.
        submitted_code: The 6-digit code to verify.
        window: Number of adjacent time steps to check (default 1 = ±30s).

    Returns:
        True if the code matches any valid time step.
    """
    current_step = _get_time_step()

    for offset in range(-window, window + 1):
        step = current_step + offset
        digest = _generate_hmac(settings.TOTP_SECRET_KEY, user_id, step)
        expected_code = _truncate_to_6_digits(digest)
        if hmac.compare_digest(submitted_code, expected_code):
            return True

    return False
