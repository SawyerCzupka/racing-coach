"""Pydantic schemas for sessions API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LapSummary(BaseModel):
    """Summary of a lap for listing purposes."""

    lap_id: str = Field(description="UUID of the lap")
    lap_number: int = Field(description="Lap number in the session")
    lap_time: float | None = Field(description="Lap time in seconds")
    is_valid: bool = Field(description="Whether the lap is valid")
    has_metrics: bool = Field(description="Whether metrics have been computed for this lap")
    created_at: datetime = Field(description="When the lap was recorded")


class SessionSummary(BaseModel):
    """Summary of a session for listing purposes."""

    session_id: str = Field(description="UUID of the session")
    track_id: int = Field(description="Track ID")
    track_name: str = Field(description="Name of the track")
    track_config_name: str | None = Field(description="Track configuration name")
    track_type: str = Field(description="Type of track")
    car_id: int = Field(description="Car ID")
    car_name: str = Field(description="Name of the car")
    car_class_id: int = Field(description="Car class ID")
    series_id: int = Field(description="Series ID")
    lap_count: int = Field(description="Number of laps in the session")
    created_at: datetime = Field(description="When the session was created")


class SessionListResponse(BaseModel):
    """Response model for session list endpoint."""

    sessions: list[SessionSummary] = Field(description="List of sessions")
    total: int = Field(description="Total number of sessions")


class SessionDetailResponse(BaseModel):
    """Response model for session detail endpoint."""

    session_id: str = Field(description="UUID of the session")
    track_id: int = Field(description="Track ID")
    track_name: str = Field(description="Name of the track")
    track_config_name: str | None = Field(description="Track configuration name")
    track_type: str = Field(description="Type of track")
    car_id: int = Field(description="Car ID")
    car_name: str = Field(description="Name of the car")
    car_class_id: int = Field(description="Car class ID")
    series_id: int = Field(description="Series ID")
    laps: list[LapSummary] = Field(description="List of laps in the session")
    created_at: datetime = Field(description="When the session was created")


class LapDetailResponse(BaseModel):
    """Response model for lap detail endpoint."""

    lap_id: str = Field(description="UUID of the lap")
    session_id: str = Field(description="UUID of the session")
    lap_number: int = Field(description="Lap number in the session")
    lap_time: float | None = Field(description="Lap time in seconds")
    is_valid: bool = Field(description="Whether the lap is valid")
    track_name: str = Field(description="Name of the track")
    track_config_name: str | None = Field(description="Track configuration name")
    car_name: str = Field(description="Name of the car")
    has_metrics: bool = Field(description="Whether metrics have been computed")
    created_at: datetime = Field(description="When the lap was recorded")


class TelemetryFrameResponse(BaseModel):
    """Response model for a single telemetry frame."""

    timestamp: datetime
    session_time: float
    lap_number: int
    lap_distance_pct: float
    lap_distance: float
    current_lap_time: float

    # Vehicle state
    speed: float
    rpm: float
    gear: int

    # Driver inputs
    throttle: float
    brake: float
    clutch: float
    steering_angle: float

    # Vehicle dynamics
    lateral_acceleration: float
    longitudinal_acceleration: float
    vertical_acceleration: float
    yaw_rate: float
    roll_rate: float
    pitch_rate: float

    # Vehicle velocity
    velocity_x: float
    velocity_y: float
    velocity_z: float

    # Vehicle orientation
    yaw: float
    pitch: float
    roll: float

    # GPS position
    latitude: float
    longitude: float
    altitude: float

    # Track conditions (optional)
    track_temp: float | None = None
    air_temp: float | None = None


class LapTelemetryResponse(BaseModel):
    """Response model for lap telemetry endpoint."""

    lap_id: str = Field(description="UUID of the lap")
    session_id: str = Field(description="UUID of the session")
    lap_number: int = Field(description="Lap number")
    frame_count: int = Field(description="Number of telemetry frames")
    frames: list[TelemetryFrameResponse] = Field(description="Telemetry frames")
