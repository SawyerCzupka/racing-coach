from dataclasses import dataclass


@dataclass
class BrakingEvent:
    start_distance: float
    start_frame: int
    entry_speed: float
    max_pressure: float
    end_frame: int = -1
    braking_duration: float = -1
    minimum_speed: float = -1


@dataclass
class CornerEvent:
    entry_distance: float
    apex_distance: float
    exit_distance: float


@dataclass
class CornerSegmentInput:
    """Corner segment definition for segment-based extraction.

    Used to define corner boundaries from saved track segments rather than
    auto-detecting from telemetry.
    """

    corner_number: int  # 1-indexed corner number
    start_distance: float  # Start distance in meters from S/F line
    end_distance: float  # End distance in meters from S/F line


@dataclass
class TrailBrakingInfo:
    """Trail braking detection results."""

    has_trail_braking: bool
    distance: float  # Track distance of trail braking overlap
    percentage: float  # Average brake pressure during turn-in


@dataclass
class BrakingMetrics:
    """Comprehensive braking metrics for a braking zone."""

    # Location and timing
    braking_point_distance: float  # Lap distance where braking starts
    braking_point_speed: float  # Speed when braking starts
    end_distance: float  # Lap distance where braking ends

    # Performance metrics
    max_brake_pressure: float  # Maximum brake pressure applied (0-1)
    braking_duration: float  # Duration of braking in seconds
    minimum_speed: float  # Minimum speed reached during braking

    # Advanced metrics
    initial_deceleration: float  # Initial deceleration rate (m/s²)
    average_deceleration: float  # Average deceleration during braking
    braking_efficiency: float  # Ratio of deceleration to brake pressure

    # Trail braking
    has_trail_braking: bool  # Whether trail braking was used
    trail_brake_distance: float  # Distance of trail braking overlap with steering
    trail_brake_percentage: float  # Percentage of brake application during turn-in


@dataclass
class CornerMetrics:
    """Comprehensive corner metrics."""

    # Key corner points (distances)
    turn_in_distance: float  # Where steering input begins
    apex_distance: float  # Point of maximum lateral G
    exit_distance: float  # Where steering unwinds
    throttle_application_distance: float  # Where throttle is reapplied

    # Speeds at key points
    turn_in_speed: float
    apex_speed: float  # Minimum corner speed
    exit_speed: float
    throttle_application_speed: float

    # Performance metrics
    max_lateral_g: float  # Maximum lateral acceleration
    time_in_corner: float  # Duration from turn-in to exit (seconds)
    corner_distance: float  # Track distance from turn-in to exit

    # Steering metrics
    max_steering_angle: float  # Maximum steering angle used

    # Speed delta
    speed_loss: float  # Speed lost from turn-in to apex
    speed_gain: float  # Speed gained from apex to exit


@dataclass
class LapMetrics:
    """Combined metrics for an entire lap."""

    lap_number: int
    lap_time: float | None

    # Collections of all events in the lap
    braking_zones: list[BrakingMetrics]
    corners: list[CornerMetrics]

    # Lap-wide statistics
    total_corners: int
    total_braking_zones: int
    average_corner_speed: float
    max_speed: float
    min_speed: float
