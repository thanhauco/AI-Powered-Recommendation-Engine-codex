from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class InteractionType(str, Enum):
    """Supported interaction events."""

    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    RATING = "rating"


class Interaction(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Event log capturing user-item interactions."""

    __tablename__ = "interactions"
    __table_args__ = (
        CheckConstraint("weight >= 0", name="ck_interactions_weight_non_negative"),
        Index("ix_interactions_user_item_event", "user_id", "item_id", "event_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[InteractionType] = mapped_column(nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="web")
    metadata_json: Mapped[Dict[str, Optional[str]]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship(back_populates="interactions", lazy="joined")
    item: Mapped["Item"] = relationship(back_populates="interactions", lazy="joined")

    __repr_attrs__ = ("id", "user_id", "item_id", "event_type")


if TYPE_CHECKING:  # pragma: no cover - typing imports only
    from app.models.item import Item
    from app.models.user import User
