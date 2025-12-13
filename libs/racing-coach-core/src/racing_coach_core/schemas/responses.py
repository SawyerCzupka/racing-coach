"""Response models for the Racing Coach API."""

from datetime import datetime

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


# Fetch response models


class LapSummary(BaseModel):
    """Summary of a lap."""

    lap_id: str
    lap_number: int
    lap_time: float | None
    is_valid: bool
    has_metrics: bool
    created_at: datetime


class SessionSummary(BaseModel):
    """Summary of a session."""

    session_id: str
    track_id: int
    track_name: str
    track_config_name: str | None
    track_type: str
    car_id: int
    car_name: str
    car_class_id: int
    series_id: int
    lap_count: int
    created_at: datetime


class SessionListResponse(BaseModel):
    """Response model for session list endpoint."""

    sessions: list[SessionSummary]
    total: int


class SessionDetailResponse(BaseModel):
    """Response model for session detail endpoint."""

    session_id: str
    track_id: int
    track_name: str
    track_config_name: str | None
    track_type: str
    car_id: int
    car_name: str
    car_class_id: int
    series_id: int
    laps: list[LapSummary]
    created_at: datetime


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

    lap_id: str
    session_id: str
    lap_number: int
    frame_count: int
    frames: list[TelemetryFrameResponse]


class BrakingMetricsResponse(BaseModel):
    """Response model for braking zone metrics."""

    braking_point_distance: float
    braking_point_speed: float
    end_distance: float
    max_brake_pressure: float
    braking_duration: float
    minimum_speed: float
    initial_deceleration: float
    average_deceleration: float
    braking_efficiency: float
    has_trail_braking: bool
    trail_brake_distance: float
    trail_brake_percentage: float


class CornerMetricsResponse(BaseModel):
    """Response model for corner metrics."""

    turn_in_distance: float
    apex_distance: float
    exit_distance: float
    throttle_application_distance: float
    turn_in_speed: float
    apex_speed: float
    exit_speed: float
    throttle_application_speed: float
    max_lateral_g: float
    time_in_corner: float
    corner_distance: float
    max_steering_angle: float
    speed_loss: float
    speed_gain: float


class LapMetricsResponse(BaseModel):
    """Response model for lap metrics endpoint."""

    lap_id: str
    lap_time: float | None
    total_corners: int
    total_braking_zones: int
    average_corner_speed: float
    max_speed: float
    min_speed: float
    braking_zones: list[BrakingMetricsResponse]
    corners: list[CornerMetricsResponse]
