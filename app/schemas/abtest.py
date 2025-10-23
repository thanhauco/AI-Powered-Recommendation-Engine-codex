from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from app.models.abtest import ABTestStatus, ABTestVariant
from app.schemas.common import APIModel, TimestampedModel


class ABTestBase(APIModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)
    status: ABTestStatus = ABTestStatus.DRAFT
    hypothesis: Optional[str] = Field(default=None, max_length=1024)
    primary_metric: str = Field(default="ctr", max_length=128)
    secondary_metrics: List[str] = Field(default_factory=list)
    variant_a_config: Dict[str, str] = Field(default_factory=dict)
    variant_b_config: Dict[str, str] = Field(default_factory=dict)
    traffic_percentage: int = Field(default=50, ge=1, le=100)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ABTestCreate(ABTestBase):
    created_by_id: uuid.UUID


class ABTestUpdate(APIModel):
    description: Optional[str] = Field(default=None, max_length=1024)
    status: Optional[ABTestStatus] = None
    hypothesis: Optional[str] = None
    primary_metric: Optional[str] = None
    secondary_metrics: Optional[List[str]] = None
    variant_a_config: Optional[Dict[str, str]] = None
    variant_b_config: Optional[Dict[str, str]] = None
    traffic_percentage: Optional[int] = Field(default=None, ge=1, le=100)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ABTestRead(TimestampedModel, ABTestBase):
    id: uuid.UUID
    created_by_id: uuid.UUID


class ABTestAssignmentRead(TimestampedModel):
    id: uuid.UUID
    ab_test_id: uuid.UUID
    user_id: uuid.UUID
    variant: ABTestVariant
    assigned_at: datetime
    metadata_json: Dict[str, str]
