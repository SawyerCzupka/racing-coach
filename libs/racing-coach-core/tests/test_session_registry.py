"""Tests for the SessionRegistry class."""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from racing_coach_core.events.session_registry import SessionRegistry
from racing_coach_core.models.telemetry import SessionFrame


def create_session_frame(**kwargs) -> SessionFrame:
    """Create a SessionFrame with default values."""
    defaults = {
        "timestamp": datetime.now(timezone.utc),
        "session_id": uuid4(),
        "track_id": 1,
        "track_name": "Test Track",
        "track_config_name": "Full Course",
        "track_type": "road course",
        "car_id": 1,
        "car_name": "Test Car",
        "car_class_id": 1,
        "series_id": 1,
    }
    defaults.update(kwargs)
    return SessionFrame(**defaults)


@pytest.mark.unit
class TestSessionRegistryUnit:
    """Unit tests for SessionRegistry."""

    def test_initialization(self):
        """Test SessionRegistry initializes correctly."""
        registry = SessionRegistry()

        assert registry.get_current_session() is None
        assert not registry.has_active_session

    def test_start_session(self):
        """Test starting a new session."""
        registry = SessionRegistry()
        session = create_session_frame()

        registry.start_session(session)

        assert registry.has_active_session
        assert registry.get_current_session() is session
        assert registry.get_current_session().session_id == session.session_id

    def test_end_session(self):
        """Test ending an active session."""
        registry = SessionRegistry()
        session = create_session_frame()

        registry.start_session(session)
        assert registry.has_active_session

        registry.end_session(session.session_id)

        assert not registry.has_active_session
        assert registry.get_current_session() is None

    def test_end_session_with_wrong_id(self, caplog: pytest.LogCaptureFixture):
        """Test ending a session with wrong ID logs warning."""
        import logging

        registry = SessionRegistry()
        session = create_session_frame()
        wrong_id = uuid4()

        registry.start_session(session)

        with caplog.at_level(logging.WARNING):
            registry.end_session(wrong_id)

        # Session should still be active
        assert registry.has_active_session
        assert "Attempted to end session" in caplog.text

    def test_end_session_when_no_session_active(self, caplog: pytest.LogCaptureFixture):
        """Test ending a session when no session is active logs warning."""
        import logging

        registry = SessionRegistry()

        with caplog.at_level(logging.WARNING):
            registry.end_session(uuid4())

        assert "no session is active" in caplog.text

    def test_start_session_while_another_active(self, caplog: pytest.LogCaptureFixture):
        """Test starting a new session while another is active logs warning."""
        import logging

        registry = SessionRegistry()
        session1 = create_session_frame()
        session2 = create_session_frame()

        registry.start_session(session1)

        with caplog.at_level(logging.WARNING):
            registry.start_session(session2)

        # New session should be active
        assert registry.get_current_session() is session2
        assert "still active" in caplog.text

    def test_get_current_session_returns_none_when_no_session(self):
        """Test that get_current_session returns None when no session is active."""
        registry = SessionRegistry()

        assert registry.get_current_session() is None

    def test_has_active_session_property(self):
        """Test has_active_session property."""
        registry = SessionRegistry()

        assert not registry.has_active_session

        session = create_session_frame()
        registry.start_session(session)

        assert registry.has_active_session

        registry.end_session(session.session_id)

        assert not registry.has_active_session


@pytest.mark.integration
class TestSessionRegistryThreadSafety:
    """Tests for SessionRegistry thread safety."""

    def test_concurrent_reads(self):
        """Test that concurrent reads don't cause issues."""
        registry = SessionRegistry()
        session = create_session_frame()
        registry.start_session(session)

        results = []
        errors = []

        def read_session():
            try:
                for _ in range(100):
                    current = registry.get_current_session()
                    results.append(current is not None)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(results)  # All reads should return a session

    def test_concurrent_start_end(self):
        """Test that concurrent start/end operations don't cause corruption."""
        registry = SessionRegistry()
        errors = []

        def start_and_end():
            try:
                for _ in range(50):
                    session = create_session_frame()
                    registry.start_session(session)
                    registry.end_session(session.session_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=start_and_end) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_read_during_write(self):
        """Test that reads work correctly while writes are happening."""
        registry = SessionRegistry()
        session = create_session_frame()
        registry.start_session(session)
        stop_event = threading.Event()
        errors = []
        read_count = [0]

        def writer():
            try:
                for i in range(100):
                    new_session = create_session_frame()
                    registry.start_session(new_session)
                stop_event.set()
            except Exception as e:
                errors.append(e)
                stop_event.set()

        def reader():
            try:
                while not stop_event.is_set():
                    _ = registry.get_current_session()
                    _ = registry.has_active_session
                    read_count[0] += 1
            except Exception as e:
                errors.append(e)

        writer_thread = threading.Thread(target=writer)
        reader_threads = [threading.Thread(target=reader) for _ in range(3)]

        for t in reader_threads:
            t.start()
        writer_thread.start()

        writer_thread.join()
        for t in reader_threads:
            t.join()

        assert len(errors) == 0
        assert read_count[0] > 0  # Ensure some reads happened
