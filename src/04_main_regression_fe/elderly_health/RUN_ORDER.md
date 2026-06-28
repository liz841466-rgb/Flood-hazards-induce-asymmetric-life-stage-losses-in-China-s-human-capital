# Elderly-health fixed-effects regression run order

This folder archives the existing Jupyter workflow used for elderly-health
fixed-effects regressions, heterogeneity analyses, intensity-response mapping,
and result summaries.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Main workflow

1. `01_baseline_fe_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Baseline fixed-effects regression for elderly health

2. `02_return_period_fe_inference.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Return-period fixed-effects inference

3. `03_health_dimension_and_disease_outcomes.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Health-dimension and disease-specific outcome regressions

4. `04_risk_zone_heterogeneity.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: High-risk and low-risk zone heterogeneity regressions

5. `05_intensity_response_curve.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Return-period intensity-response curve

6. `06_result_summary_tables.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Result summary tables and figures

## Notes

- `01_baseline_fe_regression.py` is exported from a mixed notebook that also
  contains final panel construction code. The panel-construction role is archived
  separately under `src/03_exposure_linkage/elderly_health/`.
- Raw CHARLS data, exposure-linked individual-level panels, and local regression
  result files are not included.
- Before public release, local absolute paths inside exported notebook code can be
  replaced by `config.yaml` or command-line arguments if a reusable pipeline is needed.
