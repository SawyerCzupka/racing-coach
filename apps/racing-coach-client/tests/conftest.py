"""Pytest configuration and shared fixtures for racing-coach-client tests."""

import asyncio
import os
import threading
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_factoryboy import register
from racing_coach_core.events.base import (
    Event,
    EventBus,
    EventType,
    Handler,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.models.events import LapAndSession, TelemetryAndSession
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame

from tests.factories import (
    LapAndSessionFactory,
    LapTelemetryFactory,
    SessionFrameFactory,
    TelemetryAndSessionFactory,
    TelemetryFrameFactory,
)

# Register factories to create pytest fixtures automatically
register(TelemetryFrameFactory)
register(SessionFrameFactory)
register(LapTelemetryFactory)
register(TelemetryAndSessionFactory)
register(LapAndSessionFactory)


# ============================================================================
# IBT File Configuration
# ============================================================================


@pytest.fixture
def ibt_file_path() -> Path:
    """
    Get the path to an IBT file for testing.

    Reads from REPLAY_FILE_PATH environment variable.
    If not set, tests requiring this fixture will be skipped.

    Returns:
        Path to IBT file if configured.

    Raises:
        pytest.skip: If REPLAY_FILE_PATH is not set or file doesn't exist.
    """
    file_path: str | None = os.getenv("REPLAY_FILE_PATH")
    if not file_path:
        pytest.skip("REPLAY_FILE_PATH not set - skipping IBT file tests")

    path: Path = Path(file_path)
    if not path.exists():
        pytest.skip(f"IBT file not found at {file_path}")

    return path


# ============================================================================
# Event Bus Fixtures
# ============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh EventBus instance for testing."""
    return EventBus(max_queue_size=100, max_workers=2)


@pytest.fixture
async def running_event_bus() -> AsyncGenerator[EventBus, None]:
    """Create and start an EventBus instance for integration testing."""
    bus: EventBus = EventBus(max_queue_size=100, max_workers=2)
    bus.start()
    # Give the event bus time to start up
    await asyncio.sleep(0.1)
    yield bus
    bus.stop()
    # Give the event bus time to shut down
    await asyncio.sleep(0.1)


# ============================================================================
# Event Collection Utilities
# ============================================================================


class EventCollector:
    """
    Utility class for collecting events during tests.

    Provides methods to wait for specific events and access collected events.
    """

    def __init__(self) -> None:
        self.events: list[Event[Any]] = []
        self._lock: threading.Lock = threading.Lock()

    def collect(self, context: HandlerContext[Any]) -> None:
        """Handler function to collect events (sync handler for thread pool execution)."""
        with self._lock:
            self.events.append(context.event)

    def get_events_of_type[T](self, event_type: EventType[T]) -> list[Event[T]]:
        """Get all collected events of a specific type."""
        return [e for e in self.events if e.type == event_type]  # type: ignore[return-value]

    async def wait_for_event[T](
        self,
        event_type: EventType[T],
        timeout: float = 5.0,
        count: int = 1,
    ) -> list[Event[T]]:
        """
        Wait for a specific number of events of a given type.

        Args:
            event_type: The type of event to wait for
            timeout: Maximum time to wait in seconds
            count: Number of events to wait for

        Returns:
            List of collected events of the specified type

        Raises:
            TimeoutError: If events are not received within timeout
        """
        start_time: float = asyncio.get_event_loop().time()
        while True:
            events: list[Event[T]] = self.get_events_of_type(event_type)
            if len(events) >= count:
                return events[:count]

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(
                    f"Timeout waiting for {count} {event_type.name} events. "
                    f"Got {len(events)} events."
                )

            await asyncio.sleep(0.01)

    def clear(self) -> None:
        """Clear all collected events."""
        self.events.clear()


@pytest.fixture
def event_collector() -> EventCollector:
    """Create an EventCollector for capturing events during tests."""
    return EventCollector()


@pytest.fixture
def telemetry_frame_collector(
    event_collector: EventCollector, running_event_bus: EventBus
) -> EventCollector:
    """
    Create an event collector that's registered to collect TELEMETRY_FRAME events.

    This fixture requires a running event bus.
    """
    handler: Handler[TelemetryAndSession] = Handler(
        type=SystemEvents.TELEMETRY_FRAME,
        fn=event_collector.collect,
    )
    running_event_bus.register_handlers([handler])
    return event_collector


@pytest.fixture
def lap_sequence_collector(
    event_collector: EventCollector, running_event_bus: EventBus
) -> EventCollector:
    """
    Create an event collector that's registered to collect LAP_TELEMETRY_SEQUENCE events.

    This fixture requires a running event bus.
    """
    handler: Handler[LapAndSession] = Handler(
        type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
        fn=event_collector.collect,
    )
    running_event_bus.register_handlers([handler])
    return event_collector


# ============================================================================
# Mock Telemetry Source
# ============================================================================


@pytest.fixture
def mock_telemetry_source(
    telemetry_frame_factory: Callable[..., TelemetryFrame],
    session_frame_factory: Callable[..., SessionFrame],
) -> MagicMock:
    """
    Create a mock telemetry source that returns realistic test data.

    The mock implements the TelemetryDataSource protocol.
    """
    mock: MagicMock = MagicMock()

    # Create sample data
    telemetry_data: TelemetryFrame = telemetry_frame_factory.build()  # type: ignore[attr-defined]
    session_data: SessionFrame = session_frame_factory.build()  # type: ignore[attr-defined]

    # Configure the mock to return data via __getitem__
    def getitem_side_effect(key: str) -> Any:
        # Map iRacing field names to our model field names
        field_mapping: dict[str, Any] = {
            "SessionTime": telemetry_data.session_time,
            "Lap": telemetry_data.lap_number,
            "LapDistPct": telemetry_data.lap_distance_pct,
            "LapDist": telemetry_data.lap_distance,
            "LapCurrentLapTime": telemetry_data.current_lap_time,
            "LapLastLapTime": telemetry_data.last_lap_time,
            "LapBestLapTime": telemetry_data.best_lap_time,
            "Speed": telemetry_data.speed,
            "RPM": telemetry_data.rpm,
            "Gear": telemetry_data.gear,
            "Throttle": telemetry_data.throttle,
            "Brake": telemetry_data.brake,
            "Clutch": telemetry_data.clutch,
            "SteeringWheelAngle": telemetry_data.steering_angle,
            "LatAccel": telemetry_data.lateral_acceleration,
            "LongAccel": telemetry_data.longitudinal_acceleration,
            "VertAccel": telemetry_data.vertical_acceleration,
            "YawRate": telemetry_data.yaw_rate,
            "RollRate": telemetry_data.roll_rate,
            "PitchRate": telemetry_data.pitch_rate,
            "VelocityX": telemetry_data.position_x,
            "VelocityY": telemetry_data.position_y,
            "VelocityZ": telemetry_data.position_z,
            "Yaw": telemetry_data.yaw,
            "Pitch": telemetry_data.pitch,
            "Roll": telemetry_data.roll,
            "TrackTempCrew": telemetry_data.track_temp,
            "TrackWetness": telemetry_data.track_wetness,
            "AirTemp": telemetry_data.air_temp,
            "SessionFlags": telemetry_data.session_flags,
            "PlayerTrackSurface": telemetry_data.track_surface,
            "OnPitRoad": telemetry_data.on_pit_road,
            # Tire temps
            "LFtempCL": telemetry_data.tire_temps["LF"]["left"],
            "LFtempCM": telemetry_data.tire_temps["LF"]["middle"],
            "LFtempCR": telemetry_data.tire_temps["LF"]["right"],
            "RFtempCL": telemetry_data.tire_temps["RF"]["left"],
            "RFtempCM": telemetry_data.tire_temps["RF"]["middle"],
            "RFtempCR": telemetry_data.tire_temps["RF"]["right"],
            "LRtempCL": telemetry_data.tire_temps["LR"]["left"],
            "LRtempCM": telemetry_data.tire_temps["LR"]["middle"],
            "LRtempCR": telemetry_data.tire_temps["LR"]["right"],
            "RRtempCL": telemetry_data.tire_temps["RR"]["left"],
            "RRtempCM": telemetry_data.tire_temps["RR"]["middle"],
            "RRtempCR": telemetry_data.tire_temps["RR"]["right"],
            # Tire wear
            "LFwearL": telemetry_data.tire_wear["LF"]["left"],
            "LFwearM": telemetry_data.tire_wear["LF"]["middle"],
            "LFwearR": telemetry_data.tire_wear["LF"]["right"],
            "RFwearL": telemetry_data.tire_wear["RF"]["left"],
            "RFwearM": telemetry_data.tire_wear["RF"]["middle"],
            "RFwearR": telemetry_data.tire_wear["RF"]["right"],
            "LRwearL": telemetry_data.tire_wear["LR"]["left"],
            "LRwearM": telemetry_data.tire_wear["LR"]["middle"],
            "LRwearR": telemetry_data.tire_wear["LR"]["right"],
            "RRwearL": telemetry_data.tire_wear["RR"]["left"],
            "RRwearM": telemetry_data.tire_wear["RR"]["middle"],
            "RRwearR": telemetry_data.tire_wear["RR"]["right"],
            # Brake pressure
            "LFbrakeLinePress": telemetry_data.brake_line_pressure["LF"],
            "RFbrakeLinePress": telemetry_data.brake_line_pressure["RF"],
            "LRbrakeLinePress": telemetry_data.brake_line_pressure["LR"],
            "RRbrakeLinePress": telemetry_data.brake_line_pressure["RR"],
        }

        # Check telemetry fields first
        if key in field_mapping:
            return field_mapping[key]

        # Handle session fields
        if key == "WeekendInfo":
            return {
                "TrackID": session_data.track_id,
                "TrackName": session_data.track_name,
                "TrackConfigName": session_data.track_config_name,
                "TrackType": session_data.track_type,
                "SeriesID": session_data.series_id,
            }
        elif key == "DriverInfo":
            return {
                "DriverCarIdx": 0,
                "Drivers": [
                    {
                        "CarID": session_data.car_id,
                        "CarScreenName": session_data.car_name,
                        "CarClassID": session_data.car_class_id,
                    }
                ],
            }

        raise KeyError(f"Unknown telemetry key: {key}")

    mock.__getitem__ = MagicMock(side_effect=getitem_side_effect)
    return mock
