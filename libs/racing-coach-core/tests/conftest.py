"""Pytest configuration and shared fixtures."""

import asyncio
from typing import Any

import pytest
from pytest_factoryboy import register

from racing_coach_core.events.base import Event, EventBus, EventType
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


@pytest.fixture
def sample_event_type() -> EventType[str]:
    """Create a sample EventType for testing."""
    return EventType[str](name="TEST_EVENT", data_type=str)


@pytest.fixture
def sample_event(sample_event_type: EventType[str]) -> Event[str]:
    """Create a sample Event for testing."""
    return Event(type=sample_event_type, data="test data")


@pytest.fixture
def event_bus() -> EventBus:
    """Create a fresh EventBus instance for testing."""
    return EventBus(max_queue_size=100, max_workers=2)


@pytest.fixture
async def running_event_bus() -> EventBus:
    """Create and start an EventBus instance for integration testing."""
    bus = EventBus(max_queue_size=100, max_workers=2)
    bus.start()
    # Give the event bus time to start up
    await asyncio.sleep(0.1)
    yield bus
    bus.stop()
    # Give the event bus time to shut down
    await asyncio.sleep(0.1)


@pytest.fixture
def event_collector() -> dict[str, list[Any]]:
    """Create a dictionary to collect events during tests."""
    return {"events": []}
