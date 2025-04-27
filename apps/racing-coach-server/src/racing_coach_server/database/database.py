from sqlalchemy import create_engine
from racing_coach_server.config import Settings
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

settings = Settings()


def create_db_engine(connection_string: str):
    """
    Create a SQLAlchemy engine for the TimescaleDB database.

    Args:
        connection_string (str): The database connection string.

    Returns:
        sqlalchemy.engine.Engine: The SQLAlchemy engine.
    """
    try:
        engine = create_engine(connection_string, echo=True)
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Error creating database engine: {e}")
        raise
