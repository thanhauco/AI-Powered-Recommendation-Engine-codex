from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import Boolean, Date, Float, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ReprMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Item(UUIDPrimaryKeyMixin, TimestampMixin, ReprMixin, Base):
    """Catalog item enriched with metadata for recommendations."""

    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
        Index("ix_items_description_trgm", "description", postgresql_using="gin", postgresql_ops={"description": "gin_trgm_ops"}),
    )

    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    categories: Mapped[List[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    brand: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    inventory_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[Dict[str, Optional[str]]] = mapped_column(JSONB, nullable=False, default=dict)
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rating_average: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    interactions: Mapped[List["Interaction"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    item_embeddings: Mapped[List["ItemEmbedding"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recommendation_scores: Mapped[List["RecommendationScore"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __repr_attrs__ = ("id", "sku", "title")


if TYPE_CHECKING:  # pragma: no cover - typing imports only
    from app.models.feature_store import ItemEmbedding, RecommendationScore
    from app.models.interaction import Interaction
