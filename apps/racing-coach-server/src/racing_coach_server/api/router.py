from fastapi import APIRouter, Depends, HTTPException
from racing_coach_core.events import Event, EventBus, EventType
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


@router.post("/telemetry")
def telemetry_data(data: dict):
    """
    Endpoint to receive telemetry data from the client.
    """
    print("Telemetry data received:", data)
    return {"status": "ok", "message": "Telemetry data processed."}


@router.post("/telemetry/lap")
def receive_lap(
    lap: LapTelemetry,
    session: SessionFrame,
    track_session_service: TrackSessionServiceDep,
    telemetry_service: TelemetryServiceDep,
    lap_service: LapServiceDep,
):
    """
    Endpoint to receive lap telemetry data from the client.
    """
    try:
        lap_number = lap.frames[0].lap_number

        # Get/add session to db so we have the session id
        db_track_session = track_session_service.add_or_get_session(session)

        # add lap
        db_lap = lap_service.lap_repository.create(
            session_id=db_track_session.id, lap_number=lap_number
        )
        lap_service.db_session.commit()

        # add telemetry frames
        for frame in lap.frames:
            telemetry_service.telemetry_repository.create_from_telemetry_frame(
                telemetry_frame=frame, lap_id=db_lap.id, session_id=db_track_session.id
            )
        lap_service.db_session.commit()

        return {
            "status": "success",
            "message": f"Received lap {lap_number} with {len(lap.frames)} frames",
            "lap_id": str(db_lap.id),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
