// use client_rs::Config;
use tracing::info;
use tracing_subscriber::{EnvFilter, fmt};

use client_rs::run_events;

#[tokio::main]
async fn main() {
    // Set log level by RUST_LOG if set or default to `info`
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_thread_ids(true)
        .with_file(false)
        .with_line_number(true)
        .init();

    info!("Racing Coach Client v{}", env!("CARGO_PKG_VERSION"));

    // let config = Config::new("http://localhost:8000");
    // client_rs::run(&config);

    println!("Hello World!");

    run_events().await;

    // read_telemetry().await;

    tokio::time::sleep(std::time::Duration::from_secs(5)).await;
    println!("Main Done.");
}
