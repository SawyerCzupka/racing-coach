import logging

from racing_coach_core.client import RacingCoachServerSDK
from racing_coach_core.events import EventBus, HandlerContext, SystemEvents
from racing_coach_core.events.checking import method_handles
from racing_coach_core.models.events import LapAndSession

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapUploadHandler:
    def __init__(self, event_bus: EventBus, lap_id_cache: dict | None = None):
        self.event_bus = event_bus
        self.api_client = RacingCoachServerSDK(base_url=settings.SERVER_URL)
        # Shared cache for storing lap_ids for metrics upload
        self.lap_id_cache = lap_id_cache if lap_id_cache is not None else {}

    @method_handles(SystemEvents.LAP_TELEMETRY_SEQUENCE)
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

            # Cache the lap_id for metrics upload
            lap_number = data.LapTelemetry.frames[0].lap_number if data.LapTelemetry.frames else -1
            if lap_number != -1:
                cache_key = (str(data.SessionFrame.session_id), lap_number)
                self.lap_id_cache[cache_key] = response.lap_id
                logger.debug(f"Cached lap_id {response.lap_id} for lap {lap_number}")

        except Exception as e:
            logger.error(f"Failed to upload lap telemetry: {e}")
            return
