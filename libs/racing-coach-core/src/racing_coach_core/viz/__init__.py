"""Lap visualization module for racing telemetry analysis.

This module provides reusable visualization functions for racing telemetry data.
The visualization functions use Protocol-based interfaces, allowing them to work
with any compatible data source.

The CLI (python -m racing_coach_core.viz) requires the racing-coach-server-client
package. Install with: uv add racing-coach-core[viz-cli]
"""

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
from .protocols import (
    BrakingZoneProtocol,
    CornerProtocol,
    MetricsProtocol,
    SessionInfoProtocol,
    TelemetryDataProtocol,
    TelemetryFrameProtocol,
)
from .report import generate_lap_report

__all__ = [
    # Protocols for type hints
    "BrakingZoneProtocol",
    "CornerProtocol",
    "MetricsProtocol",
    "SessionInfoProtocol",
    "TelemetryDataProtocol",
    "TelemetryFrameProtocol",
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
