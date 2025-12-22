"""Protocol definitions for visualization functions.

These protocols define the minimal interfaces required by visualization functions,
allowing them to work with any compatible data source (server responses, core schemas,
or custom implementations).
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class TelemetryFrameProtocol(Protocol):
    """Minimal interface for a telemetry frame."""

    @property
    def lap_distance(self) -> float:
        """Distance traveled in the lap (meters)."""
        ...

    @property
    def speed(self) -> float:
        """Speed in m/s."""
        ...

    @property
    def throttle(self) -> float:
        """Throttle position (0-1)."""
        ...

    @property
    def brake(self) -> float:
        """Brake position (0-1)."""
        ...

    @property
    def steering_angle(self) -> float:
        """Steering angle in radians."""
        ...

    @property
    def latitude(self) -> float:
        """GPS latitude coordinate."""
        ...

    @property
    def longitude(self) -> float:
        """GPS longitude coordinate."""
        ...

    @property
    def lateral_acceleration(self) -> float:
        """Lateral acceleration in m/s^2."""
        ...

    @property
    def longitudinal_acceleration(self) -> float:
        """Longitudinal acceleration in m/s^2."""
        ...


@runtime_checkable
class TelemetryDataProtocol(Protocol):
    """Minimal interface for lap telemetry data."""

    @property
    def frames(self) -> Sequence[TelemetryFrameProtocol]:
        """Sequence of telemetry frames."""
        ...

    @property
    def lap_number(self) -> int:
        """Lap number."""
        ...

    @property
    def frame_count(self) -> int:
        """Number of telemetry frames."""
        ...


@runtime_checkable
class BrakingZoneProtocol(Protocol):
    """Minimal interface for a braking zone."""

    @property
    def braking_point_distance(self) -> float:
        """Distance at which braking starts (meters)."""
        ...

    @property
    def end_distance(self) -> float:
        """Distance at which braking ends (meters)."""
        ...

    @property
    def braking_point_speed(self) -> float:
        """Speed at braking point (m/s)."""
        ...

    @property
    def minimum_speed(self) -> float:
        """Minimum speed in braking zone (m/s)."""
        ...

    @property
    def max_brake_pressure(self) -> float:
        """Maximum brake pressure (0-1)."""
        ...

    @property
    def braking_duration(self) -> float:
        """Duration of braking (seconds)."""
        ...

    @property
    def braking_efficiency(self) -> float:
        """Braking efficiency percentage."""
        ...

    @property
    def has_trail_braking(self) -> bool:
        """Whether trail braking was detected."""
        ...


@runtime_checkable
class CornerProtocol(Protocol):
    """Minimal interface for a corner."""

    @property
    def apex_distance(self) -> float:
        """Distance at corner apex (meters)."""
        ...

    @property
    def turn_in_distance(self) -> float:
        """Distance at turn-in point (meters)."""
        ...

    @property
    def exit_distance(self) -> float:
        """Distance at corner exit (meters)."""
        ...

    @property
    def turn_in_speed(self) -> float:
        """Speed at turn-in (m/s)."""
        ...

    @property
    def apex_speed(self) -> float:
        """Speed at apex (m/s)."""
        ...

    @property
    def exit_speed(self) -> float:
        """Speed at exit (m/s)."""
        ...

    @property
    def max_lateral_g(self) -> float:
        """Maximum lateral G-force."""
        ...

    @property
    def time_in_corner(self) -> float:
        """Time spent in corner (seconds)."""
        ...

    @property
    def max_steering_angle(self) -> float:
        """Maximum steering angle in radians."""
        ...


@runtime_checkable
class MetricsProtocol(Protocol):
    """Minimal interface for lap metrics."""

    @property
    def lap_time(self) -> float | None:
        """Lap time in seconds."""
        ...

    @property
    def max_speed(self) -> float:
        """Maximum speed (m/s)."""
        ...

    @property
    def min_speed(self) -> float:
        """Minimum speed (m/s)."""
        ...

    @property
    def average_corner_speed(self) -> float:
        """Average speed through corners (m/s)."""
        ...

    @property
    def total_braking_zones(self) -> int:
        """Total number of braking zones."""
        ...

    @property
    def total_corners(self) -> int:
        """Total number of corners."""
        ...

    @property
    def braking_zones(self) -> Sequence[BrakingZoneProtocol]:
        """List of braking zones."""
        ...

    @property
    def corners(self) -> Sequence[CornerProtocol]:
        """List of corners."""
        ...


@runtime_checkable
class SessionInfoProtocol(Protocol):
    """Minimal interface for session info."""

    @property
    def track_name(self) -> str:
        """Track name."""
        ...

    @property
    def track_config_name(self) -> str | None:
        """Track configuration name (if applicable)."""
        ...

    @property
    def car_name(self) -> str:
        """Car name."""
        ...


__all__ = [
    "TelemetryFrameProtocol",
    "TelemetryDataProtocol",
    "BrakingZoneProtocol",
    "CornerProtocol",
    "MetricsProtocol",
    "SessionInfoProtocol",
]
