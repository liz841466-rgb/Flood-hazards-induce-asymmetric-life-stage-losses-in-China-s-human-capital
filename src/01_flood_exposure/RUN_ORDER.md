# Flood exposure construction run order

This folder archives code for constructing return-period flood exposure
indicators from hydrodynamic-model outputs.

Recommended review order:

1. `storage_event_utils.py`
   - Shared helper functions for storage-based event construction.
2. `01_build_county_return_period_events_storage.py`
   - County-level return-period flood-event construction.
3. `02_build_city_return_period_events_storage_ruleC1.py`
   - City-level return-period flood-event construction and rule-C1 aggregation.

Scope:

- This folder contains code only.
- Hydrodynamic-model outputs, rasters, NetCDF files, shapefiles, and derived
  exposure-event tables are not included.
