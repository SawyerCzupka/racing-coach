# Racing Coach Rust Client Development Guide

This guide walks you through building a Rust-based telemetry client for Racing Coach, replacing the Python client with a high-performance alternative.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Initialization](#project-initialization)
3. [Generating the Server API SDK](#generating-the-server-api-sdk)
4. [Architecture Overview](#architecture-overview)
5. [Development Order](#development-order)
6. [Concurrency Model](#concurrency-model)
7. [Implementation Guide](#implementation-guide)
8. [Testing Strategy](#testing-strategy)
9. [Common Pitfalls](#common-pitfalls)
10. [Resources](#resources)

---

## Prerequisites

### 1. Install Rust

```bash
# Install rustup (Rust toolchain manager)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Follow prompts, then reload your shell
source ~/.cargo/env

# Verify installation
rustc --version
cargo --version
```

### 2. Install Required Tools

```bash
# Install cargo-progenitor for OpenAPI client generation
cargo install cargo-progenitor

# Install useful development tools
cargo install cargo-watch    # Auto-rebuild on file changes
cargo install cargo-expand   # View macro expansions
cargo install cargo-deny     # Audit dependencies
```

### 3. IDE Setup

**VS Code (Recommended):**
- Install [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer) extension
- Install [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml) for Cargo.toml editing
- Install [Error Lens](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens) for inline error display

**Settings to add (.vscode/settings.json):**
```json
{
  "rust-analyzer.check.command": "clippy",
  "rust-analyzer.cargo.features": "all"
}
```

### 4. Windows-Specific Setup (for iRacing)

The client needs to run on Windows to access live iRacing telemetry. Ensure you have:
- Windows 10/11
- Visual Studio Build Tools (C++ workload) or full Visual Studio
- iRacing installed and running for live telemetry testing

```powershell
# On Windows, you may need MSVC build tools
winget install Microsoft.VisualStudio.2022.BuildTools
# Select "Desktop development with C++" workload during installation
```

---

## Project Initialization

### 1. Create the Project

```bash
cd /home/sawyer/git/racing-coach/apps

# Create new Rust project
cargo new racing-coach-client-rs
cd racing-coach-client-rs

# Initialize git (if not already in monorepo)
# The monorepo already tracks this, so skip git init
```

### 2. Configure Cargo.toml

Replace the generated `Cargo.toml` with:

```toml
[package]
name = "racing-coach-client-rs"
version = "0.1.0"
edition = "2024"
rust-version = "1.85"
description = "High-performance iRacing telemetry client for Racing Coach"
authors = ["Your Name <your.email@example.com>"]

[dependencies]
# Async runtime
tokio = { version = "1", features = ["full", "tracing"] }
futures = "0.3"

# iRacing telemetry - using pitwall for modern, type-safe access
pitwall = "0.1"

# HTTP client for server communication
reqwest = { version = "0.12", features = ["json", "stream", "gzip"] }

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Configuration management
config = "0.14"
dotenvy = "0.15"

# Error handling
anyhow = "1"
thiserror = "2"

# Logging and tracing
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Utilities
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }

# Graceful shutdown
tokio-util = { version = "0.7", features = ["rt"] }

[dev-dependencies]
# Testing
tokio-test = "0.4"
mockall = "0.13"
proptest = "1"
criterion = { version = "0.5", features = ["async_tokio"] }
tempfile = "3"
wiremock = "0.6"

[build-dependencies]
# OpenAPI client generation
progenitor = { git = "https://github.com/oxidecomputer/progenitor" }
prettyplease = "0.2"
syn = "2"

[[bin]]
name = "racing-coach-client"
path = "src/main.rs"

[[bench]]
name = "telemetry_throughput"
harness = false

[profile.release]
lto = true
codegen-units = 1
panic = "abort"

[profile.dev]
# Faster dev builds
opt-level = 0
debug = true

[profile.dev.package."*"]
# Optimize dependencies even in dev
opt-level = 2

[lints.rust]
unsafe_code = "warn"

[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
```

### 3. Create Directory Structure

```bash
mkdir -p src/{api,collectors,events,handlers,telemetry}
mkdir -p tests/{integration,fixtures}
mkdir -p benches
```

Your structure should look like:

```
racing-coach-client-rs/
├── Cargo.toml
├── build.rs                    # API client generation
├── src/
│   ├── main.rs                 # Entry point
│   ├── lib.rs                  # Library root (for testing)
│   ├── config.rs               # Configuration
│   ├── api/
│   │   └── mod.rs              # Generated + wrapper code
│   ├── collectors/
│   │   ├── mod.rs
│   │   ├── source.rs           # TelemetrySource trait
│   │   ├── live.rs             # Live iRacing telemetry
│   │   └── replay.rs           # IBT file replay
│   ├── events/
│   │   ├── mod.rs
│   │   ├── types.rs            # Event definitions
│   │   └── bus.rs              # Event distribution
│   ├── handlers/
│   │   ├── mod.rs
│   │   ├── lap.rs              # Lap assembly
│   │   ├── metrics.rs          # Metrics extraction
│   │   └── upload.rs           # Server uploads
│   └── telemetry/
│       ├── mod.rs
│       └── frame.rs            # TelemetryFrame definition
├── tests/
│   ├── integration/
│   │   └── mod.rs
│   └── fixtures/
│       └── sample.ibt          # Test IBT file
└── benches/
    └── telemetry_throughput.rs
```

---

## Generating the Server API SDK

### Option 1: Build-time Generation (Recommended)

This regenerates the client whenever the OpenAPI spec changes.

**Create `build.rs` in project root:**

```rust
use std::env;
use std::fs;
use std::path::Path;

fn main() {
    // Path to OpenAPI spec (adjust as needed)
    let spec_path = "../racing-coach-server/openapi.json";

    // Only regenerate if spec file changes
    println!("cargo:rerun-if-changed={}", spec_path);

    // Check if spec exists
    if !Path::new(spec_path).exists() {
        // During initial build, spec might not exist yet
        // Generate a placeholder or skip
        eprintln!("Warning: OpenAPI spec not found at {}. Skipping API generation.", spec_path);
        eprintln!("Run the server and export the spec, then rebuild.");
        return;
    }

    let spec = fs::read_to_string(spec_path)
        .expect("Failed to read OpenAPI spec");

    let mut generator = progenitor::Generator::default();

    let tokens = generator
        .generate_tokens(&serde_json::from_str(&spec).unwrap())
        .expect("Failed to generate API client");

    let ast = syn::parse2(tokens).expect("Failed to parse generated code");
    let content = prettyplease::unparse(&ast);

    let out_dir = env::var("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join("api_client.rs");

    fs::write(&dest_path, content).expect("Failed to write API client");
}
```

**Use the generated client in `src/api/mod.rs`:**

```rust
// Include the generated code
include!(concat!(env!("OUT_DIR"), "/api_client.rs"));

// Re-export for convenience
pub use self::Client;
```

### Option 2: Static Crate Generation

Generate a standalone crate that you can inspect and modify:

```bash
# Ensure server is running and spec is available
cd apps/racing-coach-server
uv run fastapi dev src/racing_coach_server/app.py &

# Wait for server to start, then generate
cd ../racing-coach-client-rs

# Download the OpenAPI spec
curl http://localhost:8000/openapi.json -o openapi.json

# Generate the client crate
cargo progenitor \
  -i openapi.json \
  -o ../racing-coach-api-client-rs \
  -n racing_coach_api \
  -v 0.1.0

# Add as dependency in Cargo.toml
# racing_coach_api = { path = "../racing-coach-api-client-rs" }
```

### Exporting the OpenAPI Spec

Add a script to export the spec from the running server:

```bash
# scripts/export-openapi.sh
#!/bin/bash
set -e

SERVER_URL="${SERVER_URL:-http://localhost:8000}"
OUTPUT_PATH="${1:-apps/racing-coach-client-rs/openapi.json}"

echo "Fetching OpenAPI spec from $SERVER_URL..."
curl -s "$SERVER_URL/openapi.json" | jq '.' > "$OUTPUT_PATH"
echo "Saved to $OUTPUT_PATH"
```

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Tokio Runtime                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     broadcast::channel      ┌──────────────────┐  │
│  │  Collector   │ ─────────────────────────▶  │   Event Bus      │  │
│  │  Task        │        Event                │   (broadcast)    │  │
│  └──────────────┘                             └────────┬─────────┘  │
│         │                                              │            │
│         │ pitwall                           subscribe  │            │
│         ▼                                              ▼            │
│  ┌──────────────┐                     ┌─────────────────────────┐   │
│  │  iRacing     │                     │      Handler Tasks      │   │
│  │  Telemetry   │                     ├─────────────────────────┤   │
│  │  (live/ibt)  │                     │ ┌─────┐ ┌─────┐ ┌─────┐ │   │
│  └──────────────┘                     │ │ Lap │ │Metr.│ │Upld.│ │   │
│                                       │ └──┬──┘ └──┬──┘ └──┬──┘ │   │
│                                       └────┼──────┼───────┼────┘   │
│                                            │      │       │        │
│                               ┌────────────┘      │       │        │
│                               ▼                   ▼       ▼        │
│                     ┌──────────────┐      ┌──────────────────┐     │
│                     │ spawn_block  │      │   reqwest        │     │
│                     │ (CPU work)   │      │   (HTTP client)  │     │
│                     └──────────────┘      └──────────────────┘     │
│                                                    │               │
└────────────────────────────────────────────────────┼───────────────┘
                                                     │
                                                     ▼
                                           ┌──────────────────┐
                                           │  Racing Coach    │
                                           │  Server (Python) │
                                           └──────────────────┘
```

### Concurrency Model Options

#### Option A: Broadcast Channel (Recommended)

Best for: Fan-out pattern where multiple handlers need to see every event.

```rust
use tokio::sync::broadcast;

// Single sender, multiple receivers
// Each receiver gets a copy of every message
let (tx, _) = broadcast::channel::<Event>(10_000);

// Handlers subscribe independently
let rx1 = tx.subscribe();  // LapHandler
let rx2 = tx.subscribe();  // MetricsHandler
let rx3 = tx.subscribe();  // UploadHandler
```

**Pros:**
- Simple mental model
- Handlers are decoupled
- Easy to add/remove handlers

**Cons:**
- Events are cloned for each receiver
- Slow receivers can miss events (lagged)

#### Option B: MPSC + Handler Registry

Best for: Central dispatcher with controlled event routing.

```rust
use tokio::sync::mpsc;

// Single channel, dispatcher routes to handlers
let (tx, rx) = mpsc::channel::<Event>(10_000);

// Central dispatcher
async fn dispatch(mut rx: mpsc::Receiver<Event>, handlers: Vec<Box<dyn Handler>>) {
    while let Some(event) = rx.recv().await {
        for handler in &handlers {
            if handler.handles(&event) {
                handler.handle(event.clone()).await;
            }
        }
    }
}
```

**Pros:**
- More control over routing
- Can implement priority/filtering
- Single queue to monitor

**Cons:**
- More complex
- Handlers are coupled to dispatcher

#### Option C: Actor Model with `flume`

Best for: Complex systems with bidirectional communication.

```rust
use flume::{Sender, Receiver};

struct LapHandler {
    inbox: Receiver<Event>,
    outbox: Sender<Event>,
}

impl LapHandler {
    async fn run(self) {
        while let Ok(event) = self.inbox.recv_async().await {
            // Process and potentially emit new events
            if let Some(lap) = self.process(event) {
                self.outbox.send_async(Event::LapCompleted(lap)).await.ok();
            }
        }
    }
}
```

**Pros:**
- Clean isolation
- Bidirectional communication
- Works well with complex event flows

**Cons:**
- More boilerplate
- Need to manage actor lifecycles

### Recommended Approach

Start with **Option A (Broadcast)** because:
1. Matches your Python architecture
2. Simple to implement and debug
3. Handles your fan-out pattern naturally
4. Easy to evolve if needed

---

## Development Order

Follow this order to build incrementally with testable milestones:

### Phase 1: Foundation (Week 1)

1. **Project setup** ✓
   - Cargo.toml with dependencies
   - Directory structure
   - Basic main.rs that compiles

2. **Configuration**
   - Settings struct with serde
   - Environment variable loading
   - Validation

3. **Logging**
   - tracing-subscriber setup
   - Log levels via env filter
   - Colored console output

4. **Basic event types**
   - Event enum
   - Core data structures (TelemetryFrame, SessionInfo)

**Milestone:** `cargo run` starts and logs "Racing Coach Client starting..."

### Phase 2: Telemetry Collection (Week 2)

5. **TelemetrySource trait**
   - Define the interface
   - Error types

6. **Replay source (IBT files)**
   - Parse IBT files with pitwall
   - Implement TelemetrySource trait
   - Playback timing

7. **Live source**
   - Connect to iRacing via pitwall
   - Implement TelemetrySource trait
   - Handle disconnection

**Milestone:** Read frames from an IBT file and print to console

### Phase 3: Event System (Week 3)

8. **Event bus**
   - Broadcast channel wrapper
   - Publish/subscribe methods
   - Shutdown handling

9. **Wire collector to event bus**
   - Collector publishes TelemetryFrame events
   - Verify events are received

**Milestone:** Events flow from collector through bus

### Phase 4: Handlers (Week 4)

10. **LapHandler**
    - Buffer frames
    - Detect lap boundaries
    - Emit LapCompleted events

11. **MetricsHandler**
    - Receive LapCompleted events
    - Extract metrics (port from Python or use Rust)
    - Emit MetricsExtracted events

**Milestone:** Complete laps detected from IBT replay

### Phase 5: Server Integration (Week 5)

12. **API client generation**
    - Set up build.rs or static generation
    - Verify generated types match

13. **UploadHandler**
    - Upload lap telemetry
    - Upload metrics
    - Error handling and retries

**Milestone:** Laps and metrics appear in Racing Coach web dashboard

### Phase 6: Polish (Week 6)

14. **Graceful shutdown**
    - Handle Ctrl+C
    - Drain in-flight events
    - Clean disconnection

15. **Error recovery**
    - Reconnection logic
    - Retry failed uploads
    - Health reporting

16. **Performance testing**
    - Benchmark event throughput
    - Profile memory usage
    - Compare to Python client

**Milestone:** Production-ready client

---

## Implementation Guide

### Core Types

**`src/events/types.rs`:**

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// All events that flow through the system
#[derive(Debug, Clone)]
pub enum Event {
    /// iRacing session started
    SessionStart(SessionInfo),

    /// iRacing session ended
    SessionEnd { session_id: Uuid },

    /// Single telemetry sample
    TelemetryFrame(TelemetryData),

    /// Complete lap assembled from frames
    LapCompleted(LapData),

    /// Metrics extracted from a lap
    MetricsExtracted(MetricsData),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionInfo {
    pub session_id: Uuid,
    pub track_name: String,
    pub car_name: String,
    pub session_type: String,
    pub started_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryData {
    pub session_id: Uuid,
    pub timestamp: DateTime<Utc>,
    pub lap: i32,
    pub lap_dist_pct: f32,
    pub speed: f32,
    pub rpm: f32,
    pub gear: i32,
    pub throttle: f32,
    pub brake: f32,
    pub steering: f32,
    pub lat_accel: f32,
    pub lon_accel: f32,
    // Add more fields as needed
}

#[derive(Debug, Clone)]
pub struct LapData {
    pub lap_id: Uuid,
    pub session_id: Uuid,
    pub lap_number: i32,
    pub frames: Vec<TelemetryData>,
    pub lap_time_seconds: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsData {
    pub lap_id: Uuid,
    pub session_id: Uuid,
    pub lap_number: i32,
    pub braking_zones: Vec<BrakingZone>,
    pub corners: Vec<Corner>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrakingZone {
    pub entry_speed: f32,
    pub min_speed: f32,
    pub brake_pressure_max: f32,
    pub distance: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Corner {
    pub apex_speed: f32,
    pub apex_distance_pct: f32,
    pub max_lateral_g: f32,
}
```

### Event Bus

**`src/events/bus.rs`:**

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use tokio::sync::broadcast;
use tracing::{debug, warn};

use super::types::Event;

/// Capacity for the event channel
const DEFAULT_CAPACITY: usize = 100_000;

/// Simple event bus using broadcast channel
pub struct EventBus {
    sender: broadcast::Sender<Event>,
    stats: EventBusStats,
}

#[derive(Default)]
struct EventBusStats {
    published: AtomicU64,
    dropped: AtomicU64,
}

impl EventBus {
    pub fn new() -> Self {
        Self::with_capacity(DEFAULT_CAPACITY)
    }

    pub fn with_capacity(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self {
            sender,
            stats: EventBusStats::default(),
        }
    }

    /// Publish an event to all subscribers
    pub fn publish(&self, event: Event) {
        match self.sender.send(event) {
            Ok(receiver_count) => {
                self.stats.published.fetch_add(1, Ordering::Relaxed);
                debug!(receivers = receiver_count, "Event published");
            }
            Err(_) => {
                // No receivers - this is okay during shutdown
                self.stats.dropped.fetch_add(1, Ordering::Relaxed);
            }
        }
    }

    /// Subscribe to events
    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.sender.subscribe()
    }

    /// Get a clone of the sender for passing to other components
    pub fn sender(&self) -> broadcast::Sender<Event> {
        self.sender.clone()
    }

    /// Get current stats
    pub fn stats(&self) -> (u64, u64) {
        (
            self.stats.published.load(Ordering::Relaxed),
            self.stats.dropped.load(Ordering::Relaxed),
        )
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new()
    }
}
```

### Configuration

**`src/config.rs`:**

```rust
use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
pub struct Settings {
    /// Server URL for API calls
    #[serde(default = "default_server_url")]
    pub server_url: String,

    /// Telemetry mode: "live" or "replay"
    #[serde(default = "default_mode")]
    pub mode: TelemetryMode,

    /// Log level (trace, debug, info, warn, error)
    #[serde(default = "default_log_level")]
    pub log_level: String,

    /// Event bus capacity
    #[serde(default = "default_bus_capacity")]
    pub event_bus_capacity: usize,
}

#[derive(Debug, Deserialize, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum TelemetryMode {
    Live,
    Replay {
        /// Path to IBT file
        path: PathBuf,
        /// Playback speed multiplier (1.0 = real-time)
        #[serde(default = "default_replay_speed")]
        speed: f32,
        /// Loop replay when finished
        #[serde(default)]
        loop_replay: bool,
    },
}

fn default_server_url() -> String {
    "http://localhost:8000".to_string()
}

fn default_mode() -> TelemetryMode {
    TelemetryMode::Live
}

fn default_log_level() -> String {
    "info".to_string()
}

fn default_bus_capacity() -> usize {
    100_000
}

fn default_replay_speed() -> f32 {
    1.0
}

impl Settings {
    /// Load settings from environment and config files
    pub fn load() -> Result<Self> {
        // Load .env file if present
        dotenvy::dotenv().ok();

        let settings = config::Config::builder()
            // Start with defaults
            .set_default("server_url", default_server_url())?
            .set_default("log_level", default_log_level())?
            .set_default("event_bus_capacity", default_bus_capacity() as i64)?
            // Load from config file if exists
            .add_source(
                config::File::with_name("config")
                    .required(false)
            )
            // Override with environment variables (PREFIX_KEY format)
            .add_source(
                config::Environment::with_prefix("RACING_COACH")
                    .separator("__")
            )
            .build()
            .context("Failed to build configuration")?;

        settings
            .try_deserialize()
            .context("Failed to deserialize configuration")
    }
}
```

### Telemetry Source Trait

**`src/collectors/source.rs`:**

```rust
use anyhow::Result;
use async_trait::async_trait;

use crate::events::types::{SessionInfo, TelemetryData};

/// Trait for telemetry data sources
#[async_trait]
pub trait TelemetrySource: Send + Sync {
    /// Initialize the source and prepare for collection
    async fn start(&mut self) -> Result<()>;

    /// Stop collection and clean up
    async fn stop(&mut self) -> Result<()>;

    /// Get the next telemetry frame, or None if source is exhausted/disconnected
    async fn next_frame(&mut self) -> Option<TelemetryData>;

    /// Get current session information
    fn session_info(&self) -> Option<&SessionInfo>;

    /// Check if source is still connected/active
    fn is_active(&self) -> bool;
}
```

### Main Entry Point

**`src/main.rs`:**

```rust
use anyhow::Result;
use tokio::signal;
use tokio::sync::broadcast;
use tracing::{error, info, warn, Level};
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

mod api;
mod collectors;
mod config;
mod events;
mod handlers;
mod telemetry;

use config::{Settings, TelemetryMode};
use events::{bus::EventBus, types::Event};

#[tokio::main]
async fn main() -> Result<()> {
    // Load configuration
    let settings = Settings::load()?;

    // Initialize logging
    init_logging(&settings.log_level);

    info!("Racing Coach Client starting...");
    info!(?settings.mode, server = %settings.server_url, "Configuration loaded");

    // Create event bus
    let bus = EventBus::with_capacity(settings.event_bus_capacity);

    // Create API client
    let api_client = api::Client::new(&settings.server_url);

    // Spawn handlers
    let lap_handler = handlers::LapHandler::new(
        bus.subscribe(),
        bus.sender(),
    );
    let metrics_handler = handlers::MetricsHandler::new(
        bus.subscribe(),
        bus.sender(),
    );
    let upload_handler = handlers::UploadHandler::new(
        bus.subscribe(),
        api_client,
    );

    let lap_handle = tokio::spawn(lap_handler.run());
    let metrics_handle = tokio::spawn(metrics_handler.run());
    let upload_handle = tokio::spawn(upload_handler.run());

    // Create telemetry source based on config
    let mut source: Box<dyn collectors::TelemetrySource> = match settings.mode {
        TelemetryMode::Live => {
            info!("Connecting to iRacing...");
            Box::new(collectors::LiveSource::new().await?)
        }
        TelemetryMode::Replay { path, speed, loop_replay } => {
            info!(?path, speed, loop_replay, "Opening IBT replay");
            Box::new(collectors::ReplaySource::new(path, speed, loop_replay).await?)
        }
    };

    // Start collection
    source.start().await?;

    if let Some(session) = source.session_info() {
        info!(
            track = %session.track_name,
            car = %session.car_name,
            "Session started"
        );
        bus.publish(Event::SessionStart(session.clone()));
    }

    // Spawn collection task
    let bus_sender = bus.sender();
    let collection_handle = tokio::spawn(async move {
        while let Some(frame) = source.next_frame().await {
            if bus_sender.send(Event::TelemetryFrame(frame)).is_err() {
                // No receivers, shutting down
                break;
            }
        }
        info!("Collection finished");
    });

    // Wait for shutdown signal
    info!("Collecting telemetry. Press Ctrl+C to stop.");

    tokio::select! {
        _ = signal::ctrl_c() => {
            info!("Shutdown signal received");
        }
        _ = collection_handle => {
            info!("Collection completed");
        }
    }

    // Log stats
    let (published, dropped) = bus.stats();
    info!(published, dropped, "Event bus statistics");

    // Graceful shutdown - handlers will exit when channel closes
    drop(bus);

    // Wait briefly for handlers to finish
    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;

    info!("Racing Coach Client stopped");
    Ok(())
}

fn init_logging(level: &str) {
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(level));

    tracing_subscriber::registry()
        .with(filter)
        .with(fmt::layer().with_target(true))
        .init();
}
```

---

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```rust
// src/handlers/lap.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_lap_boundary_detection() {
        let (tx, _) = broadcast::channel(100);
        let (out_tx, mut out_rx) = broadcast::channel(100);

        let handler = LapHandler::new(tx.subscribe(), out_tx);
        let handle = tokio::spawn(handler.run());

        // Send frames that cross a lap boundary
        tx.send(Event::TelemetryFrame(make_frame(lap: 1, pct: 0.95))).unwrap();
        tx.send(Event::TelemetryFrame(make_frame(lap: 2, pct: 0.05))).unwrap();

        // Should emit LapCompleted
        let event = tokio::time::timeout(
            Duration::from_millis(100),
            out_rx.recv()
        ).await.unwrap().unwrap();

        assert!(matches!(event, Event::LapCompleted(_)));
    }
}
```

### Integration Tests

Test components working together:

```rust
// tests/integration/pipeline.rs
#[tokio::test]
async fn test_full_pipeline_with_ibt() {
    let bus = EventBus::new();

    // Set up handlers
    let lap_handler = LapHandler::new(bus.subscribe(), bus.sender());
    let metrics_handler = MetricsHandler::new(bus.subscribe(), bus.sender());

    tokio::spawn(lap_handler.run());
    tokio::spawn(metrics_handler.run());

    // Use replay source with test IBT
    let mut source = ReplaySource::new(
        "tests/fixtures/sample.ibt",
        100.0, // Fast playback
        false,
    ).await.unwrap();

    source.start().await.unwrap();

    // Collect all events
    let mut rx = bus.subscribe();
    let events = collect_events(&mut rx, Duration::from_secs(5)).await;

    // Verify we got expected events
    assert!(events.iter().any(|e| matches!(e, Event::LapCompleted(_))));
    assert!(events.iter().any(|e| matches!(e, Event::MetricsExtracted(_))));
}
```

### Benchmarks

**`benches/telemetry_throughput.rs`:**

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use racing_coach_client_rs::events::{bus::EventBus, types::Event};

fn event_throughput(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();

    let mut group = c.benchmark_group("event_bus");
    group.throughput(Throughput::Elements(1));

    group.bench_function("publish_event", |b| {
        let bus = EventBus::new();
        let _rx = bus.subscribe(); // Need at least one receiver

        b.iter(|| {
            bus.publish(black_box(Event::TelemetryFrame(make_test_frame())));
        });
    });

    group.bench_function("publish_and_receive", |b| {
        b.to_async(&rt).iter(|| async {
            let bus = EventBus::new();
            let mut rx = bus.subscribe();

            bus.publish(Event::TelemetryFrame(make_test_frame()));
            black_box(rx.recv().await.unwrap());
        });
    });

    group.finish();
}

criterion_group!(benches, event_throughput);
criterion_main!(benches);
```

Run benchmarks:

```bash
cargo bench
```

---

## Common Pitfalls

### 1. Blocking in Async Context

**Wrong:**
```rust
async fn process_lap(frames: Vec<Frame>) {
    // This blocks the async runtime!
    let metrics = extract_metrics(&frames); // CPU-intensive
}
```

**Right:**
```rust
async fn process_lap(frames: Vec<Frame>) {
    // Move CPU work to blocking thread pool
    let metrics = tokio::task::spawn_blocking(move || {
        extract_metrics(&frames)
    }).await.unwrap();
}
```

### 2. Lagged Receivers

Broadcast channels drop old messages when slow receivers fall behind:

```rust
let mut rx = bus.subscribe();

loop {
    match rx.recv().await {
        Ok(event) => handle(event),
        Err(broadcast::error::RecvError::Lagged(n)) => {
            // We missed n events!
            warn!(missed = n, "Receiver lagged, events dropped");
        }
        Err(broadcast::error::RecvError::Closed) => break,
    }
}
```

### 3. Ownership in Async Closures

**Wrong:**
```rust
let frames = vec![...];
tokio::spawn(async {
    process(&frames); // Error: frames borrowed across await
});
```

**Right:**
```rust
let frames = vec![...];
tokio::spawn(async move {
    process(&frames); // frames moved into closure
});
```

### 4. Missing Error Context

**Wrong:**
```rust
let data = fs::read_to_string(path)?; // Error: "No such file"
```

**Right:**
```rust
let data = fs::read_to_string(&path)
    .with_context(|| format!("Failed to read config from {}", path.display()))?;
// Error: "Failed to read config from /path/to/file: No such file"
```

### 5. Unbounded Growth

Watch for vectors that grow without bound:

```rust
struct LapHandler {
    buffer: Vec<Frame>, // Can grow to millions of frames!
}

impl LapHandler {
    fn handle_frame(&mut self, frame: Frame) {
        self.buffer.push(frame);

        // Add a safety limit
        if self.buffer.len() > 1_000_000 {
            warn!("Buffer exceeded limit, clearing");
            self.buffer.clear();
        }
    }
}
```

---

## Resources

### Essential Reading

1. **The Rust Book** - https://doc.rust-lang.org/book/
   - Chapters 4-10 (ownership, structs, enums, modules)
   - Chapter 16 (concurrency)

2. **Async Rust Book** - https://rust-lang.github.io/async-book/
   - Understanding futures and async/await

3. **Tokio Tutorial** - https://tokio.rs/tokio/tutorial
   - Complete guide to async Rust with Tokio

### Crate Documentation

- [tokio](https://docs.rs/tokio) - Async runtime
- [pitwall](https://docs.rs/pitwall) - iRacing telemetry
- [serde](https://serde.rs/) - Serialization framework
- [anyhow](https://docs.rs/anyhow) - Error handling
- [tracing](https://docs.rs/tracing) - Logging/diagnostics

### Community

- [Rust Users Forum](https://users.rust-lang.org/)
- [Rust Discord](https://discord.gg/rust-lang)
- [/r/rust](https://reddit.com/r/rust)

### Useful Commands

```bash
# Check code without building
cargo check

# Run with all warnings
cargo clippy

# Format code
cargo fmt

# Run tests
cargo test

# Run specific test
cargo test test_lap_boundary

# Build release binary
cargo build --release

# Watch for changes and rebuild
cargo watch -x check

# Expand macros (see generated code)
cargo expand

# Generate docs
cargo doc --open
```

---

## Next Steps

1. **Start with Phase 1** - Get a minimal `main.rs` that compiles and runs
2. **Set up CI** - Add GitHub Actions for `cargo check`, `cargo test`, `cargo clippy`
3. **Port one handler at a time** - Start with LapHandler since it's the first in the pipeline
4. **Keep the Python client running** - You can run both side-by-side during development
5. **Benchmark early** - Confirm you're getting the performance gains you expect

Good luck! Rust has a learning curve, but once it clicks, you'll appreciate the safety and performance it provides.
