# Flood event identification scripts

This folder contains cleaned scripts for identifying return-period flood events
from CaMa-Flood ensemble P50 river storage.

## Files

### storage_event_utils.py

Common functions for reading daily P50 storage binary files, computing annual
maximum storage, rasterizing administrative boundaries, fitting Gumbel thresholds,
and constructing administrative-unit by year flood event indicators.

### 01_build_county_return_period_events_storage.py

County-level return-period flood event identification.

Main logic:

```text
daily ensemble P50 storage
-> grid-level annual maximum storage
-> grid-level Gumbel return-period thresholds
-> county-year flood event indicators
```

Event rule:

```text
A county-year is coded as exposed if any valid grid cell inside the county
exceeds the corresponding T-year storage threshold.
```

### 02_build_city_return_period_events_storage_ruleC1.py

City-level return-period flood event identification using rule C1.

Main logic:

```text
daily ensemble P50 storage
-> grid-level annual maximum storage
-> D1 dry-pixel filtering
-> city-level area-weighted annual maximum storage
-> D2 dry-city filtering
-> city-level Gumbel return-period thresholds
-> city-year flood event indicators
```

## Notes

Raw CaMa-Flood outputs, administrative boundary shapefiles, and restricted
microdata are not included.

Before public release, hard-coded local paths can be replaced by a configuration
file or command-line arguments.
