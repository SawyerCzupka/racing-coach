"""Track service for fetching corner segments and track boundaries from the server."""

import logging
from uuid import UUID

from racing_coach_core.algs.events import CornerSegmentInput
from racing_coach_core.schemas.track import TrackBoundary
from racing_coach_server_client import AuthenticatedClient
from racing_coach_server_client.api.tracks import (
    get_track_boundary,
    list_corner_segments,
    list_track_boundaries,
)
from racing_coach_server_client.models import (
    CornerSegmentListResponse,
    TrackBoundaryListResponse,
    TrackBoundaryResponse,
)

logger = logging.getLogger(__name__)


class TrackService:
    """Fetches and caches track data from the server.

    Provides corner segments and track boundaries for metric extraction.
    Results are cached per (track_id, track_config_name) for the session lifetime.
    """

    def __init__(self, api_client: AuthenticatedClient):
        """Initialize the track service.

        Args:
            api_client: Authenticated API client for server communication.
        """
        self._client = api_client
        # Cache: key = (track_id, track_config_name)
        self._segments: dict[tuple[int, str | None], list[CornerSegmentInput] | None] = {}
        self._boundaries: dict[tuple[int, str | None], TrackBoundary | None] = {}
        # Cache boundary_id lookups: key = (track_id, track_config_name), value = boundary_id
        self._boundary_ids: dict[tuple[int, str | None], UUID | None] = {}

    def get_corner_segments(
        self, track_id: int, track_config: str | None
    ) -> list[CornerSegmentInput] | None:
        """Fetch corner segments for a track.

        Returns cached segments if available, otherwise fetches from server.

        Args:
            track_id: iRacing track ID
            track_config: Track configuration name (e.g., "Full Course")

        Returns:
            List of corner segments, or None if track has no saved segments.
        """
        cache_key = (track_id, track_config)

        if cache_key in self._segments:
            return self._segments[cache_key]

        # First find the boundary_id for this track
        boundary_id = self._find_boundary_id(track_id, track_config)
        if boundary_id is None:
            logger.debug(f"No track boundary found for track {track_id} ({track_config})")
            self._segments[cache_key] = None
            return None

        # Fetch corner segments for this boundary
        try:
            response = list_corner_segments.sync(boundary_id=boundary_id, client=self._client)

            if isinstance(response, CornerSegmentListResponse):
                if response.total == 0:
                    logger.debug(f"Track {track_id} ({track_config}) has no corner segments")
                    self._segments[cache_key] = None
                    return None

                segments = [
                    CornerSegmentInput(
                        corner_number=corner.corner_number,
                        start_distance=corner.start_distance,
                        end_distance=corner.end_distance,
                    )
                    for corner in response.corners
                ]
                logger.info(
                    f"Fetched {len(segments)} corner segments for track {track_id} ({track_config})"
                )
                self._segments[cache_key] = segments
                return segments
            else:
                logger.warning(f"Failed to fetch corner segments: {response}")
                self._segments[cache_key] = None
                return None

        except Exception as e:
            logger.error(f"Error fetching corner segments: {e}")
            self._segments[cache_key] = None
            return None

    def get_track_boundary(
        self, track_id: int, track_config: str | None
    ) -> TrackBoundary | None:
        """Fetch track boundary for lateral position computation.

        Returns cached boundary if available, otherwise fetches from server.

        Args:
            track_id: iRacing track ID
            track_config: Track configuration name

        Returns:
            TrackBoundary for lateral position computation, or None if not available.
        """
        cache_key = (track_id, track_config)

        if cache_key in self._boundaries:
            return self._boundaries[cache_key]

        # Find the boundary_id for this track
        boundary_id = self._find_boundary_id(track_id, track_config)
        if boundary_id is None:
            self._boundaries[cache_key] = None
            return None

        # Fetch full boundary data
        try:
            response = get_track_boundary.sync(boundary_id=boundary_id, client=self._client)

            if isinstance(response, TrackBoundaryResponse):
                boundary = TrackBoundary(
                    track_id=response.track_id,
                    track_name=response.track_name,
                    track_config_name=response.track_config_name,
                    grid_distance_pct=response.grid_distance_pct,
                    left_latitude=response.left_latitude,
                    left_longitude=response.left_longitude,
                    right_latitude=response.right_latitude,
                    right_longitude=response.right_longitude,
                    grid_size=response.grid_size,
                    source_left_frames=response.source_left_frames,
                    source_right_frames=response.source_right_frames,
                    track_length=response.track_length,
                )
                logger.info(
                    f"Fetched track boundary for {track_id} ({track_config}), "
                    f"grid_size={boundary.grid_size}, track_length={boundary.track_length}"
                )
                self._boundaries[cache_key] = boundary
                return boundary
            else:
                logger.warning(f"Failed to fetch track boundary: {response}")
                self._boundaries[cache_key] = None
                return None

        except Exception as e:
            logger.error(f"Error fetching track boundary: {e}")
            self._boundaries[cache_key] = None
            return None

    def _find_boundary_id(self, track_id: int, track_config: str | None) -> UUID | None:
        """Find the boundary ID for a track by matching track_id and config name.

        Args:
            track_id: iRacing track ID
            track_config: Track configuration name

        Returns:
            UUID of the track boundary, or None if not found.
        """
        cache_key = (track_id, track_config)

        if cache_key in self._boundary_ids:
            return self._boundary_ids[cache_key]

        try:
            response = list_track_boundaries.sync(client=self._client)

            if isinstance(response, TrackBoundaryListResponse):
                for boundary in response.boundaries:
                    if boundary.track_id == track_id:
                        # Match config name (treat empty string as None)
                        boundary_config = boundary.track_config_name or None
                        session_config = track_config or None

                        if boundary_config == session_config:
                            boundary_uuid = UUID(boundary.id)
                            self._boundary_ids[cache_key] = boundary_uuid
                            return boundary_uuid

            self._boundary_ids[cache_key] = None
            return None

        except Exception as e:
            logger.error(f"Error finding boundary ID: {e}")
            self._boundary_ids[cache_key] = None
            return None

    def clear_cache(self) -> None:
        """Clear all cached data.

        Call this when switching sessions or when data may have changed.
        """
        self._segments.clear()
        self._boundaries.clear()
        self._boundary_ids.clear()
        logger.debug("TrackService cache cleared")
