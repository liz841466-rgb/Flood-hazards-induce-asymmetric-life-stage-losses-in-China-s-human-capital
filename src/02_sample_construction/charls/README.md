# CHARLS sample construction code archive

This folder organizes the user's existing CHARLS Jupyter notebook workflow into
a GitHub-readable code archive.

## Core principle

The original CHARLS workflow was performed in Jupyter notebooks by survey wave
and processing step. This archive preserves that workflow rather than replacing
it with a newly invented pipeline.

## Summary

- Total found notebooks: 45
- Total missing expected notebooks: 0
- Wave-step found notebooks: 36
- Wave-step missing notebooks: 0

## Main files

### `charls_common.py`

Generic helper functions.

### Wave-step archive scripts

The following files group exported notebook code by the original processing step:

```text
01_wave_health_status.py
02_wave_health_recode.py
03_wave_age_region.py
04_wave_health_index.py
05_wave_health_index_age_region_merge.py
06_wave_medical_expenditure.py
07_wave_healthcare_access_time.py
08_wave_demographic_controls_optional.py
```

### Joint-panel script

```text
09_joint_unbalanced_panel.py
```

This script archives five-wave unbalanced panel construction and related
mechanism-panel construction steps.

## Data restrictions

Raw CHARLS data and individual-level processed outputs are not included. Users
must obtain CHARLS data from the original provider and comply with the data-use
agreement.

## Before public GitHub release

1. Keep raw data and individual-level outputs excluded.
2. Replace local absolute paths with a private `config.yaml`.
3. Retain `config.example.yaml` as a public template.
