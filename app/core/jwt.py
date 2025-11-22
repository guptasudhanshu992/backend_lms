from datetime import datetime, timedelta
from app.config.settings import settings
import secrets

ALGORITHM = "HS256"

# Prefer python-jose but fall back to PyJWT if jose isn't available.
try:
    from jose import jwt as jose_jwt, JWTError as JoseError

    def _encode(payload: dict) -> str:
        return jose_jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    def _decode(token: str):
        return jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

    _jwt_exc = JoseError

except Exception:
    # Fallback to PyJWT
    try:
        import jwt as pyjwt
        from jwt import PyJWTError as PyJWTExc

        def _encode(payload: dict) -> str:
            return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

        def _decode(token: str):
            return pyjwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        _jwt_exc = PyJWTExc
    except Exception:
        _encode = None
        _decode = None
        _jwt_exc = Exception


def _make_payload(subject: str, typ: str, expires_delta: int | None, extra_claims: dict | None = None):
    now = datetime.utcnow()
    if expires_delta:
        exp = now + timedelta(seconds=expires_delta)
    else:
        exp = now + (timedelta(minutes=15) if typ == 'access' else timedelta(days=7))
    # Use a consistent timestamp calculation
    exp_timestamp = int((exp - datetime(1970, 1, 1)).total_seconds())
    payload = {"sub": str(subject), "exp": exp_timestamp, "type": typ, "jti": secrets.token_urlsafe(16)}
    if extra_claims:
        payload.update(extra_claims)
    return payload


def create_access_token(subject: str, expires_delta: int | None = None, extra_claims: dict | None = None):
    """Create JWT access token for user authentication"""
    payload = _make_payload(subject, 'access', expires_delta, extra_claims)
    if not _encode:
        raise RuntimeError("No JWT library available. Install 'python-jose' or 'PyJWT'.")
    return _encode(payload)


def create_refresh_token(subject: str, expires_delta: int | None = None, extra_claims: dict | None = None):
    """Create JWT refresh token for token renewal"""
    payload = _make_payload(subject, 'refresh', expires_delta, extra_claims)
    if not _encode:
        raise RuntimeError("No JWT library available. Install 'python-jose' or 'PyJWT'.")
    return _encode(payload)


def create_verification_token(subject: str):
    """Create token for email verification"""
    exp = datetime.utcnow() + timedelta(hours=24)
    exp_timestamp = int((exp - datetime(1970, 1, 1)).total_seconds())
    payload = {"sub": str(subject), "exp": exp_timestamp, "type": "email_verify"}
    if not _encode:
        raise RuntimeError("No JWT library available.")
    return _encode(payload)


def create_reset_token(subject: str):
    """Create token for password reset"""
    exp = datetime.utcnow() + timedelta(hours=1)
    exp_timestamp = int((exp - datetime(1970, 1, 1)).total_seconds())
    payload = {"sub": str(subject), "exp": exp_timestamp, "type": "password_reset"}
    if not _encode:
        raise RuntimeError("No JWT library available.")
    return _encode(payload)


def decode_token(token: str):
    """Decode and validate JWT token"""
    if not _decode:
        return None
    try:
        return _decode(token)
    except _jwt_exc as e:
        # Add logging to debug token decode issues
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JWT decode error: {e}")
        return None
