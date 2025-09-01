from pydantic import BaseModel

from .telemetry import LapTelemetry, SessionFrame, TelemetryFrame


class TelemetryAndSession(BaseModel):
    TelemetryFrame: TelemetryFrame
    SessionFrame: SessionFrame


class LapAndSession(BaseModel):
    LapTelemetry: LapTelemetry
    SessionFrame: SessionFrame


# test = LapAndSession()
