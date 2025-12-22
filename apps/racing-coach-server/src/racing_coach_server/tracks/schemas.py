"""Pydantic schemas for track boundary API."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrackBoundarySummary(BaseModel):
    """Summary of a track boundary for listing purposes."""

    id: str = Field(description="UUID of the track boundary")
    track_id: int = Field(description="iRacing track ID")
    track_name: str = Field(description="Name of the track")
    track_config_name: str | None = Field(description="Track configuration name")
    grid_size: int = Field(description="Number of grid points in boundary data")
    created_at: datetime = Field(description="When the boundary was created")


class TrackBoundaryListResponse(BaseModel):
    """Response model for track boundary list endpoint."""

    boundaries: list[TrackBoundarySummary] = Field(description="List of track boundaries")
    total: int = Field(description="Total number of track boundaries")


class TrackBoundaryResponse(BaseModel):
    """Response model for track boundary detail endpoint."""

    id: str = Field(description="UUID of the track boundary")
    track_id: int = Field(description="iRacing track ID")
    track_name: str = Field(description="Name of the track")
    track_config_name: str | None = Field(description="Track configuration name")

    # Boundary data arrays
    grid_distance_pct: list[float] = Field(
        description="Normalized lap distance grid points (0.0 to 1.0)"
    )
    left_latitude: list[float] = Field(description="Left boundary latitudes")
    left_longitude: list[float] = Field(description="Left boundary longitudes")
    right_latitude: list[float] = Field(description="Right boundary latitudes")
    right_longitude: list[float] = Field(description="Right boundary longitudes")

    # Metadata
    grid_size: int = Field(description="Number of grid points")
    source_left_frames: int = Field(description="Original frame count for left boundary")
    source_right_frames: int = Field(description="Original frame count for right boundary")

    created_at: datetime = Field(description="When the boundary was created")
    updated_at: datetime = Field(description="When the boundary was last updated")


class TrackBoundaryUploadResponse(BaseModel):
    """Response model for track boundary upload endpoint."""

    status: str = Field(default="success", description="Upload status")
    message: str = Field(description="Human-readable status message")
    boundary_id: str = Field(description="UUID of the created/updated boundary")
    track_name: str = Field(description="Name of the track from IBT file")
    track_config_name: str | None = Field(description="Track configuration name")
    replaced_existing: bool = Field(
        default=False, description="Whether an existing boundary was replaced"
    )
