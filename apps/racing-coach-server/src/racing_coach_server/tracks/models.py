"""SQLAlchemy models for track boundary storage."""

import uuid
from typing import Self

from racing_coach_core.schemas.track import TrackBoundary as TrackBoundarySchema
from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from racing_coach_server.database.base import Base
from racing_coach_server.database.mixins import TimestampMixin


class TrackBoundary(TimestampMixin, Base):
    """Model representing a track boundary."""

    __tablename__ = "track_boundary"

    # Track identification (non-default fields first for MappedAsDataclass)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    track_config_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Boundary data - PostgreSQL ARRAY columns for grid points
    grid_distance_pct: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # pyright: ignore[reportUnknownArgumentType]
    left_latitude: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # pyright: ignore[reportUnknownArgumentType]
    left_longitude: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # pyright: ignore[reportUnknownArgumentType]
    right_latitude: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # pyright: ignore[reportUnknownArgumentType]
    right_longitude: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # pyright: ignore[reportUnknownArgumentType]

    # Metadata
    grid_size: Mapped[int] = mapped_column(Integer, nullable=False)
    source_left_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    source_right_frames: Mapped[int] = mapped_column(Integer, nullable=False)
    track_length: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # Default field (must come after non-default fields)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4
    )

    # Relationships
    corner_segments: Mapped[list["CornerSegment"]] = relationship(
        "CornerSegment",
        back_populates="track_boundary",
        cascade="all, delete-orphan",
        order_by="CornerSegment.sort_order",
        init=False,
    )

    __table_args__ = (
        UniqueConstraint("track_id", "track_config_name", name="uq_track_boundary_track_config"),
        Index("idx_track_boundary_track_id", "track_id"),
    )

    def to_schema(self) -> TrackBoundarySchema:
        """Convert to Pydantic schema."""
        return TrackBoundarySchema(
            track_id=self.track_id,
            track_name=self.track_name,
            track_config_name=self.track_config_name,
            grid_distance_pct=list(self.grid_distance_pct),
            left_latitude=list(self.left_latitude),
            left_longitude=list(self.left_longitude),
            right_latitude=list(self.right_latitude),
            right_longitude=list(self.right_longitude),
            grid_size=self.grid_size,
            source_left_frames=self.source_left_frames,
            source_right_frames=self.source_right_frames,
            track_length=self.track_length,
        )

    @classmethod
    def from_schema(cls, schema: TrackBoundarySchema) -> Self:
        """Create from Pydantic schema."""
        return cls(
            track_id=schema.track_id,
            track_name=schema.track_name,
            track_config_name=schema.track_config_name,
            grid_distance_pct=schema.grid_distance_pct,
            left_latitude=schema.left_latitude,
            left_longitude=schema.left_longitude,
            right_latitude=schema.right_latitude,
            right_longitude=schema.right_longitude,
            grid_size=schema.grid_size,
            source_left_frames=schema.source_left_frames,
            source_right_frames=schema.source_right_frames,
            track_length=schema.track_length,
        )


class CornerSegment(TimestampMixin, Base):
    """Model representing a corner segment on a track."""

    __tablename__ = "corner_segment"

    # Foreign key to track boundary (non-default field first)
    track_boundary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("track_boundary.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Corner boundaries in meters
    start_distance: Mapped[float] = mapped_column(Float, nullable=False)
    end_distance: Mapped[float] = mapped_column(Float, nullable=False)

    # Sort order for corner numbering (1-indexed corner number)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Default field (must come after non-default fields)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default_factory=uuid.uuid4
    )

    # Relationships
    track_boundary: Mapped["TrackBoundary"] = relationship(
        "TrackBoundary",
        back_populates="corner_segments",
        init=False,
    )

    __table_args__ = (
        Index("idx_corner_segment_boundary", "track_boundary_id"),
        UniqueConstraint("track_boundary_id", "sort_order", name="uq_corner_segment_order"),
    )
