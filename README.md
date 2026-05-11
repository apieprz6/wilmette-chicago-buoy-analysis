# Wilmette-Chicago Buoy Analysis

Analysis of wave direction patterns between Wilmette Harbor (NDBC 45174) and Chicago (NDBC 45198) buoys in Lake Michigan. This project investigates whether persistent wave direction shifts at Wilmette Harbor can predict similar shifts at the Chicago buoy.

## Overview

This analysis explores the relationship between wave direction changes at two NOAA buoys:
- **Wilmette Harbor Buoy (45174)**: Located near Wilmette, IL
- **Chicago Buoy (45198)**: Located offshore of Chicago, IL

The primary research question: Can we use persistent wave direction shifts detected at Wilmette to predict corresponding shifts at Chicago?

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
│   ├── 01_data_exploration.ipynb       # Initial data exploration
│   ├── 02_shift_detection.ipynb        # Shift detection methodology
│   └── 03_correlation_analysis.ipynb   # Main analysis (START HERE)
├── data/
│   └── raw/                            # NOAA buoy data files
│       ├── wilmette/                   # 45174 historical data
│       └── chicago/                    # 45198 historical data
├── results/
│   ├── FINDINGS.md                     # Summary of key findings
│   ├── case_studies/                   # Visual case studies
│   └── *.png                           # Correlation plots
├── src/                                # Python analysis modules
└── tests/                              # Unit tests
```

## Setup

### Requirements

```bash
pip install -r requirements.txt
```

Main dependencies:
- pandas
- numpy
- matplotlib
- scipy

### Running the Analysis

1. Clone this repository
2. Install dependencies
3. Open [`notebooks/03_correlation_analysis.ipynb`](notebooks/03_correlation_analysis.ipynb) in Jupyter
4. Run all cells to reproduce the analysis

## Methodology

The analysis uses:
- **Circular statistics** for wave direction analysis (accounting for 359° ↔ 1° wrapping)
- **Persistence thresholds** to detect meaningful directional shifts
- **Cross-correlation** techniques to identify time lags between buoys
- **Statistical validation** to assess prediction reliability

## Data Sources

Historical wave data from NOAA National Data Buoy Center (NDBC):
- Wilmette Harbor: https://www.ndbc.noaa.gov/station_page.php?station=45174
- Chicago: https://www.ndbc.noaa.gov/station_page.php?station=45198

## License

Data provided by NOAA NDBC (public domain).

## Questions?

For questions about the methodology or findings, please open an issue or review the detailed analysis in the notebooks.
