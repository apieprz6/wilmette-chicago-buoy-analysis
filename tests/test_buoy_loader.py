import pytest
import pandas as pd
from pathlib import Path


def test_load_buoy_data_returns_dataframe():
    """Can load a buoy file and return a DataFrame"""
    from src.buoy_loader import load_buoy_data

    # Use a real data file from the test data
    test_file = Path(__file__).parent.parent / "data" / "raw" / "wilmette" / "45174h2024.txt"

    df = load_buoy_data(str(test_file))

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_creates_timestamp_column():
    """Combines date/time columns into a single timestamp"""
    from src.buoy_loader import load_buoy_data

    test_file = Path(__file__).parent.parent / "data" / "raw" / "wilmette" / "45174h2024.txt"
    df = load_buoy_data(str(test_file))

    assert 'timestamp' in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
    # Check first row is 2024-05-09 17:40
    assert df.iloc[0]['timestamp'] == pd.Timestamp('2024-05-09 17:40:00')


def test_converts_wind_speed_to_knots():
    """Wind speed converted from m/s to knots (multiply by 1.94384)"""
    from src.buoy_loader import load_buoy_data

    test_file = Path(__file__).parent.parent / "data" / "raw" / "wilmette" / "45174h2024.txt"
    df = load_buoy_data(str(test_file))

    # First row: WSPD=7.0 m/s, GST=9.3 m/s
    # Expected: 7.0 * 1.94384 = 13.61 knots, 9.3 * 1.94384 = 18.08 knots
    assert 'wind_speed_knots' in df.columns
    assert 'gust_speed_knots' in df.columns
    assert abs(df.iloc[0]['wind_speed_knots'] - 13.61) < 0.01
    assert abs(df.iloc[0]['gust_speed_knots'] - 18.08) < 0.01


def test_replaces_missing_value_sentinels_with_nan():
    """Missing value sentinels (99.00, 999.0) replaced with NaN"""
    from src.buoy_loader import load_buoy_data
    import numpy as np

    test_file = Path(__file__).parent.parent / "data" / "raw" / "wilmette" / "45174h2024.txt"
    df = load_buoy_data(str(test_file))

    # First row has VIS=99.0 and TIDE=99.00 which should become NaN
    assert pd.isna(df.iloc[0]['VIS'])
    assert pd.isna(df.iloc[0]['TIDE'])

    # APD column has 99.00 sentinels
    assert df['APD'].isna().any()

    # MWD has 999 sentinel (row 29 has MWD=999)
    assert df['MWD'].isna().any()


def test_creates_wind_direction_column():
    """Wind direction column uses domain glossary name and validates range"""
    from src.buoy_loader import load_buoy_data

    test_file = Path(__file__).parent.parent / "data" / "raw" / "wilmette" / "45174h2024.txt"
    df = load_buoy_data(str(test_file))

    # Should have wind_dir_deg column matching domain glossary
    assert 'wind_dir_deg' in df.columns

    # First row has WDIR=351
    assert df.iloc[0]['wind_dir_deg'] == 351

    # All non-NaN values should be in valid range 0-360
    valid_dirs = df['wind_dir_deg'].dropna()
    assert (valid_dirs >= 0).all()
    assert (valid_dirs <= 360).all()
