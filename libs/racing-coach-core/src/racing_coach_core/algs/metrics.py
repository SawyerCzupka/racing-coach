"""Comprehensive metrics extraction for racing telemetry data."""

import logging
from typing import Literal

from racing_coach_core.models.telemetry import TelemetryFrame, TelemetrySequence

from .events import BrakingMetrics, CornerMetrics, LapMetrics

logger = logging.getLogger(__name__)

# Thresholds for detection
BRAKE_THRESHOLD = 0.05  # 5% brake application
STEERING_THRESHOLD = 0.15  # 15% steering angle (absolute value)
THROTTLE_THRESHOLD = 0.05  # 5% throttle application


def extract_lap_metrics(
    sequence: TelemetrySequence,
    lap_number: int | None = None,
    brake_threshold: float = BRAKE_THRESHOLD,
    steering_threshold: float = STEERING_THRESHOLD,
    throttle_threshold: float = THROTTLE_THRESHOLD,
) -> LapMetrics:
    """
    Extract comprehensive metrics from a lap's telemetry sequence.

    Args:
        sequence: The telemetry sequence for the lap
        lap_number: The lap number (optional, extracted from telemetry if not provided)
        brake_threshold: Minimum brake application to consider as braking
        steering_threshold: Minimum steering angle to consider as turning
        throttle_threshold: Minimum throttle application to consider as acceleration

    Returns:
        LapMetrics containing all extracted performance data
    """
    frames = sequence.frames

    if not frames:
        raise ValueError("Cannot extract metrics from empty telemetry sequence")

    # Extract lap number from first frame if not provided
    if lap_number is None:
        lap_number = frames[0].lap_number

    # Get lap time if available
    lap_time = None
    if hasattr(sequence, "lap_time"):
        lap_time = sequence.lap_time

    # Extract braking zones
    braking_zones = _extract_braking_zones(frames, brake_threshold, steering_threshold)

    # Extract corners
    corners = _extract_corners(frames, steering_threshold, throttle_threshold)

    # Calculate lap-wide statistics
    speeds = [frame.speed for frame in frames]
    corner_speeds = [corner.apex_speed for corner in corners]

    lap_metrics = LapMetrics(
        lap_number=lap_number,
        lap_time=lap_time,
        braking_zones=braking_zones,
        corners=corners,
        total_corners=len(corners),
        total_braking_zones=len(braking_zones),
        average_corner_speed=sum(corner_speeds) / len(corner_speeds) if corner_speeds else 0.0,
        max_speed=max(speeds) if speeds else 0.0,
        min_speed=min(speeds) if speeds else 0.0,
    )

    logger.info(
        f"Extracted metrics for lap {lap_number}: "
        f"{len(braking_zones)} braking zones, {len(corners)} corners"
    )

    return lap_metrics


def _extract_braking_zones(
    frames: list[TelemetryFrame],
    brake_threshold: float,
    steering_threshold: float,
) -> list[BrakingMetrics]:
    """Extract detailed braking metrics from telemetry frames."""
    braking_zones: list[BrakingMetrics] = []

    i = 0
    while i < len(frames):
        # Find start of braking zone
        if frames[i].brake <= brake_threshold:
            i += 1
            continue

        # Braking zone detected
        start_idx = i
        start_frame = frames[start_idx]

        # Track max pressure and minimum speed during braking
        max_pressure = start_frame.brake
        min_speed = start_frame.speed
        end_idx = start_idx

        # Find end of braking zone
        while i < len(frames) and frames[i].brake > brake_threshold:
            max_pressure = max(max_pressure, frames[i].brake)
            min_speed = min(min_speed, frames[i].speed)
            end_idx = i
            i += 1

        end_frame = frames[end_idx]

        # Calculate braking duration
        duration = (end_frame.timestamp - start_frame.timestamp).total_seconds()

        # Calculate deceleration metrics
        initial_decel = _calculate_deceleration(frames, start_idx, min(start_idx + 5, end_idx))
        avg_decel = _calculate_deceleration(frames, start_idx, end_idx)

        # Braking efficiency: deceleration per unit of brake pressure
        efficiency = abs(avg_decel) / max_pressure if max_pressure > 0 else 0.0

        # Detect trail braking (braking while turning)
        trail_braking_info = _detect_trail_braking(
            frames, start_idx, end_idx, steering_threshold, brake_threshold
        )

        braking_metrics = BrakingMetrics(
            braking_point_distance=start_frame.lap_distance,
            braking_point_speed=start_frame.speed,
            end_distance=end_frame.lap_distance,
            max_brake_pressure=max_pressure,
            braking_duration=duration,
            minimum_speed=min_speed,
            initial_deceleration=initial_decel,
            average_deceleration=avg_decel,
            braking_efficiency=efficiency,
            has_trail_braking=trail_braking_info["has_trail_braking"],
            trail_brake_distance=trail_braking_info["distance"],
            trail_brake_percentage=trail_braking_info["percentage"],
        )

        braking_zones.append(braking_metrics)

    return braking_zones


def _extract_corners(
    frames: list[TelemetryFrame],
    steering_threshold: float,
    throttle_threshold: float,
) -> list[CornerMetrics]:
    """Extract detailed corner metrics from telemetry frames."""
    corners: list[CornerMetrics] = []

    i = 0
    while i < len(frames):
        # Find turn-in point (steering angle exceeds threshold)
        if abs(frames[i].steering_angle) <= steering_threshold:
            i += 1
            continue

        # Corner detected
        turn_in_idx = i
        turn_in_frame = frames[turn_in_idx]

        # Track apex (max lateral G), exit, and throttle application points
        max_lateral_g = abs(frames[i].lateral_acceleration)
        apex_idx = i
        min_speed = frames[i].speed
        min_speed_idx = i
        max_steering = abs(frames[i].steering_angle)
        exit_idx = turn_in_idx
        throttle_idx = turn_in_idx

        throttle_applied = False

        # Scan through the corner
        while i < len(frames):
            current_steering = abs(frames[i].steering_angle)

            # Track maximum lateral G (apex)
            if abs(frames[i].lateral_acceleration) > max_lateral_g:
                max_lateral_g = abs(frames[i].lateral_acceleration)
                apex_idx = i

            # Track minimum speed
            if frames[i].speed < min_speed:
                min_speed = frames[i].speed
                min_speed_idx = i

            # Track maximum steering angle
            if current_steering > max_steering:
                max_steering = current_steering

            # Detect throttle application point (first time throttle is applied in corner)
            if not throttle_applied and frames[i].throttle > throttle_threshold:
                throttle_idx = i
                throttle_applied = True

            # Check for corner exit (steering returns below threshold)
            if current_steering < steering_threshold:
                exit_idx = i
                break

            i += 1

        # If we didn't find an exit, use the last frame we processed
        if i >= len(frames):
            exit_idx = len(frames) - 1

        # Get frames at key points
        apex_frame = frames[apex_idx]
        exit_frame = frames[exit_idx]
        throttle_frame = frames[throttle_idx]

        # Calculate time in corner
        time_in_corner = (exit_frame.timestamp - turn_in_frame.timestamp).total_seconds()

        # Calculate corner distance
        corner_distance = exit_frame.lap_distance - turn_in_frame.lap_distance
        # Handle lap wrap-around
        if corner_distance < 0:
            corner_distance += 1.0  # Assuming lap_distance is normalized to 0-1

        # Calculate speed deltas
        speed_loss = turn_in_frame.speed - min_speed
        speed_gain = exit_frame.speed - min_speed

        corner_metrics = CornerMetrics(
            turn_in_distance=turn_in_frame.lap_distance,
            apex_distance=apex_frame.lap_distance,
            exit_distance=exit_frame.lap_distance,
            throttle_application_distance=throttle_frame.lap_distance,
            turn_in_speed=turn_in_frame.speed,
            apex_speed=min_speed,  # Use minimum speed as apex speed
            exit_speed=exit_frame.speed,
            throttle_application_speed=throttle_frame.speed,
            max_lateral_g=max_lateral_g,
            time_in_corner=time_in_corner,
            corner_distance=corner_distance,
            max_steering_angle=max_steering,
            speed_loss=speed_loss,
            speed_gain=speed_gain,
        )

        corners.append(corner_metrics)

        # Move past this corner
        i = exit_idx + 1

    return corners


def _calculate_deceleration(
    frames: list[TelemetryFrame],
    start_idx: int,
    end_idx: int,
) -> float:
    """
    Calculate average deceleration between two frame indices.

    Returns negative value for deceleration, positive for acceleration.
    """
    if start_idx >= end_idx or end_idx >= len(frames):
        return 0.0

    start_frame = frames[start_idx]
    end_frame = frames[end_idx]

    # Speed delta (m/s)
    speed_delta = end_frame.speed - start_frame.speed

    # Time delta (seconds)
    time_delta = (end_frame.timestamp - start_frame.timestamp).total_seconds()

    if time_delta <= 0:
        return 0.0

    # Acceleration/deceleration in m/s²
    return speed_delta / time_delta


def _detect_trail_braking(
    frames: list[TelemetryFrame],
    brake_start_idx: int,
    brake_end_idx: int,
    steering_threshold: float,
    brake_threshold: float,
) -> dict[str, float | bool]:
    """
    Detect if trail braking was used (braking while turning).

    Returns a dictionary with:
    - has_trail_braking: bool
    - distance: float (track distance of trail braking overlap)
    - percentage: float (percentage of brake pressure during turn-in)
    """
    trail_brake_distance = 0.0
    trail_brake_pressure_sum = 0.0
    trail_brake_frames = 0

    has_trail_braking = False

    for i in range(brake_start_idx, min(brake_end_idx + 1, len(frames))):
        frame = frames[i]

        # Check if both braking and steering are happening
        if frame.brake > brake_threshold and abs(frame.steering_angle) > steering_threshold:
            has_trail_braking = True
            trail_brake_frames += 1
            trail_brake_pressure_sum += frame.brake

            # Calculate distance
            if i + 1 < len(frames):
                next_frame = frames[i + 1]
                distance_delta = next_frame.lap_distance - frame.lap_distance
                # Handle lap wrap
                if distance_delta < 0:
                    distance_delta += 1.0
                trail_brake_distance += distance_delta

    # Calculate average trail brake percentage
    trail_brake_percentage = (
        trail_brake_pressure_sum / trail_brake_frames if trail_brake_frames > 0 else 0.0
    )

    return {
        "has_trail_braking": has_trail_braking,
        "distance": trail_brake_distance,
        "percentage": trail_brake_percentage,
    }
