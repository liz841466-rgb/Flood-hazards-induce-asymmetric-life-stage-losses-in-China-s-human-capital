# Flood Exposure and Socioeconomic Impact Assessment in China

This repository archives code used to construct flood exposure indicators, build
analysis samples, link flood exposure to microdata, estimate fixed-effects models,
run mechanism analyses, compare external flood datasets, and generate figures.

This repository is a public code archive. Restricted raw data and
individual-level analysis panels are not included.

AI-assisted organization note: OpenAI Codex was used to help organize and
prepare the code archive for GitHub release.

## Repository structure

The code is organized by analysis stage:

1. `src/01_flood_exposure`
   Flood exposure construction from hydrodynamic-model outputs and
   return-period event indicators.

2. `src/02_sample_construction/`
   Sample construction for CHARLS elderly health, 2015 Census education,
   CHFS/CFHS household mechanisms, and school POI inputs.

3. `src/03_exposure_linkage/`
   Link flood exposure histories to elderly-health and childhood-education
   analysis panels.

4. `src/04_main_regression_fe/`
   Fixed-effects regressions for elderly health and childhood education.

5. `src/05_mechanism_analysis/`
   Healthcare, household education-investment, school-facility, and
   school-seasonality mechanism analyses.

6. `src/06_external_flood_dataset_comparison/`
   External flood dataset comparison using DFO, GFD, and Chinese news-based
   flood inventory validation scripts.

7. `src/07_tables_figures/`
   Scripts for main figures, supplementary figures, EDA figures, and
   external-flood supplementary figures.

## Main workflow

1. Build return-period flood exposure indicators.
2. Construct analysis samples from CHARLS, the 2015 Census, CHFS/CFHS, and school POI data.
3. Link flood exposure to elderly-health and childhood-education analysis panels.
4. Estimate fixed-effects models.
5. Run mechanism analyses.
6. Compare Gumbel-derived flood events with DFO/GFD external flood datasets.
7. Generate main and supplementary figures.

See [`RUN_ORDER.md`](RUN_ORDER.md) for a module-by-module reading order.

## Data restrictions

This repository does not include restricted or non-redistributable data, including
CHARLS microdata, 2015 Census microdata, CHFS/CFHS microdata, school POI records,
DFO/GFD raw files, hydrodynamic-model rasters, shapefiles, individual-level panels,
or local regression/figure outputs.

See [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for details.

## Reproducibility scope

The scripts preserve code cells exported from the original Jupyter notebooks.
They are intended to document the analysis workflow and support auditability.
They are not a fully self-contained public replication package because several
inputs are restricted or must remain local.

See [`REPRODUCIBILITY_NOTES.md`](REPRODUCIBILITY_NOTES.md) for details.

## Release checklist

Before public release, confirm that raw microdata, geospatial rasters,
shapefiles, NetCDF files, exposure-linked analysis panels, local regression
outputs, plotting data, and final figures are not committed. See
[`SECURITY_AND_SENSITIVE_DATA_AUDIT.md`](SECURITY_AND_SENSITIVE_DATA_AUDIT.md)
for the concise sensitive-data checklist.
