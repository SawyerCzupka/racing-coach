# Racing Coach Client Tests

This directory contains the test suite for the racing-coach-client application.

## Test Structure

The test structure mirrors the source code structure for easy navigation:

```
tests/
├── conftest.py                     # Pytest configuration and shared fixtures
├── factories.py                    # Factory-boy factories for test data
├── collectors/
│   ├── test_connection.py          # iRacingConnectionManager tests
│   ├── test_iracing.py             # TelemetryCollector tests
│   └── sources/
│       └── test_replay.py          # ReplayTelemetrySource tests
├── handlers/
│   ├── test_lap_handler.py         # LapHandler tests
│   └── test_log_handler.py         # LogHandler tests
└── test_integration.py             # End-to-end integration tests
```

## Running Tests

### Install Test Dependencies

```bash
# Install test dependencies using uv
uv sync --group test
```

### Run All Tests (Except IBT Tests)

Most tests use mocked data and don't require an actual IBT file:

```bash
pytest -m "not ibt"
```

### Run Tests with Real IBT File

Some integration tests require a real iRacing telemetry (IBT) file. To run these tests:

1. Set the `REPLAY_FILE_PATH` environment variable to point to your IBT file:

```bash
export REPLAY_FILE_PATH=/path/to/your/telemetry.ibt
```

2. Run the IBT tests:

```bash
pytest -m ibt
```

Or run all tests including IBT tests:

```bash
pytest
```

### Run Specific Test Categories

The test suite uses pytest markers to categorize tests:

- `unit`: Unit tests with mocked dependencies
- `integration`: Integration tests that test components together
- `ibt`: Tests that require a real IBT file
- `slow`: Tests that take longer to run

Examples:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run fast tests only (exclude slow tests)
pytest -m "not slow"

# Run integration tests that don't need IBT files
pytest -m "integration and not ibt"
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=racing_coach_client --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Files or Tests

```bash
# Run a specific test file
pytest tests/collectors/test_connection.py

# Run a specific test
pytest tests/collectors/test_connection.py::TestIRacingConnectionManager::test_connect_success

# Run all tests in a directory
pytest tests/handlers/
```

## Test Fixtures

### Key Fixtures from `conftest.py`

- `event_bus`: Fresh EventBus instance for testing
- `running_event_bus`: Started EventBus instance with automatic cleanup
- `event_collector`: Utility for collecting and waiting for events
- `ibt_file_path`: Path to IBT file (skips test if not configured)
- `mock_telemetry_source`: Mock telemetry source with realistic data
- `telemetry_frame_collector`: Event collector registered for TELEMETRY_FRAME events
- `lap_sequence_collector`: Event collector registered for LAP_TELEMETRY_SEQUENCE events

### Factory Fixtures

The following factories are automatically registered as fixtures:

- `telemetry_frame_factory`: Creates TelemetryFrame instances
- `session_frame_factory`: Creates SessionFrame instances
- `lap_telemetry_factory`: Creates LapTelemetry instances
- `telemetry_and_session_factory`: Creates TelemetryAndSession instances
- `lap_and_session_factory`: Creates LapAndSession instances
- `enhanced_telemetry_frame_factory`: Creates TelemetryFrame with extended value ranges

## Writing New Tests

### Test Organization

- **Unit tests**: Test individual components in isolation with mocked dependencies
  - Use `@pytest.mark.unit` marker
  - Mock external dependencies (telemetry sources, event bus, etc.)

- **Integration tests**: Test components working together
  - Use `@pytest.mark.integration` marker
  - May use real event bus but typically mock telemetry sources

- **IBT tests**: Test with real IBT files
  - Use `@pytest.mark.ibt` marker
  - Use `ibt_file_path` fixture (auto-skips if no file provided)
  - Mark as `@pytest.mark.slow` if test takes >1 second

### Example Test

```python
import pytest
from racing_coach_core.events.base import EventBus

@pytest.mark.unit
def test_my_feature(event_bus: EventBus, telemetry_frame_factory):
    """Test my feature with mocked data."""
    # Arrange
    frame = telemetry_frame_factory.build(speed=50.0)

    # Act
    result = process_frame(frame)

    # Assert
    assert result.speed == 50.0

@pytest.mark.ibt
@pytest.mark.integration
async def test_with_real_ibt(running_event_bus: EventBus, ibt_file_path):
    """Test with real IBT file."""
    source = ReplayTelemetrySource(ibt_file_path)
    # ... test implementation
```

### Using EventCollector for Async Event Testing

```python
async def test_events(running_event_bus, event_collector):
    # Register collector
    from racing_coach_core.events.base import Handler

    handler = Handler(
        type=SystemEvents.TELEMETRY_FRAME,
        func=event_collector.collect,
    )
    running_event_bus.register_handlers([handler])

    # Publish events
    # ...

    # Wait for events
    events = await event_collector.wait_for_event(
        SystemEvents.TELEMETRY_FRAME,
        timeout=2.0,
        count=5
    )

    assert len(events) == 5
```

## Continuous Integration

When running in CI, you can skip IBT tests by default:

```bash
pytest -m "not ibt" --cov=racing_coach_client
```

## Troubleshooting

### Tests Are Skipped

If you see tests being skipped with "REPLAY_FILE_PATH not set":
- This is expected for IBT tests when no IBT file is configured
- Set the `REPLAY_FILE_PATH` environment variable to run these tests

### Async Tests Hanging

If async tests hang:
- Check that the event bus is being properly stopped
- Verify `running_event_bus` fixture is being used (it handles cleanup)
- Add timeout to `wait_for_event()` calls

### Import Errors

If you see import errors:
- Ensure you're in the project root directory
- Run `uv sync --group test` to install dependencies
- Check that `pythonpath = ["src"]` is set in `pyproject.toml`
