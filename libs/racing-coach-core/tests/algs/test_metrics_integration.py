"""Integration tests for metrics extraction using real telemetry data."""

import os
from pathlib import Path

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def ibt_file_path() -> Path:
    """
    Get the path to the sample IBT file for integration testing.

    The sample file is located in the repository root under sample_data/.
    """
    # Get the repository root (3 levels up from this file)
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    ibt_path = repo_root / "sample_data" / "ligierjsp320_bathurst 2025-11-17 18-15-16.ibt"

    if not ibt_path.exists():
        pytest.skip(f"Sample IBT file not found at {ibt_path}")

    return ibt_path


class TestMetricsWithRealTelemetry:
    """Test metrics extraction with real telemetry data from IBT files."""

    @pytest.mark.slow
    def test_extract_metrics_from_ibt_file(self, ibt_file_path: Path) -> None:
        """
        Test extracting metrics from a real IBT file.

        This test:
        1. Loads telemetry from the sample IBT file
        2. Extracts metrics from one or more laps
        3. Validates that metrics are reasonable
        """
        pytest.skip(
            "This test requires the replay source to be implemented. "
            "Skipping until we have access to the ReplayTelemetrySource."
        )

    @pytest.mark.slow
    def test_braking_zones_with_real_data(self, ibt_file_path: Path) -> None:
        """Test that braking zones are detected correctly in real telemetry."""
        pytest.skip("Requires IBT file replay implementation")

    @pytest.mark.slow
    def test_corners_with_real_data(self, ibt_file_path: Path) -> None:
        """Test that corners are detected correctly in real telemetry."""
        pytest.skip("Requires IBT file replay implementation")

    @pytest.mark.slow
    def test_metrics_consistency_across_laps(self, ibt_file_path: Path) -> None:
        """
        Test that metrics are consistent across multiple laps from the same session.

        Verifies that:
        - Similar laps produce similar metrics
        - Corner count is consistent
        - Braking zone count is consistent
        """
        pytest.skip("Requires IBT file replay implementation")
