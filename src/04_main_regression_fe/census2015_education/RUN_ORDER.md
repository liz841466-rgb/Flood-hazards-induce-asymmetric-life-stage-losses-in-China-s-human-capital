# 2015 Census education fixed-effects regression run order

This folder archives the existing workflow used for child education fixed-effects
regressions, heterogeneity analyses, and intensity-response mapping.

## Main workflow

4. `01_baseline_education_fe_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Baseline education fixed-effects regression

5. `02_multi_return_period_exposure_count_regressions.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Multiple-return-period and exposure-count regressions

6. `03_children_risk_zone_heterogeneity.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: High-risk and low-risk zone heterogeneity for children

7. `04_auxiliary_child_education_regression_20260320.py`
   - Source notebook: `20260320.ipynb`
   - Purpose: Auxiliary child education regression workflow

8. `05_child_intensity_response_curve.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Child education return-period intensity-response curve

## Notes

- Raw Census microdata, exposure-linked panels, and local regression outputs are not included.
- Mixed notebooks are preserved as-is for auditability.
