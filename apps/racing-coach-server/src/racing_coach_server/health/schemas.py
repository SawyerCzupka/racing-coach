"""Pydantic schemas for health check response models."""

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Overall server status (healthy/unhealthy)")
    message: str = Field(..., description="Human-readable status message")
    database_status: str = Field(..., description="Database connection status")
    database_message: str = Field(..., description="Database connection details")
