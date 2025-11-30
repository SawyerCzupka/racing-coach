#!/usr/bin/env python
"""Benchmark comparing Python vs Rust implementations of core algorithms.

This script compares the performance of:
1. compute_speed_stats - basic statistics calculation
2. extract_braking_zones - braking zone detection
3. extract_corners - corner detection
4. extract_lap_metrics - full lap analysis (combined)

Run with: uv run python benchmark_rust_vs_python.py
"""

import statistics
import time
from datetime import datetime, timezone
from typing import Callable

from racing_coach_core.models.telemetry import TelemetryFrame, TelemetrySequence


# ============================================================================
# Telemetry Generation
# ============================================================================


def create_telemetry_frame(
    *,
    brake: float = 0.0,
    throttle: float = 0.0,
    speed: float = 50.0,
    lap_distance_pct: float = 0.5,
    steering_angle: float = 0.0,
    lateral_acceleration: float = 0.0,
    longitudinal_acceleration: float = 0.0,
    timestamp: datetime | None = None,
    lap_number: int = 1,
) -> TelemetryFrame:
    """Create a TelemetryFrame with sensible defaults."""
    return TelemetryFrame(
        timestamp=timestamp or datetime.now(timezone.utc),
        session_time=0.0,
        lap_number=lap_number,
        lap_distance_pct=lap_distance_pct,
        lap_distance=lap_distance_pct * 5000,
        current_lap_time=0.0,
        last_lap_time=0.0,
        best_lap_time=0.0,
        speed=speed,
        rpm=5000.0,
        gear=3,
        throttle=throttle,
        brake=brake,
        clutch=0.0,
        steering_angle=steering_angle,
        lateral_acceleration=lateral_acceleration,
        longitudinal_acceleration=longitudinal_acceleration,
        vertical_acceleration=0.0,
        yaw_rate=0.0,
        roll_rate=0.0,
        pitch_rate=0.0,
        velocity_x=speed,
        velocity_y=0.0,
        velocity_z=0.0,
        yaw=0.0,
        pitch=0.0,
        roll=0.0,
        latitude=0.0,
        longitude=0.0,
        altitude=0.0,
        tire_temps={"LF": {"left": 80.0, "middle": 85.0, "right": 82.0}},
        tire_wear={"LF": {"left": 0.95, "middle": 0.93, "right": 0.94}},
        brake_line_pressure={"LF": 2.5},
        track_temp=30.0,
        track_wetness=0,
        air_temp=25.0,
        session_flags=0,
        track_surface=1,
        on_pit_road=False,
    )


def generate_realistic_lap(num_frames: int, num_corners: int = 10) -> TelemetrySequence:
    """Generate a realistic lap with braking zones and corners.

    Simulates a lap with alternating straights, braking zones, and corners.
    """
    frames = []
    corner_spacing = 1.0 / num_corners

    for i in range(num_frames):
        pct = i / num_frames

        # Determine which section of the corner we're in
        corner_num = int(pct / corner_spacing)
        within_corner_pct = (pct % corner_spacing) / corner_spacing

        if within_corner_pct < 0.3:
            # Straight - full throttle
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=1.0,
                brake=0.0,
                speed=80.0,
                steering_angle=0.02,  # Slight correction
                longitudinal_acceleration=2.0,
                lateral_acceleration=0.5,
            )
        elif within_corner_pct < 0.45:
            # Braking zone
            brake_intensity = (within_corner_pct - 0.3) / 0.15
            speed = 80.0 - (brake_intensity * 45)
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.0,
                brake=0.7 + brake_intensity * 0.3,
                speed=speed,
                steering_angle=0.05,
                longitudinal_acceleration=-12.0,
                lateral_acceleration=1.0,
            )
        elif within_corner_pct < 0.55:
            # Trail braking into corner
            trail_pct = (within_corner_pct - 0.45) / 0.1
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.0,
                brake=0.5 - trail_pct * 0.4,
                speed=35.0 - trail_pct * 5,
                steering_angle=0.3 + trail_pct * 0.4,
                longitudinal_acceleration=-5.0,
                lateral_acceleration=15.0 + trail_pct * 5,
            )
        elif within_corner_pct < 0.7:
            # Apex/mid-corner
            apex_pct = (within_corner_pct - 0.55) / 0.15
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.1 + apex_pct * 0.3,
                brake=0.0,
                speed=30.0 + apex_pct * 10,
                steering_angle=0.7 - apex_pct * 0.2,
                longitudinal_acceleration=2.0,
                lateral_acceleration=20.0 - apex_pct * 5,
            )
        else:
            # Corner exit
            exit_pct = (within_corner_pct - 0.7) / 0.3
            frame = create_telemetry_frame(
                lap_distance_pct=pct,
                throttle=0.5 + exit_pct * 0.5,
                brake=0.0,
                speed=40.0 + exit_pct * 35,
                steering_angle=0.5 - exit_pct * 0.45,
                longitudinal_acceleration=8.0 - exit_pct * 3,
                lateral_acceleration=15.0 - exit_pct * 12,
            )

        frames.append(frame)

    return TelemetrySequence(frames=frames)


# ============================================================================
# Timing Utilities
# ============================================================================


def benchmark_function(
    name: str,
    func: Callable[[], None],
    iterations: int = 100,
    warmup: int = 5,
) -> dict:
    """Run a benchmark and return timing statistics."""
    # Warmup
    for _ in range(warmup):
        func()

    # Actual benchmark
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        "name": name,
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
        "max_ms": max(times),
    }


def print_results(results: dict) -> None:
    """Print benchmark results."""
    print(f"  {results['name']}: {results['mean_ms']:.4f} ms (median: {results['median_ms']:.4f} ms, stdev: {results['stdev_ms']:.4f} ms)")


def print_comparison(python_results: dict, rust_results: dict) -> float:
    """Print comparison between Python and Rust results. Returns speedup factor."""
    speedup = python_results["mean_ms"] / rust_results["mean_ms"]
    print(f"  Python: {python_results['mean_ms']:.4f} ms")
    print(f"  Rust:   {rust_results['mean_ms']:.4f} ms")
    print(f"  Speedup: {speedup:.2f}x faster")
    return speedup


# ============================================================================
# Benchmark Functions
# ============================================================================


def benchmark_speed_stats(sizes: list[int], iterations: int = 100) -> list[tuple[int, float]]:
    """Benchmark compute_speed_stats for different data sizes."""
    from racing_coach_core.rust_ext import (
        _rs_compute_speed_stats,
        is_rust_available,
    )

    if not is_rust_available():
        print("Rust extension not available!")
        return []

    print("\n" + "=" * 70)
    print("BENCHMARK: compute_speed_stats")
    print("=" * 70)

    speedups = []

    for size in sizes:
        speeds = [float(i % 100 + 20) for i in range(size)]

        print(f"\nData size: {size:,} speeds")

        # Python implementation
        def py_stats():
            if not speeds:
                return (0.0, 0.0, 0.0)
            return (min(speeds), max(speeds), sum(speeds) / len(speeds))

        # Rust implementation
        def rs_stats():
            return _rs_compute_speed_stats(speeds)

        py_results = benchmark_function("Python", py_stats, iterations)
        rs_results = benchmark_function("Rust", rs_stats, iterations)

        speedup = print_comparison(py_results, rs_results)
        speedups.append((size, speedup))

    return speedups


def benchmark_braking_zones(frame_counts: list[int], iterations: int = 50) -> list[tuple[int, float]]:
    """Benchmark braking zone extraction for different telemetry sizes."""
    from racing_coach_core.algs.metrics import _extract_braking_zones as py_extract_braking_zones
    from racing_coach_core.rust_ext import (
        _convert_sequence_to_rust_frames,
        _rs_AnalysisConfig,
        _rs_extract_braking_zones,
        is_rust_available,
    )

    if not is_rust_available():
        print("Rust extension not available!")
        return []

    print("\n" + "=" * 70)
    print("BENCHMARK: extract_braking_zones")
    print("=" * 70)

    speedups = []

    for num_frames in frame_counts:
        sequence = generate_realistic_lap(num_frames, num_corners=10)
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig()

        print(f"\nFrames: {num_frames:,} (~{num_frames/60:.1f}s at 60Hz)")

        # Python implementation
        def py_braking():
            return py_extract_braking_zones(sequence.frames, 0.05, 0.15)

        # Rust implementation
        def rs_braking():
            return _rs_extract_braking_zones(rust_frames, config=config)

        py_results = benchmark_function("Python", py_braking, iterations)
        rs_results = benchmark_function("Rust", rs_braking, iterations)

        speedup = print_comparison(py_results, rs_results)
        speedups.append((num_frames, speedup))

    return speedups


def benchmark_corners(frame_counts: list[int], iterations: int = 50) -> list[tuple[int, float]]:
    """Benchmark corner extraction for different telemetry sizes."""
    from racing_coach_core.algs.metrics import _extract_corners as py_extract_corners
    from racing_coach_core.rust_ext import (
        _convert_sequence_to_rust_frames,
        _rs_AnalysisConfig,
        _rs_extract_corners,
        is_rust_available,
    )

    if not is_rust_available():
        print("Rust extension not available!")
        return []

    print("\n" + "=" * 70)
    print("BENCHMARK: extract_corners")
    print("=" * 70)

    speedups = []

    for num_frames in frame_counts:
        sequence = generate_realistic_lap(num_frames, num_corners=10)
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig()

        print(f"\nFrames: {num_frames:,} (~{num_frames/60:.1f}s at 60Hz)")

        # Python implementation
        def py_corners():
            return py_extract_corners(sequence.frames, 0.15, 0.05)

        # Rust implementation
        def rs_corners():
            return _rs_extract_corners(rust_frames, config=config)

        py_results = benchmark_function("Python", py_corners, iterations)
        rs_results = benchmark_function("Rust", rs_corners, iterations)

        speedup = print_comparison(py_results, rs_results)
        speedups.append((num_frames, speedup))

    return speedups


def benchmark_lap_metrics(frame_counts: list[int], iterations: int = 50) -> list[tuple[int, float]]:
    """Benchmark full lap metrics extraction for different telemetry sizes."""
    from racing_coach_core.algs.metrics import extract_lap_metrics as py_extract_lap_metrics
    from racing_coach_core.rust_ext import (
        _convert_rust_lap_metrics,
        _convert_sequence_to_rust_frames,
        _rs_AnalysisConfig,
        _rs_extract_lap_metrics,
        is_rust_available,
    )

    if not is_rust_available():
        print("Rust extension not available!")
        return []

    print("\n" + "=" * 70)
    print("BENCHMARK: extract_lap_metrics (full analysis)")
    print("=" * 70)

    speedups = []

    for num_frames in frame_counts:
        sequence = generate_realistic_lap(num_frames, num_corners=10)
        rust_frames = _convert_sequence_to_rust_frames(sequence)
        config = _rs_AnalysisConfig()

        print(f"\nFrames: {num_frames:,} (~{num_frames/60:.1f}s at 60Hz)")

        # Python implementation
        def py_metrics():
            return py_extract_lap_metrics(sequence)

        # Rust implementation (raw, no conversion)
        def rs_metrics_raw():
            return _rs_extract_lap_metrics(rust_frames, lap_number=1, config=config)

        # Rust implementation (with conversion to Python types)
        def rs_metrics_full():
            result = _rs_extract_lap_metrics(rust_frames, lap_number=1, config=config)
            return _convert_rust_lap_metrics(result)

        py_results = benchmark_function("Python", py_metrics, iterations)
        rs_raw_results = benchmark_function("Rust (raw)", rs_metrics_raw, iterations)
        rs_full_results = benchmark_function("Rust (with conversion)", rs_metrics_full, iterations)

        speedup_raw = py_results["mean_ms"] / rs_raw_results["mean_ms"]
        speedup_full = py_results["mean_ms"] / rs_full_results["mean_ms"]

        print(f"  Python:                 {py_results['mean_ms']:.4f} ms")
        print(f"  Rust (raw):             {rs_raw_results['mean_ms']:.4f} ms ({speedup_raw:.2f}x faster)")
        print(f"  Rust (with conversion): {rs_full_results['mean_ms']:.4f} ms ({speedup_full:.2f}x faster)")

        speedups.append((num_frames, speedup_full))

    return speedups


def benchmark_data_conversion(frame_counts: list[int], iterations: int = 50) -> None:
    """Benchmark the overhead of converting Python data to Rust types."""
    from racing_coach_core.rust_ext import (
        _convert_sequence_to_rust_frames,
        is_rust_available,
    )

    if not is_rust_available():
        print("Rust extension not available!")
        return

    print("\n" + "=" * 70)
    print("BENCHMARK: Data Conversion Overhead")
    print("=" * 70)

    for num_frames in frame_counts:
        sequence = generate_realistic_lap(num_frames, num_corners=10)

        print(f"\nFrames: {num_frames:,}")

        def convert():
            return _convert_sequence_to_rust_frames(sequence)

        results = benchmark_function("Conversion", convert, iterations)
        print(f"  Conversion time: {results['mean_ms']:.4f} ms")


# ============================================================================
# Main
# ============================================================================


def main():
    print("=" * 70)
    print("Python vs Rust Algorithm Benchmark")
    print("=" * 70)

    from racing_coach_core.rust_ext import is_rust_available

    if not is_rust_available():
        print("\nERROR: Rust extension is not available!")
        print("Please build the Rust extension first:")
        print("  cd libs/racing-coach-core")
        print("  uv run maturin develop --release")
        return

    print("\nRust extension: AVAILABLE")

    # Define test sizes
    speed_sizes = [100, 1_000, 10_000, 100_000, 1_000_000]
    frame_counts = [600, 3_600, 7_200, 18_000]  # 10s, 60s, 2min, 5min at 60Hz

    # Run benchmarks
    speed_speedups = benchmark_speed_stats(speed_sizes, iterations=100)
    braking_speedups = benchmark_braking_zones(frame_counts, iterations=50)
    corner_speedups = benchmark_corners(frame_counts, iterations=50)
    lap_speedups = benchmark_lap_metrics(frame_counts, iterations=50)
    benchmark_data_conversion(frame_counts, iterations=50)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\nSpeed Stats Speedup:")
    for size, speedup in speed_speedups:
        print(f"  {size:>10,} items: {speedup:>6.2f}x")

    print("\nBraking Zones Speedup:")
    for frames, speedup in braking_speedups:
        print(f"  {frames:>10,} frames: {speedup:>6.2f}x")

    print("\nCorner Detection Speedup:")
    for frames, speedup in corner_speedups:
        print(f"  {frames:>10,} frames: {speedup:>6.2f}x")

    print("\nFull Lap Metrics Speedup:")
    for frames, speedup in lap_speedups:
        print(f"  {frames:>10,} frames: {speedup:>6.2f}x")

    # Overall average
    all_speedups = [s for _, s in speed_speedups + braking_speedups + corner_speedups + lap_speedups]
    if all_speedups:
        avg_speedup = statistics.mean(all_speedups)
        print(f"\nOverall Average Speedup: {avg_speedup:.2f}x faster")


if __name__ == "__main__":
    main()
