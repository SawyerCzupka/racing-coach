"""Tests for LogHandler."""

import logging
from collections.abc import Callable
from typing import Any

import pytest
from pytest import LogCaptureFixture
from racing_coach_client.handlers.log_handler import LogHandler
from racing_coach_core.events.base import Event, EventBus, HandlerContext, SystemEvents
from racing_coach_core.models.events import TelemetryAndSession
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame


@pytest.mark.unit
class TestLogHandlerUnit:
    """Unit tests for LogHandler."""

    def test_initialization(self, event_bus: EventBus) -> None:
        """Test LogHandler initializes correctly."""
        handler: LogHandler = LogHandler(event_bus, log_frequency=60)

        assert handler.event_bus is event_bus
        assert handler.log_frequency == 60
        assert handler.frame_count == -1

    def test_initialization_with_custom_frequency(self, event_bus: EventBus) -> None:
        """Test LogHandler with custom log frequency."""
        handler: LogHandler = LogHandler(event_bus, log_frequency=10)

        assert handler.log_frequency == 10

    def test_frame_count_increments(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory: Callable[..., TelemetryFrame],
        session_frame_factory: Callable[..., SessionFrame],
    ) -> None:
        """Test that frame count increments with each event."""
        handler: LogHandler = LogHandler(running_event_bus, log_frequency=100)

        # Send multiple frames
        for i in range(5):
            telem: TelemetryFrame = telemetry_frame_factory.build()  # type: ignore[attr-defined]
            session: SessionFrame = session_frame_factory.build()  # type: ignore[attr-defined]
            event: Event[TelemetryAndSession] = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context: HandlerContext[TelemetryAndSession] = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        assert handler.frame_count == 4  # Started at -1, incremented 5 times

    def test_logs_at_correct_frequency(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory: Callable[..., TelemetryFrame],
        session_frame_factory: Callable[..., SessionFrame],
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that logging occurs at the specified frequency."""
        handler: LogHandler = LogHandler(running_event_bus, log_frequency=3)

        with caplog.at_level(logging.INFO):
            # Send 10 frames
            for i in range(10):
                telem: TelemetryFrame = telemetry_frame_factory.build()  # type: ignore[attr-defined]
                session: SessionFrame = session_frame_factory.build()  # type: ignore[attr-defined]
                event: Event[TelemetryAndSession] = Event(
                    type=SystemEvents.TELEMETRY_FRAME,
                    data=TelemetryAndSession(
                        TelemetryFrame=telem, SessionFrame=session
                    ),
                )
                context: HandlerContext[TelemetryAndSession] = HandlerContext(event_bus=running_event_bus, event=event)
                handler.handle_telemetry_frame(context)

        # Should log at frames 0, 3, 6, 9 (4 times)
        # Each log creates 2 log entries (telemetry + session)
        telemetry_logs: list[Any] = [
            record for record in caplog.records if "Telemetry Frame:" in record.message
        ]
        session_logs: list[Any] = [
            record for record in caplog.records if "Session Frame:" in record.message
        ]

        assert len(telemetry_logs) == 4  # Logged at frames 0, 3, 6, 9
        assert len(session_logs) == 4

    def test_logs_contain_telemetry_data(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory: Callable[..., TelemetryFrame],
        session_frame_factory: Callable[..., SessionFrame],
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that logs contain actual telemetry data."""
        handler: LogHandler = LogHandler(running_event_bus, log_frequency=1)

        telem: TelemetryFrame = telemetry_frame_factory.build(speed=50.0, rpm=5000.0)  # type: ignore[attr-defined]
        session: SessionFrame = session_frame_factory.build(track_name="Test Track")  # type: ignore[attr-defined]

        with caplog.at_level(logging.INFO):
            event: Event[TelemetryAndSession] = Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(TelemetryFrame=telem, SessionFrame=session),
            )
            context: HandlerContext[TelemetryAndSession] = HandlerContext(event_bus=running_event_bus, event=event)
            handler.handle_telemetry_frame(context)

        # Verify telemetry data in logs
        log_messages: list[str] = [record.message for record in caplog.records]
        combined_logs: str = " ".join(log_messages)

        assert "50.0" in combined_logs  # Speed
        assert "5000" in combined_logs  # RPM
        assert "Test Track" in combined_logs  # Track name


@pytest.mark.integration
class TestLogHandlerIntegration:
    """Integration tests for LogHandler."""

    async def test_log_handler_with_event_bus(
        self,
        running_event_bus: EventBus,
        telemetry_frame_factory: Callable[..., TelemetryFrame],
        session_frame_factory: Callable[..., SessionFrame],
        caplog: LogCaptureFixture,
    ) -> None:
        """Test LogHandler integrated with event bus."""
        import asyncio

        handler: LogHandler = LogHandler(running_event_bus, log_frequency=2)

        # Publish events through event bus
        with caplog.at_level(logging.INFO):
            for i in range(6):
                telem: TelemetryFrame = telemetry_frame_factory.build()  # type: ignore[attr-defined]
                session: SessionFrame = session_frame_factory.build()  # type: ignore[attr-defined]
                event: Event[TelemetryAndSession] = Event(
                    type=SystemEvents.TELEMETRY_FRAME,
                    data=TelemetryAndSession(
                        TelemetryFrame=telem, SessionFrame=session
                    ),
                )
                running_event_bus.thread_safe_publish(event)

            # Wait for events to be processed
            await asyncio.sleep(0.5)

        # Should log at frames 0, 2, 4 (3 times)
        telemetry_logs: list[Any] = [
            record for record in caplog.records if "Telemetry Frame:" in record.message
        ]
        assert len(telemetry_logs) >= 3
