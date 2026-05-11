"""Tests for reliability metrics and lag analysis."""

import csv
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.correlator import MatchedEvent
from src.shift_detector import ShiftEvent
from src.analyzer import (
    calculate_success_rate,
    calculate_lag_statistics_by_windspeed,
    calculate_shift_direction_breakdown,
    export_reliability_summary,
    generate_lag_histograms,
    calculate_success_rate_by_magnitude,
    calculate_magnitude_lag_correlation,
    calculate_magnitude_correlation,
    find_magnitude_threshold,
    export_magnitude_correlations,
    generate_magnitude_plots
)


def test_success_rate_with_mixed_results():
    """Calculate success rate from matched events with some successes and failures."""
    # Create 3 successful matches and 2 failures
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=340.0,
        magnitude=10.0,
        wind_speed=15.0,
        veering=False
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,
        wind_speed=18.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 45),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=25.0,
        magnitude=15.0,
        wind_speed=17.0,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=355.0,
        new_direction=345.0,
        magnitude=10.0,
        wind_speed=10.0,
        veering=False
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 20),
        buoy_id="45198",
        baseline_direction=25.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=9.5,
        veering=False
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=345.0,
        new_direction=355.0,
        magnitude=10.0,
        wind_speed=8.0,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 30, True, 0.0),
        MatchedEvent(wilmette2, None, None, False, 0.0),
        MatchedEvent(wilmette3, chicago3, 45, True, 0.0),
        MatchedEvent(wilmette4, chicago4, 20, True, 0.0),
        MatchedEvent(wilmette5, None, None, False, 0.0),
    ]

    result = calculate_success_rate(matched_events)

    assert result['total_events'] == 5
    assert result['successful_matches'] == 3
    assert result['failed_matches'] == 2
    assert result['success_rate'] == 60.0  # 3/5 = 60%


def test_lag_statistics_by_windspeed_bucket():
    """Calculate lag statistics grouped by wind speed buckets."""
    # Create events across multiple wind speed buckets
    # Bucket 5-10 knots: 2 successful matches (lag 20, 25)
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=8.0,  # 5-10 bucket
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=7.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=340.0,
        magnitude=10.0,
        wind_speed=9.5,  # 5-10 bucket
        veering=False
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 25),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=5.0,
        magnitude=10.0,
        wind_speed=9.0,
        veering=False
    )

    # Bucket 10-15 knots: 3 successful matches (lag 30, 40, 50)
    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,
        wind_speed=12.0,  # 10-15 bucket
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=25.0,
        magnitude=15.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=355.0,
        new_direction=345.0,
        magnitude=10.0,
        wind_speed=14.0,  # 10-15 bucket
        veering=False
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 40),
        buoy_id="45198",
        baseline_direction=25.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=13.5,
        veering=False
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=345.0,
        new_direction=355.0,
        magnitude=10.0,
        wind_speed=13.5,  # 10-15 bucket
        veering=True
    )
    chicago5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 50),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=25.0,
        magnitude=10.0,
        wind_speed=13.0,
        veering=True
    )

    # Bucket 15-20 knots: 1 failed match
    wilmette6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 0),
        buoy_id="45174",
        baseline_direction=355.0,
        new_direction=340.0,
        magnitude=15.0,
        wind_speed=18.0,  # 15-20 bucket
        veering=False
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 25, True, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
        MatchedEvent(wilmette4, chicago4, 40, True, 0.0),
        MatchedEvent(wilmette5, chicago5, 50, True, 0.0),
        MatchedEvent(wilmette6, None, None, False, 0.0),
    ]

    result = calculate_lag_statistics_by_windspeed(matched_events)

    # Check bucket 5-10 knots
    assert '5-10' in result
    bucket_5_10 = result['5-10']
    assert bucket_5_10['count'] == 2
    assert bucket_5_10['mean_lag'] == 22.5  # (20 + 25) / 2
    assert bucket_5_10['median_lag'] == 22.5
    assert bucket_5_10['min_lag'] == 20
    assert bucket_5_10['max_lag'] == 25

    # Check bucket 10-15 knots
    assert '10-15' in result
    bucket_10_15 = result['10-15']
    assert bucket_10_15['count'] == 3
    assert bucket_10_15['mean_lag'] == 40.0  # (30 + 40 + 50) / 3
    assert bucket_10_15['median_lag'] == 40.0
    assert bucket_10_15['min_lag'] == 30
    assert bucket_10_15['max_lag'] == 50

    # Check bucket 15-20 knots (only failed match, should not appear in lag stats)
    assert '15-20' not in result or result['15-20']['count'] == 0


def test_shift_direction_breakdown():
    """Calculate success rate and average lag by shift direction (veering vs backing)."""
    # Create events: 3 veering (2 successful), 3 backing (1 successful)
    # Veering successful: lag 30, 40
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=5.0,
        magnitude=15.0,
        wind_speed=14.0,
        veering=True
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 40),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=30.0,
        magnitude=15.0,
        wind_speed=13.5,
        veering=True
    )

    # Veering failed
    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=10.0,
        veering=True
    )

    # Backing successful: lag 25
    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=15.0,
        new_direction=5.0,
        magnitude=10.0,
        wind_speed=16.0,
        veering=False
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 25),
        buoy_id="45198",
        baseline_direction=30.0,
        new_direction=20.0,
        magnitude=10.0,
        wind_speed=15.5,
        veering=False
    )

    # Backing failed
    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=350.0,
        magnitude=15.0,
        wind_speed=18.0,
        veering=False
    )

    wilmette6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=340.0,
        magnitude=10.0,
        wind_speed=20.0,
        veering=False
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 30, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 40, True, 0.0),
        MatchedEvent(wilmette3, None, None, False, 0.0),
        MatchedEvent(wilmette4, chicago4, 25, True, 0.0),
        MatchedEvent(wilmette5, None, None, False, 0.0),
        MatchedEvent(wilmette6, None, None, False, 0.0),
    ]

    result = calculate_shift_direction_breakdown(matched_events)

    # Check veering stats
    assert 'veering' in result
    veering = result['veering']
    assert veering['total_events'] == 3
    assert veering['successful_matches'] == 2
    assert veering['success_rate'] == pytest.approx(66.67, rel=0.01)  # 2/3
    assert veering['average_lag'] == 35.0  # (30 + 40) / 2

    # Check backing stats
    assert 'backing' in result
    backing = result['backing']
    assert backing['total_events'] == 3
    assert backing['successful_matches'] == 1
    assert backing['success_rate'] == pytest.approx(33.33, rel=0.01)  # 1/3
    assert backing['average_lag'] == 25.0  # only one lag value


def test_export_reliability_summary():
    """Export reliability summary to CSV with overall metrics and by-bucket statistics."""
    # Create varied events across buckets
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=8.0,  # 5-10 bucket
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 25),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=7.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=340.0,
        magnitude=10.0,
        wind_speed=12.0,  # 10-15 bucket
        veering=False
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 35),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=5.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=False
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,
        wind_speed=18.0,  # 15-20 bucket
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 25, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 35, True, 0.0),
        MatchedEvent(wilmette3, None, None, False, 0.0),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "reliability_summary.csv"
        export_reliability_summary(matched_events, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check overall section
        overall_row = rows[0]
        assert overall_row['metric'] == 'overall'
        assert overall_row['total_events'] == '3'
        assert overall_row['successful_matches'] == '2'
        assert float(overall_row['success_rate']) == pytest.approx(66.67, rel=0.01)

        # Check bucket rows
        bucket_rows = {row['metric']: row for row in rows if row['metric'].startswith('bucket_')}

        assert 'bucket_5-10' in bucket_rows
        bucket_5_10 = bucket_rows['bucket_5-10']
        assert bucket_5_10['count'] == '1'
        assert float(bucket_5_10['mean_lag']) == 25.0

        assert 'bucket_10-15' in bucket_rows
        bucket_10_15 = bucket_rows['bucket_10-15']
        assert bucket_10_15['count'] == '1'
        assert float(bucket_10_15['mean_lag']) == 35.0


def test_generate_lag_histograms():
    """Generate lag distribution histograms as PNG files."""
    # Create events with varied lag times across buckets
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=8.0,  # 5-10 bucket
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=7.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=340.0,
        magnitude=10.0,
        wind_speed=8.5,  # 5-10 bucket
        veering=False
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 30),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=5.0,
        magnitude=10.0,
        wind_speed=8.0,
        veering=False
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,
        wind_speed=12.0,  # 10-15 bucket
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 45),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=25.0,
        magnitude=15.0,
        wind_speed=11.5,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 30, True, 0.0),
        MatchedEvent(wilmette3, chicago3, 45, True, 0.0),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generate_lag_histograms(matched_events, str(output_dir))

        # Check that expected PNG files are created
        overall_plot = output_dir / "lag_distribution_overall.png"
        by_windspeed_plot = output_dir / "lag_distribution_by_windspeed.png"
        by_direction_plot = output_dir / "success_by_shift_direction.png"

        assert overall_plot.exists()
        assert by_windspeed_plot.exists()
        assert by_direction_plot.exists()


def test_success_rate_by_magnitude_bins():
    """Calculate success rate grouped by Wilmette shift magnitude in 5° buckets."""
    # Create events across magnitude buckets
    # Bucket 10-15°: 3 events (2 successful) = 66.7%
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,  # 10-15 bucket
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=5.0,
        magnitude=12.0,  # 10-15 bucket
        wind_speed=14.0,
        veering=True
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 40),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=27.0,
        magnitude=12.0,
        wind_speed=13.5,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=18.0,
        magnitude=13.0,  # 10-15 bucket
        wind_speed=10.0,
        veering=True
    )

    # Bucket 15-20°: 2 events (2 successful) = 100%
    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,  # 15-20 bucket
        wind_speed=16.0,
        veering=True
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 25),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=25.0,
        magnitude=15.0,
        wind_speed=15.5,
        veering=True
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=8.0,
        magnitude=18.0,  # 15-20 bucket
        wind_speed=18.0,
        veering=True
    )
    chicago5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 30),
        buoy_id="45198",
        baseline_direction=20.0,
        new_direction=38.0,
        magnitude=18.0,
        wind_speed=17.5,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 30, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 40, True, 0.0),
        MatchedEvent(wilmette3, None, None, False, 0.0),
        MatchedEvent(wilmette4, chicago4, 25, True, 0.0),
        MatchedEvent(wilmette5, chicago5, 30, True, 0.0),
    ]

    result = calculate_success_rate_by_magnitude(matched_events)

    # Check bucket 10-15°
    assert '10-15' in result
    bucket_10_15 = result['10-15']
    assert bucket_10_15['count'] == 3
    assert bucket_10_15['successful'] == 2
    assert bucket_10_15['success_rate'] == pytest.approx(66.67, rel=0.01)

    # Check bucket 15-20°
    assert '15-20' in result
    bucket_15_20 = result['15-20']
    assert bucket_15_20['count'] == 2
    assert bucket_15_20['successful'] == 2
    assert bucket_15_20['success_rate'] == 100.0


def test_magnitude_lag_correlation():
    """Calculate Pearson correlation between Wilmette magnitude and lag time."""
    # Create events with varying magnitudes and lag times
    # Magnitudes: 10, 15, 20, 25, 30
    # Lag times: 20, 25, 30, 35, 40
    # Perfect positive correlation
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=5.0,
        magnitude=15.0,
        wind_speed=14.0,
        veering=True
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 25),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=30.0,
        magnitude=15.0,
        wind_speed=13.5,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=25.0,
        magnitude=20.0,
        wind_speed=16.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=30.0,
        new_direction=50.0,
        magnitude=20.0,
        wind_speed=15.5,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=25.0,
        new_direction=50.0,
        magnitude=25.0,
        wind_speed=18.0,
        veering=True
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 35),
        buoy_id="45198",
        baseline_direction=50.0,
        new_direction=75.0,
        magnitude=25.0,
        wind_speed=17.5,
        veering=True
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=50.0,
        new_direction=80.0,
        magnitude=30.0,
        wind_speed=20.0,
        veering=True
    )
    chicago5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 40),
        buoy_id="45198",
        baseline_direction=75.0,
        new_direction=105.0,
        magnitude=30.0,
        wind_speed=19.5,
        veering=True
    )

    # Add one failed match (should be excluded from correlation)
    wilmette6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 0),
        buoy_id="45174",
        baseline_direction=80.0,
        new_direction=100.0,
        magnitude=20.0,
        wind_speed=15.0,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 25, True, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
        MatchedEvent(wilmette4, chicago4, 35, True, 0.0),
        MatchedEvent(wilmette5, chicago5, 40, True, 0.0),
        MatchedEvent(wilmette6, None, None, False, 0.0),
    ]

    result = calculate_magnitude_lag_correlation(matched_events)

    assert 'correlation' in result
    assert 'p_value' in result
    assert 'data_points' in result

    # Perfect positive correlation
    assert result['correlation'] == pytest.approx(1.0, abs=0.01)
    assert result['p_value'] < 0.01  # Highly significant
    assert len(result['data_points']) == 5  # Only successful matches


def test_magnitude_correlation():
    """Calculate Pearson correlation and linear regression between Wilmette and Chicago magnitudes."""
    # Create events with perfectly correlated magnitudes (slope = 1, intercept = 0)
    # Wilmette: 10, 15, 20, 25, 30
    # Chicago:  10, 15, 20, 25, 30
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=5.0,
        magnitude=15.0,
        wind_speed=14.0,
        veering=True
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 25),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=30.0,
        magnitude=15.0,
        wind_speed=13.5,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=25.0,
        magnitude=20.0,
        wind_speed=16.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=30.0,
        new_direction=50.0,
        magnitude=20.0,
        wind_speed=15.5,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=25.0,
        new_direction=50.0,
        magnitude=25.0,
        wind_speed=18.0,
        veering=True
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 35),
        buoy_id="45198",
        baseline_direction=50.0,
        new_direction=75.0,
        magnitude=25.0,
        wind_speed=17.5,
        veering=True
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=50.0,
        new_direction=80.0,
        magnitude=30.0,
        wind_speed=20.0,
        veering=True
    )
    chicago5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 40),
        buoy_id="45198",
        baseline_direction=75.0,
        new_direction=105.0,
        magnitude=30.0,
        wind_speed=19.5,
        veering=True
    )

    # Add one failed match (should be excluded)
    wilmette6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 0),
        buoy_id="45174",
        baseline_direction=80.0,
        new_direction=100.0,
        magnitude=20.0,
        wind_speed=15.0,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 25, True, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
        MatchedEvent(wilmette4, chicago4, 35, True, 0.0),
        MatchedEvent(wilmette5, chicago5, 40, True, 0.0),
        MatchedEvent(wilmette6, None, None, False, 0.0),
    ]

    result = calculate_magnitude_correlation(matched_events)

    assert 'correlation' in result
    assert 'p_value' in result
    assert 'slope' in result
    assert 'intercept' in result
    assert 'data_points' in result

    # Perfect positive correlation
    assert result['correlation'] == pytest.approx(1.0, abs=0.01)
    assert result['p_value'] < 0.01
    assert result['slope'] == pytest.approx(1.0, abs=0.01)
    assert result['intercept'] == pytest.approx(0.0, abs=0.01)
    assert len(result['data_points']) == 5  # Only successful matches


def test_find_magnitude_threshold_exists():
    """Find minimum magnitude where cumulative success rate exceeds 80%."""
    # Create events where magnitudes >= 20° have success rate >= 80%
    # Magnitude >= 10: 5/7 = 71.4%
    # Magnitude >= 12: 5/6 = 83.3% (first threshold >= 80%)
    # Magnitude >= 20: 3/3 = 100%
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=362.0,
        magnitude=12.0,
        wind_speed=14.0,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=18.0,
        magnitude=13.0,
        wind_speed=10.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=28.0,
        magnitude=13.0,
        wind_speed=9.5,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=355.0,
        magnitude=15.0,
        wind_speed=16.0,
        veering=True
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 25),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=25.0,
        magnitude=15.0,
        wind_speed=15.5,
        veering=True
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=370.0,
        magnitude=20.0,
        wind_speed=18.0,
        veering=True
    )
    chicago5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 30),
        buoy_id="45198",
        baseline_direction=20.0,
        new_direction=40.0,
        magnitude=20.0,
        wind_speed=17.5,
        veering=True
    )

    wilmette6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=30.0,
        magnitude=25.0,
        wind_speed=20.0,
        veering=True
    )
    chicago6 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 17, 40),
        buoy_id="45198",
        baseline_direction=30.0,
        new_direction=55.0,
        magnitude=25.0,
        wind_speed=19.5,
        veering=True
    )

    wilmette7 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 18, 0),
        buoy_id="45174",
        baseline_direction=30.0,
        new_direction=60.0,
        magnitude=30.0,
        wind_speed=22.0,
        veering=True
    )
    chicago7 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 18, 50),
        buoy_id="45198",
        baseline_direction=55.0,
        new_direction=85.0,
        magnitude=30.0,
        wind_speed=21.5,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, None, None, False, 0.0),
        MatchedEvent(wilmette2, None, None, False, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
        MatchedEvent(wilmette4, chicago4, 25, True, 0.0),
        MatchedEvent(wilmette5, chicago5, 30, True, 0.0),
        MatchedEvent(wilmette6, chicago6, 40, True, 0.0),
        MatchedEvent(wilmette7, chicago7, 50, True, 0.0),
    ]

    threshold = find_magnitude_threshold(matched_events, target_rate=80.0)

    # All shifts >= 12° have 5/6 = 83.3% success rate
    assert threshold == 12.0


def test_find_magnitude_threshold_not_reached():
    """Return None when success rate never reaches target threshold."""
    # Create events where success rate never reaches 80%
    # Magnitude >= 10: 2/5 = 40%
    # Magnitude >= 15: 1/3 = 33%
    # Magnitude >= 20: 1/2 = 50%
    # Magnitude >= 25: 0/1 = 0%
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=362.0,
        magnitude=12.0,
        wind_speed=14.0,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=20.0,
        magnitude=15.0,
        wind_speed=16.0,
        veering=True
    )

    wilmette4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=360.0,
        magnitude=20.0,
        wind_speed=18.0,
        veering=True
    )
    chicago4 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 15, 30),
        buoy_id="45198",
        baseline_direction=10.0,
        new_direction=30.0,
        magnitude=20.0,
        wind_speed=17.5,
        veering=True
    )

    wilmette5 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 16, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=30.0,
        magnitude=25.0,
        wind_speed=20.0,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 30, True, 0.0),
        MatchedEvent(wilmette2, None, None, False, 0.0),
        MatchedEvent(wilmette3, None, None, False, 0.0),
        MatchedEvent(wilmette4, chicago4, 30, True, 0.0),
        MatchedEvent(wilmette5, None, None, False, 0.0),
    ]

    threshold = find_magnitude_threshold(matched_events, target_rate=80.0)

    # Best case: 2/5 = 40%, never reaches 80%
    assert threshold is None


def test_export_magnitude_correlations():
    """Export magnitude correlation metrics to CSV."""
    # Create simple dataset
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=365.0,
        magnitude=15.0,
        wind_speed=14.0,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=25.0,
        magnitude=20.0,
        wind_speed=16.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=35.0,
        magnitude=20.0,
        wind_speed=15.5,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, None, None, False, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "magnitude_correlations.csv"
        export_magnitude_correlations(matched_events, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have rows for correlations, threshold, and binned success rates
        assert len(rows) > 0

        # Check for expected metrics
        metric_names = {row['metric'] for row in rows}
        assert 'magnitude_lag_correlation' in metric_names
        assert 'wilmette_chicago_magnitude_correlation' in metric_names
        assert 'magnitude_threshold_80pct' in metric_names


def test_generate_magnitude_plots():
    """Generate magnitude correlation scatter plots as PNG files."""
    # Create events with varying magnitudes
    wilmette1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )
    chicago1 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=15.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    wilmette2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),
        buoy_id="45174",
        baseline_direction=350.0,
        new_direction=365.0,
        magnitude=15.0,
        wind_speed=14.0,
        veering=True
    )
    chicago2 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 25),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=30.0,
        magnitude=15.0,
        wind_speed=13.5,
        veering=True
    )

    wilmette3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 0),
        buoy_id="45174",
        baseline_direction=5.0,
        new_direction=25.0,
        magnitude=20.0,
        wind_speed=16.0,
        veering=True
    )
    chicago3 = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 14, 30),
        buoy_id="45198",
        baseline_direction=15.0,
        new_direction=35.0,
        magnitude=20.0,
        wind_speed=15.5,
        veering=True
    )

    matched_events = [
        MatchedEvent(wilmette1, chicago1, 20, True, 0.0),
        MatchedEvent(wilmette2, chicago2, 25, True, 0.0),
        MatchedEvent(wilmette3, chicago3, 30, True, 0.0),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generate_magnitude_plots(matched_events, str(output_dir))

        # Check that expected PNG files are created
        magnitude_vs_success = output_dir / "magnitude_vs_success.png"
        magnitude_vs_lag = output_dir / "magnitude_vs_lag.png"
        wilmette_vs_chicago = output_dir / "wilmette_vs_chicago_magnitude.png"

        assert magnitude_vs_success.exists()
        assert magnitude_vs_lag.exists()
        assert wilmette_vs_chicago.exists()
