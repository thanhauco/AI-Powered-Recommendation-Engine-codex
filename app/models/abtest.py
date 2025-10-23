from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ABTestStatus(str, Enum):
    """Lifecycle states for an experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ABTestVariant(str, Enum):
    """Variant identifiers used for assignments."""

    CONTROL = "control"
    TREATMENT = "treatment"
    HOLDOUT = "holdout"


class ABTest(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Experiment configuration and metadata."""

    __tablename__ = "ab_tests"
    __table_args__ = (UniqueConstraint("slug", name="uq_ab_tests_slug"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[ABTestStatus] = mapped_column(default=ABTestStatus.DRAFT, nullable=False)
    hypothesis: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    primary_metric: Mapped[str] = mapped_column(String(128), nullable=False, default="ctr")
    secondary_metrics: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    variant_a_config: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    variant_b_config: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    traffic_percentage: Mapped[int] = mapped_column(nullable=False, default=50)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    assignments: Mapped[List["ABTestAssignment"]] = relationship(
        back_populates="ab_test",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    creator: Mapped["User"] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "slug", "status")


class ABTestAssignment(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Sticky user assignments to AB test variants."""

    __tablename__ = "ab_test_assignments"
    __table_args__ = (
        UniqueConstraint("ab_test_id", "user_id", name="uq_ab_test_assignments_test_user"),
        Index("ix_ab_test_assignments_user_variant", "user_id", "variant"),
    )

    ab_test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    variant: Mapped[ABTestVariant] = mapped_column(nullable=False, default=ABTestVariant.CONTROL)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[Dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)

    ab_test: Mapped["ABTest"] = relationship(back_populates="assignments", lazy="joined")
    user: Mapped["User"] = relationship(back_populates="assignments", lazy="joined")

    __repr_attrs__ = ("id", "ab_test_id", "user_id", "variant")


if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User
