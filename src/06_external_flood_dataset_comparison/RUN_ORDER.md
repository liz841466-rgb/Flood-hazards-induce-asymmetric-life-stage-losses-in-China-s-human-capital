# External flood dataset comparison run order

This folder archives code for comparing Gumbel-derived flood events with external
flood datasets and for using DFO as an alternative flood exposure dataset.

Recommended review order:

1. `dfo_event_comparison/`
   - City- and county-level Gumbel flood events compared with DFO records.
2. `gfd_event_validation/`
   - POD/FAR/CSI-style validation against external flood masks.
3. `chinese_news_inventory/`
   - Histogram scripts for Chinese news-based flood inventory validation.
4. `dfo_alternative_exposure_results/`
   - DFO-based robustness analyses for child education and elderly health.
5. `figures/`
   - DFO comparison and intensity-response figure scripts.

Scope:

- This module is not a validation of high-/low-risk zoning.
- DFO/GFD raw files, Chinese news inventory records, flood masks, rasters,
  restricted microdata, and local result outputs are not included.
