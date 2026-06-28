# 2015 Census childhood education exposure-linkage run order

This folder archives the existing workflow used to construct county-birth-cohort
childhood flood exposure variables and exposure-linked 2015 Census education panels.

## Main workflow

1. `01_build_county_return_period_flood_events.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: County-year return-period flood event construction

2. `02_build_childhood_exposure_and_education_panel.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Build childhood flood exposure and education analysis panel

3. `03_build_multi_return_period_exposure_counts.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Build multiple-return-period and multiple-exposure-count variables

## Notes

- Raw Census microdata and individual-level exposure-linked panels are not included.
- Mixed notebooks are preserved as-is for auditability.
