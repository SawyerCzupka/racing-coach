//! API module for Racing Coach server communication.

pub mod client;
pub mod models;

pub use client::{ApiError, RacingCoachClient};
pub use models::*;
