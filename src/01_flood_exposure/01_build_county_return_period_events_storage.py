#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
County-level return-period flood event identification from CaMa-Flood
ensemble P50 river storage.

Workflow
--------
daily ensemble P50 storage
-> grid-level annual maximum storage
-> grid-level Gumbel return-period thresholds
-> county-year flood event indicators

Event definition
----------------
A county-year is defined as exposed to a >=T-year flood if any valid grid cell
within the county has annual maximum river storage exceeding its grid-level
T-year Gumbel threshold.

This is a cleaned GitHub-ready script extracted from the notebook workflow.
Raw CaMa-Flood outputs and administrative shapefiles are not included.
"""

from pathlib import Path

import numpy as np

from storage_event_utils import (
    find_sample_json,
    prepare_storage_meta,
    pixel_area_raster,
    rasterize_admin_units,
    compute_admin_area,
    list_storage_bin_files,
    compute_annual_max_storage,
    fit_gumbel_thresholds_grid,
    compute_unit_year_events_any_pixel,
)


STOR_P50_ROOT = Path("/home/ll/jupyter_notebook/result/ensemble_storge_daily_bin_p50")

COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"

OUT_DIR = Path("/home/ll/jupyter_notebook/result/county_storage_return_events")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_START_YEAR = 1980
BASE_END_YEAR = 2020

ANALYSIS_START_YEAR = 1980
ANALYSIS_END_YEAR = 2020

RETURN_PERIODS = [2, 5, 10, 20, 50, 100]
MIN_YEARS_FOR_FIT = 15


def main():
    print("[Step] Read daily P50 storage metadata")
    sample_json = find_sample_json(STOR_P50_ROOT)
    rows, cols, dtype, scale, nan_code, transform, crs = prepare_storage_meta(sample_json)
    print(f"[INFO] storage P50 grid: cols={cols}, rows={rows}, crs={crs}")

    print("[Step] Compute grid-cell area")
    pixel_area = pixel_area_raster(transform, (rows, cols))

    print("[Step] Rasterize county boundary")
    county_id_grid, county_map = rasterize_admin_units(
        transform=transform,
        shape=(rows, cols),
        shp_path=COUNTY_SHP,
        id_field=COUNTY_ID_FIELD,
        name_field=COUNTY_NAME_FIELD,
        id_output_name="county_code",
        name_output_name="county_name",
        internal_id_name="county_id",
    )

    county_area = compute_admin_area(
        county_id_grid,
        pixel_area,
        county_map,
        internal_id_name="county_id",
    )
    county_area_path = OUT_DIR / "county_total_area_storage.csv"
    county_area.to_csv(county_area_path, index=False, encoding="utf-8-sig")
    print(f"[OUT] {county_area_path}")

    print("[Step] List daily P50 storage files")
    bin_list = list_storage_bin_files(
        STOR_P50_ROOT,
        start_year=BASE_START_YEAR,
        end_year=BASE_END_YEAR,
    )
    if not bin_list:
        raise RuntimeError("No daily P50 storage binary files were found.")

    print("[Step] Compute grid-level annual maximum storage")
    years_all, annual_max = compute_annual_max_storage(
        bin_list,
        rows,
        cols,
        dtype,
        scale,
        nan_code,
    )

    print("[Step] Fit grid-level Gumbel thresholds")
    threshold_grids = fit_gumbel_thresholds_grid(
        annual_max=annual_max,
        years_all=years_all,
        base_start=BASE_START_YEAR,
        base_end=BASE_END_YEAR,
        return_periods=RETURN_PERIODS,
        min_years_for_fit=MIN_YEARS_FOR_FIT,
    )

    threshold_path = OUT_DIR / "storage_return_thresholds_grid_gumbel_T2_5_10_20_50_100.npz"
    np.savez_compressed(
        threshold_path,
        years=years_all,
        **{f"thr_T{T}": threshold_grids[T] for T in RETURN_PERIODS},
    )
    print(f"[OUT] {threshold_path}")

    print("[Step] Construct county-year return-period flood events")
    events = compute_unit_year_events_any_pixel(
        years_all=years_all,
        annual_max=annual_max,
        threshold_grids=threshold_grids,
        unit_id_grid=county_id_grid,
        map_df=county_map,
        internal_id_name="county_id",
        analysis_start=ANALYSIS_START_YEAR,
        analysis_end=ANALYSIS_END_YEAR,
        return_periods=RETURN_PERIODS,
    )

    out_csv = OUT_DIR / (
        f"county_flood_events_T2_5_10_20_50_100_"
        f"{ANALYSIS_START_YEAR}_{ANALYSIS_END_YEAR}.csv"
    )
    events.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[DONE] {out_csv}")


if __name__ == "__main__":
    main()
