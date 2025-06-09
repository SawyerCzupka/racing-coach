import logging

from racing_coach_core.client import RacingCoachServerSDK
from racing_coach_core.events import EventHandler, EventType, HandlerContext, subscribe
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapUploadHandler(EventHandler):
    def __init__(self, event_bus):
        super().__init__(event_bus)

        self.api_client = RacingCoachServerSDK(base_url=settings.SERVER_URL)

    # @subscribe(EventType.LAP_TELEMETRY_SEQUENCE)
    def handle_lap_complete_event(self, context: HandlerContext):
        """Handle the lap complete event."""
        data = context.event.data

        lap_telemetry: LapTelemetry = data.get("LapTelemetry")
        session_frame: SessionFrame = data.get("SessionFrame")

        if not lap_telemetry or not session_frame:
            logger.error("Lap telemetry or session frame is missing.")
            return

        try:
            # Upload the lap telemetry to the server
            response = self.api_client.upload_lap_telemetry(
                lap_telemetry=lap_telemetry, session=session_frame
            )
            logger.info(f"Lap telemetry uploaded successfully: {response}")
        except Exception as e:
            logger.error(f"Failed to upload lap telemetry: {e}")
            return
