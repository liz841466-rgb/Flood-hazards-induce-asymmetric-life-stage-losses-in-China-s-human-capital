# Elderly-health exposure-linkage code archive

This folder contains archived code for constructing the CHARLS elderly-health
exposure-linked final analysis panel.

The workflow links elderly-health panel data with city-level return-period flood
exposure and rolling exposure windows.

## Summary

- Required exposure-linkage notebooks found: 4
- Required exposure-linkage notebooks missing: 0
- Optional diagnostic/bridge notebooks found: 3
- Optional diagnostic/bridge notebooks missing: 0
- Related notebooks recorded: 8
- Metadata/documentation files copied: 19

## Main files

### `01_prepare_charls_60plus_health_panel.py`

Archived code cells for constructing the five-wave CHARLS elderly-health panel.

### `02_attach_city_code_and_health_index.py`

Archived code cells for attaching health index and city-code information.

### `03_build_city_return_period_flood_exposure.py`

Archived code cells for constructing city-level return-period flood exposure and
rolling exposure windows.

### `04_merge_charls_with_city_flood_exposure.py`

Archived code cells for merging the CHARLS elderly-health panel with city-level
flood exposure. This notebook export also contains baseline fixed-effects
estimation code, so it is marked as a mixed exposure-linkage and regression file.

### `05_diagnostics_city_county_crosswalk.py`

Optional diagnostic code for city-county spatial-key correspondence.

### `06_legacy_city_gumbel_exposure_version.py`

Earlier/alternative city-level Gumbel exposure-construction notebook.

### `07_bridge_exposure_linkage_and_pilot_fe.py`

Bridge notebook containing exposure linkage and preliminary fixed-effects
inference.

## Data restrictions

Raw CHARLS microdata and individual-level exposure-linked analysis panels are
restricted and are not included in this repository.

## Repository use

This folder documents how the elderly-health final analysis panel was
constructed. It is not a fully self-contained replication package.
