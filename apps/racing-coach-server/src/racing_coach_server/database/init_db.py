"""Database initialization module.

This module handles the creation and initialization of the TimescaleDB database,
including the hypertable setup for time-series data.
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from racing_coach_server.database.base import Base
from racing_coach_server.telemetry.models import Lap, Telemetry, TrackSession  # noqa: F401

logger = logging.getLogger(__name__)


async def init_db(engine):
    """
    Initialize the database by creating tables and setting up hypertables.

    Args:
        engine: The async SQLAlchemy engine
    """
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully.")

            # Create hypertables for time-series data
            await conn.execute(
                text(
                    "SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);"
                )
            )
            logger.info("Telemetry table converted to TimescaleDB hypertable.")

    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def main():
    """Main entry point for database initialization."""
    from racing_coach_server.database.engine import engine

    await init_db(engine)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
