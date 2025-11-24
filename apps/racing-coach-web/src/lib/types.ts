/**
 * Type definitions for the application
 * These will be replaced/augmented by Orval-generated types
 */

export interface Session {
  session_id: string;
  track_name: string;
  track_config_name?: string;
  track_type: string;
  car_name: string;
  series_id: number;
  created_at: string;
}

export interface Lap {
  id: string;
  track_session_id: string;
  lap_number: number;
  lap_time: number | null;
  is_valid: boolean;
  created_at: string;
}

export interface TelemetryFrame {
  timestamp: string;
  session_time: number;
  lap_number: number;
  lap_distance_pct: number;
  lap_distance: number;
  current_lap_time: number;
  speed: number;
  rpm: number;
  gear: number;
  throttle: number;
  brake: number;
  clutch: number;
  steering_angle: number;
  lateral_acceleration: number;
  longitudinal_acceleration: number;
  vertical_acceleration: number;
  yaw_rate: number;
  position_x: number;
  position_y: number;
  position_z: number;
  tire_temps: Record<string, Record<string, number>>;
  tire_wear: Record<string, Record<string, number>>;
  track_temp: number;
  air_temp: number;
}

export interface BrakingMetrics {
  braking_point_distance: number;
  braking_point_speed: number;
  end_distance: number;
  max_brake_pressure: number;
  braking_duration: number;
  minimum_speed: number;
  initial_deceleration: number;
  average_deceleration: number;
  braking_efficiency: number;
  has_trail_braking: boolean;
  trail_brake_distance?: number;
  trail_brake_percentage?: number;
}

export interface CornerMetrics {
  turn_in_distance: number;
  apex_distance: number;
  exit_distance: number;
  throttle_application_distance: number;
  turn_in_speed: number;
  apex_speed: number;
  exit_speed: number;
  throttle_application_speed: number;
  max_lateral_g: number;
  time_in_corner: number;
  corner_distance: number;
  max_steering_angle: number;
  speed_loss: number;
  speed_gain: number;
}

export interface LapMetrics {
  lap_id: string;
  lap_time: number;
  total_corners: number;
  total_braking_zones: number;
  average_corner_speed: number;
  max_speed: number;
  min_speed: number;
  braking_zones: BrakingMetrics[];
  corners: CornerMetrics[];
}
