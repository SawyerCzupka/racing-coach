"""Track-related utility functions."""


def normalize_lap_distance_delta(delta: float, lap_range: float = 1.0) -> float:
    """
    Normalize a lap distance delta to handle wrap-around at start/finish line.

    When calculating distance between two points on a circular track,
    a negative delta indicates the segment crosses the start/finish line.

    Args:
        delta: Raw distance difference (end - start), can be negative
        lap_range: Total lap distance (1.0 for normalized, or track_length in meters)

    Returns:
        Positive distance delta, corrected for lap wrap-around

    Example:
        >>> normalize_lap_distance_delta(0.95 - 0.05)  # Normal case
        0.9
        >>> normalize_lap_distance_delta(0.05 - 0.95)  # Crosses S/F line
        0.1
    """
    return delta + lap_range if delta < 0 else delta
