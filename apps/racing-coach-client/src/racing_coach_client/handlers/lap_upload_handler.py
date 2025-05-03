import logging

from racing_coach_core.events import EventHandler, EventType, subscribe
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame

from racing_coach_client.server_api import client

logger = logging.getLogger(__name__)


class LapUploadHandler(EventHandler):
    def __init__(self, event_bus, api_client: client.RacingCoachServerClient):
        super().__init__(event_bus)
        self.api_client = api_client

    @subscribe(EventType.LAP_TELEMETRY_SEQUENCE)
    def handle_lap_complete_event(self, context):
        """Handle the lap complete event."""
        data = context.event.data

        lap_telemetry: LapTelemetry = data.get("LapTelemetry")
        session_frame: SessionFrame = data.get("SessionFrame")

        if not lap_telemetry or not session_frame:
            logger.error("Lap telemetry or session frame is missing.")
            return

        try:
            # Upload the lap telemetry to the server
            response = self.api_client.upload_lap(lap_telemetry, session_frame)
            logger.info(f"Lap telemetry uploaded successfully: {response}")
        except Exception as e:
            logger.error(f"Failed to upload lap telemetry: {e}")
            return
