from __future__ import annotations

from datetime import datetime, timedelta, UTC

from jose import jwt, JWTError
import structlog

from src.config import get_settings

logger = structlog.get_logger()


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create a JWT access token with user claims."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns claims dict or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        logger.warning("jwt_decode_failed")
        return None
