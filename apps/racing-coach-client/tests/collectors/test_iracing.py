"""Tests for TelemetryCollector."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_core.events.base import Event, EventBus, Handler, SystemEvents
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.schemas.events import SessionEnd, SessionStart, TelemetryAndSessionId
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame

from tests.conftest import EventCollector


@pytest.mark.unit
class TestTelemetryCollectorUnit:
    """Unit tests for TelemetryCollector with mocked source."""

    def test_initialization(
        self,
        event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test TelemetryCollector initializes correctly."""
        collector: TelemetryCollector = TelemetryCollector(
            event_bus, mock_telemetry_source, session_registry
        )

        assert collector.event_bus is event_bus
        assert collector.source is mock_telemetry_source
        assert collector.session_registry is session_registry
        assert collector.current_session is None
        assert not collector._running

    def test_start_when_already_running(
        self,
        event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test that starting an already running collector logs warning."""
        collector: TelemetryCollector = TelemetryCollector(
            event_bus, mock_telemetry_source, session_registry
        )
        collector._running = True

        with patch("racing_coach_client.collectors.iracing.logger") as mock_logger:
            collector.start()
            mock_logger.warning.assert_called_once()

    def test_stop(
        self,
        event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test stopping the collector."""
        collector: TelemetryCollector = TelemetryCollector(
            event_bus, mock_telemetry_source, session_registry
        )
        collector._running = True

        collector.stop()

        assert not collector._running
        mock_telemetry_source.stop.assert_called_once()

    def test_collection_loop_handles_startup_failure(
        self,
        event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test that collection loop handles source startup failure."""
        mock_telemetry_source.start.return_value = False

        collector: TelemetryCollector = TelemetryCollector(
            event_bus, mock_telemetry_source, session_registry
        )
        collector._collection_loop()

        assert not collector._running
        mock_telemetry_source.start.assert_called_once()

    def test_collection_loop_handles_session_collection_failure(
        self,
        event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test that collection loop handles session collection failure."""
        mock_telemetry_source.start.return_value = True
        mock_telemetry_source.collect_session_frame.side_effect = KeyError("Missing data")

        collector: TelemetryCollector = TelemetryCollector(
            event_bus, mock_telemetry_source, session_registry
        )
        collector._collection_loop()

        assert not collector._running
        mock_telemetry_source.stop.assert_called()


@pytest.mark.integration
class TestTelemetryCollectorIntegration:
    """Integration tests for TelemetryCollector with mocked source."""

    async def test_collector_thread_lifecycle(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
    ) -> None:
        """Test starting and stopping the collector thread."""
        mock_telemetry_source.start.return_value = True
        # Configure is_connected to return False to exit loop immediately
        type(mock_telemetry_source).is_connected = PropertyMock(return_value=False)

        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, mock_telemetry_source, session_registry
        )
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
        session_registry: SessionRegistry,
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

        mock_telemetry_source.start.return_value = True
        type(mock_telemetry_source).is_connected = PropertyMock(
            side_effect=is_connected_side_effect
        )

        # Register event collector
        handler: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, mock_telemetry_source, session_registry
        )
        collector.start()

        # Wait for events to be collected
        await asyncio.sleep(1.0)

        # Stop collector
        collector.stop()
        await asyncio.sleep(0.2)

        # Verify events were published
        events: list[Event[TelemetryAndSessionId]] = event_collector.get_events_of_type(
            SystemEvents.TELEMETRY_EVENT
        )
        assert len(events) > 0

    async def test_collector_publishes_session_events(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
        event_collector: EventCollector,
    ) -> None:
        """Test that collector publishes SESSION_START and SESSION_END events."""
        # Configure mock to disconnect after a few frames
        call_count: int = 0

        def is_connected_side_effect() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count <= 3  # Return True for first 3 calls

        mock_telemetry_source.start.return_value = True
        type(mock_telemetry_source).is_connected = PropertyMock(
            side_effect=is_connected_side_effect
        )

        # Register event collectors for session events
        session_start_handler: Handler[SessionStart] = Handler(
            type=SystemEvents.SESSION_START,
            fn=event_collector.collect,
        )
        session_end_handler: Handler[SessionEnd] = Handler(
            type=SystemEvents.SESSION_END,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([session_start_handler, session_end_handler])

        # Start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, mock_telemetry_source, session_registry
        )
        collector.start()

        # Wait for events to be collected
        await asyncio.sleep(1.0)

        # Stop collector
        collector.stop()
        await asyncio.sleep(0.2)

        # Verify SESSION_START was published
        start_events: list[Event[SessionStart]] = event_collector.get_events_of_type(
            SystemEvents.SESSION_START
        )
        assert len(start_events) == 1
        assert isinstance(start_events[0].data, SessionStart)
        assert start_events[0].data.SessionFrame is not None

        # Verify SESSION_END was published
        end_events: list[Event[SessionEnd]] = event_collector.get_events_of_type(
            SystemEvents.SESSION_END
        )
        assert len(end_events) >= 1
        assert isinstance(end_events[0].data, SessionEnd)


@pytest.mark.ibt
@pytest.mark.integration
@pytest.mark.slow
class TestTelemetryCollectorWithRealIBT:
    """Integration tests for TelemetryCollector with real IBT file."""

    async def test_collect_from_ibt_file(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        ibt_file_path: Path,
        event_collector: EventCollector,
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
        handler: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, source, session_registry
        )
        collector.start()

        # Wait for some events to be collected
        try:
            events: list[Event[TelemetryAndSessionId]] = await event_collector.wait_for_event(
                SystemEvents.TELEMETRY_EVENT, timeout=20.0, count=10
            )
            assert len(events) >= 10

            # Verify event data
            for event in events:
                assert event.type == SystemEvents.TELEMETRY_EVENT
                assert isinstance(event.data, TelemetryAndSessionId)

                # Verify telemetry data has reasonable values
                telem: TelemetryFrame = event.data.telemetry
                assert telem.speed >= 0
                assert telem.rpm >= 0
                assert 0 <= telem.throttle <= 1
                assert 0 <= telem.brake <= 1

        finally:
            collector.stop()
            await asyncio.sleep(0.2)

    async def test_session_frame_consistency(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        ibt_file_path: Path,
        event_collector: EventCollector,
    ) -> None:
        """Test that session frame remains consistent via registry."""
        from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource

        # Create replay source
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path,
            speed_multiplier=10.0,
            loop=False,
        )

        # Register event collector for session start
        handler: Handler[SessionStart] = Handler(
            type=SystemEvents.SESSION_START,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([handler])

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, source, session_registry
        )
        collector.start()

        try:
            # Wait for session start event
            events: list[Event[SessionStart]] = await event_collector.wait_for_event(
                SystemEvents.SESSION_START, timeout=10.0, count=1
            )

            # Verify session is in registry
            assert session_registry.has_active_session
            current_session = session_registry.get_current_session()
            assert current_session is not None
            assert current_session.session_id == events[0].data.SessionFrame.session_id
            assert current_session.track_name == events[0].data.SessionFrame.track_name

        finally:
            collector.stop()
            await asyncio.sleep(0.2)
