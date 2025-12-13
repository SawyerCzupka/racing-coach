"""FastAPI route handlers for the telemetry feature."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from racing_coach_core.schemas.responses import LapUploadResponse
from racing_coach_core.schemas.telemetry import LapTelemetry, SessionFrame
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.database.engine import get_async_session, transactional_session
from racing_coach_server.dependencies import (
    get_lap_service,
    get_session_service,
    get_telemetry_data_service,
)
from racing_coach_server.telemetry.services import (
    LapService,
    SessionService,
    TelemetryDataService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/lap",
    response_model=LapUploadResponse,
    tags=["telemetry"],
)
async def upload_lap(
    lap: LapTelemetry,
    session: SessionFrame,
    lap_id: UUID | None = None,
    db: AsyncSession = Depends(get_async_session),
    session_service: SessionService = Depends(get_session_service),
    lap_service: LapService = Depends(get_lap_service),
    telemetry_service: TelemetryDataService = Depends(get_telemetry_data_service),
) -> LapUploadResponse:
    """
    Upload a lap with telemetry data.

    Args:
        lap: The lap telemetry data
        session: The session frame with track/car info
        lap_id: Optional client-provided UUID for the lap. If not provided, server generates one.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed
    """

    logger.info(f"Router lap_id: {lap_id}")

    try:
        async with transactional_session(db):
            # Get lap number from first frame
            lap_number = lap.frames[0].lap_number

            # Get or create session
            db_track_session = await session_service.add_or_get_session(session)

            # Add lap to the db (use client-provided lap_id if available)
            db_lap = await lap_service.add_lap(
                track_session_id=db_track_session.id,
                lap_number=lap_number,
                lap_id=lap_id,
            )

            # Add telemetry sequence
            await telemetry_service.add_telemetry_sequence(
                telemetry_sequence=lap, lap_id=db_lap.id, session_id=db_track_session.id
            )

            logger.info(f"Successfully uploaded lap {lap_number} with {len(lap.frames)} frames")

            return LapUploadResponse(
                status="success",
                message=f"Received lap {lap_number} with {len(lap.frames)} frames",
                lap_id=str(db_lap.id),
            )

    except Exception as e:
        logger.error(f"Error uploading lap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e


@router.get("/sessions/latest", tags=["telemetry"])
async def get_latest_session(
    session_service: SessionService = Depends(get_session_service),
) -> SessionFrame:
    """
    Endpoint to retrieve the latest track session.
    """
    try:
        latest_session = await session_service.get_latest_session()

        if not latest_session:
            raise HTTPException(status_code=404, detail="No sessions found.")

        return latest_session.to_session_frame()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e
