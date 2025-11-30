//! Corner metrics result structure.

use pyo3::prelude::*;

/// Comprehensive corner metrics for a single corner.
///
/// Contains key points, speeds, and performance data.
#[derive(Debug, Clone)]
#[pyclass]
pub struct CornerMetrics {
    // Key corner points (lap distances)
    /// Lap distance where steering input begins (turn-in point)
    #[pyo3(get)]
    pub turn_in_distance: f64,

    /// Lap distance at corner apex (point of max lateral G)
    #[pyo3(get)]
    pub apex_distance: f64,

    /// Lap distance where steering unwinds (exit point)
    #[pyo3(get)]
    pub exit_distance: f64,

    /// Lap distance where throttle is first applied in corner
    #[pyo3(get)]
    pub throttle_application_distance: f64,

    // Speeds at key points (m/s)
    /// Speed at turn-in point
    #[pyo3(get)]
    pub turn_in_speed: f64,

    /// Speed at apex (typically minimum corner speed)
    #[pyo3(get)]
    pub apex_speed: f64,

    /// Speed at exit point
    #[pyo3(get)]
    pub exit_speed: f64,

    /// Speed when throttle is first applied
    #[pyo3(get)]
    pub throttle_application_speed: f64,

    // Performance metrics
    /// Maximum lateral acceleration (m/s², positive = cornering force)
    #[pyo3(get)]
    pub max_lateral_g: f64,

    /// Time spent in corner (seconds)
    #[pyo3(get)]
    pub time_in_corner: f64,

    /// Track distance from turn-in to exit
    #[pyo3(get)]
    pub corner_distance: f64,

    /// Maximum steering angle used (radians)
    #[pyo3(get)]
    pub max_steering_angle: f64,

    // Speed deltas
    /// Speed lost from turn-in to apex (positive = speed lost)
    #[pyo3(get)]
    pub speed_loss: f64,

    /// Speed gained from apex to exit (positive = speed gained)
    #[pyo3(get)]
    pub speed_gain: f64,
}

#[pymethods]
impl CornerMetrics {
    /// Create a new CornerMetrics instance.
    #[new]
    #[pyo3(signature = (
        turn_in_distance,
        apex_distance,
        exit_distance,
        throttle_application_distance,
        turn_in_speed,
        apex_speed,
        exit_speed,
        throttle_application_speed,
        max_lateral_g,
        time_in_corner,
        corner_distance,
        max_steering_angle,
        speed_loss,
        speed_gain
    ))]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        turn_in_distance: f64,
        apex_distance: f64,
        exit_distance: f64,
        throttle_application_distance: f64,
        turn_in_speed: f64,
        apex_speed: f64,
        exit_speed: f64,
        throttle_application_speed: f64,
        max_lateral_g: f64,
        time_in_corner: f64,
        corner_distance: f64,
        max_steering_angle: f64,
        speed_loss: f64,
        speed_gain: f64,
    ) -> Self {
        Self {
            turn_in_distance,
            apex_distance,
            exit_distance,
            throttle_application_distance,
            turn_in_speed,
            apex_speed,
            exit_speed,
            throttle_application_speed,
            max_lateral_g,
            time_in_corner,
            corner_distance,
            max_steering_angle,
            speed_loss,
            speed_gain,
        }
    }

    /// String representation for debugging.
    fn __repr__(&self) -> String {
        format!(
            "CornerMetrics(turn_in={:.3}, apex={:.3}, exit={:.3}, apex_speed={:.1})",
            self.turn_in_distance, self.apex_distance, self.exit_distance, self.apex_speed
        )
    }
}

/// Builder for accumulating corner metrics during detection.
#[derive(Debug)]
pub struct CornerMetricsBuilder {
    pub turn_in_idx: usize,
    pub turn_in_distance: f64,
    pub turn_in_speed: f64,
    pub turn_in_timestamp: f64,

    pub apex_idx: usize,
    pub apex_distance: f64,
    pub max_lateral_g: f64,

    pub min_speed: f64,
    pub min_speed_idx: usize,

    pub max_steering: f64,

    pub throttle_applied: bool,
    pub throttle_idx: usize,
    pub throttle_distance: f64,
    pub throttle_speed: f64,
}

impl CornerMetricsBuilder {
    /// Create a new builder from the turn-in frame.
    pub fn new(
        idx: usize,
        distance: f64,
        speed: f64,
        timestamp: f64,
        lateral_g: f64,
        steering: f64,
    ) -> Self {
        Self {
            turn_in_idx: idx,
            turn_in_distance: distance,
            turn_in_speed: speed,
            turn_in_timestamp: timestamp,
            apex_idx: idx,
            apex_distance: distance,
            max_lateral_g: lateral_g.abs(),
            min_speed: speed,
            min_speed_idx: idx,
            max_steering: steering.abs(),
            throttle_applied: false,
            throttle_idx: idx,
            throttle_distance: distance,
            throttle_speed: speed,
        }
    }

    /// Update builder with a new frame during corner.
    pub fn update(
        &mut self,
        idx: usize,
        distance: f64,
        speed: f64,
        lateral_g: f64,
        steering: f64,
        throttle: f64,
        throttle_threshold: f64,
    ) {
        let abs_lateral_g = lateral_g.abs();
        let abs_steering = steering.abs();

        // Track apex (max lateral G)
        if abs_lateral_g > self.max_lateral_g {
            self.max_lateral_g = abs_lateral_g;
            self.apex_idx = idx;
            self.apex_distance = distance;
        }

        // Track minimum speed
        if speed < self.min_speed {
            self.min_speed = speed;
            self.min_speed_idx = idx;
        }

        // Track max steering
        if abs_steering > self.max_steering {
            self.max_steering = abs_steering;
        }

        // Track first throttle application
        if !self.throttle_applied && throttle > throttle_threshold {
            self.throttle_applied = true;
            self.throttle_idx = idx;
            self.throttle_distance = distance;
            self.throttle_speed = speed;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_corner_metrics_creation() {
        let metrics = CornerMetrics::new(
            0.3, 0.35, 0.4, 0.37, 60.0, 45.0, 70.0, 50.0, 2.5, 3.0, 0.1, 0.3, 15.0, 25.0,
        );
        assert_eq!(metrics.turn_in_distance, 0.3);
        assert_eq!(metrics.apex_speed, 45.0);
        assert_eq!(metrics.max_lateral_g, 2.5);
    }

    #[test]
    fn test_builder_apex_tracking() {
        let mut builder = CornerMetricsBuilder::new(10, 0.3, 60.0, 100.0, 1.0, 0.2);

        // Update with higher lateral G
        builder.update(12, 0.32, 50.0, 2.5, 0.25, 0.0, 0.05);
        assert_eq!(builder.apex_idx, 12);
        assert_eq!(builder.max_lateral_g, 2.5);

        // Update with lower lateral G (apex shouldn't change)
        builder.update(14, 0.34, 55.0, 1.5, 0.15, 0.0, 0.05);
        assert_eq!(builder.apex_idx, 12);
    }

    #[test]
    fn test_builder_throttle_tracking() {
        let mut builder = CornerMetricsBuilder::new(10, 0.3, 60.0, 100.0, 1.0, 0.2);

        // No throttle yet
        builder.update(12, 0.32, 50.0, 2.0, 0.25, 0.0, 0.05);
        assert!(!builder.throttle_applied);

        // Throttle applied
        builder.update(14, 0.34, 55.0, 1.5, 0.15, 0.1, 0.05);
        assert!(builder.throttle_applied);
        assert_eq!(builder.throttle_idx, 14);

        // Later throttle shouldn't override
        builder.update(16, 0.36, 60.0, 1.0, 0.1, 0.3, 0.05);
        assert_eq!(builder.throttle_idx, 14);
    }
}
