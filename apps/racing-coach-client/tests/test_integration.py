"""End-to-end integration tests for racing-coach-client."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource
from racing_coach_client.handlers.lap_handler import LapHandler
from racing_coach_client.handlers.log_handler import LogHandler
from racing_coach_core.events.base import Event, EventBus, Handler, HandlerContext, SystemEvents
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.schemas.events import LapAndSession, SessionStart, TelemetryAndSessionId
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame

from tests.conftest import EventCollector
from tests.factories import SessionFrameFactory, TelemetryFrameFactory


@pytest.mark.integration
class TestEventFlowWithMocks:
    """Integration tests for event flow with mocked telemetry source."""

    async def test_collector_to_handlers_event_flow(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        mock_telemetry_source: MagicMock,
        event_collector: EventCollector,
    ) -> None:
        """Test complete event flow from collector through handlers."""
        # Setup event collector to capture both event types
        telemetry_handler: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=event_collector.collect,
        )
        lap_handler_event: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([telemetry_handler, lap_handler_event])

        # Create handlers
        LapHandler(running_event_bus, session_registry)
        LogHandler(running_event_bus, session_registry, log_frequency=5)

        # Configure mock to disconnect after several frames
        call_count: int = 0

        def is_connected_side_effect() -> bool:
            nonlocal call_count
            call_count += 1
            return call_count <= 10

        mock_telemetry_source.start.return_value = True
        type(mock_telemetry_source).is_connected = PropertyMock(
            side_effect=is_connected_side_effect
        )

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, mock_telemetry_source, session_registry
        )
        collector.start()

        try:
            # Wait for events to be collected
            await asyncio.sleep(1.0)

            # Verify TELEMETRY_EVENT events were published
            telemetry_events: list[Event[TelemetryAndSessionId]] = (
                event_collector.get_events_of_type(SystemEvents.TELEMETRY_EVENT)
            )
            assert len(telemetry_events) > 0

            # Verify events have correct structure
            for event in telemetry_events:
                assert isinstance(event.data, TelemetryAndSessionId)
                assert event.data.telemetry is not None

        finally:
            collector.stop()
            await asyncio.sleep(0.2)

    async def test_lap_handler_processes_telemetry_frames(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test that LapHandler correctly processes telemetry frames and publishes laps."""
        # Register collector for lap events
        lap_event_handler: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_event_handler])

        # Create lap handler
        lap_handler: LapHandler = LapHandler(running_event_bus, session_registry)

        # Start session
        session: SessionFrame = session_frame_factory.build()
        session_registry.start_session(session)

        # Start with outlap (lap 0)
        for i in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build(
                lap_number=0, lap_distance_pct=i * 0.2, session_time=i * 0.1
            )
            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )
            context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
                event_bus=running_event_bus, event=event
            )
            lap_handler.handle_telemetry_frame(context)

        # Complete first timed lap (lap 1)
        for i in range(10):
            telem = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.1, session_time=10 + i * 0.1
            )
            event = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            lap_handler.handle_telemetry_frame(context)

        # Start lap 2 - should trigger publish of lap 1
        telem = telemetry_frame_factory.build(
            lap_number=2, lap_distance_pct=0.01, session_time=20.0
        )
        event = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        lap_handler.handle_telemetry_frame(context)

        # Wait for lap event to be processed
        await asyncio.sleep(0.5)

        # Verify lap was published
        lap_events: list[Event[LapAndSession]] = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 1

        lap_event: Event[LapAndSession] = lap_events[0]
        assert isinstance(lap_event.data, LapAndSession)
        assert len(lap_event.data.LapTelemetry.frames) == 10
        assert lap_event.data.SessionFrame.session_id == session.session_id


@pytest.mark.ibt
@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWithRealIBT:
    """End-to-end integration tests with real IBT file."""

    async def test_complete_flow_with_ibt_file(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        ibt_file_path: Path,
        event_collector: EventCollector,
    ) -> None:
        """Test complete flow from IBT file through all handlers."""
        # Register collectors for both event types
        telemetry_handler: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=event_collector.collect,
        )
        lap_handler_event: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([telemetry_handler, lap_handler_event])

        # Create source and handlers
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path,
            speed_multiplier=50.0,  # Speed up significantly for testing
            loop=False,
        )

        LapHandler(running_event_bus, session_registry)
        LogHandler(running_event_bus, session_registry, log_frequency=50)

        # Create and start collector
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, source, session_registry
        )
        collector.start()

        try:
            # Wait for telemetry events
            telemetry_events: list[
                Event[TelemetryAndSessionId]
            ] = await event_collector.wait_for_event(
                SystemEvents.TELEMETRY_EVENT, timeout=15, count=50
            )
            assert len(telemetry_events) >= 50

            # Verify telemetry event structure
            for event in telemetry_events[:5]:  # Check first 5
                assert isinstance(event.data, TelemetryAndSessionId)
                telem: TelemetryFrame = event.data.telemetry

                # Verify realistic telemetry values
                assert telem.speed >= 0
                assert telem.rpm >= 0
                assert 0 <= telem.throttle <= 1
                assert 0 <= telem.brake <= 1
                assert telem.lap_number >= 0

            # Verify session data is available via registry
            session = session_registry.get_current_session()
            assert session is not None
            assert session.track_name is not None
            assert session.car_name is not None

            # Wait longer to see if any laps complete
            await asyncio.sleep(5.0)

            # Check if any laps were published
            lap_events: list[Event[LapAndSession]] = event_collector.get_events_of_type(
                SystemEvents.LAP_TELEMETRY_SEQUENCE
            )

            if len(lap_events) > 0:
                # If laps were published, verify their structure
                for lap_event in lap_events:
                    assert isinstance(lap_event.data, LapAndSession)
                    assert len(lap_event.data.LapTelemetry.frames) > 0
                    assert lap_event.data.SessionFrame is not None

        finally:
            collector.stop()
            await asyncio.sleep(0.2)

    async def test_session_consistency_across_events(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        ibt_file_path: Path,
        event_collector: EventCollector,
    ) -> None:
        """Test that session data remains consistent via registry."""
        # Register collector for session start
        session_handler: Handler[SessionStart] = Handler(
            type=SystemEvents.SESSION_START,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([session_handler])

        # Create source and collector
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=20.0, loop=False
        )
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, source, session_registry
        )
        collector.start()

        try:
            # Wait for session start event
            events: list[Event[SessionStart]] = await event_collector.wait_for_event(
                SystemEvents.SESSION_START, timeout=10.0, count=1
            )

            # Verify session is in registry and consistent
            assert session_registry.has_active_session
            current_session = session_registry.get_current_session()
            assert current_session is not None

            first_session = events[0].data.SessionFrame
            assert current_session.session_id == first_session.session_id
            assert current_session.track_id == first_session.track_id
            assert current_session.track_name == first_session.track_name
            assert current_session.car_id == first_session.car_id
            assert current_session.car_name == first_session.car_name

        finally:
            collector.stop()
            await asyncio.sleep(0.2)

    async def test_telemetry_progression(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        ibt_file_path: Path,
        event_collector: EventCollector,
    ) -> None:
        """Test that telemetry data progresses correctly through time."""
        # Register collector
        telemetry_handler: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([telemetry_handler])

        # Create source and collector
        source: ReplayTelemetrySource = ReplayTelemetrySource(
            file_path=ibt_file_path, speed_multiplier=10.0, loop=False
        )
        collector: TelemetryCollector = TelemetryCollector(
            running_event_bus, source, session_registry
        )
        collector.start()

        try:
            # Collect events
            events: list[Event[TelemetryAndSessionId]] = await event_collector.wait_for_event(
                SystemEvents.TELEMETRY_EVENT, timeout=10.0, count=30
            )

            # Verify session_time progresses
            session_times: list[float] = [event.data.telemetry.session_time for event in events]

            # Session time should generally increase (allowing for some tolerance)
            for i in range(1, len(session_times)):
                # Allow small decreases due to async timing, but general trend should be upward
                if i > 5:  # Skip first few frames
                    assert session_times[i] >= session_times[0]

        finally:
            collector.stop()
            await asyncio.sleep(0.2)


@pytest.mark.integration
class TestEventBusSubscriberPattern:
    """Test that subscribers correctly receive and process events."""

    async def test_multiple_subscribers_receive_same_events(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test that multiple subscribers can receive the same events."""
        # Create two separate collectors
        collector1: EventCollector = event_collector
        collector2: EventCollector = EventCollector()

        # Register both
        handler1: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=collector1.collect,
        )
        handler2: Handler[TelemetryAndSessionId] = Handler(
            type=SystemEvents.TELEMETRY_EVENT,
            fn=collector2.collect,
        )
        running_event_bus.register_handlers([handler1, handler2])

        # Create a session for the test
        session: SessionFrame = session_frame_factory.build()

        # Publish some events
        for _ in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build()
            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )
            running_event_bus.thread_safe_publish(event)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Both should receive all events
        events1: list[Event[TelemetryAndSessionId]] = collector1.get_events_of_type(
            SystemEvents.TELEMETRY_EVENT
        )
        events2: list[Event[TelemetryAndSessionId]] = collector2.get_events_of_type(
            SystemEvents.TELEMETRY_EVENT
        )

        assert len(events1) == 5
        assert len(events2) == 5

        # Events should be the same
        for e1, e2 in zip(events1, events2, strict=False):
            assert e1.data == e2.data
