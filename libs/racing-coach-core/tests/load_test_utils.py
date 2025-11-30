"""Utilities for load and stress testing the event system.

This module provides tools to measure:
- Event creation overhead (TelemetryFrame/Pydantic validation)
- Event handling throughput (publish -> handler execution)
- Memory consumption under sustained load
- Queue depth and backpressure behavior
"""

from __future__ import annotations

import gc
import statistics
import threading
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from racing_coach_core.events.base import (
    Event,
    EventBus,
    Handler,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.models.events import TelemetryAndSessionId
from racing_coach_core.models.telemetry import TelemetryFrame

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""

    # Event counts
    events_published: int = 0
    events_received: int = 0
    events_dropped: int = 0

    # Timing metrics (in milliseconds)
    latencies: list[float] = field(default_factory=list)
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Event creation metrics (in milliseconds)
    creation_times: list[float] = field(default_factory=list)
    avg_creation_time_ms: float = 0.0
    p99_creation_time_ms: float = 0.0

    # Throughput
    duration_seconds: float = 0.0
    events_per_second: float = 0.0

    # Memory metrics (in bytes)
    memory_start: int = 0
    memory_peak: int = 0
    memory_end: int = 0
    memory_growth: int = 0

    # Queue metrics
    queue_size_samples: list[int] = field(default_factory=list)
    max_queue_size: int = 0
    avg_queue_size: float = 0.0
    queue_overflow_count: int = 0

    # Failure flags
    had_latency_violations: bool = False
    had_memory_growth: bool = False
    had_dropped_events: bool = False

    def calculate_percentiles(self) -> None:
        """Calculate latency percentiles from collected latencies."""
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            n = len(sorted_latencies)
            self.min_latency_ms = sorted_latencies[0]
            self.max_latency_ms = sorted_latencies[-1]
            self.avg_latency_ms = statistics.mean(sorted_latencies)
            self.p50_latency_ms = sorted_latencies[int(n * 0.50)]
            self.p95_latency_ms = sorted_latencies[int(n * 0.95)]
            self.p99_latency_ms = sorted_latencies[min(int(n * 0.99), n - 1)]

        if self.creation_times:
            sorted_creation = sorted(self.creation_times)
            n = len(sorted_creation)
            self.avg_creation_time_ms = statistics.mean(sorted_creation)
            self.p99_creation_time_ms = sorted_creation[min(int(n * 0.99), n - 1)]

        if self.queue_size_samples:
            self.max_queue_size = max(self.queue_size_samples)
            self.avg_queue_size = statistics.mean(self.queue_size_samples)

    def summary(self) -> str:
        """Return a formatted summary of metrics."""
        drop_rate = (
            self.events_dropped / self.events_published * 100 if self.events_published > 0 else 0
        )
        return f"""
Load Test Results:
  Events: {self.events_received}/{self.events_published} ({drop_rate:.2f}% dropped)
  Duration: {self.duration_seconds:.2f}s
  Throughput: {self.events_per_second:.1f} events/sec

  Latency (publish -> handler):
    Min: {self.min_latency_ms:.2f}ms
    Avg: {self.avg_latency_ms:.2f}ms
    P50: {self.p50_latency_ms:.2f}ms
    P95: {self.p95_latency_ms:.2f}ms
    P99: {self.p99_latency_ms:.2f}ms
    Max: {self.max_latency_ms:.2f}ms

  Event Creation:
    Avg: {self.avg_creation_time_ms:.3f}ms
    P99: {self.p99_creation_time_ms:.3f}ms

  Memory:
    Start: {self.memory_start / 1024 / 1024:.2f}MB
    Peak: {self.memory_peak / 1024 / 1024:.2f}MB
    Growth: {self.memory_growth / 1024 / 1024:.2f}MB

  Queue:
    Max Depth: {self.max_queue_size}
    Avg Depth: {self.avg_queue_size:.1f}

  Failures: latency={self.had_latency_violations}, memory={self.had_memory_growth}, dropped={self.had_dropped_events}
"""


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    # Event generation
    frequency_hz: float = 60.0  # Events per second
    duration_seconds: float = 10.0

    # Thresholds
    max_latency_threshold_ms: float = 100.0
    max_memory_growth_mb: float = 100.0
    max_dropped_event_pct: float = 0.01  # 1%

    # Queue configuration
    queue_size: int = 1000
    worker_count: int | None = None

    # Monitoring
    sample_queue_interval_ms: float = 100.0


class LatencyTrackingCollector:
    """
    Event collector that tracks latency between publish and receive.

    Uses event timestamps to measure end-to-end latency.
    """

    def __init__(self) -> None:
        self.receive_times: dict[datetime, float] = {}
        self.events: list[Event[Any]] = []
        self._lock = threading.Lock()
        self.count = 0

    def collect(self, context: HandlerContext[Any]) -> None:
        """Handler function that records receive time."""
        receive_time = time.perf_counter()
        with self._lock:
            self.events.append(context.event)
            self.receive_times[context.event.timestamp] = receive_time
            self.count += 1

    def get_event_count(self) -> int:
        with self._lock:
            return self.count

    def clear(self) -> None:
        with self._lock:
            self.events.clear()
            self.receive_times.clear()
            self.count = 0


def create_telemetry_frame(index: int, frequency_hz: float = 60.0) -> TelemetryFrame:
    """Create a telemetry frame with sequential data.

    This is extracted as a separate function to allow measuring creation overhead.
    """
    lap_number = (index // 3600) + 1  # New lap every ~60 seconds at 60Hz
    lap_pct = (index % 3600) / 3600.0

    return TelemetryFrame(
        timestamp=datetime.now(timezone.utc),
        session_time=index / frequency_hz,
        lap_number=lap_number,
        lap_distance_pct=lap_pct,
        lap_distance=lap_pct * 5000,
        current_lap_time=(index % 3600) / frequency_hz,
        last_lap_time=90.0,
        best_lap_time=88.5,
        speed=50.0 + (index % 50),
        rpm=5000 + (index % 3000),
        gear=3 + (index % 4),
        throttle=0.8,
        brake=0.0,
        clutch=0.0,
        steering_angle=0.1,
        lateral_acceleration=1.5,
        longitudinal_acceleration=0.5,
        vertical_acceleration=0.0,
        yaw_rate=0.1,
        roll_rate=0.0,
        pitch_rate=0.0,
        velocity_x=50.0,
        velocity_y=0.0,
        velocity_z=0.0,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
        latitude=0.0,
        longitude=0.0,
        altitude=0.0,
        tire_temps={
            "LF": {"left": 80.0, "middle": 85.0, "right": 82.0},
            "RF": {"left": 81.0, "middle": 86.0, "right": 83.0},
            "LR": {"left": 78.0, "middle": 83.0, "right": 80.0},
            "RR": {"left": 79.0, "middle": 84.0, "right": 81.0},
        },
        tire_wear={
            "LF": {"left": 0.95, "middle": 0.93, "right": 0.94},
            "RF": {"left": 0.94, "middle": 0.92, "right": 0.93},
            "LR": {"left": 0.96, "middle": 0.94, "right": 0.95},
            "RR": {"left": 0.95, "middle": 0.93, "right": 0.94},
        },
        brake_line_pressure={"LF": 0.0, "RF": 0.0, "LR": 0.0, "RR": 0.0},
        track_temp=30.0,
        track_wetness=0,
        air_temp=25.0,
        session_flags=0,
        track_surface=3,
        on_pit_road=False,
    )


class HighFrequencyEventGenerator:
    """
    Generates telemetry events at a specified frequency.

    Simulates the TelemetryCollector publishing events at 60Hz or higher.
    Tracks both event creation time and publish time for latency measurement.
    """

    def __init__(
        self,
        event_bus: EventBus,
        session_id: UUID,
        frequency_hz: float = 60.0,
    ) -> None:
        self.event_bus = event_bus
        self.session_id = session_id
        self.frequency_hz = frequency_hz
        self._running = False
        self._thread: threading.Thread | None = None
        self._events_published = 0
        self._publish_times: dict[datetime, float] = {}
        self._creation_times: list[float] = []
        self._lock = threading.Lock()

    def _generation_loop(self, num_events: int) -> None:
        """Main loop for generating events."""
        interval = 1.0 / self.frequency_hz

        for i in range(num_events):
            if not self._running:
                break

            loop_start = time.perf_counter()

            # Measure event creation time (Pydantic validation overhead)
            creation_start = time.perf_counter()
            frame = create_telemetry_frame(i, self.frequency_hz)
            creation_end = time.perf_counter()
            creation_time_ms = (creation_end - creation_start) * 1000

            with self._lock:
                self._creation_times.append(creation_time_ms)

            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(
                    telemetry=frame,
                    session_id=self.session_id,
                ),
            )

            publish_time = time.perf_counter()
            with self._lock:
                self._publish_times[event.timestamp] = publish_time

            try:
                self.event_bus.thread_safe_publish(event)
                with self._lock:
                    self._events_published += 1
            except RuntimeError:
                pass  # Queue full or bus stopped

            # Maintain frequency
            elapsed = time.perf_counter() - loop_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self, duration_seconds: float) -> None:
        """Start generating events for the specified duration."""
        if self._running:
            return

        self._running = True
        num_events = int(duration_seconds * self.frequency_hz)

        self._thread = threading.Thread(
            target=self._generation_loop,
            args=(num_events,),
            name="EventGenerator",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop generating events."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def wait(self, timeout: float | None = None) -> None:
        """Wait for generation to complete."""
        if self._thread:
            self._thread.join(timeout=timeout)

    def get_events_published(self) -> int:
        with self._lock:
            return self._events_published

    def get_publish_times(self) -> dict[datetime, float]:
        with self._lock:
            return dict(self._publish_times)

    def get_creation_times(self) -> list[float]:
        with self._lock:
            return list(self._creation_times)


class QueueMonitor:
    """Monitors EventBus queue depth at regular intervals."""

    def __init__(self, event_bus: EventBus, sample_interval_ms: float = 100.0) -> None:
        self.event_bus = event_bus
        self.sample_interval = sample_interval_ms / 1000.0
        self._running = False
        self._thread: threading.Thread | None = None
        self.samples: list[int] = []
        self._lock = threading.Lock()

    def _monitor_loop(self) -> None:
        """Main loop for monitoring queue depth."""
        while self._running:
            if self.event_bus._queue is not None:
                qsize = self.event_bus._queue.qsize()
                with self._lock:
                    self.samples.append(qsize)
            time.sleep(self.sample_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, name="QueueMonitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def get_samples(self) -> list[int]:
        with self._lock:
            return list(self.samples)


class MemoryTracker:
    """Tracks memory usage during test execution using tracemalloc."""

    def __init__(self) -> None:
        self.start_size: int = 0
        self.peak_size: int = 0
        self.end_size: int = 0
        self._tracking = False

    def start(self) -> None:
        gc.collect()
        tracemalloc.start()
        self._tracking = True
        self.start_size = tracemalloc.get_traced_memory()[0]

    def stop(self) -> tuple[int, int, int]:
        if not self._tracking:
            return (0, 0, 0)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._tracking = False
        self.peak_size = peak
        self.end_size = current
        return (self.start_size, self.peak_size, self.end_size)


def run_load_test(
    event_bus: EventBus,
    collector: LatencyTrackingCollector,
    config: LoadTestConfig,
) -> LoadTestMetrics:
    """Execute a load test and collect metrics."""
    metrics = LoadTestMetrics()
    session_id = uuid4()

    memory_tracker = MemoryTracker()
    queue_monitor = QueueMonitor(event_bus, config.sample_queue_interval_ms)
    generator = HighFrequencyEventGenerator(event_bus, session_id, config.frequency_hz)

    memory_tracker.start()
    queue_monitor.start()

    start_time = time.perf_counter()
    generator.start(config.duration_seconds)
    generator.wait(timeout=config.duration_seconds + 5.0)

    # Allow queue to drain
    time.sleep(1.0)
    end_time = time.perf_counter()

    generator.stop()
    queue_monitor.stop()
    memory_start, memory_peak, memory_end = memory_tracker.stop()

    # Populate metrics
    metrics.events_published = generator.get_events_published()
    metrics.events_received = collector.get_event_count()
    metrics.events_dropped = max(0, metrics.events_published - metrics.events_received)
    metrics.duration_seconds = end_time - start_time
    metrics.events_per_second = (
        metrics.events_received / metrics.duration_seconds if metrics.duration_seconds > 0 else 0
    )

    # Calculate latencies
    publish_times = generator.get_publish_times()
    for event_timestamp, publish_time in publish_times.items():
        if event_timestamp in collector.receive_times:
            latency_ms = (collector.receive_times[event_timestamp] - publish_time) * 1000
            metrics.latencies.append(latency_ms)

    # Add creation times
    metrics.creation_times = generator.get_creation_times()

    # Memory and queue metrics
    metrics.memory_start, metrics.memory_peak, metrics.memory_end = (
        memory_start,
        memory_peak,
        memory_end,
    )
    metrics.memory_growth = memory_end - memory_start
    metrics.queue_size_samples = queue_monitor.get_samples()

    # Calculate percentiles
    metrics.calculate_percentiles()

    # Set failure flags
    metrics.had_latency_violations = metrics.p99_latency_ms > config.max_latency_threshold_ms
    metrics.had_memory_growth = metrics.memory_growth > (config.max_memory_growth_mb * 1024 * 1024)
    if metrics.events_published > 0:
        metrics.had_dropped_events = (
            metrics.events_dropped / metrics.events_published
        ) > config.max_dropped_event_pct

    return metrics


def measure_event_creation_overhead(
    num_events: int = 1000,
) -> tuple[float, float, float]:
    """
    Measure the overhead of creating TelemetryFrame objects.

    Returns (avg_ms, p99_ms, max_ms) for event creation time.
    """
    creation_times: list[float] = []

    for i in range(num_events):
        start = time.perf_counter()
        _ = create_telemetry_frame(i)
        end = time.perf_counter()
        creation_times.append((end - start) * 1000)

    sorted_times = sorted(creation_times)
    avg_ms = statistics.mean(sorted_times)
    p99_ms = sorted_times[min(int(len(sorted_times) * 0.99), len(sorted_times) - 1)]
    max_ms = sorted_times[-1]

    return (avg_ms, p99_ms, max_ms)


def find_breaking_point(
    event_bus_factory: Callable[[], EventBus],
    start_frequency: float = 60.0,
    max_frequency: float = 2000.0,
    step_multiplier: float = 1.5,
    test_duration: float = 5.0,
    latency_threshold_ms: float = 100.0,
    drop_threshold_pct: float = 0.01,
) -> tuple[float, LoadTestMetrics]:
    """
    Progressively increase frequency until system breaks.

    Returns (max_sustainable_frequency, final_metrics).
    """
    current_freq = start_frequency
    last_good_freq = 0.0
    last_metrics: LoadTestMetrics | None = None

    while current_freq <= max_frequency:
        bus = event_bus_factory()
        bus.start()
        time.sleep(0.1)

        collector = LatencyTrackingCollector()
        handler = Handler(type=SystemEvents.TELEMETRY_EVENT, fn=collector.collect)
        bus.register_handler(handler)
        time.sleep(0.1)

        config = LoadTestConfig(
            frequency_hz=current_freq,
            duration_seconds=test_duration,
            max_latency_threshold_ms=latency_threshold_ms,
            max_dropped_event_pct=drop_threshold_pct,
        )
        metrics = run_load_test(bus, collector, config)

        bus.stop()
        time.sleep(0.1)

        # Check if we've hit the breaking point
        if metrics.had_latency_violations or metrics.had_dropped_events:
            return (last_good_freq, metrics)

        last_good_freq = current_freq
        last_metrics = metrics
        current_freq *= step_multiplier

    return (last_good_freq, last_metrics or LoadTestMetrics())
