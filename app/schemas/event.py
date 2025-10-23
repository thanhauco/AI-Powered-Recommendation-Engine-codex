from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional

from pydantic import Field

from app.schemas.common import APIModel, TimestampedModel


class EventLogCreate(APIModel):
    event_type: str = Field(max_length=128)
    user_id: Optional[uuid.UUID] = None
    ab_test_id: Optional[uuid.UUID] = None
    payload: Dict[str, str] = Field(default_factory=dict)
    metadata_json: Dict[str, str] = Field(default_factory=dict)
    occurred_at: datetime


class EventLogRead(TimestampedModel, EventLogCreate):
    id: uuid.UUID


class FeatureFlagBase(APIModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)
    is_enabled: bool = False
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    owner_id: Optional[uuid.UUID] = None
    rules: Dict[str, str] = Field(default_factory=dict)


class FeatureFlagCreate(FeatureFlagBase):
    ...


class FeatureFlagUpdate(APIModel):
    description: Optional[str] = Field(default=None, max_length=1024)
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    owner_id: Optional[uuid.UUID] = None
    rules: Optional[Dict[str, str]] = None


class FeatureFlagRead(TimestampedModel, FeatureFlagBase):
    id: uuid.UUID
