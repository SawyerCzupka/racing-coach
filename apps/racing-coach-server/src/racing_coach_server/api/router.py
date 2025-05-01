from fastapi import APIRouter
from racing_coach_core.events import Event, EventBus, EventType
from racing_coach_core.models.telemetry import (
    LapTelemetry,
    SessionFrame,
    TelemetryFrame,
)

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
