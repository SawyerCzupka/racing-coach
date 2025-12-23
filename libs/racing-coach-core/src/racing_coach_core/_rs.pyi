"""Type stubs for the Rust extension module."""

from typing import Optional

# ============================================================================
# Input Types
# ============================================================================

class TelemetryFrame:
    """A single telemetry frame containing all data needed for analysis."""

    brake: float
    """Brake pressure (0.0-1.0)"""

    throttle: float
    """Throttle position (0.0-1.0)"""

    speed: float
    """Vehicle speed in m/s"""

    lap_distance: float
    """Normalized lap distance (0.0-1.0)"""

    steering_angle: float
    """Steering angle in radians"""

    lateral_acceleration: float
    """Lateral acceleration in m/s²"""

    longitudinal_acceleration: float
    """Longitudinal acceleration in m/s²"""

    timestamp: float
    """Timestamp in seconds"""

    def __init__(
        self,
        brake: float,
        throttle: float,
        speed: float,
        lap_distance: float,
        steering_angle: float,
        lateral_acceleration: float,
        longitudinal_acceleration: float,
        timestamp: float,
    ) -> None: ...

class AnalysisConfig:
    """Configuration for telemetry analysis thresholds."""

    brake_threshold: float
    """Minimum brake pressure to consider as braking (default: 0.05)"""

    steering_threshold: float
    """Minimum steering angle to consider as turning (default: 0.15 radians)"""

    throttle_threshold: float
    """Minimum throttle position to consider as accelerating (default: 0.05)"""

    decel_window: int
    """Number of frames for initial deceleration calculation (default: 5)"""

    def __init__(
        self,
        brake_threshold: float = 0.05,
        steering_threshold: float = 0.15,
        throttle_threshold: float = 0.05,
        decel_window: int = 5,
    ) -> None: ...
    @staticmethod
    def defaults() -> AnalysisConfig:
        """Create a config with default values."""
        ...

# ============================================================================
# Result Types
# ============================================================================

class BrakingMetrics:
    """Comprehensive braking metrics for a single braking zone."""

    # Location metrics
    braking_point_distance: float
    """Lap distance where braking starts (normalized 0-1)"""

    braking_point_speed: float
    """Speed when braking starts (m/s)"""

    end_distance: float
    """Lap distance where braking ends (normalized 0-1)"""

    # Performance metrics
    max_brake_pressure: float
    """Maximum brake pressure applied (0-1)"""

    braking_duration: float
    """Duration of braking in seconds"""

    minimum_speed: float
    """Minimum speed reached during braking (m/s)"""

    # Deceleration metrics
    initial_deceleration: float
    """Initial deceleration rate over first N frames (m/s²)"""

    average_deceleration: float
    """Average deceleration during entire braking zone (m/s²)"""

    braking_efficiency: float
    """Braking efficiency: |deceleration| / brake_pressure"""

    # Trail braking metrics
    has_trail_braking: bool
    """Whether trail braking was detected"""

    trail_brake_distance: float
    """Track distance of trail braking overlap"""

    trail_brake_percentage: float
    """Average brake pressure during trail braking phase"""

    def __init__(
        self,
        braking_point_distance: float,
        braking_point_speed: float,
        end_distance: float,
        max_brake_pressure: float,
        braking_duration: float,
        minimum_speed: float,
        initial_deceleration: float,
        average_deceleration: float,
        braking_efficiency: float,
        has_trail_braking: bool,
        trail_brake_distance: float,
        trail_brake_percentage: float,
    ) -> None: ...

class CornerMetrics:
    """Comprehensive corner metrics for a single corner."""

    # Key corner points
    turn_in_distance: float
    """Lap distance where steering input begins"""

    apex_distance: float
    """Lap distance at corner apex (point of max lateral G)"""

    exit_distance: float
    """Lap distance where steering unwinds"""

    throttle_application_distance: float
    """Lap distance where throttle is first applied in corner"""

    # Speeds at key points
    turn_in_speed: float
    """Speed at turn-in point (m/s)"""

    apex_speed: float
    """Speed at apex (typically minimum corner speed) (m/s)"""

    exit_speed: float
    """Speed at exit point (m/s)"""

    throttle_application_speed: float
    """Speed when throttle is first applied (m/s)"""

    # Performance metrics
    max_lateral_g: float
    """Maximum lateral acceleration (m/s²)"""

    time_in_corner: float
    """Time spent in corner (seconds)"""

    corner_distance: float
    """Track distance from turn-in to exit"""

    max_steering_angle: float
    """Maximum steering angle used (radians)"""

    # Speed deltas
    speed_loss: float
    """Speed lost from turn-in to apex"""

    speed_gain: float
    """Speed gained from apex to exit"""

    def __init__(
        self,
        turn_in_distance: float,
        apex_distance: float,
        exit_distance: float,
        throttle_application_distance: float,
        turn_in_speed: float,
        apex_speed: float,
        exit_speed: float,
        throttle_application_speed: float,
        max_lateral_g: float,
        time_in_corner: float,
        corner_distance: float,
        max_steering_angle: float,
        speed_loss: float,
        speed_gain: float,
    ) -> None: ...

class LapMetrics:
    """Aggregate metrics for an entire lap."""

    lap_number: int
    """Lap number"""

    lap_time: float | None
    """Lap time in seconds (None if not available)"""

    braking_zones: list[BrakingMetrics]
    """All braking zones detected in the lap"""

    corners: list[CornerMetrics]
    """All corners detected in the lap"""

    total_corners: int
    """Total number of corners"""

    total_braking_zones: int
    """Total number of braking zones"""

    average_corner_speed: float
    """Average speed at corner apexes (m/s)"""

    max_speed: float
    """Maximum speed during the lap (m/s)"""

    min_speed: float
    """Minimum speed during the lap (m/s)"""

    def __init__(
        self,
        lap_number: int,
        lap_time: float | None,
        braking_zones: list[BrakingMetrics],
        corners: list[CornerMetrics],
        total_corners: int,
        total_braking_zones: int,
        average_corner_speed: float,
        max_speed: float,
        min_speed: float,
    ) -> None: ...

# ============================================================================
# Functions
# ============================================================================

def py_extract_lap_metrics(
    frames: list[TelemetryFrame],
    lap_number: int = 0,
    lap_time: float | None = None,
    config: AnalysisConfig | None = None,
) -> LapMetrics:
    """Extract comprehensive lap metrics from telemetry frames.

    This is the main entry point for lap analysis. It performs a single-pass
    analysis detecting all braking zones and corners.

    Args:
        frames: List of TelemetryFrame objects
        lap_number: The lap number (default: 0)
        lap_time: Optional lap time in seconds
        config: Optional AnalysisConfig (uses defaults if not provided)

    Returns:
        LapMetrics containing all detected events and statistics
    """
    ...

def py_extract_braking_zones(
    frames: list[TelemetryFrame],
    config: AnalysisConfig | None = None,
) -> list[BrakingMetrics]:
    """Extract braking zones from telemetry frames.

    Args:
        frames: List of TelemetryFrame objects
        config: Optional AnalysisConfig (uses defaults if not provided)

    Returns:
        List of BrakingMetrics for each detected braking zone
    """
    ...

def py_extract_corners(
    frames: list[TelemetryFrame],
    config: AnalysisConfig | None = None,
) -> list[CornerMetrics]:
    """Extract corners from telemetry frames.

    Args:
        frames: List of TelemetryFrame objects
        config: Optional AnalysisConfig (uses defaults if not provided)

    Returns:
        List of CornerMetrics for each detected corner
    """
    ...

def hello_from_rust(name: str | None = None) -> str:
    """A simple hello world function to verify Rust + PyO3 integration works."""
    ...

def compute_speed_stats(speeds: list[float]) -> tuple[float, float, float]:
    """Compute basic speed statistics from a list of speeds.

    Args:
        speeds: List of speed values in m/s

    Returns:
        Tuple of (min, max, mean) speeds
    """
    ...
