import logging

from racing_coach_core.client import RacingCoachServerSDK
from racing_coach_core.events import EventBus, HandlerContext
from racing_coach_core.models.events import LapAndSession

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapUploadHandler:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.api_client = RacingCoachServerSDK(base_url=settings.SERVER_URL)

    # @subscribe(EventType.LAP_TELEMETRY_SEQUENCE)
    def handle_lap_complete_event(self, context: HandlerContext[LapAndSession]):
        """Handle the lap complete event."""
        data = context.event.data

        if not data.LapTelemetry or not data.SessionFrame:
            logger.error("Lap telemetry or session frame is missing.")
            return

        try:
            # Upload the lap telemetry to the server
            response = self.api_client.upload_lap_telemetry(
                lap_telemetry=data.LapTelemetry, session=data.SessionFrame
            )
            logger.info(f"Lap telemetry uploaded successfully: {response}")
        except Exception as e:
            logger.error(f"Failed to upload lap telemetry: {e}")
            return
