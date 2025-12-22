"""FastAPI route handlers for track boundary management."""

import logging
import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from racing_coach_core.algs.boundary import extract_track_boundary_from_ibt
from racing_coach_server.database.engine import transactional_session
from racing_coach_server.dependencies import AsyncSessionDep, CurrentUserDep
from racing_coach_server.tracks.schemas import (
    TrackBoundaryListResponse,
    TrackBoundaryResponse,
    TrackBoundarySummary,
    TrackBoundaryUploadResponse,
)
from racing_coach_server.tracks.service import TrackBoundaryService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_track_boundary_service(db: AsyncSessionDep) -> TrackBoundaryService:
    """Provide TrackBoundaryService with injected AsyncSession."""
    return TrackBoundaryService(db)


@router.get(
    "",
    response_model=TrackBoundaryListResponse,
    tags=["tracks"],
    operation_id="listTrackBoundaries",
)
async def list_track_boundaries(
    db: AsyncSessionDep,
) -> TrackBoundaryListResponse:
    """List all track boundaries."""
    service = await get_track_boundary_service(db)
    boundaries = await service.list_boundaries()

    summaries = [
        TrackBoundarySummary(
            id=str(b.id),
            track_id=b.track_id,
            track_name=b.track_name,
            track_config_name=b.track_config_name,
            grid_size=b.grid_size,
            created_at=b.created_at,
        )
        for b in boundaries
    ]

    return TrackBoundaryListResponse(boundaries=summaries, total=len(summaries))


@router.get(
    "/{boundary_id}",
    response_model=TrackBoundaryResponse,
    tags=["tracks"],
    operation_id="getTrackBoundary",
)
async def get_track_boundary(
    boundary_id: UUID,
    db: AsyncSessionDep,
) -> TrackBoundaryResponse:
    """Get a track boundary by ID."""
    service = await get_track_boundary_service(db)
    boundary = await service.get_boundary(boundary_id)

    if not boundary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track boundary {boundary_id} not found",
        )

    return TrackBoundaryResponse(
        id=str(boundary.id),
        track_id=boundary.track_id,
        track_name=boundary.track_name,
        track_config_name=boundary.track_config_name,
        grid_distance_pct=list(boundary.grid_distance_pct),
        left_latitude=list(boundary.left_latitude),
        left_longitude=list(boundary.left_longitude),
        right_latitude=list(boundary.right_latitude),
        right_longitude=list(boundary.right_longitude),
        grid_size=boundary.grid_size,
        source_left_frames=boundary.source_left_frames,
        source_right_frames=boundary.source_right_frames,
        created_at=boundary.created_at,
        updated_at=boundary.updated_at,
    )


@router.post(
    "/upload",
    response_model=TrackBoundaryUploadResponse,
    tags=["tracks"],
    operation_id="uploadTrackBoundary",
)
async def upload_track_boundary(
    db: AsyncSessionDep,
    current_user: CurrentUserDep,  # Auth required
    file: UploadFile = File(..., description="IBT file containing boundary laps"),
    left_lap_number: int = Form(default=1, description="Lap number for left boundary"),
    right_lap_number: int = Form(default=3, description="Lap number for right boundary"),
) -> TrackBoundaryUploadResponse:
    """
    Upload an IBT file to generate and store a track boundary.

    The IBT file should contain at least two laps:
    - One lap hugging the left side of the track
    - One lap hugging the right side of the track

    If a boundary already exists for the track+config, it will be replaced.

    Defaults follow the Garage61 collection method:
    - Left boundary: Lap 1 (after reset at start line)
    - Right boundary: Lap 3 (after reset at start line)
    """
    if not file.filename or not file.filename.lower().endswith(".ibt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an IBT file (.ibt extension)",
        )

    # Create temp file with proper cleanup
    tmp_path = None
    try:
        # Write uploaded file to temp location
        with tempfile.NamedTemporaryFile(suffix=".ibt", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(
            f"Processing IBT file: {file.filename} "
            f"(left_lap={left_lap_number}, right_lap={right_lap_number})"
        )

        # Process IBT file with existing algorithm
        try:
            boundary_schema = extract_track_boundary_from_ibt(
                tmp_path,
                left_lap_number=left_lap_number,
                right_lap_number=right_lap_number,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except Exception as e:
            logger.error(f"Error processing IBT file: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process IBT file: {str(e)}",
            ) from e

        # Store in database
        service = await get_track_boundary_service(db)
        async with transactional_session(db):
            boundary, replaced = await service.upsert_boundary(boundary_schema)
            await db.flush()  # Ensure ID is assigned

            action = "updated" if replaced else "created"
            logger.info(
                f"Track boundary {action} for {boundary.track_name} "
                f"(config: {boundary.track_config_name}, id: {boundary.id})"
            )

            return TrackBoundaryUploadResponse(
                status="success",
                message=f"Track boundary {action} successfully",
                boundary_id=str(boundary.id),
                track_name=boundary.track_name,
                track_config_name=boundary.track_config_name,
                replaced_existing=replaced,
            )

    finally:
        # Always cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.delete(
    "/{boundary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["tracks"],
    operation_id="deleteTrackBoundary",
)
async def delete_track_boundary(
    boundary_id: UUID,
    db: AsyncSessionDep,
    current_user: CurrentUserDep,  # Auth required
) -> None:
    """Delete a track boundary."""
    service = await get_track_boundary_service(db)

    async with transactional_session(db):
        deleted = await service.delete_boundary(boundary_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track boundary {boundary_id} not found",
            )
