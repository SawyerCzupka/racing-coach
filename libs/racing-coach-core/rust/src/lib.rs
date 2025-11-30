//! Racing Coach Core - Rust telemetry analysis library.
//!
//! This crate provides high-performance algorithms for analyzing racing telemetry data.
//! It is designed to be used from Python via PyO3 bindings.
//!
//! # Modules
//!
//! - [`types`] - Input types (TelemetryFrame, AnalysisConfig)
//! - [`results`] - Output types (BrakingMetrics, CornerMetrics, LapMetrics)
//! - [`detection`] - Event detection (braking zones, corners)
//! - [`analysis`] - Analysis functions (deceleration, trail braking)
//! - [`pipeline`] - Unified metrics extraction
//! - [`utils`] - Utility functions

use pyo3::prelude::*;

pub mod analysis;
pub mod detection;
pub mod pipeline;
pub mod results;
pub mod types;
pub mod utils;

// Re-export commonly used items
pub use detection::{extract_braking_zones, extract_corners};
pub use pipeline::extract_lap_metrics;
pub use results::{BrakingMetrics, CornerMetrics, LapMetrics};
pub use types::{AnalysisConfig, TelemetryFrame};

// ============================================================================
// Python-facing wrapper functions
// ============================================================================

/// Extract comprehensive lap metrics from telemetry frames.
///
/// This is the main entry point for lap analysis. It performs a single-pass
/// analysis detecting all braking zones and corners.
///
/// # Arguments
/// * `frames` - List of TelemetryFrame objects
/// * `lap_number` - The lap number (default: 0)
/// * `lap_time` - Optional lap time in seconds
/// * `config` - Optional AnalysisConfig (uses defaults if not provided)
///
/// # Returns
/// * LapMetrics containing all detected events and statistics
#[pyfunction]
#[pyo3(signature = (frames, lap_number=0, lap_time=None, config=None))]
fn py_extract_lap_metrics(
    frames: Vec<TelemetryFrame>,
    lap_number: i32,
    lap_time: Option<f64>,
    config: Option<AnalysisConfig>,
) -> PyResult<LapMetrics> {
    let config = config.unwrap_or_default();
    Ok(extract_lap_metrics(&frames, &config, lap_number, lap_time))
}

/// Extract braking zones from telemetry frames.
///
/// This is a standalone function for extracting only braking metrics.
/// Use py_extract_lap_metrics for combined analysis.
///
/// # Arguments
/// * `frames` - List of TelemetryFrame objects
/// * `config` - Optional AnalysisConfig (uses defaults if not provided)
///
/// # Returns
/// * List of BrakingMetrics for each detected braking zone
#[pyfunction]
#[pyo3(signature = (frames, config=None))]
fn py_extract_braking_zones(
    frames: Vec<TelemetryFrame>,
    config: Option<AnalysisConfig>,
) -> PyResult<Vec<BrakingMetrics>> {
    let config = config.unwrap_or_default();
    Ok(extract_braking_zones(&frames, &config))
}

/// Extract corners from telemetry frames.
///
/// This is a standalone function for extracting only corner metrics.
/// Use py_extract_lap_metrics for combined analysis.
///
/// # Arguments
/// * `frames` - List of TelemetryFrame objects
/// * `config` - Optional AnalysisConfig (uses defaults if not provided)
///
/// # Returns
/// * List of CornerMetrics for each detected corner
#[pyfunction]
#[pyo3(signature = (frames, config=None))]
fn py_extract_corners(
    frames: Vec<TelemetryFrame>,
    config: Option<AnalysisConfig>,
) -> PyResult<Vec<CornerMetrics>> {
    let config = config.unwrap_or_default();
    Ok(extract_corners(&frames, &config))
}

/// A simple hello world function to verify Rust + PyO3 integration works.
///
/// Call this from Python to verify the Rust extension is properly installed:
/// ```python
/// from racing_coach_core._rs import hello_from_rust
/// print(hello_from_rust())  # "Hello from Rust!"
/// print(hello_from_rust("Racing Coach"))  # "Hello, Racing Coach! Greetings from Rust."
/// ```
#[pyfunction]
#[pyo3(signature = (name=None))]
fn hello_from_rust(name: Option<&str>) -> String {
    match name {
        Some(n) => format!("Hello, {}! Greetings from Rust.", n),
        None => "Hello from Rust!".to_string(),
    }
}

/// Compute basic speed statistics from a list of speeds.
///
/// # Arguments
/// * `speeds` - List of speed values in m/s
///
/// # Returns
/// * Tuple of (min, max, mean) speeds
#[pyfunction]
fn compute_speed_stats(speeds: Vec<f64>) -> PyResult<(f64, f64, f64)> {
    if speeds.is_empty() {
        return Ok((0.0, 0.0, 0.0));
    }

    let sum: f64 = speeds.iter().sum();
    let count = speeds.len() as f64;
    let mean = sum / count;

    let min = speeds.iter().cloned().fold(f64::INFINITY, f64::min);
    let max = speeds.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

    Ok((min, max, mean))
}

// ============================================================================
// Python module definition
// ============================================================================

/// The Python module definition.
/// This creates a module named `_rs` that will be placed at `racing_coach_core._rs`
#[pymodule]
fn _rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Types
    m.add_class::<TelemetryFrame>()?;
    m.add_class::<AnalysisConfig>()?;

    // Results
    m.add_class::<BrakingMetrics>()?;
    m.add_class::<CornerMetrics>()?;
    m.add_class::<LapMetrics>()?;

    // Functions
    m.add_function(wrap_pyfunction!(py_extract_lap_metrics, m)?)?;
    m.add_function(wrap_pyfunction!(py_extract_braking_zones, m)?)?;
    m.add_function(wrap_pyfunction!(py_extract_corners, m)?)?;
    m.add_function(wrap_pyfunction!(hello_from_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_speed_stats, m)?)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello_from_rust() {
        assert_eq!(hello_from_rust(None), "Hello from Rust!");
        assert_eq!(
            hello_from_rust(Some("Test")),
            "Hello, Test! Greetings from Rust."
        );
    }

    #[test]
    fn test_compute_speed_stats() {
        let result = compute_speed_stats(vec![10.0, 20.0, 30.0]).unwrap();
        assert_eq!(result, (10.0, 30.0, 20.0));
    }

    #[test]
    fn test_compute_speed_stats_empty() {
        let result = compute_speed_stats(vec![]).unwrap();
        assert_eq!(result, (0.0, 0.0, 0.0));
    }
}
