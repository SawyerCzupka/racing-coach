//! Unified single-pass metrics extraction.

use crate::analysis::SpeedStatistics;
use crate::detection::{BrakingDetector, CornerDetector, EventDetector};
use crate::results::{BrakingMetrics, BrakingMetricsBuilder, CornerMetrics, CornerMetricsBuilder, LapMetrics};
use crate::types::{AnalysisConfig, TelemetryFrame};

/// Extract comprehensive lap metrics in a single pass through the telemetry data.
///
/// This function combines braking zone and corner detection into a single
/// iteration over the frame data, maximizing cache efficiency and minimizing
/// total iterations. Both detection algorithms run in parallel on each frame.
///
/// # Arguments
/// * `frames` - Slice of telemetry frames for the lap
/// * `config` - Analysis configuration with detection thresholds
/// * `lap_number` - The lap number
/// * `lap_time` - Optional lap time in seconds
///
/// # Returns
/// * `LapMetrics` containing all detected braking zones, corners, and statistics
///
/// # Performance
/// This function is O(n) where n is the number of frames, with minimal memory
/// allocations during iteration due to pre-allocated result vectors.
pub fn extract_lap_metrics(
    frames: &[TelemetryFrame],
    config: &AnalysisConfig,
    lap_number: i32,
    lap_time: Option<f64>,
) -> LapMetrics {
    if frames.is_empty() {
        return LapMetrics::from_detection(lap_number, lap_time, vec![], vec![], 0.0, 0.0);
    }

    // Initialize detectors
    let mut braking_detector = BrakingDetector::new(config);
    let mut corner_detector = CornerDetector::new(config);

    // Track lap-wide statistics
    let mut speed_stats = SpeedStatistics::new();

    // Collect builders that need finalization
    let mut pending_braking: Vec<(BrakingMetricsBuilder, usize)> = Vec::with_capacity(20);
    let mut pending_corners: Vec<(CornerMetricsBuilder, usize)> = Vec::with_capacity(25);

    // Single pass through all frames
    for (idx, frame) in frames.iter().enumerate() {
        // Update lap-wide statistics
        speed_stats.update(frame.speed);

        // Process braking detection
        if let Some(builder) = braking_detector.process_frame(frame, idx) {
            // Braking zone ended - the end index is the previous frame
            pending_braking.push((builder, idx.saturating_sub(1)));
        }

        // Process corner detection
        if let Some(builder) = corner_detector.process_frame(frame, idx) {
            // Corner ended - the end index is the previous frame
            pending_corners.push((builder, idx.saturating_sub(1)));
        }
    }

    // Finalize any in-progress events at end of lap
    if let Some(builder) = braking_detector.finalize() {
        pending_braking.push((builder, frames.len() - 1));
    }
    if let Some(builder) = corner_detector.finalize() {
        pending_corners.push((builder, frames.len() - 1));
    }

    // Convert builders to final metrics
    let braking_zones: Vec<BrakingMetrics> = pending_braking
        .into_iter()
        .map(|(builder, end_idx)| braking_detector.finalize_builder(builder, frames, end_idx))
        .collect();

    let corners: Vec<CornerMetrics> = pending_corners
        .into_iter()
        .map(|(builder, end_idx)| corner_detector.finalize_builder(builder, frames, end_idx))
        .collect();

    LapMetrics::from_detection(
        lap_number,
        lap_time,
        braking_zones,
        corners,
        speed_stats.max(),
        speed_stats.min(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_frame(
        brake: f64,
        throttle: f64,
        speed: f64,
        lap_distance: f64,
        steering: f64,
        lateral_g: f64,
        timestamp: f64,
    ) -> TelemetryFrame {
        TelemetryFrame::new(
            brake,
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
    fn test_empty_frames() {
        let frames: Vec<TelemetryFrame> = vec![];
        let metrics = extract_lap_metrics(&frames, &default_config(), 1, Some(90.0));

        assert_eq!(metrics.lap_number, 1);
        assert_eq!(metrics.lap_time, Some(90.0));
        assert!(metrics.braking_zones.is_empty());
        assert!(metrics.corners.is_empty());
        assert_eq!(metrics.max_speed, 0.0);
        assert_eq!(metrics.min_speed, 0.0);
    }

    #[test]
    fn test_speed_statistics() {
        let frames = vec![
            make_frame(0.0, 0.5, 50.0, 0.0, 0.0, 0.0, 0.0),
            make_frame(0.0, 0.5, 100.0, 0.1, 0.0, 0.0, 1.0),
            make_frame(0.0, 0.5, 30.0, 0.2, 0.0, 0.0, 2.0),
            make_frame(0.0, 0.5, 80.0, 0.3, 0.0, 0.0, 3.0),
        ];

        let metrics = extract_lap_metrics(&frames, &default_config(), 1, None);

        assert_eq!(metrics.max_speed, 100.0);
        assert_eq!(metrics.min_speed, 30.0);
    }

    #[test]
    fn test_combined_braking_and_corner() {
        // Simulate a corner with braking zone
        let frames = vec![
            // Straight
            make_frame(0.0, 0.8, 80.0, 0.30, 0.0, 0.0, 0.0),
            // Braking into corner
            make_frame(0.9, 0.0, 70.0, 0.35, 0.0, 0.0, 0.5),
            make_frame(0.7, 0.0, 55.0, 0.40, 0.1, 1.0, 1.0),
            // Turn in with trail braking
            make_frame(0.4, 0.0, 45.0, 0.45, 0.25, 2.0, 1.5),
            // Apex
            make_frame(0.0, 0.0, 40.0, 0.50, 0.3, 2.5, 2.0),
            // Exit with throttle
            make_frame(0.0, 0.3, 50.0, 0.55, 0.2, 1.5, 2.5),
            make_frame(0.0, 0.6, 65.0, 0.60, 0.0, 0.5, 3.0),
        ];

        let metrics = extract_lap_metrics(&frames, &default_config(), 5, Some(85.5));

        assert_eq!(metrics.lap_number, 5);
        assert_eq!(metrics.lap_time, Some(85.5));
        assert_eq!(metrics.total_braking_zones, 1);
        assert_eq!(metrics.total_corners, 1);

        // Verify braking zone metrics
        let brake_zone = &metrics.braking_zones[0];
        assert!(brake_zone.max_brake_pressure >= 0.7);
        assert!(brake_zone.has_trail_braking); // Was braking while steering

        // Verify corner metrics
        let corner = &metrics.corners[0];
        assert!(corner.max_lateral_g >= 2.0);
        assert!(corner.apex_speed <= 50.0);
    }

    #[test]
    fn test_multiple_events() {
        let frames = vec![
            // First braking zone
            make_frame(0.0, 0.5, 80.0, 0.00, 0.0, 0.0, 0.0),
            make_frame(0.8, 0.0, 60.0, 0.05, 0.0, 0.0, 0.5),
            make_frame(0.0, 0.3, 55.0, 0.10, 0.0, 0.0, 1.0),
            // First corner
            make_frame(0.0, 0.5, 60.0, 0.15, 0.3, 2.0, 1.5),
            make_frame(0.0, 0.5, 65.0, 0.20, 0.0, 0.5, 2.0),
            // Second braking zone
            make_frame(0.0, 0.5, 90.0, 0.40, 0.0, 0.0, 3.0),
            make_frame(0.7, 0.0, 70.0, 0.45, 0.0, 0.0, 3.5),
            make_frame(0.0, 0.3, 60.0, 0.50, 0.0, 0.0, 4.0),
            // Second corner
            make_frame(0.0, 0.5, 65.0, 0.55, -0.25, 1.8, 4.5),
            make_frame(0.0, 0.5, 70.0, 0.60, 0.0, 0.3, 5.0),
        ];

        let metrics = extract_lap_metrics(&frames, &default_config(), 1, None);

        assert_eq!(metrics.total_braking_zones, 2);
        assert_eq!(metrics.total_corners, 2);
        assert_eq!(metrics.max_speed, 90.0);
        assert_eq!(metrics.min_speed, 55.0);
    }

    #[test]
    fn test_average_corner_speed() {
        let frames = vec![
            // Corner 1 with apex speed 45
            make_frame(0.0, 0.5, 60.0, 0.10, 0.3, 2.0, 0.0),
            make_frame(0.0, 0.5, 45.0, 0.15, 0.3, 2.5, 0.5),
            make_frame(0.0, 0.5, 55.0, 0.20, 0.0, 0.5, 1.0),
            // Corner 2 with apex speed 55
            make_frame(0.0, 0.5, 70.0, 0.50, 0.3, 2.0, 2.0),
            make_frame(0.0, 0.5, 55.0, 0.55, 0.3, 2.5, 2.5),
            make_frame(0.0, 0.5, 65.0, 0.60, 0.0, 0.5, 3.0),
        ];

        let metrics = extract_lap_metrics(&frames, &default_config(), 1, None);

        assert_eq!(metrics.total_corners, 2);
        assert_eq!(metrics.average_corner_speed, 50.0); // (45 + 55) / 2
    }
}
