"""Load and parse NDBC buoy data files."""

import pandas as pd
import numpy as np


def load_buoy_data(filepath: str) -> pd.DataFrame:
    """Load NDBC standard meteorological text file into a DataFrame.

    Args:
        filepath: Path to NDBC .txt file

    Returns:
        DataFrame with parsed buoy data
    """
    # Read the file, skipping the header rows
    df = pd.read_csv(
        filepath,
        sep=r'\s+',
        skiprows=2,
        header=None,
        names=['YY', 'MM', 'DD', 'hh', 'mm', 'WDIR', 'WSPD', 'GST', 'WVHT',
               'DPD', 'APD', 'MWD', 'PRES', 'ATMP', 'WTMP', 'DEWP', 'VIS', 'TIDE']
    )

    # Create timestamp column
    df['timestamp'] = pd.to_datetime(df[['YY', 'MM', 'DD', 'hh', 'mm']].rename(
        columns={'YY': 'year', 'MM': 'month', 'DD': 'day', 'hh': 'hour', 'mm': 'minute'}
    ))

    # Convert wind speeds from m/s to knots
    df['wind_speed_knots'] = df['WSPD'] * 1.94384
    df['gust_speed_knots'] = df['GST'] * 1.94384

    # Create wind direction column using domain glossary name
    df['wind_dir_deg'] = df['WDIR']

    # Replace missing value sentinels with NaN
    df = df.replace([99.00, 999.0], np.nan)

    return df
