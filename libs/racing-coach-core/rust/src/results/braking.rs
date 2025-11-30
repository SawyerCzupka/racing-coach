//! Braking metrics result structure.

use pyo3::prelude::*;

/// Comprehensive braking metrics for a single braking zone.
///
/// Contains location, performance, deceleration, and trail braking data.
#[derive(Debug, Clone)]
#[pyclass]
pub struct BrakingMetrics {
    // Location metrics
    /// Lap distance where braking starts (normalized 0-1)
    #[pyo3(get)]
    pub braking_point_distance: f64,

    /// Speed when braking starts (m/s)
    #[pyo3(get)]
    pub braking_point_speed: f64,

    /// Lap distance where braking ends (normalized 0-1)
    #[pyo3(get)]
    pub end_distance: f64,

    // Performance metrics
    /// Maximum brake pressure applied (0-1)
    #[pyo3(get)]
    pub max_brake_pressure: f64,

    /// Duration of braking in seconds
    #[pyo3(get)]
    pub braking_duration: f64,

    /// Minimum speed reached during braking (m/s)
    #[pyo3(get)]
    pub minimum_speed: f64,

    // Deceleration metrics
    /// Initial deceleration rate over first N frames (m/s²), negative for decel
    #[pyo3(get)]
    pub initial_deceleration: f64,

    /// Average deceleration during entire braking zone (m/s²), negative for decel
    #[pyo3(get)]
    pub average_deceleration: f64,

    /// Braking efficiency: |deceleration| / brake_pressure
    #[pyo3(get)]
    pub braking_efficiency: f64,

    // Trail braking metrics
    /// Whether trail braking was detected (braking while steering)
    #[pyo3(get)]
    pub has_trail_braking: bool,

    /// Track distance of trail braking overlap
    #[pyo3(get)]
    pub trail_brake_distance: f64,

    /// Average brake pressure during trail braking phase
    #[pyo3(get)]
    pub trail_brake_percentage: f64,
}

#[pymethods]
impl BrakingMetrics {
    /// Create a new BrakingMetrics instance.
    #[new]
    #[pyo3(signature = (
        braking_point_distance,
        braking_point_speed,
        end_distance,
        max_brake_pressure,
        braking_duration,
        minimum_speed,
        initial_deceleration,
        average_deceleration,
        braking_efficiency,
        has_trail_braking,
        trail_brake_distance,
        trail_brake_percentage
    ))]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        braking_point_distance: f64,
        braking_point_speed: f64,
        end_distance: f64,
        max_brake_pressure: f64,
        braking_duration: f64,
        minimum_speed: f64,
        initial_deceleration: f64,
        average_deceleration: f64,
        braking_efficiency: f64,
        has_trail_braking: bool,
        trail_brake_distance: f64,
        trail_brake_percentage: f64,
    ) -> Self {
        Self {
            braking_point_distance,
            braking_point_speed,
            end_distance,
            max_brake_pressure,
            braking_duration,
            minimum_speed,
            initial_deceleration,
            average_deceleration,
            braking_efficiency,
            has_trail_braking,
            trail_brake_distance,
            trail_brake_percentage,
        }
    }

    /// String representation for debugging.
    fn __repr__(&self) -> String {
        format!(
            "BrakingMetrics(dist={:.3}->{:.3}, speed={:.1}->{:.1}, max_brake={:.2})",
            self.braking_point_distance,
            self.end_distance,
            self.braking_point_speed,
            self.minimum_speed,
            self.max_brake_pressure
        )
    }
}

/// Builder for accumulating braking metrics during detection.
#[derive(Debug)]
pub struct BrakingMetricsBuilder {
    pub start_idx: usize,
    pub start_distance: f64,
    pub start_speed: f64,
    pub start_timestamp: f64,
    pub max_pressure: f64,
    pub min_speed: f64,
}

impl BrakingMetricsBuilder {
    /// Create a new builder from the starting frame.
    pub fn new(idx: usize, distance: f64, speed: f64, brake: f64, timestamp: f64) -> Self {
        Self {
            start_idx: idx,
            start_distance: distance,
            start_speed: speed,
            start_timestamp: timestamp,
            max_pressure: brake,
            min_speed: speed,
        }
    }

    /// Update builder with a new frame during braking.
    pub fn update(&mut self, brake: f64, speed: f64) {
        self.max_pressure = self.max_pressure.max(brake);
        self.min_speed = self.min_speed.min(speed);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_braking_metrics_creation() {
        let metrics = BrakingMetrics::new(
            0.5, 80.0, 0.55, 0.9, 2.5, 40.0, -15.0, -12.0, 13.3, true, 0.02, 0.6,
        );
        assert_eq!(metrics.braking_point_distance, 0.5);
        assert_eq!(metrics.max_brake_pressure, 0.9);
        assert!(metrics.has_trail_braking);
    }

    #[test]
    fn test_builder() {
        let mut builder = BrakingMetricsBuilder::new(10, 0.5, 80.0, 0.3, 100.0);
        builder.update(0.9, 70.0);
        builder.update(0.8, 50.0);

        assert_eq!(builder.max_pressure, 0.9);
        assert_eq!(builder.min_speed, 50.0);
    }
}
