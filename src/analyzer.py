"""Reliability metrics and lag analysis for matched shift events."""

import csv
import statistics
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from src.correlator import MatchedEvent


def _get_wind_bucket(wind_speed: float) -> str:
    """Get wind speed bucket name for given wind speed.

    Args:
        wind_speed: Wind speed in knots

    Returns:
        Bucket name: '5-10', '10-15', '15-20', '20+', or empty string if outside range
    """
    if 5 <= wind_speed < 10:
        return '5-10'
    elif 10 <= wind_speed < 15:
        return '10-15'
    elif 15 <= wind_speed < 20:
        return '15-20'
    elif wind_speed >= 20:
        return '20+'
    return ''


def _get_magnitude_bucket(magnitude: float) -> str:
    """Get magnitude bucket name for given shift magnitude.

    Args:
        magnitude: Shift magnitude in degrees

    Returns:
        Bucket name: '10-15', '15-20', '20-25', '25-30', '30+', or empty string if <10°
    """
    if 10 <= magnitude < 15:
        return '10-15'
    elif 15 <= magnitude < 20:
        return '15-20'
    elif 20 <= magnitude < 25:
        return '20-25'
    elif 25 <= magnitude < 30:
        return '25-30'
    elif magnitude >= 30:
        return '30+'
    return ''


def calculate_success_rate(matched_events: list[MatchedEvent]) -> dict:
    """Calculate overall prediction success metrics.

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary with total_events, successful_matches, failed_matches, success_rate
    """
    total = len(matched_events)
    successful = sum(1 for event in matched_events if event.success)
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0.0

    return {
        'total_events': total,
        'successful_matches': successful,
        'failed_matches': failed,
        'success_rate': success_rate
    }


def calculate_lag_statistics_by_windspeed(matched_events: list[MatchedEvent]) -> dict:
    """Calculate lag statistics grouped by wind speed buckets.

    Wind speed buckets: 5-10, 10-15, 15-20, 20+ knots.
    Uses wind speed from Wilmette shift (the predictor).
    Only includes successful matches with non-None lag times.

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary keyed by bucket name ('5-10', '10-15', '15-20', '20+')
        Each bucket contains: count, mean_lag, median_lag, std_lag, min_lag, max_lag
    """
    buckets = {
        '5-10': [],
        '10-15': [],
        '15-20': [],
        '20+': []
    }

    for event in matched_events:
        if not event.success or event.lag_time is None:
            continue

        bucket_name = _get_wind_bucket(event.wilmette_shift.wind_speed)
        if bucket_name:
            buckets[bucket_name].append(event.lag_time)

    result = {}
    for bucket_name, lag_times in buckets.items():
        if len(lag_times) == 0:
            continue

        result[bucket_name] = {
            'count': len(lag_times),
            'mean_lag': statistics.mean(lag_times),
            'median_lag': statistics.median(lag_times),
            'std_lag': statistics.stdev(lag_times) if len(lag_times) > 1 else 0.0,
            'min_lag': min(lag_times),
            'max_lag': max(lag_times)
        }

    return result


def calculate_shift_direction_breakdown(matched_events: list[MatchedEvent]) -> dict:
    """Calculate success rate and average lag by shift direction (veering vs backing).

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary with 'veering' and 'backing' keys
        Each contains: total_events, successful_matches, success_rate, average_lag
    """
    veering_events = [e for e in matched_events if e.wilmette_shift.veering]
    backing_events = [e for e in matched_events if not e.wilmette_shift.veering]

    def calculate_direction_stats(events):
        total = len(events)
        successful = sum(1 for e in events if e.success)
        success_rate = (successful / total * 100) if total > 0 else 0.0

        successful_lags = [e.lag_time for e in events if e.success and e.lag_time is not None]
        average_lag = statistics.mean(successful_lags) if successful_lags else 0.0

        return {
            'total_events': total,
            'successful_matches': successful,
            'success_rate': success_rate,
            'average_lag': average_lag
        }

    return {
        'veering': calculate_direction_stats(veering_events),
        'backing': calculate_direction_stats(backing_events)
    }


def export_reliability_summary(matched_events: list[MatchedEvent], output_path: str):
    """Export reliability summary to CSV file.

    Creates CSV with overall metrics and by-bucket statistics.

    Args:
        matched_events: List of matched events from correlator
        output_path: Path to output CSV file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    overall = calculate_success_rate(matched_events)
    by_bucket = calculate_lag_statistics_by_windspeed(matched_events)

    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'metric', 'total_events', 'successful_matches', 'failed_matches',
            'success_rate', 'count', 'mean_lag', 'median_lag', 'std_lag',
            'min_lag', 'max_lag'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Write overall metrics
        writer.writerow({
            'metric': 'overall',
            'total_events': overall['total_events'],
            'successful_matches': overall['successful_matches'],
            'failed_matches': overall['failed_matches'],
            'success_rate': f"{overall['success_rate']:.2f}",
            'count': '',
            'mean_lag': '',
            'median_lag': '',
            'std_lag': '',
            'min_lag': '',
            'max_lag': ''
        })

        # Write bucket statistics
        for bucket_name, stats in by_bucket.items():
            writer.writerow({
                'metric': f'bucket_{bucket_name}',
                'total_events': '',
                'successful_matches': '',
                'failed_matches': '',
                'success_rate': '',
                'count': stats['count'],
                'mean_lag': f"{stats['mean_lag']:.2f}",
                'median_lag': f"{stats['median_lag']:.2f}",
                'std_lag': f"{stats['std_lag']:.2f}",
                'min_lag': stats['min_lag'],
                'max_lag': stats['max_lag']
            })


def generate_lag_histograms(matched_events: list[MatchedEvent], output_dir: str):
    """Generate lag distribution histograms and save as PNG files.

    Creates three plots:
    1. Overall lag distribution
    2. Lag distribution by wind speed bucket (subplots)
    3. Success rate by shift direction (bar chart)

    Args:
        matched_events: List of matched events from correlator
        output_dir: Directory path for output PNG files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract successful lag times
    successful_lags = [e.lag_time for e in matched_events if e.success and e.lag_time is not None]

    # Plot 1: Overall lag distribution
    if successful_lags:
        plt.figure(figsize=(10, 6))
        plt.hist(successful_lags, bins=12, edgecolor='black', alpha=0.7)
        plt.xlabel('Lag Time (minutes)')
        plt.ylabel('Frequency')
        plt.title('Overall Lag Distribution')
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(output_path / "lag_distribution_overall.png", dpi=150, bbox_inches='tight')
        plt.close()

    # Plot 2: Lag distribution by wind speed bucket
    by_bucket = calculate_lag_statistics_by_windspeed(matched_events)
    if by_bucket:
        bucket_order = ['5-10', '10-15', '15-20', '20+']
        available_buckets = [b for b in bucket_order if b in by_bucket]

        if available_buckets:
            fig, axes = plt.subplots(len(available_buckets), 1, figsize=(10, 4 * len(available_buckets)))
            if len(available_buckets) == 1:
                axes = [axes]

            for ax, bucket_name in zip(axes, available_buckets):
                bucket_lags = [e.lag_time for e in matched_events
                              if e.success and e.lag_time is not None
                              and _get_wind_bucket(e.wilmette_shift.wind_speed) == bucket_name]

                ax.hist(bucket_lags, bins=10, edgecolor='black', alpha=0.7)
                ax.set_xlabel('Lag Time (minutes)')
                ax.set_ylabel('Frequency')
                ax.set_title(f'Lag Distribution: {bucket_name} knots')
                ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()
            plt.savefig(output_path / "lag_distribution_by_windspeed.png", dpi=150, bbox_inches='tight')
            plt.close()

    # Plot 3: Success rate by shift direction
    direction_stats = calculate_shift_direction_breakdown(matched_events)
    if direction_stats:
        directions = ['Veering', 'Backing']
        success_rates = [
            direction_stats['veering']['success_rate'],
            direction_stats['backing']['success_rate']
        ]

        plt.figure(figsize=(8, 6))
        bars = plt.bar(directions, success_rates, edgecolor='black', alpha=0.7)
        plt.ylabel('Success Rate (%)')
        plt.title('Success Rate by Shift Direction')
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.1f}%',
                    ha='center', va='bottom')

        plt.savefig(output_path / "success_by_shift_direction.png", dpi=150, bbox_inches='tight')
        plt.close()


def calculate_success_rate_by_magnitude(matched_events: list[MatchedEvent]) -> dict:
    """Calculate success rate grouped by Wilmette shift magnitude in 5° buckets.

    Buckets: 10-15°, 15-20°, 20-25°, 25-30°, 30+°

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary keyed by bucket name ('10-15', '15-20', etc.)
        Each bucket contains: count, successful, success_rate
    """
    buckets = {
        '10-15': [],
        '15-20': [],
        '20-25': [],
        '25-30': [],
        '30+': []
    }

    for event in matched_events:
        bucket_name = _get_magnitude_bucket(event.wilmette_shift.magnitude)
        if bucket_name:
            buckets[bucket_name].append(event)

    result = {}
    for bucket_name, events in buckets.items():
        if len(events) == 0:
            continue

        successful = sum(1 for e in events if e.success)
        success_rate = (successful / len(events) * 100) if len(events) > 0 else 0.0

        result[bucket_name] = {
            'count': len(events),
            'successful': successful,
            'success_rate': success_rate
        }

    return result


def calculate_magnitude_lag_correlation(matched_events: list[MatchedEvent]) -> dict:
    """Calculate Pearson correlation between Wilmette magnitude and lag time.

    Only includes successful matches with non-None lag times.

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary with correlation, p_value, and data_points [(magnitude, lag)]
    """
    # Extract successful events with lag times
    data_points = []
    for event in matched_events:
        if event.success and event.lag_time is not None:
            data_points.append((event.wilmette_shift.magnitude, event.lag_time))

    if len(data_points) < 2:
        return {
            'correlation': 0.0,
            'p_value': 1.0,
            'data_points': data_points
        }

    magnitudes = [p[0] for p in data_points]
    lag_times = [p[1] for p in data_points]

    correlation, p_value = stats.pearsonr(magnitudes, lag_times)

    return {
        'correlation': correlation,
        'p_value': p_value,
        'data_points': data_points
    }


def calculate_magnitude_correlation(matched_events: list[MatchedEvent]) -> dict:
    """Calculate Pearson correlation and linear regression between Wilmette and Chicago magnitudes.

    Only includes successful matches.

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Dictionary with correlation, p_value, slope, intercept, and data_points [(wilmette_mag, chicago_mag)]
    """
    # Extract successful events
    data_points = []
    for event in matched_events:
        if event.success and event.chicago_shift is not None:
            data_points.append((event.wilmette_shift.magnitude, event.chicago_shift.magnitude))

    if len(data_points) < 2:
        return {
            'correlation': 0.0,
            'p_value': 1.0,
            'slope': 0.0,
            'intercept': 0.0,
            'data_points': data_points
        }

    wilmette_magnitudes = [p[0] for p in data_points]
    chicago_magnitudes = [p[1] for p in data_points]

    correlation, p_value = stats.pearsonr(wilmette_magnitudes, chicago_magnitudes)
    regression = stats.linregress(wilmette_magnitudes, chicago_magnitudes)

    return {
        'correlation': correlation,
        'p_value': p_value,
        'slope': regression.slope,
        'intercept': regression.intercept,
        'data_points': data_points
    }


def find_magnitude_threshold(matched_events: list[MatchedEvent], target_rate: float = 80.0) -> float | None:
    """Find minimum Wilmette magnitude where cumulative success rate exceeds target threshold.

    Uses cumulative approach: for each magnitude X, calculates success rate for all shifts >= X.
    Returns the minimum magnitude where success rate first exceeds target_rate.

    Args:
        matched_events: List of matched events from correlator
        target_rate: Target success rate percentage (default 80.0)

    Returns:
        Minimum magnitude threshold in degrees, or None if target never reached
    """
    if not matched_events:
        return None

    # Get all unique magnitudes, sorted
    magnitudes = sorted(set(event.wilmette_shift.magnitude for event in matched_events))

    # For each magnitude threshold, calculate cumulative success rate
    for threshold_magnitude in magnitudes:
        events_above_threshold = [
            event for event in matched_events
            if event.wilmette_shift.magnitude >= threshold_magnitude
        ]

        if not events_above_threshold:
            continue

        successful = sum(1 for event in events_above_threshold if event.success)
        success_rate = (successful / len(events_above_threshold)) * 100

        if success_rate >= target_rate:
            return threshold_magnitude

    return None


def export_magnitude_correlations(matched_events: list[MatchedEvent], output_path: str):
    """Export magnitude correlation metrics to CSV file.

    Includes:
    - Magnitude vs lag correlation
    - Wilmette vs Chicago magnitude correlation
    - Magnitude threshold for 80% success rate
    - Binned success rates by magnitude

    Args:
        matched_events: List of matched events from correlator
        output_path: Path to output CSV file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    mag_lag_corr = calculate_magnitude_lag_correlation(matched_events)
    mag_corr = calculate_magnitude_correlation(matched_events)
    threshold = find_magnitude_threshold(matched_events, target_rate=80.0)
    by_magnitude = calculate_success_rate_by_magnitude(matched_events)

    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'metric', 'value', 'p_value', 'slope', 'intercept',
            'count', 'successful', 'success_rate'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Write magnitude-lag correlation
        writer.writerow({
            'metric': 'magnitude_lag_correlation',
            'value': f"{mag_lag_corr['correlation']:.4f}",
            'p_value': f"{mag_lag_corr['p_value']:.4f}",
            'slope': '',
            'intercept': '',
            'count': '',
            'successful': '',
            'success_rate': ''
        })

        # Write Wilmette-Chicago magnitude correlation
        writer.writerow({
            'metric': 'wilmette_chicago_magnitude_correlation',
            'value': f"{mag_corr['correlation']:.4f}",
            'p_value': f"{mag_corr['p_value']:.4f}",
            'slope': f"{mag_corr['slope']:.4f}",
            'intercept': f"{mag_corr['intercept']:.4f}",
            'count': '',
            'successful': '',
            'success_rate': ''
        })

        # Write magnitude threshold
        writer.writerow({
            'metric': 'magnitude_threshold_80pct',
            'value': f"{threshold:.1f}" if threshold is not None else 'None',
            'p_value': '',
            'slope': '',
            'intercept': '',
            'count': '',
            'successful': '',
            'success_rate': ''
        })

        # Write binned success rates
        for bucket_name, stats in by_magnitude.items():
            writer.writerow({
                'metric': f'bucket_{bucket_name}',
                'value': '',
                'p_value': '',
                'slope': '',
                'intercept': '',
                'count': stats['count'],
                'successful': stats['successful'],
                'success_rate': f"{stats['success_rate']:.2f}"
            })


def generate_magnitude_plots(matched_events: list[MatchedEvent], output_dir: str):
    """Generate magnitude correlation scatter plots and save as PNG files.

    Creates three plots:
    1. Magnitude vs success rate (by 5° buckets)
    2. Magnitude vs lag time
    3. Wilmette magnitude vs Chicago magnitude

    Args:
        matched_events: List of matched events from correlator
        output_dir: Directory path for output PNG files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Plot 1: Magnitude vs success rate
    by_magnitude = calculate_success_rate_by_magnitude(matched_events)
    if by_magnitude:
        bucket_order = ['10-15', '15-20', '20-25', '25-30', '30+']
        available_buckets = [b for b in bucket_order if b in by_magnitude]

        if available_buckets:
            bucket_labels = available_buckets
            success_rates = [by_magnitude[b]['success_rate'] for b in available_buckets]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(bucket_labels)), success_rates, edgecolor='black', alpha=0.7)
            plt.xticks(range(len(bucket_labels)), bucket_labels)
            plt.xlabel('Shift Magnitude (degrees)')
            plt.ylabel('Success Rate (%)')
            plt.title('Prediction Success Rate by Shift Magnitude')
            plt.ylim(0, 100)
            plt.grid(axis='y', alpha=0.3)

            # Add value labels on bars
            for i, (bar, rate) in enumerate(zip(bars, success_rates)):
                height = bar.get_height()
                plt.text(i, height, f'{rate:.1f}%', ha='center', va='bottom')

            plt.savefig(output_path / "magnitude_vs_success.png", dpi=150, bbox_inches='tight')
            plt.close()

    # Plot 2: Magnitude vs lag time
    mag_lag_data = calculate_magnitude_lag_correlation(matched_events)
    if mag_lag_data['data_points']:
        magnitudes = [p[0] for p in mag_lag_data['data_points']]
        lag_times = [p[1] for p in mag_lag_data['data_points']]

        plt.figure(figsize=(10, 6))
        plt.scatter(magnitudes, lag_times, alpha=0.6, edgecolor='black')
        plt.xlabel('Wilmette Shift Magnitude (degrees)')
        plt.ylabel('Lag Time (minutes)')
        plt.title(f'Shift Magnitude vs Lag Time (r={mag_lag_data["correlation"]:.3f})')
        plt.grid(alpha=0.3)
        plt.savefig(output_path / "magnitude_vs_lag.png", dpi=150, bbox_inches='tight')
        plt.close()

    # Plot 3: Wilmette vs Chicago magnitude
    mag_corr_data = calculate_magnitude_correlation(matched_events)
    if mag_corr_data['data_points']:
        wilmette_mags = [p[0] for p in mag_corr_data['data_points']]
        chicago_mags = [p[1] for p in mag_corr_data['data_points']]

        plt.figure(figsize=(10, 6))
        plt.scatter(wilmette_mags, chicago_mags, alpha=0.6, edgecolor='black')

        # Add regression line
        if len(wilmette_mags) >= 2:
            slope = mag_corr_data['slope']
            intercept = mag_corr_data['intercept']
            x_line = [min(wilmette_mags), max(wilmette_mags)]
            y_line = [slope * x + intercept for x in x_line]
            plt.plot(x_line, y_line, 'r--', alpha=0.8, label=f'y = {slope:.2f}x + {intercept:.2f}')
            plt.legend()

        plt.xlabel('Wilmette Shift Magnitude (degrees)')
        plt.ylabel('Chicago Shift Magnitude (degrees)')
        plt.title(f'Wilmette vs Chicago Shift Magnitude (r={mag_corr_data["correlation"]:.3f})')
        plt.grid(alpha=0.3)
        plt.savefig(output_path / "wilmette_vs_chicago_magnitude.png", dpi=150, bbox_inches='tight')
        plt.close()
