"""Detect persistent wind shifts in buoy time series data."""

from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from src.wind_math import circular_mean, angular_distance

# Detection thresholds
BASELINE_WINDOW_SIZE = 12  # readings (2 hours at 10-min intervals)
STABILITY_THRESHOLD = 15.0  # degrees (relaxed from 10° to handle natural wind variability)
SHIFT_MAGNITUDE_THRESHOLD = 10.0  # degrees
PERSISTENCE_THRESHOLD = 10.0  # degrees
MIN_WIND_SPEED = 5.0  # knots
NORTH_WIND_MIN = 315.0  # degrees
NORTH_WIND_MAX = 45.0  # degrees


def _is_north_wind(direction: float) -> bool:
    """Check if wind direction is in north range (315-045°)."""
    return direction >= NORTH_WIND_MIN or direction <= NORTH_WIND_MAX


def _is_baseline_stable(baseline_dir: float, readings: list[float]) -> bool:
    """Check if all baseline readings are within ±10° of mean."""
    return all(
        abs(angular_distance(baseline_dir, reading)) <= STABILITY_THRESHOLD
        for reading in readings
    )


def _is_shift_persistent(current_dir: float, next_dir: float) -> bool:
    """Check if new direction persists (next reading within 10°)."""
    return abs(angular_distance(current_dir, next_dir)) <= PERSISTENCE_THRESHOLD


@dataclass
class ShiftEvent:
    """A detected persistent wind shift."""
    timestamp: datetime
    buoy_id: str
    baseline_direction: float
    new_direction: float
    magnitude: float
    wind_speed: float
    veering: bool


def detect_shifts(df: pd.DataFrame, buoy_id: str) -> list[ShiftEvent]:
    """Detect persistent wind shifts in buoy time series.

    Args:
        df: DataFrame with timestamp, wind_dir_deg, wind_speed_knots columns
        buoy_id: Identifier for the buoy

    Returns:
        List of detected ShiftEvent objects
    """
    events = []

    # Need at least baseline window + 2 for persistence check
    min_required = BASELINE_WINDOW_SIZE + 2
    if len(df) < min_required:
        return events

    # Track last shift index to avoid double-counting
    last_shift_index = -1

    # Scan through data looking for shifts
    for i in range(BASELINE_WINDOW_SIZE, len(df) - 1):
        # Skip if we just detected a shift
        if i <= last_shift_index + 1:
            continue

        # Calculate baseline from previous readings
        baseline_window = df.iloc[i-BASELINE_WINDOW_SIZE:i]
        baseline_dirs = baseline_window['wind_dir_deg'].tolist()
        baseline_dir = circular_mean(baseline_dirs)

        # Check baseline stability
        if not _is_baseline_stable(baseline_dir, baseline_dirs):
            continue

        # Filter: only process north winds
        if not _is_north_wind(baseline_dir):
            continue

        # Filter: wind speed must be ≥5 knots
        current_speed = df.iloc[i]['wind_speed_knots']
        if current_speed < MIN_WIND_SPEED:
            continue

        # Check current and next reading for shift
        current_dir = df.iloc[i]['wind_dir_deg']
        next_dir = df.iloc[i+1]['wind_dir_deg']

        # Calculate shift magnitude
        shift_magnitude = abs(angular_distance(baseline_dir, current_dir))

        # Check if this is a shift that persists
        if shift_magnitude >= SHIFT_MAGNITUDE_THRESHOLD:
            if _is_shift_persistent(current_dir, next_dir):
                # Determine if veering (clockwise) or backing
                signed_distance = angular_distance(baseline_dir, current_dir)
                veering = signed_distance > 0

                events.append(ShiftEvent(
                    timestamp=df.iloc[i]['timestamp'],
                    buoy_id=buoy_id,
                    baseline_direction=float(baseline_dir),
                    new_direction=float(current_dir),
                    magnitude=float(shift_magnitude),
                    wind_speed=float(df.iloc[i]['wind_speed_knots']),
                    veering=bool(veering)
                ))
                last_shift_index = i

    return events
