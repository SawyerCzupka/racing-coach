"""FastAPI route handlers for the telemetry feature."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from racing_coach_core.models.responses import LapUploadResponse
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.database.engine import transactional_session
from racing_coach_server.dependencies import get_telemetry_service
from racing_coach_server.telemetry.service import TelemetryService

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
    service: TelemetryService = Depends(get_telemetry_service),
) -> LapUploadResponse:
    """
    Upload a lap with telemetry data.

    The transaction is managed by the transactional_session context manager:
    - If any operation fails, the transaction is automatically rolled back
    - If all operations succeed, changes are committed
    """
    try:
        async with transactional_session(service.db) as txn:
            # Get lap number from first frame
            lap_number = lap.frames[0].lap_number

            # Get or create session
            db_track_session = await service.add_or_get_session(session)

            # Add lap to the db to get the lap id
            db_lap = await service.add_lap(
                track_session_id=db_track_session.id, lap_number=lap_number
            )

            # Add telemetry sequence
            await service.add_telemetry_sequence(
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
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/sessions/latest", tags=["telemetry"])
async def get_latest_session(
    service: TelemetryService = Depends(get_telemetry_service),
) -> SessionFrame:
    """
    Endpoint to retrieve the latest track session.
    """
    try:
        latest_session = await service.get_latest_session()

        if not latest_session:
            raise HTTPException(status_code=404, detail="No sessions found.")

        return latest_session.to_session_frame()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
