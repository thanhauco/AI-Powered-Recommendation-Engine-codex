from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    str(settings.database_url),
    echo=False,
    pool_pre_ping=True,
    future=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session for request-scoped dependencies."""

    async with async_session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose of the global SQLAlchemy engine."""

    await engine.dispose()
