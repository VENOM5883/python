"""Хеширование паролей (PBKDF2) и JWT-токены."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.exceptions import AuthError

ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int, role: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role, "iat": now,
               "exp": now + timedelta(minutes=settings.jwt_ttl_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired") from None
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token") from None
