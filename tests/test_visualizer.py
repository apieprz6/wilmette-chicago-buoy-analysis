"""Tests for visualizer module."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.visualizer import (
    select_best_matches,
    select_failure_cases,
    generate_case_study_plot,
    generate_decision_table,
    generate_findings_report
)
from src.shift_detector import ShiftEvent
from src.correlator import MatchedEvent


def test_select_best_matches_returns_events_with_shortest_lags():
    """Best matches are selected by shortest lag time."""
    # Create test events with different lag times
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 290, 20, 15.0, True)
    w2 = ShiftEvent(datetime(2025, 1, 1, 11, 0), 'wilmette', 180, 210, 30, 18.0, True)
    w3 = ShiftEvent(datetime(2025, 1, 1, 12, 0), 'wilmette', 90, 120, 30, 12.0, True)

    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 5), 'chicago', 270, 290, 20, 14.0, True)
    c2 = ShiftEvent(datetime(2025, 1, 1, 11, 30), 'chicago', 180, 210, 30, 17.0, True)
    c3 = ShiftEvent(datetime(2025, 1, 1, 12, 45), 'chicago', 90, 120, 30, 11.0, True)

    matched_events = [
        MatchedEvent(w1, c1, 5, True, 0.0),   # lag: 5 min
        MatchedEvent(w2, c2, 30, True, 0.0),  # lag: 30 min
        MatchedEvent(w3, c3, 45, True, 0.0),  # lag: 45 min
    ]

    best = select_best_matches(matched_events, count=2)

    assert len(best) == 2
    assert best[0].lag_time == 5
    assert best[1].lag_time == 30


def test_select_best_matches_prioritizes_strong_wind_conditions():
    """Among similar lags, prefer stronger wind conditions."""
    # Two events with same lag, different wind speeds
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 290, 20, 8.0, True)   # light
    w2 = ShiftEvent(datetime(2025, 1, 1, 11, 0), 'wilmette', 180, 210, 30, 18.0, True)  # strong

    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 10), 'chicago', 270, 290, 20, 7.0, True)
    c2 = ShiftEvent(datetime(2025, 1, 1, 11, 10), 'chicago', 180, 210, 30, 17.0, True)

    matched_events = [
        MatchedEvent(w1, c1, 10, True, 0.0),  # lag: 10 min, light wind
        MatchedEvent(w2, c2, 10, True, 0.0),  # lag: 10 min, strong wind
    ]

    best = select_best_matches(matched_events, count=2)

    assert len(best) == 2
    # Stronger wind should come first when lags are equal
    assert best[0].wilmette_shift.wind_speed == 18.0
    assert best[1].wilmette_shift.wind_speed == 8.0


def test_select_failure_cases_returns_strongest_wilmette_shifts():
    """Failure cases are unsuccessful matches with strongest Wilmette shifts."""
    # Create failed matches with different shift magnitudes
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 290, 20, 15.0, True)   # 20° shift
    w2 = ShiftEvent(datetime(2025, 1, 1, 11, 0), 'wilmette', 180, 215, 35, 18.0, True)   # 35° shift
    w3 = ShiftEvent(datetime(2025, 1, 1, 12, 0), 'wilmette', 90, 105, 15, 12.0, True)    # 15° shift

    matched_events = [
        MatchedEvent(w1, None, None, False, 0.0),  # failed, 20° magnitude
        MatchedEvent(w2, None, None, False, 0.0),  # failed, 35° magnitude
        MatchedEvent(w3, None, None, False, 0.0),  # failed, 15° magnitude
    ]

    failures = select_failure_cases(matched_events, count=2)

    assert len(failures) == 2
    # Largest magnitude first
    assert failures[0].wilmette_shift.magnitude == 35
    assert failures[1].wilmette_shift.magnitude == 20


def test_generate_case_study_plot_creates_png_file(tmp_path):
    """Case study plot generates PNG file with time-series overlay."""
    # Create matched event with shift at noon
    shift_time = datetime(2025, 1, 1, 12, 0)
    w_shift = ShiftEvent(shift_time, 'wilmette', 270, 290, 20, 15.0, True)
    c_shift = ShiftEvent(shift_time + timedelta(minutes=10), 'chicago', 270, 290, 20, 14.0, True)
    matched_event = MatchedEvent(w_shift, c_shift, 10, True, 0.0)

    # Create time-series data: 10:30 to 13:30 (3-hour window centered on noon)
    timestamps = pd.date_range(start=shift_time - timedelta(hours=1.5),
                               end=shift_time + timedelta(hours=1.5),
                               freq='10min')
    wilmette_df = pd.DataFrame({
        'timestamp': timestamps,
        'wind_dir_deg': [270] * len(timestamps),  # constant for simplicity
        'wind_speed_knots': [15.0] * len(timestamps)
    })
    chicago_df = pd.DataFrame({
        'timestamp': timestamps,
        'wind_dir_deg': [270] * len(timestamps),
        'wind_speed_knots': [14.0] * len(timestamps)
    })

    output_path = tmp_path / "case_study.png"
    generate_case_study_plot(matched_event, wilmette_df, chicago_df, str(output_path))

    # Verify file was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_decision_table_creates_markdown_table():
    """Decision table has wind speed rows and magnitude columns with metrics."""
    # Create events covering different buckets
    events = []

    # 10-15 knots, 15-20° shift
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 285, 15, 12.0, True)
    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 10), 'chicago', 270, 285, 15, 11.0, True)
    events.append(MatchedEvent(w1, c1, 10, True, 0.0))

    # 15-20 knots, 20-25° shift
    w2 = ShiftEvent(datetime(2025, 1, 1, 11, 0), 'wilmette', 180, 202, 22, 18.0, True)
    c2 = ShiftEvent(datetime(2025, 1, 1, 11, 15), 'chicago', 180, 202, 22, 17.0, True)
    events.append(MatchedEvent(w2, c2, 15, True, 0.0))

    table_md = generate_decision_table(events)

    # Verify it's markdown format
    assert '|' in table_md
    assert 'Wind Speed' in table_md
    assert '10-15' in table_md or '15-20' in table_md  # magnitude buckets
    assert '%' in table_md  # success rate
    assert 'min' in table_md  # lag time


def test_generate_findings_report_creates_complete_markdown(tmp_path):
    """Findings report includes all sections: metrics, table, case studies, recommendations."""
    # Create sample events
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 290, 20, 15.0, True)
    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 10), 'chicago', 270, 290, 20, 14.0, True)
    matched_events = [MatchedEvent(w1, c1, 10, True, 0.0)]

    decision_table = "| Wind Speed | 10-15 |\n|---|---|\n| **10-15** | 100% (10 min) |"
    case_study_dir = "results/case_studies"
    output_path = tmp_path / "FINDINGS.md"

    generate_findings_report(matched_events, decision_table, case_study_dir, str(output_path))

    # Verify file was created
    assert output_path.exists()

    # Verify content sections
    content = output_path.read_text()
    assert '# Wilmette-Chicago Buoy Shift Analysis' in content or 'Findings' in content
    assert 'success rate' in content.lower()
    assert decision_table in content
    assert 'case_studies' in content.lower() or 'case study' in content.lower()
    assert 'recommendation' in content.lower() or 'when to trust' in content.lower()


def test_select_best_matches_handles_empty_list():
    """Best matches returns empty list when no events provided."""
    best = select_best_matches([], count=3)
    assert best == []


def test_select_failure_cases_handles_no_failures():
    """Failure cases returns empty list when all events successful."""
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 290, 20, 15.0, True)
    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 10), 'chicago', 270, 290, 20, 14.0, True)
    matched_events = [MatchedEvent(w1, c1, 10, True, 0.0)]

    failures = select_failure_cases(matched_events, count=3)
    assert failures == []


def test_generate_decision_table_handles_empty_buckets():
    """Decision table shows dashes for empty buckets."""
    # Single event in one bucket
    w1 = ShiftEvent(datetime(2025, 1, 1, 10, 0), 'wilmette', 270, 285, 15, 12.0, True)
    c1 = ShiftEvent(datetime(2025, 1, 1, 10, 10), 'chicago', 270, 285, 15, 11.0, True)
    matched_events = [MatchedEvent(w1, c1, 10, True, 0.0)]

    table_md = generate_decision_table(matched_events)

    # Should have dashes for empty cells
    assert '—' in table_md


def test_generate_case_study_plot_handles_failure_case(tmp_path):
    """Case study plot works for failure cases (no Chicago shift)."""
    shift_time = datetime(2025, 1, 1, 12, 0)
    w_shift = ShiftEvent(shift_time, 'wilmette', 270, 290, 20, 15.0, True)
    matched_event = MatchedEvent(w_shift, None, None, False, 0.0)  # failure case

    timestamps = pd.date_range(start=shift_time - timedelta(hours=1.5),
                               end=shift_time + timedelta(hours=1.5),
                               freq='10min')
    wilmette_df = pd.DataFrame({
        'timestamp': timestamps,
        'wind_dir_deg': [270] * len(timestamps),
        'wind_speed_knots': [15.0] * len(timestamps)
    })
    chicago_df = pd.DataFrame({
        'timestamp': timestamps,
        'wind_dir_deg': [270] * len(timestamps),
        'wind_speed_knots': [14.0] * len(timestamps)
    })

    output_path = tmp_path / "failure_case.png"
    generate_case_study_plot(matched_event, wilmette_df, chicago_df, str(output_path))

    # Should still create plot for failure case
    assert output_path.exists()
    assert output_path.stat().st_size > 0
