//! Integration tests for configuration module.

use racing_coach_client::config::{CliArgs, Config, ConfigError, TelemetryMode};
use std::path::PathBuf;
use tempfile::NamedTempFile;

#[test]
fn test_telemetry_mode_parsing() {
    // Case insensitive parsing
    assert_eq!("live".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
    assert_eq!("Live".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
    assert_eq!("LIVE".parse::<TelemetryMode>().unwrap(), TelemetryMode::Live);
    assert_eq!("replay".parse::<TelemetryMode>().unwrap(), TelemetryMode::Replay);
    assert_eq!("Replay".parse::<TelemetryMode>().unwrap(), TelemetryMode::Replay);
    assert_eq!("REPLAY".parse::<TelemetryMode>().unwrap(), TelemetryMode::Replay);
}

#[test]
fn test_telemetry_mode_invalid() {
    assert!("invalid".parse::<TelemetryMode>().is_err());
    assert!("".parse::<TelemetryMode>().is_err());
    assert!("live_mode".parse::<TelemetryMode>().is_err());
}

#[test]
fn test_telemetry_mode_display() {
    assert_eq!(format!("{}", TelemetryMode::Live), "live");
    assert_eq!(format!("{}", TelemetryMode::Replay), "replay");
}

#[test]
fn test_default_config() {
    let config = Config::default();

    assert_eq!(config.mode, TelemetryMode::Live);
    assert!(config.ibt_file.is_none());
    assert_eq!(config.playback_speed, 1.0);
    assert_eq!(config.server_url, "http://localhost:8000");
    assert!(config.upload_enabled);
    assert_eq!(config.log_level, "info");
    assert_eq!(config.lap_completion_threshold, 0.05);
}

#[test]
fn test_config_api_urls() {
    let config = Config {
        server_url: "http://example.com:9000".to_string(),
        ..Default::default()
    };

    assert_eq!(config.telemetry_api_url(), "http://example.com:9000/api/v1/telemetry");
    assert_eq!(config.metrics_api_url(), "http://example.com:9000/api/v1/metrics");
    assert_eq!(config.sessions_api_url(), "http://example.com:9000/api/v1/sessions");
    assert_eq!(config.health_url(), "http://example.com:9000/api/v1/health");
}

#[test]
fn test_cli_args_validation_live_mode() {
    let args = CliArgs {
        mode: TelemetryMode::Live,
        file: None,
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    assert!(args.validate().is_ok());
}

#[test]
fn test_cli_args_validation_replay_without_file() {
    let args = CliArgs {
        mode: TelemetryMode::Replay,
        file: None, // Missing file for replay mode
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::MissingIbtFile));
}

#[test]
fn test_cli_args_validation_replay_with_nonexistent_file() {
    let args = CliArgs {
        mode: TelemetryMode::Replay,
        file: Some(PathBuf::from("/nonexistent/path/file.ibt")),
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::IbtFileNotFound(_)));
}

#[test]
fn test_cli_args_validation_replay_with_existing_file() {
    // Create a temporary file
    let temp_file = NamedTempFile::new().unwrap();
    let path = temp_file.path().to_path_buf();

    let args = CliArgs {
        mode: TelemetryMode::Replay,
        file: Some(path),
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    assert!(args.validate().is_ok());
}

#[test]
fn test_cli_args_validation_invalid_playback_speed_zero() {
    let args = CliArgs {
        mode: TelemetryMode::Live,
        file: None,
        speed: 0.0, // Invalid: zero
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::InvalidPlaybackSpeed(_)));
}

#[test]
fn test_cli_args_validation_invalid_playback_speed_negative() {
    let args = CliArgs {
        mode: TelemetryMode::Live,
        file: None,
        speed: -1.0, // Invalid: negative
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::InvalidPlaybackSpeed(_)));
}

#[test]
fn test_cli_args_validation_valid_playback_speeds() {
    for speed in [0.1, 0.5, 1.0, 2.0, 10.0, 100.0] {
        let args = CliArgs {
            mode: TelemetryMode::Live,
            file: None,
            speed,
            server_url: "http://localhost:8000".to_string(),
            upload: true,
            log_level: "info".to_string(),
            lap_completion_threshold: 0.05,
        };

        assert!(args.validate().is_ok(), "Speed {} should be valid", speed);
    }
}

#[test]
fn test_cli_args_validation_invalid_threshold_negative() {
    let args = CliArgs {
        mode: TelemetryMode::Live,
        file: None,
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: -0.1, // Invalid: negative
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::InvalidThreshold(_)));
}

#[test]
fn test_cli_args_validation_invalid_threshold_greater_than_one() {
    let args = CliArgs {
        mode: TelemetryMode::Live,
        file: None,
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 1.5, // Invalid: > 1.0
    };

    let result = args.validate();
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), ConfigError::InvalidThreshold(_)));
}

#[test]
fn test_cli_args_validation_valid_thresholds() {
    for threshold in [0.0, 0.01, 0.05, 0.1, 0.5, 0.99, 1.0] {
        let args = CliArgs {
            mode: TelemetryMode::Live,
            file: None,
            speed: 1.0,
            server_url: "http://localhost:8000".to_string(),
            upload: true,
            log_level: "info".to_string(),
            lap_completion_threshold: threshold,
        };

        assert!(args.validate().is_ok(), "Threshold {} should be valid", threshold);
    }
}

#[test]
fn test_config_from_args() {
    let temp_file = NamedTempFile::new().unwrap();
    let path = temp_file.path().to_path_buf();

    let args = CliArgs {
        mode: TelemetryMode::Replay,
        file: Some(path.clone()),
        speed: 2.0,
        server_url: "http://custom:9000".to_string(),
        upload: false,
        log_level: "debug".to_string(),
        lap_completion_threshold: 0.1,
    };

    let config = Config::from_args(args).unwrap();

    assert_eq!(config.mode, TelemetryMode::Replay);
    assert_eq!(config.ibt_file, Some(path));
    assert_eq!(config.playback_speed, 2.0);
    assert_eq!(config.server_url, "http://custom:9000");
    assert!(!config.upload_enabled);
    assert_eq!(config.log_level, "debug");
    assert_eq!(config.lap_completion_threshold, 0.1);
}

#[test]
fn test_config_from_args_fails_validation() {
    let args = CliArgs {
        mode: TelemetryMode::Replay,
        file: None, // Invalid: missing file for replay
        speed: 1.0,
        server_url: "http://localhost:8000".to_string(),
        upload: true,
        log_level: "info".to_string(),
        lap_completion_threshold: 0.05,
    };

    let result = Config::from_args(args);
    assert!(result.is_err());
}

#[test]
fn test_config_error_display() {
    let errors = vec![
        (ConfigError::MissingIbtFile, "IBT file path is required"),
        (ConfigError::IbtFileNotFound(PathBuf::from("/test")), "/test"),
        (ConfigError::InvalidPlaybackSpeed(-1.0), "-1"),
        (ConfigError::InvalidThreshold(2.0), "2"),
        (ConfigError::Other("custom error".to_string()), "custom error"),
    ];

    for (error, expected_substring) in errors {
        let error_str = error.to_string();
        assert!(
            error_str.contains(expected_substring),
            "Error '{}' should contain '{}'",
            error_str,
            expected_substring
        );
    }
}

#[test]
fn test_config_url_with_trailing_slash() {
    let config = Config {
        server_url: "http://example.com:8000/".to_string(),
        ..Default::default()
    };

    // URLs should work even with trailing slash (though not ideal)
    assert!(config.telemetry_api_url().contains("/api/v1/telemetry"));
}

#[test]
fn test_config_with_different_ports() {
    for port in [80, 443, 8000, 8080, 3000, 9000] {
        let config = Config {
            server_url: format!("http://localhost:{}", port),
            ..Default::default()
        };

        assert!(config.health_url().contains(&port.to_string()));
    }
}

#[test]
fn test_config_with_https() {
    let config = Config {
        server_url: "https://secure.example.com".to_string(),
        ..Default::default()
    };

    assert!(config.health_url().starts_with("https://"));
}
