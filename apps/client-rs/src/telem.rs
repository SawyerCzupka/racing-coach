use std::sync::Arc;

use futures::StreamExt;
use pitwall::{PitwallFrame, UpdateRate};
use tokio::sync::watch;

use crate::events::{Event, EventBus, TelemetryFramePayload};
use crate::pitwall_ext::AcceleratedReplayConnection;
use crate::pos_service::PositionState;

#[derive(Debug, PitwallFrame)]
struct CarData {
    #[field_name = "Speed"]
    speed: f32,
    #[field_name = "RPM"]
    rpm: f32,
    #[field_name = "Gear"]
    gear: i32,
    #[field_name = "Lap"]
    lap: i32,
    #[field_name = "LapDistPct"]
    lap_dist_pct: f32,
    #[field_name = "SessionTime"]
    session_time: f64,
}

pub async fn read_telemetry_print() {
    let connection = AcceleratedReplayConnection::open(
        "../../sample_data/ligierjsp320_bathurst 2025-11-17 18-15-16.ibt",
        5.0,
    )
    .await
    .unwrap();

    let mut stream = connection.subscribe::<CarData>(UpdateRate::Max(60));

    while let Some(frame) = stream.next().await {
        println!(
            "Speed: {:.1} mph, RPM: {}, Gear: {}",
            frame.speed, frame.rpm, frame.gear
        )
    }
}

pub async fn read_telemetry_eventbus(
    bus: EventBus,
    speed: f64,
    pos_tx: watch::Sender<PositionState>,
) {
    let connection = AcceleratedReplayConnection::open(
        "../../sample_data/ligierjsp320_bathurst 2025-11-17 18-15-16.ibt",
        speed,
    )
    .await
    .unwrap();

    let mut stream = connection.subscribe::<CarData>(UpdateRate::Max(60));
    let mut published_count: u64 = 0;

    while let Some(frame) = stream.next().await {
        match pos_tx.send(PositionState {
            lap_dist_pct: frame.lap_dist_pct,
            lap_number: frame.lap,
        }) {
            Ok(_) => {}
            Err(error) => {
                println!("Error Msg: '{error}'");
                panic!();
            }
        }

        let payload = TelemetryFramePayload {
            speed: frame.speed,
            rpm: frame.rpm,
            gear: frame.gear,
            lap_number: frame.lap,
            lap_distance_pct: frame.lap_dist_pct,
            session_time: frame.session_time,
        };

        bus.publish(Event::TelemetryFrame(Arc::new(payload)))
            .unwrap();
        published_count += 1;
    }

    println!(
        "[Telemetry Publisher] Finished - total frames published: {}",
        published_count
    );
}
