//! Trail braking detection and analysis.

use crate::types::{AnalysisConfig, TelemetryFrame};
use crate::utils::wrap_distance;

/// Information about trail braking within a braking zone.
#[derive(Debug, Clone, Copy)]
pub struct TrailBrakingInfo {
    /// Whether any trail braking was detected
    pub has_trail_braking: bool,
    /// Track distance where both braking and steering occurred
    pub distance: f64,
    /// Average brake pressure during trail braking phase
    pub percentage: f64,
}

impl Default for TrailBrakingInfo {
    fn default() -> Self {
        Self {
            has_trail_braking: false,
            distance: 0.0,
            percentage: 0.0,
        }
    }
}

/// Detect trail braking within a braking zone.
///
/// Trail braking is the technique of maintaining brake pressure while
/// beginning to turn into a corner. This function analyzes a braking zone
/// to detect if and how much trail braking occurred.
///
/// # Arguments
/// * `frames` - Slice of telemetry frames
/// * `brake_start_idx` - Start index of the braking zone
/// * `brake_end_idx` - End index of the braking zone
/// * `config` - Analysis configuration with thresholds
///
/// # Returns
/// * `TrailBrakingInfo` containing detection results
pub fn detect_trail_braking(
    frames: &[TelemetryFrame],
    brake_start_idx: usize,
    brake_end_idx: usize,
    config: &AnalysisConfig,
) -> TrailBrakingInfo {
    if frames.is_empty() || brake_start_idx >= frames.len() {
        return TrailBrakingInfo::default();
    }

    let end_idx = brake_end_idx.min(frames.len() - 1);
    if brake_start_idx > end_idx {
        return TrailBrakingInfo::default();
    }

    let mut trail_distance = 0.0;
    let mut pressure_sum = 0.0;
    let mut trail_frames = 0usize;

    for i in brake_start_idx..=end_idx {
        let frame = &frames[i];

        // Check if both braking AND steering are active
        let is_braking = frame.brake > config.brake_threshold;
        let is_steering = frame.steering_angle.abs() > config.steering_threshold;

        if is_braking && is_steering {
            trail_frames += 1;
            pressure_sum += frame.brake;

            // Calculate distance delta to next frame
            if i + 1 < frames.len() {
                let distance_delta = frames[i + 1].lap_distance - frame.lap_distance;
                trail_distance += wrap_distance(distance_delta);
            }
        }
    }

    TrailBrakingInfo {
        has_trail_braking: trail_frames > 0,
        distance: trail_distance,
        percentage: if trail_frames > 0 {
            pressure_sum / trail_frames as f64
        } else {
            0.0
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_frame(brake: f64, steering: f64, lap_distance: f64) -> TelemetryFrame {
        TelemetryFrame::new(brake, 0.0, 50.0, lap_distance, steering, 0.0, 0.0, 0.0)
    }

    fn default_config() -> AnalysisConfig {
        AnalysisConfig::default()
    }

    #[test]
    fn test_no_trail_braking() {
        let frames = vec![
            make_frame(0.8, 0.0, 0.50), // Braking, no steering
            make_frame(0.6, 0.0, 0.51),
            make_frame(0.4, 0.0, 0.52),
        ];

        let info = detect_trail_braking(&frames, 0, 2, &default_config());
        assert!(!info.has_trail_braking);
        assert_eq!(info.distance, 0.0);
    }

    #[test]
    fn test_trail_braking_detected() {
        let frames = vec![
            make_frame(0.8, 0.0, 0.50),  // Braking only
            make_frame(0.6, 0.2, 0.51),  // Trail braking!
            make_frame(0.4, 0.25, 0.52), // Trail braking!
            make_frame(0.0, 0.3, 0.53),  // Steering only
        ];

        let info = detect_trail_braking(&frames, 0, 3, &default_config());
        assert!(info.has_trail_braking);
        assert!((info.distance - 0.02).abs() < 1e-10); // 0.52-0.51 + 0.53-0.52
        assert!((info.percentage - 0.5).abs() < 1e-10); // (0.6 + 0.4) / 2
    }

    #[test]
    fn test_trail_braking_lap_wraparound() {
        let frames = vec![
            make_frame(0.8, 0.2, 0.99), // Trail braking near S/F
            make_frame(0.6, 0.2, 0.01), // After crossing S/F
        ];

        let info = detect_trail_braking(&frames, 0, 1, &default_config());
        assert!(info.has_trail_braking);
        assert!((info.distance - 0.02).abs() < 1e-10); // Wrapped correctly
    }

    #[test]
    fn test_empty_frames() {
        let frames: Vec<TelemetryFrame> = vec![];
        let info = detect_trail_braking(&frames, 0, 0, &default_config());
        assert!(!info.has_trail_braking);
    }

    #[test]
    fn test_invalid_indices() {
        let frames = vec![make_frame(0.8, 0.2, 0.50)];

        // start > end
        let info = detect_trail_braking(&frames, 5, 2, &default_config());
        assert!(!info.has_trail_braking);

        // start out of bounds
        let info = detect_trail_braking(&frames, 10, 15, &default_config());
        assert!(!info.has_trail_braking);
    }
}
