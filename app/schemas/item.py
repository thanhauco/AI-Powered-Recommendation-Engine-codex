from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import Field

from app.schemas.common import APIModel, TimestampedModel


class ItemBase(APIModel):
    sku: str = Field(min_length=3, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    description: str
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    color: Optional[str] = None
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    inventory_count: int = Field(default=0, ge=0)
    is_active: bool = True
    metadata_json: Dict[str, Optional[str]] = Field(default_factory=dict)
    release_date: Optional[date] = None
    rating_average: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class ItemCreate(ItemBase):
    ...


class ItemUpdate(APIModel):
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    inventory_count: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    metadata_json: Optional[Dict[str, Optional[str]]] = None
    release_date: Optional[date] = None
    rating_average: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class ItemRead(TimestampedModel, ItemBase):
    id: uuid.UUID


class ItemSearchFilters(APIModel):
    query: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    min_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    max_price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    sort: Optional[str] = Field(default="relevance")
