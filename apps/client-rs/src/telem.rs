use crate::events::RacingEvent;
use crate::pitwall_ext::AcceleratedReplayConnection;
use crate::pos_service::PositionState;
use eventbus::EventBus;
use futures::StreamExt;
use pitwall::{PitwallFrame, UpdateRate};
use std::sync::Arc;
use tokio::sync::watch;

#[derive(Debug, PitwallFrame)]
pub struct TelemetryFrame {
    #[field_name = "SessionTime"]
    pub session_time: f64,
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

    #[field_name = "Speed"]
    pub speed: f32,
    #[field_name = "RPM"]
    pub rpm: f32,
    #[field_name = "Gear"]
    pub gear: i32,
    #[field_name = "Throttle"]
    pub throttle: f32,
    #[field_name = "Brake"]
    pub brake: f32,
    #[field_name = "Clutch"]
    pub clutch: f32,

    #[field_name = "PlayerTrackSurface"]
    pub track_surface: i32,
}

pub async fn read_telemetry_print() {
    let connection = AcceleratedReplayConnection::open(
        "../../sample_data/ligierjsp320_bathurst 2025-11-17 18-15-16.ibt",
        5.0,
    )
    .await
    .unwrap();

    let mut stream = connection.subscribe::<TelemetryFrame>(UpdateRate::Max(60));

    while let Some(frame) = stream.next().await {
        println!(
            "Speed: {:.1} mph, RPM: {}, Gear: {}",
            frame.speed, frame.rpm, frame.gear
        )
    }
}

pub async fn read_telemetry_eventbus(
    bus: EventBus<RacingEvent>,
    speed: f64,
    pos_tx: watch::Sender<PositionState>,
) {
    let connection = AcceleratedReplayConnection::open(
        "../../../sample_data/ligierjsp320_bathurst 2025-11-17 18-15-16.ibt",
        speed,
    )
    .await
    .unwrap();

    let mut stream = connection.subscribe::<TelemetryFrame>(UpdateRate::Max(60));
    let mut published_count: u64 = 0;

    while let Some(frame) = stream.next().await {
        match pos_tx.send(PositionState {
            lap_dist_pct: frame.lap_distance_pct,
            lap_number: frame.lap_number,
        }) {
            Ok(_) => {}
            Err(error) => {
                println!("Error Msg: '{error}'");
                panic!();
            }
        }

        match bus.publish(RacingEvent::TelemetryFrameCollected(Arc::new(frame))) {
            Ok(_) => {}
            Err(error) => {
                println!("Error Msg: {error}")
            }
        }
        published_count += 1;
    }

    println!(
        "[Telemetry Publisher] Finished - total frames published: {}",
        published_count
    );
}
