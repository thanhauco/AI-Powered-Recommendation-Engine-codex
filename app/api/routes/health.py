from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis_client
from app.core.database import get_db_session

router = APIRouter()


@router.get("/live", summary="Liveness probe", status_code=status.HTTP_200_OK)
async def live() -> dict[str, str]:
    """Return an affirmative liveness response."""

    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe", status_code=status.HTTP_200_OK)
async def ready(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    """
    Validate downstream dependencies to declare service readiness.
    """

    await db.execute(text("SELECT 1"))
    await redis.ping()
    return {"status": "ready"}
