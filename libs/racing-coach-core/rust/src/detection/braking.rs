//! Braking zone detection.

use crate::analysis::{calculate_deceleration, detect_trail_braking};
use crate::results::{BrakingMetrics, BrakingMetricsBuilder};
use crate::types::{AnalysisConfig, TelemetryFrame};

use super::EventDetector;

/// State for braking zone detection.
#[derive(Debug, Clone, Copy, PartialEq)]
enum BrakingState {
    /// Not currently in a braking zone
    Idle,
    /// In a braking zone, tracking since start_idx
    Active,
}

/// Detector for braking zones using a state machine approach.
///
/// Tracks when brake pressure crosses the threshold and accumulates
/// metrics until the braking zone ends.
pub struct BrakingDetector<'a> {
    config: &'a AnalysisConfig,
    state: BrakingState,
    builder: Option<BrakingMetricsBuilder>,
    current_end_idx: usize,
}

impl<'a> BrakingDetector<'a> {
    /// Create a new braking detector with the given configuration.
    pub fn new(config: &'a AnalysisConfig) -> Self {
        Self {
            config,
            state: BrakingState::Idle,
            builder: None,
            current_end_idx: 0,
        }
    }

    /// Finalize a builder into BrakingMetrics using the full frame slice.
    pub fn finalize_builder(
        &self,
        builder: BrakingMetricsBuilder,
        frames: &[TelemetryFrame],
        end_idx: usize,
    ) -> BrakingMetrics {
        let end_frame = &frames[end_idx.min(frames.len() - 1)];

        // Calculate deceleration metrics
        let initial_decel = calculate_deceleration(
            frames,
            builder.start_idx,
            (builder.start_idx + self.config.decel_window).min(end_idx),
        );
        let avg_decel = calculate_deceleration(frames, builder.start_idx, end_idx);

        // Braking efficiency: |deceleration| / brake_pressure
        let efficiency = if builder.max_pressure > 0.0 {
            avg_decel.abs() / builder.max_pressure
        } else {
            0.0
        };

        // Detect trail braking
        let trail_info = detect_trail_braking(frames, builder.start_idx, end_idx, self.config);

        // Calculate duration
        let duration = end_frame.timestamp - builder.start_timestamp;

        BrakingMetrics::new(
            builder.start_distance,
            builder.start_speed,
            end_frame.lap_distance,
            builder.max_pressure,
            duration,
            builder.min_speed,
            initial_decel,
            avg_decel,
            efficiency,
            trail_info.has_trail_braking,
            trail_info.distance,
            trail_info.percentage,
        )
    }
}

impl EventDetector for BrakingDetector<'_> {
    type Builder = BrakingMetricsBuilder;

    fn process_frame(&mut self, frame: &TelemetryFrame, index: usize) -> Option<Self::Builder> {
        let is_braking = frame.brake > self.config.brake_threshold;

        match self.state {
            BrakingState::Idle => {
                if is_braking {
                    // Start new braking zone
                    self.state = BrakingState::Active;
                    self.builder = Some(BrakingMetricsBuilder::new(
                        index,
                        frame.lap_distance,
                        frame.speed,
                        frame.brake,
                        frame.timestamp,
                    ));
                    self.current_end_idx = index;
                }
                None
            }
            BrakingState::Active => {
                if is_braking {
                    // Continue braking - update builder
                    if let Some(ref mut builder) = self.builder {
                        builder.update(frame.brake, frame.speed);
                    }
                    self.current_end_idx = index;
                    None
                } else {
                    // End of braking zone - return completed builder
                    self.state = BrakingState::Idle;
                    self.builder.take()
                }
            }
        }
    }

    fn finalize(&mut self) -> Option<Self::Builder> {
        if self.state == BrakingState::Active {
            self.state = BrakingState::Idle;
            self.builder.take()
        } else {
            None
        }
    }

    fn reset(&mut self) {
        self.state = BrakingState::Idle;
        self.builder = None;
        self.current_end_idx = 0;
    }
}

/// Extract all braking zones from telemetry frames.
///
/// This is the standalone function for extracting braking zones
/// when you don't need the unified single-pass approach.
///
/// # Arguments
/// * `frames` - Slice of telemetry frames
/// * `config` - Analysis configuration
///
/// # Returns
/// * Vector of BrakingMetrics for each detected braking zone
pub fn extract_braking_zones(
    frames: &[TelemetryFrame],
    config: &AnalysisConfig,
) -> Vec<BrakingMetrics> {
    if frames.is_empty() {
        return vec![];
    }

    let mut detector = BrakingDetector::new(config);
    let mut results = Vec::with_capacity(20); // Pre-allocate for typical lap
    let mut pending_builders: Vec<(BrakingMetricsBuilder, usize)> = Vec::new();

    for (idx, frame) in frames.iter().enumerate() {
        if let Some(builder) = detector.process_frame(frame, idx) {
            // Braking zone ended at previous frame
            pending_builders.push((builder, idx.saturating_sub(1)));
        }
    }

    // Handle any in-progress braking zone at end of lap
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

    fn make_frame(brake: f64, speed: f64, lap_distance: f64, timestamp: f64) -> TelemetryFrame {
        TelemetryFrame::new(brake, 0.0, speed, lap_distance, 0.0, 0.0, 0.0, timestamp)
    }

    fn default_config() -> AnalysisConfig {
        AnalysisConfig::default()
    }

    #[test]
    fn test_no_braking() {
        let frames = vec![
            make_frame(0.0, 50.0, 0.0, 0.0),
            make_frame(0.0, 50.0, 0.1, 1.0),
            make_frame(0.0, 50.0, 0.2, 2.0),
        ];

        let zones = extract_braking_zones(&frames, &default_config());
        assert!(zones.is_empty());
    }

    #[test]
    fn test_single_braking_zone() {
        let frames = vec![
            make_frame(0.0, 80.0, 0.40, 0.0),  // No braking
            make_frame(0.8, 75.0, 0.45, 0.5),  // Start braking
            make_frame(0.9, 60.0, 0.50, 1.0),  // Peak braking
            make_frame(0.6, 45.0, 0.55, 1.5),  // Still braking
            make_frame(0.0, 40.0, 0.60, 2.0),  // End braking
            make_frame(0.0, 45.0, 0.65, 2.5),  // Accelerating
        ];

        let zones = extract_braking_zones(&frames, &default_config());
        assert_eq!(zones.len(), 1);

        let zone = &zones[0];
        assert_eq!(zone.braking_point_distance, 0.45);
        assert_eq!(zone.braking_point_speed, 75.0);
        assert_eq!(zone.max_brake_pressure, 0.9);
        assert_eq!(zone.minimum_speed, 45.0);
        assert!((zone.braking_duration - 1.5).abs() < 1e-10); // 2.0 - 0.5
    }

    #[test]
    fn test_multiple_braking_zones() {
        let frames = vec![
            make_frame(0.0, 80.0, 0.0, 0.0),
            make_frame(0.8, 60.0, 0.1, 1.0),
            make_frame(0.0, 50.0, 0.2, 2.0), // End first
            make_frame(0.0, 70.0, 0.5, 3.0),
            make_frame(0.7, 55.0, 0.6, 4.0), // Start second
            make_frame(0.0, 45.0, 0.7, 5.0), // End second
        ];

        let zones = extract_braking_zones(&frames, &default_config());
        assert_eq!(zones.len(), 2);
    }

    #[test]
    fn test_braking_at_end_of_lap() {
        let frames = vec![
            make_frame(0.0, 80.0, 0.90, 0.0),
            make_frame(0.8, 60.0, 0.95, 1.0), // Start braking
            make_frame(0.9, 50.0, 0.99, 2.0), // Still braking at lap end
        ];

        let zones = extract_braking_zones(&frames, &default_config());
        assert_eq!(zones.len(), 1); // Should detect even without explicit end
    }

    #[test]
    fn test_empty_frames() {
        let frames: Vec<TelemetryFrame> = vec![];
        let zones = extract_braking_zones(&frames, &default_config());
        assert!(zones.is_empty());
    }
}
