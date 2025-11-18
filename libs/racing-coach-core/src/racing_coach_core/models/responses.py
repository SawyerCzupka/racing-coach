"""Response models for the Racing Coach API."""

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str
    message: str


class LapUploadResponse(BaseModel):
    """Response model for lap telemetry upload."""

    status: str
    message: str
    lap_id: str


class MetricsUploadResponse(BaseModel):
    """Response model for lap metrics upload."""

    status: str
    message: str
    lap_metrics_id: str
