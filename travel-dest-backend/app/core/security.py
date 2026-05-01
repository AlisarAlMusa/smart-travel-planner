"""Small JWT and password helpers for authentication."""

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import Settings


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2 so raw passwords are never stored."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(salt + digest).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify an incoming password against a stored PBKDF2 hash."""
    raw_bytes = base64.b64decode(stored_hash.encode("utf-8"))
    salt = raw_bytes[:16]
    original_digest = raw_bytes[16:]
    check_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(original_digest, check_digest)


def create_access_token(subject: str, settings: Settings) -> str:
    """Create a signed JWT access token for one user id."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate one JWT access token."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

