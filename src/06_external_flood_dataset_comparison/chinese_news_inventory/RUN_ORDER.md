# Chinese News Inventory Histogram Run Order

Run these scripts after generating the local county-level validation summary
tables from the Chinese news-based flood inventory workflow.

1. `01_county_hit_false_histogram.py`
   - Plots county-level hit-rate and false-rate histograms.
2. `02_county_add_rate_histogram.py`
   - Plots the additional add-rate histogram for inventory events not recorded
     in DFO.

The scripts assume local CSV inputs and write local PNG outputs. No raw
inventory data, plotting data, or generated figures are included in this
repository.

