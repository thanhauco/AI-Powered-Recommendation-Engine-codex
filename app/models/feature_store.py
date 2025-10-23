from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UserEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Pre-computed user embedding vectors."""

    __tablename__ = "feature_store_user_embeddings"
    __table_args__ = (
        Index("ix_feature_store_user_embeddings_user_model", "user_id", "model_version", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "user_id", "model_version")


class ItemEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Pre-computed item embedding vectors."""

    __tablename__ = "feature_store_item_embeddings"
    __table_args__ = (
        Index("ix_feature_store_item_embeddings_item_model", "item_id", "model_version", unique=True),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    item: Mapped["Item"] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "item_id", "model_version")


class RecommendationScore(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Materialized recommendation scores per user-item pair."""

    __tablename__ = "feature_store_recommendation_scores"
    __table_args__ = (
        Index(
            "ix_feature_store_recommendation_scores_user_item_version",
            "user_id",
            "item_id",
            "model_version",
            unique=True,
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)
    explanation: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(lazy="joined")
    item: Mapped["Item"] = relationship(lazy="joined")

    __repr_attrs__ = ("id", "user_id", "item_id", "model_version")


if TYPE_CHECKING:  # pragma: no cover - typing imports only
    from app.models.item import Item
    from app.models.user import User
