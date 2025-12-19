"""Unit tests for lap comparison service."""

import pytest
from racing_coach_server.metrics.comparison_service import LapComparisonService

from tests.polyfactories import BrakingMetricsDBFactory, CornerMetricsDBFactory, LapMetricsDBFactory


@pytest.mark.unit
class TestLapComparisonService:
    """Unit tests for lap comparison logic."""

    def test_compare_identical_laps(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
        braking_metrics_db_factory: BrakingMetricsDBFactory,
        corner_metrics_db_factory: CornerMetricsDBFactory,
    ) -> None:
        """Test comparing two identical laps produces zero deltas."""
        # Create identical metrics
        baseline = lap_metrics_db_factory.build(
            lap_time=90.0,
            max_speed=100.0,
            min_speed=40.0,
            average_corner_speed=50.0,
            total_corners=2,
            total_braking_zones=2,
        )

        baseline.braking_zones = [
            braking_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                zone_number=1,
                braking_point_distance=0.25,
                braking_point_speed=75.0,
            ),
            braking_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                zone_number=2,
                braking_point_distance=0.75,
                braking_point_speed=80.0,
            ),
        ]

        baseline.corners = [
            corner_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                corner_number=1,
                apex_distance=0.30,
                apex_speed=45.0,
            ),
            corner_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                corner_number=2,
                apex_distance=0.80,
                apex_speed=48.0,
            ),
        ]

        # Create identical comparison (copy of baseline)
        comparison = lap_metrics_db_factory.build(
            lap_time=90.0,
            max_speed=100.0,
            min_speed=40.0,
            average_corner_speed=50.0,
            total_corners=2,
            total_braking_zones=2,
        )

        comparison.braking_zones = [
            braking_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                zone_number=1,
                braking_point_distance=0.25,
                braking_point_speed=75.0,
            ),
            braking_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                zone_number=2,
                braking_point_distance=0.75,
                braking_point_speed=80.0,
            ),
        ]

        comparison.corners = [
            corner_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                corner_number=1,
                apex_distance=0.30,
                apex_speed=45.0,
            ),
            corner_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                corner_number=2,
                apex_distance=0.80,
                apex_speed=48.0,
            ),
        ]

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert summary
        assert result.summary.lap_time_delta == 0.0
        assert result.summary.max_speed_delta == 0.0
        assert result.summary.min_speed_delta == 0.0
        assert result.summary.matched_braking_zones == 2
        assert result.summary.matched_corners == 2

        # Assert braking zones all matched with zero deltas
        assert len(result.braking_zone_comparisons) == 2
        for bc in result.braking_zone_comparisons:
            assert bc.matched_zone_index is not None
            assert bc.distance_delta == pytest.approx(0.0, abs=0.001)
            assert bc.braking_point_speed_delta == pytest.approx(0.0, abs=0.001)

        # Assert corners all matched with zero deltas
        assert len(result.corner_comparisons) == 2
        for cc in result.corner_comparisons:
            assert cc.matched_corner_index is not None
            assert cc.distance_delta == pytest.approx(0.0, abs=0.001)
            assert cc.apex_speed_delta == pytest.approx(0.0, abs=0.001)

    def test_compare_laps_with_improvements(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
        braking_metrics_db_factory: BrakingMetricsDBFactory,
        corner_metrics_db_factory: CornerMetricsDBFactory,
    ) -> None:
        """Test comparison shows positive deltas when comparison lap is faster."""
        # Create baseline metrics
        baseline = lap_metrics_db_factory.build(
            lap_time=92.0,
            max_speed=95.0,
            average_corner_speed=45.0,
        )
        baseline.braking_zones = [
            braking_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                braking_point_distance=0.25,
                braking_point_speed=70.0,
            )
        ]
        baseline.corners = [
            corner_metrics_db_factory.build(
                lap_metrics_id=baseline.id,
                apex_distance=0.30,
                apex_speed=45.0,
            )
        ]

        # Create improved comparison lap (faster)
        comparison = lap_metrics_db_factory.build(
            lap_time=90.0,  # 2 seconds faster
            max_speed=98.0,  # 3 mph faster
            average_corner_speed=48.0,  # 3 mph faster in corners
        )
        comparison.braking_zones = [
            braking_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                braking_point_distance=0.25,
                braking_point_speed=75.0,  # 5 mph faster
            )
        ]
        comparison.corners = [
            corner_metrics_db_factory.build(
                lap_metrics_id=comparison.id,
                apex_distance=0.30,
                apex_speed=48.0,  # 3 mph faster
            )
        ]

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert improvements
        assert result.summary.lap_time_delta == -2.0  # Negative = faster
        assert result.summary.max_speed_delta == 3.0  # Positive = faster
        assert result.summary.average_corner_speed_delta == 3.0

        # Assert braking improvement
        assert result.braking_zone_comparisons[0].braking_point_speed_delta == 5.0

        # Assert corner improvement
        assert result.corner_comparisons[0].apex_speed_delta == 3.0

    def test_distance_based_matching(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
        corner_metrics_db_factory: CornerMetricsDBFactory,
    ) -> None:
        """Test that corners are matched by closest distance."""
        # Create baseline with 3 corners
        baseline = lap_metrics_db_factory.build()
        baseline.corners = [
            corner_metrics_db_factory.build(apex_distance=0.20),
            corner_metrics_db_factory.build(apex_distance=0.50),
            corner_metrics_db_factory.build(apex_distance=0.80),
        ]

        # Create comparison with 3 corners at slightly different positions
        comparison = lap_metrics_db_factory.build()
        comparison.corners = [
            corner_metrics_db_factory.build(apex_distance=0.22),  # Should match 0.20
            corner_metrics_db_factory.build(apex_distance=0.78),  # Should match 0.80
            corner_metrics_db_factory.build(apex_distance=0.52),  # Should match 0.50
        ]

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert all corners matched
        assert len(result.corner_comparisons) == 3
        assert all(cc.matched_corner_index is not None for cc in result.corner_comparisons)

        # Verify correct matching (closest distance)
        # Baseline 0.20 -> Comparison 0.22 (index 0)
        assert result.corner_comparisons[0].baseline_apex_distance == pytest.approx(0.20)
        assert result.corner_comparisons[0].comparison_apex_distance == pytest.approx(0.22)

        # Baseline 0.50 -> Comparison 0.52 (index 2)
        assert result.corner_comparisons[1].baseline_apex_distance == pytest.approx(0.50)
        assert result.corner_comparisons[1].comparison_apex_distance == pytest.approx(0.52)

        # Baseline 0.80 -> Comparison 0.78 (index 1)
        assert result.corner_comparisons[2].baseline_apex_distance == pytest.approx(0.80)
        assert result.corner_comparisons[2].comparison_apex_distance == pytest.approx(0.78)

    def test_unmatched_zones(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
        braking_metrics_db_factory: BrakingMetricsDBFactory,
    ) -> None:
        """Test that zones that don't match show as unmatched."""
        # Create baseline with 2 braking zones
        baseline = lap_metrics_db_factory.build()
        baseline.braking_zones = [
            braking_metrics_db_factory.build(braking_point_distance=0.25),
            braking_metrics_db_factory.build(braking_point_distance=0.75),
        ]

        # Create comparison with only 1 zone (far from both baseline zones)
        comparison = lap_metrics_db_factory.build()
        comparison.braking_zones = [
            braking_metrics_db_factory.build(braking_point_distance=0.50),
        ]

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert: both baseline zones should be unmatched (too far from 0.50)
        assert len(result.braking_zone_comparisons) == 2
        # We expect at least one zone to be unmatched due to distance threshold
        unmatched_zones = [
            bc for bc in result.braking_zone_comparisons if bc.matched_zone_index is None
        ]
        assert len(unmatched_zones) >= 1

    def test_trail_braking_comparison(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
        braking_metrics_db_factory: BrakingMetricsDBFactory,
    ) -> None:
        """Test trail braking comparison between laps."""
        # Baseline uses trail braking
        baseline = lap_metrics_db_factory.build()
        baseline.braking_zones = [
            braking_metrics_db_factory.build(
                braking_point_distance=0.25,
                has_trail_braking=True,
            )
        ]

        # Comparison doesn't use trail braking
        comparison = lap_metrics_db_factory.build()
        comparison.braking_zones = [
            braking_metrics_db_factory.build(
                braking_point_distance=0.25,
                has_trail_braking=False,
            )
        ]

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert trail braking comparison
        assert result.braking_zone_comparisons[0].trail_braking_comparison == "baseline_only"

    def test_empty_laps_comparison(
        self,
        lap_metrics_db_factory: LapMetricsDBFactory,
    ) -> None:
        """Test comparison with no braking zones or corners."""
        baseline = lap_metrics_db_factory.build()
        baseline.braking_zones = []
        baseline.corners = []

        comparison = lap_metrics_db_factory.build()
        comparison.braking_zones = []
        comparison.corners = []

        # Compare
        result = LapComparisonService.compare_laps(baseline, comparison)

        # Assert empty comparisons
        assert len(result.braking_zone_comparisons) == 0
        assert len(result.corner_comparisons) == 0
        assert result.summary.matched_braking_zones == 0
        assert result.summary.matched_corners == 0
