from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, status

from app.core.security import decode_token


class TokenPair(Dict[str, str]):
    access_token: str
    refresh_token: str


def decode_token_type(token: str, expected_type: str) -> Dict[str, Any]:
    payload = decode_token(token)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload
