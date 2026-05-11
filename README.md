# Wilmette-Chicago Buoy Wind Shift Prediction Analysis

Can wind shifts observed at the Wilmette Harbor buoy (17 miles north) predict shifts at the Chicago buoy during sailboat races? This analysis uses 4+ years of NOAA buoy data (2021-2025) to answer whether the "Wilmette oracle" is reliable enough to inform tactical racing decisions.

## Research Question

**Primary:** When Wilmette Harbor (NDBC 45174) experiences a persistent wind shift during north wind conditions, does Chicago (NDBC 45198) experience a similar shift within 60 minutes?

**Tactical Context:** Races last 60-90 minutes. If Wilmette shifts can predict Chicago shifts with known lag times, racers can make proactive tactical decisions (tack early, position for the new wind) rather than reacting after the shift arrives.

## What This Analysis Does

1. **Detects persistent wind shifts** at both buoys using circular statistics
   - Filters for north winds (315-045°) and wind speed ≥5 knots
   - Identifies shifts ≥10° from stable 2-hour baseline
   - Requires 20-minute persistence to exclude temporary fluctuations

2. **Correlates shift events** between Wilmette and Chicago
   - Matches Wilmette shifts to Chicago shifts within 60-minute window
   - Validates directional consistency (±15° tolerance)
   - Measures lag time and reliability

3. **Quantifies prediction reliability** by wind conditions
   - Overall success rate and confidence metrics
   - Lag time distribution by wind speed bucket
   - Magnitude correlation (does Wilmette shift size predict Chicago shift size?)
   - Case studies showing successful predictions and failure modes

## Key Findings

📊 **View the complete analysis in:** [`notebooks/03_correlation_analysis.ipynb`](notebooks/03_correlation_analysis.ipynb)

Key results and visualizations are available in the [`results/`](results/) directory, including:

- Statistical correlation metrics
- Case study visualizations (successful predictions and failures)
- Magnitude relationship plots
- Detailed findings summary in [`results/FINDINGS.md`](results/FINDINGS.md)

## Repository Structure

```
├── notebooks/
│   ├── 01_data_exploration.ipynb       # Load and validate buoy data
│   ├── 02_shift_detection.ipynb        # Detect persistent shifts at each buoy
│   └── 03_correlation_analysis.ipynb   # Correlate shifts, analyze reliability (START HERE)
├── src/                                # Core analysis modules (tested)
│   ├── buoy_loader.py                  # Parse NDBC text files
│   ├── wind_math.py                    # Circular statistics (angular distance, means)
│   ├── shift_detector.py               # Persistent shift detection algorithm
│   ├── correlator.py                   # Match Wilmette → Chicago shift pairs
│   ├── analyzer.py                     # Statistical analysis and metrics
│   └── visualizer.py                   # Report generation
├── tests/                              # Unit tests (pytest)
├── data/raw/                           # NOAA buoy historical data (2021-2025)
│   ├── wilmette/                       # NDBC 45174
│   └── chicago/                        # NDBC 45198
└── results/
    ├── FINDINGS.md                     # Summary of key findings
    ├── case_studies/                   # Visual case studies
    └── *.png                           # Correlation plots and statistics
```

## Running the Analysis

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Main dependencies: pandas, numpy, matplotlib, scipy, pytest
```

### Reproduce the Analysis

1. **Data exploration:** [`notebooks/01_data_exploration.ipynb`](notebooks/01_data_exploration.ipynb)
   - Load NDBC buoy data, inspect structure, validate completeness

2. **Shift detection:** [`notebooks/02_shift_detection.ipynb`](notebooks/02_shift_detection.ipynb)
   - Apply shift detection algorithm, visualize detected events

3. **Correlation analysis:** [`notebooks/03_correlation_analysis.ipynb`](notebooks/03_correlation_analysis.ipynb) ⭐ **START HERE**
   - Run full correlation analysis, generate reliability metrics, create visualizations

All notebooks import tested modules from `src/` — core logic is not duplicated in notebook cells.

### Run Tests

```bash
pytest tests/
```

Tested modules: `wind_math`, `shift_detector`, `buoy_loader`, `correlator` (>90% coverage)

## Methodology

**Algorithm Parameters** (derived from tactical racing requirements):

- **North wind filter:** 315-045° (geometry where Wilmette is upwind of Chicago)
- **Minimum shift magnitude:** 10° (tactically significant change)
- **Persistence requirement:** 20 minutes (filters out temporary fluctuations)
- **Baseline window:** 2 hours with ±10° stability
- **Wind speed filter:** ≥5 knots (excludes unreliable low-wind readings)
- **Prediction match tolerance:** ±15° directional agreement
- **Maximum lag window:** 60 minutes (race-relevant timeframe)

**Key Techniques:**

- **Circular statistics** for wind direction (355° and 5° are 10° apart, not 350°)
- **Baseline stability validation** to detect shifts from coherent patterns, not oscillations
- **Time-windowed correlation** to match Wilmette shifts to subsequent Chicago shifts
- **Wind speed bucketization** (5-10, 10-15, 15-20, 20+ knots) for lag analysis
- **Magnitude correlation analysis** to identify confidence thresholds

## Data Sources

**NOAA National Data Buoy Center (NDBC)** - Historical observations (2021-2025, May-November deployment seasons):

- **Wilmette Harbor (45174):** https://www.ndbc.noaa.gov/station_page.php?station=45174
- **Chicago (45198):** https://www.ndbc.noaa.gov/station_page.php?station=45198

10-minute interval readings of wind direction, wind speed, and other meteorological variables. Analysis uses paired observations only (both buoys must have complete data).

## Out of Scope

This analysis explicitly excludes:

- HRRR forecast data integration (future enhancement)
- Real-time monitoring/alerting system (race-day tool is future work)
- Statistical significance testing (p-values, hypothesis tests)
- Machine learning models (this is rule-based correlation analysis)
- Wind directions other than north (315-045°)
- Wave or current data
- Interactive dashboards (static reports and notebooks only)

## License

Data provided by NOAA NDBC (public domain).

## Questions?

For questions about the methodology or findings, please open an issue or review the detailed analysis in [`notebooks/03_correlation_analysis.ipynb`](notebooks/03_correlation_analysis.ipynb).
