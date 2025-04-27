from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging

from racing_coach_server.config import settings

logger = logging.getLogger(__name__)

try:
    engine = create_engine(settings.DB_CONNECTION_STR, echo=True)

except SQLAlchemyError as e:
    logger.error(f"Error creating database engine: {e}")
    raise

Base = declarative_base()

SessionFactory = sessionmaker(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    db_session = SessionFactory()
    try:
        yield db_session
    finally:
        db_session.close()
