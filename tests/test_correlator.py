"""Tests for shift correlation logic."""

from datetime import datetime, timedelta
from src.shift_detector import ShiftEvent
from src.correlator import correlate_shifts


def test_successful_match():
    """Wilmette shift finds Chicago shift with similar behavior (both veer by ~10°)."""
    # Wilmette: veers 10° (340→350)
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    # Chicago: veers 12° (5→17) - same behavior, magnitude within ±15°
    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=5.0,
        new_direction=17.0,
        magnitude=12.0,
        wind_speed=11.5,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    matched = result[0]
    assert matched.wilmette_shift == wilmette
    assert matched.chicago_shift == chicago
    assert matched.lag_time == 30
    assert matched.success is True
    assert matched.magnitude_error == 2.0  # |10 - 12|


def test_no_match_too_late():
    """Chicago shift outside 60-minute window is not matched."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    # Chicago shift 61 minutes later - too late
    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 1),
        buoy_id="45198",
        baseline_direction=338.0,
        new_direction=348.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    matched = result[0]
    assert matched.wilmette_shift == wilmette
    assert matched.chicago_shift is None
    assert matched.lag_time is None
    assert matched.success is False


def test_no_match_magnitude_too_different():
    """Chicago shift magnitude differs by >15° - not matched."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    # Chicago also veers but by 30° (magnitude difference = 20°)
    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=320.0,
        new_direction=350.0,
        magnitude=30.0,
        wind_speed=11.5,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    matched = result[0]
    assert matched.chicago_shift is None
    assert matched.success is False


def test_no_match_opposite_rotation():
    """Chicago shift in opposite rotation (veering vs backing) - not matched."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True  # Veering
    )

    # Chicago backs instead of veering
    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 30),
        buoy_id="45198",
        baseline_direction=20.0,
        new_direction=10.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=False  # Backing
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    matched = result[0]
    assert matched.chicago_shift is None
    assert matched.success is False


def test_multiple_candidates_takes_earliest():
    """When multiple Chicago shifts match, takes the one with shortest lag."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    # Two Chicago shifts both within criteria
    chicago_early = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 20),  # 20 minutes
        buoy_id="45198",
        baseline_direction=338.0,
        new_direction=348.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    chicago_late = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 45),  # 45 minutes
        buoy_id="45198",
        baseline_direction=338.0,
        new_direction=352.0,
        magnitude=10.0,
        wind_speed=11.0,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago_late, chicago_early])

    assert len(result) == 1
    matched = result[0]
    assert matched.chicago_shift == chicago_early
    assert matched.lag_time == 20
    assert matched.success is True


def test_window_boundary_zero_minutes():
    """Chicago shift at exactly same time (0 minutes lag) matches."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),  # Same time
        buoy_id="45198",
        baseline_direction=338.0,
        new_direction=348.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    assert result[0].lag_time == 0
    assert result[0].success is True


def test_window_boundary_sixty_minutes():
    """Chicago shift at exactly 60 minutes matches (inclusive boundary)."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    chicago = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 13, 0),  # Exactly 60 minutes
        buoy_id="45198",
        baseline_direction=338.0,
        new_direction=348.0,
        magnitude=10.0,
        wind_speed=11.5,
        veering=True
    )

    result = correlate_shifts([wilmette], [chicago])

    assert len(result) == 1
    assert result[0].lag_time == 60
    assert result[0].success is True


def test_no_chicago_shifts():
    """Wilmette shift with empty Chicago list returns unmatched event."""
    wilmette = ShiftEvent(
        timestamp=datetime(2025, 1, 15, 12, 0),
        buoy_id="45174",
        baseline_direction=340.0,
        new_direction=350.0,
        magnitude=10.0,
        wind_speed=12.0,
        veering=True
    )

    result = correlate_shifts([wilmette], [])

    assert len(result) == 1
    assert result[0].chicago_shift is None
    assert result[0].success is False
