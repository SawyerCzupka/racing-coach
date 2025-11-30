"""CLI entry point for lap visualization.

Usage:
    # List all sessions
    python -m racing_coach_core.viz --server http://localhost:8000 --list-sessions

    # List laps in a session
    python -m racing_coach_core.viz --server http://localhost:8000 --list-laps SESSION_ID

    # Generate visualization for a lap
    python -m racing_coach_core.viz --server http://localhost:8000 --lap LAP_ID

    # Options
    --output FILE    # Save to specific file (default: lap_<LAP_ID>.html)
    --no-open        # Don't auto-open in browser
"""

import argparse
import sys
import webbrowser
from pathlib import Path
from uuid import UUID

import httpx
from racing_coach_server_client import Client
from racing_coach_server_client.api.metrics import get_lap_metrics_api_v1_metrics_lap_lap_id_get
from racing_coach_server_client.api.sessions import get_lap_telemetry, get_session_detail, get_sessions_list
from racing_coach_server_client.models import (
    LapMetricsResponse,
    LapTelemetryResponse,
    SessionDetailResponse,
    SessionListResponse,
)

from .report import generate_lap_report


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize racing lap telemetry and metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--server",
        "-s",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)",
    )

    # Mutually exclusive action group
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all available sessions",
    )
    action_group.add_argument(
        "--list-laps",
        metavar="SESSION_ID",
        help="List laps in a session",
    )
    action_group.add_argument(
        "--lap",
        metavar="LAP_ID",
        help="Generate visualization for a specific lap",
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Output file path (default: lap_<LAP_ID>.html)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open the report in browser",
    )

    args = parser.parse_args()

    try:
        client = Client(base_url=args.server)

        if args.list_sessions:
            return list_sessions(client)
        elif args.list_laps:
            return list_laps(client, args.list_laps)
        elif args.lap:
            return visualize_lap(client, args.lap, args.output, not args.no_open)

    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 1
    except httpx.RequestError as e:
        print(f"Request error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130

    return 0


def list_sessions(client: Client) -> int:
    """List all sessions."""
    print("Fetching sessions...")
    response = get_sessions_list.sync(client=client)

    if not isinstance(response, SessionListResponse) or not response.sessions:
        print("No sessions found.")
        return 0

    print(f"\nFound {response.total} session(s):\n")
    print(f"{'ID':<38} {'Track':<30} {'Car':<25} {'Laps':<6} {'Date'}")
    print("-" * 120)

    for session in response.sessions:
        track = session.track_name
        if session.track_config_name:
            track = f"{track} ({session.track_config_name})"
        if len(track) > 28:
            track = track[:25] + "..."

        car = session.car_name
        if len(car) > 23:
            car = car[:20] + "..."

        date_str = session.created_at.strftime("%Y-%m-%d %H:%M")

        print(f"{session.session_id:<38} {track:<30} {car:<25} {session.lap_count:<6} {date_str}")

    return 0


def list_laps(client: Client, session_id: str) -> int:
    """List laps in a session."""
    print(f"Fetching session {session_id}...")
    session = get_session_detail.sync(UUID(session_id), client=client)

    if not isinstance(session, SessionDetailResponse):
        print(f"Error: Could not fetch session {session_id}", file=sys.stderr)
        return 1

    track = session.track_name
    if session.track_config_name:
        track = f"{track} - {session.track_config_name}"

    print(f"\nSession: {track}")
    print(f"Car: {session.car_name}")
    print(f"\nFound {len(session.laps)} lap(s):\n")

    if not session.laps:
        print("No laps in this session.")
        return 0

    print(f"{'#':<4} {'Lap ID':<38} {'Time':<12} {'Valid':<7} {'Metrics'}")
    print("-" * 80)

    for lap in session.laps:
        lap_time = format_lap_time(lap.lap_time) if lap.lap_time else "N/A"
        valid = "Yes" if lap.is_valid else "No"
        metrics = "Yes" if lap.has_metrics else "No"

        print(f"{lap.lap_number:<4} {lap.lap_id:<38} {lap_time:<12} {valid:<7} {metrics}")

    return 0


def visualize_lap(
    client: Client,
    lap_id: str,
    output_path: str | None,
    open_browser: bool,
) -> int:
    """Generate visualization for a lap."""
    print(f"Fetching data for lap {lap_id}...")

    # First, we need to find the session for this lap
    # We'll get all sessions and find which one contains this lap
    sessions = get_sessions_list.sync(client=client)
    if not isinstance(sessions, SessionListResponse):
        print("Error: Could not fetch sessions", file=sys.stderr)
        return 1

    session_id: str | None = None
    session_detail: SessionDetailResponse | None = None

    for session_summary in sessions.sessions:
        session = get_session_detail.sync(UUID(session_summary.session_id), client=client)
        if not isinstance(session, SessionDetailResponse):
            continue
        for lap in session.laps:
            if lap.lap_id == lap_id:
                session_id = session_summary.session_id
                session_detail = session
                break
        if session_id:
            break

    if not session_id or not session_detail:
        print(f"Error: Lap {lap_id} not found in any session", file=sys.stderr)
        return 1

    print(f"  Found in session: {session_detail.track_name}")

    # Fetch telemetry
    print("  Fetching telemetry...")
    telemetry = get_lap_telemetry.sync(UUID(session_id), UUID(lap_id), client=client)
    if not isinstance(telemetry, LapTelemetryResponse):
        print("Error: Could not fetch telemetry", file=sys.stderr)
        return 1
    print(f"  Got {telemetry.frame_count} telemetry frames")

    # Try to fetch metrics (may not exist)
    metrics: LapMetricsResponse | None = None
    print("  Fetching metrics...")
    metrics_response = get_lap_metrics_api_v1_metrics_lap_lap_id_get.sync(lap_id, client=client)
    if isinstance(metrics_response, LapMetricsResponse):
        metrics = metrics_response
        print(f"  Got {metrics.total_braking_zones} braking zones, {metrics.total_corners} corners")
    else:
        print("  No metrics available for this lap")

    # Generate report
    print("  Generating visualization...")
    html = generate_lap_report(telemetry, metrics, session_detail)

    # Determine output path
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = Path(f"lap_{lap_id[:8]}.html")

    # Write file
    out_file.write_text(html)
    print(f"\nReport saved to: {out_file.absolute()}")

    # Open in browser
    if open_browser:
        print("Opening in browser...")
        webbrowser.open(f"file://{out_file.absolute()}")

    return 0


def format_lap_time(seconds: float | None) -> str:
    """Format lap time as M:SS.mmm."""
    if seconds is None:
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"


if __name__ == "__main__":
    sys.exit(main())
