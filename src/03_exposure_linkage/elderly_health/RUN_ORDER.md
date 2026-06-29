# Elderly-health exposure-linkage run order

This folder archives the existing Jupyter workflow used to construct the
CHARLS elderly-health exposure-linked final analysis panel.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Required exposure-linkage workflow

1. `01_prepare_charls_60plus_health_panel.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Prepare the five-wave CHARLS 60-plus elderly-health panel

2. `02_attach_city_code_and_health_index.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Attach health index and city code to the elderly-health panel

3. `03_build_city_return_period_flood_exposure.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Build city-level return-period flood exposure and rolling windows

4. `04_merge_charls_with_city_flood_exposure.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Merge CHARLS elderly-health panel with city-level flood exposure

## Supporting diagnostic script

5. `05_diagnostics_city_county_crosswalk.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Diagnose city-county spatial-key correspondence

## Notes

- `04_merge_charls_with_city_flood_exposure.py` is a mixed notebook export:
  it contains final panel construction and baseline fixed-effects code.
- Raw CHARLS data and exposure-linked individual-level panels are not included.
- Before public release, local absolute paths inside exported notebook code can be
  replaced by `config.yaml` or command-line arguments if a reusable pipeline is needed.
