# 2015 Census sample-construction workflow

This folder archives the existing Jupyter-notebook workflow used to construct
2015 census education microdata and county-by-birth-cohort scaffolds for the
flood impact analysis.

The repository does not include raw 2015 census microdata or individual-level
processed outputs. Users must obtain the raw data from the authorized provider
and comply with the relevant data-use agreement.

## Summary

- Workflow notebooks found: 4
- Workflow notebooks missing: 0
- Metadata/documentation files copied: 0

## Generated files

### `00_raw_data_inspection.py`

Archives the notebook used to inspect raw census files, metadata, encodings,
column structure, and reading strategies.

### `01_extract_region_education_variables.py`

Archives the notebook used to inspect and extract region codes and
education-related variables.

### `02_build_census2015_microdata_base.py`

Archives the notebook used to construct the core individual-level education
microdata base, including birth year, education outcomes, county codes, and
sample variables.

### `03_build_county_birthyear_scaffold.py`

Archives the notebook used to prepare or document the county-by-birth-year
structure used to link childhood flood exposure windows.

### `legacy_notebook_exports/`

Contains exact exported code cells from each source notebook. These files are
kept for auditability and are not a polished public API.

### `metadata/`

Contains small metadata or documentation files copied from the source folder,
if any. Restricted raw data and individual-level outputs are excluded.

## Recommended run order

See `RUN_ORDER.md`.

## Important sample-definition note

If earlier notebook versions use a narrower cohort range, the public replication
workflow should be checked against the final paper definition. The final intended
education-sample definition should be documented in `config.yaml` and in the
analysis scripts.
