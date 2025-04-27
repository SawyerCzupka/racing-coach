"""Database initialization module.

This module handles the creation and initialization of the TimescaleDB database,
including the hypertable setup for time-series data.
"""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

from racing_coach_server.database.models import Base

from .database import create_db_engine

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
                text(
                    "SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);"
                )
            )
            logger.info("Telemetry table converted to TimescaleDB hypertable.")

    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise


def setup_database(connection_string: str):
    """
    Set up the database by creating the engine and initializing it.

    Args:
        connection_string (str): The database connection string.
    """
    engine = create_db_engine(connection_string)
    init_db(engine)


if __name__ == "__main__":
    # Example usage
    connection_string = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/racing_coach"
    )
    setup_database(connection_string)
