from pydantic import BaseModel
from .telemetry import TelemetrySequence, SessionFrame, TelemetryFrame, LapTelemetry


class TelemetryAndSession(BaseModel):
    TelemetryFrame: TelemetryFrame
    SessionFrame: SessionFrame


class LapAndSession(BaseModel):
    LapTelemetry: LapTelemetry
    SessionFrame: SessionFrame


# test = LapAndSession()
