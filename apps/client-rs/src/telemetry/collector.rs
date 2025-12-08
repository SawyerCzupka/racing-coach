//! Telemetry collector that bridges telemetry sources to the event bus.

use chrono::Utc;
use futures::StreamExt;
use pitwall::{SessionInfo, UpdateRate};
use std::sync::Arc;
use tokio::sync::watch;
use tokio_util::sync::CancellationToken;
use tracing::{debug, error, info, warn};
use uuid::Uuid;

use super::frame::RacingFrame;
use super::source::{TelemetrySource, TelemetrySourceConfig, TelemetrySourceError};
use crate::events::{
    Event, EventBus, EventPublisher, SessionInfo as EventSessionInfo, TelemetryEventPayload,
    TelemetryFrame,
};

/// Telemetry collector errors
#[derive(Debug, thiserror::Error)]
pub enum CollectorError {
    #[error("Source error: {0}")]
    SourceError(#[from] TelemetrySourceError),

    #[error("Event bus error: {0}")]
    EventBusError(String),
}

/// Telemetry collector that collects frames and publishes events
pub struct TelemetryCollector {
    config: TelemetrySourceConfig,
    cancel: CancellationToken,
    current_session_id: watch::Sender<Option<Uuid>>,
}

impl TelemetryCollector {
    /// Create a new telemetry collector
    pub fn new(config: TelemetrySourceConfig) -> Self {
        let (session_tx, _) = watch::channel(None);
        Self {
            config,
            cancel: CancellationToken::new(),
            current_session_id: session_tx,
        }
    }

    /// Get a watch receiver for the current session ID
    pub fn session_id_receiver(&self) -> watch::Receiver<Option<Uuid>> {
        self.current_session_id.subscribe()
    }

    /// Start collecting telemetry and publishing events
    ///
    /// This method spawns an async task that:
    /// 1. Connects to the telemetry source
    /// 2. Publishes SESSION_START event with session info
    /// 3. Streams telemetry frames and publishes TELEMETRY_EVENT events
    /// 4. Publishes SESSION_END event when the stream ends
    pub async fn run(self, event_bus: Arc<EventBus>) -> Result<(), CollectorError> {
        info!(
            "Starting telemetry collector in {:?} mode",
            self.config.mode
        );

        // Create telemetry source
        let source = TelemetrySource::create(&self.config).await?;
        let publisher = event_bus.publisher();

        // Wait for initial session info
        let session_info = self.wait_for_session(&source).await;
        let session_id = Uuid::new_v4();

        // Update session ID watch
        let _ = self.current_session_id.send(Some(session_id));

        // Publish session start event
        if let Some(info) = &session_info {
            self.publish_session_start(&publisher, info, session_id).await;
        }

        // Subscribe to telemetry frames
        let mut frame_stream = source.subscribe(UpdateRate::Native);

        // Collection loop
        let mut frame_count: u64 = 0;
        info!("Starting telemetry collection loop");

        loop {
            tokio::select! {
                // Handle cancellation
                _ = self.cancel.cancelled() => {
                    info!("Collector cancelled");
                    break;
                }

                // Handle next frame
                frame = frame_stream.next() => {
                    match frame {
                        Some(racing_frame) => {
                            frame_count += 1;

                            // Convert frame and publish event
                            let telemetry_frame = racing_frame_to_telemetry(&racing_frame);
                            let event = Event::TelemetryEvent(TelemetryEventPayload {
                                frame: telemetry_frame,
                                session_id,
                            });

                            if let Err(e) = publisher.publish(event).await {
                                error!("Failed to publish telemetry event: {}", e);
                            }

                            // Log progress periodically
                            if frame_count % 1000 == 0 {
                                debug!(
                                    "Collected {} frames (lap {}, {:.1}%)",
                                    frame_count,
                                    racing_frame.lap_number,
                                    racing_frame.lap_distance_pct * 100.0
                                );
                            }
                        }
                        None => {
                            info!("Telemetry stream ended");
                            break;
                        }
                    }
                }
            }
        }

        // Publish session end event
        self.publish_session_end(&publisher, session_id).await;
        let _ = self.current_session_id.send(None);

        info!("Telemetry collection complete: {} frames collected", frame_count);
        Ok(())
    }

    /// Wait for session info to become available
    async fn wait_for_session(&self, source: &TelemetrySource) -> Option<Arc<SessionInfo>> {
        info!("Waiting for session info...");

        // First check if session is already available
        if let Some(session) = source.current_session() {
            info!("Session info available: {}", session.weekend_info.track_name);
            return Some(session);
        }

        // Wait for session update
        let mut session_stream = source.session_updates();
        tokio::select! {
            _ = self.cancel.cancelled() => {
                warn!("Cancelled while waiting for session info");
                None
            }
            session = session_stream.next() => {
                if let Some(s) = &session {
                    info!("Session info received: {}", s.weekend_info.track_name);
                }
                session
            }
        }
    }

    /// Publish session start event
    async fn publish_session_start(
        &self,
        publisher: &EventPublisher,
        session: &SessionInfo,
        session_id: Uuid,
    ) {
        let weekend = &session.weekend_info;
        let driver_info = session.driver_info.as_ref();

        // Get car info from driver info if available
        let (car_id, car_name, car_class_id) = if let Some(di) = driver_info {
            let car_idx = di.driver_car_idx.unwrap_or(0) as usize;
            if let Some(drivers) = &di.drivers {
                if let Some(driver) = drivers.get(car_idx) {
                    (
                        driver.car_id.unwrap_or(0),
                        driver.car_screen_name.clone().unwrap_or_default(),
                        driver.car_class_id.unwrap_or(0),
                    )
                } else {
                    (0, String::new(), 0)
                }
            } else {
                (0, String::new(), 0)
            }
        } else {
            (0, String::new(), 0)
        };

        let session_info = EventSessionInfo {
            session_id,
            timestamp: Utc::now(),
            track_id: weekend.track_id.unwrap_or(0),
            track_name: weekend.track_name.clone(),
            track_config_name: weekend.track_config_name.clone(),
            track_type: weekend.track_type.clone().unwrap_or_else(|| "road course".to_string()),
            car_id,
            car_name,
            car_class_id,
            series_id: weekend.series_id.unwrap_or(0),
        };

        info!(
            "Starting session: {} - {} ({})",
            session_info.track_name,
            session_info.car_name,
            session_id
        );

        if let Err(e) = publisher.publish(Event::SessionStart(session_info)).await {
            error!("Failed to publish session start event: {}", e);
        }
    }

    /// Publish session end event
    async fn publish_session_end(&self, publisher: &EventPublisher, session_id: Uuid) {
        info!("Session ended: {}", session_id);

        if let Err(e) = publisher
            .publish(Event::SessionEnd { session_id })
            .await
        {
            error!("Failed to publish session end event: {}", e);
        }
    }

    /// Request graceful shutdown
    pub fn shutdown(&self) {
        info!("Collector shutdown requested");
        self.cancel.cancel();
    }

    /// Get cancellation token for external use
    pub fn cancel_token(&self) -> CancellationToken {
        self.cancel.clone()
    }
}

/// Convert a RacingFrame to the event system's TelemetryFrame
fn racing_frame_to_telemetry(frame: &RacingFrame) -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time: frame.session_time,
        lap_number: frame.lap_number,
        lap_distance_pct: frame.lap_distance_pct,
        lap_distance: frame.lap_distance,
        current_lap_time: frame.current_lap_time,
        last_lap_time: frame.last_lap_time,
        best_lap_time: frame.best_lap_time,
        speed: frame.speed,
        rpm: frame.rpm,
        gear: frame.gear,
        throttle: frame.throttle,
        brake: frame.brake,
        clutch: frame.clutch,
        steering_angle: frame.steering_angle,
        lateral_acceleration: frame.lateral_acceleration,
        longitudinal_acceleration: frame.longitudinal_acceleration,
        vertical_acceleration: frame.vertical_acceleration,
        yaw_rate: frame.yaw_rate,
        roll_rate: frame.roll_rate,
        pitch_rate: frame.pitch_rate,
        velocity_x: frame.velocity_x,
        velocity_y: frame.velocity_y,
        velocity_z: frame.velocity_z,
        yaw: frame.yaw,
        pitch: frame.pitch,
        roll: frame.roll,
        track_temp: frame.track_temp,
        air_temp: frame.air_temp,
        on_pit_road: frame.on_pit_road,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::TelemetryMode;

    #[test]
    fn test_collector_creation() {
        let config = TelemetrySourceConfig {
            mode: TelemetryMode::Replay,
            ibt_file: Some(std::path::PathBuf::from("test.ibt")),
            playback_speed: 1.0,
        };

        let collector = TelemetryCollector::new(config);
        assert!(collector.session_id_receiver().borrow().is_none());
    }

    #[test]
    fn test_racing_frame_conversion() {
        let racing_frame = RacingFrame {
            session_time: 100.0,
            lap_number: 5,
            lap_distance_pct: 0.5,
            lap_distance: 2500.0,
            current_lap_time: 45.5,
            last_lap_time: 90.0,
            best_lap_time: 88.5,
            speed: 50.0,
            rpm: 7500.0,
            gear: 4,
            throttle: 0.8,
            brake: 0.0,
            clutch: 0.0,
            steering_angle: 0.1,
            lateral_acceleration: 15.0,
            longitudinal_acceleration: 2.0,
            vertical_acceleration: 0.0,
            yaw_rate: 0.05,
            roll_rate: 0.01,
            pitch_rate: 0.0,
            velocity_x: 49.0,
            velocity_y: 5.0,
            velocity_z: 0.0,
            yaw: 1.5,
            pitch: 0.0,
            roll: 0.02,
            track_temp: 30.0,
            air_temp: 25.0,
            on_pit_road: false,
        };

        let telemetry = racing_frame_to_telemetry(&racing_frame);

        assert_eq!(telemetry.lap_number, 5);
        assert_eq!(telemetry.speed, 50.0);
        assert_eq!(telemetry.throttle, 0.8);
        assert!(!telemetry.on_pit_road);
    }
}
