from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, expires_minutes: int | None = None, extra_claims: Dict[str, Any] | None = None) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.access_token_expires_minutes)
    return _create_token(subject=subject, expire_delta=expire_delta, token_type="access", extra_claims=extra_claims)


def create_refresh_token(subject: str, expires_minutes: int | None = None) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.refresh_token_expires_minutes)
    return _create_token(subject=subject, expire_delta=expire_delta, token_type="refresh")


def _create_token(*, subject: str, expire_delta: timedelta, token_type: str, extra_claims: Dict[str, Any] | None = None) -> str:
    expire = datetime.now(tz=UTC) + expire_delta
    payload: Dict[str, Any] = {"sub": subject, "exp": expire, "type": token_type}
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise InvalidTokenError("Invalid token") from exc
    return payload


class InvalidTokenError(Exception):
    ...
