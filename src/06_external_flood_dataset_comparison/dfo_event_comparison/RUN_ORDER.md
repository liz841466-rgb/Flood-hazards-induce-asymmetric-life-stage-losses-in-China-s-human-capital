# DFO event comparison run order

This folder archives notebooks for external flood dataset comparison.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Required workflow

1. `01_city_gumbel_events_vs_dfo.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Compare city-level Gumbel flood events with DFO records

2. `02_county_gumbel_events_vs_dfo.py`
   - Source notebook: internal original notebook (non-public source filename omitted).
   - Purpose: Compare county-level Gumbel flood events with DFO records

## Notes

- This module is not a high-/low-risk zoning validation module.
- DFO/GFD raw files, restricted microdata, exposure-linked panels, and local result outputs are not included.
- Abandoned notebooks are retained for auditability only.
