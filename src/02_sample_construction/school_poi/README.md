# School POI / education-facility code archive

This folder contains archived code for constructing school POI and
education-facility datasets used in the flood impact assessment workflow.

The archive follows the user's existing Jupyter workflow and preserves original
notebook code cells for auditability.

## Summary

- Required main notebooks found: 10
- Required main notebooks missing: 0
- Optional main notebooks found: 1
- Extra notebooks recorded: 0
- Jupyter checkpoint notebooks skipped: 41
- Province notebooks audited: 31
- Province notebooks exported as legacy code: 3
- Metadata/documentation files copied: 0

## Main files

### `01_province_level_school_poi_cleaning_template.py`

Representative province-level school POI cleaning workflow.

### `02_remove_universities_and_filter_school_types.py`

Code for removing universities and filtering school facility types.

### `03_merge_national_school_poi.py`

Code for merging province-level outputs into a national school POI table.

### `04_school_poi_exploratory_analysis.py`

Exploratory checks for the school POI dataset.

### `05_generate_school_poi_by_province_optimized.py`

Optimized batch workflow for generating province-level school POI data.

### `06_extract_euluc_clcd_for_school_points.py`

Code for extracting EULUC and CLCD attributes for school points.

### `07_generate_annual_urban_landuse_layers.py`

Code for generating annual urban land-use layers.

### `08_generate_annual_nighttime_light_layers.py`

Code for generating annual nighttime-light layers.

### `09_read_nighttime_light_and_population_density.py`

Code for reading nighttime-light and population-density data.

### `10_infer_school_establishment_year_multisource.py`

Code for inferring school establishment year using multisource evidence.

### `11_manual_corrections.py`

Manual correction notebook exports, retained for auditability.

## Data restrictions

Raw POI records, geospatial rasters, and school-level processed outputs are not
included in this repository. Users must obtain the underlying data from their
original providers and comply with the relevant data-use agreements.

## Repository use

This folder documents how school POI and auxiliary school-location variables
were constructed. It is not a fully self-contained replication package.
