"""Track boundary models for lateral position calculation."""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Self

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from .telemetry import TelemetryFrame, TelemetrySequence

logger = logging.getLogger(__name__)


class TrackBoundary(BaseModel):
    """
    Track boundary data for a specific track configuration.

    Stores left and right boundary GPS coordinates indexed by lap_distance_pct.
    Boundaries are normalized to a common grid for efficient lookup.

    Part 1 of the track boundary workflow: Create once per track from boundary laps,
    then save to file for reuse.
    """

    # Track identification
    track_id: int = Field(description="iRacing track ID")
    track_name: str = Field(description="Track name")
    track_config_name: str | None = Field(default=None, description="Track configuration name")

    # Boundary data - stored as aligned arrays for efficient computation
    # All arrays have the same length (grid_size)
    grid_distance_pct: list[float] = Field(
        description="Normalized lap distance grid points (0.0 to 1.0)"
    )
    left_latitude: list[float] = Field(description="Left boundary latitudes")
    left_longitude: list[float] = Field(description="Left boundary longitudes")
    right_latitude: list[float] = Field(description="Right boundary latitudes")
    right_longitude: list[float] = Field(description="Right boundary longitudes")

    # Metadata
    grid_size: int = Field(description="Number of grid points")
    source_left_frames: int = Field(description="Original frame count for left boundary lap")
    source_right_frames: int = Field(description="Original frame count for right boundary lap")

    @classmethod
    def from_boundary_laps(
        cls,
        track_id: int,
        track_name: str,
        left_lap_data: pd.DataFrame,  # columns: lap_distance_pct, latitude, longitude
        right_lap_data: pd.DataFrame,  # columns: lap_distance_pct, latitude, longitude
        track_config_name: str | None = None,
        grid_size: int = 1000,
    ) -> Self:
        """
        Create a TrackBoundary from raw boundary lap data.

        Normalizes both boundary laps to a common grid using interpolation.

        Args:
            track_id: iRacing track ID
            track_name: Track name
            left_lap_data: DataFrame with lap_distance_pct, latitude, longitude for left boundary
            right_lap_data: DataFrame with lap_distance_pct, latitude, longitude for right boundary
            track_config_name: Optional track configuration name
            grid_size: Number of points in normalized grid (default: 1000)

        Returns:
            TrackBoundary with interpolated boundary data
        """
        # Create uniform grid from 0.0 to just under 1.0
        grid = np.linspace(0.0, 1.0, grid_size, endpoint=True)

        # Process left boundary
        left_sorted = left_lap_data.sort_values("lap_distance_pct").drop_duplicates(
            subset="lap_distance_pct", keep="first"
        )

        # Ensure we have data at 0.0 and near 1.0 for proper interpolation
        left_dist = left_sorted["lap_distance_pct"].values
        left_lat = left_sorted["latitude"].values
        left_lon = left_sorted["longitude"].values

        # Use numpy interp with handling for wrap-around
        left_lat_interp = np.interp(grid, left_dist, left_lat)
        left_lon_interp = np.interp(grid, left_dist, left_lon)

        # Process right boundary
        right_sorted = right_lap_data.sort_values("lap_distance_pct").drop_duplicates(
            subset="lap_distance_pct", keep="first"
        )

        right_dist = right_sorted["lap_distance_pct"].values
        right_lat = right_sorted["latitude"].values
        right_lon = right_sorted["longitude"].values

        right_lat_interp = np.interp(grid, right_dist, right_lat)
        right_lon_interp = np.interp(grid, right_dist, right_lon)

        logger.info(
            f"Created TrackBoundary for {track_name}: "
            f"left={len(left_lap_data)} frames, right={len(right_lap_data)} frames, "
            f"grid_size={grid_size}"
        )

        return cls(
            track_id=track_id,
            track_name=track_name,
            track_config_name=track_config_name,
            grid_distance_pct=grid.tolist(),
            left_latitude=left_lat_interp.tolist(),
            left_longitude=left_lon_interp.tolist(),
            right_latitude=right_lat_interp.tolist(),
            right_longitude=right_lon_interp.tolist(),
            grid_size=grid_size,
            source_left_frames=len(left_lap_data),
            source_right_frames=len(right_lap_data),
        )

    def to_parquet(self, file_path: str | Path) -> None:
        """Save track boundary to Parquet format."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        file_path = Path(file_path)

        # Create DataFrame from boundary data
        df = pd.DataFrame(
            {
                "grid_distance_pct": self.grid_distance_pct,
                "left_latitude": self.left_latitude,
                "left_longitude": self.left_longitude,
                "right_latitude": self.right_latitude,
                "right_longitude": self.right_longitude,
            }
        )

        # Convert to pyarrow table
        table = pa.Table.from_pandas(df)

        # Store metadata in parquet file metadata
        metadata = {
            b"track_id": str(self.track_id).encode(),
            b"track_name": self.track_name.encode(),
            b"track_config_name": (self.track_config_name or "").encode(),
            b"grid_size": str(self.grid_size).encode(),
            b"source_left_frames": str(self.source_left_frames).encode(),
            b"source_right_frames": str(self.source_right_frames).encode(),
        }

        # Merge with existing metadata and create new schema
        existing_metadata = table.schema.metadata or {}
        merged_metadata = {**existing_metadata, **metadata}
        new_schema = table.schema.with_metadata(merged_metadata)
        table = table.cast(new_schema)

        # Write with metadata
        pq.write_table(table, file_path)

        logger.info(f"Saved TrackBoundary to {file_path}")

    @classmethod
    def from_parquet(cls, file_path: str | Path) -> Self:
        """Load track boundary from Parquet format."""
        import pyarrow.parquet as pq

        file_path = Path(file_path)

        # Read parquet file with metadata
        table = pq.read_table(file_path)
        metadata = table.schema.metadata or {}

        df = table.to_pandas()

        # Extract metadata (stored as bytes)
        def get_meta(key: str, default: str = "") -> str:
            value = metadata.get(key.encode(), default.encode())
            return value.decode() if isinstance(value, bytes) else value

        track_config_name = get_meta("track_config_name")

        return cls(
            track_id=int(get_meta("track_id", "0")),
            track_name=get_meta("track_name", "Unknown"),
            track_config_name=track_config_name if track_config_name else None,
            grid_distance_pct=df["grid_distance_pct"].tolist(),
            left_latitude=df["left_latitude"].tolist(),
            left_longitude=df["left_longitude"].tolist(),
            right_latitude=df["right_latitude"].tolist(),
            right_longitude=df["right_longitude"].tolist(),
            grid_size=int(get_meta("grid_size", str(len(df)))),
            source_left_frames=int(get_meta("source_left_frames", "0")),
            source_right_frames=int(get_meta("source_right_frames", "0")),
        )


class AugmentedTelemetryFrame(TelemetryFrame):
    """
    TelemetryFrame extended with computed lateral position.

    Inherits all fields from TelemetryFrame and adds:
    - lateral_position: Normalized position between track boundaries
    """

    lateral_position: float = Field(
        description="Lateral position: -1.0=left edge, 0.0=center, 1.0=right edge. "
        "Values outside [-1, 1] indicate car is beyond boundaries."
    )

    @classmethod
    def from_telemetry_frame(
        cls,
        frame: TelemetryFrame,
        lateral_position: float,
    ) -> Self:
        """Create an AugmentedTelemetryFrame from a TelemetryFrame."""
        return cls(
            **frame.model_dump(),
            lateral_position=lateral_position,
        )


class AugmentedTelemetrySequence(BaseModel):
    """
    Efficient storage for augmented telemetry data.

    Stores lateral positions separately for memory efficiency,
    allowing bulk computation and numpy operations.
    """

    frames: list[TelemetryFrame] = Field(description="Original telemetry frames")
    lateral_positions: list[float] = Field(
        description="Lateral positions for each frame (-1 to 1, can exceed for off-track)"
    )

    def __len__(self) -> int:
        return len(self.frames)

    def get_augmented_frame(self, index: int) -> AugmentedTelemetryFrame:
        """Get a single augmented frame by index."""
        return AugmentedTelemetryFrame.from_telemetry_frame(
            self.frames[index],
            self.lateral_positions[index],
        )

    def iter_augmented(self) -> Iterator[AugmentedTelemetryFrame]:
        """Iterate over all frames as AugmentedTelemetryFrames."""
        for frame, lat_pos in zip(self.frames, self.lateral_positions):
            yield AugmentedTelemetryFrame.from_telemetry_frame(frame, lat_pos)

    @classmethod
    def from_telemetry_sequence(
        cls,
        sequence: TelemetrySequence,
        lateral_positions: list[float],
    ) -> Self:
        """Create from a TelemetrySequence and computed lateral positions."""
        if len(sequence.frames) != len(lateral_positions):
            raise ValueError(
                f"Frame count ({len(sequence.frames)}) does not match "
                f"lateral position count ({len(lateral_positions)})"
            )
        return cls(frames=sequence.frames, lateral_positions=lateral_positions)

    def to_parquet(self, file_path: str | Path) -> None:
        """Save to Parquet with lateral positions included."""
        file_path = Path(file_path)

        # Convert frames to dict and add lateral positions
        data = []
        for frame, lat_pos in zip(self.frames, self.lateral_positions):
            frame_dict = frame.model_dump()
            frame_dict["lateral_position"] = lat_pos
            data.append(frame_dict)

        df = pd.DataFrame(data)
        df.to_parquet(file_path)

        logger.info(f"Saved AugmentedTelemetrySequence ({len(self)} frames) to {file_path}")

    @classmethod
    def from_parquet(cls, file_path: str | Path) -> Self:
        """Load from Parquet."""
        file_path = Path(file_path)
        df = pd.read_parquet(file_path)

        # Extract lateral positions
        lateral_positions = df["lateral_position"].tolist()

        # Remove lateral_position column and create TelemetryFrames
        df = df.drop(columns=["lateral_position"])
        frames = [TelemetryFrame(**row) for _, row in df.iterrows()]  # type: ignore

        return cls(frames=frames, lateral_positions=lateral_positions)
