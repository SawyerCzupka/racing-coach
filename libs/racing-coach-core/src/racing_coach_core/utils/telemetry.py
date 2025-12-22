from datetime import datetime
from pathlib import Path

import irsdk  # pyright: ignore[reportMissingTypeStubs]

from racing_coach_core.schemas.telemetry import SessionFrame, TelemetryFrame, TelemetrySequence


class _IBTFrameAdapter:
    """Adapter to provide dict-like access to IBT frame data for TelemetryDataSource protocol."""

    def __init__(self, ibt: irsdk.IBT, frame_idx: int) -> None:
        self._ibt = ibt
        self._frame_idx = frame_idx

    def __getitem__(self, key: str) -> object:
        return self._ibt.get(self._frame_idx, key)  # pyright: ignore[reportUnknownMemberType]


def get_telemetry_sequence_from_ibt(ibt_path: str | Path) -> TelemetrySequence:
    """Read an IBT file and convert it to a TelemetrySequence

    Args:
        ibt_path (str | Path): path to the IBT file

    Returns:
        TelemetrySequence: sequence of TelemetryFrame objects
    """
    ibt = irsdk.IBT()
    ibt.open(ibt_file=ibt_path)  # pyright: ignore[reportUnknownMemberType]

    try:
        session_times: list[float] | None = ibt.get_all("SessionTime")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        total_frames = len(session_times) if session_times else 0

        frames: list[TelemetryFrame] = []
        timestamp = datetime.now()

        for frame_idx in range(total_frames):
            adapter = _IBTFrameAdapter(ibt, frame_idx)
            frame = TelemetryFrame.from_irsdk(adapter, timestamp)
            frames.append(frame)

        return TelemetrySequence(frames=frames)
    finally:
        ibt.close()  # pyright: ignore[reportUnknownMemberType]


def get_session_frame_from_ibt(ibt_path: str | Path) -> SessionFrame:
    """Read an IBT file and extract session metadata.

    Args:
        ibt_path (str | Path): path to the IBT file

    Returns:
        SessionFrame: session metadata extracted from the IBT file
    """
    ir = irsdk.IRSDK()
    ir.startup(test_file=str(ibt_path))  # pyright: ignore[reportUnknownMemberType]

    try:
        return SessionFrame.from_irsdk(ir, datetime.now())  # pyright: ignore[reportArgumentType]
    finally:
        ir.shutdown()  # pyright: ignore[reportUnknownMemberType]
