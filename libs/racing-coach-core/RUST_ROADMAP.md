# Rust Implementation Roadmap

This document outlines the Python functions that should be reimplemented in Rust for performance gains. The functions are listed in priority order based on impact and frequency of execution.

## Quick Start

### Prerequisites
- Rust toolchain: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Maturin: `pip install maturin`

### Build & Test
```bash
cd libs/racing-coach-core

# Development build (faster, unoptimized)
maturin develop

# Test the integration
python -c "from racing_coach_core.rust_ext import hello_from_rust; print(hello_from_rust())"

# Release build (optimized)
maturin develop --release
```

---

## Phase 1: Core Metrics Extraction (HIGH PRIORITY)

These functions run on every lap completion and process 5,400+ telemetry frames.

### 1.1 `_extract_braking_zones()`

**File:** `src/racing_coach_core/algs/metrics.py` (lines 82-147)

**Current Performance:** ~10-20ms per lap

**Why Rewrite:**
- Inner loop runs 100+ times per lap
- Multiple `max()` and `min()` operations per iteration
- Heavy Python object access (`frames[i].brake`, `frames[i].speed`)

**Input/Output:**
```python
# Input
frames: list[TelemetryFrame]  # 5,400+ frames
brake_threshold: float = 0.05
decel_window: int = 5

# Output
list[BrakingMetrics]  # 15-20 braking zones per lap
```

**Key Data Needed per Frame:**
- `brake: float` (0.0-1.0)
- `speed: float` (m/s)
- `lap_distance: float` (0.0-1.0, normalized)
- `steering_angle: float` (degrees)

**Rust Implementation Notes:**
- Accept frames as a list of dicts or a struct
- Use `Vec<BrakingZone>` internally
- Return Python-compatible list of dicts or dataclass instances

---

### 1.2 `_extract_corners()`

**File:** `src/racing_coach_core/algs/metrics.py` (lines 150-254)

**Current Performance:** ~20-30ms per lap

**Why Rewrite:**
- Inner loop runs 3,600+ times per lap (most iterations of any function)
- Multiple `abs()` calls on same values
- Complex state tracking (entry/apex/exit detection)

**Input/Output:**
```python
# Input
frames: list[TelemetryFrame]
steering_threshold: float = 5.0  # degrees
min_corner_frames: int = 10

# Output
list[CornerMetrics]  # 20-25 corners per lap
```

**Key Data Needed per Frame:**
- `steering_angle: float`
- `lateral_acceleration: float` (g-force)
- `speed: float`
- `throttle: float`
- `lap_distance: float`

**Rust Implementation Notes:**
- Pre-compute `abs(steering_angle)` and `abs(lateral_acceleration)` once per frame
- Use state machine enum for corner phase tracking
- Consider returning apex index for visualization

---

### 1.3 `_detect_trail_braking()`

**File:** `src/racing_coach_core/algs/metrics.py` (lines 286-334)

**Current Performance:** ~5-10ms per lap (called 15-20 times)

**Why Rewrite:**
- Nested conditions in tight loop
- Distance wrap-around calculation
- Called once per braking zone

**Input/Output:**
```python
# Input
frames: list[TelemetryFrame]
brake_start_idx: int
brake_end_idx: int
brake_threshold: float = 0.05
steering_threshold: float = 2.0

# Output
TrailBrakingInfo  # has_trail_braking, distance, avg_pressure
```

---

### 1.4 `_calculate_deceleration()`

**File:** `src/racing_coach_core/algs/metrics.py` (lines 257-283)

**Current Performance:** <1ms per call, but called 30-40 times per lap

**Why Rewrite:**
- Simple math but many invocations
- Can be inlined into `_extract_braking_zones()` in Rust

**Input/Output:**
```python
# Input
frames: list[TelemetryFrame]
start_idx: int
end_idx: int

# Output
float  # deceleration in m/s²
```

---

## Phase 2: Unified Single-Pass Algorithm (MEDIUM PRIORITY)

After implementing Phase 1 functions individually, consider a unified algorithm:

### 2.1 `extract_lap_metrics_rs()`

**Concept:** Single pass through all frames, detecting braking zones AND corners simultaneously.

**Benefits:**
- Only iterate frames once instead of 3 times
- Better cache locality
- Eliminates Python function call overhead between phases

**Rust Pseudocode:**
```rust
fn extract_lap_metrics(frames: Vec<TelemetryFrame>) -> LapMetrics {
    let mut braking_zones = Vec::new();
    let mut corners = Vec::new();
    let mut state = State::Neutral;

    for (i, frame) in frames.iter().enumerate() {
        // Braking detection
        if frame.brake > THRESHOLD && state != State::Braking {
            // Start braking zone
        }

        // Corner detection (can overlap with braking)
        if abs(frame.steering_angle) > STEERING_THRESHOLD {
            // Track corner state
        }
    }

    LapMetrics { braking_zones, corners, ... }
}
```

---

## Phase 3: Frame Parsing (LOW PRIORITY)

Only implement if Phase 1-2 show you need more real-time headroom.

### 3.1 `TelemetryFrame.from_irsdk()`

**File:** `src/racing_coach_core/models/telemetry.py` (lines 102-208)

**Current Performance:** 1-2ms per frame × 60 fps = 60-120ms/s overhead

**Why Consider:**
- Creates nested dicts for tire temps (12 values), tire wear (12 values), brake pressures (4 values)
- Pydantic validation adds overhead
- Called 216,000 times per hour in live mode

**Caveats:**
- Currently within frame budget (~5-10ms of 16.67ms)
- Would require careful API design to return Pydantic-compatible data

---

## Data Structures Reference

### TelemetryFrame (Key Fields)

```python
@dataclass
class TelemetryFrame:
    timestamp: datetime
    session_time: float
    lap_number: int
    lap_distance: float      # 0.0-1.0 normalized

    # Motion
    speed: float             # m/s
    rpm: float
    gear: int

    # Inputs
    throttle: float          # 0.0-1.0
    brake: float             # 0.0-1.0
    steering_angle: float    # degrees

    # Accelerations
    lateral_acceleration: float   # g
    longitudinal_acceleration: float  # g
    vertical_acceleration: float  # g

    # Nested (consider flattening for Rust)
    tire_temps: dict[str, dict[str, float]]  # {"LF": {"L": 80.0, "M": 85.0, "R": 82.0}, ...}
    tire_wear: dict[str, dict[str, float]]
    brake_line_pressure: dict[str, float]    # {"LF": 1500.0, ...}
```

### BrakingMetrics (Output)

```python
@dataclass
class BrakingMetrics:
    zone_number: int
    start_distance: float
    end_distance: float
    entry_speed: float
    min_speed: float
    max_brake_pressure: float
    initial_deceleration: float
    average_deceleration: float
    braking_efficiency: float
    has_trail_braking: bool
    trail_brake_distance: float | None
```

### CornerMetrics (Output)

```python
@dataclass
class CornerMetrics:
    corner_number: int
    entry_distance: float
    apex_distance: float
    exit_distance: float
    entry_speed: float
    apex_speed: float
    exit_speed: float
    min_speed: float
    max_lateral_g: float
    throttle_application_distance: float
    apex_steering_angle: float
    is_left_turn: bool
```

---

## Benchmarking

Add benchmarks to track improvements:

```python
# tests/benchmarks/test_metrics_benchmark.py
import time
from racing_coach_core.algs.metrics import extract_lap_metrics
from racing_coach_core.rust_ext import extract_lap_metrics_rs  # Rust version

def benchmark_metrics_extraction(lap_data):
    # Python version
    start = time.perf_counter()
    for _ in range(100):
        extract_lap_metrics(lap_data)
    python_time = (time.perf_counter() - start) / 100

    # Rust version
    start = time.perf_counter()
    for _ in range(100):
        extract_lap_metrics_rs(lap_data)
    rust_time = (time.perf_counter() - start) / 100

    print(f"Python: {python_time*1000:.2f}ms")
    print(f"Rust:   {rust_time*1000:.2f}ms")
    print(f"Speedup: {python_time/rust_time:.1f}x")
```

---

## Resources

- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin Documentation](https://www.maturin.rs/)
- [PyO3 Performance Tips](https://pyo3.rs/v0.23.0/performance)
- [Rust + Python: A Match Made in Data Science Heaven](https://blog.jetbrains.com/pycharm/2024/04/rust-and-python/)
