"""Track boundary visualization functions.

This module provides reusable plotting utilities for visualizing track boundaries
and lateral position data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .constants import MS_TO_KMH
from .styles import COLORS, SPEED_COLORSCALE, get_chart_layout, get_xaxis, get_yaxis

if TYPE_CHECKING:
    from racing_coach_core.schemas.track import (
        AugmentedTelemetrySequence,
        TrackBoundary,
    )

# Lateral position colorscale: red (left) -> white (center) -> blue (right)
LATERAL_COLORSCALE = [
    [0.0, "#ef4444"],  # red - full left
    [0.25, "#fca5a5"],  # light red
    [0.5, "#ffffff"],  # white - center
    [0.75, "#93c5fd"],  # light blue
    [1.0, "#3b82f6"],  # blue - full right
]

# Additional colors for boundary visualization
BOUNDARY_COLORS = {
    "left_boundary": "#ef4444",  # red
    "right_boundary": "#22c55e",  # green
    "center_line": "#6b7280",  # gray
    "lateral": "#f59e0b",  # amber
    "start_finish": "#fbbf24",  # yellow
}


def create_track_boundary_map(
    boundary: "TrackBoundary",
    show_center_line: bool = True,
    show_start_finish: bool = True,
    title: str | None = None,
) -> go.Figure:
    """
    Create a 2D track map showing left and right boundaries.

    Args:
        boundary: TrackBoundary object with left/right boundary data
        show_center_line: Whether to show the center line (default: True)
        show_start_finish: Whether to mark the start/finish (default: True)
        title: Optional custom title (default: uses track name)

    Returns:
        Plotly figure with track boundary map
    """
    fig = go.Figure()

    left_lon = np.array(boundary.left_longitude)
    left_lat = np.array(boundary.left_latitude)
    right_lon = np.array(boundary.right_longitude)
    right_lat = np.array(boundary.right_latitude)

    # Left boundary
    fig.add_trace(
        go.Scatter(
            x=left_lon,
            y=left_lat,
            mode="lines",
            line={"color": BOUNDARY_COLORS["left_boundary"], "width": 2},
            name="Left Boundary",
        )
    )

    # Right boundary
    fig.add_trace(
        go.Scatter(
            x=right_lon,
            y=right_lat,
            mode="lines",
            line={"color": BOUNDARY_COLORS["right_boundary"], "width": 2},
            name="Right Boundary",
        )
    )

    # Center line
    if show_center_line:
        center_lon = (left_lon + right_lon) / 2
        center_lat = (left_lat + right_lat) / 2
        fig.add_trace(
            go.Scatter(
                x=center_lon,
                y=center_lat,
                mode="lines",
                line={"color": BOUNDARY_COLORS["center_line"], "width": 1, "dash": "dash"},
                name="Center Line",
            )
        )

    # Start/Finish marker
    if show_start_finish:
        sf_lon = (left_lon[0] + right_lon[0]) / 2
        sf_lat = (left_lat[0] + right_lat[0]) / 2
        fig.add_trace(
            go.Scatter(
                x=[sf_lon],
                y=[sf_lat],
                mode="markers+text",
                marker={"size": 14, "color": BOUNDARY_COLORS["start_finish"], "symbol": "star"},
                text=["S/F"],
                textposition="top center",
                textfont={"color": COLORS["text"], "size": 12},
                name="Start/Finish",
            )
        )

    # Layout
    map_title = title or f"{boundary.track_name} Track Boundaries"
    fig.update_layout(
        **get_chart_layout(
            map_title,
            legend={
                "x": 0,
                "y": 1,
                "bgcolor": "rgba(0,0,0,0.7)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis(title="", showticklabels=False, showgrid=False),
        yaxis=get_yaxis(title="", showticklabels=False, showgrid=False, scaleanchor="x"),
        height=800,
    )

    return fig


def create_track_map_with_racing_line(
    boundary: "TrackBoundary",
    longitudes: list[float] | np.ndarray,
    latitudes: list[float] | np.ndarray,
    speeds: list[float] | np.ndarray,
    show_boundaries: bool = True,
    show_start_finish: bool = True,
    title: str | None = None,
) -> go.Figure:
    """
    Create a track map with racing line colored by speed.

    Args:
        boundary: TrackBoundary object with left/right boundary data
        longitudes: Racing line longitude coordinates
        latitudes: Racing line latitude coordinates
        speeds: Speed values in m/s (will be converted to km/h for display)
        show_boundaries: Whether to show track boundaries (default: True)
        show_start_finish: Whether to mark the start/finish (default: True)
        title: Optional custom title

    Returns:
        Plotly figure with track map and racing line
    """
    fig = go.Figure()

    lon = np.array(longitudes)
    lat = np.array(latitudes)
    speed_kmh = np.array(speeds) * MS_TO_KMH

    # Track boundaries
    if show_boundaries:
        left_lon = np.array(boundary.left_longitude)
        left_lat = np.array(boundary.left_latitude)
        right_lon = np.array(boundary.right_longitude)
        right_lat = np.array(boundary.right_latitude)

        fig.add_trace(
            go.Scatter(
                x=left_lon,
                y=left_lat,
                mode="lines",
                line={"color": BOUNDARY_COLORS["left_boundary"], "width": 2, "dash": "dot"},
                name="Left Boundary",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=right_lon,
                y=right_lat,
                mode="lines",
                line={"color": BOUNDARY_COLORS["right_boundary"], "width": 2, "dash": "dot"},
                name="Right Boundary",
            )
        )

    # Racing line colored by speed
    fig.add_trace(
        go.Scatter(
            x=lon,
            y=lat,
            mode="markers",
            marker={
                "size": 3,
                "color": speed_kmh,
                "colorscale": SPEED_COLORSCALE,
                "colorbar": {
                    "title": {"text": "Speed (km/h)", "font": {"color": COLORS["text"]}},
                    "tickfont": {"color": COLORS["text_secondary"]},
                },
                "showscale": True,
            },
            name="Racing Line",
            hovertemplate="Speed: %{marker.color:.1f} km/h<extra></extra>",
        )
    )

    # Start/Finish marker
    if show_start_finish and len(lon) > 0:
        fig.add_trace(
            go.Scatter(
                x=[lon[0]],
                y=[lat[0]],
                mode="markers+text",
                marker={"size": 12, "color": BOUNDARY_COLORS["start_finish"], "symbol": "star"},
                text=["S/F"],
                textposition="top center",
                textfont={"color": COLORS["text"], "size": 12},
                name="Start/Finish",
            )
        )

    map_title = title or f"{boundary.track_name} - Racing Line"
    fig.update_layout(
        **get_chart_layout(
            map_title,
            legend={
                "x": 0,
                "y": 1,
                "bgcolor": "rgba(0,0,0,0.7)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis(title="", showticklabels=False, showgrid=False),
        yaxis=get_yaxis(title="", showticklabels=False, showgrid=False, scaleanchor="x"),
        height=800,
    )

    return fig


def create_track_map_with_lateral_position(
    boundary: "TrackBoundary",
    longitudes: list[float] | np.ndarray,
    latitudes: list[float] | np.ndarray,
    lateral_positions: list[float] | np.ndarray,
    show_boundaries: bool = True,
    show_start_finish: bool = True,
    title: str | None = None,
) -> go.Figure:
    """
    Create a track map with racing line colored by lateral position.

    Args:
        boundary: TrackBoundary object with left/right boundary data
        longitudes: Racing line longitude coordinates
        latitudes: Racing line latitude coordinates
        lateral_positions: Lateral position values (-1=left, 0=center, 1=right)
        show_boundaries: Whether to show track boundaries (default: True)
        show_start_finish: Whether to mark the start/finish (default: True)
        title: Optional custom title

    Returns:
        Plotly figure with track map colored by lateral position
    """
    fig = go.Figure()

    lon = np.array(longitudes)
    lat = np.array(latitudes)
    lateral = np.array(lateral_positions)

    # Track boundaries
    if show_boundaries:
        left_lon = np.array(boundary.left_longitude)
        left_lat = np.array(boundary.left_latitude)
        right_lon = np.array(boundary.right_longitude)
        right_lat = np.array(boundary.right_latitude)

        fig.add_trace(
            go.Scatter(
                x=left_lon,
                y=left_lat,
                mode="lines",
                line={"color": BOUNDARY_COLORS["left_boundary"], "width": 2, "dash": "dot"},
                name="Left Boundary",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=right_lon,
                y=right_lat,
                mode="lines",
                line={"color": BOUNDARY_COLORS["right_boundary"], "width": 2, "dash": "dot"},
                name="Right Boundary",
            )
        )

    # Normalize lateral positions to 0-1 for colorscale
    lateral_normalized = np.clip((lateral + 1) / 2, 0, 1)

    # Racing line colored by lateral position
    fig.add_trace(
        go.Scatter(
            x=lon,
            y=lat,
            mode="markers",
            marker={
                "size": 4,
                "color": lateral_normalized,
                "colorscale": LATERAL_COLORSCALE,
                "cmin": 0,
                "cmax": 1,
                "colorbar": {
                    "title": {"text": "Track Position", "font": {"color": COLORS["text"]}},
                    "tickfont": {"color": COLORS["text_secondary"]},
                    "tickvals": [0, 0.25, 0.5, 0.75, 1],
                    "ticktext": ["Left", "", "Center", "", "Right"],
                },
                "showscale": True,
            },
            name="Racing Line",
            customdata=lateral,
            hovertemplate="Lateral: %{customdata:.2f}<extra></extra>",
        )
    )

    # Start/Finish marker
    if show_start_finish and len(lon) > 0:
        fig.add_trace(
            go.Scatter(
                x=[lon[0]],
                y=[lat[0]],
                mode="markers+text",
                marker={"size": 14, "color": BOUNDARY_COLORS["start_finish"], "symbol": "star"},
                text=["S/F"],
                textposition="top center",
                textfont={"color": COLORS["text"], "size": 12},
                name="Start/Finish",
            )
        )

    map_title = title or f"{boundary.track_name} - Lateral Position"
    fig.update_layout(
        **get_chart_layout(
            map_title,
            legend={
                "x": 0,
                "y": 1,
                "bgcolor": "rgba(0,0,0,0.7)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis(title="", showticklabels=False, showgrid=False),
        yaxis=get_yaxis(title="", showticklabels=False, showgrid=False, scaleanchor="x"),
        height=800,
    )

    return fig


def create_lateral_position_chart(
    distances: list[float] | np.ndarray,
    lateral_positions: list[float] | np.ndarray,
    title: str = "Lateral Position",
) -> go.Figure:
    """
    Create a lateral position vs distance chart.

    Args:
        distances: Distance values in meters
        lateral_positions: Lateral position values (-1=left, 0=center, 1=right)
        title: Chart title

    Returns:
        Plotly figure with lateral position chart
    """
    fig = go.Figure()

    dist = np.array(distances)
    lateral = np.array(lateral_positions)

    # Lateral position trace with fill
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=lateral,
            mode="lines",
            line={"color": BOUNDARY_COLORS["lateral"], "width": 1.5},
            name="Lateral Position",
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.2)",
            hovertemplate="Distance: %{x:.0f}m<br>Lateral: %{y:.2f}<extra></extra>",
        )
    )

    # Reference lines
    fig.add_hline(y=-1, line_dash="dash", line_color=COLORS["text_secondary"], opacity=0.5)
    fig.add_hline(y=1, line_dash="dash", line_color=COLORS["text_secondary"], opacity=0.5)
    fig.add_hline(y=0, line_dash="solid", line_color=COLORS["text_secondary"], opacity=0.3)

    # Annotations for boundaries
    fig.add_annotation(
        x=0.02,
        y=-1,
        xref="paper",
        yref="y",
        text="Left Edge",
        showarrow=False,
        font={"color": COLORS["text_secondary"], "size": 10},
    )
    fig.add_annotation(
        x=0.02,
        y=1,
        xref="paper",
        yref="y",
        text="Right Edge",
        showarrow=False,
        font={"color": COLORS["text_secondary"], "size": 10},
    )

    fig.update_layout(
        **get_chart_layout(title, showlegend=False),
        xaxis=get_xaxis("Distance (m)"),
        yaxis=get_yaxis("Lateral Position", range=[-1.5, 1.5]),
    )

    return fig


def create_telemetry_with_lateral_chart(
    distances: list[float] | np.ndarray,
    speeds: list[float] | np.ndarray,
    throttle: list[float] | np.ndarray,
    brake: list[float] | np.ndarray,
    steering: list[float] | np.ndarray,
    lateral_positions: list[float] | np.ndarray,
    title: str = "Telemetry with Lateral Position",
) -> go.Figure:
    """
    Create a multi-panel telemetry chart including lateral position.

    Args:
        distances: Distance values in meters
        speeds: Speed values in m/s
        throttle: Throttle values (0-1)
        brake: Brake values (0-1)
        steering: Steering angle in radians
        lateral_positions: Lateral position values (-1=left, 0=center, 1=right)
        title: Chart title

    Returns:
        Plotly figure with 4-panel telemetry chart
    """
    dist = np.array(distances)
    speed_kmh = np.array(speeds) * MS_TO_KMH
    throttle_pct = np.array(throttle) * 100
    brake_pct = np.array(brake) * 100
    steering_deg = np.degrees(np.array(steering))
    lateral = np.array(lateral_positions)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "Speed (km/h)",
            "Throttle & Brake (%)",
            "Steering (deg)",
            "Lateral Position",
        ),
    )

    # Speed
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=speed_kmh,
            mode="lines",
            line={"color": COLORS["speed"], "width": 1.5},
            name="Speed",
            hovertemplate="Distance: %{x:.0f}m<br>Speed: %{y:.1f} km/h<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Throttle
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=throttle_pct,
            mode="lines",
            line={"color": COLORS["throttle"], "width": 1.5},
            name="Throttle",
            hovertemplate="Distance: %{x:.0f}m<br>Throttle: %{y:.0f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Brake
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=brake_pct,
            mode="lines",
            line={"color": COLORS["brake"], "width": 1.5},
            name="Brake",
            hovertemplate="Distance: %{x:.0f}m<br>Brake: %{y:.0f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Steering
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=steering_deg,
            mode="lines",
            line={"color": COLORS["steering"], "width": 1.5},
            name="Steering",
            hovertemplate="Distance: %{x:.0f}m<br>Steering: %{y:.1f}°<extra></extra>",
        ),
        row=3,
        col=1,
    )

    # Lateral position
    fig.add_trace(
        go.Scatter(
            x=dist,
            y=lateral,
            mode="lines",
            line={"color": BOUNDARY_COLORS["lateral"], "width": 1.5},
            name="Lateral",
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.2)",
            hovertemplate="Distance: %{x:.0f}m<br>Lateral: %{y:.2f}<extra></extra>",
        ),
        row=4,
        col=1,
    )

    # Reference lines for lateral position
    fig.add_hline(
        y=-1, line_dash="dash", line_color=COLORS["text_secondary"], opacity=0.5, row=4, col=1
    )
    fig.add_hline(
        y=1, line_dash="dash", line_color=COLORS["text_secondary"], opacity=0.5, row=4, col=1
    )
    fig.add_hline(
        y=0, line_dash="solid", line_color=COLORS["text_secondary"], opacity=0.3, row=4, col=1
    )

    # Update layout
    fig.update_layout(
        title={"text": title, "font": {"color": COLORS["text"]}},
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["background"],
        font={"color": COLORS["text"]},
        height=900,
        showlegend=True,
        legend={"x": 1.02, "y": 1, "bgcolor": "rgba(0,0,0,0.5)"},
    )

    # Update all axes
    for i in range(1, 5):
        fig.update_xaxes(
            gridcolor=COLORS["grid"], tickfont={"color": COLORS["text_secondary"]}, row=i, col=1
        )
        fig.update_yaxes(
            gridcolor=COLORS["grid"], tickfont={"color": COLORS["text_secondary"]}, row=i, col=1
        )

    fig.update_xaxes(title_text="Distance (m)", row=4, col=1)

    return fig


def create_augmented_telemetry_chart(
    augmented_sequence: "AugmentedTelemetrySequence",
    title: str = "Augmented Telemetry",
) -> go.Figure:
    """
    Create a telemetry chart from an AugmentedTelemetrySequence.

    Args:
        augmented_sequence: AugmentedTelemetrySequence with frames and lateral positions
        title: Chart title

    Returns:
        Plotly figure with telemetry chart
    """
    frames = augmented_sequence.frames
    lateral = augmented_sequence.lateral_positions

    distances = [f.lap_distance for f in frames]
    speeds = [f.speed for f in frames]
    throttle = [f.throttle for f in frames]
    brake = [f.brake for f in frames]
    steering = [f.steering_angle for f in frames]

    return create_telemetry_with_lateral_chart(
        distances=distances,
        speeds=speeds,
        throttle=throttle,
        brake=brake,
        steering=steering,
        lateral_positions=lateral,
        title=title,
    )
