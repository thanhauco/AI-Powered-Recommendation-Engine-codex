from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base schema with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, arbitrary_types_allowed=True)


class TimestampedModel(APIModel):
    """Adds created/updated timestamp fields."""

    created_at: datetime
    updated_at: datetime
