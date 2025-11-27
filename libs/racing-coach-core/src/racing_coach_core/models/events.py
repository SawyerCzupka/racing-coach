from uuid import UUID

from pydantic import BaseModel

from ..algs.events import LapMetrics
from .telemetry import LapTelemetry, SessionFrame, TelemetryFrame


class TelemetryAndSession(BaseModel):
    TelemetryFrame: TelemetryFrame
    SessionFrame: SessionFrame


class LapAndSession(BaseModel):
    LapTelemetry: LapTelemetry
    SessionFrame: SessionFrame


class MetricsAndSession(BaseModel):
    """Event data for lap metrics extraction."""

    LapMetrics: LapMetrics
    SessionFrame: SessionFrame


class SessionStart(BaseModel):
    """Event data for session start."""

    SessionFrame: SessionFrame


class SessionEnd(BaseModel):
    """Event data for session end."""

    session_id: UUID
