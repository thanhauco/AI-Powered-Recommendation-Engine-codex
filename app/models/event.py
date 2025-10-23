from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EventLog(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Application-wide structured event log for analytics and auditing."""

    __tablename__ = "event_logs"
    __table_args__ = (
        Index("ix_event_logs_type_created", "event_type", "created_at"),
        Index("ix_event_logs_user_created", "user_id", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ab_test_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("ab_tests.id", ondelete="SET NULL"), nullable=True)
    payload: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_json: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="event_logs", lazy="joined")
    ab_test: Mapped[Optional["ABTest"]] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "event_type", "occurred_at")


class FeatureFlag(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Environment feature flags with metadata."""

    __tablename__ = "feature_flags"
    __table_args__ = (UniqueConstraint("slug", name="uq_feature_flags_slug"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollout_percentage: Mapped[int] = mapped_column(nullable=False, default=0)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rules: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    owner: Mapped[Optional["User"]] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "slug", "is_enabled")


if TYPE_CHECKING:  # pragma: no cover
    from app.models.abtest import ABTest
    from app.models.user import User
