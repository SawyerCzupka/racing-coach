"""Load tests for full client pipeline.

These tests verify that the complete event pipeline (collector -> handlers)
can handle high-frequency telemetry events without issues.

Run with: uv run pytest -m load -v -s
Skip in CI with: uv run pytest -m "not load"
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest
from racing_coach_client.handlers.lap_handler import LapHandler
from racing_coach_core.events.base import (
    Event,
    EventBus,
    Handler,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.schemas.events import LapAndSession, TelemetryAndSessionId
from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame

from tests.factories import SessionFrameFactory, TelemetryFrameFactory

# Import load test utilities
_core_tests_path = (
    Path(__file__).parent.parent.parent.parent / "libs" / "racing-coach-core" / "tests"
)
if str(_core_tests_path) not in sys.path:
    sys.path.insert(0, str(_core_tests_path))

from load_test_utils import (  # noqa: E402
    LatencyTrackingCollector,
    LoadTestConfig,
    run_load_test,
)


@pytest.mark.load
@pytest.mark.slow
class TestLapHandlerUnderLoad:
    """Test LapHandler buffer behavior under sustained load."""

    async def test_lap_handler_buffer_single_lap(
        self,
        running_high_capacity_bus: EventBus,
        session_registry: SessionRegistry,
    ) -> None:
        """
        Test LapHandler buffer behavior for a single complete lap at 60Hz.

        At 60Hz with 60 second lap, we expect ~3600 frames per lap.
        """
        lap_events: list[Event[LapAndSession]] = []

        def collect_lap(context: HandlerContext[LapAndSession]) -> None:
            lap_events.append(context.event)

        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.LAP_TELEMETRY_SEQUENCE, fn=collect_lap)
        )

        lap_handler = LapHandler(running_high_capacity_bus, session_registry)

        # Register the lap handler for telemetry events
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=lap_handler.handle_telemetry_frame)
        )

        # Start a session
        session: SessionFrame = SessionFrameFactory.build()  # type: ignore[attr-defined]
        session_registry.start_session(session)

        # Simulate 1 complete lap at 60Hz (3600 frames) + trigger lap change
        frames_per_lap = 3600
        start_time = time.perf_counter()

        for i in range(frames_per_lap):
            frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
                lap_number=1,
                lap_distance_pct=i / frames_per_lap,
                session_time=i / 60.0,
            )
            event: Event[TelemetryAndSessionId] = Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=frame, session_id=session.session_id),
            )
            running_high_capacity_bus.thread_safe_publish(event)

        # Trigger lap completion by starting lap 2
        final_frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
            lap_number=2, lap_distance_pct=0.01
        )
        final_event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=final_frame, session_id=session.session_id),
        )
        running_high_capacity_bus.thread_safe_publish(final_event)

        elapsed = time.perf_counter() - start_time

        # Wait for events to be processed
        await asyncio.sleep(2.0)

        print(f"\nSingle Lap Test:")
        print(f"  Frames sent: {frames_per_lap + 1}")
        print(f"  Time to publish: {elapsed:.2f}s")
        print(f"  Lap events received: {len(lap_events)}")

        if lap_events:
            print(f"  Frames in lap: {len(lap_events[0].data.LapTelemetry.frames)}")

        assert len(lap_events) == 1, f"Expected 1 lap event, got {len(lap_events)}"
        assert len(lap_events[0].data.LapTelemetry.frames) == frames_per_lap

    async def test_lap_handler_multiple_laps_sustained(
        self,
        running_high_capacity_bus: EventBus,
        session_registry: SessionRegistry,
    ) -> None:
        """
        Test LapHandler with 3 complete laps at 60Hz sustained load.

        Verifies:
        - All frames are buffered correctly
        - Lap events are published at correct boundaries
        - No frames are lost during high-frequency buffering
        """
        lap_events: list[Event[LapAndSession]] = []

        def collect_lap(context: HandlerContext[LapAndSession]) -> None:
            lap_events.append(context.event)

        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.LAP_TELEMETRY_SEQUENCE, fn=collect_lap)
        )

        lap_handler = LapHandler(running_high_capacity_bus, session_registry)
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=lap_handler.handle_telemetry_frame)
        )

        session: SessionFrame = SessionFrameFactory.build()  # type: ignore[attr-defined]
        session_registry.start_session(session)

        # Simulate 3 complete laps
        frames_per_lap = 3600  # 60 seconds at 60Hz
        total_laps = 3
        start_time = time.perf_counter()

        for lap in range(1, total_laps + 1):
            for i in range(frames_per_lap):
                frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
                    lap_number=lap,
                    lap_distance_pct=i / frames_per_lap,
                    session_time=(lap - 1) * 60 + i / 60.0,
                )
                event: Event[TelemetryAndSessionId] = Event(
                    type=SystemEvents.TELEMETRY_EVENT,
                    data=TelemetryAndSessionId(telemetry=frame, session_id=session.session_id),
                )
                running_high_capacity_bus.thread_safe_publish(event)

        # Trigger final lap completion
        final_frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
            lap_number=total_laps + 1, lap_distance_pct=0.01
        )
        final_event: Event[TelemetryAndSessionId] = Event(
            type=SystemEvents.TELEMETRY_EVENT,
            data=TelemetryAndSessionId(telemetry=final_frame, session_id=session.session_id),
        )
        running_high_capacity_bus.thread_safe_publish(final_event)

        elapsed = time.perf_counter() - start_time

        # Wait for events to be processed
        await asyncio.sleep(3.0)

        print(f"\nMultiple Laps Test:")
        print(f"  Total frames sent: {frames_per_lap * total_laps + 1}")
        print(f"  Time to publish: {elapsed:.2f}s")
        print(f"  Lap events received: {len(lap_events)}")

        for i, lap_event in enumerate(lap_events):
            frame_count = len(lap_event.data.LapTelemetry.frames)
            print(f"  Lap {i + 1}: {frame_count} frames")

        assert len(lap_events) == total_laps, f"Expected {total_laps} laps, got {len(lap_events)}"

        for i, lap_event in enumerate(lap_events):
            frame_count = len(lap_event.data.LapTelemetry.frames)
            assert frame_count == frames_per_lap, (
                f"Lap {i + 1} has {frame_count} frames, expected {frames_per_lap}"
            )


@pytest.mark.load
@pytest.mark.slow
class TestFullPipelineLatency:
    """Tests focused on end-to-end latency through the pipeline."""

    async def test_telemetry_event_latency(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Measure end-to-end latency from event publish to handler receipt."""
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        )

        config = LoadTestConfig(frequency_hz=60.0, duration_seconds=10.0)
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print(metrics.summary())

        assert metrics.p99_latency_ms < 100.0, (
            f"P99 latency {metrics.p99_latency_ms:.2f}ms exceeds 100ms"
        )
        assert metrics.events_dropped == 0, f"Dropped {metrics.events_dropped} events"


@pytest.mark.load
@pytest.mark.slow
class TestPipelineStress:
    """Stress tests for the full pipeline."""

    async def test_sustained_100hz_load(
        self,
        running_high_capacity_bus: EventBus,
        latency_collector: LatencyTrackingCollector,
    ) -> None:
        """Stress test with sustained high-frequency events (100Hz for 30s)."""
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=latency_collector.collect)
        )

        config = LoadTestConfig(
            frequency_hz=100.0,
            duration_seconds=30.0,
            max_latency_threshold_ms=150.0,
        )
        metrics = run_load_test(running_high_capacity_bus, latency_collector, config)

        print(f"\nSustained High Load (100Hz for 30s):")
        print(f"  Events: {metrics.events_received}/{metrics.events_published}")
        print(f"  Throughput: {metrics.events_per_second:.1f} events/sec")
        print(f"  P99 Latency: {metrics.p99_latency_ms:.2f}ms")
        print(f"  Memory Growth: {metrics.memory_growth / 1024 / 1024:.2f}MB")

        drop_rate = metrics.events_dropped / max(1, metrics.events_published)
        assert drop_rate < 0.01, f"Drop rate {drop_rate:.2%} exceeds 1%"

    async def test_pipeline_with_multiple_handlers(
        self,
        running_high_capacity_bus: EventBus,
        session_registry: SessionRegistry,
    ) -> None:
        """Test full pipeline with LapHandler + additional handlers at 60Hz."""
        telemetry_count = 0
        lap_count = 0

        def count_telemetry(context: HandlerContext[TelemetryAndSessionId]) -> None:
            nonlocal telemetry_count
            telemetry_count += 1

        def count_laps(context: HandlerContext[LapAndSession]) -> None:
            nonlocal lap_count
            lap_count += 1

        # Register multiple handlers
        lap_handler = LapHandler(running_high_capacity_bus, session_registry)
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=lap_handler.handle_telemetry_frame)
        )
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=count_telemetry)
        )
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.LAP_TELEMETRY_SEQUENCE, fn=count_laps)
        )

        session: SessionFrame = SessionFrameFactory.build()  # type: ignore[attr-defined]
        session_registry.start_session(session)

        # Send 2 laps worth of data
        frames_per_lap = 1800  # 30 seconds at 60Hz (shorter for speed)
        total_laps = 2
        expected_events = frames_per_lap * total_laps + 1

        start_time = time.perf_counter()

        for lap in range(1, total_laps + 1):
            for i in range(frames_per_lap):
                frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
                    lap_number=lap,
                    lap_distance_pct=i / frames_per_lap,
                )
                event: Event[TelemetryAndSessionId] = Event(
                    type=SystemEvents.TELEMETRY_EVENT,
                    data=TelemetryAndSessionId(telemetry=frame, session_id=session.session_id),
                )
                running_high_capacity_bus.thread_safe_publish(event)

        # Trigger final lap
        final_frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
            lap_number=total_laps + 1, lap_distance_pct=0.01
        )
        running_high_capacity_bus.thread_safe_publish(
            Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=final_frame, session_id=session.session_id),
            )
        )

        elapsed = time.perf_counter() - start_time
        await asyncio.sleep(3.0)

        print(f"\nMultiple Handlers Test:")
        print(f"  Time to publish {expected_events} events: {elapsed:.2f}s")
        print(f"  Telemetry events counted: {telemetry_count}")
        print(f"  Lap events counted: {lap_count}")

        assert telemetry_count == expected_events, (
            f"Expected {expected_events} telemetry events, got {telemetry_count}"
        )
        assert lap_count == total_laps, f"Expected {total_laps} lap events, got {lap_count}"


@pytest.mark.load
@pytest.mark.slow
class TestPipelineMemory:
    """Tests focused on memory behavior of the full pipeline."""

    async def test_lap_handler_memory_stability(
        self,
        running_high_capacity_bus: EventBus,
        session_registry: SessionRegistry,
    ) -> None:
        """
        Test that LapHandler doesn't leak memory across multiple laps.

        The telemetry buffer should be cleared after each lap is published.
        """
        import gc
        import tracemalloc

        lap_events: list[Event[LapAndSession]] = []

        def collect_lap(context: HandlerContext[LapAndSession]) -> None:
            lap_events.append(context.event)

        lap_handler = LapHandler(running_high_capacity_bus, session_registry)
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.TELEMETRY_EVENT, fn=lap_handler.handle_telemetry_frame)
        )
        running_high_capacity_bus.register_handler(
            Handler(type=SystemEvents.LAP_TELEMETRY_SEQUENCE, fn=collect_lap)
        )

        session: SessionFrame = SessionFrameFactory.build()  # type: ignore[attr-defined]
        session_registry.start_session(session)

        gc.collect()
        tracemalloc.start()
        memory_start = tracemalloc.get_traced_memory()[0]

        # Send 5 laps of data
        frames_per_lap = 600  # 10 seconds at 60Hz (shorter for speed)
        total_laps = 5

        for lap in range(1, total_laps + 1):
            for i in range(frames_per_lap):
                frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
                    lap_number=lap,
                    lap_distance_pct=i / frames_per_lap,
                )
                event: Event[TelemetryAndSessionId] = Event(
                    type=SystemEvents.TELEMETRY_EVENT,
                    data=TelemetryAndSessionId(telemetry=frame, session_id=session.session_id),
                )
                running_high_capacity_bus.thread_safe_publish(event)

        # Trigger final lap
        final_frame: TelemetryFrame = TelemetryFrameFactory.build(  # type: ignore[attr-defined]
            lap_number=total_laps + 1, lap_distance_pct=0.01
        )
        running_high_capacity_bus.thread_safe_publish(
            Event(
                type=SystemEvents.TELEMETRY_EVENT,
                data=TelemetryAndSessionId(telemetry=final_frame, session_id=session.session_id),
            )
        )

        await asyncio.sleep(2.0)

        memory_current, memory_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        memory_growth_mb = (memory_current - memory_start) / 1024 / 1024
        memory_peak_mb = memory_peak / 1024 / 1024

        print(f"\nLap Handler Memory Test ({total_laps} laps):")
        print(f"  Start: {memory_start / 1024 / 1024:.2f}MB")
        print(f"  Current: {memory_current / 1024 / 1024:.2f}MB")
        print(f"  Peak: {memory_peak_mb:.2f}MB")
        print(f"  Growth: {memory_growth_mb:.2f}MB")
        print(f"  Laps collected: {len(lap_events)}")
        print(f"  Buffer size after test: {len(lap_handler.telemetry_buffer)}")

        assert len(lap_events) == total_laps
        # Buffer should be small (only current lap frames, or empty if lap just completed)
        assert len(lap_handler.telemetry_buffer) <= frames_per_lap + 10
