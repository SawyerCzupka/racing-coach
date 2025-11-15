"""Tests for TelemetryCollector."""

import asyncio
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_core.events.base import Event, EventBus, Handler, SystemEvents
from racing_coach_core.models.events import TelemetryAndSession
from racing_coach_core.models.telemetry import SessionFrame

from tests.conftest import EventCollector


@pytest.mark.unit
class TestTelemetryCollectorUnit:
    """Unit tests for TelemetryCollector with mocked source."""

    def test_initialization(self, event_bus: EventBus, mock_telemetry_source: MagicMock) -> None:
        """Test TelemetryCollector initializes correctly."""
        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)

        assert collector.event_bus is event_bus
        assert collector.source is mock_telemetry_source
        assert collector.current_session is None
        assert not collector._running

    def test_collect_session_frame(
        self, event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test collecting session metadata."""
        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)

        session: SessionFrame = collector.collect_session_frame()

        assert session is not None
        assert session.track_name is not None
        assert session.car_name is not None
        mock_telemetry_source.freeze_var_buffer_latest.assert_called_once()

    def test_collect_and_publish_telemetry_frame_without_session(
        self, event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test that collect_and_publish raises error without session."""
        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)

        with pytest.raises(RuntimeError, match="no session frame available"):
            collector.collect_and_publish_telemetry_frame()

    async def test_collect_and_publish_telemetry_frame(
        self,
        running_event_bus: EventBus,
        mock_telemetry_source: MagicMock,
        event_collector: EventCollector,
    ) -> None:
        """Test collecting and publishing a telemetry frame."""
        # Register collector
        handler: Handler[TelemetryAndSession] = Handler(
            type=SystemEvents.TELEMETRY_FRAME,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Create collector and set session
        collector: TelemetryCollector = TelemetryCollector(running_event_bus, mock_telemetry_source)
        collector.current_session = collector.collect_session_frame()

        # Collect and publish
        collector.collect_and_publish_telemetry_frame()

        # Wait for event to be processed
        events: list[Event[TelemetryAndSession]] = await event_collector.wait_for_event(
            SystemEvents.TELEMETRY_FRAME, timeout=2.0, count=1
        )

        assert len(events) == 1
        event: Event[TelemetryAndSession] = events[0]
        assert event.type == SystemEvents.TELEMETRY_FRAME
        assert isinstance(event.data, TelemetryAndSession)
        assert event.data.TelemetryFrame is not None
        assert event.data.SessionFrame is not None

    def test_start_when_already_running(
        self, event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test that starting an already running collector logs warning."""
        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)
        collector._running = True

        with patch("racing_coach_client.collectors.iracing.logger") as mock_logger:
            collector.start()
            mock_logger.warning.assert_called_once()

    def test_stop(self, event_bus: EventBus, mock_telemetry_source: MagicMock) -> None:
        """Test stopping the collector."""
        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)
        collector._running = True

        collector.stop()

        assert not collector._running
        mock_telemetry_source.shutdown.assert_called_once()

    def test_collection_loop_handles_startup_failure(
        self, event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test that collection loop handles source startup failure."""
        mock_telemetry_source.startup.return_value = False

        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)
        collector._collection_loop()

        assert not collector._running
        mock_telemetry_source.startup.assert_called_once()

    def test_collection_loop_handles_session_collection_failure(
        self, event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test that collection loop handles session collection failure."""
        mock_telemetry_source.startup.return_value = True
        mock_telemetry_source.__getitem__.side_effect = KeyError("Missing data")

        collector: TelemetryCollector = TelemetryCollector(event_bus, mock_telemetry_source)
        collector._collection_loop()

        assert not collector._running
        mock_telemetry_source.shutdown.assert_called_once()


@pytest.mark.integration
class TestTelemetryCollectorIntegration:
    """Integration tests for TelemetryCollector with mocked source."""

    async def test_collector_thread_lifecycle(
        self, running_event_bus: EventBus, mock_telemetry_source: MagicMock
    ) -> None:
        """Test starting and stopping the collector thread."""
        mock_telemetry_source.startup.return_value = True
        mock_telemetry_source.is_connected.return_value = False  # Exit loop immediately

        collector: TelemetryCollector = TelemetryCollector(running_event_bus, mock_telemetry_source)
        collector.start()

        # Give thread time to start
        await asyncio.sleep(0.2)

        # Stop collector
        collector.stop()

        # Give thread time to stop
        await asyncio.sleep(0.2)

        assert not collector._running

    async def test_collector_publishes_telemetry_events(
        self,
        running_event_bus: EventBus,
        mock_telemetry_source: MagicMock,
        event_collector: EventCollector,
    ) -> None:
        """Test that collector publishes telemetry events at expected rate."""
        # Configure mock to disconnect after a few frames
        call_count: int = 0

        def is_connected_side_effect() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count <= 5  # Return True for first 5 calls

        mock_telemetry_source.startup.return_value = True
        mock_telemetry_source.is_connected.side_effect = is_connected_side_effect

        # Register event collector
        handler: Handler[TelemetryAndSession] = Handler(
            type=SystemEvents.TELEMETRY_FRAME,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Start collector
        collector: TelemetryCollector = TelemetryCollector(running_event_bus, mock_telemetry_source)
        collector.start()

        # Wait for events to be collected
        await asyncio.sleep(1.0)

        # Stop collector
        collector.stop()
        await asyncio.sleep(0.2)

        # Verify events were published
        events: list[Event[TelemetryAndSession]] = event_collector.get_events_of_type(
            SystemEvents.TELEMETRY_FRAME
        )
        assert len(events) > 0


@pytest.mark.ibt
@pytest.mark.integration
@pytest.mark.slow
class TestTelemetryCollectorWithRealIBT:
    """Integration tests for TelemetryCollector with real IBT file."""

    async def test_collect_from_ibt_file(
        self, running_event_bus: EventBus, ibt_file_path: Path, event_collector: EventCollector
    ) -> None:
        """Test collecting telemetry from a real IBT file."""
        from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource

        # Create replay source
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path,
            speed_multiplier=10.0,  # Speed up for testing
            loop=False,
        )

        # Register event collector
        handler: Handler[TelemetryAndSession] = Handler(
            type=SystemEvents.TELEMETRY_FRAME,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(running_event_bus, source)
        collector.start()

        # Wait for some events to be collected
        try:
            events: list[Event[TelemetryAndSession]] = await event_collector.wait_for_event(
                SystemEvents.TELEMETRY_FRAME, timeout=20.0, count=10
            )
            assert len(events) >= 10

            # Verify event data
            for event in events:
                assert event.type == SystemEvents.TELEMETRY_FRAME
                assert isinstance(event.data, TelemetryAndSession)
                assert event.data.TelemetryFrame is not None
                assert event.data.SessionFrame is not None

                # Verify telemetry data has reasonable values
                telem: Any = event.data.TelemetryFrame
                assert telem.speed >= 0
                assert telem.rpm >= 0
                assert 0 <= telem.throttle <= 1
                assert 0 <= telem.brake <= 1

        finally:
            collector.stop()
            await asyncio.sleep(0.2)

    async def test_session_frame_consistency(
        self, running_event_bus: EventBus, ibt_file_path: Path, event_collector: EventCollector
    ) -> None:
        """Test that session frame remains consistent across telemetry frames."""
        from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource

        # Create replay source
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path,
            speed_multiplier=10.0,
            loop=False,
        )

        # Register event collector
        handler: Handler[TelemetryAndSession] = Handler(
            type=SystemEvents.TELEMETRY_FRAME,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(running_event_bus, source)
        collector.start()

        try:
            # Wait for multiple events
            events: list[Event[TelemetryAndSession]] = await event_collector.wait_for_event(
                SystemEvents.TELEMETRY_FRAME, timeout=10.0, count=5
            )

            # Verify all events have the same session frame
            session_frames: list[SessionFrame] = [event.data.SessionFrame for event in events]
            first_session: SessionFrame = session_frames[0]

            for session in session_frames[1:]:
                assert session.session_id == first_session.session_id
                assert session.track_id == first_session.track_id
                assert session.track_name == first_session.track_name
                assert session.car_id == first_session.car_id

        finally:
            collector.stop()
            await asyncio.sleep(0.2)
