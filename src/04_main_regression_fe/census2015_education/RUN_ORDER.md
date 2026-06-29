# 2015 Census education fixed-effects regression run order

This folder archives the existing workflow used for child education fixed-effects
regressions, heterogeneity analyses, and intensity-response mapping.

## Main workflow

1. `01_baseline_education_fe_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Baseline education fixed-effects regression

2. `02_multi_return_period_exposure_count_regressions.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Multiple-return-period and exposure-count regressions

3. `03_children_risk_zone_heterogeneity.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: High-risk and low-risk zone heterogeneity for children

4. `05_child_intensity_response_curve.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Child education return-period intensity-response curve

## Notes

- Raw Census microdata, exposure-linked panels, and local regression outputs are not included.
- Mixed notebooks are preserved as-is for auditability.
