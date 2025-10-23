from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional

from pydantic import Field

from app.models.interaction import InteractionType
from app.schemas.common import APIModel, TimestampedModel


class InteractionCreate(APIModel):
    user_id: uuid.UUID
    item_id: uuid.UUID
    event_type: InteractionType
    event_at: datetime
    weight: float = Field(default=1.0, ge=0.0)
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    source: str = Field(default="web", max_length=64)
    metadata_json: Dict[str, Optional[str]] = Field(default_factory=dict)


class InteractionRead(TimestampedModel, InteractionCreate):
    id: uuid.UUID
