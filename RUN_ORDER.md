# Repository run and review order

This repository is a code archive organized by analysis stage. The folders
should be reviewed in the following order.

## 1. Flood exposure construction

- `src/01_flood_exposure` - Flood exposure construction
  - Local run order: `src/01_flood_exposure/RUN_ORDER.md`

## 2. Sample construction

- `src/02_sample_construction/charls` - CHARLS elderly-health sample construction
  - Local run order: `src/02_sample_construction/charls/RUN_ORDER.md`
- `src/02_sample_construction/census2015` - 2015 Census education sample construction
  - Local run order: `src/02_sample_construction/census2015/RUN_ORDER.md`
- `src/02_sample_construction/chfs` - CHFS/CFHS household sample construction
  - Local run order: `src/02_sample_construction/chfs/RUN_ORDER.md`
- `src/02_sample_construction/school_poi` - School POI sample construction
  - Local run order: `src/02_sample_construction/school_poi/RUN_ORDER.md`

## 3. Exposure linkage

- `src/03_exposure_linkage/elderly_health` - Elderly-health exposure linkage
  - Local run order: `src/03_exposure_linkage/elderly_health/RUN_ORDER.md`
- `src/03_exposure_linkage/census2015_education` - Childhood education exposure linkage
  - Local run order: `src/03_exposure_linkage/census2015_education/RUN_ORDER.md`

## 4. Fixed-effects regressions

- `src/04_main_regression_fe/elderly_health` - Elderly-health fixed-effects regressions
  - Local run order: `src/04_main_regression_fe/elderly_health/RUN_ORDER.md`
- `src/04_main_regression_fe/census2015_education` - Childhood education fixed-effects regressions
  - Local run order: `src/04_main_regression_fe/census2015_education/RUN_ORDER.md`

## 5. Mechanism analyses

- `src/05_mechanism_analysis/elderly_health` - Elderly-health mechanism analysis
  - Local run order: `src/05_mechanism_analysis/elderly_health/RUN_ORDER.md`
- `src/05_mechanism_analysis/child_education` - Child-education mechanism analysis
  - Local run order: `src/05_mechanism_analysis/child_education/RUN_ORDER.md`

## 6. External flood dataset comparison

- `src/06_external_flood_dataset_comparison` - External flood dataset comparison
  - Local run order: `src/06_external_flood_dataset_comparison/RUN_ORDER.md`

## 7. Tables and figures

- `src/07_tables_figures` - Tables and figures
  - Local run order: `src/07_tables_figures/RUN_ORDER.md`

## Final checks before public release

1. Ensure all `config.yaml` files are excluded and only `config.example.yaml` files remain.
2. Ensure no raw data, individual-level panels, geospatial rasters, shapefiles, NetCDF files, or local result files are committed.
3. Confirm that the repository contains only code, concise documentation, and configuration examples.
