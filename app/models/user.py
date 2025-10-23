from __future__ import annotations

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, Enum):
    """Role-based access tiers."""

    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"


class User(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Application user model."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferences: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    feature_flags: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    last_login_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    interactions: Mapped[List["Interaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assignments: Mapped[List["ABTestAssignment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    event_logs: Mapped[List["EventLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __repr_attrs__ = ("id", "email", "role")


if TYPE_CHECKING:  # pragma: no cover - imported only for typing
    from app.models.abtest import ABTestAssignment
    from app.models.event import EventLog
    from app.models.interaction import Interaction
