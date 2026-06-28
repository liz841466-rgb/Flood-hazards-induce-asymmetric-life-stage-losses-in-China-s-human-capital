#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utilities for CaMa-Flood storage-based return-period flood event identification.

This file was extracted from the notebook workflow. It supports county-level and
city-level event construction from daily ensemble P50 river storage.

Raw CaMa-Flood outputs and administrative shapefiles are not included.
"""

import os
import re
import json
from glob import glob

import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio import features
from rasterio.transform import Affine
from pyproj import Geod
from scipy.stats import gumbel_r


def find_sample_json(p50_root):
    """Find one .bin.json metadata file under the daily P50 storage directory."""
    pattern = os.path.join(str(p50_root), "**", "*.bin.json")
    cands = sorted(glob(pattern, recursive=True))
    if not cands:
        raise RuntimeError(f"No .bin.json metadata file was found under: {p50_root}")
    print(f"[INFO] Using sample metadata: {cands[0]}")
    return cands[0]


def prepare_storage_meta(sample_json):
    """Read metadata for a daily P50 storage binary file."""
    with open(sample_json, "r", encoding="utf-8") as jf:
        meta = json.load(jf)

    rows = int(meta["rows"])
    cols = int(meta["cols"])
    compact = meta.get("compact_mode", "float32")

    if compact == "float32":
        dtype = np.dtype("<f4")
        scale = 1.0
        nan_code = None
    elif compact == "float16":
        dtype = np.dtype("<f2")
        scale = 1.0
        nan_code = None
    elif compact == "u16_q01m":
        dtype = np.dtype("<u2")
        bands = meta["bands"][0]
        scale = float(bands.get("scale", 0.01))
        nan_code = np.uint16(bands.get("nan", 65535))
    else:
        raise ValueError(f"Unknown compact_mode: {compact}")

    x0, y0, dx, dy = meta["transform"]
    transform = Affine(dx, 0, x0, 0, dy, y0)
    crs = meta.get("crs", "EPSG:4326")
    return rows, cols, dtype, scale, nan_code, transform, crs


def pixel_area_raster(transform, shape):
    """Estimate grid-cell area in square meters for an EPSG:4326 raster."""
    ny, nx = shape
    geod = Geod(ellps="WGS84")

    xs = transform.c + (np.arange(nx) + 0.5) * transform.a
    ys = transform.f + (np.arange(ny) + 0.5) * transform.e

    x_left = xs[0] - 0.5 * transform.a
    x_right = xs[-1] + 0.5 * transform.a

    area = np.zeros((ny, nx), dtype=np.float64)
    for j in range(ny):
        dlon_row = geod.line_length([x_left, x_right], [ys[j], ys[j]]) / nx
        y_top = ys[j] - 0.5 * transform.e
        y_bottom = ys[j] + 0.5 * transform.e
        dlat = geod.line_length([xs[0], xs[0]], [y_top, y_bottom])
        area[j, :] = dlon_row * dlat

    return area


def rasterize_admin_units(
    transform,
    shape,
    shp_path,
    id_field=None,
    name_field=None,
    id_candidates=None,
    id_output_name="unit_code",
    name_output_name="unit_name",
    internal_id_name="unit_id",
):
    """
    Rasterize administrative units to the CaMa-Flood grid.

    Returns
    -------
    admin_id_grid : np.ndarray
        Integer internal unit ID raster.
    map_df : pandas.DataFrame
        Mapping table from internal ID to administrative code/name.
    """
    ny, nx = shape

    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    gdf = gdf.to_crs(4326)

    candidates = []
    if id_field:
        candidates.append(id_field)
    if id_candidates:
        candidates.extend(id_candidates)

    candidates.extend([
        "adcode", "ADCODE", "GB", "CODE", "code",
        "id", "ID", "county_id", "COUNTY_ID",
        "city_code", "CITY_CODE", "citycode", "CITYCODE",
        "县代码", "区县码", "市代码"
    ])

    id_col = next((c for c in candidates if c in gdf.columns), None)
    if id_col is None:
        raise ValueError(f"No valid administrative ID field was found in: {shp_path}")

    ids_raw = gdf[id_col]
    if ids_raw.isna().any():
        raise ValueError(f"Administrative ID field contains missing values: {id_col}")

    ids_as_key = ids_raw.astype(str)
    codes, uniques = pd.factorize(ids_as_key, sort=False)
    internal_ids = (codes + 1).astype(np.int32)

    map_df = pd.DataFrame({
        internal_id_name: np.arange(1, len(uniques) + 1, dtype=np.int32),
        id_output_name: uniques.astype(str),
    })

    if name_field and name_field in gdf.columns:
        name_map = gdf[[id_col, name_field]].drop_duplicates(subset=[id_col]).copy()
        name_map[id_col] = name_map[id_col].astype(str)
        name_map.columns = [id_output_name, name_output_name]
        map_df = map_df.merge(name_map, on=id_output_name, how="left")

    shapes_iter = ((geom, int(uid)) for geom, uid in zip(gdf.geometry, internal_ids))

    admin_id_grid = features.rasterize(
        shapes=shapes_iter,
        out_shape=(ny, nx),
        transform=transform,
        fill=0,
        dtype="int32"
    )

    return admin_id_grid, map_df


def compute_admin_area(admin_id_grid, pixel_area, map_df, internal_id_name):
    """Compute administrative-unit area from rasterized grid cells."""
    mask = admin_id_grid > 0
    ids = admin_id_grid[mask].astype(np.int32)
    weights = pixel_area[mask]

    max_id = int(admin_id_grid.max())
    area_by_id = np.bincount(ids, weights=weights, minlength=max_id + 1)

    out = map_df.copy()
    out["area_m2"] = out[internal_id_name].map({
        int(i): float(v) for i, v in enumerate(area_by_id) if i != 0
    }).fillna(0.0)
    out["area_km2"] = out["area_m2"] / 1e6

    return out


def list_storage_bin_files(p50_root, start_year=None, end_year=None):
    """List daily P50 storage binary files and parse date from filename."""
    pattern = os.path.join(str(p50_root), "**", "*.bin")
    paths = sorted(glob(pattern, recursive=True))

    out = []
    for p in paths:
        fname = os.path.basename(p)
        m = re.search(r"(\d{8})", fname)
        if not m:
            continue

        datestr = m.group(1)
        year = int(datestr[:4])

        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue

        date = pd.to_datetime(datestr, format="%Y%m%d")
        out.append((p, date))

    print(f"[INFO] Found {len(out)} daily P50 storage binary files.")
    return out


def load_cama_storage(bin_path, rows, cols, dtype, scale=1.0, nan_code=None):
    """Read one daily P50 storage binary file as a 2-D float32 array."""
    n = rows * cols

    with open(bin_path, "rb") as f:
        buf = f.read()

    arr = np.frombuffer(buf, dtype=dtype, count=n)

    if arr.size != n:
        raise RuntimeError(
            f"Data length mismatch: {bin_path}. Expected {n}, got {arr.size}."
        )

    arr = arr.reshape((rows, cols)).astype(np.float32)

    if nan_code is not None:
        arr[arr == nan_code] = np.nan

    arr = arr * scale
    arr = np.where(np.isfinite(arr) & (arr > 0), arr, np.nan)

    return arr


def compute_annual_max_storage(bin_list, rows, cols, dtype, scale=1.0, nan_code=None):
    """
    Compute grid-level annual maximum storage from daily P50 storage files.

    Returns
    -------
    years_all : np.ndarray
    annual_max : np.ndarray
        Shape = (n_years, rows, cols).
    """
    if not bin_list:
        raise RuntimeError("bin_list is empty.")

    years = sorted({date.year for _, date in bin_list})
    year_to_idx = {y: i for i, y in enumerate(years)}
    annual_max = np.full((len(years), rows, cols), np.nan, dtype=np.float32)

    print(f"[INFO] Years: {years[0]}-{years[-1]}, n={len(years)}")

    prev_year = None
    for bin_path, date in sorted(bin_list, key=lambda x: x[1]):
        y = int(date.year)
        idx = year_to_idx[y]

        if prev_year is None or y != prev_year:
            print(f"[INFO] Processing daily storage for year {y} ...")
            prev_year = y

        arr = load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code)

        current = annual_max[idx]
        current_nan = ~np.isfinite(current)
        arr_nan = ~np.isfinite(arr)

        replace = current_nan & (~arr_nan)
        current[replace] = arr[replace]

        both_valid = (~current_nan) & (~arr_nan)
        current[both_valid] = np.maximum(current[both_valid], arr[both_valid])

        annual_max[idx] = current

    return np.asarray(years, dtype=int), annual_max


def fit_gumbel_thresholds_grid(
    annual_max,
    years_all,
    base_start,
    base_end,
    return_periods,
    min_years_for_fit=15,
):
    """Fit grid-level Gumbel distributions and compute return-period thresholds."""
    years_all = np.asarray(years_all, dtype=int)
    base_mask = (years_all >= base_start) & (years_all <= base_end)

    if not base_mask.any():
        raise RuntimeError("No years fall inside the baseline period.")

    base = annual_max[base_mask]
    n_base, rows, cols = base.shape
    n_cells = rows * cols

    print(f"[INFO] Grid-level Gumbel fit baseline: {base_start}-{base_end}, n={n_base}")

    flat = base.reshape((n_base, n_cells))
    thresholds = {
        T: np.full(n_cells, np.nan, dtype=np.float32)
        for T in return_periods
    }

    for j in range(n_cells):
        s = flat[:, j]
        s = s[np.isfinite(s)]
        s = s[s > 0]

        if s.size < min_years_for_fit:
            continue

        try:
            loc, scale = gumbel_r.fit(s)
        except Exception:
            continue

        if not np.isfinite(loc) or not np.isfinite(scale) or scale <= 0:
            continue

        for T in return_periods:
            p = 1.0 - 1.0 / float(T)
            q = gumbel_r.ppf(p, loc=loc, scale=scale)
            if np.isfinite(q):
                thresholds[T][j] = float(q)

    return {
        T: thresholds[T].reshape((rows, cols))
        for T in return_periods
    }


def compute_unit_year_events_any_pixel(
    years_all,
    annual_max,
    threshold_grids,
    unit_id_grid,
    map_df,
    internal_id_name,
    analysis_start,
    analysis_end,
    return_periods,
):
    """
    Construct administrative-unit by year flood events using any-pixel trigger.

    A unit-year is coded as 1 if any valid grid cell inside the unit exceeds
    the corresponding return-period threshold.
    """
    years_all = np.asarray(years_all, dtype=int)
    year_to_idx = {int(y): i for i, y in enumerate(years_all)}

    analysis_years = sorted([
        int(y) for y in years_all
        if analysis_start <= int(y) <= analysis_end
    ])

    print(f"[INFO] Event analysis period: {analysis_start}-{analysis_end}, n={len(analysis_years)}")

    valid_unit_mask = unit_id_grid > 0
    out = []

    for y in analysis_years:
        idx = year_to_idx[y]
        s_year = annual_max[idx]

        df_year = map_df.copy()
        df_year.insert(0, "year", y)

        for T in return_periods:
            thr = threshold_grids[T]
            event_grid = (s_year >= thr) & np.isfinite(thr) & valid_unit_mask

            triggered_ids = unit_id_grid[event_grid]
            if triggered_ids.size > 0:
                triggered = set(np.unique(triggered_ids.astype(np.int32)).tolist())
            else:
                triggered = set()

            df_year[f"flood_ge_T{T}"] = (
                df_year[internal_id_name].isin(triggered).astype(np.int8)
            )

        out.append(df_year)

    return pd.concat(out, ignore_index=True)


def compute_admin_annual_weighted_mean(annual_max, unit_id_grid, pixel_area):
    """
    Convert grid-level annual maximum storage into administrative-unit
    area-weighted annual mean storage series.
    """
    n_years, rows, cols = annual_max.shape
    max_uid = int(unit_id_grid.max())

    unit_series = np.full((n_years, max_uid + 1), np.nan, dtype=np.float32)
    valid_unit_mask = unit_id_grid > 0

    for t in range(n_years):
        s_year = annual_max[t]
        mask = valid_unit_mask & np.isfinite(s_year)

        if not mask.any():
            continue

        ids = unit_id_grid[mask].astype(np.int32)
        areas = pixel_area[mask].astype(np.float64)
        vals = s_year[mask].astype(np.float64)

        num = np.bincount(ids, weights=areas * vals, minlength=max_uid + 1)
        den = np.bincount(ids, weights=areas, minlength=max_uid + 1)

        with np.errstate(divide="ignore", invalid="ignore"):
            mean_vals = num / den

        mean_vals[den == 0] = np.nan
        unit_series[t, :] = mean_vals.astype(np.float32)

    return unit_series


def fit_gumbel_thresholds_series(
    unit_series,
    years_all,
    base_start,
    base_end,
    return_periods,
    min_years_for_fit=15,
):
    """Fit Gumbel distributions to administrative-unit annual series."""
    years_all = np.asarray(years_all, dtype=int)
    base_mask = (years_all >= base_start) & (years_all <= base_end)

    if not base_mask.any():
        raise RuntimeError("No years fall inside the baseline period.")

    base = unit_series[base_mask]
    n_base, n_units = base.shape

    print(f"[INFO] Unit-level Gumbel fit baseline: {base_start}-{base_end}, n={n_base}")

    thresholds = {
        T: np.full((n_units,), np.nan, dtype=np.float32)
        for T in return_periods
    }

    for uid in range(1, n_units):
        s = base[:, uid]
        s = s[np.isfinite(s)]
        s = s[s > 0]

        if s.size < min_years_for_fit:
            continue

        try:
            loc, scale = gumbel_r.fit(s)
        except Exception:
            continue

        if not np.isfinite(loc) or not np.isfinite(scale) or scale <= 0:
            continue

        for T in return_periods:
            p = 1.0 - 1.0 / float(T)
            q = gumbel_r.ppf(p, loc=loc, scale=scale)
            if np.isfinite(q):
                thresholds[T][uid] = float(q)

    return thresholds


def compute_unit_year_events_from_series(
    years_all,
    unit_series,
    unit_thresholds,
    map_df,
    internal_id_name,
    analysis_start,
    analysis_end,
    return_periods,
):
    """Construct administrative-unit by year flood events from unit annual series."""
    years_all = np.asarray(years_all, dtype=int)
    year_to_idx = {int(y): i for i, y in enumerate(years_all)}

    analysis_years = sorted([
        int(y) for y in years_all
        if analysis_start <= int(y) <= analysis_end
    ])

    print(f"[INFO] Event analysis period: {analysis_start}-{analysis_end}, n={len(analysis_years)}")

    out = []

    for y in analysis_years:
        idx = year_to_idx[y]
        unit_vals = unit_series[idx]

        df_year = map_df.copy()
        df_year.insert(0, "year", y)

        ids = df_year[internal_id_name].to_numpy(dtype=int)

        for T in return_periods:
            thr = unit_thresholds[T]
            flags = np.zeros_like(ids, dtype=np.int8)

            valid = np.isfinite(thr[ids]) & np.isfinite(unit_vals[ids])
            flags[valid & (unit_vals[ids] >= thr[ids])] = 1

            df_year[f"flood_ge_T{T}"] = flags

        out.append(df_year)

    return pd.concat(out, ignore_index=True)
