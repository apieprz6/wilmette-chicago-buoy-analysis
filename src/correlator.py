"""Correlate Wilmette shifts to Chicago shifts."""

from dataclasses import dataclass
from src.shift_detector import ShiftEvent
from src.wind_math import angular_distance

# Correlation criteria
MAX_LAG_MINUTES = 60
DIRECTION_TOLERANCE = 15.0  # degrees


@dataclass
class MatchedEvent:
    """A Wilmette shift matched (or not) to a Chicago shift."""
    wilmette_shift: ShiftEvent
    chicago_shift: ShiftEvent | None
    lag_time: int | None  # minutes
    success: bool
    magnitude_error: float  # difference in shift magnitudes (degrees)


def correlate_shifts(wilmette_shifts: list[ShiftEvent],
                    chicago_shifts: list[ShiftEvent]) -> list[MatchedEvent]:
    """Match Wilmette shifts to corresponding Chicago shifts.

    Matches based on shift BEHAVIOR (veering/backing + magnitude), not absolute
    wind directions. Both buoys must shift in the same rotational direction
    (both veering or both backing) with magnitudes within ±15°.

    Args:
        wilmette_shifts: List of detected shifts at Wilmette buoy
        chicago_shifts: List of detected shifts at Chicago buoy

    Returns:
        List of MatchedEvent objects, one per Wilmette shift
    """
    results = []

    for wilmette in wilmette_shifts:
        chicago_match = None
        min_lag = None

        for chicago in chicago_shifts:
            lag_seconds = (chicago.timestamp - wilmette.timestamp).total_seconds()
            lag_minutes = int(lag_seconds / 60)

            if lag_minutes < 0 or lag_minutes > MAX_LAG_MINUTES:
                continue

            # Must shift in same rotational direction (both veer OR both back)
            if wilmette.veering != chicago.veering:
                continue

            # Shift magnitudes must be within tolerance
            magnitude_error = abs(wilmette.magnitude - chicago.magnitude)
            if magnitude_error > DIRECTION_TOLERANCE:
                continue

            if min_lag is None or lag_minutes < min_lag:
                chicago_match = chicago
                min_lag = lag_minutes

        if chicago_match:
            magnitude_error = abs(wilmette.magnitude - chicago_match.magnitude)
            results.append(MatchedEvent(
                wilmette_shift=wilmette,
                chicago_shift=chicago_match,
                lag_time=min_lag,
                success=True,
                magnitude_error=magnitude_error
            ))
        else:
            results.append(MatchedEvent(
                wilmette_shift=wilmette,
                chicago_shift=None,
                lag_time=None,
                success=False,
                magnitude_error=0.0
            ))

    return results
