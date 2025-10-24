from __future__ import annotations

import uuid
from typing import Iterable, Sequence

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, UserRole


class UserService:
    """Encapsulates user-related persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self, *, limit: int = 50, offset: int = 0) -> tuple[list[User], int]:
        query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.scalars(query)
        users = result.all()
        total = await self.session.scalar(select(func.count()).select_from(User))
        return users, total or 0

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def get_by_email(self, email: EmailStr) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create_user(
        self,
        *,
        email: EmailStr,
        password: str,
        full_name: str | None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        preferences: dict[str, object] | None = None,
        feature_flags: Sequence[str] | None = None,
    ) -> User:
        if await self.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user = User(
            email=str(email).lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=is_active,
            preferences=preferences or {},
            feature_flags=list(feature_flags or []),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_user(self, user: User, *, payload: dict[str, object]) -> User:
        data = dict(payload)
        password = data.pop("password", None)
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
        if password:
            user.hashed_password = hash_password(str(password))
        await self.session.flush()
        return user

    async def change_password(self, user: User, *, new_password: str) -> None:
        user.hashed_password = hash_password(new_password)
        await self.session.flush()
