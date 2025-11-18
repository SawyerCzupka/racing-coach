"""Metrics extraction handler for racing coach client.

This handler listens to LAP_TELEMETRY_SEQUENCE events and extracts comprehensive
performance metrics including braking points, corner analysis, and lap statistics.
"""

import logging

from racing_coach_core.algs.metrics import extract_lap_metrics
from racing_coach_core.events import (
    Event,
    EventBus,
    HandlerContext,
    SystemEvents,
)
from racing_coach_core.events.checking import method_handles
from racing_coach_core.models.events import LapAndSession, MetricsAndSession

logger = logging.getLogger(__name__)


class MetricsHandler:
    """Handler for extracting performance metrics from lap telemetry."""

    def __init__(self, event_bus: EventBus):
        """Initialize the metrics handler.

        Args:
            event_bus: The event bus for publishing extracted metrics
        """
        self.event_bus = event_bus

    @method_handles(SystemEvents.LAP_TELEMETRY_SEQUENCE)
    def handle_lap_telemetry(self, context: HandlerContext[LapAndSession]):
        """Extract metrics from completed lap telemetry.

        Args:
            context: Handler context containing the lap telemetry event
        """
        data = context.event.data
        lap_telemetry = data.LapTelemetry
        session_frame = data.SessionFrame

        try:
            # Extract comprehensive metrics from the lap
            lap_metrics = extract_lap_metrics(
                sequence=lap_telemetry,
                lap_number=lap_telemetry.frames[0].lap_number if lap_telemetry.frames else None,
            )

            logger.info(
                f"Extracted metrics for lap {lap_metrics.lap_number}: "
                f"{lap_metrics.total_braking_zones} braking zones, "
                f"{lap_metrics.total_corners} corners, "
                f"avg corner speed: {lap_metrics.average_corner_speed:.1f} m/s"
            )

            # Log detailed braking metrics
            for i, braking in enumerate(lap_metrics.braking_zones):
                logger.debug(
                    f"  Braking zone {i + 1}: "
                    f"distance={braking.braking_point_distance:.3f}, "
                    f"speed={braking.braking_point_speed:.1f} m/s, "
                    f"max_pressure={braking.max_brake_pressure:.2f}, "
                    f"trail_braking={braking.has_trail_braking}"
                )

            # Log detailed corner metrics
            for i, corner in enumerate(lap_metrics.corners):
                logger.debug(
                    f"  Corner {i + 1}: "
                    f"turn_in={corner.turn_in_distance:.3f}, "
                    f"apex={corner.apex_distance:.3f}, "
                    f"exit={corner.exit_distance:.3f}, "
                    f"apex_speed={corner.apex_speed:.1f} m/s, "
                    f"max_lateral_g={corner.max_lateral_g:.2f}"
                )

            # Publish the extracted metrics
            self.event_bus.thread_safe_publish(
                Event(
                    type=SystemEvents.LAP_METRICS_EXTRACTED,
                    data=MetricsAndSession(
                        LapMetrics=lap_metrics,
                        SessionFrame=session_frame,
                    ),
                )
            )

            logger.info(f"Published metrics for lap {lap_metrics.lap_number}")

        except Exception as e:
            logger.error(f"Failed to extract metrics from lap telemetry: {e}", exc_info=True)
