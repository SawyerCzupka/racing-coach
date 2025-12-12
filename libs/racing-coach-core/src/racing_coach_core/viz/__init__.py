"""Lap visualization module for racing telemetry analysis."""

from .boundary import (
    BOUNDARY_COLORS,
    LATERAL_COLORSCALE,
    create_augmented_telemetry_chart,
    create_lateral_position_chart,
    create_telemetry_with_lateral_chart,
    create_track_boundary_map,
    create_track_map_with_lateral_position,
    create_track_map_with_racing_line,
)
from .report import generate_lap_report

__all__ = [
    # Boundary visualizations
    "BOUNDARY_COLORS",
    "LATERAL_COLORSCALE",
    "create_augmented_telemetry_chart",
    "create_lateral_position_chart",
    "create_telemetry_with_lateral_chart",
    "create_track_boundary_map",
    "create_track_map_with_lateral_position",
    "create_track_map_with_racing_line",
    # Report generation
    "generate_lap_report",
]
