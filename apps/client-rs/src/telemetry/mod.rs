//! Telemetry module for iRacing data collection.
//!
//! Provides telemetry sources (live and replay) and collection infrastructure.

pub mod collector;
pub mod frame;
pub mod source;

pub use collector::TelemetryCollector;
pub use frame::RacingFrame;
pub use source::{TelemetrySource, TelemetrySourceConfig, TelemetrySourceError};
