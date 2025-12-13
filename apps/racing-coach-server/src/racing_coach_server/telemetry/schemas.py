"""Pydantic schemas for telemetry feature request/response models."""

from pydantic import BaseModel
from racing_coach_core.schemas.responses import LapUploadResponse
from racing_coach_core.schemas.telemetry import LapTelemetry, SessionFrame

# Re-export LapUploadResponse for convenience
__all__ = ["LapUploadRequest", "LapUploadResponse"]


class LapUploadRequest(BaseModel):
    """Request model for uploading a lap with telemetry data."""

    lap: LapTelemetry
    session: SessionFrame
