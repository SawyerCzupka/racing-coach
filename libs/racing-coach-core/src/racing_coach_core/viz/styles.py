"""Styling constants for lap visualization charts."""

# Dark theme colors (matching the web app)
COLORS = {
    "background": "#1f2937",  # gray-800
    "paper": "#111827",  # gray-900
    "text": "#f9fafb",  # gray-50
    "text_secondary": "#9ca3af",  # gray-400
    "grid": "#374151",  # gray-700
    "throttle": "#22c55e",  # green-500
    "brake": "#ef4444",  # red-500
    "speed": "#3b82f6",  # blue-500
    "steering": "#a855f7",  # purple-500
    "lateral_g": "#a855f7",  # purple-500
    "longitudinal_g": "#f97316",  # orange-500
    "braking_zone": "rgba(239, 68, 68, 0.2)",  # red with transparency
    "corner_region": "rgba(168, 85, 247, 0.15)",  # purple with transparency
    "brake_point_marker": "#ef4444",  # red-500
    "apex_marker": "#3b82f6",  # blue-500
    "turn_in_marker": "#22c55e",  # green-500
    "exit_marker": "#f97316",  # orange-500
}

# Speed colorscale for track map (low to high speed)
SPEED_COLORSCALE = [
    [0.0, "#ef4444"],  # red - slow
    [0.25, "#f97316"],  # orange
    [0.5, "#eab308"],  # yellow
    [0.75, "#22c55e"],  # green
    [1.0, "#3b82f6"],  # blue - fast
]

# Common layout settings
LAYOUT_DEFAULTS = {
    "paper_bgcolor": COLORS["paper"],
    "plot_bgcolor": COLORS["background"],
    "font": {"color": COLORS["text"], "family": "system-ui, sans-serif"},
    "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
    "showlegend": True,
    "legend": {
        "bgcolor": "rgba(0,0,0,0)",
        "font": {"color": COLORS["text"]},
    },
}

# Axis styling
AXIS_DEFAULTS = {
    "gridcolor": COLORS["grid"],
    "zerolinecolor": COLORS["grid"],
    "tickfont": {"color": COLORS["text_secondary"]},
    "title": {"font": {"color": COLORS["text"]}},
}

# Marker sizes
MARKER_SIZES = {
    "brake_point": 12,
    "apex": 10,
    "turn_in": 8,
    "exit": 8,
}


def get_chart_layout(title: str, **kwargs) -> dict:
    """Get a layout dict with defaults applied."""
    layout = {**LAYOUT_DEFAULTS, "title": {"text": title, "font": {"color": COLORS["text"]}}}
    layout.update(kwargs)
    return layout


def get_xaxis(title: str = "", **kwargs) -> dict:
    """Get x-axis settings with defaults."""
    axis = {**AXIS_DEFAULTS}
    if title:
        axis["title"] = {"text": title, "font": {"color": COLORS["text"]}}
    axis.update(kwargs)
    return axis


def get_yaxis(title: str = "", **kwargs) -> dict:
    """Get y-axis settings with defaults."""
    axis = {**AXIS_DEFAULTS}
    if title:
        axis["title"] = {"text": title, "font": {"color": COLORS["text"]}}
    axis.update(kwargs)
    return axis
