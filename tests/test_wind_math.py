import pytest
from src.wind_math import angular_distance, circular_mean, circular_variance


def test_angular_distance_wraps_across_zero():
    """355° to 5° should be +10° (clockwise), not +350° or -350°"""
    assert angular_distance(355, 5) == 10


def test_angular_distance_reverse_direction():
    """5° to 355° should be -10° (counter-clockwise)"""
    assert angular_distance(5, 355) == -10


@pytest.mark.parametrize("a,b,expected", [
    # Boundary cases
    (355, 5, 10),      # wrap clockwise across 0°
    (5, 355, -10),     # wrap counter-clockwise across 0°
    (0, 180, 180),     # maximum positive distance
    (180, 0, -180),    # maximum negative distance
    (0, 0, 0),         # same angle

    # Four quadrants
    (45, 90, 45),      # Q1 to Q1 clockwise
    (90, 45, -45),     # Q1 to Q1 counter-clockwise
    (135, 225, 90),    # Q2 to Q3
    (270, 90, -180),   # Q4 to Q1 (both paths equal, returns negative)
    (90, 270, 180),    # Q1 to Q4 (both paths equal, returns positive)

    # All cardinals
    (0, 90, 90),       # N to E
    (90, 180, 90),     # E to S
    (180, 270, 90),    # S to W
    (270, 0, 90),      # W to N (wraps)
])
def test_angular_distance_edge_cases(a, b, expected):
    """Test angular_distance with comprehensive edge cases"""
    assert angular_distance(a, b) == expected


# circular_mean tests


def test_circular_mean_across_zero():
    """Mean of 350° and 10° should be 0°, not 180°"""
    result = circular_mean([350, 10])
    # Result can be 0° or 360° (equivalent)
    assert abs(result - 0) < 0.01 or abs(result - 360) < 0.01


@pytest.mark.parametrize("angles,expected", [
    # Boundary wrapping
    ([350, 10], 0),          # mean across 0°
    ([355, 5, 15], 5),       # three angles across 0°

    # Single angle
    ([90], 90),              # single value returns itself

    # All same angle
    ([45, 45, 45], 45),      # identical angles

    # Cardinal directions
    ([90], 90),              # east
    ([180], 180),            # south
    ([270], 270),            # west

    # Quadrants
    ([30, 60], 45),          # Q1
    ([120, 150], 135),       # Q2
    ([210, 240], 225),       # Q3
    ([300, 330], 315),       # Q4
])
def test_circular_mean_cases(angles, expected):
    """Test circular_mean with various angle combinations"""
    result = circular_mean(angles)
    # Handle 0°/360° equivalence
    if expected == 0:
        assert abs(result - 0) < 0.01 or abs(result - 360) < 0.01
    else:
        assert abs(result - expected) < 0.01


# circular_variance tests


def test_circular_variance_identical_angles():
    """Variance of identical angles should be 0 (no dispersion)"""
    result = circular_variance([45, 45, 45, 45])
    assert abs(result - 0) < 0.01


def test_circular_variance_opposite_angles():
    """Variance of opposite angles should be high (approaching 1)"""
    result = circular_variance([0, 180])
    assert result > 0.9  # Very high dispersion


@pytest.mark.parametrize("angles,expected_low_variance", [
    # Low variance (clustered)
    ([0, 5, 10], True),           # tightly clustered around 0°
    ([350, 355, 0, 5], True),     # clustered across boundary
    ([85, 90, 95], True),         # clustered in Q1

    # High variance (dispersed)
    ([0, 90, 180, 270], False),   # evenly distributed
    ([0, 180], False),            # opposite directions
    ([30, 150, 270], False),      # widely spaced
])
def test_circular_variance_dispersion(angles, expected_low_variance):
    """Test circular_variance distinguishes between clustered and dispersed angles"""
    result = circular_variance(angles)
    if expected_low_variance:
        assert result < 0.2, f"Expected low variance for {angles}, got {result}"
    else:
        assert result > 0.5, f"Expected high variance for {angles}, got {result}"
