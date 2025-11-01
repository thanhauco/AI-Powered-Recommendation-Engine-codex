from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable, Sequence

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Item, RecommendationScore, UserEmbedding


@dataclass(slots=True)
class RecommendationCandidate:
    item: Item
    score: float
    rank: int | None = None
    explanation: dict[str, float] | None = None


class FeatureStoreService:
    """Read/write helpers for recommendation artifacts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_user_embeddings(self, user_ids: Sequence[uuid.UUID], *, model_version: str | None = None) -> dict[uuid.UUID, UserEmbedding]:
        stmt: Select = select(UserEmbedding).where(UserEmbedding.user_id.in_(user_ids))
        if model_version:
            stmt = stmt.where(UserEmbedding.model_version == model_version)
        stmt = stmt.order_by(UserEmbedding.computed_at.desc())
        records = (await self.session.scalars(stmt)).all()
        embeddings: dict[uuid.UUID, UserEmbedding] = {}
        for record in records:
            if record.user_id not in embeddings:
                embeddings[record.user_id] = record
        return embeddings

    async def fetch_recommendation_scores(
        self,
        user_id: uuid.UUID,
        *,
        model_version: str | None = None,
        limit: int = 20,
    ) -> list[RecommendationCandidate]:
        stmt = (
            select(RecommendationScore, Item)
            .join(Item, RecommendationScore.item_id == Item.id)
            .where(RecommendationScore.user_id == user_id)
            .order_by(RecommendationScore.score.desc())
            .limit(limit)
        )
        if model_version:
            stmt = stmt.where(RecommendationScore.model_version == model_version)
        results = await self.session.execute(stmt)
        candidates: list[RecommendationCandidate] = []
        for score, item in results.all():
            candidates.append(
                RecommendationCandidate(
                    item=item,
                    score=score.score,
                    rank=score.rank,
                    explanation=score.explanation,
                )
            )
        return candidates

    async def upsert_recommendation_scores(
        self,
        user_id: uuid.UUID,
        candidates: Sequence[RecommendationCandidate],
        *,
        model_version: str,
    ) -> None:
        await self.session.execute(
            delete(RecommendationScore).where(
                RecommendationScore.user_id == user_id,
                RecommendationScore.model_version == model_version,
            )
        )
        now = datetime.now(tz=UTC)
        for rank, candidate in enumerate(candidates, start=1):
            self.session.add(
                RecommendationScore(
                    user_id=user_id,
                    item_id=candidate.item.id,
                    model_version=model_version,
                    score=float(candidate.score),
                    rank=rank,
                    explanation=candidate.explanation or {},
                    computed_at=now,
                )
            )
        await self.session.flush()

    async def aggregate_interaction_counts(self, user_id: uuid.UUID) -> dict[uuid.UUID, float]:
        from app.models import Interaction

        stmt = (
            select(Interaction.item_id, func.sum(Interaction.weight))
            .where(Interaction.user_id == user_id)
            .group_by(Interaction.item_id)
        )
        rows = await self.session.execute(stmt)
        return {item_id: float(weight or 0.0) for item_id, weight in rows.all()}

    async def fetch_items(self, item_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, Item]:
        if not item_ids:
            return {}
        stmt = select(Item).where(Item.id.in_(item_ids))
        records = (await self.session.scalars(stmt)).all()
        return {item.id: item for item in records}
