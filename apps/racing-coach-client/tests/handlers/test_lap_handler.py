"""Tests for LapHandler."""

import asyncio

import pytest
from racing_coach_client.handlers.lap_handler import LapHandler
from racing_coach_core.events.base import Event, EventBus, Handler, HandlerContext, SystemEvents
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.schemas.events import LapAndSession, SessionStart, TelemetryAndSessionId
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame

from tests.conftest import EventCollector
from tests.factories import SessionFrameFactory, TelemetryFrameFactory


@pytest.mark.unit
class TestLapHandlerUnit:
    """Unit tests for LapHandler."""

    def test_initialization(self, event_bus: EventBus, session_registry: SessionRegistry) -> None:
        """Test LapHandler initializes correctly."""
        handler: LapHandler = LapHandler(event_bus, session_registry)

        assert handler.event_bus is event_bus
        assert handler.session_registry is session_registry
        assert handler.current_lap == -1
        assert handler.telemetry_buffer == []
        assert handler.last_session_id is None

    async def test_first_telemetry_frame_sets_session(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
    ) -> None:
        """Test that first telemetry frame uses session from registry."""
        handler: LapHandler = LapHandler(running_event_bus, session_registry)

        # Create test data
        telem: TelemetryFrame = telemetry_frame_factory.build(lap_number=1)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Handle event
        event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
        )

        context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
            event_bus=running_event_bus, event=event
        )
        handler.handle_telemetry_frame(context)

        assert session_registry.get_current_session() is session
        assert len(handler.telemetry_buffer) == 1

    async def test_telemetry_frames_buffered_during_lap(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
    ) -> None:
        """Test that telemetry frames are buffered during a lap."""
        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Send multiple frames for lap 1
        for i in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.2
            )
            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )

            context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
                event_bus=running_event_bus, event=event
            )
            handler.handle_telemetry_frame(context)

        # Verify frames are buffered
        assert len(handler.telemetry_buffer) == 5
        assert handler.current_lap == 1

    async def test_lap_change_publishes_event(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test that lap change triggers LAP_TELEMETRY_SEQUENCE event."""
        # Register collector for lap events
        lap_handler_registration: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Start with lap 0 (outlap), then transition to lap 1
        telem_outlap: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=0, lap_distance_pct=0.5
        )
        event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_outlap, session_id=session.session_id),
        )

        context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
            event_bus=running_event_bus, event=event
        )
        handler.handle_telemetry_frame(context)

        # Send frames for lap 1
        for i in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.2
            )
            event = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Change to lap 2 - should trigger publish
        telem_lap2: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=2, lap_distance_pct=0.01
        )
        event = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_lap2, session_id=session.session_id),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Wait for lap event
        events: list[Event[LapAndSession]] = await event_collector.wait_for_event(
            SystemEvents.LAP_TELEMETRY_SEQUENCE, timeout=2.0, count=1
        )

        assert len(events) == 1
        lap_event: Event[LapAndSession] = events[0]
        assert lap_event.type == SystemEvents.LAP_TELEMETRY_SEQUENCE
        assert isinstance(lap_event.data, LapAndSession)
        assert len(lap_event.data.LapTelemetry.frames) == 5

        # Buffer should be cleared and new lap started
        assert len(handler.telemetry_buffer) == 1
        assert handler.current_lap == 2

    async def test_starting_first_lap_clears_buffer(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
    ) -> None:
        """Test that starting first lap clears buffer without publishing."""
        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Start from lap 0 (initial state)
        telem_outlap: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=0, lap_distance_pct=0.5
        )
        event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_outlap, session_id=session.session_id),
        )

        context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
            event_bus=running_event_bus, event=event
        )
        handler.handle_telemetry_frame(context)

        # Transition to lap 1
        telem_lap1: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=1, lap_distance_pct=0.01
        )
        event = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_lap1, session_id=session.session_id),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Should clear buffer and start new lap
        assert handler.current_lap == 1
        assert len(handler.telemetry_buffer) == 1

    async def test_ignores_incomplete_lap_transitions(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test that incomplete laps (< LAP_COMPLETION_THRESHOLD) are ignored."""
        # Register collector for lap events
        lap_handler_registration: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Start with lap 1
        telem_lap1: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=1, lap_distance_pct=0.5
        )
        event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_lap1, session_id=session.session_id),
        )

        context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
            event_bus=running_event_bus, event=event
        )
        handler.handle_telemetry_frame(context)

        # Add some frames
        for i in range(3):
            telem: TelemetryFrame = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=0.5 + i * 0.1
            )
            event = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Transition to lap 0 early (incomplete lap) - should be ignored
        telem_lap0: TelemetryFrame = telemetry_frame_factory.build(
            lap_number=0,
            lap_distance_pct=0.2,  # < LAP_COMPLETION_THRESHOLD
        )
        event = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=telem_lap0, session_id=session.session_id),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Wait a bit
        await asyncio.sleep(0.2)

        # Should not have published any lap events
        lap_events: list[Event[LapAndSession]] = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 0

        # Buffer should be cleared
        assert len(handler.telemetry_buffer) == 0
        assert handler.current_lap == 0

    def test_publish_lap_and_flush_buffer_with_empty_buffer(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that publishing with empty buffer logs warning."""
        import logging

        handler: LapHandler = LapHandler(running_event_bus, session_registry)

        with caplog.at_level(logging.WARNING):
            handler.publish_lap_and_flush_buffer()

        # Should not raise error, just log warning
        assert len(handler.telemetry_buffer) == 0
        # Verify warning was logged
        assert any("empty" in record.message.lower() for record in caplog.records)

    def test_publish_lap_and_flush_buffer_without_session(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that publishing without session logs warning."""
        import logging

        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        handler.telemetry_buffer = [telemetry_frame_factory.build()]

        with caplog.at_level(logging.WARNING):
            handler.publish_lap_and_flush_buffer()

        # Should not raise error, just log warning
        assert session_registry.get_current_session() is None
        # Verify warning was logged
        assert any("session" in record.message.lower() for record in caplog.records)

    async def test_session_start_flushes_buffer_on_new_session(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test that SESSION_START with new session flushes incomplete lap buffer."""
        # Register collector for lap events
        lap_handler_registration: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler: LapHandler = LapHandler(running_event_bus, session_registry)

        # First session
        session1: SessionFrame = session_frame_factory.build()
        session_registry.start_session(session1)

        # Handle session start
        session_start_event1: Event[SessionStart] = Event(
            type=SystemEvents.SESSION_START,
            data=SessionStart(SessionFrame=session1),
        )
        context1: HandlerContext[SessionStart] = HandlerContext(
            event_bus=running_event_bus, event=session_start_event1
        )
        handler.handle_session_start(context1)

        # Buffer some telemetry
        for i in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.2
            )
            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=telem, session_id=session1.session_id),
            )
            ctx: HandlerContext[TelemetryAndSessionId] = HandlerContext(
                event_bus=running_event_bus, event=event
            )
            handler.handle_telemetry_frame(ctx)

        assert len(handler.telemetry_buffer) == 5

        # Start new session - should flush buffer
        session2: SessionFrame = session_frame_factory.build()
        session_registry.start_session(session2)

        session_start_event2: Event[SessionStart] = Event(
            type=SystemEvents.SESSION_START,
            data=SessionStart(SessionFrame=session2),
        )
        context2: HandlerContext[SessionStart] = HandlerContext(
            event_bus=running_event_bus, event=session_start_event2
        )
        handler.handle_session_start(context2)

        # Wait for lap event
        await asyncio.sleep(0.3)

        # Should have published the incomplete lap
        lap_events: list[Event[LapAndSession]] = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 1
        assert len(lap_events[0].data.LapTelemetry.frames) == 5

        # Buffer should be cleared
        assert len(handler.telemetry_buffer) == 0
        assert handler.current_lap == -1
        assert handler.last_session_id == session2.session_id


@pytest.mark.integration
class TestLapHandlerIntegration:
    """Integration tests for LapHandler."""

    async def test_multiple_lap_transitions(
        self,
        running_event_bus: EventBus,
        session_registry: SessionRegistry,
        telemetry_frame_factory: TelemetryFrameFactory,
        session_frame_factory: SessionFrameFactory,
        event_collector: EventCollector,
    ) -> None:
        """Test handling multiple lap transitions."""
        # Register collector for lap events
        lap_handler_registration: Handler[LapAndSession] = Handler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            fn=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler: LapHandler = LapHandler(running_event_bus, session_registry)
        session: SessionFrame = session_frame_factory.build()

        # Start session in registry
        session_registry.start_session(session)

        # Simulate 3 complete laps
        for lap_num in range(1, 4):
            # Send frames for this lap
            for i in range(10):
                telem: TelemetryFrame = telemetry_frame_factory.build(
                    lap_number=lap_num,
                    lap_distance_pct=i * 0.1,
                    session_time=lap_num * 100 + i,
                )
                event: Event[TelemetryAndSessionId] = Event(
                    type=SystemEvents.TELEMETRY_EVENT,
                    data=TelemetryAndSessionId(telemetry=telem, session_id=session.session_id),
                )
                context: HandlerContext[TelemetryAndSessionId] = HandlerContext(
                    event_bus=running_event_bus, event=event
                )
                handler.handle_telemetry_frame(context)

        # Wait for lap events (should be 2, since last lap is still in progress)
        await asyncio.sleep(0.5)

        lap_events: list[Event[LapAndSession]] = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 2  # Laps 1 and 2 completed

        # Verify each lap has 10 frames
        for lap_event in lap_events:
            assert len(lap_event.data.LapTelemetry.frames) == 10
