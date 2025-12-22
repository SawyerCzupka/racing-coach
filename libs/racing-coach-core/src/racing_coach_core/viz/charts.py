"""Chart building functions for lap visualization."""

from typing import Sequence

import numpy as np
import plotly.graph_objects as go

from .constants import MS_TO_KMH, accel_to_g, rad_to_deg
from .protocols import MetricsProtocol, TelemetryDataProtocol, TelemetryFrameProtocol
from .styles import (
    COLORS,
    MARKER_SIZES,
    SPEED_COLORSCALE,
    get_chart_layout,
    get_xaxis,
    get_yaxis,
)


def create_track_map(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
) -> go.Figure:
    """
    Create a track map showing the driving line colored by speed.

    Uses GPS coordinates (latitude/longitude) for accurate 2D track representation.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics for annotations

    Returns:
        Plotly figure with track map
    """
    frames = telemetry.frames

    # Extract GPS position and speed data
    # Use longitude for X (east-west) and latitude for Y (north-south)
    lon = [f.longitude for f in frames]
    lat = [f.latitude for f in frames]
    speed_kmh = [f.speed * MS_TO_KMH for f in frames]
    distances = [f.lap_distance for f in frames]

    fig = go.Figure()

    # Main driving line colored by speed
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
            customdata=list(zip(speed_kmh, distances)),  # type: ignore[arg-type]  # plotly stubs incorrect
            hovertemplate="Speed: %{customdata[0]:.1f} km/h<br>Distance: %{customdata[1]:.0f}m<extra></extra>",
            name="Driving Line",
            showlegend=False,
        )
    )

    # Add metric annotations if available
    if metrics:
        # Braking points with numbered labels
        brake_lon: list[float] = []
        brake_lat: list[float] = []
        brake_labels: list[str] = []
        for i, bz in enumerate(metrics.braking_zones, 1):
            idx = _find_closest_frame_by_distance(frames, bz.braking_point_distance)
            if idx is not None:
                brake_lon.append(frames[idx].longitude)
                brake_lat.append(frames[idx].latitude)
                brake_labels.append(f"B{i}")

        if brake_lon:
            fig.add_trace(
                go.Scatter(
                    x=brake_lon,
                    y=brake_lat,
                    mode="markers+text",
                    marker={
                        "symbol": "diamond",
                        "size": MARKER_SIZES["brake_point"],
                        "color": COLORS["brake_point_marker"],
                        "line": {"width": 1, "color": COLORS["text"]},
                    },
                    text=brake_labels,
                    textposition="top center",
                    textfont={"size": 9, "color": COLORS["brake"]},
                    name="Brake Points",
                    hovertemplate="%{text}<extra></extra>",
                )
            )

        # Corner apexes with numbered labels
        apex_lon: list[float] = []
        apex_lat: list[float] = []
        apex_labels: list[str] = []
        for i, corner in enumerate(metrics.corners, 1):
            idx = _find_closest_frame_by_distance(frames, corner.apex_distance)
            if idx is not None:
                apex_lon.append(frames[idx].longitude)
                apex_lat.append(frames[idx].latitude)
                apex_labels.append(f"C{i}")

        if apex_lon:
            fig.add_trace(
                go.Scatter(
                    x=apex_lon,
                    y=apex_lat,
                    mode="markers+text",
                    marker={
                        "symbol": "circle",
                        "size": MARKER_SIZES["apex"],
                        "color": COLORS["apex_marker"],
                        "line": {"width": 1, "color": COLORS["text"]},
                    },
                    text=apex_labels,
                    textposition="bottom center",
                    textfont={"size": 9, "color": COLORS["apex_marker"]},
                    name="Apexes",
                    hovertemplate="%{text}<extra></extra>",
                )
            )

    fig.update_layout(
        **get_chart_layout(
            "Track Map",
            legend={
                "x": 0,
                "y": 1,
                "bgcolor": "rgba(0,0,0,0.5)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis(title="", showticklabels=False, showgrid=False),
        yaxis=get_yaxis(title="", showticklabels=False, showgrid=False, scaleanchor="x"),
    )

    return fig


def create_speed_chart(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
) -> go.Figure:
    """
    Create a speed vs distance chart with braking zone annotations.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics for annotations

    Returns:
        Plotly figure with speed chart
    """
    frames = telemetry.frames

    distances = [f.lap_distance for f in frames]
    speed_kmh = [f.speed * MS_TO_KMH for f in frames]

    fig = go.Figure()

    # Add braking zone shading first (behind the line)
    if metrics:
        _add_braking_zone_shading(fig, metrics)

    # Speed trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=speed_kmh,
            mode="lines",
            line={"color": COLORS["speed"], "width": 2},
            name="Speed",
            hovertemplate="Distance: %{x:.0f}m<br>Speed: %{y:.1f} km/h<extra></extra>",
        )
    )

    # Add corner apex markers with labels
    if metrics:
        _add_corner_apex_markers(fig, metrics)

    fig.update_layout(
        **get_chart_layout("Speed", showlegend=False),
        xaxis=get_xaxis("Distance (m)"),
        yaxis=get_yaxis("Speed (km/h)"),
    )

    return fig


def create_inputs_chart(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
) -> go.Figure:
    """
    Create a throttle/brake inputs vs distance chart.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics for annotations

    Returns:
        Plotly figure with inputs chart
    """
    frames = telemetry.frames

    distances = [f.lap_distance for f in frames]
    throttle = [f.throttle * 100 for f in frames]  # Convert to percentage
    brake = [f.brake * 100 for f in frames]

    fig = go.Figure()

    # Add braking zone shading with labels
    if metrics:
        _add_braking_zone_shading(fig, metrics)

    # Throttle trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=throttle,
            mode="lines",
            line={"color": COLORS["throttle"], "width": 2},
            name="Throttle",
            hovertemplate="Distance: %{x:.0f}m<br>Throttle: %{y:.0f}%<extra></extra>",
        )
    )

    # Brake trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=brake,
            mode="lines",
            line={"color": COLORS["brake"], "width": 2},
            name="Brake",
            hovertemplate="Distance: %{x:.0f}m<br>Brake: %{y:.0f}%<extra></extra>",
        )
    )

    fig.update_layout(
        **get_chart_layout(
            "Inputs",
            legend={
                "x": 1,
                "y": 1,
                "xanchor": "right",
                "bgcolor": "rgba(0,0,0,0.5)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis("Distance (m)"),
        yaxis=get_yaxis("Input (%)", range=[0, 105]),
    )

    return fig


def create_steering_chart(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
) -> go.Figure:
    """
    Create a steering angle vs distance chart with corner annotations.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics for annotations

    Returns:
        Plotly figure with steering chart
    """
    frames = telemetry.frames

    distances = [f.lap_distance for f in frames]
    steering_deg = [rad_to_deg(f.steering_angle) for f in frames]

    fig = go.Figure()

    # Add corner region shading with labels
    if metrics:
        _add_corner_region_shading(fig, metrics)

    # Steering trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=steering_deg,
            mode="lines",
            line={"color": COLORS["steering"], "width": 2},
            name="Steering",
            hovertemplate="Distance: %{x:.0f}m<br>Steering: %{y:.1f}°<extra></extra>",
        )
    )

    fig.update_layout(
        **get_chart_layout("Steering Angle", showlegend=False),
        xaxis=get_xaxis("Distance (m)"),
        yaxis=get_yaxis("Angle (degrees)"),
    )

    return fig


def create_gforce_chart(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
) -> go.Figure:
    """
    Create a G-force vs distance chart.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics for annotations

    Returns:
        Plotly figure with G-force chart
    """
    frames = telemetry.frames

    distances = [f.lap_distance for f in frames]
    lateral_g = [accel_to_g(f.lateral_acceleration) for f in frames]
    longitudinal_g = [accel_to_g(f.longitudinal_acceleration) for f in frames]

    fig = go.Figure()

    # Add braking zone shading with labels
    if metrics:
        _add_braking_zone_shading(fig, metrics)

    # Lateral G trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=lateral_g,
            mode="lines",
            line={"color": COLORS["lateral_g"], "width": 2},
            name="Lateral G",
            hovertemplate="Distance: %{x:.0f}m<br>Lateral: %{y:.2f}G<extra></extra>",
        )
    )

    # Longitudinal G trace
    fig.add_trace(
        go.Scatter(
            x=distances,
            y=longitudinal_g,
            mode="lines",
            line={"color": COLORS["longitudinal_g"], "width": 2},
            name="Longitudinal G",
            hovertemplate="Distance: %{x:.0f}m<br>Longitudinal: %{y:.2f}G<extra></extra>",
        )
    )

    fig.update_layout(
        **get_chart_layout(
            "G-Forces",
            legend={
                "x": 1,
                "y": 1,
                "xanchor": "right",
                "bgcolor": "rgba(0,0,0,0.5)",
                "font": {"color": COLORS["text"]},
            },
        ),
        xaxis=get_xaxis("Distance (m)"),
        yaxis=get_yaxis("G-Force"),
    )

    return fig


def create_friction_circle(telemetry: TelemetryDataProtocol) -> go.Figure:
    """
    Create a G-G diagram (friction circle) showing lateral vs longitudinal G.

    Args:
        telemetry: Lap telemetry data

    Returns:
        Plotly figure with friction circle
    """
    frames = telemetry.frames

    lateral_g = [accel_to_g(f.lateral_acceleration) for f in frames]
    longitudinal_g = [accel_to_g(f.longitudinal_acceleration) for f in frames]
    speed_kmh = [f.speed * MS_TO_KMH for f in frames]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=lateral_g,
            y=longitudinal_g,
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
            hovertemplate="Lateral: %{x:.2f}G<br>Longitudinal: %{y:.2f}G<extra></extra>",
            showlegend=False,
        )
    )

    # Add reference circles
    for g_level in [1.0, 2.0, 3.0]:
        theta = np.linspace(0, 2 * np.pi, 100)
        fig.add_trace(
            go.Scatter(
                x=g_level * np.cos(theta),
                y=g_level * np.sin(theta),
                mode="lines",
                line={"color": COLORS["grid"], "width": 1, "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        **get_chart_layout("Friction Circle (G-G Diagram)"),
        xaxis=get_xaxis("Lateral G", zeroline=True, zerolinewidth=1),
        yaxis=get_yaxis("Longitudinal G", zeroline=True, zerolinewidth=1, scaleanchor="x"),
    )

    return fig


def _add_braking_zone_shading(fig: go.Figure, metrics: MetricsProtocol) -> None:
    """Add braking zone shading rectangles to a figure."""
    for i, bz in enumerate(metrics.braking_zones, 1):
        fig.add_vrect(
            x0=bz.braking_point_distance,
            x1=bz.end_distance,
            fillcolor=COLORS["braking_zone"],
            line_width=0,
            layer="below",
            annotation_text=f"B{i}",
            annotation_position="top left",
            annotation={"font": {"size": 10, "color": COLORS["brake"]}},
        )


def _add_corner_apex_markers(fig: go.Figure, metrics: MetricsProtocol) -> None:
    """Add corner apex vertical line markers to a figure."""
    for i, corner in enumerate(metrics.corners, 1):
        fig.add_vline(
            x=corner.apex_distance,
            line_dash="dot",
            line_color=COLORS["apex_marker"],
            opacity=0.5,
            annotation_text=f"C{i}",
            annotation_position="bottom",
            annotation={"font": {"size": 9, "color": COLORS["apex_marker"]}},
        )


def _add_corner_region_shading(fig: go.Figure, metrics: MetricsProtocol) -> None:
    """Add corner region shading rectangles to a figure."""
    for i, corner in enumerate(metrics.corners, 1):
        fig.add_vrect(
            x0=corner.turn_in_distance,
            x1=corner.exit_distance,
            fillcolor=COLORS["corner_region"],
            line_width=0,
            layer="below",
            annotation_text=f"C{i}",
            annotation_position="top left",
            annotation={"font": {"size": 10, "color": COLORS["steering"]}},
        )


def _find_closest_frame_by_distance(
    frames: Sequence[TelemetryFrameProtocol], target_distance: float
) -> int | None:
    """Find the index of the frame closest to the target distance."""
    if not frames:
        return None

    closest_idx = 0
    closest_diff = abs(frames[0].lap_distance - target_distance)

    for i, frame in enumerate(frames):
        diff = abs(frame.lap_distance - target_distance)
        if diff < closest_diff:
            closest_diff = diff
            closest_idx = i

    return closest_idx
