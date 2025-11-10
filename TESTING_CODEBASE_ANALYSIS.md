# Racing Coach: Codebase Testing Analysis

This document provides a detailed analysis of the Racing Coach codebase from a testing perspective. It documents all architectural patterns, external service integrations, and data flow mechanisms that impact testing strategy.

## Executive Summary

Racing Coach is a monorepo-based telemetry collection system with:
- **Zero existing tests** (critical gap)
- **Thread-safe event bus** with async/concurrent execution
- **Pluggable telemetry sources** (Live iRacing SDK and IBT file replay)
- **FastAPI REST API** with PostgreSQL backend
- **Pydantic-based data validation** throughout
- **No authentication/authorization** (all endpoints public)
- **Type-safe architecture** with comprehensive type hints

---

## 1. Architecture Overview

### Monorepo Structure

```
racing-coach/
├── libs/
│   └── racing-coach-core/          # Shared library
├── apps/
│   ├── racing-coach-client/        # Telemetry collector
│   └── racing-coach-server/        # FastAPI backend
├── pants.toml                       # Build system
├── docker-compose.yaml              # Database stack
└── justfile                         # Development commands
```

### Component Interaction Flow

```
iRacing Instance (or IBT File)
    ↓ [pyirsdk]
TelemetryCollector (client)
    ├─ LiveTelemetrySource OR ReplayTelemetrySource
    └─ publishes TELEMETRY_FRAME events
        ↓ [EventBus]
    LapHandler (accumulates frames)
        └─ publishes LAP_TELEMETRY_SEQUENCE event
            ↓ [EventBus]
        LapUploadHandler (HTTP POST)
            ↓ [requests]
        FastAPI Server
            ├─ /telemetry/lap endpoint
            ├─ /health endpoint
            └─ /sessions/latest endpoint
                ↓ [SQLAlchemy + psycopg2]
            PostgreSQL Database
                ├─ TrackSession table
                ├─ Lap table
                └─ Telemetry table (95+ columns)
```

---

## 2. Threading & Concurrency Model

### Multi-Threaded Architecture

The client uses a sophisticated multi-threaded design:

```
Main Thread (app.py)
    ├── Starts EventBus
    │   └── EventBus Thread (asyncio event loop)
    │       ├── Maintains asyncio queue
    │       ├── Processes events asynchronously
    │       └── Delegates handlers to ThreadPoolExecutor
    │
    ├── Starts TelemetryCollector
    │   └── Collection Thread (blocking I/O)
    │       ├── Reads from iRacing SDK OR IBT file
    │       ├── Maintains 60 Hz collection rate
    │       └── Publishes events via thread_safe_publish()
    │
    └── Main Loop (wait for Ctrl+C, then graceful shutdown)
        └── EventBus.stop() → waits for event queue to drain
```

### EventBus Design

**File:** `libs/racing-coach-core/src/racing_coach_core/events/base.py`

Key characteristics:
- **Async Queue-Based**: Uses `asyncio.Queue` (max size: 1000, configurable)
- **Thread-Safe Publishing**: `thread_safe_publish()` for sync contexts
- **Async Publishing**: `await publish()` for async contexts
- **Handler Execution**: Runs in `ThreadPoolExecutor` (default: CPU count)
- **Exception Isolation**: Uses `asyncio.gather(..., return_exceptions=True)` to prevent single handler failure from crashing the bus
- **Graceful Shutdown**: Waits for queue to drain before exiting

**Testing Implications:**
- Must test event ordering and concurrent handler execution
- Must verify queue doesn't overflow during high-frequency telemetry (60 Hz)
- Must test shutdown gracefully drains pending events
- Exception handling in handlers must not leak

### Data Collection Loop

**File:** `apps/racing-coach-client/src/racing_coach_client/collectors/iracing.py`

```python
def _collection_loop(self):
    """Blocking loop for telemetry reading (60 Hz)."""
    while self._running:
        # Approximately 16.67 ms per iteration for 60 Hz
        telemetry_frame = self.collect_telemetry_frame()
        session_frame = self.get_session_frame()

        # Publish event (non-blocking via thread_safe_publish)
        self.event_bus.thread_safe_publish(
            Event(
                type=SystemEvents.TELEMETRY_FRAME,
                data=TelemetryAndSession(
                    TelemetryFrame=telemetry_frame,
                    SessionFrame=session_frame
                ),
                timestamp=datetime.now()
            )
        )
```

**Testing Implications:**
- Mock telemetry source to simulate iRacing data
- Verify events are published at ~60 Hz
- Test behavior when collection thread is interrupted
- Verify no data loss between collection and event bus

---

## 3. Telemetry Source Abstraction

### Protocol-Based Design

**File:** `apps/racing-coach-client/src/racing_coach_client/collectors/sources/base.py`

```python
@runtime_checkable
class TelemetrySource(Protocol):
    """Both Live and Replay sources implement this protocol."""

    def startup() -> bool: ...
    def shutdown() -> None: ...
    def is_connected() -> bool: ...
    def freeze_var_buffer_latest() -> None: ...
    def __getitem__(key: str) -> Any: ...
```

This enables:
- **Easy mocking** for tests without iRacing SDK
- **Multiple implementations** (Live and Replay already exist)
- **Custom test sources** (e.g., pre-recorded data playback)

### Live Telemetry Source

**File:** `apps/racing-coach-client/src/racing_coach_client/collectors/sources/live.py`

- Connects to running iRacing instance via `pyirsdk.IRSDK()`
- Reads 95+ telemetry variables per frame
- Auto-reconnects on disconnect
- Raises `TelemetrySourceError` on failures

**Testing Challenges:**
- Requires iRacing to be running (Windows-only)
- Hard to simulate corner cases (connection loss, etc.)
- Solution: Mock the IRSDK instance or use ReplayTelemetrySource

### Replay Telemetry Source

**File:** `apps/racing-coach-client/src/racing_coach_client/collectors/sources/replay.py`

- Reads IBT (iRacing telemetry) files
- Supports configurable playback speed (1.0x = real-time)
- Supports optional looping
- Caches frame variables for consistent reads

**Testing Advantages:**
- No external dependencies (files are static)
- Deterministic behavior (same file = same data)
- Can test at various playback speeds
- Can test end-of-file handling

**Testing Implementation:**
- Create fixture IBT files or use real IBT samples
- Test playback speed variations
- Test frame advancement and variable caching

---

## 4. Event Handling System

### Event Flow

```
EventBus
├── Stores registered handlers in dict[EventType, list[Handler]]
├── Receives event via publish() or thread_safe_publish()
├── Queues event in asyncio.Queue
└── Background loop:
    ├── Dequeues event
    ├── Looks up handlers for event.type
    ├── Creates HandlerContext
    └── Concurrently executes all handlers via ThreadPoolExecutor
```

### Handler Decorator (Zero Overhead)

**File:** `libs/racing-coach-core/src/racing_coach_core/events/checking.py`

```python
@handler_for[TelemetryAndSession](SystemEvents.TELEMETRY_FRAME)
def my_handler(context: HandlerContext[TelemetryAndSession]) -> None:
    # Handler implementation
    pass
```

**Current Status:** Decorator is currently a no-op (metadata generation commented out)

### Handlers in Racing Coach

```
Client Handlers:
├── LapHandler (lap_handler.py)
│   └── on_telemetry_frame() -> aggregates frames
│       └── publishes LAP_TELEMETRY_SEQUENCE when lap complete
│
└── LapUploadHandler (lap_upload_handler.py)
    └── on_lap_telemetry_sequence() -> uploads to server
        └── Makes blocking HTTP request
            └── Publishes success/failure event

Server: No event handlers (synchronous request/response model)
```

**Testing Implications:**
- Test handler ordering (lap aggregation → upload)
- Test handler exception isolation
- Verify handlers execute concurrently where applicable
- Mock EventBus for unit testing handlers in isolation

---

## 5. Client-Server Communication

### REST API Endpoints

**File:** `apps/racing-coach-server/src/racing_coach_server/api/router.py`

#### POST /telemetry/lap
- **Purpose**: Upload completed lap with telemetry frames
- **Request Body**:
  ```json
  {
    "lap": {
      "frames": [TelemetryFrame...],
      "lap_time": float | null
    },
    "session": SessionFrame
  }
  ```
- **Response (200)**:
  ```json
  {
    "status": "success",
    "message": "Received lap {lap_number} with {frame_count} frames",
    "lap_id": "uuid-string"
  }
  ```
- **Error (500)**: Generic server error response
- **No Authentication**: Endpoint is public

#### GET /health
- **Purpose**: Health check
- **Response**:
  ```json
  {
    "status": "ok",
    "message": "Racing Coach Server is running."
  }
  ```

#### GET /sessions/latest
- **Purpose**: Retrieve latest session metadata
- **Response**: SessionFrame object
- **Error (404)**: "No sessions found."

### HTTP Client SDK

**File:** `libs/racing-coach-core/src/racing_coach_core/client/client.py`

```python
class RacingCoachServerSDK:
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.3
    )

    def upload_lap_telemetry(
        lap_telemetry: LapTelemetry,
        session: SessionFrame
    ) -> LapUploadResponse

    def health_check() -> HealthCheckResponse

    def get_latest_session() -> SessionFrame
```

**Features:**
- Automatic retry with exponential backoff (429, 5xx errors)
- Configurable timeout and max retries
- Custom exception hierarchy: `RacingCoachClientError`, `RequestError`, `ServerError`
- Context manager support for proper resource cleanup

**Testing Implications:**
- Mock HTTP responses using `requests_mock` or `responses` library
- Test retry behavior and exponential backoff
- Test error handling for various HTTP status codes
- Test timeout behavior
- Test serialization/deserialization of Pydantic models

---

## 6. Database Architecture

### Connection Configuration

**File:** `apps/racing-coach-server/src/racing_coach_server/config.py`

```python
DB_CONNECTION_STR = (
    "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
)
```

Default uses:
- `psycopg2`: PostgreSQL adapter
- localhost:5432
- Database name: `postgres`
- Default credentials (⚠️ security risk in production)

### SQLAlchemy ORM Models

**File:** `apps/racing-coach-server/src/racing_coach_server/database/models.py`

#### TrackSession
- **Columns**: track_id, track_name, track_config_name, track_type, car_id, car_name, car_class_id, series_id, created_at, updated_at
- **Primary Key**: id (UUID)
- **Relationships**: One-to-Many with Lap, One-to-Many with Telemetry
- **Indexes**: track_id, car_id, (track_id, car_id)
- **Methods**: `to_session_frame()` → SessionFrame

#### Lap
- **Columns**: lap_number, lap_time, is_valid, created_at, updated_at
- **Primary Key**: id (UUID)
- **Foreign Key**: track_session_id (cascading delete)
- **Relationships**: Many-to-One with TrackSession, One-to-Many with Telemetry
- **Unique Constraint**: (track_session_id, lap_number)
- **Indexes**: (track_session_id, lap_number)

#### Telemetry
- **Columns**: 95+ fields including:
  - Timing: timestamp, session_time, lap_number
  - Vehicle State: speed, rpm, gear
  - Driver Inputs: throttle, brake, clutch, steering_angle
  - Dynamics: lateral/longitudinal/vertical acceleration, rates
  - Tires: 4 tires × 3 positions × (temp + wear), brake pressure per wheel
  - Track Conditions: track_temp, track_wetness, air_temp
  - Session: flags, track_surface, on_pit_road
- **Primary Key**: (timestamp, id) - composite for time-series
- **Foreign Keys**: track_session_id, lap_id (both cascading delete)
- **Indexes**: lap_id, track_session_id, timestamp, session_time

### Data Layer Architecture

**Repository Pattern:**

```
TelemetryRepository
├── add_telemetry_frame(frame: TelemetryFrame) -> None
├── get_telemetry_for_lap(lap_id: UUID) -> list[Telemetry]
└── get_telemetry_for_session(session_id: UUID) -> list[Telemetry]

LapRepository
├── add_lap(lap: Lap) -> UUID
├── get_lap(lap_id: UUID) -> Lap
└── get_laps_for_session(session_id: UUID) -> list[Lap]

TrackSessionRepository
├── add_session(session: TrackSession) -> UUID
├── get_session(session_id: UUID) -> TrackSession
└── get_latest_session() -> TrackSession
```

**Service Layer:**

```
TelemetryService
├── add_telemetry_sequence(
    frames: list[TelemetryFrame],
    session_id: UUID,
    lap_id: UUID
  ) -> None

LapService
├── add_lap(
    lap_telemetry: LapTelemetry,
    session_id: UUID
  ) -> UUID

TrackSessionService
├── add_or_get_session(session: SessionFrame) -> UUID
```

### Database Initialization

**File:** `apps/racing-coach-server/src/racing_coach_server/database/init_db.py`

```python
def init_db(engine):
    # 1. Create all SQLAlchemy tables
    Base.metadata.create_all(engine)

    # 2. Convert telemetry table to TimescaleDB hypertable (optional)
    engine.execute(
        "SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE);"
    )
```

**Testing Implications:**
- Need database schema creation for integration tests
- TimescaleDB conversion is optional but improves performance
- Must handle cascading deletes properly
- Need to test unique constraints and indexes

---

## 7. Data Models & Serialization

### Core Pydantic Models

All models use Pydantic v2 with comprehensive type hints.

#### TelemetryFrame
- ~95 fields covering all aspects of vehicle telemetry
- Unit precision (speeds in m/s, angles in radians, etc.)
- Nested dicts for tire data (temps, wear per wheel position)
- Classmethod `from_irsdk()` for source extraction
- Methods: `model_dump(mode='json')` for serialization

#### SessionFrame
- Metadata about racing session (track, car, series)
- UUID for session identification
- Classmethod `from_irsdk()` for extraction

#### LapTelemetry (extends TelemetrySequence)
- Collection of TelemetryFrame objects
- Optional lap_time
- Methods:
  - `to_parquet()` / `from_parquet()` for file I/O
  - `get_lap_time()` → calculated from frame timestamps
  - `is_valid()` → checks track_surface==3 for all frames

#### Response Models
- `HealthCheckResponse`: {status, message}
- `LapUploadResponse`: {status, message, lap_id}

**Testing Implications:**
- Validate all Pydantic models for required/optional fields
- Test serialization roundtrips (JSON ↔ model)
- Test `from_irsdk()` classmethods with mock data
- Verify Parquet file I/O
- Test validation logic (e.g., lap validity checks)

---

## 8. Analysis Algorithms

### Braking Event Detection

**File:** `libs/racing-coach-core/src/racing_coach_core/algs/braking.py`

```python
def extract_braking_events(
    sequence: TelemetrySequence,
    brake_threshold: float = 0.05
) -> list[BrakingEvent]
```

**Algorithm:**
1. Scan brake pedal input
2. When brake > threshold: record event start (distance, frame, speed)
3. Track max brake pressure during event
4. When brake < threshold: record event end
5. Calculate braking duration and minimum speed

**Output:** List of `BrakingEvent` objects with:
- start_distance, entry_speed
- max_pressure, braking_duration
- minimum_speed

### Corner Event Detection

**File:** `libs/racing-coach-core/src/racing_coach_core/algs/cornering.py`

```python
def extract_corner_from_braking(
    sequence: TelemetrySequence,
    brake_event: BrakingEvent | None = None,
    steering_threshold: float = 0.15
) -> list[CornerEvent]
```

**Algorithm:**
1. Identify entry: steering_angle > threshold
2. Identify apex: max lateral_acceleration
3. Identify exit: steering_angle < threshold
4. Record distances for each phase

**Output:** List of `CornerEvent` objects with:
- entry_distance, apex_distance, exit_distance

**Testing Implications:**
- Unit test algorithms with synthetic telemetry data
- Test edge cases (sharp vs. gradual corners, multiple rapid turns)
- Validate threshold parameters
- Test on real IBT files if available

---

## 9. Configuration & Environment Management

### Client Configuration

**File:** `apps/racing-coach-client/src/racing_coach_client/config.py`

```python
class Settings(BaseSettings):
    SERVER_URL: str = "http://localhost:8000"
    TELEMETRY_MODE: Literal["live", "replay"] = "replay"
    LAP_COMPLETION_THRESHOLD: float = 95.0
    REPLAY_FILE_PATH: str | None = None
    REPLAY_SPEED: float = 1.0
    REPLAY_LOOP: bool = False
    COLLECTION_RATE_HZ: int = 60
```

Uses Pydantic-settings to read from environment variables.

### Server Configuration

**File:** `apps/racing-coach-server/src/racing_coach_server/config.py`

```python
class Settings(BaseSettings):
    DB_CONNECTION_STR: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
    )
```

**Testing Implications:**
- Override settings via environment variables
- Test both "live" and "replay" modes
- Verify configuration validation

---

## 10. External Service Dependencies

### iRacing SDK (pyirsdk)

- **Type**: External service (local process)
- **Platform**: Windows-only
- **Access Pattern**: Read telemetry variables via protocol
- **Failure Modes**:
  - iRacing not running
  - Connection lost during session
  - Variable read failures
- **Testing Strategy**: Mock using ReplayTelemetrySource or custom test source

### PostgreSQL Database

- **Type**: External database service
- **Connection**: TCP/IP via psycopg2
- **Initialization**: SQLAlchemy creates tables
- **Failure Modes**:
  - Connection refused
  - Connection timeout
  - Schema mismatch
  - Data integrity violations
- **Testing Strategy**: Use testcontainers to spin up PostgreSQL for integration tests

### Docker Compose Stack

**File:** `docker-compose.yaml`

```yaml
services:
  postgres:
    image: timescaledb/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

Provides TimescaleDB for time-series optimization (optional).

---

## 11. Current Testing Status

### ❌ Missing Test Infrastructure

- **No test files**: Zero `test_*.py` files in codebase
- **No test dependencies**: pytest not in pyproject.toml
- **No test configuration**: No pytest.ini, tox.ini, conftest.py
- **No fixtures**: No shared test data or mocks
- **No CI/CD tests**: No GitHub Actions or similar

### ✅ Code Quality Setup

- **Type checking**: basedpyright with strict mode
- **Linting**: ruff configured
- **Import sorting**: isort configured

**Implication:** Code quality checks are automated, but functional correctness is untested.

---

## 12. Security Considerations

### ❌ No Authentication/Authorization

- All API endpoints are public (no auth required)
- No API key validation
- No JWT tokens
- No user/session isolation

### ⚠️ Configuration Risks

- Default database credentials in code
- HTTP (not HTTPS) by default
- Credentials not loaded from secrets manager

### ✅ Data Validation

- Pydantic validates all model schemas
- SQLAlchemy prevents SQL injection (uses parameterized queries)

### Testing Implications for Security

- No authentication tests needed (currently)
- Should verify no authentication credentials are hardcoded
- Should test input validation via Pydantic models
- Consider adding authentication in future (requires test updates)

---

## 13. Summary: Testing Priorities

### High Priority (Critical Gaps)

| Component | Type | Why Important |
|-----------|------|---------------|
| EventBus | Unit + Integration | Core threading model, critical for data flow |
| TelemetryCollector | Integration | Orchestrates collection, publishes events |
| LapHandler | Unit | Lap aggregation logic, state management |
| HTTP Client (SDK) | Unit | Serialization, retry logic, error handling |
| FastAPI Endpoints | Integration | Server entry points, DB interactions |
| Database Layer | Integration | Data persistence, schema correctness |
| Telemetry Models | Unit | Data validation, serialization |

### Medium Priority (Important but less critical)

| Component | Type | Why Important |
|-----------|------|---------------|
| Analysis Algorithms | Unit | Lap analysis, correctness of results |
| Configuration | Unit | Settings validation, environment handling |
| Telemetry Sources | Unit | Protocol compliance, mock sources |

### Low Priority (Nice to have)

| Component | Type | Why Important |
|-----------|------|---------------|
| Shutdown/Cleanup | Integration | Graceful shutdown, resource cleanup |
| Error Messages | Unit | User-facing messages, debugging |

---

## 14. Key Architectural Insights for Testing

### ✅ Advantages

1. **Protocol-Based Sources**: TelemetrySource protocol enables easy mocking
2. **Event-Driven**: EventBus decouples components, aids testability
3. **Pydantic Models**: Type-safe, self-documenting, easy to validate
4. **Service Layer**: Separates business logic from FastAPI routes
5. **Type Hints**: Full typing enables static analysis and IDE support
6. **Repository Pattern**: Data access is abstracted and mockable

### ❌ Challenges

1. **Threading Model**: EventBus + collector thread requires careful synchronization testing
2. **60 Hz Collection**: High-frequency data requires performance testing
3. **iRacing SDK Dependency**: Windows-only, hard to test in CI/CD without mocks
4. **No Existing Tests**: Starting from zero, must establish patterns
5. **Async/Sync Mixing**: EventBus runs async, handlers run sync in thread pool

---

## 15. Test Infrastructure Requirements

### Tools Needed

- **pytest**: Test runner and framework
- **pytest-asyncio**: Async test support for EventBus
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Fixture-based mocking
- **pydantic-factories**: Generate test data for Pydantic models
- **factory-boy**: ORM fixture generation (for database models)
- **pytest-factoryboy**: Pytest integration for factory-boy
- **testcontainers**: Docker containers for PostgreSQL
- **requests-mock** or **responses**: Mock HTTP responses
- **httpx**: Async HTTP client (FastAPI's TestClient uses it)

### Files to Create

- `tests/conftest.py`: Shared fixtures, database setup
- `tests/unit/`: Unit tests for models, algorithms, logic
- `tests/integration/`: Integration tests for API, database
- `tests/fixtures/`: Test data, factories, mock sources
- `tests/e2e/`: End-to-end tests (client → server → database)

---

## 16. Database Testing Strategy

### Unit Tests (fast, isolated)
- Test Pydantic models (TelemetryFrame, SessionFrame, LapTelemetry)
- Test model validation
- Test serialization/deserialization

### Integration Tests (with real database)
- Use testcontainers to spin up PostgreSQL
- Test repository CRUD operations
- Test service logic with database
- Test schema creation and migrations
- Test indexes and constraints
- Test cascading deletes

### Fixtures Needed
- Valid TelemetryFrame instance
- Valid SessionFrame instance
- Valid LapTelemetry (sequence of frames)
- TrackSession ORM instance
- Lap ORM instance
- Telemetry ORM instance

---

## 17. Event Bus Testing Strategy

### Unit Tests
- Test handler registration and lookup
- Test event publishing (sync and async paths)
- Test handler invocation
- Test exception isolation (one handler failure doesn't crash bus)

### Integration Tests
- Test full event flow (publish → queue → handler execution)
- Test concurrent event processing
- Test queue overflow behavior (max_size=1000)
- Test shutdown gracefully drains queue
- Test threading model (collector thread → EventBus thread → handler thread pool)

### Stress Tests
- Test 60 Hz event rate over extended period
- Test queue behavior under high load
- Test memory stability

---

## 18. API Testing Strategy

### Unit Tests
- Test endpoint parameter validation
- Test response model serialization
- Test error response formats

### Integration Tests
- Test full request/response cycle with real database
- Test status codes (200, 404, 500)
- Test POST /telemetry/lap with various frame counts
- Test GET /sessions/latest when no sessions exist
- Test cascading behavior (delete session → deletes laps → deletes telemetry)

### Fixtures Needed
- FastAPI TestClient
- Pre-populated database with sample data
- Override settings (test DB connection string)

---

## 19. Client Testing Strategy

### Unit Tests
- Test LapHandler lap aggregation logic
- Test LapUploadHandler upload serialization
- Test error handling in handlers

### Integration Tests
- Test TelemetryCollector with ReplayTelemetrySource
- Test full collection → event publishing → handler execution flow
- Test lap detection threshold (95% of lap distance)
- Test graceful shutdown

### Fixtures Needed
- Sample IBT file (or create synthetic replay source)
- Mock EventBus or real EventBus
- Mock HTTP server (for testing uploads)

