//! Telemetry frame definitions for iRacing data.
//!
//! Uses pitwall's derive macro for type-safe frame construction.

use pitwall::PitwallFrame;

/// Complete racing telemetry frame matching Python TelemetryFrame structure.
///
/// This frame is used for both live and replay telemetry collection.
/// All fields map to iRacing's telemetry variable names.
#[derive(PitwallFrame, Debug, Clone)]
pub struct RacingFrame {
    // Time
    #[field_name = "SessionTime"]
    pub session_time: f64,

    // Lap Information
    #[field_name = "Lap"]
    pub lap_number: i32,

    #[field_name = "LapDistPct"]
    pub lap_distance_pct: f32,

    #[field_name = "LapDist"]
    pub lap_distance: f32,

    #[field_name = "LapCurrentLapTime"]
    pub current_lap_time: f32,

    #[field_name = "LapLastLapTime"]
    pub last_lap_time: f32,

    #[field_name = "LapBestLapTime"]
    pub best_lap_time: f32,

    // Vehicle State
    #[field_name = "Speed"]
    pub speed: f32,

    #[field_name = "RPM"]
    pub rpm: f32,

    #[field_name = "Gear"]
    pub gear: i32,

    // Driver Inputs
    #[field_name = "Throttle"]
    pub throttle: f32,

    #[field_name = "Brake"]
    pub brake: f32,

    #[field_name = "Clutch"]
    #[missing = "0.0f32"]
    pub clutch: f32,

    #[field_name = "SteeringWheelAngle"]
    pub steering_angle: f32,

    // Vehicle Dynamics
    #[field_name = "LatAccel"]
    pub lateral_acceleration: f32,

    #[field_name = "LongAccel"]
    pub longitudinal_acceleration: f32,

    #[field_name = "VertAccel"]
    #[missing = "0.0f32"]
    pub vertical_acceleration: f32,

    #[field_name = "YawRate"]
    pub yaw_rate: f32,

    #[field_name = "RollRate"]
    #[missing = "0.0f32"]
    pub roll_rate: f32,

    #[field_name = "PitchRate"]
    #[missing = "0.0f32"]
    pub pitch_rate: f32,

    // Vehicle Velocity
    #[field_name = "VelocityX"]
    pub velocity_x: f32,

    #[field_name = "VelocityY"]
    pub velocity_y: f32,

    #[field_name = "VelocityZ"]
    #[missing = "0.0f32"]
    pub velocity_z: f32,

    // Vehicle Orientation
    #[field_name = "Yaw"]
    pub yaw: f32,

    #[field_name = "Pitch"]
    #[missing = "0.0f32"]
    pub pitch: f32,

    #[field_name = "Roll"]
    #[missing = "0.0f32"]
    pub roll: f32,

    // Track Conditions
    #[field_name = "TrackTempCrew"]
    #[missing = "25.0f32"]
    pub track_temp: f32,

    #[field_name = "AirTemp"]
    #[missing = "20.0f32"]
    pub air_temp: f32,

    // Session State
    #[field_name = "OnPitRoad"]
    pub on_pit_road: bool,
}

impl RacingFrame {
    /// Convert speed from m/s to km/h
    pub fn speed_kmh(&self) -> f32 {
        self.speed * 3.6
    }

    /// Convert speed from m/s to mph
    pub fn speed_mph(&self) -> f32 {
        self.speed * 2.237
    }

    /// Check if the driver is braking (brake > threshold)
    pub fn is_braking(&self, threshold: f32) -> bool {
        self.brake > threshold
    }

    /// Check if the driver is on throttle (throttle > threshold)
    pub fn is_on_throttle(&self, threshold: f32) -> bool {
        self.throttle > threshold
    }

    /// Check if steering input is significant (above threshold in either direction)
    pub fn is_steering(&self, threshold: f32) -> bool {
        self.steering_angle.abs() > threshold
    }

    /// Get lateral G-force (acceleration / 9.81)
    pub fn lateral_g(&self) -> f32 {
        self.lateral_acceleration / 9.81
    }

    /// Get longitudinal G-force (acceleration / 9.81)
    pub fn longitudinal_g(&self) -> f32 {
        self.longitudinal_acceleration / 9.81
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_frame() -> RacingFrame {
        RacingFrame {
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

    #[test]
    fn test_speed_conversion() {
        let frame = sample_frame();
        assert!((frame.speed_kmh() - 180.0).abs() < 0.1);
        assert!((frame.speed_mph() - 111.85).abs() < 0.1);
    }

    #[test]
    fn test_g_force() {
        let frame = sample_frame();
        assert!((frame.lateral_g() - 1.53).abs() < 0.01);
    }

    #[test]
    fn test_is_braking() {
        let mut frame = sample_frame();
        assert!(!frame.is_braking(0.05));
        frame.brake = 0.5;
        assert!(frame.is_braking(0.05));
    }
}
