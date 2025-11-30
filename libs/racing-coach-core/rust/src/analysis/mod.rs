//! Analysis functions for telemetry data.

mod deceleration;
mod statistics;
mod trail_braking;

pub use deceleration::calculate_deceleration;
pub use statistics::SpeedStatistics;
pub use trail_braking::{detect_trail_braking, TrailBrakingInfo};
