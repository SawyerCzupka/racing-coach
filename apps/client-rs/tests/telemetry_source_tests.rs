//! Tests for the telemetry source module.

use racing_coach_client::config::TelemetryMode;
use racing_coach_client::telemetry::{TelemetrySource, TelemetrySourceConfig, TelemetrySourceError};
use std::path::PathBuf;

// ============================================================================
// TelemetrySourceConfig Tests
// ============================================================================

#[test]
fn test_source_config_replay_mode() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 1.0,
    };

    assert_eq!(config.mode, TelemetryMode::Replay);
    assert_eq!(config.playback_speed, 1.0);
    assert!(config.ibt_file.is_some());
}

#[test]
fn test_source_config_live_mode() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Live,
        ibt_file: None,
        playback_speed: 1.0,
    };

    assert_eq!(config.mode, TelemetryMode::Live);
    assert!(config.ibt_file.is_none());
}

#[test]
fn test_source_config_custom_speed() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("data.ibt")),
        playback_speed: 2.5,
    };

    assert_eq!(config.playback_speed, 2.5);
}

#[test]
fn test_source_config_clone() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 1.5,
    };

    let cloned = config.clone();
    assert_eq!(config.mode, cloned.mode);
    assert_eq!(config.playback_speed, cloned.playback_speed);
    assert_eq!(config.ibt_file, cloned.ibt_file);
}

#[test]
fn test_source_config_debug() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 1.0,
    };

    let debug_str = format!("{:?}", config);
    assert!(debug_str.contains("TelemetrySourceConfig"));
    assert!(debug_str.contains("Replay"));
}

// ============================================================================
// TelemetrySourceError Tests
// ============================================================================

#[test]
fn test_error_ibt_open_error() {
    let error = TelemetrySourceError::IbtOpenError("file not found".to_string());
    let error_str = format!("{}", error);
    assert!(error_str.contains("IBT file") || error_str.contains("file not found"));
}

#[test]
fn test_error_connection_error() {
    let error = TelemetrySourceError::ConnectionError("connection refused".to_string());
    let error_str = format!("{}", error);
    assert!(error_str.contains("iRacing") || error_str.contains("connection refused"));
}

#[test]
fn test_error_missing_ibt_file() {
    let error = TelemetrySourceError::MissingIbtFile;
    let error_str = format!("{}", error);
    assert!(error_str.contains("IBT") || error_str.contains("ibt") || error_str.contains("file"));
}

#[test]
fn test_error_debug() {
    let error = TelemetrySourceError::MissingIbtFile;
    let debug_str = format!("{:?}", error);
    assert!(debug_str.contains("MissingIbtFile"));
}

// ============================================================================
// TelemetrySource Creation Tests
// ============================================================================

#[tokio::test]
async fn test_source_create_replay_missing_file() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: None,
        playback_speed: 1.0,
    };

    let result = TelemetrySource::create(&config).await;
    assert!(result.is_err());

    match result {
        Err(TelemetrySourceError::MissingIbtFile) => (),
        _ => panic!("Expected MissingIbtFile error"),
    }
}

#[tokio::test]
async fn test_source_create_replay_nonexistent_file() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("/nonexistent/path/to/file.ibt")),
        playback_speed: 1.0,
    };

    let result = TelemetrySource::create(&config).await;
    assert!(result.is_err());

    match result {
        Err(TelemetrySourceError::IbtOpenError(_)) => (),
        _ => panic!("Expected IbtOpenError"),
    }
}

#[tokio::test]
async fn test_source_create_live_on_non_windows() {
    // On non-Windows platforms, live mode should fail
    #[cfg(not(windows))]
    {
        let config = TelemetrySourceConfig {
            mode: TelemetryMode::Live,
            ibt_file: None,
            playback_speed: 1.0,
        };

        let result = TelemetrySource::create(&config).await;
        assert!(result.is_err());

        match result {
            Err(TelemetrySourceError::ConnectionError(msg)) => {
                assert!(msg.contains("Windows") || msg.contains("windows"));
            }
            _ => panic!("Expected ConnectionError about Windows"),
        }
    }
}

// ============================================================================
// Path Handling Tests
// ============================================================================

#[test]
fn test_source_config_path_with_spaces() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("/path/with spaces/file.ibt")),
        playback_speed: 1.0,
    };

    assert_eq!(
        config.ibt_file.as_ref().unwrap().to_string_lossy(),
        "/path/with spaces/file.ibt"
    );
}

#[test]
fn test_source_config_relative_path() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("./data/test.ibt")),
        playback_speed: 1.0,
    };

    assert!(config.ibt_file.is_some());
}

#[test]
fn test_source_config_absolute_path() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("/home/user/data/test.ibt")),
        playback_speed: 1.0,
    };

    assert!(config.ibt_file.as_ref().unwrap().is_absolute());
}

// ============================================================================
// Playback Speed Tests
// ============================================================================

#[test]
fn test_source_config_speed_normal() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 1.0,
    };

    assert_eq!(config.playback_speed, 1.0);
}

#[test]
fn test_source_config_speed_fast() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 10.0,
    };

    assert_eq!(config.playback_speed, 10.0);
}

#[test]
fn test_source_config_speed_slow() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 0.5,
    };

    assert_eq!(config.playback_speed, 0.5);
}

#[test]
fn test_source_config_speed_fractional() {
    let config = TelemetrySourceConfig {
        mode: TelemetryMode::Replay,
        ibt_file: Some(PathBuf::from("test.ibt")),
        playback_speed: 1.5,
    };

    assert!((config.playback_speed - 1.5).abs() < f64::EPSILON);
}
