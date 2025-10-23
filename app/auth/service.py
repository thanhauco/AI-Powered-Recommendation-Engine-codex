from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models import User, UserRole


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        user = await self._get_user_by_email(normalized_email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        user.last_login_at = datetime.now(tz=UTC).isoformat()
        await self.session.flush()
        return user

    async def create_user(self, *, email: str, password: str, full_name: Optional[str], role: UserRole) -> User:
        normalized_email = email.strip().lower()
        existing = await self._get_user_by_email(normalized_email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user = User(email=normalized_email, hashed_password=hash_password(password), full_name=full_name, role=role)
        self.session.add(user)
        await self.session.flush()
        return user

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        return await self.session.scalar(select(User).where(User.email == email))

    async def issue_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(str(user.id), extra_claims={"role": user.role.value})
        refresh = create_refresh_token(str(user.id))
        return access, refresh

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        from app.auth.tokens import decode_token_type

        payload = decode_token_type(refresh_token, expected_type="refresh")
        user_id = payload["sub"]
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        return await self.issue_tokens(user)

    async def change_password(self, user: User, new_password: str) -> None:
        user.hashed_password = hash_password(new_password)
        await self.session.flush()
