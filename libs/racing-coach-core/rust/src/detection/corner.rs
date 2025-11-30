//! Corner detection.

use crate::results::{CornerMetrics, CornerMetricsBuilder};
use crate::types::{AnalysisConfig, TelemetryFrame};
use crate::utils::wrap_distance;

use super::EventDetector;

/// State for corner detection.
#[derive(Debug, Clone, Copy, PartialEq)]
enum CornerState {
    /// Not currently in a corner
    Idle,
    /// In a corner
    Active,
}

/// Detector for corners using a state machine approach.
///
/// Tracks when steering angle crosses the threshold and accumulates
/// metrics including apex (max lateral G), minimum speed, and throttle application.
pub struct CornerDetector<'a> {
    config: &'a AnalysisConfig,
    state: CornerState,
    builder: Option<CornerMetricsBuilder>,
    current_end_idx: usize,
}

impl<'a> CornerDetector<'a> {
    /// Create a new corner detector with the given configuration.
    pub fn new(config: &'a AnalysisConfig) -> Self {
        Self {
            config,
            state: CornerState::Idle,
            builder: None,
            current_end_idx: 0,
        }
    }

    /// Finalize a builder into CornerMetrics using the full frame slice.
    pub fn finalize_builder(
        &self,
        builder: CornerMetricsBuilder,
        frames: &[TelemetryFrame],
        end_idx: usize,
    ) -> CornerMetrics {
        let exit_frame = &frames[end_idx.min(frames.len() - 1)];

        // Calculate time in corner
        let time_in_corner = exit_frame.timestamp - builder.turn_in_timestamp;

        // Calculate corner distance with wrap-around handling
        let corner_distance = wrap_distance(exit_frame.lap_distance - builder.turn_in_distance);

        // Calculate speed deltas
        let speed_loss = builder.turn_in_speed - builder.min_speed;
        let speed_gain = exit_frame.speed - builder.min_speed;

        CornerMetrics::new(
            builder.turn_in_distance,
            builder.apex_distance,
            exit_frame.lap_distance,
            if builder.throttle_applied {
                builder.throttle_distance
            } else {
                exit_frame.lap_distance
            },
            builder.turn_in_speed,
            builder.min_speed, // apex_speed = min speed in corner
            exit_frame.speed,
            if builder.throttle_applied {
                builder.throttle_speed
            } else {
                exit_frame.speed
            },
            builder.max_lateral_g,
            time_in_corner,
            corner_distance,
            builder.max_steering,
            speed_loss,
            speed_gain,
        )
    }
}

impl EventDetector for CornerDetector<'_> {
    type Builder = CornerMetricsBuilder;

    fn process_frame(&mut self, frame: &TelemetryFrame, index: usize) -> Option<Self::Builder> {
        let is_turning = frame.steering_angle.abs() > self.config.steering_threshold;

        match self.state {
            CornerState::Idle => {
                if is_turning {
                    // Start new corner
                    self.state = CornerState::Active;
                    self.builder = Some(CornerMetricsBuilder::new(
                        index,
                        frame.lap_distance,
                        frame.speed,
                        frame.timestamp,
                        frame.lateral_acceleration,
                        frame.steering_angle,
                    ));
                    self.current_end_idx = index;
                }
                None
            }
            CornerState::Active => {
                if is_turning {
                    // Continue in corner - update builder
                    if let Some(ref mut builder) = self.builder {
                        builder.update(
                            index,
                            frame.lap_distance,
                            frame.speed,
                            frame.lateral_acceleration,
                            frame.steering_angle,
                            frame.throttle,
                            self.config.throttle_threshold,
                        );
                    }
                    self.current_end_idx = index;
                    None
                } else {
                    // Exit corner - return completed builder
                    self.state = CornerState::Idle;
                    self.builder.take()
                }
            }
        }
    }

    fn finalize(&mut self) -> Option<Self::Builder> {
        if self.state == CornerState::Active {
            self.state = CornerState::Idle;
            self.builder.take()
        } else {
            None
        }
    }

    fn reset(&mut self) {
        self.state = CornerState::Idle;
        self.builder = None;
        self.current_end_idx = 0;
    }
}

/// Extract all corners from telemetry frames.
///
/// This is the standalone function for extracting corners
/// when you don't need the unified single-pass approach.
///
/// # Arguments
/// * `frames` - Slice of telemetry frames
/// * `config` - Analysis configuration
///
/// # Returns
/// * Vector of CornerMetrics for each detected corner
pub fn extract_corners(frames: &[TelemetryFrame], config: &AnalysisConfig) -> Vec<CornerMetrics> {
    if frames.is_empty() {
        return vec![];
    }

    let mut detector = CornerDetector::new(config);
    let mut results = Vec::with_capacity(25); // Pre-allocate for typical lap
    let mut pending_builders: Vec<(CornerMetricsBuilder, usize)> = Vec::new();

    for (idx, frame) in frames.iter().enumerate() {
        if let Some(builder) = detector.process_frame(frame, idx) {
            // Corner ended at previous frame
            pending_builders.push((builder, idx.saturating_sub(1)));
        }
    }

    // Handle any in-progress corner at end of lap
    if let Some(builder) = detector.finalize() {
        pending_builders.push((builder, frames.len() - 1));
    }

    // Finalize all builders
    for (builder, end_idx) in pending_builders {
        results.push(detector.finalize_builder(builder, frames, end_idx));
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_frame(
        steering: f64,
        speed: f64,
        lateral_g: f64,
        lap_distance: f64,
        timestamp: f64,
        throttle: f64,
    ) -> TelemetryFrame {
        TelemetryFrame::new(
            0.0,
            throttle,
            speed,
            lap_distance,
            steering,
            lateral_g,
            0.0,
            timestamp,
        )
    }

    fn default_config() -> AnalysisConfig {
        AnalysisConfig::default()
    }

    #[test]
    fn test_no_corners() {
        let frames = vec![
            make_frame(0.0, 50.0, 0.0, 0.0, 0.0, 0.5), // Straight
            make_frame(0.0, 50.0, 0.0, 0.1, 1.0, 0.5),
            make_frame(0.0, 50.0, 0.0, 0.2, 2.0, 0.5),
        ];

        let corners = extract_corners(&frames, &default_config());
        assert!(corners.is_empty());
    }

    #[test]
    fn test_single_corner() {
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.30, 0.0, 0.0),  // Straight
            make_frame(0.2, 55.0, 1.5, 0.32, 0.5, 0.0),  // Turn in
            make_frame(0.3, 45.0, 2.5, 0.35, 1.0, 0.0),  // Apex (max lateral G)
            make_frame(0.2, 50.0, 2.0, 0.38, 1.5, 0.1),  // Throttle applied
            make_frame(0.0, 60.0, 0.5, 0.40, 2.0, 0.5),  // Exit
        ];

        let corners = extract_corners(&frames, &default_config());
        assert_eq!(corners.len(), 1);

        let corner = &corners[0];
        assert_eq!(corner.turn_in_distance, 0.32);
        assert_eq!(corner.turn_in_speed, 55.0);
        assert_eq!(corner.apex_distance, 0.35); // Where max lateral G occurred
        assert_eq!(corner.apex_speed, 45.0); // Minimum speed
        assert_eq!(corner.max_lateral_g, 2.5);
        assert_eq!(corner.max_steering_angle, 0.3);
        assert!(corner.throttle_application_distance > 0.0);
    }

    #[test]
    fn test_apex_is_max_lateral_g() {
        // Apex should be where lateral G is maximum, not where speed is minimum
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.30, 0.0, 0.0),
            make_frame(0.2, 50.0, 1.5, 0.32, 0.5, 0.0), // Lower speed here
            make_frame(0.3, 55.0, 2.5, 0.35, 1.0, 0.0), // But max lateral G here
            make_frame(0.0, 60.0, 0.5, 0.40, 1.5, 0.5),
        ];

        let corners = extract_corners(&frames, &default_config());
        assert_eq!(corners.len(), 1);

        let corner = &corners[0];
        assert_eq!(corner.apex_distance, 0.35); // Max lateral G location
        assert_eq!(corner.apex_speed, 50.0); // But apex_speed is minimum speed
    }

    #[test]
    fn test_multiple_corners() {
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.10, 0.0, 0.5),
            make_frame(0.3, 45.0, 2.0, 0.15, 1.0, 0.0), // Corner 1
            make_frame(0.0, 55.0, 0.0, 0.20, 2.0, 0.5), // Straight
            make_frame(0.0, 60.0, 0.0, 0.50, 3.0, 0.5),
            make_frame(-0.3, 40.0, 2.5, 0.55, 4.0, 0.0), // Corner 2 (left turn)
            make_frame(0.0, 50.0, 0.0, 0.60, 5.0, 0.5),
        ];

        let corners = extract_corners(&frames, &default_config());
        assert_eq!(corners.len(), 2);
    }

    #[test]
    fn test_corner_at_lap_end() {
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.90, 0.0, 0.5),
            make_frame(0.3, 45.0, 2.0, 0.95, 1.0, 0.0), // Turn in
            make_frame(0.3, 40.0, 2.5, 0.99, 2.0, 0.0), // Still in corner at lap end
        ];

        let corners = extract_corners(&frames, &default_config());
        assert_eq!(corners.len(), 1); // Should detect
    }

    #[test]
    fn test_lap_wraparound_distance() {
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.95, 0.0, 0.5),
            make_frame(0.3, 45.0, 2.0, 0.98, 1.0, 0.0), // Turn in near S/F
            make_frame(0.3, 40.0, 2.5, 0.02, 2.0, 0.0), // Cross S/F line
            make_frame(0.0, 50.0, 0.5, 0.05, 3.0, 0.5), // Exit
        ];

        let corners = extract_corners(&frames, &default_config());
        assert_eq!(corners.len(), 1);

        let corner = &corners[0];
        // Corner distance should handle wrap correctly: 0.05 - 0.98 + 1.0 = 0.07
        assert!((corner.corner_distance - 0.07).abs() < 0.01);
    }

    #[test]
    fn test_empty_frames() {
        let frames: Vec<TelemetryFrame> = vec![];
        let corners = extract_corners(&frames, &default_config());
        assert!(corners.is_empty());
    }

    #[test]
    fn test_throttle_application_point() {
        let frames = vec![
            make_frame(0.0, 60.0, 0.0, 0.30, 0.0, 0.0),
            make_frame(0.3, 50.0, 2.0, 0.32, 0.5, 0.0),  // No throttle yet
            make_frame(0.3, 45.0, 2.5, 0.35, 1.0, 0.0),  // Apex, no throttle
            make_frame(0.2, 48.0, 2.0, 0.38, 1.5, 0.1),  // First throttle
            make_frame(0.2, 52.0, 1.5, 0.40, 2.0, 0.3),  // More throttle
            make_frame(0.0, 60.0, 0.5, 0.42, 2.5, 0.5),  // Exit
        ];

        let corners = extract_corners(&frames, &default_config());
        let corner = &corners[0];

        assert_eq!(corner.throttle_application_distance, 0.38);
        assert_eq!(corner.throttle_application_speed, 48.0);
    }
}
