#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
City-level return-period flood event identification from CaMa-Flood
ensemble P50 river storage.

Workflow
--------
daily ensemble P50 storage
-> grid-level annual maximum storage
-> D1 dry-pixel filtering
-> city-level area-weighted annual maximum storage
-> D2 dry-city filtering
-> city-level Gumbel return-period thresholds
-> city-year flood event indicators

Rule C1
-------
This script first constructs city-level annual maximum storage series using
area-weighted mean storage over valid grid cells, and then fits city-level
Gumbel return-period thresholds.

Raw CaMa-Flood outputs and administrative shapefiles are not included.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from storage_event_utils import (
    find_sample_json,
    prepare_storage_meta,
    pixel_area_raster,
    rasterize_admin_units,
    compute_admin_area,
    list_storage_bin_files,
    compute_annual_max_storage,
    compute_admin_annual_weighted_mean,
    fit_gumbel_thresholds_series,
    compute_unit_year_events_from_series,
)


STOR_P50_ROOT = Path("/home/ll/jupyter_notebook/result/ensemble_storge_daily_bin_p50")

CITY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/city/city.shp")
CITY_ID_FIELD = "市代码"
CITY_NAME_FIELD = "市"

OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_START_YEAR = 1980
BASE_END_YEAR = 2020

ANALYSIS_START_YEAR = 1980
ANALYSIS_END_YEAR = 2020

RETURN_PERIODS = [2, 5, 10, 20, 50, 100]
MIN_YEARS_FOR_FIT = 15

DRY_FRAC_MIN = 0.30
DRY_CITY_MIN = 0.05


def main():
    print("[Step] Read daily P50 storage metadata")
    sample_json = find_sample_json(STOR_P50_ROOT)
    rows, cols, dtype, scale, nan_code, transform, crs = prepare_storage_meta(sample_json)
    print(f"[INFO] storage P50 grid: cols={cols}, rows={rows}, crs={crs}")

    print("[Step] Compute grid-cell area")
    pixel_area = pixel_area_raster(transform, (rows, cols))

    print("[Step] Rasterize city boundary")
    city_id_grid, city_map = rasterize_admin_units(
        transform=transform,
        shape=(rows, cols),
        shp_path=CITY_SHP,
        id_field=CITY_ID_FIELD,
        name_field=CITY_NAME_FIELD,
        id_output_name="city_code",
        name_output_name="city_name",
        internal_id_name="city_id",
    )

    city_area = compute_admin_area(
        city_id_grid,
        pixel_area,
        city_map,
        internal_id_name="city_id",
    )
    city_area_path = OUT_DIR / "city_total_area_storage.csv"
    city_area.to_csv(city_area_path, index=False, encoding="utf-8-sig")
    print(f"[OUT] {city_area_path}")

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

    print("[Step] Apply D1 dry-pixel filtering")
    years_all = np.asarray(years_all, dtype=int)
    base_mask = (years_all >= BASE_START_YEAR) & (years_all <= BASE_END_YEAR)

    valid_frac = np.isfinite(annual_max[base_mask]).sum(axis=0) / float(base_mask.sum())
    dry_pixel_mask = valid_frac < DRY_FRAC_MIN

    n_dry_pixels = int(dry_pixel_mask.sum())
    n_all_pixels = int(rows * cols)
    print(
        f"[D1] dry pixels: {n_dry_pixels}/{n_all_pixels} "
        f"({n_dry_pixels / n_all_pixels:.3f}), DRY_FRAC_MIN={DRY_FRAC_MIN}"
    )

    annual_max[:, dry_pixel_mask] = np.nan

    dry_pixel_path = OUT_DIR / "dry_mask_pixels_D1.npy"
    np.save(dry_pixel_path, dry_pixel_mask.astype(np.uint8))

    pd.DataFrame({
        "DRY_FRAC_MIN": [DRY_FRAC_MIN],
        "n_dry_pixels": [n_dry_pixels],
        "n_all_pixels": [n_all_pixels],
        "dry_pixel_share": [n_dry_pixels / n_all_pixels],
    }).to_csv(
        OUT_DIR / "dry_mask_pixels_D1_report.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("[Step] Compute city-level area-weighted annual storage series")
    city_series = compute_admin_annual_weighted_mean(
        annual_max=annual_max,
        unit_id_grid=city_id_grid,
        pixel_area=pixel_area,
    )

    print("[Step] Apply D2 dry-city filtering")
    max_city_id = int(city_id_grid.max())

    valid_pixel_any = np.isfinite(annual_max).any(axis=0) & (city_id_grid > 0)

    ids_valid = city_id_grid[valid_pixel_any].astype(np.int32)
    areas_valid = pixel_area[valid_pixel_any].astype(np.float64)

    ids_total = city_id_grid[city_id_grid > 0].astype(np.int32)
    areas_total = pixel_area[city_id_grid > 0].astype(np.float64)

    valid_area = np.bincount(ids_valid, weights=areas_valid, minlength=max_city_id + 1)
    total_area = np.bincount(ids_total, weights=areas_total, minlength=max_city_id + 1)

    with np.errstate(divide="ignore", invalid="ignore"):
        valid_area_frac = valid_area / total_area
    valid_area_frac[total_area == 0] = np.nan

    dry_cities = np.where(valid_area_frac < DRY_CITY_MIN)[0]
    dry_cities = dry_cities[dry_cities > 0]

    print(
        f"[D2] dry cities: {len(dry_cities)}/{max_city_id} "
        f"({len(dry_cities) / max_city_id:.3f}), DRY_CITY_MIN={DRY_CITY_MIN}"
    )

    if len(dry_cities) > 0:
        city_series[:, dry_cities] = np.nan

    d2_report = city_map.copy()
    d2_report["valid_area_frac"] = d2_report["city_id"].map({
        int(i): float(valid_area_frac[i])
        for i in range(len(valid_area_frac))
        if np.isfinite(valid_area_frac[i])
    })
    d2_report["is_dry_city_D2"] = d2_report["city_id"].isin(dry_cities).astype(int)

    d2_report_path = OUT_DIR / "dry_cities_D2_report.csv"
    d2_report.to_csv(d2_report_path, index=False, encoding="utf-8-sig")
    print(f"[OUT] {d2_report_path}")

    print("[Step] Fit city-level Gumbel thresholds")
    thresholds = fit_gumbel_thresholds_series(
        unit_series=city_series,
        years_all=years_all,
        base_start=BASE_START_YEAR,
        base_end=BASE_END_YEAR,
        return_periods=RETURN_PERIODS,
        min_years_for_fit=MIN_YEARS_FOR_FIT,
    )

    threshold_path = OUT_DIR / "storage_return_thresholds_city_gumbel_ruleC1_T2_5_10_20_50_100.npz"
    np.savez_compressed(
        threshold_path,
        years=years_all,
        city_id=city_map["city_id"].to_numpy(),
        city_code=city_map["city_code"].astype(str).to_numpy(),
        **{f"thr_T{T}": thresholds[T] for T in RETURN_PERIODS},
    )
    print(f"[OUT] {threshold_path}")

    print("[Step] Construct city-year return-period flood events")
    events = compute_unit_year_events_from_series(
        years_all=years_all,
        unit_series=city_series,
        unit_thresholds=thresholds,
        map_df=city_map,
        internal_id_name="city_id",
        analysis_start=ANALYSIS_START_YEAR,
        analysis_end=ANALYSIS_END_YEAR,
        return_periods=RETURN_PERIODS,
    )

    out_csv = OUT_DIR / (
        f"city_flood_events_T2_5_10_20_50_100_"
        f"{ANALYSIS_START_YEAR}_{ANALYSIS_END_YEAR}.csv"
    )
    events.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[DONE] {out_csv}")


if __name__ == "__main__":
    main()
