//! Lap metrics aggregate structure.

use pyo3::prelude::*;

use super::{BrakingMetrics, CornerMetrics};

/// Aggregate metrics for an entire lap.
///
/// Contains collections of braking zones and corners along with lap-wide statistics.
#[derive(Debug, Clone)]
#[pyclass]
pub struct LapMetrics {
    /// Lap number
    #[pyo3(get)]
    pub lap_number: i32,

    /// Lap time in seconds (None if not available)
    #[pyo3(get)]
    pub lap_time: Option<f64>,

    /// All braking zones detected in the lap
    #[pyo3(get)]
    pub braking_zones: Vec<BrakingMetrics>,

    /// All corners detected in the lap
    #[pyo3(get)]
    pub corners: Vec<CornerMetrics>,

    /// Total number of corners
    #[pyo3(get)]
    pub total_corners: usize,

    /// Total number of braking zones
    #[pyo3(get)]
    pub total_braking_zones: usize,

    /// Average speed at corner apexes (m/s)
    #[pyo3(get)]
    pub average_corner_speed: f64,

    /// Maximum speed during the lap (m/s)
    #[pyo3(get)]
    pub max_speed: f64,

    /// Minimum speed during the lap (m/s)
    #[pyo3(get)]
    pub min_speed: f64,
}

#[pymethods]
impl LapMetrics {
    /// Create a new LapMetrics instance.
    #[new]
    #[pyo3(signature = (
        lap_number,
        lap_time,
        braking_zones,
        corners,
        total_corners,
        total_braking_zones,
        average_corner_speed,
        max_speed,
        min_speed
    ))]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        lap_number: i32,
        lap_time: Option<f64>,
        braking_zones: Vec<BrakingMetrics>,
        corners: Vec<CornerMetrics>,
        total_corners: usize,
        total_braking_zones: usize,
        average_corner_speed: f64,
        max_speed: f64,
        min_speed: f64,
    ) -> Self {
        Self {
            lap_number,
            lap_time,
            braking_zones,
            corners,
            total_corners,
            total_braking_zones,
            average_corner_speed,
            max_speed,
            min_speed,
        }
    }

    /// String representation for debugging.
    fn __repr__(&self) -> String {
        format!(
            "LapMetrics(lap={}, time={:?}, braking_zones={}, corners={})",
            self.lap_number, self.lap_time, self.total_braking_zones, self.total_corners
        )
    }
}

impl LapMetrics {
    /// Create LapMetrics from detected zones and corners.
    pub fn from_detection(
        lap_number: i32,
        lap_time: Option<f64>,
        braking_zones: Vec<BrakingMetrics>,
        corners: Vec<CornerMetrics>,
        max_speed: f64,
        min_speed: f64,
    ) -> Self {
        let total_braking_zones = braking_zones.len();
        let total_corners = corners.len();

        let average_corner_speed = if corners.is_empty() {
            0.0
        } else {
            corners.iter().map(|c| c.apex_speed).sum::<f64>() / corners.len() as f64
        };

        Self {
            lap_number,
            lap_time,
            braking_zones,
            corners,
            total_corners,
            total_braking_zones,
            average_corner_speed,
            max_speed,
            min_speed,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_braking_metrics() -> BrakingMetrics {
        BrakingMetrics::new(
            0.5, 80.0, 0.55, 0.9, 2.5, 40.0, -15.0, -12.0, 13.3, false, 0.0, 0.0,
        )
    }

    fn make_corner_metrics(apex_speed: f64) -> CornerMetrics {
        CornerMetrics::new(
            0.3,
            0.35,
            0.4,
            0.37,
            60.0,
            apex_speed,
            70.0,
            50.0,
            2.5,
            3.0,
            0.1,
            0.3,
            15.0,
            25.0,
        )
    }

    #[test]
    fn test_lap_metrics_from_detection() {
        let braking_zones = vec![make_braking_metrics()];
        let corners = vec![make_corner_metrics(45.0), make_corner_metrics(55.0)];

        let metrics = LapMetrics::from_detection(1, Some(90.5), braking_zones, corners, 100.0, 30.0);

        assert_eq!(metrics.lap_number, 1);
        assert_eq!(metrics.lap_time, Some(90.5));
        assert_eq!(metrics.total_braking_zones, 1);
        assert_eq!(metrics.total_corners, 2);
        assert_eq!(metrics.average_corner_speed, 50.0); // (45 + 55) / 2
        assert_eq!(metrics.max_speed, 100.0);
        assert_eq!(metrics.min_speed, 30.0);
    }

    #[test]
    fn test_empty_corners_average() {
        let metrics = LapMetrics::from_detection(1, None, vec![], vec![], 100.0, 30.0);
        assert_eq!(metrics.average_corner_speed, 0.0);
    }
}
