//! Event system throughput benchmarks.
//!
//! Run with: cargo bench --bench event_throughput
//!
//! This benchmark measures the maximum throughput of the event bus system
//! in terms of events per second (Hz).

use async_trait::async_trait;
use chrono::Utc;
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use racing_coach_client::events::{
    Event, EventBus, EventBusConfig, EventHandler, HandlerContext, HandlerError, SessionInfo,
    TelemetryEventPayload, TelemetryFrame,
};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tokio::runtime::Runtime;
use tokio::time::Duration;
use uuid::Uuid;

/// Minimal handler that just counts events for benchmarking
struct BenchHandler {
    count: AtomicU64,
}

impl BenchHandler {
    fn new() -> Self {
        Self {
            count: AtomicU64::new(0),
        }
    }

    fn count(&self) -> u64 {
        self.count.load(Ordering::Relaxed)
    }
}

#[async_trait]
impl EventHandler for BenchHandler {
    fn name(&self) -> &'static str {
        "BenchHandler"
    }

    async fn handle(&self, event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        match event {
            Event::TelemetryEvent(_) => {
                self.count.fetch_add(1, Ordering::Relaxed);
                Ok(true)
            }
            _ => Ok(false),
        }
    }
}

/// No-op handler for measuring raw event bus overhead
struct NoOpHandler;

#[async_trait]
impl EventHandler for NoOpHandler {
    fn name(&self) -> &'static str {
        "NoOpHandler"
    }

    async fn handle(&self, _event: &Event, _ctx: &HandlerContext<'_>) -> Result<bool, HandlerError> {
        Ok(false)
    }
}

fn create_test_frame() -> TelemetryFrame {
    TelemetryFrame {
        timestamp: Utc::now(),
        session_time: 100.0,
        lap_number: 1,
        lap_distance_pct: 0.5,
        lap_distance: 2500.0,
        current_lap_time: 45.0,
        last_lap_time: 90.0,
        best_lap_time: 88.0,
        speed: 50.0,
        rpm: 7500.0,
        gear: 4,
        throttle: 0.8,
        brake: 0.0,
        clutch: 0.0,
        steering_angle: 0.0,
        lateral_acceleration: 0.0,
        longitudinal_acceleration: 0.0,
        vertical_acceleration: 0.0,
        yaw_rate: 0.0,
        roll_rate: 0.0,
        pitch_rate: 0.0,
        velocity_x: 50.0,
        velocity_y: 0.0,
        velocity_z: 0.0,
        yaw: 0.0,
        pitch: 0.0,
        roll: 0.0,
        track_temp: 30.0,
        air_temp: 25.0,
        on_pit_road: false,
    }
}

fn create_test_event(session_id: Uuid) -> Event {
    Event::TelemetryEvent(TelemetryEventPayload {
        frame: create_test_frame(),
        session_id,
    })
}

/// Benchmark: Publishing events to the bus without handlers
fn bench_event_publish_only(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("event_publish");
    group.throughput(Throughput::Elements(1));

    group.bench_function("publish_single", |b| {
        b.to_async(&rt).iter_custom(|iters| async move {
            let event_bus = Arc::new(EventBus::new());
            let publisher = event_bus.publisher();

            let start = std::time::Instant::now();
            for _ in 0..iters {
                let event = create_test_event(session_id);
                let _ = black_box(publisher.publish(event).await);
            }
            start.elapsed()
        });
    });

    group.finish();
}

/// Benchmark: Full event flow with a single handler
fn bench_event_full_flow(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("event_full_flow");

    for count in [100, 1000, 10000].iter() {
        group.throughput(Throughput::Elements(*count as u64));

        group.bench_with_input(
            BenchmarkId::new("single_handler", count),
            count,
            |b, &count| {
                b.to_async(&rt).iter_custom(|iters| async move {
                    let mut total_elapsed = std::time::Duration::ZERO;

                    for _ in 0..iters {
                        let event_bus = Arc::new(EventBus::new());
                        let handler = Arc::new(BenchHandler::new());

                        let bus = event_bus.clone();
                        let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
                        let event_loop = tokio::spawn(async move {
                            bus.run(handlers).await;
                        });

                        // Wait for startup
                        tokio::time::sleep(Duration::from_millis(10)).await;

                        let publisher = event_bus.publisher();
                        let start = std::time::Instant::now();

                        // Publish events
                        for _ in 0..count {
                            let event = create_test_event(session_id);
                            publisher.publish(event).await.unwrap();
                        }

                        // Wait for all events to be processed
                        while handler.count() < count as u64 {
                            tokio::time::sleep(Duration::from_micros(100)).await;
                        }

                        total_elapsed += start.elapsed();

                        event_bus.shutdown();
                        let _ = tokio::time::timeout(Duration::from_secs(1), event_loop).await;
                    }

                    total_elapsed
                });
            },
        );
    }

    group.finish();
}

/// Benchmark: Event flow with multiple handlers
fn bench_event_multiple_handlers(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("event_multiple_handlers");
    group.throughput(Throughput::Elements(1000));

    for handler_count in [1, 2, 4, 8].iter() {
        group.bench_with_input(
            BenchmarkId::new("handlers", handler_count),
            handler_count,
            |b, &handler_count| {
                b.to_async(&rt).iter_custom(|iters| async move {
                    let event_count = 1000;
                    let mut total_elapsed = std::time::Duration::ZERO;

                    for _ in 0..iters {
                        let event_bus = Arc::new(EventBus::new());
                        let handlers: Vec<Arc<BenchHandler>> = (0..handler_count)
                            .map(|_| Arc::new(BenchHandler::new()))
                            .collect();

                        let handler_refs: Vec<Arc<dyn EventHandler>> =
                            handlers.iter().map(|h| h.clone() as Arc<dyn EventHandler>).collect();

                        let bus = event_bus.clone();
                        let event_loop = tokio::spawn(async move {
                            bus.run(handler_refs).await;
                        });

                        tokio::time::sleep(Duration::from_millis(10)).await;

                        let publisher = event_bus.publisher();
                        let start = std::time::Instant::now();

                        for _ in 0..event_count {
                            let event = create_test_event(session_id);
                            publisher.publish(event).await.unwrap();
                        }

                        // Wait for all handlers to process all events
                        loop {
                            let all_done = handlers
                                .iter()
                                .all(|h| h.count() >= event_count as u64);
                            if all_done {
                                break;
                            }
                            tokio::time::sleep(Duration::from_micros(100)).await;
                        }

                        total_elapsed += start.elapsed();

                        event_bus.shutdown();
                        let _ = tokio::time::timeout(Duration::from_secs(1), event_loop).await;
                    }

                    total_elapsed
                });
            },
        );
    }

    group.finish();
}

/// Benchmark: Concurrent publishers
fn bench_concurrent_publishers(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();

    let mut group = c.benchmark_group("concurrent_publishers");
    group.throughput(Throughput::Elements(1000));

    for publisher_count in [1, 2, 4, 8].iter() {
        group.bench_with_input(
            BenchmarkId::new("publishers", publisher_count),
            publisher_count,
            |b, &publisher_count| {
                b.to_async(&rt).iter_custom(|iters| async move {
                    let events_per_publisher = 1000 / publisher_count;
                    let total_events = events_per_publisher * publisher_count;
                    let mut total_elapsed = std::time::Duration::ZERO;

                    for _ in 0..iters {
                        let event_bus = Arc::new(EventBus::new());
                        let handler = Arc::new(BenchHandler::new());

                        let bus = event_bus.clone();
                        let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
                        let event_loop = tokio::spawn(async move {
                            bus.run(handlers).await;
                        });

                        tokio::time::sleep(Duration::from_millis(10)).await;

                        let start = std::time::Instant::now();

                        // Spawn concurrent publishers
                        let mut publish_tasks = vec![];
                        for _ in 0..publisher_count {
                            let publisher = event_bus.publisher();
                            let session_id = Uuid::new_v4();
                            let task = tokio::spawn(async move {
                                for _ in 0..events_per_publisher {
                                    let event = create_test_event(session_id);
                                    publisher.publish(event).await.unwrap();
                                }
                            });
                            publish_tasks.push(task);
                        }

                        // Wait for all publishers
                        for task in publish_tasks {
                            task.await.unwrap();
                        }

                        // Wait for processing
                        while handler.count() < total_events as u64 {
                            tokio::time::sleep(Duration::from_micros(100)).await;
                        }

                        total_elapsed += start.elapsed();

                        event_bus.shutdown();
                        let _ = tokio::time::timeout(Duration::from_secs(1), event_loop).await;
                    }

                    total_elapsed
                });
            },
        );
    }

    group.finish();
}

/// Benchmark: Event bus with different channel capacities
fn bench_channel_capacity(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("channel_capacity");
    group.throughput(Throughput::Elements(1000));

    for capacity in [100, 500, 1000, 5000].iter() {
        group.bench_with_input(
            BenchmarkId::new("capacity", capacity),
            capacity,
            |b, &capacity| {
                b.to_async(&rt).iter_custom(|iters| async move {
                    let event_count = 1000;
                    let mut total_elapsed = std::time::Duration::ZERO;

                    for _ in 0..iters {
                        let config = EventBusConfig {
                            channel_capacity: capacity,
                        };
                        let event_bus = Arc::new(EventBus::with_config(config));
                        let handler = Arc::new(BenchHandler::new());

                        let bus = event_bus.clone();
                        let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
                        let event_loop = tokio::spawn(async move {
                            bus.run(handlers).await;
                        });

                        tokio::time::sleep(Duration::from_millis(10)).await;

                        let publisher = event_bus.publisher();
                        let start = std::time::Instant::now();

                        for _ in 0..event_count {
                            let event = create_test_event(session_id);
                            publisher.publish(event).await.unwrap();
                        }

                        while handler.count() < event_count as u64 {
                            tokio::time::sleep(Duration::from_micros(100)).await;
                        }

                        total_elapsed += start.elapsed();

                        event_bus.shutdown();
                        let _ = tokio::time::timeout(Duration::from_secs(1), event_loop).await;
                    }

                    total_elapsed
                });
            },
        );
    }

    group.finish();
}

/// Benchmark: Sync publish performance
fn bench_sync_publish(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("sync_publish");
    group.throughput(Throughput::Elements(1000));

    group.bench_function("sync_publish_1000", |b| {
        b.to_async(&rt).iter_custom(|iters| async move {
            let event_count = 1000;
            let mut total_elapsed = std::time::Duration::ZERO;

            for _ in 0..iters {
                let event_bus = Arc::new(EventBus::new());
                let handler = Arc::new(BenchHandler::new());

                let bus = event_bus.clone();
                let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
                let event_loop = tokio::spawn(async move {
                    bus.run(handlers).await;
                });

                tokio::time::sleep(Duration::from_millis(10)).await;

                let start = std::time::Instant::now();

                for _ in 0..event_count {
                    let event = create_test_event(session_id);
                    event_bus.publish_sync(event).unwrap();
                }

                // Wait for processing
                while handler.count() < event_count as u64 {
                    tokio::time::sleep(Duration::from_micros(100)).await;
                }

                total_elapsed += start.elapsed();

                event_bus.shutdown();
                let _ = tokio::time::timeout(Duration::from_secs(1), event_loop).await;
            }

            total_elapsed
        });
    });

    group.finish();
}

/// Quick throughput measurement for README/documentation
fn bench_max_throughput(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let session_id = Uuid::new_v4();

    let mut group = c.benchmark_group("max_throughput");
    group.sample_size(10);
    group.measurement_time(std::time::Duration::from_secs(5));
    group.throughput(Throughput::Elements(10000));

    group.bench_function("10k_events", |b| {
        b.to_async(&rt).iter_custom(|iters| async move {
            let event_count = 10000;
            let mut total_elapsed = std::time::Duration::ZERO;

            for _ in 0..iters {
                let event_bus = Arc::new(EventBus::new());
                let handler = Arc::new(BenchHandler::new());

                let bus = event_bus.clone();
                let handlers: Vec<Arc<dyn EventHandler>> = vec![handler.clone()];
                let event_loop = tokio::spawn(async move {
                    bus.run(handlers).await;
                });

                tokio::time::sleep(Duration::from_millis(20)).await;

                let publisher = event_bus.publisher();
                let start = std::time::Instant::now();

                for _ in 0..event_count {
                    let event = create_test_event(session_id);
                    publisher.publish(event).await.unwrap();
                }

                while handler.count() < event_count as u64 {
                    tokio::time::sleep(Duration::from_micros(100)).await;
                }

                total_elapsed += start.elapsed();

                event_bus.shutdown();
                let _ = tokio::time::timeout(Duration::from_secs(2), event_loop).await;
            }

            total_elapsed
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_event_publish_only,
    bench_event_full_flow,
    bench_event_multiple_handlers,
    bench_concurrent_publishers,
    bench_channel_capacity,
    bench_sync_publish,
    bench_max_throughput,
);

criterion_main!(benches);
