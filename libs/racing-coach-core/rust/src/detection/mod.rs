//! Event detection for braking zones and corners.

mod braking;
mod corner;

pub use braking::{extract_braking_zones, BrakingDetector};
pub use corner::{extract_corners, CornerDetector};

use crate::types::TelemetryFrame;

/// Trait for detecting driving events from telemetry frames.
///
/// Each detector is a state machine that processes frames one-by-one,
/// potentially producing events when state transitions occur.
pub trait EventDetector {
    /// The builder type used to accumulate event data during detection.
    type Builder;

    /// Process a single frame, potentially completing an event.
    ///
    /// Returns `Some(builder)` when an event is completed (state transition
    /// from active to idle). The caller should finalize the builder into
    /// a result using the full frame slice.
    fn process_frame(&mut self, frame: &TelemetryFrame, index: usize) -> Option<Self::Builder>;

    /// Finalize any in-progress event at the end of the sequence.
    ///
    /// Call this after processing all frames to handle events that
    /// extend to the end of the data (e.g., a braking zone that
    /// doesn't end before the lap ends).
    fn finalize(&mut self) -> Option<Self::Builder>;

    /// Reset the detector to its initial state.
    ///
    /// Call this before processing a new lap to clear any accumulated state.
    fn reset(&mut self);
}
