//! Analysis configuration and thresholds.

use pyo3::prelude::*;

/// Configuration for telemetry analysis thresholds.
///
/// All thresholds have sensible defaults that work well for most racing scenarios.
#[derive(Debug, Clone, Copy)]
#[pyclass]
pub struct AnalysisConfig {
    /// Minimum brake pressure to consider as braking (default: 0.05 = 5%)
    #[pyo3(get, set)]
    pub brake_threshold: f64,

    /// Minimum steering angle to consider as turning (default: 0.15 radians ≈ 8.6°)
    #[pyo3(get, set)]
    pub steering_threshold: f64,

    /// Minimum throttle position to consider as accelerating (default: 0.05 = 5%)
    #[pyo3(get, set)]
    pub throttle_threshold: f64,

    /// Number of frames to use for initial deceleration calculation (default: 5)
    #[pyo3(get, set)]
    pub decel_window: usize,
}

impl Default for AnalysisConfig {
    fn default() -> Self {
        Self {
            brake_threshold: 0.05,
            steering_threshold: 0.15,
            throttle_threshold: 0.05,
            decel_window: 5,
        }
    }
}

#[pymethods]
impl AnalysisConfig {
    /// Create a new AnalysisConfig with custom thresholds.
    #[new]
    #[pyo3(signature = (brake_threshold=0.05, steering_threshold=0.15, throttle_threshold=0.05, decel_window=5))]
    pub fn new(
        brake_threshold: f64,
        steering_threshold: f64,
        throttle_threshold: f64,
        decel_window: usize,
    ) -> Self {
        Self {
            brake_threshold,
            steering_threshold,
            throttle_threshold,
            decel_window,
        }
    }

    /// Create a config with default values.
    #[staticmethod]
    pub fn defaults() -> Self {
        Self::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = AnalysisConfig::default();
        assert_eq!(config.brake_threshold, 0.05);
        assert_eq!(config.steering_threshold, 0.15);
        assert_eq!(config.throttle_threshold, 0.05);
        assert_eq!(config.decel_window, 5);
    }

    #[test]
    fn test_custom_config() {
        let config = AnalysisConfig::new(0.1, 0.2, 0.1, 10);
        assert_eq!(config.brake_threshold, 0.1);
        assert_eq!(config.steering_threshold, 0.2);
        assert_eq!(config.throttle_threshold, 0.1);
        assert_eq!(config.decel_window, 10);
    }
}
