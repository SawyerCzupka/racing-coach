from uuid import UUID

from pydantic import BaseModel

from ..algs.events import LapMetrics
from .telemetry import LapTelemetry, SessionFrame, TelemetryFrame


class TelemetryAndSession(BaseModel):
    TelemetryFrame: TelemetryFrame
    SessionFrame: SessionFrame


class TelemetryAndSessionId(BaseModel):
    telemetry: TelemetryFrame
    session_id: UUID


class LapAndSession(BaseModel):
    LapTelemetry: LapTelemetry
    SessionFrame: SessionFrame
    lap_id: UUID  # Client-generated UUID for this lap


class MetricsAndSession(BaseModel):
    """Event data for lap metrics extraction."""

    LapMetrics: LapMetrics
    SessionFrame: SessionFrame
    lap_id: UUID  # Passed through from LapAndSession


class SessionStart(BaseModel):
    """Event data for session start."""

    SessionFrame: SessionFrame


class SessionEnd(BaseModel):
    """Event data for session end."""

    session_id: UUID
