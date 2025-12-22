"""HTML report generation for lap visualization."""

from .charts import (
    create_friction_circle,
    create_gforce_chart,
    create_inputs_chart,
    create_speed_chart,
    create_steering_chart,
    create_track_map,
)
from .constants import MS_TO_KMH, RAD_TO_DEG
from .protocols import MetricsProtocol, SessionInfoProtocol, TelemetryDataProtocol
from .styles import COLORS


def generate_lap_report(
    telemetry: TelemetryDataProtocol,
    metrics: MetricsProtocol | None = None,
    session: SessionInfoProtocol | None = None,
) -> str:
    """
    Generate a complete HTML report for a lap.

    Args:
        telemetry: Lap telemetry data
        metrics: Optional lap metrics
        session: Optional session info for metadata

    Returns:
        Complete HTML string
    """
    # Build header info
    track_name = session.track_name if session else "Unknown Track"
    track_config = session.track_config_name if session and session.track_config_name else ""
    car_name = session.car_name if session else "Unknown Car"
    lap_number = telemetry.lap_number
    lap_time = _format_lap_time(metrics.lap_time) if metrics and metrics.lap_time else "N/A"

    track_display = f"{track_name} - {track_config}" if track_config else track_name

    # Generate individual charts
    track_map = create_track_map(telemetry, metrics)
    speed_chart = create_speed_chart(telemetry, metrics)
    inputs_chart = create_inputs_chart(telemetry, metrics)
    steering_chart = create_steering_chart(telemetry, metrics)
    gforce_chart = create_gforce_chart(telemetry, metrics)
    friction_circle = create_friction_circle(telemetry)

    # Build metrics summary HTML
    metrics_html = _build_metrics_summary_html(metrics) if metrics else ""

    # Build braking zones table
    braking_table_html = _build_braking_table_html(metrics) if metrics else ""

    # Build corners table
    corners_table_html = _build_corners_table_html(metrics) if metrics else ""

    # Convert figures to HTML divs
    track_map_html = track_map.to_html(full_html=False, include_plotlyjs=False)
    speed_chart_html = speed_chart.to_html(full_html=False, include_plotlyjs=False)
    inputs_chart_html = inputs_chart.to_html(full_html=False, include_plotlyjs=False)
    steering_chart_html = steering_chart.to_html(full_html=False, include_plotlyjs=False)
    gforce_chart_html = gforce_chart.to_html(full_html=False, include_plotlyjs=False)
    friction_circle_html = friction_circle.to_html(full_html=False, include_plotlyjs=False)

    # Assemble the full HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lap {lap_number} - {track_display}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background-color: {COLORS["paper"]};
            color: {COLORS["text"]};
            line-height: 1.5;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: {COLORS["background"]};
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 1.5rem;
            margin-bottom: 8px;
        }}
        .header-meta {{
            display: flex;
            gap: 24px;
            color: {COLORS["text_secondary"]};
            font-size: 0.9rem;
        }}
        .header-meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .grid-2col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .grid-3col {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-container {{
            background-color: {COLORS["background"]};
            border-radius: 8px;
            padding: 16px;
            min-height: 350px;
        }}
        .chart-container.tall {{
            min-height: 450px;
        }}
        .chart-container.full-width {{
            grid-column: 1 / -1;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background-color: {COLORS["background"]};
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 1.5rem;
            font-weight: 600;
            color: {COLORS["speed"]};
        }}
        .metric-label {{
            font-size: 0.8rem;
            color: {COLORS["text_secondary"]};
            margin-top: 4px;
        }}
        .section-title {{
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: {COLORS["text"]};
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid {COLORS["grid"]};
        }}
        th {{
            background-color: {COLORS["background"]};
            color: {COLORS["text_secondary"]};
            font-weight: 500;
        }}
        tr:hover {{
            background-color: rgba(255,255,255,0.03);
        }}
        .table-container {{
            background-color: {COLORS["background"]};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            overflow-x: auto;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .badge-yes {{
            background-color: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }}
        .badge-no {{
            background-color: rgba(107, 114, 128, 0.2);
            color: #9ca3af;
        }}
        .zone-label {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            min-width: 32px;
            text-align: center;
        }}
        .brake-label {{
            background-color: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }}
        .corner-label {{
            background-color: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
        }}
        @media (max-width: 1200px) {{
            .grid-2col, .grid-3col {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Lap {lap_number} Analysis</h1>
            <div class="header-meta">
                <span><strong>Track:</strong> {track_display}</span>
                <span><strong>Car:</strong> {car_name}</span>
                <span><strong>Lap Time:</strong> {lap_time}</span>
                <span><strong>Telemetry Points:</strong> {telemetry.frame_count}</span>
            </div>
        </div>

        {metrics_html}

        <div class="grid-2col">
            <div class="chart-container tall">
                {track_map_html}
            </div>
            <div class="chart-container tall">
                {friction_circle_html}
            </div>
        </div>

        <div class="chart-container full-width" style="margin-bottom: 20px;">
            {speed_chart_html}
        </div>

        <div class="chart-container full-width" style="margin-bottom: 20px;">
            {inputs_chart_html}
        </div>

        <div class="grid-2col">
            <div class="chart-container">
                {steering_chart_html}
            </div>
            <div class="chart-container">
                {gforce_chart_html}
            </div>
        </div>

        {braking_table_html}

        {corners_table_html}
    </div>
</body>
</html>
"""
    return html


def _format_lap_time(seconds: float | None) -> str:
    """Format lap time in M:SS.mmm format."""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"


def _build_metrics_summary_html(metrics: MetricsProtocol) -> str:
    """Build the metrics summary cards HTML."""
    max_speed_kmh = metrics.max_speed * MS_TO_KMH
    min_speed_kmh = metrics.min_speed * MS_TO_KMH
    avg_corner_speed_kmh = metrics.average_corner_speed * MS_TO_KMH

    return f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{max_speed_kmh:.1f}</div>
                <div class="metric-label">Max Speed (km/h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{min_speed_kmh:.1f}</div>
                <div class="metric-label">Min Speed (km/h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_corner_speed_kmh:.1f}</div>
                <div class="metric-label">Avg Corner Speed (km/h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.total_braking_zones}</div>
                <div class="metric-label">Braking Zones</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.total_corners}</div>
                <div class="metric-label">Corners</div>
            </div>
        </div>
    """


def _build_braking_table_html(metrics: MetricsProtocol) -> str:
    """Build the braking zones table HTML."""
    if not metrics.braking_zones:
        return ""

    rows = ""
    for i, bz in enumerate(metrics.braking_zones, 1):
        entry_speed_kmh = bz.braking_point_speed * MS_TO_KMH
        min_speed_kmh = bz.minimum_speed * MS_TO_KMH
        trail_badge = (
            '<span class="badge badge-yes">Yes</span>'
            if bz.has_trail_braking
            else '<span class="badge badge-no">No</span>'
        )
        rows += f"""
            <tr>
                <td><span class="zone-label brake-label">B{i}</span></td>
                <td>{bz.braking_point_distance:.0f}m</td>
                <td>{entry_speed_kmh:.1f}</td>
                <td>{min_speed_kmh:.1f}</td>
                <td>{bz.max_brake_pressure * 100:.0f}%</td>
                <td>{bz.braking_duration:.2f}s</td>
                <td>{bz.braking_efficiency:.1f}%</td>
                <td>{trail_badge}</td>
            </tr>
        """

    return f"""
        <div class="table-container">
            <h3 class="section-title">Braking Zones</h3>
            <table>
                <thead>
                    <tr>
                        <th>Zone</th>
                        <th>Distance</th>
                        <th>Entry (km/h)</th>
                        <th>Min (km/h)</th>
                        <th>Max Pressure</th>
                        <th>Duration</th>
                        <th>Efficiency</th>
                        <th>Trail Brake</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    """


def _build_corners_table_html(metrics: MetricsProtocol) -> str:
    """Build the corners table HTML."""
    if not metrics.corners:
        return ""

    rows = ""
    for i, corner in enumerate(metrics.corners, 1):
        turn_in_kmh = corner.turn_in_speed * MS_TO_KMH
        apex_kmh = corner.apex_speed * MS_TO_KMH
        exit_kmh = corner.exit_speed * MS_TO_KMH
        rows += f"""
            <tr>
                <td><span class="zone-label corner-label">C{i}</span></td>
                <td>{corner.turn_in_distance:.0f}m</td>
                <td>{turn_in_kmh:.1f}</td>
                <td>{apex_kmh:.1f}</td>
                <td>{exit_kmh:.1f}</td>
                <td>{corner.max_lateral_g:.2f}G</td>
                <td>{corner.time_in_corner:.2f}s</td>
                <td>{corner.max_steering_angle * RAD_TO_DEG:.1f}°</td>
            </tr>
        """

    return f"""
        <div class="table-container">
            <h3 class="section-title">Corners</h3>
            <table>
                <thead>
                    <tr>
                        <th>Corner</th>
                        <th>Turn-in</th>
                        <th>Entry (km/h)</th>
                        <th>Apex (km/h)</th>
                        <th>Exit (km/h)</th>
                        <th>Max Lat G</th>
                        <th>Time</th>
                        <th>Max Steering</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    """
