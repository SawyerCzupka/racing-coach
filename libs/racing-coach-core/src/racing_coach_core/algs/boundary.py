"""Track boundary extraction and lateral position calculation.

This module provides two main workflows:

Part 1: Create Track Boundaries (one-time per track)
    - extract_track_boundary_from_ibt() - Process boundary IBT file

Part 2: Calculate Lateral Position (every lap)
    - get_lateral_position() - Single point lookup
    - compute_lateral_positions() - Batch for TelemetrySequence
    - compute_lateral_positions_vectorized() - Numpy arrays for efficiency
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import irsdk  # type: ignore[import-untyped]
import numpy as np
import pandas as pd

from racing_coach_core.schemas.telemetry import TelemetrySequence
from racing_coach_core.schemas.track import (
    AugmentedTelemetrySequence,
    TrackBoundary,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Part 1: Create Track Boundaries
# =============================================================================


def extract_track_boundary_from_ibt(
    ibt_file_path: str | Path,
    left_lap_number: int = 1,
    right_lap_number: int = 3,
    grid_size: int = 1000,
) -> TrackBoundary:
    """
    Extract track boundary data from an IBT file containing boundary laps.

    This function processes an IBT file where the driver has recorded:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    Args:
        ibt_file_path: Path to the IBT file with boundary laps
        left_lap_number: Lap number for left boundary (default: 1)
        right_lap_number: Lap number for right boundary (default: 3)
        grid_size: Number of points in normalized grid (default: 1000)

    Returns:
        TrackBoundary with interpolated boundary data

    Raises:
        ValueError: If specified laps not found in IBT file
        RuntimeError: If IBT file cannot be opened
    """
    ibt_path = Path(ibt_file_path)

    # Initialize IBT reader for telemetry data
    ibt = irsdk.IBT()
    ibt.open(str(ibt_path))

    # Initialize IRSDK for session metadata
    ir = irsdk.IRSDK()
    if not ir.startup(test_file=str(ibt_path)):
        raise RuntimeError(f"Failed to open IBT file: {ibt_path}")

    try:
        # Extract session info for track metadata
        weekend_info: dict[str, Any] = ir["WeekendInfo"]  # type: ignore[index]
        track_id: int = weekend_info["TrackID"]
        track_name: str = weekend_info["TrackName"]
        track_config_name: str | None = weekend_info.get("TrackConfigName")

        logger.info(f"Processing IBT file for track: {track_name} (ID: {track_id})")

        # Get all telemetry data
        all_laps: list[Any] = ibt.get_all("Lap") or []
        all_lap_dist_pct: list[Any] = ibt.get_all("LapDistPct") or []
        all_lat: list[Any] = ibt.get_all("Lat") or []
        all_lon: list[Any] = ibt.get_all("Lon") or []

        if not all_laps:
            raise ValueError("No lap data found in IBT file")

        # Extract frames for each boundary lap
        left_data = _extract_lap_gps_data(
            all_laps, all_lap_dist_pct, all_lat, all_lon, left_lap_number
        )
        right_data = _extract_lap_gps_data(
            all_laps, all_lap_dist_pct, all_lat, all_lon, right_lap_number
        )

        if left_data.empty:
            raise ValueError(f"Left boundary lap {left_lap_number} not found in IBT file")
        if right_data.empty:
            raise ValueError(f"Right boundary lap {right_lap_number} not found in IBT file")

        logger.info(
            f"Extracted boundary data: left={len(left_data)} frames, right={len(right_data)} frames"
        )

        return TrackBoundary.from_boundary_laps(
            track_id=track_id,
            track_name=track_name,
            track_config_name=track_config_name,
            left_lap_data=left_data,
            right_lap_data=right_data,
            grid_size=grid_size,
        )

    finally:
        ir.shutdown()
        ibt.close()


def _extract_lap_gps_data(
    all_laps: list[Any],
    all_lap_dist_pct: list[Any],
    all_lat: list[Any],
    all_lon: list[Any],
    target_lap: int,
) -> pd.DataFrame:
    """
    Extract GPS data for a specific lap.

    Args:
        all_laps: List of lap numbers for each frame
        all_lap_dist_pct: List of lap distance percentages
        all_lat: List of latitudes
        all_lon: List of longitudes
        target_lap: Lap number to extract

    Returns:
        DataFrame with lap_distance_pct, latitude, longitude columns
    """
    indices = [i for i, lap in enumerate(all_laps) if lap == target_lap]

    if not indices:
        return pd.DataFrame()

    return pd.DataFrame(
        {
            "lap_distance_pct": [all_lap_dist_pct[i] for i in indices],
            "latitude": [all_lat[i] for i in indices],
            "longitude": [all_lon[i] for i in indices],
        }
    )


# =============================================================================
# Part 2: Calculate Lateral Position
# =============================================================================


def get_lateral_position(
    track_boundary: TrackBoundary,
    lap_distance_pct: float,
    lat: float,
    lon: float,
) -> float:
    """
    Calculate lateral position of a point relative to track boundaries.

    Args:
        track_boundary: The track boundary data
        lap_distance_pct: Current position along lap (0.0-1.0)
        lat: Current latitude
        lon: Current longitude

    Returns:
        Lateral position where:
        - -1.0 = left edge
        - 0.0 = center
        - 1.0 = right edge
        Values CAN exceed [-1, 1] if car is outside boundaries
    """
    # Normalize lap_distance_pct to [0, 1)
    lap_distance_pct = lap_distance_pct % 1.0

    # Find grid position (fractional index)
    grid_spacing = 1.0 / track_boundary.grid_size

    # Find surrounding grid indices
    idx_float = lap_distance_pct / grid_spacing
    idx_low = int(idx_float) % track_boundary.grid_size
    idx_high = (idx_low + 1) % track_boundary.grid_size
    t = idx_float - int(idx_float)  # Interpolation factor

    # Interpolate boundary positions
    left_lat = (1 - t) * track_boundary.left_latitude[idx_low] + t * track_boundary.left_latitude[
        idx_high
    ]
    left_lon = (1 - t) * track_boundary.left_longitude[idx_low] + t * track_boundary.left_longitude[
        idx_high
    ]
    right_lat = (1 - t) * track_boundary.right_latitude[
        idx_low
    ] + t * track_boundary.right_latitude[idx_high]
    right_lon = (1 - t) * track_boundary.right_longitude[
        idx_low
    ] + t * track_boundary.right_longitude[idx_high]

    # Calculate lateral position using projection
    return _project_to_lateral_position(
        car_lat=lat,
        car_lon=lon,
        left_lat=left_lat,
        left_lon=left_lon,
        right_lat=right_lat,
        right_lon=right_lon,
    )


def _project_to_lateral_position(
    car_lat: float,
    car_lon: float,
    left_lat: float,
    left_lon: float,
    right_lat: float,
    right_lon: float,
) -> float:
    """
    Project car position onto the line between left and right boundaries.

    Uses simple linear interpolation on lat/lon which is sufficient
    for short track segments.

    Returns:
        -1.0 at left boundary, 0.0 at center, 1.0 at right boundary.
        Extrapolates beyond [-1, 1] if car is outside boundaries.
    """
    # Vector from left to right boundary
    track_vec_lat = right_lat - left_lat
    track_vec_lon = right_lon - left_lon

    # Vector from left boundary to car
    car_vec_lat = car_lat - left_lat
    car_vec_lon = car_lon - left_lon

    # Project car vector onto track vector
    # t = (car_vec . track_vec) / (track_vec . track_vec)
    track_dot = track_vec_lat * track_vec_lat + track_vec_lon * track_vec_lon

    if track_dot < 1e-12:  # Boundaries too close, return center
        return 0.0

    t = (car_vec_lat * track_vec_lat + car_vec_lon * track_vec_lon) / track_dot

    # Convert t from [0, 1] to [-1, 1]
    # t=0 -> lateral=-1 (left), t=1 -> lateral=1 (right)
    lateral_position = 2.0 * t - 1.0

    return lateral_position


def compute_lateral_positions(
    track_boundary: TrackBoundary,
    telemetry_sequence: TelemetrySequence,
) -> AugmentedTelemetrySequence:
    """
    Compute lateral positions for all frames in a telemetry sequence.

    Args:
        track_boundary: Track boundary data
        telemetry_sequence: Sequence of telemetry frames

    Returns:
        AugmentedTelemetrySequence with lateral positions
    """
    lateral_positions = []

    for frame in telemetry_sequence.frames:
        lat_pos = get_lateral_position(
            track_boundary,
            frame.lap_distance_pct,
            frame.latitude,
            frame.longitude,
        )
        lateral_positions.append(lat_pos)

    return AugmentedTelemetrySequence(
        frames=telemetry_sequence.frames,
        lateral_positions=lateral_positions,
    )


def compute_lateral_positions_vectorized(
    track_boundary: TrackBoundary,
    lap_distance_pct: np.ndarray,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
) -> np.ndarray:
    """
    Vectorized computation of lateral positions for efficiency.

    For processing large datasets, this numpy-based implementation
    is significantly faster than the per-frame approach.

    Args:
        track_boundary: Track boundary data
        lap_distance_pct: Array of lap distance percentages
        latitudes: Array of latitudes
        longitudes: Array of longitudes

    Returns:
        Array of lateral positions (-1 to 1, can exceed for off-track)
    """
    # Pre-convert boundary data to numpy arrays
    left_lat = np.array(track_boundary.left_latitude)
    left_lon = np.array(track_boundary.left_longitude)
    right_lat = np.array(track_boundary.right_latitude)
    right_lon = np.array(track_boundary.right_longitude)

    # Normalize and find grid indices
    lap_dist_norm = lap_distance_pct % 1.0
    grid_spacing = 1.0 / track_boundary.grid_size
    idx_float = lap_dist_norm / grid_spacing
    idx_low = (idx_float.astype(int)) % track_boundary.grid_size
    idx_high = (idx_low + 1) % track_boundary.grid_size
    t = idx_float - idx_float.astype(int)

    # Vectorized interpolation of boundaries
    interp_left_lat = (1 - t) * left_lat[idx_low] + t * left_lat[idx_high]
    interp_left_lon = (1 - t) * left_lon[idx_low] + t * left_lon[idx_high]
    interp_right_lat = (1 - t) * right_lat[idx_low] + t * right_lat[idx_high]
    interp_right_lon = (1 - t) * right_lon[idx_low] + t * right_lon[idx_high]

    # Vectorized projection
    track_vec_lat = interp_right_lat - interp_left_lat
    track_vec_lon = interp_right_lon - interp_left_lon
    car_vec_lat = latitudes - interp_left_lat
    car_vec_lon = longitudes - interp_left_lon

    track_dot = track_vec_lat**2 + track_vec_lon**2
    # Avoid division by zero
    track_dot = np.maximum(track_dot, 1e-12)

    projection = (car_vec_lat * track_vec_lat + car_vec_lon * track_vec_lon) / track_dot
    lateral_positions = 2.0 * projection - 1.0

    return lateral_positions
