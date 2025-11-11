"""Tests for the EventBus class."""

import asyncio
import time
from typing import Any

import pytest
from racing_coach_core.events.base import (
    Event,
    EventBus,
    EventType,
    Handler,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.models.events import TelemetryAndSession


@pytest.mark.unit
class TestEventBusInitialization:
    """Test EventBus initialization and configuration."""

    def test_create_event_bus_default(self):
        """Test creating an EventBus with default parameters."""
        bus = EventBus()
        assert not bus.is_running()
        assert bus._max_queue_size == 1000  # type: ignore
        assert bus._thread_pool is not None  # type: ignore

    def test_create_event_bus_custom_params(self):
        """Test creating an EventBus with custom parameters."""
        bus = EventBus(max_queue_size=500, max_workers=4, thread_name_prefix="TestHandler")
        assert not bus.is_running()
        assert bus._max_queue_size == 500  # type: ignore
        assert bus._thread_pool._thread_name_prefix == "TestHandler"  # type: ignore

    def test_event_bus_initial_state(self):
        """Test that EventBus starts in the correct initial state."""
        bus = EventBus()
        assert bus._handlers == {}  # type: ignore
        assert not bus.is_running()
        assert bus._loop is None  # type: ignore


@pytest.mark.unit
class TestEventBusSubscription:
    """Test EventBus subscription and unsubscription."""

    def test_subscribe_handler(self, event_bus: EventBus, sample_event_type: EventType[str]):
        """Test subscribing a handler to an event type."""

        def handler(context: HandlerContext[str]) -> None:
            pass

        event_bus.subscribe(sample_event_type, handler)
        assert sample_event_type in event_bus._handlers  # type: ignore
        assert handler in event_bus._handlers[sample_event_type]  # type: ignore

    def test_subscribe_multiple_handlers(
        self, event_bus: EventBus, sample_event_type: EventType[str]
    ):
        """Test subscribing multiple handlers to the same event type."""

        def handler1(context: HandlerContext[str]) -> None:
            pass

        def handler2(context: HandlerContext[str]) -> None:
            pass

        event_bus.subscribe(sample_event_type, handler1)
        event_bus.subscribe(sample_event_type, handler2)

        assert len(event_bus._handlers[sample_event_type]) == 2  # type: ignore
        assert handler1 in event_bus._handlers[sample_event_type]  # type: ignore
        assert handler2 in event_bus._handlers[sample_event_type]  # type: ignore

    def test_subscribe_same_handler_twice(
        self, event_bus: EventBus, sample_event_type: EventType[str]
    ):
        """Test that subscribing the same handler twice does not duplicate it."""

        def handler(context: HandlerContext[str]) -> None:
            pass

        event_bus.subscribe(sample_event_type, handler)
        event_bus.subscribe(sample_event_type, handler)

        assert len(event_bus._handlers[sample_event_type]) == 1  # type: ignore

    def test_unsubscribe_handler(self, event_bus: EventBus, sample_event_type: EventType[str]):
        """Test unsubscribing a handler from an event type."""

        def handler(context: HandlerContext[str]) -> None:
            pass

        event_bus.subscribe(sample_event_type, handler)
        event_bus.unsubscribe(sample_event_type, handler)

        assert len(event_bus._handlers[sample_event_type]) == 0  # type: ignore

    def test_unsubscribe_nonexistent_handler(
        self, event_bus: EventBus, sample_event_type: EventType[str]
    ):
        """Test unsubscribing a handler that was never subscribed."""

        def handler(context: HandlerContext[str]) -> None:
            pass

        # Should not raise an error
        event_bus.unsubscribe(sample_event_type, handler)

    def test_subscribe_to_multiple_event_types(self, event_bus: EventBus):
        """Test subscribing handlers to different event types."""
        event_type1 = EventType[str](name="EVENT_1", data_type=str)
        event_type2 = EventType[int](name="EVENT_2", data_type=int)

        def handler1(context: HandlerContext[str]) -> None:
            pass

        def handler2(context: HandlerContext[int]) -> None:
            pass

        event_bus.subscribe(event_type1, handler1)
        event_bus.subscribe(event_type2, handler2)

        assert event_type1 in event_bus._handlers  # type: ignore
        assert event_type2 in event_bus._handlers  # type: ignore
        assert handler1 in event_bus._handlers[event_type1]  # type: ignore
        assert handler2 in event_bus._handlers[event_type2]  # type: ignore


@pytest.mark.unit
class TestEventBusHandlerRegistration:
    """Test EventBus handler registration methods."""

    def test_register_handler(self, event_bus: EventBus, sample_event_type: EventType[str]):
        """Test registering a Handler object."""

        def handler_func(context: HandlerContext[str]) -> None:
            pass

        handler = Handler(type=sample_event_type, fn=handler_func)
        event_bus.register_handler(handler)

        assert sample_event_type in event_bus._handlers  # type: ignore
        assert handler_func in event_bus._handlers[sample_event_type]  # type: ignore

    def test_register_multiple_handlers(
        self, event_bus: EventBus, sample_event_type: EventType[str]
    ):
        """Test registering multiple Handler objects."""

        def handler_func1(context: HandlerContext[str]) -> None:
            pass

        def handler_func2(context: HandlerContext[str]) -> None:
            pass

        handler1 = Handler(type=sample_event_type, fn=handler_func1)
        handler2 = Handler(type=sample_event_type, fn=handler_func2)

        event_bus.register_handler(handler1)
        event_bus.register_handler(handler2)

        assert len(event_bus._handlers[sample_event_type]) == 2  # type: ignore

    def test_register_handlers_list(self, event_bus: EventBus, sample_event_type: EventType[str]):
        """Test registering a list of Handler objects."""

        def handler_func1(context: HandlerContext[str]) -> None:
            pass

        def handler_func2(context: HandlerContext[str]) -> None:
            pass

        handlers = [
            Handler(type=sample_event_type, fn=handler_func1),
            Handler(type=sample_event_type, fn=handler_func2),
        ]

        event_bus.register_handlers(handlers)

        assert len(event_bus._handlers[sample_event_type]) == 2  # type: ignore


@pytest.mark.unit
class TestEventBusStartStop:
    """Test EventBus start and stop functionality."""

    def test_start_event_bus(self, event_bus: EventBus):
        """Test starting the event bus."""
        event_bus.start()
        time.sleep(0.1)  # Give it time to start
        assert event_bus.is_running()
        event_bus.stop()

    def test_start_event_bus_twice(self, event_bus: EventBus):
        """Test that starting an already running event bus does nothing."""
        event_bus.start()
        time.sleep(0.1)
        event_bus.start()  # Should not raise an error
        assert event_bus.is_running()
        event_bus.stop()

    def test_stop_event_bus(self, event_bus: EventBus):
        """Test stopping the event bus."""
        event_bus.start()
        time.sleep(0.1)
        event_bus.stop()
        assert not event_bus.is_running()

    def test_stop_event_bus_not_running(self, event_bus: EventBus):
        """Test stopping an event bus that is not running."""
        # Should not raise an error
        event_bus.stop()


@pytest.mark.integration
class TestEventBusPublishIntegration:
    """Integration tests for EventBus publish functionality."""

    async def test_publish_event(self, running_event_bus: EventBus):
        """Test publishing an event to the bus."""
        event_type = EventType[str](name="TEST", data_type=str)
        event = Event(type=event_type, data="test data")

        await running_event_bus.publish(event)
        # Give the queue time to process
        await asyncio.sleep(0.1)

    async def test_publish_event_not_running(self, event_bus: EventBus):
        """Test that publishing to a non-running bus raises an error."""
        event_type = EventType[str](name="TEST", data_type=str)
        event = Event(type=event_type, data="test data")

        with pytest.raises(RuntimeError, match="Event bus not running"):
            await event_bus.publish(event)

    async def test_handler_receives_event(self, running_event_bus: EventBus):
        """Test that a subscribed handler receives published events."""
        event_type = EventType[str](name="TEST", data_type=str)
        received_data = []

        def handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type, handler)

        event = Event(type=event_type, data="test data")
        await running_event_bus.publish(event)

        # Wait for the event to be processed
        await asyncio.sleep(0.2)

        assert len(received_data) == 1
        assert received_data[0] == "test data"

    async def test_multiple_handlers_receive_event(self, running_event_bus: EventBus):
        """Test that multiple handlers receive the same event."""
        event_type = EventType[str](name="TEST", data_type=str)
        received_data1 = []
        received_data2 = []

        def handler1(context: HandlerContext[str]) -> None:
            received_data1.append(context.event.data)

        def handler2(context: HandlerContext[str]) -> None:
            received_data2.append(context.event.data)

        running_event_bus.subscribe(event_type, handler1)
        running_event_bus.subscribe(event_type, handler2)

        event = Event(type=event_type, data="test data")
        await running_event_bus.publish(event)

        # Wait for events to be processed
        await asyncio.sleep(0.2)

        assert received_data1 == ["test data"]
        assert received_data2 == ["test data"]

    async def test_handler_not_called_for_different_event_type(self, running_event_bus: EventBus):
        """Test that handlers are only called for their subscribed event types."""
        event_type1 = EventType[str](name="TYPE_1", data_type=str)
        event_type2 = EventType[str](name="TYPE_2", data_type=str)
        received_data = []

        def handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type1, handler)

        event = Event(type=event_type2, data="test data")
        await running_event_bus.publish(event)

        # Wait to ensure no processing happens
        await asyncio.sleep(0.2)

        assert len(received_data) == 0

    async def test_publish_multiple_events(self, running_event_bus: EventBus):
        """Test publishing multiple events in sequence."""
        event_type = EventType[str](name="TEST", data_type=str)
        received_data = []

        def handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type, handler)

        for i in range(5):
            event = Event(type=event_type, data=f"data_{i}")
            await running_event_bus.publish(event)

        # Wait for all events to be processed
        await asyncio.sleep(0.3)

        assert len(received_data) == 5
        assert received_data == [f"data_{i}" for i in range(5)]

    @pytest.mark.slow
    async def test_handler_exception_does_not_stop_processing(self, running_event_bus: EventBus):
        """Test that an exception in one handler doesn't stop other handlers."""
        event_type = EventType[str](name="TEST", data_type=str)
        received_data = []

        def failing_handler(context: HandlerContext[str]) -> None:
            raise ValueError("Handler failed")

        def success_handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type, failing_handler)
        running_event_bus.subscribe(event_type, success_handler)

        event = Event(type=event_type, data="test data")
        await running_event_bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.2)

        # The success handler should still have been called
        assert received_data == ["test data"]


@pytest.mark.integration
class TestEventBusThreadSafePublish:
    """Integration tests for thread-safe publishing."""

    async def test_thread_safe_publish(self, running_event_bus: EventBus):
        """Test thread-safe publishing from a different thread."""
        event_type = EventType[str](name="TEST", data_type=str)
        received_data = []

        def handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type, handler)

        event = Event(type=event_type, data="thread data")

        # Call thread_safe_publish (would normally be called from a different thread)
        running_event_bus.thread_safe_publish(event)

        # Wait for event to be processed
        await asyncio.sleep(0.2)

        assert received_data == ["thread data"]

    async def test_thread_safe_publish_not_running(self, event_bus: EventBus):
        """Test that thread-safe publishing to a non-running bus raises an error."""
        event_type = EventType[str](name="TEST", data_type=str)
        event = Event(type=event_type, data="test data")

        with pytest.raises(RuntimeError, match="Event bus not running"):
            event_bus.thread_safe_publish(event)


@pytest.mark.integration
class TestEventBusWithSystemEvents:
    """Integration tests using system event types."""

    async def test_publish_telemetry_frame_event(
        self, running_event_bus: EventBus, telemetry_and_session_factory
    ):
        """Test publishing a TELEMETRY_FRAME system event."""
        received_events = []

        def handler(context: HandlerContext[TelemetryAndSession]) -> None:
            received_events.append(context.event.data)

        running_event_bus.subscribe(SystemEvents.TELEMETRY_FRAME, handler)

        telemetry_data = telemetry_and_session_factory()
        event = Event(type=SystemEvents.TELEMETRY_FRAME, data=telemetry_data)
        await running_event_bus.publish(event)

        await asyncio.sleep(0.2)

        assert len(received_events) == 1
        assert isinstance(received_events[0], TelemetryAndSession)

    async def test_handler_accesses_telemetry_data(
        self, running_event_bus: EventBus, telemetry_and_session_factory
    ):
        """Test that handlers can access telemetry data from events."""
        accessed_data = {}

        def handler(context: HandlerContext[TelemetryAndSession]) -> None:
            telemetry = context.event.data.TelemetryFrame
            accessed_data["speed"] = telemetry.speed
            accessed_data["lap_number"] = telemetry.lap_number

        running_event_bus.subscribe(SystemEvents.TELEMETRY_FRAME, handler)

        telemetry_data = telemetry_and_session_factory()
        event = Event(type=SystemEvents.TELEMETRY_FRAME, data=telemetry_data)
        await running_event_bus.publish(event)

        await asyncio.sleep(0.2)

        assert "speed" in accessed_data
        assert "lap_number" in accessed_data
        assert accessed_data["speed"] == telemetry_data.TelemetryFrame.speed
        assert accessed_data["lap_number"] == telemetry_data.TelemetryFrame.lap_number


@pytest.mark.integration
@pytest.mark.slow
class TestEventBusPerformance:
    """Performance and stress tests for EventBus."""

    async def test_high_volume_events(self, running_event_bus: EventBus):
        """Test handling a high volume of events."""
        event_type = EventType[int](name="COUNTER", data_type=int)
        received_count = [0]

        def handler(context: HandlerContext[int]) -> None:
            received_count[0] += 1

        running_event_bus.subscribe(event_type, handler)

        # Publish 100 events
        num_events = 100
        for i in range(num_events):
            event = Event(type=event_type, data=i)
            await running_event_bus.publish(event)

        # Wait for all events to be processed
        await asyncio.sleep(1.0)

        assert received_count[0] == num_events

    async def test_concurrent_publishing(self, running_event_bus: EventBus):
        """Test publishing events concurrently from multiple coroutines."""
        event_type = EventType[str](name="CONCURRENT", data_type=str)
        received_data = []

        def handler(context: HandlerContext[str]) -> None:
            received_data.append(context.event.data)

        running_event_bus.subscribe(event_type, handler)

        async def publish_events(prefix: str, count: int):
            for i in range(count):
                event = Event(type=event_type, data=f"{prefix}_{i}")
                await running_event_bus.publish(event)

        # Run multiple publishers concurrently
        await asyncio.gather(
            publish_events("task1", 10),
            publish_events("task2", 10),
            publish_events("task3", 10),
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        assert len(received_data) == 30
