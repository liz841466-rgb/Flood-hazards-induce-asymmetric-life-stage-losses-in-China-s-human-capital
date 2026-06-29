# DFO alternative exposure results run order

This folder archives notebooks for external flood dataset comparison.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Required workflow

1. `01_prepare_dfo_child_education_data.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Prepare DFO child-education alternative exposure data

2. `02_dfo_child_education_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: DFO child-education alternative exposure regression

3. `03_dfo_child_education_intensity_curve.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: DFO child-education intensity-response curve

4. `04_dfo_elderly_health_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: DFO elderly-health alternative exposure regression

5. `05_dfo_elderly_severity_curve.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: DFO elderly-health severity-response curve

## Notes

- This module is not a high-/low-risk zoning validation module.
- DFO/GFD raw files, restricted microdata, exposure-linked panels, and local result outputs are not included.
