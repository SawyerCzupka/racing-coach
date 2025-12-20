"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from polyfactory.pytest_plugin import register_fixture
from racing_coach_core.events.base import Event, EventBus, EventType

from tests.factories import (
    BrakingMetricsFactory,
    CornerMetricsFactory,
    LapAndSessionFactory,
    LapMetricsFactory,
    LapTelemetryFactory,
    SessionFrameFactory,
    TelemetryAndSessionFactory,
    TelemetryFrameFactory,
)
from tests.load_test_utils import (
    LatencyTrackingCollector,
    LoadTestConfig,
)

# Register factories to create pytest fixtures automatically
register_fixture(TelemetryFrameFactory)
register_fixture(SessionFrameFactory)
register_fixture(LapTelemetryFactory)
register_fixture(TelemetryAndSessionFactory)
register_fixture(LapAndSessionFactory)
register_fixture(BrakingMetricsFactory)
register_fixture(CornerMetricsFactory)
register_fixture(LapMetricsFactory)


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
async def running_event_bus() -> AsyncGenerator[EventBus, None]:
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


# ============================================================================
# Load Test Fixtures
# ============================================================================


@pytest.fixture
def load_test_config() -> LoadTestConfig:
    """Default configuration for load tests."""
    return LoadTestConfig(
        frequency_hz=60.0,
        duration_seconds=5.0,
        max_latency_threshold_ms=100.0,
        max_memory_growth_mb=50.0,
        max_dropped_event_pct=0.01,
    )


@pytest.fixture
def latency_collector() -> LatencyTrackingCollector:
    """Create a latency-tracking event collector."""
    return LatencyTrackingCollector()


@pytest.fixture
def high_capacity_event_bus() -> EventBus:
    """Create an EventBus with higher capacity for load testing."""
    return EventBus(max_queue_size=10000, max_workers=4)


@pytest.fixture
async def running_high_capacity_bus() -> AsyncGenerator[EventBus, None]:
    """Create and start a high-capacity EventBus for load testing."""
    bus = EventBus(max_queue_size=10000, max_workers=4)
    bus.start()
    await asyncio.sleep(0.1)
    yield bus
    bus.stop()
    await asyncio.sleep(0.1)
