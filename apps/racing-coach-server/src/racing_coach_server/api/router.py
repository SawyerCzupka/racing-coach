from fastapi import APIRouter, Depends, HTTPException
from racing_coach_core.events import Event, EventBus, EventType
from racing_coach_core.models.responses import LapUploadResponse
from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)

from ..dependencies import LapServiceDep, TelemetryServiceDep, TrackSessionServiceDep

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint to verify if the server is running.
    Returns a simple message indicating the server status.
    """
    return {"status": "ok", "message": "Racing Coach Server is running."}


@router.post("/telemetry/lap")
def receive_lap(
    lap: LapTelemetry,
    session: SessionFrame,
    track_session_service: TrackSessionServiceDep,
    telemetry_service: TelemetryServiceDep,
    lap_service: LapServiceDep,
) -> LapUploadResponse:
    """
    Endpoint to receive lap telemetry data from the client.
    """
    try:
        lap_number = lap.frames[0].lap_number

        # Get/add session to db so we have the session id
        db_track_session = track_session_service.add_or_get_session(session)

        # Add lap to the db to get the lap id
        db_lap = lap_service.add_lap(track_session_id=db_track_session.id, lap_number=lap_number)

        telemetry_service.add_telemetry_sequence(
            telemetry_sequence=lap, lap_id=db_lap.id, session_id=db_track_session.id
        )

        # return {
        #     "status": "success",
        #     "message": f"Received lap {lap_number} with {len(lap.frames)} frames",
        #     "lap_id": str(db_lap.id),
        # }
        return LapUploadResponse(
            status="success",
            message=f"Received lap {lap_number} with {len(lap.frames)} frames",
            lap_id=str(db_lap.id),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/sessions/latest")
def get_latest_session(track_session_service: TrackSessionServiceDep) -> SessionFrame:
    """
    Endpoint to retrieve the latest track session.
    """
    latest_session = track_session_service.get_latest_session()

    if not latest_session:
        raise HTTPException(status_code=404, detail="No sessions found.")

    return latest_session.to_session_frame()
