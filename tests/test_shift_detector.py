"""Tests for shift detection algorithm."""

import pandas as pd
import pytest
from datetime import datetime, timedelta
from src.shift_detector import detect_shifts, ShiftEvent


def test_detects_basic_persistent_shift():
    """Detect a shift that persists for 20+ minutes."""
    # Create stable baseline: 12 readings at 350° over 2 hours
    baseline_time = datetime(2024, 6, 1, 12, 0)
    baseline_rows = []
    for i in range(12):
        baseline_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })

    # Add shift to 370° (20° veering shift) that persists for 30 minutes (3 readings)
    shift_time = baseline_time + timedelta(hours=2)
    for i in range(3):
        baseline_rows.append({
            'timestamp': shift_time + timedelta(minutes=i*10),
            'wind_dir_deg': 10.0,  # 370° normalized to 10°
            'wind_speed_knots': 10.0
        })

    df = pd.DataFrame(baseline_rows)
    events = detect_shifts(df, 'test-buoy')

    assert len(events) == 1
    assert events[0].buoy_id == 'test-buoy'
    assert events[0].baseline_direction == 350.0
    assert events[0].new_direction == 10.0
    assert events[0].magnitude == 20.0
    assert events[0].veering is True


def test_baseline_uses_circular_mean():
    """Baseline calculation uses circular mean for 2-hour window."""
    baseline_time = datetime(2024, 6, 1, 12, 0)
    baseline_rows = []

    # Create baseline with angles spanning 0°, but stable within ±10°
    # [355°, 358°, 0°, 2°, 5°, ...] - Circular mean should be ~0°, not ~177° (arithmetic mean)
    angles = [355, 358, 0, 2, 5, 355, 358, 0, 2, 5, 355, 358]
    for i, angle in enumerate(angles):
        baseline_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': float(angle),
            'wind_speed_knots': 10.0
        })

    # Add shift to 25° that persists (well beyond baseline range)
    shift_time = baseline_time + timedelta(hours=2)
    for i in range(2):
        baseline_rows.append({
            'timestamp': shift_time + timedelta(minutes=i*10),
            'wind_dir_deg': 25.0,
            'wind_speed_knots': 10.0
        })

    df = pd.DataFrame(baseline_rows)
    events = detect_shifts(df, 'test-buoy')

    # Should detect shift from ~0° to 25°
    assert len(events) == 1
    # Baseline should be near 0° (not 177° from arithmetic mean)
    assert events[0].baseline_direction < 10.0 or events[0].baseline_direction > 350.0


def test_rejects_unstable_baseline():
    """Reject shifts when baseline readings vary by more than ±10°."""
    baseline_time = datetime(2024, 6, 1, 12, 0)
    baseline_rows = []

    # Create unstable baseline: readings vary widely around 350°
    # [330°, 350°, 10°, 340°, 5°, ...] - outside ±10° stability criterion
    angles = [330, 350, 10, 340, 5, 335, 355, 15, 345, 0, 330, 350]
    for i, angle in enumerate(angles):
        baseline_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': float(angle),
            'wind_speed_knots': 10.0
        })

    # Add what looks like a shift to 30°
    shift_time = baseline_time + timedelta(hours=2)
    for i in range(2):
        baseline_rows.append({
            'timestamp': shift_time + timedelta(minutes=i*10),
            'wind_dir_deg': 30.0,
            'wind_speed_knots': 10.0
        })

    df = pd.DataFrame(baseline_rows)
    events = detect_shifts(df, 'test-buoy')

    # Should NOT detect shift due to unstable baseline
    assert len(events) == 0


def test_filters_to_north_winds_only():
    """Only process wind directions in north range (315-045°)."""
    baseline_time = datetime(2024, 6, 1, 12, 0)

    # Test 1: Baseline in south winds (180°) - should be filtered out
    south_rows = []
    for i in range(12):
        south_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 180.0,
            'wind_speed_knots': 10.0
        })
    # Add shift
    for i in range(2):
        south_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 200.0,
            'wind_speed_knots': 10.0
        })
    df_south = pd.DataFrame(south_rows)
    events_south = detect_shifts(df_south, 'test-buoy')
    assert len(events_south) == 0

    # Test 2: Baseline in north range (350°) - should be processed
    north_rows = []
    for i in range(12):
        north_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    # Add shift
    for i in range(2):
        north_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 10.0,
            'wind_speed_knots': 10.0
        })
    df_north = pd.DataFrame(north_rows)
    events_north = detect_shifts(df_north, 'test-buoy')
    assert len(events_north) == 1


def test_filters_low_wind_speeds():
    """Exclude readings with wind speed below 5 knots."""
    baseline_time = datetime(2024, 6, 1, 12, 0)

    # Create baseline with low wind speeds (below 5 knots)
    low_wind_rows = []
    for i in range(12):
        low_wind_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 3.0  # Below 5 knot threshold
        })
    # Add shift
    for i in range(2):
        low_wind_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 10.0,
            'wind_speed_knots': 3.0
        })
    df_low = pd.DataFrame(low_wind_rows)
    events_low = detect_shifts(df_low, 'test-buoy')
    assert len(events_low) == 0

    # Create baseline with adequate wind speeds (≥5 knots)
    good_wind_rows = []
    for i in range(12):
        good_wind_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 8.0
        })
    # Add shift
    for i in range(2):
        good_wind_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 10.0,
            'wind_speed_knots': 8.0
        })
    df_good = pd.DataFrame(good_wind_rows)
    events_good = detect_shifts(df_good, 'test-buoy')
    assert len(events_good) == 1


def test_shift_magnitude_threshold():
    """Only detect shifts ≥10° from baseline."""
    baseline_time = datetime(2024, 6, 1, 12, 0)

    # Test 1: Small shift (8°) - should NOT be detected
    small_shift_rows = []
    for i in range(12):
        small_shift_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    for i in range(2):
        small_shift_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 358.0,  # 8° shift
            'wind_speed_knots': 10.0
        })
    df_small = pd.DataFrame(small_shift_rows)
    events_small = detect_shifts(df_small, 'test-buoy')
    assert len(events_small) == 0

    # Test 2: Exactly 10° shift - should be detected
    exact_shift_rows = []
    for i in range(12):
        exact_shift_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    for i in range(2):
        exact_shift_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 0.0,  # Exactly 10° shift
            'wind_speed_knots': 10.0
        })
    df_exact = pd.DataFrame(exact_shift_rows)
    events_exact = detect_shifts(df_exact, 'test-buoy')
    assert len(events_exact) == 1
    assert events_exact[0].magnitude == 10.0


def test_persistence_validation():
    """Shift must persist for 20+ minutes (2+ consecutive readings)."""
    baseline_time = datetime(2024, 6, 1, 12, 0)

    # Test 1: Shift that doesn't persist (oscillates back)
    non_persistent_rows = []
    for i in range(12):
        non_persistent_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    # Add one reading at shifted direction, then back to baseline
    non_persistent_rows.append({
        'timestamp': baseline_time + timedelta(hours=2),
        'wind_dir_deg': 10.0,  # 20° shift
        'wind_speed_knots': 10.0
    })
    non_persistent_rows.append({
        'timestamp': baseline_time + timedelta(hours=2, minutes=10),
        'wind_dir_deg': 350.0,  # Back to baseline - not persistent
        'wind_speed_knots': 10.0
    })
    df_non_persistent = pd.DataFrame(non_persistent_rows)
    events_non_persistent = detect_shifts(df_non_persistent, 'test-buoy')
    assert len(events_non_persistent) == 0

    # Test 2: Shift that persists (2 consecutive readings)
    persistent_rows = []
    for i in range(12):
        persistent_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    # Add 2 consecutive readings at shifted direction
    for i in range(2):
        persistent_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 10.0,  # 20° shift persists
            'wind_speed_knots': 10.0
        })
    df_persistent = pd.DataFrame(persistent_rows)
    events_persistent = detect_shifts(df_persistent, 'test-buoy')
    assert len(events_persistent) == 1


def test_veering_vs_backing_classification():
    """Correctly identify veering (clockwise) vs backing (counter-clockwise)."""
    baseline_time = datetime(2024, 6, 1, 12, 0)

    # Test 1: Veering shift (clockwise: 350° → 10°, positive rotation)
    veering_rows = []
    for i in range(12):
        veering_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 350.0,
            'wind_speed_knots': 10.0
        })
    for i in range(2):
        veering_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 10.0,  # Clockwise shift
            'wind_speed_knots': 10.0
        })
    df_veering = pd.DataFrame(veering_rows)
    events_veering = detect_shifts(df_veering, 'test-buoy')
    assert len(events_veering) == 1
    assert events_veering[0].veering is True

    # Test 2: Backing shift (counter-clockwise: 10° → 350°, negative rotation)
    backing_rows = []
    for i in range(12):
        backing_rows.append({
            'timestamp': baseline_time + timedelta(minutes=i*10),
            'wind_dir_deg': 10.0,
            'wind_speed_knots': 10.0
        })
    for i in range(2):
        backing_rows.append({
            'timestamp': baseline_time + timedelta(hours=2, minutes=i*10),
            'wind_dir_deg': 350.0,  # Counter-clockwise shift
            'wind_speed_knots': 10.0
        })
    df_backing = pd.DataFrame(backing_rows)
    events_backing = detect_shifts(df_backing, 'test-buoy')
    assert len(events_backing) == 1
    assert events_backing[0].veering is False
