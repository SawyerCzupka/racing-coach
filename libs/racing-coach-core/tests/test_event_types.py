"""Tests for event type classes and data structures."""

from datetime import datetime

import pytest
from racing_coach_core.events.base import (
    Event,
    EventType,
    Handler,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.schemas.events import LapAndSession, TelemetryAndSession


@pytest.mark.unit
class TestEventType:
    """Test the EventType class."""

    def test_create_event_type(self):
        """Test creating an EventType with a name and data type."""
        event_type = EventType[str](name="TEST_EVENT", data_type=str)
        assert event_type.name == "TEST_EVENT"
        assert event_type.data_type == str

    def test_event_type_repr(self):
        """Test the string representation of EventType."""
        event_type = EventType[str](name="TEST_EVENT", data_type=str)
        assert repr(event_type) == "EventType<TEST_EVENT>"

    def test_event_type_frozen(self):
        """Test that EventType is immutable (frozen)."""
        event_type = EventType[str](name="TEST_EVENT", data_type=str)
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            event_type.name = "CHANGED"  # type: ignore

    def test_event_type_equality(self):
        """Test that EventTypes with the same values are equal."""
        event_type1 = EventType[str](name="TEST_EVENT", data_type=str)
        event_type2 = EventType[str](name="TEST_EVENT", data_type=str)
        assert event_type1 == event_type2

    def test_event_type_inequality(self):
        """Test that EventTypes with different values are not equal."""
        event_type1 = EventType[str](name="TEST_EVENT_1", data_type=str)
        event_type2 = EventType[str](name="TEST_EVENT_2", data_type=str)
        assert event_type1 != event_type2

    def test_event_type_with_complex_data_type(self):
        """Test creating an EventType with a complex data type."""
        event_type = EventType[dict](name="COMPLEX_EVENT", data_type=dict)
        assert event_type.name == "COMPLEX_EVENT"
        assert event_type.data_type == dict


@pytest.mark.unit
class TestSystemEvents:
    """Test the SystemEvents class."""

    def test_system_events_lap_telemetry_sequence(self):
        """Test that LAP_TELEMETRY_SEQUENCE is properly defined."""
        assert SystemEvents.LAP_TELEMETRY_SEQUENCE.name == "LAP_TELEMETRY_SEQUENCE"
        # data_type is type[T] which is a generic type parameter
        assert SystemEvents.LAP_TELEMETRY_SEQUENCE.data_type is not None

    def test_system_events_telemetry_frame(self):
        """Test that TELEMETRY_FRAME is properly defined."""
        assert SystemEvents.TELEMETRY_FRAME.name == "TELEMETRY_FRAME"
        # data_type is type[T] which is a generic type parameter
        assert SystemEvents.TELEMETRY_FRAME.data_type is not None

    def test_system_events_are_event_types(self):
        """Test that system events are instances of EventType."""
        assert isinstance(SystemEvents.LAP_TELEMETRY_SEQUENCE, EventType)
        assert isinstance(SystemEvents.TELEMETRY_FRAME, EventType)


@pytest.mark.unit
class TestEvent:
    """Test the Event class."""

    def test_create_event(self, sample_event_type: EventType[str]):
        """Test creating an Event with type and data."""
        event = Event(type=sample_event_type, data="test data")
        assert event.type == sample_event_type
        assert event.data == "test data"
        assert isinstance(event.timestamp, datetime)

    def test_event_timestamp_default(self, sample_event_type: EventType[str]):
        """Test that Event has a default timestamp."""
        event = Event(type=sample_event_type, data="test data")
        assert isinstance(event.timestamp, datetime)
        # Timestamp should be recent (within last second)
        now = datetime.now()
        assert (now - event.timestamp).total_seconds() < 1

    def test_event_with_custom_timestamp(self, sample_event_type: EventType[str]):
        """Test creating an Event with a custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        event = Event(type=sample_event_type, data="test data", timestamp=custom_time)
        assert event.timestamp == custom_time

    def test_event_frozen(self, sample_event_type: EventType[str]):
        """Test that Event is immutable (frozen)."""
        event = Event(type=sample_event_type, data="test data")
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            event.data = "changed"  # type: ignore

    def test_event_with_complex_data(self):
        """Test creating an Event with complex data types."""
        event_type = EventType[dict](name="COMPLEX", data_type=dict)
        complex_data = {"key1": "value1", "key2": [1, 2, 3]}
        event = Event(type=event_type, data=complex_data)
        assert event.data == complex_data

    def test_event_with_system_event_type(self, telemetry_and_session_factory):
        """Test creating an Event with a system event type."""
        # Create an instance from the factory
        telemetry_data = telemetry_and_session_factory()
        event = Event(type=SystemEvents.TELEMETRY_FRAME, data=telemetry_data)
        assert event.type == SystemEvents.TELEMETRY_FRAME
        assert isinstance(event.data, TelemetryAndSession)


@pytest.mark.unit
class TestHandlerContext:
    """Test the HandlerContext class."""

    def test_create_handler_context(self, event_bus, sample_event: Event[str]):
        """Test creating a HandlerContext."""
        context = HandlerContext(event_bus=event_bus, event=sample_event)
        assert context.event_bus is event_bus
        assert context.event is sample_event

    def test_handler_context_frozen(self, event_bus, sample_event: Event[str]):
        """Test that HandlerContext is immutable (frozen)."""
        context = HandlerContext(event_bus=event_bus, event=sample_event)
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            context.event = None  # type: ignore

    def test_handler_context_access_event_data(self, event_bus, sample_event: Event[str]):
        """Test accessing event data through HandlerContext."""
        context = HandlerContext(event_bus=event_bus, event=sample_event)
        assert context.event.data == "test data"
        assert context.event.type.name == "TEST_EVENT"


@pytest.mark.unit
class TestHandler:
    """Test the Handler class."""

    def test_create_handler(self, sample_event_type: EventType[str]):
        """Test creating a Handler."""

        def handler_func(context: HandlerContext[str]) -> None:
            pass

        handler = Handler(type=sample_event_type, fn=handler_func)
        assert handler.type == sample_event_type
        assert handler.fn is handler_func

    def test_handler_frozen(self, sample_event_type: EventType[str]):
        """Test that Handler is immutable (frozen)."""

        def handler_func(context: HandlerContext[str]) -> None:
            pass

        handler = Handler(type=sample_event_type, fn=handler_func)
        with pytest.raises(Exception):  # dataclass frozen=True raises FrozenInstanceError
            handler.type = None  # type: ignore

    def test_handler_callable(self, sample_event_type: EventType[str], event_bus):
        """Test that Handler function can be called."""
        called = []

        def handler_func(context: HandlerContext[str]) -> None:
            called.append(context.event.data)

        handler = Handler(type=sample_event_type, fn=handler_func)
        event = Event(type=sample_event_type, data="test data")
        context = HandlerContext(event_bus=event_bus, event=event)

        handler.fn(context)
        assert called == ["test data"]
