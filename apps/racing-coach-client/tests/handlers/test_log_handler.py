"""Tests for LogHandler."""

import logging

import pytest
from racing_coach_client.handlers.log_handler import LogHandler
from racing_coach_core.events.base import Event, EventBus, HandlerContext, SystemEvents
from racing_coach_core.models.events import TelemetryAndSession


@pytest.mark.unit
class TestLogHandlerUnit:
    """Unit tests for LogHandler."""

    def test_initialization(self, event_bus: EventBus):
        """Test LogHandler initializes correctly."""
        handler = LogHandler(event_bus, log_frequency=60)

        assert handler.event_bus is event_bus
        assert handler.log_frequency == 60
        assert handler.frame_count == -1

    def test_initialization_with_custom_frequency(self, event_bus: EventBus):
        """Test LogHandler with custom log frequency."""
        handler = LogHandler(event_bus, log_frequency=10)

        assert handler.log_frequency == 10

    def test_frame_count_increments(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
    ):
        """Test that frame count increments with each event."""
        handler = LogHandler(running_event_bus, log_frequency=100)

        # Send multiple frames
        for i in range(5):
            telem = telemetry_frame_factory.build()
            session = session_frame_factory.build()
            event = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        assert handler.frame_count == 4  # Started at -1, incremented 5 times

    def test_logs_at_correct_frequency(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        caplog,
    ):
        """Test that logging occurs at the specified frequency."""
        handler = LogHandler(running_event_bus, log_frequency=3)

        with caplog.at_level(logging.INFO):
            # Send 10 frames
            for i in range(10):
                telem = telemetry_frame_factory.build()
                session = session_frame_factory.build()
                event = Event(
                    type=SystemEvents.TELEMETRY_FRAME,
                    data=TelemetryAndSession(
                        TelemetryFrame=telem, SessionFrame=session
                    ),
                )
                context = HandlerContext(event_bus=running_event_bus, event=event)
                handler.handle_telemetry_frame(context)

        # Should log at frames 0, 3, 6, 9 (4 times)
        # Each log creates 2 log entries (telemetry + session)
        telemetry_logs = [
            record for record in caplog.records if "Telemetry Frame:" in record.message
        ]
        session_logs = [
            record for record in caplog.records if "Session Frame:" in record.message
        ]

        assert len(telemetry_logs) == 4  # Logged at frames 0, 3, 6, 9
        assert len(session_logs) == 4

    def test_handles_missing_telemetry_frame(
        self, running_event_bus: EventBus, session_frame_factory, caplog
    ):
        """Test that handler handles missing telemetry frame gracefully."""
        handler = LogHandler(running_event_bus, log_frequency=1)

        # Create event with None telemetry frame
        session = session_frame_factory.build()
        event = Event(
            type=SystemEvents.TELEMETRY_FRAME,
            data=TelemetryAndSession(TelemetryFrame=None, SessionFrame=session),  # type: ignore
        )

        with caplog.at_level(logging.WARNING):
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Should log warning
        warnings = [
            record
            for record in caplog.records
            if "No Telemetry Frame data found" in record.message
        ]
        assert len(warnings) == 1

    def test_logs_contain_telemetry_data(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        caplog,
    ):
        """Test that logs contain actual telemetry data."""
        handler = LogHandler(running_event_bus, log_frequency=1)

        telem = telemetry_frame_factory.build(speed=50.0, rpm=5000.0)
        session = session_frame_factory.build(track_name="Test Track")

        with caplog.at_level(logging.INFO):
            event = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Verify telemetry data in logs
        log_messages = [record.message for record in caplog.records]
        combined_logs = " ".join(log_messages)

        assert "50.0" in combined_logs  # Speed
        assert "5000" in combined_logs  # RPM
        assert "Test Track" in combined_logs  # Track name


@pytest.mark.integration
class TestLogHandlerIntegration:
    """Integration tests for LogHandler."""

    async def test_log_handler_with_event_bus(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory,
        session_frame_factory,
        caplog,
    ):
        """Test LogHandler integrated with event bus."""
        import asyncio

        handler = LogHandler(running_event_bus, log_frequency=2)

        # Publish events through event bus
        with caplog.at_level(logging.INFO):
            for i in range(6):
                telem = telemetry_frame_factory.build()
                session = session_frame_factory.build()
                event = Event(
                    type=SystemEvents.TELEMETRY_FRAME,
                    data=TelemetryAndSession(
                        TelemetryFrame=telem, SessionFrame=session
                    ),
                )
                running_event_bus.thread_safe_publish(event)

            # Wait for events to be processed
            await asyncio.sleep(0.5)

        # Should log at frames 0, 2, 4 (3 times)
        telemetry_logs = [
            record for record in caplog.records if "Telemetry Frame:" in record.message
        ]
        assert len(telemetry_logs) >= 3
