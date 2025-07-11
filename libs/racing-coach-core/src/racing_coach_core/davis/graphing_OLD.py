import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from racing_coach_core.algs.braking import BrakingEvent
from racing_coach_core.models import LapTelemetry


def make_lap_telemetry_plot(lap: LapTelemetry) -> go.Figure:
    df = pd.DataFrame([frame.model_dump() for frame in lap.frames])

    df["time_elapsed"] = df["session_time"] - df["session_time"].iloc[0]

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02)

    fig.add_trace(
        go.Scatter(
            x=df["time_elapsed"],
            y=df["throttle"],
            name="Throttle",
            line=dict(color="green"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_elapsed"], y=df["brake"], name="Brake", line=dict(color="red")
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_elapsed"],
            y=df["steering_angle"],
            name="Steering",
            line=dict(color="blue"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time_elapsed"],
            y=df["speed"] * 3.6,
            name="Speed (km/h)",
            line=dict(color="purple"),
        ),
        row=3,
        col=1,
    )
    fig.update_layout(
        height=800,
        title_text=f"Lap {df['lap_number'].iloc[0]} Telemetry",
        showlegend=True,
        hovermode="x unified",
    )

    # Update axes labels
    fig.update_yaxes(title_text="Input %", range=[0, 1], row=1, col=1)
    fig.update_yaxes(title_text="Angle (rad)", row=2, col=1)
    fig.update_yaxes(title_text="Speed (km/h)", row=3, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)

    return fig


def make_lap_telemetry_plot_with_braking(
    lap: LapTelemetry, braking_events: list[BrakingEvent]
) -> go.Figure:
    """
    Creates a telemetry plot with braking events highlighted.

    Args:
        lap: LapTelemetry object containing frame data
        braking_events: List of BrakingEvent objects to visualize

    Returns:
        Plotly figure object with telemetry and braking events
    """
    # Get base telemetry plot
    fig = make_lap_telemetry_plot(lap)

    # Create DataFrame for time reference
    df = pd.DataFrame([frame.model_dump() for frame in lap.frames])
    df["time_elapsed"] = df["session_time"] - df["session_time"].iloc[0]

    # Add braking event visualization
    for i, event in enumerate(braking_events, 1):
        # Get time values for start and end frames
        start_time = df.iloc[event.start_frame]["time_elapsed"]
        end_time = df.iloc[event.end_frame]["time_elapsed"]

        # Add shaded region for braking event across all subplots
        for row in range(1, 4):  # 3 subplots
            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="rgba(255, 0, 0, 0.1)",
                layer="below",
                line_width=0,
                row=row,
                col=1,
            )

        # Add annotation for braking event details
        fig.add_annotation(
            x=start_time,
            y=1,
            text=f"Braking {i}<br>Entry: {event.entry_speed * 3.6:.1f} km/h<br>Min: {event.minimum_speed * 3.6:.1f} km/h",
            showarrow=True,
            arrowhead=1,
            row=3,
            col=1,
            yanchor="bottom",
            bgcolor="rgba(255, 255, 255, 0.8)",
        )

    # Update title to reflect addition of braking events
    fig.update_layout(
        title_text=f"Lap {df['lap_number'].iloc[0]} Telemetry with Braking Events"
    )

    return fig
