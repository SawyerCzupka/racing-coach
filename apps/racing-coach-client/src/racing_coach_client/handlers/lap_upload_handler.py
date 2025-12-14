import logging

from racing_coach_core.events import Event, EventBus, HandlerContext, SystemEvents
from racing_coach_core.events.checking import method_handles
from racing_coach_core.schemas.events import LapAndSession, LapUploadResult
from racing_coach_server_client import Client
from racing_coach_server_client.api.telemetry import upload_lap_api_v1_telemetry_lap_post
from racing_coach_server_client.models import (
    BodyUploadLapApiV1TelemetryLapPost,
    LapUploadResponse,
)
from racing_coach_server_client.models import (
    LapTelemetry as ApiLapTelemetry,
)
from racing_coach_server_client.models import (
    SessionFrame as ApiSessionFrame,
)

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class LapUploadHandler:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.api_client = Client(base_url=settings.SERVER_URL)

    @method_handles(SystemEvents.LAP_TELEMETRY_SEQUENCE)
    def handle_lap_complete_event(self, context: HandlerContext[LapAndSession]):
        """Handle the lap complete event."""
        data = context.event.data

        if not data.LapTelemetry or not data.SessionFrame:
            logger.error("Lap telemetry or session frame is missing.")
            return

        lap_number = data.LapTelemetry.frames[0].lap_number if data.LapTelemetry.frames else -1

        try:
            # Convert Pydantic models to API client models
            body = BodyUploadLapApiV1TelemetryLapPost(
                lap=ApiLapTelemetry.from_dict(data.LapTelemetry.model_dump(mode="json")),
                session=ApiSessionFrame.from_dict(data.SessionFrame.model_dump(mode="json")),
            )

            # Upload the lap telemetry to the server with client-generated lap_id
            response = upload_lap_api_v1_telemetry_lap_post.sync(
                client=self.api_client,
                body=body,
                lap_id=data.lap_id,
            )

            if isinstance(response, LapUploadResponse):
                logger.info(f"✓ Lap {lap_number} uploaded successfully (lap_id: {data.lap_id})")
                self.event_bus.thread_safe_publish(
                    Event(
                        type=SystemEvents.LAP_UPLOAD_SUCCESS,
                        data=LapUploadResult(
                            lap_id=data.lap_id,
                            lap_number=lap_number,
                            success=True,
                        ),
                    )
                )
            else:
                error_msg = str(response)
                logger.error(f"✗ Failed to upload lap {lap_number}: {error_msg}")
                self.event_bus.thread_safe_publish(
                    Event(
                        type=SystemEvents.LAP_UPLOAD_FAILED,
                        data=LapUploadResult(
                            lap_id=data.lap_id,
                            lap_number=lap_number,
                            success=False,
                            error_message=error_msg,
                        ),
                    )
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ Failed to upload lap {lap_number}: {error_msg}")
            self.event_bus.thread_safe_publish(
                Event(
                    type=SystemEvents.LAP_UPLOAD_FAILED,
                    data=LapUploadResult(
                        lap_id=data.lap_id,
                        lap_number=lap_number,
                        success=False,
                        error_message=error_msg,
                    ),
                )
            )
