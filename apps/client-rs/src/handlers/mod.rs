//! Event handlers for processing telemetry data.
//!
//! This module contains handlers that react to events from the telemetry collector:
//! - LapHandler: Buffers frames and detects lap completion
//! - MetricsHandler: Extracts performance metrics from laps
//! - LapUploadHandler: Uploads lap telemetry to server
//! - MetricsUploadHandler: Uploads metrics to server

pub mod lap;
pub mod lap_upload;
pub mod metrics;
pub mod metrics_upload;

pub use lap::LapHandler;
pub use lap_upload::LapUploadHandler;
pub use metrics::MetricsHandler;
pub use metrics_upload::MetricsUploadHandler;
