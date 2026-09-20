"""Password hashing and small, dependency-free bearer-token helpers."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

import bcrypt

from app.core.config import settings


class SecurityConfigurationError(RuntimeError):
    """Raised when a required security setting has not been configured."""


def hash_secret(value: str) -> str:
    """Hash a password or recovery string using bcrypt (never encrypt it)."""
    return bcrypt.hashpw(
        value.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    ).decode("utf-8")


def verify_secret(value: str, stored_hash: str) -> bool:
    """Safely compare a plaintext value with a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(value.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_access_token(*, user_id: str, email: str) -> tuple[str, int]:
    """Create a short signed JWT-like bearer token without storing plaintext data.

    The project only needs token issuance at this point. When authenticated API
    routes are added, they can verify the same HS256 token using ``JWT_SECRET``.
    """
    if not settings.jwt_secret:
        raise SecurityConfigurationError("JWT_SECRET must be configured before users can log in.")

    now = int(time.time())
    expires_in = settings.access_token_ttl_minutes * 60
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64url(
        json.dumps(
            {"sub": user_id, "email": email, "iat": now, "exp": now + expires_in},
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = _b64url(hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}", expires_in


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify the locally issued HS256 token and return its safe payload."""
    if not settings.jwt_secret:
        raise SecurityConfigurationError("JWT_SECRET must be configured before authenticated routes can be used.")
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode("ascii")
        expected = _b64url(hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        padded_payload = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded_payload).decode("utf-8"))
        if not isinstance(claims.get("sub"), str) or int(claims.get("exp", 0)) < int(time.time()):
            raise ValueError("expired or malformed token")
        return claims
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid or expired access token.") from exc
