"""Database initialization module.

This module handles the creation and initialization of the TimescaleDB database,
including the hypertable setup for time-series data.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from racing_coach_server.database.models import Base

logger = logging.getLogger(__name__)


def init_db(engine):
    """
    Initialize the database by creating tables and setting up hypertables.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine.
    """
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")

        # Create hypertables for time-series data
        with engine.connect() as conn:
            conn.execute(
                text("SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);")
            )
            logger.info("Telemetry table converted to TimescaleDB hypertable.")

    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise


if __name__ == "__main__":
    from racing_coach_server.database.database import (
        engine,
    )  # uses connection string from settings

    init_db(engine)
