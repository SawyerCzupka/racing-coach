//! Deceleration calculation functions.

use crate::types::TelemetryFrame;

/// Calculate average deceleration between two frame indices.
///
/// Returns the rate of speed change in m/s². Negative values indicate
/// deceleration (slowing down), positive values indicate acceleration.
///
/// # Arguments
/// * `frames` - Slice of telemetry frames
/// * `start_idx` - Starting frame index
/// * `end_idx` - Ending frame index
///
/// # Returns
/// * Deceleration in m/s² (negative for slowing down)
/// * Returns 0.0 if indices are invalid or time delta is zero
pub fn calculate_deceleration(frames: &[TelemetryFrame], start_idx: usize, end_idx: usize) -> f64 {
    if start_idx >= end_idx || end_idx >= frames.len() {
        return 0.0;
    }

    let start_frame = &frames[start_idx];
    let end_frame = &frames[end_idx];

    let speed_delta = end_frame.speed - start_frame.speed;
    let time_delta = end_frame.timestamp - start_frame.timestamp;

    if time_delta <= 0.0 {
        0.0
    } else {
        speed_delta / time_delta
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_frame(speed: f64, timestamp: f64) -> TelemetryFrame {
        TelemetryFrame::new(0.0, 0.0, speed, 0.0, 0.0, 0.0, 0.0, timestamp)
    }

    #[test]
    fn test_deceleration_basic() {
        let frames = vec![
            make_frame(100.0, 0.0), // 100 m/s at t=0
            make_frame(80.0, 1.0),  // 80 m/s at t=1
            make_frame(60.0, 2.0),  // 60 m/s at t=2
        ];

        let decel = calculate_deceleration(&frames, 0, 2);
        assert!((decel - (-20.0)).abs() < 1e-10); // -20 m/s² over 2 seconds
    }

    #[test]
    fn test_acceleration() {
        let frames = vec![
            make_frame(50.0, 0.0),
            make_frame(70.0, 1.0),
        ];

        let accel = calculate_deceleration(&frames, 0, 1);
        assert!((accel - 20.0).abs() < 1e-10); // +20 m/s²
    }

    #[test]
    fn test_invalid_indices() {
        let frames = vec![
            make_frame(100.0, 0.0),
            make_frame(80.0, 1.0),
        ];

        // start >= end
        assert_eq!(calculate_deceleration(&frames, 1, 1), 0.0);
        assert_eq!(calculate_deceleration(&frames, 1, 0), 0.0);

        // end out of bounds
        assert_eq!(calculate_deceleration(&frames, 0, 10), 0.0);
    }

    #[test]
    fn test_zero_time_delta() {
        let frames = vec![
            make_frame(100.0, 0.0),
            make_frame(80.0, 0.0), // Same timestamp
        ];

        assert_eq!(calculate_deceleration(&frames, 0, 1), 0.0);
    }
}
