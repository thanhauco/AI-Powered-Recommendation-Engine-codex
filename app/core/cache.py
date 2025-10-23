from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Return a cached Redis client instance."""

    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Gracefully close the Redis client if it was created."""

    global _redis_client
    if _redis_client is None:
        return
    await _redis_client.close()
    await _redis_client.connection_pool.disconnect()
    _redis_client = None
