"""Database engine configuration for async SQLAlchemy."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from racing_coach_server.config import settings

logger = logging.getLogger(__name__)

# Create async engine with asyncpg
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,  # Use NullPool for development, switch to QueuePool for production
)

# Session factory for creating AsyncSession instances
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to provide AsyncSession to route handlers."""
    async with AsyncSessionFactory() as session:
        yield session


@asynccontextmanager
async def transactional_session(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for transactional operations.

    Automatically commits on success and rolls back on exceptions.

    Args:
        session: The AsyncSession to wrap in a transaction

    Yields:
        AsyncSession: The session with transaction management

    Example:
        async with transactional_session(session) as txn:
            # Do database operations
            await txn.add(model)
            # Automatically commits on success
    """
    try:
        yield session
        await session.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction rolled back due to error: {e}")
        raise
