from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import APIModel, TimestampedModel


class UserBase(APIModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: List[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(APIModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None
    feature_flags: Optional[List[str]] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UserRead(TimestampedModel, UserBase):
    id: uuid.UUID
