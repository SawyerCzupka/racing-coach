import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.responses import HealthCheckResponse, LapUploadResponse
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
        response = self._make_request("GET", "/health")
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

        response = self._make_request("POST", "/telemetry/lap", json=payload)

        logger.info(
            f"Successfully uploaded lap telemetry: {response.get('message', 'No message')}"
        )
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
        response = self._make_request("GET", "/sessions/latest")
        return SessionFrame(**response)

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
        return self._make_request("POST", "/telemetry", json=data)

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
            response = self.session.request(
                method=method, url=url, timeout=self.timeout, **kwargs
            )

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
                        error_data.get("detail", response.reason)
                        if error_data
                        else response.reason
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
