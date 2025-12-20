"""Load and stress tests for EventBus.

These tests verify that the EventBus can handle high-frequency event streams
(60Hz+) without dropping events, excessive latency, or unbounded memory growth.

Run with: uv run pytest -m load -v -s
Skip in CI with: uv run pytest -m "not load"
"""

import asyncio
import time
from typing import Any
from uuid import uuid4

import pytest
from racing_coach_core.events.base import EventBus, Handler, HandlerContext, SystemEvents

from tests.load_test_utils import (
    HighFrequencyEventGenerator,
    LatencyTrackingCollector,
    LoadTestConfig,
    QueueMonitor,
    find_breaking_point,
    measure_event_creation_overhead,
    run_load_test,
)


@pytest.mark.load
@pytest.mark.slow
class TestEventCreationOverhead:
    """Tests focused on TelemetryFrame/Event creation performance."""

    def test_telemetry_frame_creation_overhead(self) -> None:
        """
        Measure TelemetryFrame creation overhead (Pydantic validation).

        At 60Hz, each frame creation must complete in <16.6ms to keep up.
        We target <5ms avg for headroom.
        """
        avg_ms, p99_ms, max_ms = measure_event_creation_overhead(num_events=1000)

        print("\nTelemetryFrame Creation Overhead (1000 events):")
        print(f"  Avg: {avg_ms:.3f}ms")
        print(f"  P99: {p99_ms:.3f}ms")
        print(f"  Max: {max_ms:.3f}ms")

        # At 60Hz, we have 16.6ms per frame - allow up to 5ms for creation
        assert avg_ms < 5.0, f"Average creation time {avg_ms:.3f}ms exceeds 5ms threshold"
        assert p99_ms < 10.0, f"P99 creation time {p99_ms:.3f}ms exceeds 10ms threshold"

    def test_sustained_event_creation(self) -> None:
        """Test sustained event creation to detect memory leaks or GC pauses."""
        # Create 6000 events (100 seconds at 60Hz equivalent)
        avg_ms, p99_ms, max_ms = measure_event_creation_overhead(num_events=6000)

        print("\nSustained TelemetryFrame Creation (6000 events):")
        print(f"  Avg: {avg_ms:.3f}ms")
        print(f"  P99: {p99_ms:.3f}ms")
        print(f"  Max: {max_ms:.3f}ms (likely includes GC)")

        assert avg_ms < 5.0, f"Average creation time {avg_ms:.3f}ms exceeds 5ms threshold"


@pytest.mark.load
@pytest.mark.slow
class TestEventBusUnderLoad:
    """Test EventBus behavior under sustained high-frequency load."""

    async def test_60hz_sustained_load(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """
        Test EventBus handling 60Hz event stream (simulating iRacing telemetry).

        Verifies:
        - No events dropped
        - Latency stays under 100ms
        - Memory doesn't grow unbounded
        """
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        running_high_capacity_bus.register_handler(handler)
        await asyncio.sleep(0.1)

        config = LoadTestConfig(
            frequency_hz=60.0,
            duration_seconds=10.0,
            max_latency_threshold_ms=100.0,
        )
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print(metrics.summary())

        assert metrics.events_dropped == 0, f"Dropped {metrics.events_dropped} events"
        assert metrics.p99_latency_ms < 100.0, (
            f"P99 latency {metrics.p99_latency_ms:.2f}ms exceeds 100ms"
        )
        assert metrics.memory_growth < 50 * 1024 * 1024, (
            f"Memory grew by {metrics.memory_growth / 1024 / 1024:.2f}MB"
        )

    async def test_120hz_burst_load(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Test EventBus handling 120Hz burst (2x normal rate)."""
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        running_high_capacity_bus.register_handler(handler)
        await asyncio.sleep(0.1)

        config = LoadTestConfig(
            frequency_hz=120.0,
            duration_seconds=5.0,
            max_latency_threshold_ms=150.0,
        )
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print(metrics.summary())

        drop_rate = metrics.events_dropped / max(1, metrics.events_published)
        assert drop_rate < 0.01, f"Drop rate {drop_rate:.2%} exceeds 1%"
        assert metrics.p99_latency_ms < 150.0, (
            f"P99 latency {metrics.p99_latency_ms:.2f}ms exceeds 150ms"
        )

    async def test_queue_depth_under_load(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Test that queue depth stays bounded under sustained load."""
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        running_high_capacity_bus.register_handler(handler)

        queue_monitor = QueueMonitor(running_high_capacity_bus, sample_interval_ms=50.0)
        queue_monitor.start()

        generator = HighFrequencyEventGenerator(
            running_high_capacity_bus, uuid4(), frequency_hz=60.0
        )
        generator.start(duration_seconds=5.0)
        generator.wait()

        await asyncio.sleep(1.0)  # Allow queue to drain
        queue_monitor.stop()

        samples = queue_monitor.get_samples()
        max_depth = max(samples) if samples else 0
        avg_depth = sum(samples) / len(samples) if samples else 0

        print("\nQueue Depth Analysis:")
        print(f"  Max: {max_depth}")
        print(f"  Avg: {avg_depth:.1f}")
        print(f"  Samples: {len(samples)}")

        # Queue should stay well below capacity (10000)
        assert max_depth < running_high_capacity_bus._max_queue_size * 0.5, (  # pyright: ignore[reportPrivateUsage]
            f"Queue depth {max_depth} exceeds 50% of capacity"
        )


@pytest.mark.load
@pytest.mark.slow
class TestEventBusLatencyMetrics:
    """Tests focused on latency measurement and thresholds."""

    async def test_latency_distribution_at_60hz(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Measure and report full latency distribution at 60Hz."""
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        running_high_capacity_bus.register_handler(handler)

        config = LoadTestConfig(frequency_hz=60.0, duration_seconds=10.0)
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print("\nLatency Distribution at 60Hz:")
        print(f"  Min: {metrics.min_latency_ms:.2f}ms")
        print(f"  Avg: {metrics.avg_latency_ms:.2f}ms")
        print(f"  P50: {metrics.p50_latency_ms:.2f}ms")
        print(f"  P95: {metrics.p95_latency_ms:.2f}ms")
        print(f"  P99: {metrics.p99_latency_ms:.2f}ms")
        print(f"  Max: {metrics.max_latency_ms:.2f}ms")

        assert metrics.avg_latency_ms < 50.0, "Average latency too high"
        assert metrics.p95_latency_ms < 100.0, "P95 latency too high"

    async def test_slow_handler_impact(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Test impact of a slow handler on overall latency."""

        def slow_handler(context: HandlerContext[Any]) -> None:
            time.sleep(0.05)  # 50ms delay

        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=slow_handler)
        )
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        )

        config = LoadTestConfig(frequency_hz=60.0, duration_seconds=5.0)
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print("\nWith 50ms slow handler:")
        print(f"  P99 Latency: {metrics.p99_latency_ms:.2f}ms")
        print(f"  Max Queue: {metrics.max_queue_size}")
        print(f"  Dropped: {metrics.events_dropped}")
        print(f"  Events/sec: {metrics.events_per_second:.1f}")

        # With a 50ms slow handler and parallel execution, we expect increased latency
        # but the fast collector should still work. Queue will grow.


@pytest.mark.load
@pytest.mark.slow
class TestEventBusMemory:
    """Tests focused on memory behavior under load."""

    async def test_memory_stability_long_run(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Test memory doesn't grow unbounded during long runs (30s at 60Hz)."""
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        running_high_capacity_bus.register_handler(handler)

        config = LoadTestConfig(
            frequency_hz=60.0,
            duration_seconds=30.0,
            max_memory_growth_mb=100.0,
        )
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        memory_growth_mb = metrics.memory_growth / 1024 / 1024
        print("\nMemory after 30s at 60Hz:")
        print(f"  Start: {metrics.memory_start / 1024 / 1024:.2f}MB")
        print(f"  Peak: {metrics.memory_peak / 1024 / 1024:.2f}MB")
        print(f"  End: {metrics.memory_end / 1024 / 1024:.2f}MB")
        print(f"  Growth: {memory_growth_mb:.2f}MB")

        assert memory_growth_mb < 100.0, f"Memory grew by {memory_growth_mb:.2f}MB"


@pytest.mark.load
@pytest.mark.slow
class TestEventBusBreakingPoint:
    """Tests to find the system's breaking point."""

    async def test_find_max_sustainable_frequency(self) -> None:
        """Progressively increase event frequency until system breaks."""

        def bus_factory() -> EventBus:
            return EventBus(max_queue_size=10000, max_workers=4)

        max_freq, final_metrics = find_breaking_point(
            bus_factory,
            start_frequency=60.0,
            max_frequency=2000.0,
            step_multiplier=1.5,
            test_duration=5.0,
            latency_threshold_ms=100.0,
        )

        print("\nBreaking Point Analysis:")
        print(f"  Max Sustainable Frequency: {max_freq:.1f}Hz")
        print(f"  Final Test Frequency: {final_metrics.events_per_second:.1f} events/sec actual")
        print(f"  Final P99 Latency: {final_metrics.p99_latency_ms:.2f}ms")
        print(f"  Final Drop Rate: {final_metrics.events_dropped}/{final_metrics.events_published}")

        assert max_freq >= 60.0, f"Cannot sustain 60Hz, max was {max_freq}Hz"

    async def test_queue_overflow_behavior(self) -> None:
        """Test behavior when queue overflows (small queue + fast events)."""
        bus = EventBus(max_queue_size=100, max_workers=2)
        bus.start()
        await asyncio.sleep(0.1)

        collector = LatencyTrackingCollector()

        def slow_handler(context: HandlerContext[Any]) -> None:
            time.sleep(0.1)  # 100ms delay - will cause queue buildup
            collector.collect(context)

        bus.register_handler(Handler(type=SystemEvents.TELEMETRY_EVENT, fn=slow_handler))

        config = LoadTestConfig(frequency_hz=200.0, duration_seconds=3.0)
        metrics = run_load_test(bus, collector, config)

        bus.stop()

        print("\nQueue Overflow Test (small queue + fast events):")
        print(f"  Published: {metrics.events_published}")
        print(f"  Received: {metrics.events_received}")
        print(f"  Dropped: {metrics.events_dropped}")
        print(f"  Max Queue: {metrics.max_queue_size}")

        # With 100-item queue and 200Hz events going to a 100ms handler,
        # queue will fill up quickly and events will be lost
        # This test documents the overflow behavior


@pytest.mark.load
@pytest.mark.slow
class TestEventBusMultipleHandlers:
    """Tests for multiple handler scenarios under load."""

    async def test_multiple_handlers_at_60hz(
        self,
        running_high_capacity_bus: EventBus,
    ) -> None:
        """Test EventBus with multiple handlers at 60Hz."""
        collectors = [LatencyTrackingCollector() for _ in range(3)]

        for collector in collectors:
            handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=collector.collect)
            running_high_capacity_bus.register_handler(handler)

        await asyncio.sleep(0.1)

        config = LoadTestConfig(frequency_hz=60.0, duration_seconds=5.0)
        # Use first collector for metrics
        metrics = run_load_test(running_high_capacity_bus, collectors[0], config)

        print("\n3 Handlers at 60Hz:")
        print(f"  Events published: {metrics.events_published}")
        for i, collector in enumerate(collectors):
            print(f"  Handler {i + 1} received: {collector.get_event_count()}")
        print(f"  P99 Latency: {metrics.p99_latency_ms:.2f}ms")

        # All handlers should receive same number of events
        for i, collector in enumerate(collectors):
            count = collector.get_event_count()
            assert count == metrics.events_published, (
                f"Handler {i + 1} received {count}, expected {metrics.events_published}"
            )
