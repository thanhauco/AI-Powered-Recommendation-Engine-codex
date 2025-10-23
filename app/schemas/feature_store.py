from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List

from app.schemas.common import TimestampedModel


class UserEmbeddingRead(TimestampedModel):
    id: uuid.UUID
    user_id: uuid.UUID
    model_version: str
    embedding: List[float]
    embedding_dim: int
    metadata_json: Dict[str, str]
    computed_at: datetime


class ItemEmbeddingRead(TimestampedModel):
    id: uuid.UUID
    item_id: uuid.UUID
    model_version: str
    embedding: List[float]
    embedding_dim: int
    metadata_json: Dict[str, str]
    computed_at: datetime


class RecommendationScoreRead(TimestampedModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_id: uuid.UUID
    model_version: str
    score: float
    rank: int
    explanation: Dict[str, float]
    computed_at: datetime
