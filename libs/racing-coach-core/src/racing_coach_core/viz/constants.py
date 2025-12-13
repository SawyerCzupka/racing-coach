"""Unit conversion constants and helper functions for visualization."""

# Unit conversion constants
MS_TO_KMH: float = 3.6
"""Convert meters per second to kilometers per hour."""

RAD_TO_DEG: float = 57.2957795131
"""Convert radians to degrees (180/π)."""

GRAVITY_MS2: float = 9.81
"""Standard gravity in m/s² for G-force calculations."""


def speed_to_kmh(speed_ms: float) -> float:
    """Convert speed from m/s to km/h."""
    return speed_ms * MS_TO_KMH


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees."""
    return radians * RAD_TO_DEG


def accel_to_g(accel_ms2: float) -> float:
    """Convert acceleration from m/s² to G-force."""
    return accel_ms2 / GRAVITY_MS2
