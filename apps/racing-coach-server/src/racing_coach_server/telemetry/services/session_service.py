"""Service for session management."""

import logging
from uuid import UUID

from racing_coach_core.schemas.telemetry import SessionFrame
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from racing_coach_server.telemetry.models import TrackSession

logger = logging.getLogger(__name__)


class SessionService:
    """Service for track session operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_get_session(self, session_frame: SessionFrame) -> TrackSession:
        """
        Idempotent session creation - returns existing session if found,
        creates new one otherwise.

        Args:
            session_frame: The session information from the client

        Returns:
            TrackSession: The existing or newly created session
        """
        stmt = select(TrackSession).where(TrackSession.id == session_frame.session_id)
        result = await self.db.execute(stmt)
        existing_session = result.scalar_one_or_none()

        if existing_session:
            logger.debug(f"Found existing session with ID {session_frame.session_id}")
            return existing_session

        new_session = TrackSession(
            id=session_frame.session_id,
            track_id=session_frame.track_id,
            track_name=session_frame.track_name,
            track_config_name=session_frame.track_config_name,
            track_type=session_frame.track_type,
            car_id=session_frame.car_id,
            car_name=session_frame.car_name,
            car_class_id=session_frame.car_class_id,
            series_id=session_frame.series_id,
            session_type=session_frame.session_type,
        )
        self.db.add(new_session)
        await self.db.flush()
        logger.info(f"Created new session with ID {new_session.id}")
        return new_session

    async def get_latest_session(self) -> TrackSession | None:
        """
        Get the most recent track session.

        Returns:
            TrackSession | None: The latest session or None if no sessions exist
        """
        stmt = select(TrackSession).order_by(desc(TrackSession.created_at)).limit(1)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"Found latest session with ID {session.id}")
        else:
            logger.debug("No sessions found in database")

        return session

    async def get_all_sessions(self) -> list[TrackSession]:
        """
        Get all track sessions ordered by created_at descending.

        Returns:
            list[TrackSession]: All sessions with their lap counts
        """
        stmt = (
            select(TrackSession)
            .options(selectinload(TrackSession.laps))
            .order_by(desc(TrackSession.created_at))
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        logger.debug(f"Found {len(sessions)} sessions")
        return list(sessions)

    async def get_session_by_id(self, session_id: UUID) -> TrackSession | None:
        """
        Get a specific session by ID with its laps.

        Args:
            session_id: The ID of the session

        Returns:
            TrackSession | None: The session or None if not found
        """
        stmt = (
            select(TrackSession)
            .where(TrackSession.id == session_id)
            .options(selectinload(TrackSession.laps))
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"Found session with ID {session_id}")
        else:
            logger.debug(f"No session found with ID {session_id}")

        return session
