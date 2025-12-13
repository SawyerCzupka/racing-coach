"""Metrics upload handler for racing coach client.

This handler listens to LAP_METRICS_EXTRACTED events and uploads the metrics
to the Racing Coach server.
"""

import logging
from dataclasses import asdict

from racing_coach_core.events import EventBus, HandlerContext, SystemEvents
from racing_coach_core.events.checking import method_handles
from racing_coach_core.schemas.events import MetricsAndSession
from racing_coach_server_client import Client
from racing_coach_server_client.api.metrics import upload_lap_metrics_api_v1_metrics_lap_post
from racing_coach_server_client.models import LapMetrics as ApiLapMetrics
from racing_coach_server_client.models import MetricsUploadRequest, MetricsUploadResponse

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class MetricsUploadHandler:
    """Handler for uploading lap metrics to the server."""

    def __init__(self, event_bus: EventBus):
        """Initialize the metrics upload handler.

        Args:
            event_bus: The event bus for subscribing to events
        """
        self.event_bus = event_bus
        self.api_client = Client(base_url=settings.SERVER_URL)

    @method_handles(SystemEvents.LAP_METRICS_EXTRACTED)
    def handle_metrics_extracted(self, context: HandlerContext[MetricsAndSession]):
        """Handle the lap metrics extracted event and upload to server.

        Args:
            context: Handler context containing the metrics event
        """
        data = context.event.data
        lap_metrics = data.LapMetrics
        session_frame = data.SessionFrame
        lap_id = data.lap_id  # Guaranteed to exist from client-side generation

        if not lap_metrics or not session_frame:
            logger.error("Lap metrics or session frame is missing.")
            return

        try:
            # Convert dataclass to API model
            api_lap_metrics = ApiLapMetrics.from_dict(asdict(lap_metrics))
            body = MetricsUploadRequest(
                lap_metrics=api_lap_metrics,
                lap_id=str(lap_id),
            )

            # Upload the lap metrics to the server
            response = upload_lap_metrics_api_v1_metrics_lap_post.sync(
                client=self.api_client,
                body=body,
            )

            if isinstance(response, MetricsUploadResponse):
                logger.info(
                    f"✓ Lap {lap_metrics.lap_number} metrics uploaded (id: {response.lap_metrics_id})"
                )
            else:
                logger.error(
                    f"✗ Failed to upload metrics for lap {lap_metrics.lap_number}: {response}"
                )

        except Exception as e:
            logger.error(f"✗ Failed to upload metrics for lap {lap_metrics.lap_number}: {e}")
