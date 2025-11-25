import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..algs.events import LapMetrics
from ..models.responses import (
    HealthCheckResponse,
    LapMetricsResponse,
    LapTelemetryResponse,
    LapUploadResponse,
    MetricsUploadResponse,
    SessionDetailResponse,
    SessionListResponse,
)
from ..models.telemetry import LapTelemetry, SessionFrame
from .exceptions import RequestError, ServerError

logger = logging.getLogger(__name__)


class RacingCoachServerSDK:
    """
    SDK client for the Racing Coach Server API.

    Provides a clean interface for uploading telemetry data and managing
    racing session information.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ):
        """
        Initialize the Racing Coach client.

        Args:
            base_url: The base URL of the Racing Coach server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            backoff_factor: Exponential backoff factor for retries
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=backoff_factor,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "racing-coach-client/0.1.0",
            }
        )

    def health_check(self) -> HealthCheckResponse:
        """
        Check if the server is healthy and responding.

        Returns:
            Server health status response

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request("GET", "/api/v1/health")
        return HealthCheckResponse(**response)

    def upload_lap_telemetry(
        self, lap_telemetry: LapTelemetry, session: SessionFrame
    ) -> LapUploadResponse:
        """
        Upload lap telemetry data to the server.

        Args:
            lap_telemetry: Complete lap telemetry data
            session: Session information for the lap

        Returns:
            Server response with upload confirmation and lap ID

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        payload = {
            "lap": lap_telemetry.model_dump(mode="json"),
            "session": session.model_dump(mode="json"),
        }

        logger.info(
            f"Uploading lap {lap_telemetry.frames[0].lap_number if lap_telemetry.frames else 'unknown'} "
            f"with {len(lap_telemetry.frames)} telemetry frames"
        )

        response = self._make_request("POST", "/api/v1/telemetry/lap", json=payload)

        logger.info(f"Successfully uploaded lap telemetry: {response.get('message', 'No message')}")
        return LapUploadResponse(**response)

    def get_latest_session(self) -> SessionFrame:
        """
        Get the latest track session from the server.

        Returns:
            Latest session frame

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request("GET", "/api/v1/sessions/latest")
        return SessionFrame(**response)

    def get_sessions(self) -> SessionListResponse:
        """
        Get all sessions from the server.

        Returns:
            List of session summaries

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request("GET", "/api/v1/sessions")
        return SessionListResponse(**response)

    def get_session(self, session_id: str) -> SessionDetailResponse:
        """
        Get details of a specific session including its laps.

        Args:
            session_id: The UUID of the session

        Returns:
            Session details with lap list

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request("GET", f"/api/v1/sessions/{session_id}")
        return SessionDetailResponse(**response)

    def get_lap_telemetry(self, session_id: str, lap_id: str) -> LapTelemetryResponse:
        """
        Get telemetry frames for a specific lap.

        Args:
            session_id: The UUID of the session
            lap_id: The UUID of the lap

        Returns:
            Lap telemetry with all frames

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request(
            "GET", f"/api/v1/sessions/{session_id}/laps/{lap_id}/telemetry"
        )
        return LapTelemetryResponse(**response)

    def get_lap_metrics(self, lap_id: str) -> LapMetricsResponse:
        """
        Get extracted metrics for a specific lap.

        Args:
            lap_id: The UUID of the lap

        Returns:
            Lap metrics including braking zones and corners

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        response = self._make_request("GET", f"/api/v1/metrics/lap/{lap_id}")
        return LapMetricsResponse(**response)

    def send_telemetry_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Send raw telemetry data to the server.

        Args:
            data: Raw telemetry data dictionary

        Returns:
            Server response

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        return self._make_request("POST", "/api/v1/telemetry", json=data)

    def upload_lap_metrics(self, lap_metrics: LapMetrics, lap_id: str) -> MetricsUploadResponse:
        """
        Upload lap performance metrics to the server.

        Args:
            lap_metrics: Extracted lap metrics (braking, corners, etc.)
            lap_id: The UUID of the lap these metrics are for

        Returns:
            Server response with upload confirmation

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        # Convert dataclass to dict for JSON serialization
        payload = {
            "lap_metrics": {
                "lap_number": lap_metrics.lap_number,
                "lap_time": lap_metrics.lap_time,
                "braking_zones": [
                    {
                        "braking_point_distance": b.braking_point_distance,
                        "braking_point_speed": b.braking_point_speed,
                        "end_distance": b.end_distance,
                        "max_brake_pressure": b.max_brake_pressure,
                        "braking_duration": b.braking_duration,
                        "minimum_speed": b.minimum_speed,
                        "initial_deceleration": b.initial_deceleration,
                        "average_deceleration": b.average_deceleration,
                        "braking_efficiency": b.braking_efficiency,
                        "has_trail_braking": b.has_trail_braking,
                        "trail_brake_distance": b.trail_brake_distance,
                        "trail_brake_percentage": b.trail_brake_percentage,
                    }
                    for b in lap_metrics.braking_zones
                ],
                "corners": [
                    {
                        "turn_in_distance": c.turn_in_distance,
                        "apex_distance": c.apex_distance,
                        "exit_distance": c.exit_distance,
                        "throttle_application_distance": c.throttle_application_distance,
                        "turn_in_speed": c.turn_in_speed,
                        "apex_speed": c.apex_speed,
                        "exit_speed": c.exit_speed,
                        "throttle_application_speed": c.throttle_application_speed,
                        "max_lateral_g": c.max_lateral_g,
                        "time_in_corner": c.time_in_corner,
                        "corner_distance": c.corner_distance,
                        "max_steering_angle": c.max_steering_angle,
                        "speed_loss": c.speed_loss,
                        "speed_gain": c.speed_gain,
                    }
                    for c in lap_metrics.corners
                ],
                "total_corners": lap_metrics.total_corners,
                "total_braking_zones": lap_metrics.total_braking_zones,
                "average_corner_speed": lap_metrics.average_corner_speed,
                "max_speed": lap_metrics.max_speed,
                "min_speed": lap_metrics.min_speed,
            },
            "lap_id": lap_id,
        }

        logger.info(
            f"Uploading metrics for lap {lap_id}: {lap_metrics.total_corners} corners, {lap_metrics.total_braking_zones} braking zones"
        )

        response = self._make_request("POST", "/api/v1/metrics/lap", json=payload)

        logger.info(f"Successfully uploaded lap metrics: {response.get('message', 'No message')}")
        return MetricsUploadResponse(**response)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """
        Make an HTTP request to the server.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            Parsed JSON response

        Raises:
            RequestError: If the request fails
            ServerError: If the server returns an error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)

            # Log request details
            logger.debug(f"{method} {url} -> {response.status_code}")

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                except (ValueError, requests.JSONDecodeError):
                    error_data = None

                if response.status_code >= 500:
                    raise ServerError(
                        f"Server error: {response.status_code} {response.reason}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )
                else:
                    detail = (
                        error_data.get("detail", response.reason) if error_data else response.reason
                    )
                    raise RequestError(
                        f"Client error: {response.status_code} {detail}",
                        status_code=response.status_code,
                        response_text=response.text,
                    )

            # Parse and return response
            try:
                return response.json()
            except (ValueError, requests.JSONDecodeError) as e:
                raise RequestError(f"Invalid JSON response: {e}")

        except requests.exceptions.Timeout:
            raise RequestError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise RequestError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise RequestError(f"Request failed: {e}")

    def close(self):
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
