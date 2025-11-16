"""Pydantic schemas for telemetry feature request/response models."""

from uuid import UUID

from pydantic import BaseModel, Field
from racing_coach_core.models.responses import LapUploadResponse
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame

# Re-export LapUploadResponse for convenience
__all__ = ["LapUploadRequest", "LapUploadResponse"]


class LapUploadRequest(BaseModel):
    """Request model for uploading a lap with telemetry data."""

    lap: LapTelemetry
    session: SessionFrame
