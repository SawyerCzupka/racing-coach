# Racing Coach: Testing Recommendations

This document provides a comprehensive testing strategy for the Racing Coach project, synthesizing codebase analysis with industry best practices for Python testing frameworks.

## Executive Summary

**Recommended Tech Stack:**

| Category | Tool | Rationale |
|----------|------|-----------|
| **Test Runner** | pytest | Industry standard, excellent plugin ecosystem |
| **Async Testing** | pytest-asyncio | Essential for EventBus async/sync threading |
| **Coverage** | pytest-cov | Built-in coverage reporting |
| **Fixtures** | pytest-factoryboy + pydantic-factories | Type-safe test data generation |
| **DB Testing** | testcontainers + SQLAlchemy sessionmaker | Real PostgreSQL without container overhead |
| **HTTP Mocking** | responses or requests-mock | Mock external API calls |
| **Code Quality** | Keep existing (ruff, basedpyright) | Already configured, working well |

---

## 1. Recommended Test Stack

### Core Testing Framework

#### pytest
- **Why**: Industry standard, vast ecosystem, excellent for both sync and async tests
- **Version**: Latest (5.x+)
- **Key Benefits**:
  - Built-in assertion introspection
  - Powerful fixture system (conftest.py)
  - Excellent plugin ecosystem
  - Good IDE integration
  - Simple syntax: `test_*.py` and `def test_*()` conventions
- **Setup**: Already familiar to you, minimal learning curve

### Async & Threading Support

#### pytest-asyncio
- **Why**: Essential for testing the EventBus threading model
- **Key Features**:
  - `@pytest.mark.asyncio` decorator for async tests
  - Automatic event loop management per test
  - Prevents event loop closure issues between tests
  - Handles both sync and async test functions
- **Racing Coach Usage**:
  ```python
  @pytest.mark.asyncio
  async def test_event_bus_publishes_event():
      bus = EventBus()
      bus.start()
      event = Event(type=..., data=..., timestamp=...)
      await bus.publish(event)
      # assertions
      bus.stop()
  ```
- **Configuration** (pyproject.toml):
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"  # Automatically detects and runs async tests
  ```

### Test Data & Fixtures

#### pydantic-factories (Recommended for Pydantic models)
- **Why**: Automatic test data generation for all Pydantic models
- **Key Features**:
  - Generates valid data for all Pydantic field types
  - Supports nested models (like TelemetryFrame with tire_temps dict)
  - Type-aware (knows what values are valid for each field)
  - Minimal configuration needed
- **Racing Coach Usage**:
  ```python
  from pydantic_factories import ModelFactory
  from racing_coach_core.models.telemetry import TelemetryFrame

  class TelemetryFrameFactory(ModelFactory[TelemetryFrame]):
      __model__ = TelemetryFrame

  # In tests:
  frame = TelemetryFrameFactory.create()  # Auto-generates valid frame
  frames = TelemetryFrameFactory.create_batch(100)  # Generate 100 frames
  ```

#### factory-boy + pytest-factoryboy (For SQLAlchemy models)
- **Why**: Industry standard for database ORM fixtures
- **Key Features**:
  - Generates valid ORM instances
  - Relationships are automatically created
  - Integrates seamlessly with pytest via pytest-factoryboy
  - Supports trait-based customization
- **Racing Coach Usage**:
  ```python
  from factory import Factory, Faker
  from racing_coach_server.database.models import TrackSession, Lap

  class TrackSessionFactory(Factory):
      class Meta:
          model = TrackSession

      track_id = 1
      track_name = "Road America"
      car_id = 1234
      car_name = "Ferrari 488 GTE Evo"

  class LapFactory(Factory):
      class Meta:
          model = Lap

      track_session = factory.SubFactory(TrackSessionFactory)
      lap_number = 1
      lap_time = 123.456
      is_valid = True
  ```
- **Integration with pytest**:
  ```python
  def test_lap_handler(lap_factory):
      lap = lap_factory()  # Created automatically from LapFactory
      assert lap.is_valid
  ```

#### testcontainers (For PostgreSQL)
- **Why**: Spin up real PostgreSQL in Docker for integration tests without manual setup
- **Key Features**:
  - Automatic container lifecycle management
  - Works with SQLAlchemy connection URLs
  - Session-scoped or function-scoped
  - No manual Docker commands needed
- **Racing Coach Usage**:
  ```python
  import pytest
  from testcontainers.postgres import PostgresContainer
  from sqlalchemy import create_engine
  from sqlalchemy.orm import Session

  @pytest.fixture(scope="session")
  def postgres_container():
      with PostgresContainer("postgres:16") as postgres:
          yield postgres

  @pytest.fixture(scope="session")
  def db_engine(postgres_container):
      engine = create_engine(postgres_container.get_connection_url())
      Base.metadata.create_all(engine)  # Create schema
      yield engine
      engine.dispose()

  @pytest.fixture
  def db_session(db_engine):
      connection = db_engine.connect()
      transaction = connection.begin()
      session = Session(bind=connection)

      yield session

      session.close()
      transaction.rollback()
      connection.close()
  ```

### HTTP Mocking

**Option A: responses library** (Recommended for simplicity)
- Decorator-based
- Minimal setup
- Good for mocking external APIs
```python
import responses
from racing_coach_core.client.client import RacingCoachServerSDK

@responses.activate
def test_health_check():
    responses.add(
        responses.GET,
        "http://localhost:8000/health",
        json={"status": "ok", "message": "Running"},
        status=200
    )

    sdk = RacingCoachServerSDK("http://localhost:8000")
    response = sdk.health_check()
    assert response.status == "ok"
```

**Option B: requests-mock library** (Context manager style)
- Can use as fixture
- Good for context-specific mocking
```python
def test_upload_with_retry(requests_mock):
    # Mock endpoint
    requests_mock.post(
        "http://localhost:8000/telemetry/lap",
        json={"status": "success", "lap_id": "uuid-1"},
        status=200
    )

    sdk = RacingCoachServerSDK("http://localhost:8000")
    response = sdk.upload_lap_telemetry(lap, session)
    assert response.status == "success"
```

**Use Both:**
- `responses` for simple cases (one-off mocks)
- `requests-mock` for complex scenarios (request assertion, multiple endpoints)

### Code Coverage

#### pytest-cov
- **Why**: Built-in to pytest ecosystem, excellent reporting
- **Usage**:
  ```bash
  pytest --cov=racing_coach_core --cov=racing_coach_client --cov=racing_coach_server
  ```
- **Configuration** (pyproject.toml):
  ```toml
  [tool.coverage.run]
  branch = true
  source = ["racing_coach_core", "racing_coach_client", "racing_coach_server"]

  [tool.coverage.report]
  exclude_lines = [
      "pragma: no cover",
      "def __repr__",
      "raise AssertionError",
      "raise NotImplementedError",
      "if __name__ == .__main__.:"
  ]
  ```

---

## 2. Dependency Installation

### Add to libs/racing-coach-core/pyproject.toml

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "pydantic-factories>=1.31.0",
]
```

### Add to apps/racing-coach-server/pyproject.toml

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "testcontainers>=4.0.0",  # Includes postgres module
    "factory-boy>=3.3.0",
    "pytest-factoryboy>=2.5.0",
    "requests-mock>=1.12.0",
    "httpx>=0.27.0",  # FastAPI's TestClient dependency
]
```

### Add to apps/racing-coach-client/pyproject.toml

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "pydantic-factories>=1.31.0",
    "responses>=0.25.0",
    "pytest-mock>=3.14.0",  # For mocking iRacing SDK
]
```

### Installation Commands

```bash
# Install test dependencies for core library
cd libs/racing-coach-core
uv pip install -e ".[test]"

# Install test dependencies for server
cd apps/racing-coach-server
uv pip install -e ".[test]"

# Install test dependencies for client
cd apps/racing-coach-client
uv pip install -e ".[test]"
```

---

## 3. Directory Structure

```
racing-coach/
├── tests/
│   ├── conftest.py                    # Shared fixtures and configuration
│   │
│   ├── unit/
│   │   ├── conftest.py                # Unit test fixtures
│   │   ├── core/                      # racing-coach-core tests
│   │   │   ├── test_telemetry_frame.py
│   │   │   ├── test_session_frame.py
│   │   │   ├── test_event_bus.py
│   │   │   ├── test_braking_alg.py
│   │   │   └── test_cornering_alg.py
│   │   ├── server/                    # racing-coach-server tests
│   │   │   ├── test_responses.py      # Response models
│   │   │   └── test_config.py
│   │   └── client/                    # racing-coach-client tests
│   │       ├── test_lap_handler.py
│   │       └── test_lap_upload_handler.py
│   │
│   ├── integration/
│   │   ├── conftest.py                # Integration test fixtures (DB, containers)
│   │   ├── server/
│   │   │   ├── test_api_endpoints.py  # FastAPI endpoint tests
│   │   │   ├── test_health_check.py
│   │   │   ├── test_telemetry_upload.py
│   │   │   ├── test_session_retrieval.py
│   │   │   ├── test_db_schema.py      # Schema validation
│   │   │   ├── test_db_constraints.py # Unique, foreign keys
│   │   │   └── test_db_cascades.py    # Cascading deletes
│   │   ├── client/
│   │   │   └── test_client_server.py  # Client → Server integration
│   │   └── core/
│   │       └── test_http_client.py    # RacingCoachServerSDK
│   │
│   ├── e2e/
│   │   ├── conftest.py
│   │   └── test_full_workflow.py      # Client → Server → DB flow
│   │
│   ├── fixtures/
│   │   ├── factories.py               # All factory definitions
│   │   ├── data/
│   │   │   └── sample.ibt             # Sample IBT file (if available)
│   │   └── mocks/
│   │       ├── mock_irsdk.py          # Mock pyirsdk
│   │       └── mock_telemetry_source.py
│   │
│   └── __init__.py

pyproject.toml                          # Root project config (if used)
pytest.ini  or pyproject.toml           # Pytest configuration
```

---

## 4. Essential Fixtures (conftest.py)

### Root Level: tests/conftest.py

```python
import pytest
from datetime import datetime
from uuid import uuid4
from racing_coach_core.models.telemetry import SessionFrame
from racing_coach_core.models.responses import HealthCheckResponse, LapUploadResponse

@pytest.fixture
def sample_session_frame():
    """Standard SessionFrame for all tests."""
    return SessionFrame(
        timestamp=datetime.now(),
        session_id=uuid4(),
        track_id=1,
        track_name="Road America",
        track_config_name=None,
        track_type="road course",
        car_id=1234,
        car_name="Ferrari 488 GTE Evo",
        car_class_id=1,
        series_id=10
    )

@pytest.fixture
def mock_health_check_response():
    """Mock successful health check response."""
    return HealthCheckResponse(
        status="ok",
        message="Racing Coach Server is running."
    )
```

### Server Level: tests/integration/conftest.py

```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from racing_coach_server.database.models import Base

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for entire test session."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Create SQLAlchemy engine connected to test database."""
    engine = create_engine(
        postgres_container.get_connection_url(),
        poolclass=StaticPool,  # Important for test isolation
    )
    Base.metadata.create_all(engine)  # Create schema
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Provide session with transaction rollback for test isolation."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()  # Rollback after test
    connection.close()

@pytest.fixture
def test_client(db_session):
    """Provide FastAPI TestClient with test database."""
    from fastapi.testclient import TestClient
    from racing_coach_server.app import app
    from racing_coach_server.dependencies import get_db_session

    # Override dependency injection to use test database
    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
```

### Client Level: tests/unit/client/conftest.py

```python
import pytest
from unittest.mock import Mock, MagicMock
from racing_coach_client.collectors.sources.base import TelemetrySource

@pytest.fixture
def mock_telemetry_source():
    """Mock TelemetrySource protocol for testing."""
    source = Mock(spec=TelemetrySource)
    source.startup.return_value = True
    source.shutdown.return_value = None
    source.is_connected.return_value = True
    source.freeze_var_buffer_latest.return_value = None
    source.__getitem__.return_value = 0.0  # Default value
    return source
```

---

## 5. Testing Strategy by Component

### 5.1 Unit Tests: Data Models (racing-coach-core)

**File:** `tests/unit/core/test_telemetry_frame.py`

```python
import pytest
from pydantic_factories import ModelFactory
from racing_coach_core.models.telemetry import TelemetryFrame

class TelemetryFrameFactory(ModelFactory[TelemetryFrame]):
    __model__ = TelemetryFrame

class TestTelemetryFrameValidation:
    def test_valid_frame_creation(self):
        """Test that factory creates valid frames."""
        frame = TelemetryFrameFactory.create()
        assert frame.speed >= 0
        assert 0 <= frame.throttle <= 1
        assert isinstance(frame.tire_temps, dict)

    def test_frame_serialization(self):
        """Test JSON serialization for API."""
        frame = TelemetryFrameFactory.create()
        json_data = frame.model_dump(mode="json")
        assert "speed" in json_data
        assert "timestamp" in json_data

    def test_frame_invalid_throttle(self):
        """Test validation of invalid values."""
        with pytest.raises(ValueError):
            TelemetryFrame(
                **TelemetryFrameFactory.build().__dict__,
                throttle=1.5  # Invalid: > 1.0
            )
```

### 5.2 Unit Tests: Event Bus (racing-coach-core)

**File:** `tests/unit/core/test_event_bus.py`

```python
import pytest
from racing_coach_core.events.base import EventBus, Event, EventType, Handler, HandlerContext

@pytest.mark.asyncio
async def test_event_bus_publishes_event():
    """Test basic event publishing."""
    bus = EventBus()
    bus.start()

    received_events = []

    def handler(context: HandlerContext):
        received_events.append(context.event)

    test_event_type = EventType("test", dict)
    bus.subscribe(test_event_type, handler)

    test_event = Event(type=test_event_type, data={}, timestamp=datetime.now())
    bus.thread_safe_publish(test_event)

    # Give time for event to process
    await asyncio.sleep(0.1)
    bus.stop()

    assert len(received_events) == 1
    assert received_events[0] == test_event

@pytest.mark.asyncio
async def test_event_bus_exception_isolation():
    """Test that one handler exception doesn't crash others."""
    bus = EventBus()
    bus.start()

    successful_handlers = []

    def failing_handler(context: HandlerContext):
        raise ValueError("Handler error")

    def successful_handler(context: HandlerContext):
        successful_handlers.append(context.event)

    test_event_type = EventType("test", dict)
    bus.subscribe(test_event_type, failing_handler)
    bus.subscribe(test_event_type, successful_handler)

    test_event = Event(type=test_event_type, data={}, timestamp=datetime.now())
    bus.thread_safe_publish(test_event)

    await asyncio.sleep(0.1)
    bus.stop()

    # Successful handler should still execute despite failure
    assert len(successful_handlers) == 1
```

### 5.3 Unit Tests: Analysis Algorithms (racing-coach-core)

**File:** `tests/unit/core/test_braking_alg.py`

```python
import pytest
from pydantic_factories import ModelFactory
from racing_coach_core.models.telemetry import TelemetryFrame, LapTelemetry
from racing_coach_core.algs.braking import extract_braking_events

class TelemetrySequenceFactory(ModelFactory[TelemetryFrame]):
    __model__ = TelemetryFrame

def test_extract_braking_events_single_brake():
    """Test braking event detection."""
    frames = []

    # No braking
    for i in range(10):
        frame = TelemetrySequenceFactory.create(brake=0.0)
        frames.append(frame)

    # Braking event
    for i in range(5):
        frame = TelemetrySequenceFactory.create(brake=0.8, speed=100 - i*5)
        frames.append(frame)

    # No braking
    for i in range(10):
        frame = TelemetrySequenceFactory.create(brake=0.0)
        frames.append(frame)

    lap = LapTelemetry(frames=frames, lap_time=30.0)
    events = extract_braking_events(lap)

    assert len(events) == 1
    assert events[0].max_pressure == 0.8
```

### 5.4 Unit Tests: HTTP Client (racing-coach-core)

**File:** `tests/unit/core/test_http_client.py`

```python
import pytest
import responses
from racing_coach_core.client.client import RacingCoachServerSDK

@responses.activate
def test_health_check():
    """Test health check endpoint."""
    responses.add(
        responses.GET,
        "http://localhost:8000/health",
        json={"status": "ok", "message": "Running"},
        status=200
    )

    sdk = RacingCoachServerSDK("http://localhost:8000")
    response = sdk.health_check()

    assert response.status == "ok"

@responses.activate
def test_retry_on_server_error():
    """Test retry behavior on 500 errors."""
    responses.add(
        responses.GET,
        "http://localhost:8000/health",
        json={"error": "Server error"},
        status=500
    )
    # Second attempt succeeds
    responses.add(
        responses.GET,
        "http://localhost:8000/health",
        json={"status": "ok"},
        status=200
    )

    sdk = RacingCoachServerSDK("http://localhost:8000", max_retries=3)
    response = sdk.health_check()

    # Should succeed on retry
    assert response.status == "ok"
```

### 5.5 Unit Tests: Event Handlers (racing-coach-client)

**File:** `tests/unit/client/test_lap_handler.py`

```python
import pytest
from pydantic_factories import ModelFactory
from racing_coach_client.handlers.lap_handler import LapHandler
from racing_coach_core.models.telemetry import TelemetryFrame

class MockEventBus:
    def __init__(self):
        self.published_events = []

    def thread_safe_publish(self, event):
        self.published_events.append(event)

def test_lap_handler_accumulates_frames():
    """Test that handler accumulates frames and detects lap completion."""
    mock_bus = MockEventBus()
    handler = LapHandler(mock_bus, lap_completion_threshold=95.0)

    # Generate 100 frames at 0-99% lap distance
    for i in range(100):
        frame = TelemetryFrameFactory.create(
            lap_distance_pct=i,
            track_surface=3  # On-track
        )
        # Simulate handler receiving event
        handler.handle_telemetry_frame(...)

    # Should detect lap completion at 95%
    lap_events = [e for e in mock_bus.published_events
                  if "LAP_TELEMETRY" in str(e.type)]
    assert len(lap_events) > 0
```

### 5.6 Integration Tests: FastAPI Endpoints (racing-coach-server)

**File:** `tests/integration/server/test_api_endpoints.py`

```python
import pytest
from uuid import uuid4
from racing_coach_core.models.telemetry import SessionFrame, TelemetryFrame, LapTelemetry
from pydantic_factories import ModelFactory

class TestHealthEndpoint:
    def test_health_check(self, test_client):
        """Test /health endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestTelemetryUploadEndpoint:
    def test_upload_lap(self, test_client, sample_session_frame):
        """Test successful lap upload."""
        frames = TelemetryFrameFactory.create_batch(100)
        lap = LapTelemetry(frames=frames, lap_time=123.456)

        response = test_client.post(
            "/telemetry/lap",
            json={
                "lap": lap.model_dump(mode="json"),
                "session": sample_session_frame.model_dump(mode="json")
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "lap_id" in response.json()

    def test_upload_creates_session(self, test_client, sample_session_frame):
        """Test that upload creates TrackSession if it doesn't exist."""
        frames = TelemetryFrameFactory.create_batch(50)
        lap = LapTelemetry(frames=frames, lap_time=125.0)

        response = test_client.post(
            "/telemetry/lap",
            json={
                "lap": lap.model_dump(mode="json"),
                "session": sample_session_frame.model_dump(mode="json")
            }
        )

        assert response.status_code == 200

        # Verify session was created
        latest = test_client.get("/sessions/latest")
        assert latest.status_code == 200
        assert latest.json()["track_id"] == sample_session_frame.track_id

class TestLatestSessionEndpoint:
    def test_get_latest_session_not_found(self, test_client):
        """Test /sessions/latest returns 404 when no sessions."""
        response = test_client.get("/sessions/latest")

        assert response.status_code == 404
        assert "No sessions found" in response.json()["detail"]
```

### 5.7 Integration Tests: Database (racing-coach-server)

**File:** `tests/integration/server/test_db_schema.py`

```python
import pytest
from sqlalchemy import inspect
from racing_coach_server.database.models import Base, TrackSession, Lap, Telemetry

class TestDatabaseSchema:
    def test_tables_created(self, db_engine):
        """Verify all tables were created."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "track_session" in tables
        assert "lap" in tables
        assert "telemetry" in tables

    def test_telemetry_columns(self, db_engine):
        """Verify telemetry table has expected columns."""
        inspector = inspect(db_engine)
        columns = [c["name"] for c in inspector.get_columns("telemetry")]

        assert "speed" in columns
        assert "brake" in columns
        assert "throttle" in columns
        assert "steering_angle" in columns
        # ... check all 95+ columns

    def test_unique_constraints(self, db_engine):
        """Verify unique constraints."""
        inspector = inspect(db_engine)
        constraints = inspector.get_unique_constraints("lap")

        # Lap(track_session_id, lap_number) must be unique
        constraint_cols = [c for c in constraints
                          if set(c) == {"track_session_id", "lap_number"}]
        assert len(constraint_cols) > 0

    def test_foreign_keys(self, db_engine):
        """Verify foreign key relationships."""
        inspector = inspect(db_engine)

        # Lap.track_session_id → TrackSession.id
        fks = inspector.get_foreign_keys("lap")
        lap_to_session = [fk for fk in fks
                         if fk["referred_table"] == "track_session"]
        assert len(lap_to_session) > 0
```

### 5.8 Integration Tests: Database Operations (racing-coach-server)

**File:** `tests/integration/server/test_db_operations.py`

```python
import pytest
from uuid import uuid4
from racing_coach_server.database.services.track_session import TrackSessionService
from racing_coach_core.models.telemetry import SessionFrame

class TestTrackSessionService:
    def test_add_or_get_session_creates_new(self, db_session):
        """Test creating new session."""
        service = TrackSessionService(db_session)
        session_frame = SessionFrame(
            timestamp=datetime.now(),
            session_id=uuid4(),
            track_id=1,
            track_name="Road America",
            car_id=1234,
            car_name="Ferrari",
            car_class_id=1,
            series_id=10
        )

        session_id = service.add_or_get_session(session_frame)

        assert session_id is not None
        session = db_session.query(TrackSession).filter_by(id=session_id).first()
        assert session.track_name == "Road America"

    def test_add_or_get_session_returns_existing(self, db_session):
        """Test retrieving existing session."""
        service = TrackSessionService(db_session)
        session_frame = SessionFrame(...)

        session_id_1 = service.add_or_get_session(session_frame)
        session_id_2 = service.add_or_get_session(session_frame)

        # Should return same ID
        assert session_id_1 == session_id_2
```

### 5.9 Integration Tests: Client-Server (racing-coach-client)

**File:** `tests/integration/client/test_client_server.py`

```python
import pytest
from unittest.mock import patch
from racing_coach_client.handlers.lap_upload_handler import LapUploadHandler
from racing_coach_core.models.telemetry import LapTelemetry

@responses.activate
def test_lap_upload_handler_uploads_to_server(mock_event_bus, sample_session_frame):
    """Test that handler successfully uploads lap to server."""
    # Mock server endpoint
    responses.add(
        responses.POST,
        "http://localhost:8000/telemetry/lap",
        json={"status": "success", "lap_id": "lap-123"},
        status=200
    )

    handler = LapUploadHandler(
        mock_event_bus,
        "http://localhost:8000"
    )

    frames = TelemetryFrameFactory.create_batch(50)
    lap = LapTelemetry(frames=frames, lap_time=120.0)

    # Handler should upload and succeed
    handler.handle_lap_telemetry(lap, sample_session_frame)

    # Verify HTTP call was made
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "http://localhost:8000/telemetry/lap"
```

### 5.10 End-to-End Tests

**File:** `tests/e2e/test_full_workflow.py`

```python
import pytest
import asyncio
from unittest.mock import Mock
from racing_coach_client.collectors.sources.replay import ReplayTelemetrySource
from racing_coach_client.collectors.iracing import TelemetryCollector
from racing_coach_core.events.base import EventBus

@pytest.mark.asyncio
async def test_full_collection_flow(test_client, sample_ibt_file):
    """Test: Collect telemetry → detect lap → upload to server."""

    # 1. Set up replay source with IBT file
    replay_source = ReplayTelemetrySource(
        file_path=sample_ibt_file,
        speed_multiplier=10.0,  # 10x speed for fast test
        loop=False
    )

    # 2. Create event bus and collector
    event_bus = EventBus()
    event_bus.start()

    collector = TelemetryCollector(
        source=replay_source,
        event_bus=event_bus
    )

    # 3. Register handlers that will upload to test server
    from racing_coach_client.handlers.lap_handler import LapHandler
    from racing_coach_client.handlers.lap_upload_handler import LapUploadHandler

    lap_handler = LapHandler(event_bus)
    upload_handler = LapUploadHandler(event_bus, "http://localhost:8000")

    # 4. Start collection
    collector.start()

    # 5. Wait for completion
    await asyncio.sleep(5)
    collector.stop()
    event_bus.stop()

    # 6. Verify data reached server
    latest = test_client.get("/sessions/latest")
    assert latest.status_code == 200

    session_data = latest.json()
    assert session_data["track_name"] is not None
```

---

## 6. Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (slower, requires Docker)
pytest tests/integration/

# Run specific test file
pytest tests/unit/core/test_telemetry_frame.py

# Run specific test
pytest tests/unit/core/test_telemetry_frame.py::TestTelemetryFrameValidation::test_valid_frame_creation

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=racing_coach_core --cov=racing_coach_client --cov=racing_coach_server

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### PyCharm/IDE Integration

- pytest is auto-discovered by most IDEs
- Right-click test file → Run tests
- Green checkmarks indicate passing tests
- Coverage highlights show tested lines

---

## 7. pytest Configuration

**File:** `pyproject.toml` (add to root or app-specific)

```toml
[tool.pytest.ini_options]
# Test discovery
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Asyncio configuration
asyncio_mode = "auto"

# Output and reporting
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--disable-warnings",  # Reduce noise
]

# Markers for categorizing tests
markers = [
    "unit: Unit tests (fast, no external services)",
    "integration: Integration tests (slower, may use Docker)",
    "e2e: End-to-end tests (slowest, full system)",
    "asyncio: Async test",
    "slow: Slow test (>1 second)",
]

# Ignore deprecation warnings from dependencies
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
branch = true
source = ["racing_coach_core", "racing_coach_client", "racing_coach_server"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

exclude_paths = ["*/tests/*"]
```

---

## 8. Continuous Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e libs/racing-coach-core[test]
        uv pip install -e apps/racing-coach-server[test]
        uv pip install -e apps/racing-coach-client[test]

    - name: Run tests
      run: pytest --cov

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 9. Test Execution Plan

### Phase 1: Foundation (Week 1-2)
1. Set up pytest infrastructure and conftest.py
2. Create factory fixtures for all models
3. Write unit tests for data models (TelemetryFrame, SessionFrame)
4. Write unit tests for algorithms (braking, cornering)

### Phase 2: Core Components (Week 2-3)
1. Write unit tests for EventBus
2. Write unit tests for HTTP client (with mocking)
3. Write unit tests for event handlers
4. Achieve 70%+ coverage for racing-coach-core

### Phase 3: Server Integration (Week 3-4)
1. Set up testcontainers for PostgreSQL
2. Write integration tests for database schema
3. Write integration tests for FastAPI endpoints
4. Write integration tests for CRUD operations
5. Achieve 70%+ coverage for racing-coach-server

### Phase 4: Client & E2E (Week 4-5)
1. Write unit tests for client handlers
2. Write integration tests for client-server communication
3. Create sample IBT file for replay testing
4. Write end-to-end tests
5. Achieve 70%+ coverage for racing-coach-client

### Phase 5: Refinement (Week 5+)
1. Increase coverage targets (80%+)
2. Add stress tests (60 Hz sustained load)
3. Add performance benchmarks
4. Document testing patterns for team

---

## 10. Factory Pattern Best Practices

### Pydantic Factories

```python
from pydantic_factories import ModelFactory
from racing_coach_core.models.telemetry import TelemetryFrame
from datetime import datetime

class TelemetryFrameFactory(ModelFactory[TelemetryFrame]):
    __model__ = TelemetryFrame

    # Override specific fields
    timestamp: datetime = datetime.now()

    # Or use Faker for realistic data
    # from faker import Faker
    # faker = Faker()
    # speed = faker.random.uniform(0, 300)  # Realistic speeds

# Usage:
frame = TelemetryFrameFactory.create()  # Single instance
frames = TelemetryFrameFactory.create_batch(100)  # Multiple

# With overrides:
frame = TelemetryFrameFactory.create(speed=200, brake=0.5)
```

### Factory Boy for ORM Models

```python
import factory
from racing_coach_server.database.models import TrackSession, Lap

class TrackSessionFactory(factory.Factory):
    class Meta:
        model = TrackSession

    id = factory.LazyFunction(uuid4)
    track_id = 1
    track_name = "Road America"
    car_id = 1234
    car_name = "Ferrari 488"

class LapFactory(factory.Factory):
    class Meta:
        model = Lap

    id = factory.LazyFunction(uuid4)
    track_session = factory.SubFactory(TrackSessionFactory)
    lap_number = factory.Sequence(lambda n: n + 1)
    lap_time = 120.5
    is_valid = True

# Usage with pytest-factoryboy:
def test_with_lap(lap_factory):
    lap = lap_factory()  # Auto-fixture
    assert lap.lap_time > 0
```

---

## 11. Common Testing Patterns

### Testing with Database Transactions

```python
def test_lap_creation_rolls_back(db_session):
    """Verify test isolation via rollback."""
    service = LapService(db_session)
    lap_id = service.add_lap(...)

    assert db_session.query(Lap).filter_by(id=lap_id).first() is not None

    # Transaction will rollback after test
```

### Testing Concurrent Event Handlers

```python
@pytest.mark.asyncio
async def test_concurrent_handlers():
    """Test multiple handlers run concurrently."""
    bus = EventBus()
    bus.start()

    execution_times = []

    def slow_handler(context):
        execution_times.append(("slow", time.time()))
        time.sleep(0.1)

    def fast_handler(context):
        execution_times.append(("fast", time.time()))

    event_type = EventType("test", dict)
    bus.subscribe(event_type, slow_handler)
    bus.subscribe(event_type, fast_handler)

    event = Event(type=event_type, data={}, timestamp=datetime.now())
    bus.thread_safe_publish(event)

    await asyncio.sleep(0.2)
    bus.stop()

    # Fast handler started close to slow handler (concurrent)
    time_diff = execution_times[1][1] - execution_times[0][1]
    assert time_diff < 0.05  # Started within 50ms
```

### Testing Fixtures with Dependencies

```python
@pytest.fixture
def populated_database(db_session):
    """Pre-populate database with test data."""
    session = TrackSessionFactory(db_session)
    laps = [LapFactory(db_session, track_session=session) for _ in range(10)]
    db_session.commit()
    return {"session": session, "laps": laps}

def test_with_data(populated_database, db_session):
    """Use pre-populated data."""
    session = populated_database["session"]
    laps = db_session.query(Lap).filter_by(track_session_id=session.id).all()
    assert len(laps) == 10
```

---

## 12. Key Takeaways

### Do's ✅
- **Use pytest-asyncio** for EventBus threading tests
- **Use pydantic-factories** for Pydantic model test data
- **Use testcontainers** for real PostgreSQL testing
- **Use responses/requests-mock** for HTTP mocking
- **Use transaction rollback** for database test isolation
- **Use dependency_overrides** for FastAPI test client
- **Write unit tests first** (fast feedback loop)
- **Then integration tests** (catch real interactions)

### Don'ts ❌
- Don't use in-memory SQLite (different SQL dialect than production)
- Don't forget to rollback transactions after tests (data leaks)
- Don't forget to clean up fastapi.dependency_overrides
- Don't mix unit and integration tests in same file (hard to organize)
- Don't test with real iRacing SDK (use ReplayTelemetrySource mock)
- Don't hardcode test data (use factories for flexibility)
- Don't skip async tests (EventBus is async, must test properly)

### Optional Enhancements
- **pytest-xdist**: Run tests in parallel (`pytest -n auto`)
- **pytest-benchmark**: Performance regression testing
- **hypothesis**: Property-based testing for algorithms
- **stubs**: Type hints for mocked objects (better IDE support)

---

## 13. Recommended Reading

### Core Documentation
- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [testcontainers Python](https://testcontainers.com/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)

### Best Practices
- [pytest with Eric - advanced patterns](https://pytest-with-eric.com/)
- [TestDriven.io - FastAPI testing](https://testdriven.io/blog/fastapi-crud/)
- [Real Python - pytest](https://realpython.com/pytest-python-testing/)

### Libraries
- [pydantic-factories](https://lyz-code.github.io/pydantic_factories/)
- [factory-boy](https://factoryboy.readthedocs.io/)
- [responses HTTP mocking](https://github.com/getsentry/responses)

