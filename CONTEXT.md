# Buoy Wind Shift Analysis - Domain Context

## Purpose

Determine if the Wilmette buoy (45174) can predict wind shifts at the Chicago buoy (45198) during northerly wind conditions, providing tactical advantage in sailboat racing.

## Racing Context

Chicago sailboat races typically last 60-90 minutes for buoy races. Racers consult weather models pre-race for predicted shifts, but real-time observation of shifts starting at the upwind (Wilmette) location could provide competitive advantage for positioning on the race course.

## Geographic Setup

- **Chicago Buoy (45198)**: 41.892°N 87.563°W - race location, downwind/south position
- **Wilmette Buoy (45174)**: 42.135°N 87.655°W - monitoring location, upwind/north position
- **Separation**: ~17 nautical miles north-south

When winds are from the north, weather systems move from Wilmette toward Chicago. This creates a potential leading indicator.

## Glossary

### North Winds
Wind direction in the range 315°-045° (northwest through north to northeast, 90° arc). This directional range allows the Wilmette buoy (positioned north) to observe weather patterns before they reach Chicago (positioned south).

### Persistent Shift
A change in wind direction of ≥10° that maintains the new direction for at least 20 minutes (2+ consecutive buoy readings). Distinguishes meaningful pattern changes from temporary oscillations.

**Significance**: A 10° shift is tactically significant in racing—enough to gain or lose multiple boat positions depending on course positioning.

### Baseline Wind Direction
The stable wind direction regime before a shift occurs. Calculated as the 2-hour moving average (12 readings at 10-minute intervals) preceding a detected shift.

**Stability criterion**: Baseline readings must vary by no more than ±15° to confirm a coherent wind pattern existed before the shift. This was relaxed from the original ±10° to account for natural wind variability over water, which otherwise excluded most shift candidates.

### Shift Magnitude
The angular difference between the baseline wind direction and the new persistent direction, measured in degrees. Always calculated using circular math to properly handle the 0°/360° boundary.

**Categories for analysis**:
- Small: 10-15°
- Moderate: 15-25°  
- Large: >25°

### Prediction Success
A shift event at Wilmette successfully predicts Chicago when:
1. Chicago experiences a shift within 0-60 minutes of Wilmette's shift detection
2. Chicago's shift direction is within ±15° of Wilmette's shift direction
3. Both shifts meet persistence criteria (hold for ≥20 minutes)

**Match tolerance**: The ±15° tolerance accounts for local effects (shoreline, urban heating) while capturing directional correlation.

### Lag Time
The elapsed time between detection of a persistent shift at Wilmette and detection of a corresponding shift at Chicago, measured in minutes.

**Actionable window**: 0-60 minutes. Beyond 60 minutes, races may be finishing and the signal loses tactical value.

### Wind Speed Buckets
Classification of events by wind speed at Wilmette when shift is detected:

- **5-10 knots**: Light air racing conditions
- **10-15 knots**: Moderate conditions, optimal racing, where shift tactics matter most
- **15-20 knots**: Fresh breeze
- **20+ knots**: Strong winds, heavy air

**Filter threshold**: Winds below 5 knots excluded from analysis due to unreliable direction readings from buoy anemometers.

### Shift Direction
The rotational sense of a wind shift:
- **Veering**: Clockwise rotation (e.g., north to northeast)
- **Backing**: Counter-clockwise rotation (e.g., north to northwest)

In northern hemisphere, veering often indicates approaching warm front or increasing pressure; backing often indicates cold front or decreasing pressure.

### Sailing Season
May through November, when buoys are deployed on Lake Michigan. Peak racing activity May-October.

## Data Sources

### NDBC Buoy Data
Standard meteorological buoy observations at 10-minute intervals:
- **WDIR**: Wind direction (degrees true)
- **WSPD**: Wind speed (m/s)
- **GST**: Wind gust (m/s)
- Other: wave height, period, pressure, temperature

**Data period**: 2021-2025 (limited by Chicago buoy deployment history)

**Quality control**: Periods with missing data are excluded from analysis (strict completeness requirement).

## Analysis Objectives

1. **Correlation strength**: What percentage of Wilmette shifts successfully predict Chicago shifts?
2. **Lag distribution**: How long does it typically take for shifts to propagate from Wilmette to Chicago?
3. **Wind speed dependency**: Does lag time vary with wind speed?
4. **Magnitude correlation**: Are larger shifts more predictable? Does shift size affect lag time or success rate?
5. **Tactical intelligence**: Identify scenarios where the Wilmette signal is reliable enough to act on during racing.
