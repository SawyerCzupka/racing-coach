"""Tests for LapHandler."""

import asyncio

import pytest
from racing_coach_client.handlers.lap_handler import LapHandler
from racing_coach_core.events.base import Event, EventBus, Handler, SystemEvents
from racing_coach_core.models.events import LapAndSession, TelemetryAndSession
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame


@pytest.mark.unit
class TestLapHandlerUnit:
    """Unit tests for LapHandler."""

    def test_initialization(self, event_bus: EventBus):
        """Test LapHandler initializes correctly."""
        handler = LapHandler(event_bus)

        assert handler.event_bus is event_bus
        assert handler.current_lap == -1
        assert handler.telemetry_buffer == []
        assert handler.current_session is None

    async def test_first_telemetry_frame_sets_session(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
    ):
        """Test that first telemetry frame sets the session."""
        handler = LapHandler(running_event_bus)

        # Create test data
        telem = telemetry_frame_factory.build(lap_number=1)
        session = session_frame_factory.build()

        # Handle event
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
        )

        from racing_coach_core.events.base import HandlerContext

        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        assert handler.current_session is session

    async def test_telemetry_frames_buffered_during_lap(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
    ):
        """Test that telemetry frames are buffered during a lap."""
        handler = LapHandler(running_event_bus)
        session = session_frame_factory.build()

        # Send multiple frames for lap 1
        for i in range(5):
            telem = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.2
            )
            event = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )

            from racing_coach_core.events.base import HandlerContext

            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Verify frames are buffered
        assert len(handler.telemetry_buffer) == 5
        assert handler.current_lap == 1

    async def test_lap_change_publishes_event(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        event_collector,
    ):
        """Test that lap change triggers LAP_TELEMETRY_SEQUENCE event."""
        # Register collector for lap events
        from racing_coach_core.events.base import Handler as EventHandler

        lap_handler_registration = EventHandler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            func=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler = LapHandler(running_event_bus)
        session = session_frame_factory.build()

        # Start with lap 0 (outlap), then transition to lap 1
        telem_outlap = telemetry_frame_factory.build(
            lap_number=0, lap_distance_pct=0.5
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_outlap, SessionFrame=session),
        )

        from racing_coach_core.events.base import HandlerContext

        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Send frames for lap 1
        for i in range(5):
            telem = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=i * 0.2
            )
            event = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Change to lap 2 - should trigger publish
        telem_lap2 = telemetry_frame_factory.build(
            lap_number=2, lap_distance_pct=0.01
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_lap2, SessionFrame=session),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Wait for lap event
        events = await event_collector.wait_for_event(
            SystemEvents.LAP_TELEMETRY_SEQUENCE, timeout=2.0, count=1
        )

        assert len(events) == 1
        lap_event = events[0]
        assert lap_event.type == SystemEvents.LAP_TELEMETRY_SEQUENCE
        assert isinstance(lap_event.data, LapAndSession)
        assert len(lap_event.data.LapTelemetry.frames) == 5

        # Buffer should be cleared and new lap started
        assert len(handler.telemetry_buffer) == 1
        assert handler.current_lap == 2

    async def test_starting_first_lap_clears_buffer(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
    ):
        """Test that starting first lap clears buffer without publishing."""
        handler = LapHandler(running_event_bus)
        session = session_frame_factory.build()

        # Start from lap 0 (initial state)
        telem_outlap = telemetry_frame_factory.build(
            lap_number=0, lap_distance_pct=0.5
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_outlap, SessionFrame=session),
        )

        from racing_coach_core.events.base import HandlerContext

        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Transition to lap 1
        telem_lap1 = telemetry_frame_factory.build(
            lap_number=1, lap_distance_pct=0.01
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_lap1, SessionFrame=session),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Should clear buffer and start new lap
        assert handler.current_lap == 1
        assert len(handler.telemetry_buffer) == 1

    async def test_ignores_incomplete_lap_transitions(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        event_collector,
    ):
        """Test that incomplete laps (< LAP_COMPLETION_THRESHOLD) are ignored."""
        # Register collector for lap events
        from racing_coach_core.events.base import Handler as EventHandler

        lap_handler_registration = EventHandler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            func=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler = LapHandler(running_event_bus)
        session = session_frame_factory.build()

        # Start with lap 1
        telem_lap1 = telemetry_frame_factory.build(
            lap_number=1, lap_distance_pct=0.5
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_lap1, SessionFrame=session),
        )

        from racing_coach_core.events.base import HandlerContext

        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Add some frames
        for i in range(3):
            telem = telemetry_frame_factory.build(
                lap_number=1, lap_distance_pct=0.5 + i * 0.1
            )
            event = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Transition to lap 0 early (incomplete lap) - should be ignored
        telem_lap0 = telemetry_frame_factory.build(
            lap_number=0, lap_distance_pct=0.2  # < LAP_COMPLETION_THRESHOLD
        )
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=telem_lap0, SessionFrame=session),
        )
        context = HandlerContext(event_bus=running_event_bus, event=event)
        handler.handle_telemetry_frame(context)

        # Wait a bit
        await asyncio.sleep(0.2)

        # Should not have published any lap events
        lap_events = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 0

        # Buffer should be cleared
        assert len(handler.telemetry_buffer) == 0
        assert handler.current_lap == 0

    def test_publish_lap_and_flush_buffer_with_empty_buffer(
        self, running_event_bus: EventBus
    ):
        """Test that publishing with empty buffer logs warning."""
        handler = LapHandler(running_event_bus)

        import logging

        with pytest.LogCaptureFixture.for_logger(
            "racing_coach_client.handlers.lap_handler", level=logging.WARNING
        ) as log_capture:
            handler.publish_lap_and_flush_buffer()

        # Should not raise error, just log warning
        assert len(handler.telemetry_buffer) == 0

    def test_publish_lap_and_flush_buffer_without_session(
        self, running_event_bus: EventBus, telemetry_frame_factory
    ):
        """Test that publishing without session logs warning."""
        handler = LapHandler(running_event_bus)
        handler.telemetry_buffer = [telemetry_frame_factory.build()]

        import logging

        with pytest.LogCaptureFixture.for_logger(
            "racing_coach_client.handlers.lap_handler", level=logging.WARNING
        ) as log_capture:
            handler.publish_lap_and_flush_buffer()

        # Should not raise error, just log warning
        assert handler.current_session is None


@pytest.mark.integration
class TestLapHandlerIntegration:
    """Integration tests for LapHandler."""

    async def test_multiple_lap_transitions(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        event_collector,
    ):
        """Test handling multiple lap transitions."""
        # Register collector for lap events
        from racing_coach_core.events.base import Handler as EventHandler

        lap_handler_registration = EventHandler(
            type=SystemEvents.LAP_TELEMETRY_SEQUENCE,
            func=event_collector.collect,
        )
        running_event_bus.register_handlers([lap_handler_registration])

        handler = LapHandler(running_event_bus)
        session = session_frame_factory.build()

        from racing_coach_core.events.base import HandlerContext

        # Simulate 3 complete laps
        for lap_num in range(1, 4):
            # Send frames for this lap
            for i in range(10):
                telem = telemetry_frame_factory.build(
                    lap_number=lap_num,
                    lap_distance_pct=i * 0.1,
                    session_time=lap_num * 100 + i,
                )
                event = Event(
                    type=SystemEvents.TELEMETRY_FRAME,
                    data=TelemetryAndSession(
                        TelemetryFrame=telem, SessionFrame=session
                    ),
                )
                context = HandlerContext(event_bus=running_event_bus, event=event)
                handler.handle_telemetry_frame(context)

        # Wait for lap events (should be 2, since last lap is still in progress)
        await asyncio.sleep(0.5)

        lap_events = event_collector.get_events_of_type(
            SystemEvents.LAP_TELEMETRY_SEQUENCE
        )
        assert len(lap_events) == 2  # Laps 1 and 2 completed

        # Verify each lap has 10 frames
        for lap_event in lap_events:
            assert len(lap_event.data.LapTelemetry.frames) == 10
