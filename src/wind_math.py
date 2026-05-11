"""Circular statistics for wind direction analysis."""
import math


def _unit_vector_components(angles: list[float]) -> tuple[float, float]:
    """Calculate sum of unit vector components for circular statistics.

    Args:
        angles: List of angles in degrees

    Returns:
        Tuple of (sin_sum, cos_sum)
    """
    radians = [math.radians(a) for a in angles]
    sin_sum = sum(math.sin(r) for r in radians)
    cos_sum = sum(math.cos(r) for r in radians)
    return sin_sum, cos_sum


def angular_distance(a: float, b: float) -> float:
    """Calculate signed angular distance from a to b.

    Args:
        a: Starting angle in degrees (0-360)
        b: Ending angle in degrees (0-360)

    Returns:
        Signed distance in degrees (-180 to +180).
        Positive values indicate clockwise rotation.
    """
    diff = b - a
    # Normalize to -180 to +180 range
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return diff


def circular_mean(angles: list[float]) -> float:
    """Calculate circular mean of angles using unit vector method.

    Args:
        angles: List of angles in degrees (0-360)

    Returns:
        Circular mean in degrees (0-360)
    """
    sin_sum, cos_sum = _unit_vector_components(angles)

    # Convert back to degrees
    mean_rad = math.atan2(sin_sum, cos_sum)
    mean_deg = math.degrees(mean_rad)

    # Normalize to 0-360 range
    if mean_deg < 0:
        mean_deg += 360

    return mean_deg


def circular_variance(angles: list[float]) -> float:
    """Calculate circular variance measuring angular dispersion.

    Args:
        angles: List of angles in degrees (0-360)

    Returns:
        Circular variance (0 to 1).
        0 = all angles identical (no dispersion)
        1 = uniformly distributed (maximum dispersion)
    """
    sin_sum, cos_sum = _unit_vector_components(angles)

    n = len(angles)
    # Mean resultant length R
    R = math.sqrt(sin_sum**2 + cos_sum**2) / n

    # Circular variance = 1 - R
    return 1 - R
