"""Service for track boundary management."""

import logging
from uuid import UUID

from racing_coach_core.schemas.track import TrackBoundary as TrackBoundarySchema
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from racing_coach_server.tracks.models import CornerSegment, TrackBoundary
from racing_coach_server.tracks.schemas import CornerSegmentCreate

logger = logging.getLogger(__name__)


class TrackBoundaryService:
    """Service for track boundary operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_boundaries(self) -> list[TrackBoundary]:
        """
        List all track boundaries ordered by track name.

        Returns:
            List of all track boundaries
        """
        stmt = select(TrackBoundary).order_by(TrackBoundary.track_name)
        result = await self.db.execute(stmt)
        boundaries = list(result.scalars().all())

        logger.debug(f"Found {len(boundaries)} track boundaries")
        return boundaries

    async def get_boundary(self, boundary_id: UUID) -> TrackBoundary | None:
        """
        Get a track boundary by ID.

        Args:
            boundary_id: The UUID of the boundary

        Returns:
            The track boundary or None if not found
        """
        stmt = select(TrackBoundary).where(TrackBoundary.id == boundary_id)
        result = await self.db.execute(stmt)
        boundary = result.scalar_one_or_none()

        if boundary:
            logger.debug(f"Found track boundary {boundary_id}")
        else:
            logger.debug(f"No track boundary found with ID {boundary_id}")

        return boundary

    async def get_boundary_by_track(
        self, track_id: int, track_config_name: str | None
    ) -> TrackBoundary | None:
        """
        Get a track boundary by track ID and config name.

        Args:
            track_id: The iRacing track ID
            track_config_name: The track configuration name (can be None)

        Returns:
            The track boundary or None if not found
        """
        if track_config_name is None:
            stmt = select(TrackBoundary).where(
                and_(
                    TrackBoundary.track_id == track_id,
                    TrackBoundary.track_config_name.is_(None),
                )
            )
        else:
            stmt = select(TrackBoundary).where(
                and_(
                    TrackBoundary.track_id == track_id,
                    TrackBoundary.track_config_name == track_config_name,
                )
            )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_boundary(
        self, boundary_schema: TrackBoundarySchema
    ) -> tuple[TrackBoundary, bool]:
        """
        Create or update a track boundary.

        If a boundary with the same track_id and track_config_name exists,
        it will be updated. Otherwise, a new boundary is created.

        Args:
            boundary_schema: The TrackBoundary Pydantic schema

        Returns:
            Tuple of (boundary, replaced_existing) where replaced_existing
            indicates if an existing boundary was updated
        """
        existing = await self.get_boundary_by_track(
            boundary_schema.track_id, boundary_schema.track_config_name
        )

        if existing:
            # Update existing boundary
            existing.track_name = boundary_schema.track_name
            existing.grid_distance_pct = boundary_schema.grid_distance_pct
            existing.left_latitude = boundary_schema.left_latitude
            existing.left_longitude = boundary_schema.left_longitude
            existing.right_latitude = boundary_schema.right_latitude
            existing.right_longitude = boundary_schema.right_longitude
            existing.grid_size = boundary_schema.grid_size
            existing.source_left_frames = boundary_schema.source_left_frames
            existing.source_right_frames = boundary_schema.source_right_frames
            existing.track_length = boundary_schema.track_length

            logger.info(
                f"Updated track boundary for {boundary_schema.track_name} "
                f"(config: {boundary_schema.track_config_name})"
            )
            return existing, True
        else:
            # Create new boundary
            new_boundary = TrackBoundary.from_schema(boundary_schema)
            self.db.add(new_boundary)

            logger.info(
                f"Created track boundary for {boundary_schema.track_name} "
                f"(config: {boundary_schema.track_config_name})"
            )
            return new_boundary, False

    async def delete_boundary(self, boundary_id: UUID) -> bool:
        """
        Delete a track boundary.

        Args:
            boundary_id: The UUID of the boundary to delete

        Returns:
            True if deleted, False if not found
        """
        boundary = await self.get_boundary(boundary_id)
        if boundary:
            await self.db.delete(boundary)
            logger.info(
                f"Deleted track boundary {boundary_id} "
                f"({boundary.track_name} - {boundary.track_config_name})"
            )
            return True

        logger.debug(f"No track boundary found to delete with ID {boundary_id}")
        return False


class CornerSegmentService:
    """Service for corner segment operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_corners(self, boundary_id: UUID) -> list[CornerSegment]:
        """
        List all corner segments for a track boundary, ordered by sort_order.

        Args:
            boundary_id: The UUID of the track boundary

        Returns:
            List of corner segments ordered by sort_order
        """
        stmt = (
            select(CornerSegment)
            .where(CornerSegment.track_boundary_id == boundary_id)
            .order_by(CornerSegment.sort_order)
        )
        result = await self.db.execute(stmt)
        corners = list(result.scalars().all())

        logger.debug(f"Found {len(corners)} corner segments for boundary {boundary_id}")
        return corners

    async def get_corner(self, corner_id: UUID) -> CornerSegment | None:
        """
        Get a corner segment by ID.

        Args:
            corner_id: The UUID of the corner segment

        Returns:
            The corner segment or None if not found
        """
        stmt = select(CornerSegment).where(CornerSegment.id == corner_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_create_corners(
        self,
        boundary_id: UUID,
        corners: list[CornerSegmentCreate],
    ) -> list[CornerSegment]:
        """
        Replace all corner segments for a track boundary.

        Deletes existing corners and creates new ones from the provided list.
        Sort order is assigned based on the order in the list.

        Args:
            boundary_id: The UUID of the track boundary
            corners: List of corner segment data in order

        Returns:
            List of created corner segments
        """
        # Delete existing corners
        existing = await self.list_corners(boundary_id)
        for corner in existing:
            await self.db.delete(corner)

        # Flush deletes before inserting to avoid unique constraint violations
        await self.db.flush()

        # Create new corners with sort_order based on list position
        created_corners = []
        for idx, corner_data in enumerate(corners):
            corner = CornerSegment(
                track_boundary_id=boundary_id,
                start_distance=corner_data.start_distance,
                end_distance=corner_data.end_distance,
                sort_order=idx + 1,  # 1-indexed
            )
            self.db.add(corner)
            created_corners.append(corner)

        await self.db.flush()  # Ensure IDs are assigned

        logger.info(f"Created {len(created_corners)} corner segments for boundary {boundary_id}")
        return created_corners

    async def update_corner(
        self,
        corner_id: UUID,
        corner_data: CornerSegmentCreate,
    ) -> CornerSegment | None:
        """
        Update a corner segment's boundaries.

        Args:
            corner_id: The UUID of the corner segment
            corner_data: New start/end distances

        Returns:
            The updated corner segment or None if not found
        """
        corner = await self.get_corner(corner_id)
        if corner:
            corner.start_distance = corner_data.start_distance
            corner.end_distance = corner_data.end_distance
            logger.info(f"Updated corner segment {corner_id}")
            return corner

        logger.debug(f"No corner segment found with ID {corner_id}")
        return None

    async def delete_corner(self, corner_id: UUID) -> bool:
        """
        Delete a corner segment and renumber remaining corners.

        Args:
            corner_id: The UUID of the corner segment to delete

        Returns:
            True if deleted, False if not found
        """
        corner = await self.get_corner(corner_id)
        if not corner:
            logger.debug(f"No corner segment found to delete with ID {corner_id}")
            return False

        boundary_id = corner.track_boundary_id
        deleted_sort_order = corner.sort_order

        await self.db.delete(corner)

        # Renumber remaining corners
        remaining = await self.list_corners(boundary_id)
        for remaining_corner in remaining:
            if remaining_corner.sort_order > deleted_sort_order:
                remaining_corner.sort_order -= 1

        logger.info(f"Deleted corner segment {corner_id} and renumbered remaining corners")
        return True
