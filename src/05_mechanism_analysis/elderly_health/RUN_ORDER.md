# Elderly-health mechanism analysis run order

This folder archives the existing Jupyter workflow for medical expenditure,
healthcare access, channel-index construction, and pathway analysis.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Required workflow

1. `01_initial_mechanism_design_and_data_review.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Initial mechanism design and data review

2. `02_construct_three_channel_indices.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Construct three elderly-health channel indices

3. `03_channel_direction_and_sign_check.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Check channel direction and sign harmonization

4. `04_flood_exposure_channel_index_regression.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Flood exposure by channel-index regression

5. `05_pathway_analysis.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Pathway analysis

6. `06_major_mechanism_categories.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Major mechanism categories

## Optional / legacy / EDA notebooks

7. `07_alternative_mechanism_strategy_legacy.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Alternative mechanism strategy

8. `08_eda_mechanism_names.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: EDA for mechanism names

9. `09_eda_medical_expenditure_and_healthcare_access.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: EDA for medical expenditure and healthcare access

## Notes

- Raw survey data, individual-level panels, POI records, and local result outputs are not included.
- Optional, legacy, abandoned, and EDA notebooks are retained for auditability.
