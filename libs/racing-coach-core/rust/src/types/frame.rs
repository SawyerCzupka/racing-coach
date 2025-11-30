//! Telemetry frame input structure.

use pyo3::prelude::*;

/// A single telemetry frame containing all data needed for analysis.
///
/// This struct uses `Copy` for efficient passing through the analysis pipeline.
/// Fields are ordered by access frequency for cache efficiency.
#[derive(Debug, Clone, Copy)]
#[pyclass]
pub struct TelemetryFrame {
    // Hot path: accessed every frame during detection
    #[pyo3(get)]
    pub brake: f64,
    #[pyo3(get)]
    pub steering_angle: f64,
    #[pyo3(get)]
    pub throttle: f64,
    #[pyo3(get)]
    pub speed: f64,

    // Warm path: accessed for event metrics
    #[pyo3(get)]
    pub lap_distance: f64,
    #[pyo3(get)]
    pub timestamp: f64,

    // Cold path: accessed only for specific calculations
    #[pyo3(get)]
    pub lateral_acceleration: f64,
    #[pyo3(get)]
    pub longitudinal_acceleration: f64,
}

#[pymethods]
impl TelemetryFrame {
    /// Create a new TelemetryFrame.
    ///
    /// # Arguments
    /// * `brake` - Brake pressure (0.0-1.0)
    /// * `throttle` - Throttle position (0.0-1.0)
    /// * `speed` - Vehicle speed in m/s
    /// * `lap_distance` - Normalized lap distance (0.0-1.0)
    /// * `steering_angle` - Steering angle in radians
    /// * `lateral_acceleration` - Lateral acceleration in m/s²
    /// * `longitudinal_acceleration` - Longitudinal acceleration in m/s²
    /// * `timestamp` - Timestamp in seconds
    #[new]
    #[pyo3(signature = (brake, throttle, speed, lap_distance, steering_angle, lateral_acceleration, longitudinal_acceleration, timestamp))]
    pub fn new(
        brake: f64,
        throttle: f64,
        speed: f64,
        lap_distance: f64,
        steering_angle: f64,
        lateral_acceleration: f64,
        longitudinal_acceleration: f64,
        timestamp: f64,
    ) -> Self {
        Self {
            brake,
            throttle,
            speed,
            lap_distance,
            steering_angle,
            lateral_acceleration,
            longitudinal_acceleration,
            timestamp,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_telemetry_frame_creation() {
        let frame = TelemetryFrame::new(0.5, 0.0, 50.0, 0.25, 0.1, 5.0, -8.0, 100.0);
        assert_eq!(frame.brake, 0.5);
        assert_eq!(frame.throttle, 0.0);
        assert_eq!(frame.speed, 50.0);
        assert_eq!(frame.lap_distance, 0.25);
        assert_eq!(frame.steering_angle, 0.1);
        assert_eq!(frame.lateral_acceleration, 5.0);
        assert_eq!(frame.longitudinal_acceleration, -8.0);
        assert_eq!(frame.timestamp, 100.0);
    }

    #[test]
    fn test_telemetry_frame_is_copy() {
        let frame = TelemetryFrame::new(0.5, 0.0, 50.0, 0.25, 0.1, 5.0, -8.0, 100.0);
        let frame_copy = frame; // Copy, not move
        assert_eq!(frame.brake, frame_copy.brake); // Original still accessible
    }
}
