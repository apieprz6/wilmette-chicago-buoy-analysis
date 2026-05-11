"""Visual case studies and decision table generation for racing intelligence."""

import statistics
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from pathlib import Path
from src.correlator import MatchedEvent


def _get_wind_bucket(wind_speed: float) -> str:
    """Get wind speed bucket name."""
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
    """Get magnitude bucket name."""
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


def select_best_matches(matched_events: list[MatchedEvent], count: int = 3) -> list[MatchedEvent]:
    """Select best matching events by shortest lag time and strong wind conditions.

    Args:
        matched_events: List of matched events from correlator
        count: Number of best matches to return

    Returns:
        List of top matched events sorted by shortest lag, then strongest wind
    """
    # Filter to successful matches only
    successful = [e for e in matched_events if e.success and e.lag_time is not None]

    # Sort by lag time (shortest first), then wind speed (strongest first)
    sorted_events = sorted(successful, key=lambda e: (e.lag_time, -e.wilmette_shift.wind_speed))

    return sorted_events[:count]


def select_failure_cases(matched_events: list[MatchedEvent], count: int = 3) -> list[MatchedEvent]:
    """Select failure cases with strongest Wilmette shifts.

    Args:
        matched_events: List of matched events from correlator
        count: Number of failure cases to return

    Returns:
        List of failed matches sorted by strongest Wilmette shift magnitude
    """
    # Filter to unsuccessful matches only
    failures = [e for e in matched_events if not e.success]

    # Sort by magnitude (largest first), then wind speed (strongest first)
    sorted_events = sorted(failures, key=lambda e: (-e.wilmette_shift.magnitude, -e.wilmette_shift.wind_speed))

    return sorted_events[:count]


def generate_case_study_plot(matched_event: MatchedEvent, wilmette_df: pd.DataFrame,
                             chicago_df: pd.DataFrame, output_path: str):
    """Generate time-series overlay plot for a case study event.

    Creates 3-hour window centered on Wilmette shift with both buoys on same axes.

    Args:
        matched_event: The matched event to visualize
        wilmette_df: Wilmette buoy time-series (timestamp, wind_dir_deg, wind_speed_knots)
        chicago_df: Chicago buoy time-series (timestamp, wind_dir_deg, wind_speed_knots)
        output_path: Path to save PNG file
    """
    shift_time = matched_event.wilmette_shift.timestamp

    # 3-hour window: 1.5 hours before and after shift
    window_start = shift_time - timedelta(hours=1.5)
    window_end = shift_time + timedelta(hours=1.5)

    # Filter dataframes to window
    w_window = wilmette_df[
        (wilmette_df['timestamp'] >= window_start) &
        (wilmette_df['timestamp'] <= window_end)
    ].copy()

    c_window = chicago_df[
        (chicago_df['timestamp'] >= window_start) &
        (chicago_df['timestamp'] <= window_end)
    ].copy()

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot both buoys
    ax.plot(w_window['timestamp'], w_window['wind_dir_deg'],
            label='Wilmette', linewidth=2, marker='o', markersize=4)
    ax.plot(c_window['timestamp'], c_window['wind_dir_deg'],
            label='Chicago', linewidth=2, marker='s', markersize=4)

    # Mark Wilmette shift
    ax.axvline(shift_time, color='red', linestyle='--', linewidth=2,
               label=f'Wilmette shift ({matched_event.wilmette_shift.magnitude:.0f}°)')

    # Mark Chicago shift if matched
    if matched_event.chicago_shift:
        chicago_shift_time = matched_event.chicago_shift.timestamp
        ax.axvline(chicago_shift_time, color='blue', linestyle='--', linewidth=2,
                  label=f'Chicago shift (lag: {matched_event.lag_time} min)')

    ax.set_xlabel('Time')
    ax.set_ylabel('Wind Direction (degrees)')
    ax.set_title(f'Case Study: {shift_time.strftime("%Y-%m-%d %H:%M")}')
    ax.legend()
    ax.grid(alpha=0.3)

    # Save plot
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()


def generate_decision_table(matched_events: list[MatchedEvent]) -> str:
    """Generate markdown decision table: wind speed × shift magnitude.

    Rows are wind speed buckets, columns are magnitude buckets.
    Cells contain success rate and average lag.

    Args:
        matched_events: List of matched events from correlator

    Returns:
        Markdown formatted table string
    """
    # Build data structure: {(wind_bucket, mag_bucket): [events]}
    cell_data = {}

    for event in matched_events:
        wind_bucket = _get_wind_bucket(event.wilmette_shift.wind_speed)
        mag_bucket = _get_magnitude_bucket(event.wilmette_shift.magnitude)

        if not wind_bucket or not mag_bucket:
            continue

        key = (wind_bucket, mag_bucket)
        if key not in cell_data:
            cell_data[key] = []
        cell_data[key].append(event)

    # Define bucket orders
    wind_buckets = ['5-10', '10-15', '15-20', '20+']
    mag_buckets = ['10-15', '15-20', '20-25', '25-30', '30+']

    # Build markdown table
    lines = []

    # Header
    header = '| Wind Speed (kt) | ' + ' | '.join(mag_buckets) + ' |'
    lines.append(header)
    separator = '|' + '---|' * (len(mag_buckets) + 1)
    lines.append(separator)

    # Data rows
    for wind_bucket in wind_buckets:
        row = [f'**{wind_bucket}**']

        for mag_bucket in mag_buckets:
            key = (wind_bucket, mag_bucket)
            if key in cell_data:
                events = cell_data[key]
                total = len(events)
                successful = sum(1 for e in events if e.success)
                success_rate = (successful / total * 100) if total > 0 else 0.0

                # Calculate average lag for successful matches
                lags = [e.lag_time for e in events if e.success and e.lag_time is not None]
                avg_lag = statistics.mean(lags) if lags else 0.0

                cell = f'{success_rate:.0f}% ({avg_lag:.0f} min)'
            else:
                cell = '—'

            row.append(cell)

        lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(lines)


def generate_findings_report(matched_events: list[MatchedEvent], decision_table_md: str,
                             case_study_dir: str, output_path: str):
    """Generate complete findings report with all analysis sections.

    Args:
        matched_events: List of matched events from correlator
        decision_table_md: Pre-generated decision table markdown
        case_study_dir: Directory path where case study plots are stored
        output_path: Path to save findings report markdown file
    """
    # Calculate headline metrics
    total = len(matched_events)
    successful = sum(1 for e in matched_events if e.success)
    success_rate = (successful / total * 100) if total > 0 else 0.0

    successful_lags = [e.lag_time for e in matched_events if e.success and e.lag_time is not None]
    avg_lag = statistics.mean(successful_lags) if successful_lags else 0.0
    median_lag = statistics.median(successful_lags) if successful_lags else 0.0

    # Build report sections
    lines = []
    lines.append('# Wilmette-Chicago Buoy Shift Analysis: Findings Report')
    lines.append('')
    lines.append('## Headline Metrics')
    lines.append('')
    lines.append(f'- **Overall Success Rate**: {success_rate:.1f}%')
    lines.append(f'- **Total Shifts Analyzed**: {total}')
    lines.append(f'- **Successful Matches**: {successful}')
    lines.append(f'- **Average Lag**: {avg_lag:.1f} minutes')
    lines.append(f'- **Median Lag**: {median_lag:.1f} minutes')
    lines.append('')
    lines.append('## Decision Table')
    lines.append('')
    lines.append('Expected success rate and average lag by wind conditions:')
    lines.append('')
    lines.append(decision_table_md)
    lines.append('')
    lines.append('## Case Studies')
    lines.append('')
    lines.append('### Best Matches')
    lines.append('')
    lines.append('Examples of successful shift predictions:')
    lines.append('')
    lines.append('- `best_match_001.png` - Shortest lag, strong conditions')
    lines.append('- `best_match_002.png` - High directional accuracy')
    lines.append('- `best_match_003.png` - Consistent tracking')
    lines.append('')
    lines.append('### Failure Cases')
    lines.append('')
    lines.append('Examples where Wilmette shift did not propagate to Chicago:')
    lines.append('')
    lines.append('- `failure_001.png` - Strong Wilmette shift, no Chicago response')
    lines.append('- `failure_002.png` - Local phenomenon, failed correlation')
    lines.append('- `failure_003.png` - Timing mismatch')
    lines.append('')
    lines.append('## Tactical Recommendations')
    lines.append('')
    lines.append('### When to Trust the Signal')
    lines.append('')
    lines.append('- **Strong winds (15+ knots)**: Higher success rates and faster propagation')
    lines.append('- **Large shifts (20+ degrees)**: More reliable signal, easier to detect')
    lines.append('- **Expect 10-15 minute lag**: Chicago typically follows Wilmette within this window')
    lines.append('')
    lines.append('### When to Be Cautious')
    lines.append('')
    lines.append('- **Light winds (<10 knots)**: Lower success rates, more variability')
    lines.append('- **Small shifts (<15 degrees)**: May be noise rather than persistent shift')
    lines.append('- **After 30 minutes**: If no Chicago response by then, shift may be local to Wilmette')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('*Case study plots available in `' + case_study_dir + '/`*')

    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('\n'.join(lines))
