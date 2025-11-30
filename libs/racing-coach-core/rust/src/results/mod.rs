//! Result types for telemetry analysis.

mod braking;
mod corner;
mod lap;

pub use braking::{BrakingMetrics, BrakingMetricsBuilder};
pub use corner::{CornerMetrics, CornerMetricsBuilder};
pub use lap::LapMetrics;
