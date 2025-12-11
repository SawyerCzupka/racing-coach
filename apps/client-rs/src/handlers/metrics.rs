//! Metrics handler for extracting performance metrics from lap telemetry.
//!
//! Analyzes lap telemetry to detect braking zones, corners, and compute
//! performance statistics.

use async_trait::async_trait;
use std::time::Instant;
use tracing::{debug, error, info};
use uuid::Uuid;

use crate::events::{
    BrakingMetrics, CornerMetrics, Event, EventHandler, HandlerContext, HandlerError,
    LapMetricsExtractedPayload, LapMetricsPayload, LapTelemetrySequencePayload, TelemetryFrame,
};

/// Configuration for metrics extraction
#[derive(Debug, Clone)]
pub struct MetricsConfig {
    /// Minimum brake pressure to start a braking zone (0.0-1.0)
    pub brake_threshold: f32,
    /// Minimum steering angle to detect cornering (radians)
    pub steering_threshold: f32,
    /// Minimum lateral G for apex detection
    pub min_lateral_g: f32,
    /// Minimum frames for a valid braking zone
    pub min_braking_frames: usize,
    /// Minimum frames for a valid corner
    pub min_corner_frames: usize,
}

impl Default for MetricsConfig {
    fn default() -> Self {
        Self {
            brake_threshold: 0.05,
            steering_threshold: 0.1, // ~5.7 degrees
            min_lateral_g: 0.5,
            min_braking_frames: 10,
            min_corner_frames: 20,
        }
    }
}

/// Handler that extracts performance metrics from completed laps
pub struct MetricsHandler {
    config: MetricsConfig,
}

impl MetricsHandler {
    /// Create a new metrics handler with default configuration
    pub fn new() -> Self {
        Self::with_config(MetricsConfig::default())
    }

    /// Create a new metrics handler with custom configuration
    pub fn with_config(config: MetricsConfig) -> Self {
        Self { config }
    }

    /// Extract metrics from lap telemetry
    fn extract_metrics(
        &self,
        payload: &LapTelemetrySequencePayload,
    ) -> Result<LapMetricsPayload, String> {
        let frames = &payload.lap_telemetry.frames;

        if frames.is_empty() {
            return Err("No frames in lap telemetry".to_string());
        }

        let lap_number = frames[0].lap_number;

        // Extract braking zones
        let braking_zones = self.detect_braking_zones(frames);

        // Extract corners
        let corners = self.detect_corners(frames);

        // Calculate statistics
        let (max_speed, min_speed) = self.calculate_speed_range(frames);
        let average_corner_speed = self.calculate_average_corner_speed(&corners, frames);

        Ok(LapMetricsPayload {
            lap_number,
            lap_time: payload.lap_telemetry.lap_time,
            max_speed,
            min_speed,
            average_corner_speed,
            total_corners: corners.len() as i32,
            total_braking_zones: braking_zones.len() as i32,
            braking_zones,
            corners,
        })
    }

    /// Detect braking zones in the lap
    fn detect_braking_zones(&self, frames: &[TelemetryFrame]) -> Vec<BrakingMetrics> {
        let mut zones = Vec::new();
        let mut in_braking_zone = false;
        let mut zone_start_idx = 0;
        let mut max_pressure: f32 = 0.0;
        let mut min_speed: f32 = f32::MAX;
        let mut entry_speed: f32 = 0.0;

        for (i, frame) in frames.iter().enumerate() {
            let is_braking = frame.brake > self.config.brake_threshold;

            if is_braking && !in_braking_zone {
                // Start new braking zone
                in_braking_zone = true;
                zone_start_idx = i;
                max_pressure = frame.brake;
                entry_speed = frame.speed;
                min_speed = frame.speed;
            } else if is_braking && in_braking_zone {
                // Continue braking zone
                max_pressure = max_pressure.max(frame.brake);
                min_speed = min_speed.min(frame.speed);
            } else if !is_braking && in_braking_zone {
                // End braking zone
                in_braking_zone = false;

                let zone_frames = i - zone_start_idx;
                if zone_frames >= self.config.min_braking_frames {
                    let start_frame = &frames[zone_start_idx];
                    let end_frame = &frames[i - 1];

                    let duration = end_frame.session_time - start_frame.session_time;
                    let decel = if duration > 0.0 {
                        (entry_speed - min_speed) / duration as f32
                    } else {
                        0.0
                    };

                    // Detect trail braking (braking while steering)
                    let (has_trail_braking, trail_distance, trail_pct) =
                        self.detect_trail_braking(frames, zone_start_idx, i);

                    zones.push(BrakingMetrics {
                        braking_point_distance: start_frame.lap_distance_pct,
                        braking_point_speed: entry_speed,
                        end_distance: end_frame.lap_distance_pct,
                        max_brake_pressure: max_pressure,
                        braking_duration: duration as f32,
                        minimum_speed: min_speed,
                        initial_deceleration: self.calculate_initial_decel(frames, zone_start_idx),
                        average_deceleration: decel,
                        braking_efficiency: if max_pressure > 0.0 {
                            decel / (max_pressure * 50.0) // Normalize to expected decel
                        } else {
                            0.0
                        },
                        has_trail_braking,
                        trail_brake_distance: trail_distance,
                        trail_brake_percentage: trail_pct,
                    });
                }

                max_pressure = 0.0;
                min_speed = f32::MAX;
            }
        }

        zones
    }

    /// Detect corners in the lap
    fn detect_corners(&self, frames: &[TelemetryFrame]) -> Vec<CornerMetrics> {
        let mut corners = Vec::new();
        let mut in_corner = false;
        let mut corner_start_idx = 0;
        let mut apex_idx = 0;
        let mut max_lateral_g: f32 = 0.0;
        let mut max_steering: f32 = 0.0;

        for (i, frame) in frames.iter().enumerate() {
            let is_cornering = frame.steering_angle.abs() > self.config.steering_threshold;
            let lateral_g = frame.lateral_acceleration.abs() / 9.81;

            if is_cornering && !in_corner {
                // Start new corner
                in_corner = true;
                corner_start_idx = i;
                apex_idx = i;
                max_lateral_g = lateral_g;
                max_steering = frame.steering_angle.abs();
            } else if is_cornering && in_corner {
                // Continue corner - track apex (max lateral G)
                if lateral_g > max_lateral_g {
                    max_lateral_g = lateral_g;
                    apex_idx = i;
                }
                max_steering = max_steering.max(frame.steering_angle.abs());
            } else if !is_cornering && in_corner {
                // End corner
                in_corner = false;

                let corner_frames = i - corner_start_idx;
                if corner_frames >= self.config.min_corner_frames && max_lateral_g >= self.config.min_lateral_g {
                    let turn_in = &frames[corner_start_idx];
                    let apex = &frames[apex_idx];
                    let exit = &frames[i - 1];

                    // Find throttle application point
                    let (throttle_idx, _) = self.find_throttle_application(frames, apex_idx, i);
                    let throttle_frame = &frames[throttle_idx];

                    let duration = exit.session_time - turn_in.session_time;

                    corners.push(CornerMetrics {
                        turn_in_distance: turn_in.lap_distance_pct,
                        apex_distance: apex.lap_distance_pct,
                        exit_distance: exit.lap_distance_pct,
                        throttle_application_distance: throttle_frame.lap_distance_pct,
                        turn_in_speed: turn_in.speed,
                        apex_speed: apex.speed,
                        exit_speed: exit.speed,
                        throttle_application_speed: throttle_frame.speed,
                        max_lateral_g,
                        time_in_corner: duration as f32,
                        corner_distance: exit.lap_distance_pct - turn_in.lap_distance_pct,
                        max_steering_angle: max_steering,
                        speed_loss: turn_in.speed - apex.speed,
                        speed_gain: exit.speed - apex.speed,
                    });
                }

                max_lateral_g = 0.0;
                max_steering = 0.0;
            }
        }

        corners
    }

    /// Detect trail braking within a braking zone
    fn detect_trail_braking(
        &self,
        frames: &[TelemetryFrame],
        start_idx: usize,
        end_idx: usize,
    ) -> (bool, f32, f32) {
        let mut trail_frames = 0;

        for frame in &frames[start_idx..end_idx] {
            // Trail braking: braking while steering
            if frame.brake > self.config.brake_threshold
                && frame.steering_angle.abs() > self.config.steering_threshold
            {
                trail_frames += 1;
            }
        }

        let total_frames = end_idx - start_idx;
        let has_trail = trail_frames > 3;
        let trail_pct = if total_frames > 0 {
            trail_frames as f32 / total_frames as f32
        } else {
            0.0
        };

        let trail_distance = if has_trail && !frames.is_empty() {
            frames.get(start_idx + trail_frames).map_or(0.0, |f| f.lap_distance_pct)
                - frames[start_idx].lap_distance_pct
        } else {
            0.0
        };

        (has_trail, trail_distance, trail_pct)
    }

    /// Calculate initial deceleration rate (first few frames of braking)
    fn calculate_initial_decel(&self, frames: &[TelemetryFrame], start_idx: usize) -> f32 {
        let sample_frames = 5.min(frames.len() - start_idx);
        if sample_frames < 2 {
            return 0.0;
        }

        let start = &frames[start_idx];
        let end = &frames[start_idx + sample_frames - 1];

        let dt = end.session_time - start.session_time;
        if dt > 0.0 {
            (start.speed - end.speed) / dt as f32
        } else {
            0.0
        }
    }

    /// Find the point where throttle is reapplied after apex
    fn find_throttle_application(
        &self,
        frames: &[TelemetryFrame],
        apex_idx: usize,
        end_idx: usize,
    ) -> (usize, f32) {
        for i in apex_idx..end_idx {
            if frames[i].throttle > 0.2 {
                return (i, frames[i].throttle);
            }
        }
        (apex_idx, 0.0)
    }

    /// Calculate speed range for the lap
    fn calculate_speed_range(&self, frames: &[TelemetryFrame]) -> (f32, f32) {
        let mut max_speed: f32 = 0.0;
        let mut min_speed: f32 = f32::MAX;

        for frame in frames {
            max_speed = max_speed.max(frame.speed);
            min_speed = min_speed.min(frame.speed);
        }

        (max_speed, min_speed)
    }

    /// Calculate average corner speed across all corners
    fn calculate_average_corner_speed(
        &self,
        corners: &[CornerMetrics],
        _frames: &[TelemetryFrame],
    ) -> f32 {
        if corners.is_empty() {
            return 0.0;
        }

        let total: f32 = corners.iter().map(|c| c.apex_speed).sum();
        total / corners.len() as f32
    }
}

impl Default for MetricsHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl EventHandler for MetricsHandler {
    fn name(&self) -> &'static str {
        "MetricsHandler"
    }

    async fn handle(&self, event: &Event, ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::LapTelemetrySequence(payload) => {
                let start = Instant::now();

                match self.extract_metrics(payload) {
                    Ok(metrics) => {
                        let elapsed = start.elapsed();

                        info!(
                            "Extracted metrics for lap {}: {} braking zones, {} corners ({:.1}ms)",
                            metrics.lap_number,
                            metrics.total_braking_zones,
                            metrics.total_corners,
                            elapsed.as_secs_f64() * 1000.0
                        );

                        // Log detailed metrics
                        for (i, braking) in metrics.braking_zones.iter().enumerate() {
                            debug!(
                                "  Braking zone {}: dist={:.3}, speed={:.1} m/s, max_pressure={:.2}, trail={}",
                                i + 1,
                                braking.braking_point_distance,
                                braking.braking_point_speed,
                                braking.max_brake_pressure,
                                braking.has_trail_braking
                            );
                        }

                        for (i, corner) in metrics.corners.iter().enumerate() {
                            debug!(
                                "  Corner {}: turn_in={:.3}, apex={:.3}, exit={:.3}, apex_speed={:.1} m/s, max_lat_g={:.2}",
                                i + 1,
                                corner.turn_in_distance,
                                corner.apex_distance,
                                corner.exit_distance,
                                corner.apex_speed,
                                corner.max_lateral_g
                            );
                        }

                        // Publish metrics extracted event
                        let metrics_event = Event::LapMetricsExtracted(LapMetricsExtractedPayload {
                            metrics,
                            session: payload.session.clone(),
                            lap_id: payload.lap_id,
                        });

                        ctx.publisher
                            .publish(metrics_event)
                            .await
                            .map_err(|e| HandlerError::PublishError(e))?;
                    }
                    Err(e) => {
                        error!("Failed to extract metrics: {}", e);
                    }
                }

                Ok(true)
            }
            _ => Ok(false),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    fn create_test_frame(
        lap_distance_pct: f32,
        speed: f32,
        brake: f32,
        throttle: f32,
        steering: f32,
        lat_accel: f32,
        session_time: f64,
    ) -> TelemetryFrame {
        TelemetryFrame {
            timestamp: Utc::now(),
            session_time,
            lap_number: 1,
            lap_distance_pct,
            lap_distance: lap_distance_pct * 5000.0,
            current_lap_time: session_time as f32,
            last_lap_time: 0.0,
            best_lap_time: 0.0,
            speed,
            rpm: 7500.0,
            gear: 4,
            throttle,
            brake,
            clutch: 0.0,
            steering_angle: steering,
            lateral_acceleration: lat_accel,
            longitudinal_acceleration: 0.0,
            vertical_acceleration: 0.0,
            yaw_rate: 0.0,
            roll_rate: 0.0,
            pitch_rate: 0.0,
            velocity_x: speed,
            velocity_y: 0.0,
            velocity_z: 0.0,
            yaw: 0.0,
            pitch: 0.0,
            roll: 0.0,
            track_temp: 30.0,
            air_temp: 25.0,
            on_pit_road: false,
        }
    }

    #[test]
    fn test_metrics_handler_creation() {
        let handler = MetricsHandler::new();
        assert_eq!(handler.name(), "MetricsHandler");
    }

    #[test]
    fn test_detect_braking_zones() {
        let handler = MetricsHandler::new();

        // Create frames with a braking zone
        let mut frames = Vec::new();

        // Before braking
        for i in 0..20 {
            frames.push(create_test_frame(
                i as f32 * 0.01,
                80.0,
                0.0,
                1.0,
                0.0,
                0.0,
                i as f64 * 0.016,
            ));
        }

        // Braking zone
        for i in 20..40 {
            let speed = 80.0 - (i - 20) as f32 * 2.0;
            frames.push(create_test_frame(
                i as f32 * 0.01,
                speed,
                0.8,
                0.0,
                0.0,
                -15.0,
                i as f64 * 0.016,
            ));
        }

        // After braking
        for i in 40..60 {
            frames.push(create_test_frame(
                i as f32 * 0.01,
                40.0,
                0.0,
                0.5,
                0.0,
                0.0,
                i as f64 * 0.016,
            ));
        }

        let zones = handler.detect_braking_zones(&frames);
        assert_eq!(zones.len(), 1);
        assert!(zones[0].max_brake_pressure > 0.5);
    }

    #[test]
    fn test_detect_corners() {
        let handler = MetricsHandler::new();

        // Create frames with a corner
        let mut frames = Vec::new();

        // Straight before corner
        for i in 0..30 {
            frames.push(create_test_frame(
                i as f32 * 0.01,
                60.0,
                0.0,
                0.8,
                0.0,
                0.0,
                i as f64 * 0.016,
            ));
        }

        // Corner (turn in, apex, exit) - 40 frames with consistent steering above threshold
        for i in 30..70 {
            let t = (i - 30) as f32 / 40.0;
            // Steering peaks in the middle of the corner, but stays above threshold throughout
            let steering = 0.15 + 0.25 * (t * std::f32::consts::PI).sin();
            // Lateral G peaks at apex (middle)
            let lat_g = 15.0 * (t * std::f32::consts::PI).sin();
            frames.push(create_test_frame(
                i as f32 * 0.01,
                50.0,
                0.0,
                0.3 + t * 0.5,
                steering,
                lat_g,
                i as f64 * 0.016,
            ));
        }

        // Straight after corner
        for i in 70..100 {
            frames.push(create_test_frame(
                i as f32 * 0.01,
                60.0,
                0.0,
                1.0,
                0.0,
                0.0,
                i as f64 * 0.016,
            ));
        }

        let corners = handler.detect_corners(&frames);
        assert!(!corners.is_empty(), "Expected at least one corner to be detected");
        assert!(corners[0].max_lateral_g > 0.5, "Expected significant lateral G");
    }

    #[test]
    fn test_speed_range_calculation() {
        let handler = MetricsHandler::new();

        let frames = vec![
            create_test_frame(0.0, 50.0, 0.0, 1.0, 0.0, 0.0, 0.0),
            create_test_frame(0.1, 80.0, 0.0, 1.0, 0.0, 0.0, 1.0),
            create_test_frame(0.2, 30.0, 0.5, 0.0, 0.0, 0.0, 2.0),
            create_test_frame(0.3, 60.0, 0.0, 0.8, 0.0, 0.0, 3.0),
        ];

        let (max, min) = handler.calculate_speed_range(&frames);
        assert_eq!(max, 80.0);
        assert_eq!(min, 30.0);
    }
}
