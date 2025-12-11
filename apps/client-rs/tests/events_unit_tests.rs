//! Unit tests for the events module (types, payloads, error, handler).

use chrono::Utc;
use racing_coach_client::events::{
    BrakingMetrics, CornerMetrics, Event, EventBusError, HandlerError, LapMetricsExtractedPayload,
    LapMetricsPayload, LapTelemetryPayload, LapTelemetrySequencePayload, SessionInfo,
    TelemetryEventPayload, TelemetryFrame, TimestampedEvent,
};
use std::sync::Arc;
use uuid::Uuid;

// ============================================================================
// Test Helpers
// ============================================================================

fn create_test_session() -> SessionInfo {
    SessionInfo {
        session_id: Uuid::new_v4(),
        timestamp: Utc::now(),
        track_id: 142,
        track_name: "Mount Panorama".to_string(),
        track_config_name: Some("Full Circuit".to_string()),
        track_type: "road course".to_string(),
        car_id: 123,
        car_name: "Mazda MX-5".to_string(),
        car_class_id: 456,
        series_id: 789,
    }
}

fn create_test_frame() -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
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
    }
}

fn create_test_braking_metrics() -> BrakingMetrics {
    BrakingMetrics {
        braking_point_distance: 0.5,
        braking_point_speed: 80.0,
        end_distance: 0.55,
        max_brake_pressure: 0.95,
        braking_duration: 1.5,
        minimum_speed: 40.0,
        initial_deceleration: 15.0,
        average_deceleration: 12.0,
        braking_efficiency: 0.85,
        has_trail_braking: true,
        trail_brake_distance: 0.02,
        trail_brake_percentage: 0.3,
    }
}

fn create_test_corner_metrics() -> CornerMetrics {
    CornerMetrics {
        turn_in_distance: 0.4,
        apex_distance: 0.45,
        exit_distance: 0.5,
        throttle_application_distance: 0.47,
        turn_in_speed: 60.0,
        apex_speed: 45.0,
        exit_speed: 55.0,
        throttle_application_speed: 48.0,
        max_lateral_g: 2.5,
        time_in_corner: 3.0,
        corner_distance: 0.1,
        max_steering_angle: 0.8,
        speed_loss: 15.0,
        speed_gain: 10.0,
    }
}

// ============================================================================
// TimestampedEvent Tests
// ============================================================================

#[test]
fn test_timestamped_event_creation() {
    let before = Utc::now();
    let event = Event::SessionEnd {
        session_id: Uuid::new_v4(),
    };
    let timestamped = TimestampedEvent::new(event);
    let after = Utc::now();

    assert!(timestamped.timestamp >= before);
    assert!(timestamped.timestamp <= after);
}

#[test]
fn test_timestamped_event_preserves_event() {
    let session_id = Uuid::new_v4();
    let event = Event::SessionEnd { session_id };
    let timestamped = TimestampedEvent::new(event);

    match timestamped.event {
        Event::SessionEnd { session_id: id } => assert_eq!(id, session_id),
        _ => panic!("Expected SessionEnd event"),
    }
}

#[test]
fn test_timestamped_event_clone() {
    let event = Event::SessionStart(create_test_session());
    let timestamped = TimestampedEvent::new(event);
    let cloned = timestamped.clone();

    assert_eq!(timestamped.timestamp, cloned.timestamp);
}

#[test]
fn test_timestamped_event_debug() {
    let event = Event::SessionEnd {
        session_id: Uuid::new_v4(),
    };
    let timestamped = TimestampedEvent::new(event);
    let debug_str = format!("{:?}", timestamped);

    assert!(debug_str.contains("TimestampedEvent"));
    assert!(debug_str.contains("SessionEnd"));
}

// ============================================================================
// Event Enum Tests
// ============================================================================

#[test]
fn test_event_telemetry_frame_variant() {
    let frame = create_test_frame();
    let event = Event::TelemetryFrame(frame.clone());

    match event {
        Event::TelemetryFrame(f) => {
            assert_eq!(f.lap_number, frame.lap_number);
            assert_eq!(f.speed, frame.speed);
        }
        _ => panic!("Expected TelemetryFrame variant"),
    }
}

#[test]
fn test_event_telemetry_event_variant() {
    let frame = create_test_frame();
    let session_id = Uuid::new_v4();
    let payload = TelemetryEventPayload {
        frame: frame.clone(),
        session_id,
    };
    let event = Event::TelemetryEvent(payload);

    match event {
        Event::TelemetryEvent(p) => {
            assert_eq!(p.session_id, session_id);
            assert_eq!(p.frame.lap_number, frame.lap_number);
        }
        _ => panic!("Expected TelemetryEvent variant"),
    }
}

#[test]
fn test_event_session_start_variant() {
    let session = create_test_session();
    let event = Event::SessionStart(session.clone());

    match event {
        Event::SessionStart(s) => {
            assert_eq!(s.track_name, session.track_name);
            assert_eq!(s.car_id, session.car_id);
        }
        _ => panic!("Expected SessionStart variant"),
    }
}

#[test]
fn test_event_session_end_variant() {
    let session_id = Uuid::new_v4();
    let event = Event::SessionEnd { session_id };

    match event {
        Event::SessionEnd { session_id: id } => assert_eq!(id, session_id),
        _ => panic!("Expected SessionEnd variant"),
    }
}

#[test]
fn test_event_lap_telemetry_sequence_variant() {
    let frames = vec![create_test_frame(), create_test_frame()];
    let session = create_test_session();
    let lap_id = Uuid::new_v4();

    let payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames: Arc::new(frames),
            lap_time: Some(90.5),
        },
        session,
        lap_id,
    };

    let event = Event::LapTelemetrySequence(payload);

    match event {
        Event::LapTelemetrySequence(p) => {
            assert_eq!(p.lap_id, lap_id);
            assert_eq!(p.lap_telemetry.frames.len(), 2);
            assert_eq!(p.lap_telemetry.lap_time, Some(90.5));
        }
        _ => panic!("Expected LapTelemetrySequence variant"),
    }
}

#[test]
fn test_event_lap_metrics_extracted_variant() {
    let session = create_test_session();
    let lap_id = Uuid::new_v4();

    let metrics = LapMetricsPayload {
        lap_number: 5,
        lap_time: Some(90.5),
        max_speed: 85.0,
        min_speed: 25.0,
        average_corner_speed: 45.0,
        total_corners: 10,
        total_braking_zones: 8,
        braking_zones: vec![create_test_braking_metrics()],
        corners: vec![create_test_corner_metrics()],
    };

    let payload = LapMetricsExtractedPayload {
        metrics,
        session,
        lap_id,
    };

    let event = Event::LapMetricsExtracted(payload);

    match event {
        Event::LapMetricsExtracted(p) => {
            assert_eq!(p.lap_id, lap_id);
            assert_eq!(p.metrics.lap_number, 5);
            assert_eq!(p.metrics.total_corners, 10);
        }
        _ => panic!("Expected LapMetricsExtracted variant"),
    }
}

#[test]
fn test_event_clone() {
    let session = create_test_session();
    let event = Event::SessionStart(session);
    let cloned = event.clone();

    match (event, cloned) {
        (Event::SessionStart(e1), Event::SessionStart(e2)) => {
            assert_eq!(e1.session_id, e2.session_id);
        }
        _ => panic!("Clone should preserve variant"),
    }
}

#[test]
fn test_event_debug() {
    let event = Event::SessionEnd {
        session_id: Uuid::new_v4(),
    };
    let debug_str = format!("{:?}", event);
    assert!(debug_str.contains("SessionEnd"));
}

// ============================================================================
// SessionInfo Tests
// ============================================================================

#[test]
fn test_session_info_creation() {
    let session = create_test_session();

    assert_eq!(session.track_id, 142);
    assert_eq!(session.track_name, "Mount Panorama");
    assert_eq!(session.track_config_name, Some("Full Circuit".to_string()));
    assert_eq!(session.car_id, 123);
    assert_eq!(session.car_name, "Mazda MX-5");
}

#[test]
fn test_session_info_clone() {
    let session = create_test_session();
    let cloned = session.clone();

    assert_eq!(session.session_id, cloned.session_id);
    assert_eq!(session.track_name, cloned.track_name);
    assert_eq!(session.timestamp, cloned.timestamp);
}

#[test]
fn test_session_info_debug() {
    let session = create_test_session();
    let debug_str = format!("{:?}", session);

    assert!(debug_str.contains("SessionInfo"));
    assert!(debug_str.contains("Mount Panorama"));
}

#[test]
fn test_session_info_without_config_name() {
    let session = SessionInfo {
        session_id: Uuid::new_v4(),
        timestamp: Utc::now(),
        track_id: 100,
        track_name: "Spa".to_string(),
        track_config_name: None,
        track_type: "road course".to_string(),
        car_id: 50,
        car_name: "Test Car".to_string(),
        car_class_id: 1,
        series_id: 2,
    };

    assert!(session.track_config_name.is_none());
}

// ============================================================================
// TelemetryFrame Tests
// ============================================================================

#[test]
fn test_telemetry_frame_creation() {
    let frame = create_test_frame();

    assert_eq!(frame.lap_number, 5);
    assert_eq!(frame.speed, 50.0);
    assert_eq!(frame.throttle, 0.8);
    assert_eq!(frame.brake, 0.0);
    assert!(!frame.on_pit_road);
}

#[test]
fn test_telemetry_frame_clone() {
    let frame = create_test_frame();
    let cloned = frame.clone();

    assert_eq!(frame.lap_number, cloned.lap_number);
    assert_eq!(frame.speed, cloned.speed);
    assert_eq!(frame.timestamp, cloned.timestamp);
}

#[test]
fn test_telemetry_frame_debug() {
    let frame = create_test_frame();
    let debug_str = format!("{:?}", frame);

    assert!(debug_str.contains("TelemetryFrame"));
    assert!(debug_str.contains("lap_number"));
}

#[test]
fn test_telemetry_frame_all_fields() {
    let frame = create_test_frame();

    // Verify all fields are accessible
    assert!(frame.session_time > 0.0);
    assert!(frame.lap_distance_pct >= 0.0 && frame.lap_distance_pct <= 1.0);
    assert!(frame.lap_distance >= 0.0);
    assert!(frame.current_lap_time >= 0.0);
    assert!(frame.rpm > 0.0);
    assert!(frame.gear > 0);
}

// ============================================================================
// TelemetryEventPayload Tests
// ============================================================================

#[test]
fn test_telemetry_event_payload_creation() {
    let frame = create_test_frame();
    let session_id = Uuid::new_v4();

    let payload = TelemetryEventPayload { frame, session_id };

    assert_eq!(payload.session_id, session_id);
    assert_eq!(payload.frame.lap_number, 5);
}

#[test]
fn test_telemetry_event_payload_clone() {
    let payload = TelemetryEventPayload {
        frame: create_test_frame(),
        session_id: Uuid::new_v4(),
    };
    let cloned = payload.clone();

    assert_eq!(payload.session_id, cloned.session_id);
}

// ============================================================================
// LapTelemetryPayload Tests
// ============================================================================

#[test]
fn test_lap_telemetry_payload_with_frames() {
    let frames = vec![create_test_frame(), create_test_frame(), create_test_frame()];

    let payload = LapTelemetryPayload {
        frames: Arc::new(frames),
        lap_time: Some(90.5),
    };

    assert_eq!(payload.frames.len(), 3);
    assert_eq!(payload.lap_time, Some(90.5));
}

#[test]
fn test_lap_telemetry_payload_without_lap_time() {
    let payload = LapTelemetryPayload {
        frames: Arc::new(vec![]),
        lap_time: None,
    };

    assert!(payload.lap_time.is_none());
}

#[test]
fn test_lap_telemetry_payload_arc_sharing() {
    let frames = Arc::new(vec![create_test_frame()]);
    let payload1 = LapTelemetryPayload {
        frames: frames.clone(),
        lap_time: Some(90.0),
    };
    let payload2 = LapTelemetryPayload {
        frames: frames.clone(),
        lap_time: Some(91.0),
    };

    // Both payloads share the same frame data
    assert!(Arc::ptr_eq(&payload1.frames, &payload2.frames));
}

// ============================================================================
// LapTelemetrySequencePayload Tests
// ============================================================================

#[test]
fn test_lap_telemetry_sequence_payload() {
    let session = create_test_session();
    let lap_id = Uuid::new_v4();
    let frames = vec![create_test_frame()];

    let payload = LapTelemetrySequencePayload {
        lap_telemetry: LapTelemetryPayload {
            frames: Arc::new(frames),
            lap_time: Some(88.0),
        },
        session,
        lap_id,
    };

    assert_eq!(payload.lap_id, lap_id);
    assert_eq!(payload.lap_telemetry.lap_time, Some(88.0));
}

// ============================================================================
// BrakingMetrics Tests
// ============================================================================

#[test]
fn test_braking_metrics_creation() {
    let metrics = create_test_braking_metrics();

    assert_eq!(metrics.braking_point_distance, 0.5);
    assert_eq!(metrics.braking_point_speed, 80.0);
    assert_eq!(metrics.max_brake_pressure, 0.95);
    assert!(metrics.has_trail_braking);
}

#[test]
fn test_braking_metrics_clone() {
    let metrics = create_test_braking_metrics();
    let cloned = metrics.clone();

    assert_eq!(metrics.braking_point_distance, cloned.braking_point_distance);
    assert_eq!(metrics.has_trail_braking, cloned.has_trail_braking);
}

#[test]
fn test_braking_metrics_debug() {
    let metrics = create_test_braking_metrics();
    let debug_str = format!("{:?}", metrics);

    assert!(debug_str.contains("BrakingMetrics"));
    assert!(debug_str.contains("braking_point_distance"));
}

// ============================================================================
// CornerMetrics Tests
// ============================================================================

#[test]
fn test_corner_metrics_creation() {
    let metrics = create_test_corner_metrics();

    assert_eq!(metrics.turn_in_distance, 0.4);
    assert_eq!(metrics.apex_distance, 0.45);
    assert_eq!(metrics.max_lateral_g, 2.5);
}

#[test]
fn test_corner_metrics_clone() {
    let metrics = create_test_corner_metrics();
    let cloned = metrics.clone();

    assert_eq!(metrics.apex_distance, cloned.apex_distance);
    assert_eq!(metrics.max_lateral_g, cloned.max_lateral_g);
}

#[test]
fn test_corner_metrics_debug() {
    let metrics = create_test_corner_metrics();
    let debug_str = format!("{:?}", metrics);

    assert!(debug_str.contains("CornerMetrics"));
    assert!(debug_str.contains("apex_distance"));
}

// ============================================================================
// LapMetricsPayload Tests
// ============================================================================

#[test]
fn test_lap_metrics_payload_creation() {
    let metrics = LapMetricsPayload {
        lap_number: 5,
        lap_time: Some(90.5),
        max_speed: 85.0,
        min_speed: 25.0,
        average_corner_speed: 45.0,
        total_corners: 10,
        total_braking_zones: 8,
        braking_zones: vec![create_test_braking_metrics()],
        corners: vec![create_test_corner_metrics()],
    };

    assert_eq!(metrics.lap_number, 5);
    assert_eq!(metrics.lap_time, Some(90.5));
    assert_eq!(metrics.total_corners, 10);
    assert_eq!(metrics.braking_zones.len(), 1);
    assert_eq!(metrics.corners.len(), 1);
}

#[test]
fn test_lap_metrics_payload_empty_zones() {
    let metrics = LapMetricsPayload {
        lap_number: 1,
        lap_time: None,
        max_speed: 0.0,
        min_speed: 0.0,
        average_corner_speed: 0.0,
        total_corners: 0,
        total_braking_zones: 0,
        braking_zones: vec![],
        corners: vec![],
    };

    assert!(metrics.braking_zones.is_empty());
    assert!(metrics.corners.is_empty());
}

// ============================================================================
// LapMetricsExtractedPayload Tests
// ============================================================================

#[test]
fn test_lap_metrics_extracted_payload() {
    let session = create_test_session();
    let lap_id = Uuid::new_v4();

    let payload = LapMetricsExtractedPayload {
        metrics: LapMetricsPayload {
            lap_number: 3,
            lap_time: Some(95.0),
            max_speed: 80.0,
            min_speed: 30.0,
            average_corner_speed: 50.0,
            total_corners: 5,
            total_braking_zones: 4,
            braking_zones: vec![],
            corners: vec![],
        },
        session,
        lap_id,
    };

    assert_eq!(payload.lap_id, lap_id);
    assert_eq!(payload.metrics.lap_number, 3);
}

// ============================================================================
// EventBusError Tests
// ============================================================================

#[test]
fn test_event_bus_error_channel_closed() {
    let error = EventBusError::ChannelClosed;
    let error_str = format!("{}", error);
    assert!(error_str.contains("channel closed") || error_str.contains("Channel closed"));
}

#[test]
fn test_event_bus_error_not_running() {
    let error = EventBusError::NotRunning;
    let error_str = format!("{}", error);
    assert!(error_str.contains("not running") || error_str.contains("Not running"));
}

#[test]
fn test_event_bus_error_debug() {
    let error = EventBusError::ChannelClosed;
    let debug_str = format!("{:?}", error);
    assert!(debug_str.contains("ChannelClosed"));
}

// ============================================================================
// HandlerError Tests
// ============================================================================

#[test]
fn test_handler_error_processing_error() {
    let error = HandlerError::ProcessingError("test error".to_string());
    let error_str = format!("{}", error);
    assert!(error_str.contains("test error"));
}

#[test]
fn test_handler_error_from_event_bus_error() {
    let bus_error = EventBusError::ChannelClosed;
    let handler_error: HandlerError = bus_error.into();

    match handler_error {
        HandlerError::PublishError(_) => (),
        _ => panic!("Expected PublishError variant"),
    }
}

#[test]
fn test_handler_error_debug() {
    let error = HandlerError::ProcessingError("debug test".to_string());
    let debug_str = format!("{:?}", error);
    assert!(debug_str.contains("ProcessingError"));
}
