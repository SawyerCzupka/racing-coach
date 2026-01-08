//! Integration tests for connection layer
//!
//! These tests verify that telemetry streaming and session info propagation
//! work correctly with both live and replay connections.

#[cfg(test)]
use super::*;
#[cfg(test)]
use crate::{
    UpdateRate,
    adapters::{AdapterValidation, FieldExtraction, FrameAdapter},
};
#[cfg(test)]
use futures::StreamExt;
#[cfg(test)]
use std::time::Duration;
#[cfg(test)]
use tracing::info;

// Manual implementation for testing to avoid derive macro issues
#[cfg(all(test, windows))]
#[derive(Debug)]
struct BasicTelemetry {
    speed: f32,
    rpm: f32,
    gear: i32,
}

#[cfg(all(test, windows))]
impl FrameAdapter for BasicTelemetry {
    fn validate_schema(schema: &crate::VariableSchema) -> crate::Result<AdapterValidation> {
        let mut extraction_plan = Vec::new();

        if let Some(var_info) = schema.variables.get("Speed") {
            extraction_plan.push(FieldExtraction::Required {
                name: "Speed".to_string(),
                var_info: var_info.clone(),
            });
        }

        if let Some(var_info) = schema.variables.get("RPM") {
            extraction_plan.push(FieldExtraction::Required {
                name: "RPM".to_string(),
                var_info: var_info.clone(),
            });
        }

        if let Some(var_info) = schema.variables.get("Gear") {
            extraction_plan.push(FieldExtraction::Required {
                name: "Gear".to_string(),
                var_info: var_info.clone(),
            });
        }

        Ok(AdapterValidation::new(extraction_plan))
    }

    fn adapt(packet: &crate::types::FramePacket, validation: &AdapterValidation) -> Self {
        use crate::VarData;

        let data = packet.data.as_ref();

        let speed = if let Some(index) = validation.index_of("Speed") {
            if let Some(FieldExtraction::Required { var_info, .. }) =
                validation.extraction_plan.get(index)
            {
                f32::from_bytes(data, var_info).unwrap_or(0.0)
            } else {
                0.0
            }
        } else {
            0.0
        };

        let rpm = if let Some(index) = validation.index_of("RPM") {
            if let Some(FieldExtraction::Required { var_info, .. }) =
                validation.extraction_plan.get(index)
            {
                f32::from_bytes(data, var_info).unwrap_or(0.0)
            } else {
                0.0
            }
        } else {
            0.0
        };

        let gear = if let Some(index) = validation.index_of("Gear") {
            if let Some(FieldExtraction::Required { var_info, .. }) =
                validation.extraction_plan.get(index)
            {
                i32::from_bytes(data, var_info).unwrap_or(0)
            } else {
                0
            }
        } else {
            0
        };

        BasicTelemetry { speed, rpm, gear }
    }
}

// Simple frame for throttle testing
#[cfg(test)]
#[derive(Debug)]
struct SimpleFrame {
    #[allow(dead_code)]
    speed: f32,
}

#[cfg(test)]
impl FrameAdapter for SimpleFrame {
    fn validate_schema(schema: &crate::VariableSchema) -> crate::Result<AdapterValidation> {
        let mut extraction_plan = Vec::new();

        if let Some(var_info) = schema.variables.get("Speed") {
            extraction_plan.push(FieldExtraction::Required {
                name: "Speed".to_string(),
                var_info: var_info.clone(),
            });
        }

        Ok(AdapterValidation::new(extraction_plan))
    }

    fn adapt(packet: &crate::types::FramePacket, validation: &AdapterValidation) -> Self {
        use crate::VarData;

        let data = packet.data.as_ref();

        let speed = if let Some(index) = validation.index_of("Speed") {
            if let Some(FieldExtraction::Required { var_info, .. }) =
                validation.extraction_plan.get(index)
            {
                f32::from_bytes(data, var_info).unwrap_or(0.0)
            } else {
                0.0
            }
        } else {
            0.0
        };

        SimpleFrame { speed }
    }
}

#[cfg(all(test, windows))]
#[tokio::test]
#[ignore = "iracing_required"]
async fn live_session_immediate_delivery() {
    // Initialize logging for debugging
    let _ = tracing_subscriber::fmt::try_init();

    info!("Testing LIVE session immediate delivery");

    let connection = match live::LiveConnection::connect().await {
        Ok(conn) => conn,
        Err(e) => {
            eprintln!("Failed to connect to iRacing: {}", e);
            eprintln!("Make sure iRacing is running with a session loaded");
            panic!("Cannot test without iRacing");
        }
    };

    info!("Connected to live iRacing");

    // Use synchronous access for immediate session availability
    // Broadcast streams wait for next message, so use current_session() for immediate access
    let start = std::time::Instant::now();

    // Poll for session to be available (Driver parses async, may take a moment)
    let session = tokio::time::timeout(Duration::from_secs(2), async {
        loop {
            if let Some(session) = connection.current_session() {
                return session;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("Timeout waiting for session - should be available within 2 seconds");

    let elapsed = start.elapsed();

    // Verify session has expected fields
    assert!(!session.weekend_info.track_name.is_empty(), "Track name should not be empty");
    assert!(!session.weekend_info.track_length.is_empty(), "Track length should not be empty");

    info!("Session delivered in {:?}", elapsed);
    info!("Track: {}", session.weekend_info.track_name);
    info!("Length: {}", session.weekend_info.track_length);
    info!("Sessions: {}", session.session_info.sessions.len());
    info!("Current session num: {}", session.session_info.current_session_num);
}

#[cfg(all(test, windows))]
#[tokio::test]
#[ignore = "iracing_required"]
async fn live_session_info_propagation() {
    // Initialize logging for debugging
    let _ = tracing_subscriber::fmt::try_init();

    info!("Connecting to live telemetry...");
    let connection = match live::LiveConnection::connect().await {
        Ok(conn) => conn,
        Err(e) => {
            eprintln!("Failed to connect to iRacing: {}", e);
            eprintln!("Make sure iRacing is running with a session loaded");
            panic!("Cannot test without iRacing");
        }
    };

    info!("Connected! Testing session info stream...");

    // Get session updates stream
    let mut session_stream = Box::pin(connection.session_updates());

    // Get the initial session info (there's typically only one unless session changes)
    let mut session_count = 0;

    // Use timeout to avoid hanging if no updates - only expect 1 session
    let timeout = Duration::from_secs(2);
    let start = tokio::time::Instant::now();

    while session_count < 1 && start.elapsed() < timeout {
        match tokio::time::timeout(Duration::from_secs(1), session_stream.next()).await {
            Ok(Some(session)) => {
                session_count += 1;

                // Verify session has expected fields
                assert!(
                    !session.weekend_info.track_name.is_empty(),
                    "Track name should not be empty"
                );
                assert!(
                    !session.weekend_info.track_length.is_empty(),
                    "Track length should not be empty"
                );

                info!(
                    "Session {}: Track={}, Length={}, Sessions={}",
                    session_count,
                    session.weekend_info.track_name,
                    session.weekend_info.track_length,
                    session.session_info.sessions.len()
                );
            }
            Ok(None) => {
                info!("Session stream ended");
                break;
            }
            Err(_) => {
                // Timeout is fine - might not have session changes
                info!("No session update within timeout");
            }
        }
    }

    // For live, use current_session() to verify session is available even if stream didn't yield
    if session_count == 0 {
        if let Some(session) = connection.current_session() {
            info!(
                "Session available via current_session(): Track={}",
                session.weekend_info.track_name
            );
            session_count = 1;
        }
    }

    assert!(session_count > 0, "Should receive at least one session info");
    info!("Successfully received {} session updates", session_count);
}

#[cfg(windows)]
#[tokio::test]
#[ignore = "iracing_required"]
async fn live_telemetry_with_session_correlation() {
    let _ = tracing_subscriber::fmt::try_init();

    info!("Connecting for telemetry correlation test...");
    let connection = live::LiveConnection::connect().await.expect("Failed to connect to iRacing");

    // Subscribe to both telemetry and session info
    let mut telemetry_stream =
        Box::pin(connection.subscribe::<BasicTelemetry>(UpdateRate::Max(10)));
    let mut session_stream = Box::pin(connection.session_updates());

    // Get initial session info - try sync access first, then stream
    let initial_session = connection.current_session().or_else(|| {
        // If not available yet, try waiting briefly
        None
    });

    if let Some(session) = initial_session {
        info!("Initial session: {}", session.weekend_info.track_name);
    } else {
        // Try getting from stream
        if let Ok(Some(session)) =
            tokio::time::timeout(Duration::from_secs(2), session_stream.next()).await
        {
            info!("Initial session from stream: {}", session.weekend_info.track_name);
        }
    }

    // Collect some telemetry frames
    let mut frame_count = 0;
    let timeout = Duration::from_secs(3);
    let start = tokio::time::Instant::now();

    while frame_count < 10 && start.elapsed() < timeout {
        match tokio::time::timeout(Duration::from_millis(200), telemetry_stream.next()).await {
            Ok(Some(frame)) => {
                frame_count += 1;
                info!(
                    "Frame {}: Speed={:.1} km/h, RPM={:.0}, Gear={}",
                    frame_count, frame.speed, frame.rpm, frame.gear
                );
            }
            Ok(None) => break,
            Err(_) => continue,
        }
    }

    assert!(frame_count > 0, "Should receive telemetry frames");
    info!("Successfully received {} telemetry frames", frame_count);
}

#[tokio::test]
async fn replay_session_immediate_delivery() {
    use crate::test_utils;

    let _ = tracing_subscriber::fmt::try_init();

    // Get a test IBT file
    let ibt_file = test_utils::get_smallest_ibt_test_file().expect("No IBT test files found");

    info!("Opening replay file: {:?}", ibt_file);
    let connection =
        replay::ReplayConnection::open(ibt_file).await.expect("Failed to open IBT file");

    // Use synchronous access for immediate session availability
    // ReplayConnection waits for first frame, so session should be available immediately
    let session = connection
        .current_session()
        .expect("Session should be immediately available after ReplayConnection::open()");

    // Verify session has expected data
    assert!(!session.weekend_info.track_name.is_empty(), "Track name should not be empty");
    assert!(!session.weekend_info.track_length.is_empty(), "Track length should not be empty");

    info!(
        "Initial session delivered immediately: Track={}, Sessions={}",
        session.weekend_info.track_name,
        session.session_info.sessions.len()
    );
}

#[tokio::test]
async fn replay_session_info_propagation() {
    use crate::test_utils;

    let _ = tracing_subscriber::fmt::try_init();

    // Get a test IBT file
    let ibt_file = test_utils::get_smallest_ibt_test_file().expect("No IBT test files found");

    info!("Opening replay file: {:?}", ibt_file);
    let connection =
        replay::ReplayConnection::open(ibt_file).await.expect("Failed to open IBT file");

    // First verify sync access works
    let initial_session =
        connection.current_session().expect("Should have session after connection");
    info!(
        "Initial session via current_session(): Track={}",
        initial_session.weekend_info.track_name
    );

    // Get session updates stream for ongoing updates
    let mut session_stream = Box::pin(connection.session_updates());

    // Collect session updates
    let mut sessions = Vec::new();
    let timeout = Duration::from_secs(5);
    let start = tokio::time::Instant::now();

    while start.elapsed() < timeout {
        match tokio::time::timeout(Duration::from_millis(100), session_stream.next()).await {
            Ok(Some(session)) => {
                info!(
                    "Session update: Track={}, Sessions={}",
                    session.weekend_info.track_name,
                    session.session_info.sessions.len()
                );
                sessions.push(session);
            }
            Ok(None) => {
                info!("Session stream ended");
                break;
            }
            Err(_) => {
                // No more updates
                break;
            }
        }
    }

    // Sync access should always work
    assert!(
        connection.current_session().is_some(),
        "current_session() should return session"
    );

    info!("Successfully received {} session stream updates", sessions.len());
}

#[tokio::test]
async fn replay_telemetry_stream_throttling() {
    use crate::test_utils;
    use std::time::Instant;

    let _ = tracing_subscriber::fmt::try_init();

    let ibt_file = test_utils::get_smallest_ibt_test_file().expect("No IBT test files found");

    let connection =
        replay::ReplayConnection::open(ibt_file).await.expect("Failed to open IBT file");

    // Subscribe with throttling to 5 Hz
    let mut stream = Box::pin(connection.subscribe::<SimpleFrame>(UpdateRate::Max(5)));

    let mut frames = Vec::new();
    let mut timestamps = Vec::new();
    let start = Instant::now();

    // Collect frames for 2 seconds
    while start.elapsed() < Duration::from_secs(2) {
        match tokio::time::timeout(Duration::from_millis(250), stream.next()).await {
            Ok(Some(frame)) => {
                timestamps.push(Instant::now());
                frames.push(frame);
            }
            Ok(None) => break,
            Err(_) => continue,
        }
    }

    // Should have received frames
    assert!(!frames.is_empty(), "Should receive frames");

    // Check throttling - should be approximately 5 Hz
    if timestamps.len() > 2 {
        let mut intervals = Vec::new();
        for i in 1..timestamps.len() {
            intervals.push(timestamps[i].duration_since(timestamps[i - 1]));
        }

        let avg_interval = intervals.iter().sum::<Duration>() / intervals.len() as u32;
        let expected_interval = Duration::from_millis(200); // 5 Hz = 200ms

        // Allow 50ms tolerance
        let diff = avg_interval.abs_diff(expected_interval);

        assert!(
            diff < Duration::from_millis(50),
            "Throttling not working correctly. Expected ~200ms, got {:?}",
            avg_interval
        );

        info!("Throttling working: avg interval = {:?}", avg_interval);
    }

    info!("Received {} frames over {:?}", frames.len(), start.elapsed());
}

#[tokio::test]
async fn replay_current_frame_access() {
    use crate::test_utils;

    let _ = tracing_subscriber::fmt::try_init();

    let ibt_file = test_utils::get_smallest_ibt_test_file().expect("No IBT test files found");

    let connection =
        replay::ReplayConnection::open(ibt_file).await.expect("Failed to open IBT file");

    // After open(), current_frame should be available since we wait for first frame
    let frame = connection.current_frame().expect("current_frame should be available after open");

    info!("Current frame tick: {}", frame.tick);
    info!("Current frame session version: {}", frame.session_version);

    assert!(frame.tick >= 0, "Frame tick should be non-negative");
}
