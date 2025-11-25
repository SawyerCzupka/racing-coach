"""Metrics upload handler for racing coach client.

This handler listens to LAP_METRICS_EXTRACTED events and uploads the metrics
to the Racing Coach server.
"""

import logging

from racing_coach_core.client import RacingCoachServerSDK
from racing_coach_core.events import EventBus, HandlerContext, SystemEvents
from racing_coach_core.events.checking import method_handles
from racing_coach_core.models.events import MetricsAndSession

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class MetricsUploadHandler:
    """Handler for uploading lap metrics to the server."""

    def __init__(self, event_bus: EventBus, lap_id_cache: dict | None = None):
        """Initialize the metrics upload handler.

        Args:
            event_bus: The event bus for subscribing to events
            lap_id_cache: Shared cache for lap IDs (shared with LapUploadHandler)
        """
        self.event_bus = event_bus
        self.api_client = RacingCoachServerSDK(base_url=settings.SERVER_URL)
        # Shared cache for lap_ids (populated by LapUploadHandler)
        self.lap_id_cache = lap_id_cache if lap_id_cache is not None else {}

    @method_handles(SystemEvents.LAP_METRICS_EXTRACTED)
    def handle_metrics_extracted(self, context: HandlerContext[MetricsAndSession]):
        """Handle the lap metrics extracted event and upload to server.

        Args:
            context: Handler context containing the metrics event
        """
        data = context.event.data
        lap_metrics = data.LapMetrics
        session_frame = data.SessionFrame

        if not lap_metrics or not session_frame:
            logger.error("Lap metrics or session frame is missing.")
            return

        try:
            # Get lap_id from shared cache (populated by LapUploadHandler)
            cache_key = (str(session_frame.session_id), lap_metrics.lap_number)

            if cache_key in self.lap_id_cache:
                lap_id = self.lap_id_cache[cache_key]
                logger.debug(f"Using cached lap_id {lap_id} for lap {lap_metrics.lap_number}")
            else:
                # We don't have the lap_id cached yet
                # This can happen if metrics extraction completes before lap upload
                logger.warning(
                    f"No lap_id cached for session {session_frame.session_id}, "
                    f"lap {lap_metrics.lap_number}. Skipping metrics upload."
                )
                return

            # Upload the lap metrics to the server
            response = self.api_client.upload_lap_metrics(
                lap_metrics=lap_metrics,
                lap_id=lap_id,
            )
            logger.info(
                f"✓ Lap {lap_metrics.lap_number} metrics uploaded "
                f"(id: {response.lap_metrics_id})"
            )

        except Exception as e:
            logger.error(
                f"✗ Failed to upload metrics for lap {lap_metrics.lap_number}: {e}"
            )
