# Racing Coach Core - Rust Extension

High-performance telemetry analysis algorithms implemented in Rust with Python bindings via PyO3.

## Prerequisites

### Rust Toolchain

Install Rust via [rustup](https://rustup.rs/):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Verify installation:

```bash
rustc --version  # Should be 1.70+
cargo --version
```

### Python Environment

The project uses `uv` for Python dependency management. Maturin is included as a dependency in `pyproject.toml`.

```bash
cd libs/racing-coach-core
uv sync
```

## Building

### Development Build (Fast, Unoptimized)

```bash
cd libs/racing-coach-core
uv run maturin develop
```

This compiles the Rust code and installs it into the virtual environment as an editable package. Use this during development for faster iteration.

### Release Build (Optimized)

```bash
uv run maturin develop --release
```

Use this when you want to test performance or before running benchmarks.

### Build Wheel Only

```bash
uv run maturin build --release
```

Creates a wheel in `rust/target/wheels/` without installing it.

## Testing

### Rust Unit Tests

Rust tests require Python linkage via PyO3. Use maturin's test command:

```bash
cd libs/racing-coach-core
uv run maturin develop
cargo test --no-default-features  # May have linking issues
```

For reliable Rust testing, run tests through Python after building:

```bash
uv run python -c "
from racing_coach_core._rs import TelemetryFrame, py_extract_lap_metrics
# Test code here
"
```

### Python Integration Tests

After building with `maturin develop`:

```bash
uv run pytest tests/
```

### Verify Rust Extension is Loaded

```python
from racing_coach_core.rust_ext import is_rust_available
print(is_rust_available())  # Should print True
```

## Maturin

[Maturin](https://www.maturin.rs/) is the build tool for Rust/Python hybrid projects. It handles:

- Compiling Rust code to a native extension module
- Creating Python wheels with correct platform tags
- Installing the extension into the virtual environment

### Key Commands

| Command | Description |
|---------|-------------|
| `maturin develop` | Build and install in dev mode (fast) |
| `maturin develop --release` | Build optimized and install |
| `maturin build` | Build wheel only |
| `maturin build --release` | Build optimized wheel |

### Configuration

Maturin is configured in the parent `pyproject.toml`:

```toml
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[tool.maturin]
python-source = "src"
manifest-path = "rust/Cargo.toml"
module-name = "racing_coach_core._rs"
features = ["pyo3/extension-module"]
```

Key settings:
- **python-source**: Python code location (`src/`)
- **manifest-path**: Rust Cargo.toml location
- **module-name**: Import path for the compiled module (`racing_coach_core._rs`)
- **features**: Enables PyO3 extension module compilation

## Module Structure

```
rust/src/
├── lib.rs                  # PyO3 module registration, Python-facing functions
├── types/
│   ├── mod.rs
│   ├── frame.rs            # TelemetryFrame (8 fields)
│   └── config.rs           # AnalysisConfig (thresholds)
├── results/
│   ├── mod.rs
│   ├── braking.rs          # BrakingMetrics (12 fields)
│   ├── corner.rs           # CornerMetrics (14 fields)
│   └── lap.rs              # LapMetrics (aggregate)
├── detection/
│   ├── mod.rs              # EventDetector trait
│   ├── braking.rs          # BrakingDetector, extract_braking_zones()
│   └── corner.rs           # CornerDetector, extract_corners()
├── analysis/
│   ├── mod.rs
│   ├── deceleration.rs     # calculate_deceleration()
│   ├── trail_braking.rs    # detect_trail_braking()
│   └── statistics.rs       # SpeedStatistics accumulator
├── pipeline/
│   ├── mod.rs
│   └── metrics.rs          # extract_lap_metrics() - unified single-pass
└── utils/
    ├── mod.rs
    └── math.rs             # wrap_distance()
```

## Python API

The Rust extension exposes these types and functions to Python:

### Types

```python
from racing_coach_core._rs import (
    TelemetryFrame,    # Input: 8 telemetry fields
    AnalysisConfig,    # Thresholds configuration
    BrakingMetrics,    # Output: 12 braking zone metrics
    CornerMetrics,     # Output: 14 corner metrics
    LapMetrics,        # Output: aggregate lap analysis
)
```

### Functions

```python
from racing_coach_core._rs import (
    py_extract_lap_metrics,    # Full lap analysis (single-pass, best performance)
    py_extract_braking_zones,  # Braking zones only
    py_extract_corners,        # Corners only
    hello_from_rust,           # Integration test
    compute_speed_stats,       # Example numeric function
)
```

### Python Wrapper

For convenience, use the wrapper module which handles Rust-to-Python type conversion and provides fallbacks:

```python
from racing_coach_core.rust_ext import (
    extract_lap_metrics,      # Accepts TelemetrySequence, returns Python dataclasses
    extract_braking_zones,
    extract_corners,
    is_rust_available,
)
```

## Development Workflow

1. **Make Rust changes** in `rust/src/`

2. **Rebuild the extension**:
   ```bash
   uv run maturin develop --release
   ```

3. **Test in Python**:
   ```bash
   uv run python -c "from racing_coach_core._rs import ..."
   ```

4. **Run full test suite**:
   ```bash
   uv run pytest
   ```

### Type Checking

Update the Python type stubs when changing the Rust API:

```
src/racing_coach_core/_rs.pyi
```

### Common Issues

**"Module not found" after changes**: Rebuild with `maturin develop`

**Linking errors in `cargo test`**: PyO3 tests need Python. Use `maturin develop` then test through Python.

**Import errors**: Ensure you're in the correct virtual environment (`uv run` or activate `.venv`)

## Dependencies

### Rust (Cargo.toml)

```toml
[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
```

### Python (pyproject.toml)

```toml
dependencies = ["maturin>=1.10.2"]
```

## Performance

The Rust implementation provides significant speedups for telemetry analysis:

- Single-pass algorithm for combined braking/corner detection
- Cache-friendly data structures (fields ordered by access frequency)
- Zero-copy where possible via PyO3
- Pre-allocated vectors with estimated capacities

Use `maturin develop --release` for benchmarking to get optimized code.
