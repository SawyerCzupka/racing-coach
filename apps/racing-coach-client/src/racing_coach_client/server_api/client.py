import logging

import requests
from racing_coach_core.models.telemetry import LapTelemetry, SessionFrame

from racing_coach_client.config import settings

logger = logging.getLogger(__name__)


class RacingCoachServerClient:
    def __init__(self, server_url: str | None = None):
        self.server_url = server_url if server_url else settings.SERVER_URL

    def upload_lap(self, lap_telemetry: LapTelemetry, session: SessionFrame):
        """
        Upload lap telemetry data to the server.

        Args:
            lap_telemetry (LapTelemetry): The telemetry data for the lap to be uploaded.
            session (SessionFrame): The session frame data associated with the lap.

        Returns:
            dict: The server's response in JSON format.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request.
        """

        endpoint_url = f"{self.server_url}/telemetry/lap"

        payload = {
            "lap": lap_telemetry.model_dump(),
            "session": session.model_dump(),
        }

        try:
            response = requests.post(endpoint_url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log the error or handle it as needed
            print(f"Error uploading lap telemetry: {e}")
            raise
