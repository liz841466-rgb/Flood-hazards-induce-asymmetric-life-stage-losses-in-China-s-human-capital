#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
from glob import glob

import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio import features
from rasterio.transform import Affine
from pyproj import Geod

from scipy.stats import gumbel_r


# =============================================================================

# CaMa-Flood processing note.
STOR_P50_ROOT = "/home/ll/jupyter_notebook/result/ensemble_storge_daily_bin_p50"

# Shapefile output note.
COUNTY_SHP = "/home/ll/jupyter_notebook/gis_data/China/country/country.shp"
COUNTY_ID_FIELD = "县代码"   # Original notebook comment normalized for the public code archive.
COUNTY_NAME_FIELD = "县"     # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
OUT_DIR = "/home/ll/jupyter_notebook/result/county_storage_return_events"
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
BASE_START_YEAR = 1980
BASE_END_YEAR   = 2020

# Original notebook comment normalized for the public code archive.
ANALYSIS_START_YEAR = 1986
ANALYSIS_END_YEAR   = 2020

# Original notebook comment normalized for the public code archive.
RETURN_PERIODS = [10, 20, 50, 100]

# Gumbel return-period processing.
MIN_YEARS_FOR_FIT = 15

# =============================================================================

def find_sample_json(p50_root):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pattern = os.path.join(p50_root, "**", "*.bin.json")
    cands = glob(pattern, recursive=True)
    if not cands:
        raise RuntimeError(f"在 {p50_root} 下未找到任何 .bin.json 文件。")
    cands = sorted(cands)
    print("[INFO] Notebook progress message.")
    return cands[0]


def prepare_storge_meta(sample_json):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    import json
    with open(sample_json, "r", encoding="utf-8") as jf:
        meta = json.load(jf)

    rows, cols = int(meta["rows"]), int(meta["cols"])
    compact = meta.get("compact_mode", "float32")

    # Original notebook comment normalized for the public code archive.
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
        raise ValueError(f"未知 compact_mode: {compact}")

    x0, y0, dx, dy = meta["transform"]
    transform = Affine(dx, 0, x0, 0, dy, y0)
    crs = meta.get("crs", "EPSG:4326")
    return rows, cols, dtype, scale, nan_code, transform, crs


def pixel_area_raster(transform, shape):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ny, nx = shape
    geod = Geod(ellps="WGS84")

    xs = transform.c + (np.arange(nx) + 0.5) * transform.a
    ys = transform.f + (np.arange(ny) + 0.5) * transform.e

    x_left  = xs[0]  - 0.5 * transform.a
    x_right = xs[-1] + 0.5 * transform.a

    area = np.zeros((ny, nx), dtype=np.float64)
    for j in range(ny):
        # Original notebook comment normalized for the public code archive.
        dlon_row = geod.line_length([x_left, x_right], [ys[j], ys[j]]) / nx
        # Original notebook comment normalized for the public code archive.
        y_top = ys[j] - 0.5 * transform.e
        y_bot = ys[j] + 0.5 * transform.e
        dlat = geod.line_length([xs[0], xs[0]], [y_top, y_bot])
        area[j, :] = dlon_row * dlat
    return area


def rasterize_counties(transform, shape, county_shp, id_field, name_field):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ny, nx = shape
    gdf = gpd.read_file(county_shp)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    gdf = gdf.to_crs(4326)

    # Original notebook comment normalized for the public code archive.
    candidates = [id_field] if id_field else []
    candidates += [
        "adcode", "ADCODE", "GB", "CODE", "code", "id", "ID",
        "county_id", "COUNTY_ID", "县代码", "区县码"
    ]
    id_col = next((c for c in candidates if c in gdf.columns), None)
    if id_col is None:
        raise ValueError("县界文件中找不到 ID 字段。")

    ids_raw = gdf[id_col]
    if ids_raw.isna().any():
        raise ValueError(f"县 ID 字段 {id_col} 存在缺失值。")

    ids_as_key = ids_raw.astype(str)
    codes, uniques = pd.factorize(ids_as_key, sort=False)
    cid_per_row = (codes + 1).astype(np.int32)  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    if name_field and name_field in gdf.columns:
        name_map = gdf[[id_col, name_field]].drop_duplicates(subset=[id_col]).copy()
        name_map[id_col] = name_map[id_col].astype(str)
        name_map.columns = ["county_code", "county_name"]
    else:
        name_map = pd.DataFrame(columns=["county_code", "county_name"])

    map_df = pd.DataFrame({
        "county_id": np.arange(1, len(uniques) + 1, dtype=np.int32),
        "county_code": uniques
    })
    if not name_map.empty:
        map_df = map_df.merge(name_map, on="county_code", how="left")

    shapes_iter = ((geom, int(cid)) for geom, cid in zip(gdf.geometry, cid_per_row))
    county_id_full = features.rasterize(
        shapes=shapes_iter,
        out_shape=(ny, nx),
        transform=transform,
        fill=0,
        dtype="int32"
    )
    return county_id_full, map_df


def compute_county_area(county_id_full, pix_area_full, map_df):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    mask = county_id_full > 0
    cids = county_id_full[mask].astype(np.int32)
    weights = pix_area_full[mask]
    max_cid = int(county_id_full.max())

    bc = np.bincount(cids, weights=weights, minlength=max_cid + 1)
    area_m2 = {int(i): float(w) for i, w in enumerate(bc) if i != 0}

    df_area = map_df.copy()
    df_area["area_m2"]  = df_area["county_id"].map(area_m2).fillna(0.0)
    df_area["area_km2"] = df_area["area_m2"] / 1e6
    return df_area


def list_storge_bin_files(p50_root, start_year=None, end_year=None):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pattern = os.path.join(p50_root, "**", "*.bin")
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
    print("[INFO] Notebook progress message.")
    return out


def load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    n = rows * cols
    with open(bin_path, "rb") as f:
        buf = f.read()
    arr = np.frombuffer(buf, dtype=dtype, count=n)
    if arr.size != n:
        raise RuntimeError(f"{bin_path} 数据长度不匹配。期望 {n}，实际 {arr.size}")
    arr = arr.reshape((rows, cols))

    arr = arr.astype(np.float32)
    if nan_code is not None:
        arr[arr == nan_code] = np.nan
    arr = arr * scale

    # Original notebook comment normalized for the public code archive.
    arr = np.where(np.isfinite(arr) & (arr > 0), arr, np.nan)
    return arr


def compute_annual_max_storage(bin_list, rows, cols, dtype, scale, nan_code):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not bin_list:
        raise RuntimeError("bin_list 为空。")

    years = sorted({date.year for _, date in bin_list})
    year_to_idx = {y: i for i, y in enumerate(years)}
    Ny = len(years)

    S_annual_max = np.full((Ny, rows, cols), np.nan, dtype=np.float32)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    bin_list_sorted = sorted(bin_list, key=lambda x: x[1])

    prev_year = None
    for bin_path, date in bin_list_sorted:
        y = date.year
        idx = year_to_idx[y]
        if prev_year is None or y != prev_year:
            print("[INFO] Notebook progress message.")
            prev_year = y

        arr = load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code)

        # Original notebook comment normalized for the public code archive.
        current_max = S_annual_max[idx]
        # Original notebook comment normalized for the public code archive.
        mask_curr_nan = ~np.isfinite(current_max)
        mask_arr_nan  = ~np.isfinite(arr)
        # Original notebook comment normalized for the public code archive.
        replace_mask = mask_curr_nan & (~mask_arr_nan)
        current_max[replace_mask] = arr[replace_mask]
        # Original notebook comment normalized for the public code archive.
        both_valid = (~mask_curr_nan) & (~mask_arr_nan)
        current_max[both_valid] = np.maximum(current_max[both_valid], arr[both_valid])
        # Original notebook comment normalized for the public code archive.
        S_annual_max[idx] = current_max

    return np.array(years, dtype=int), S_annual_max


def compute_return_thresholds_gumbel(S_annual_max, years_all, base_start, base_end, return_periods):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    Ny, rows, cols = S_annual_max.shape
    years_all = np.asarray(years_all, dtype=int)

    # Original notebook comment normalized for the public code archive.
    mask_base = (years_all >= base_start) & (years_all <= base_end)
    if not mask_base.any():
        raise RuntimeError("基准期内没有年份，请检查 BASE_START_YEAR/BASE_END_YEAR。")

    S_base = S_annual_max[mask_base]  # (Nbase, rows, cols)
    Nbase = S_base.shape[0]
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    n_cells = rows * cols
    S_flat = S_base.reshape((Nbase, n_cells))

    thresholds = {T: np.full(n_cells, np.nan, dtype=np.float32) for T in return_periods}

    for j in range(n_cells):
        series = S_flat[:, j]
        series = series[np.isfinite(series)]
        if series.size < MIN_YEARS_FOR_FIT:
            continue

        # Original notebook comment normalized for the public code archive.
        series = series[series > 0]
        if series.size < MIN_YEARS_FOR_FIT:
            continue

        try:
            loc, scale = gumbel_r.fit(series)
        except Exception:
            continue
        if not np.isfinite(loc) or not np.isfinite(scale) or scale <= 0:
            continue

        for T in return_periods:
            p = 1.0 - 1.0 / float(T)
            q = gumbel_r.ppf(p, loc=loc, scale=scale)
            if np.isfinite(q):
                thresholds[T][j] = float(q)

    # Original notebook comment normalized for the public code archive.
    thr_grids = {T: thresholds[T].reshape((rows, cols)) for T in return_periods}
    return thr_grids


def compute_county_year_events(years_all,
                               S_annual_max,
                               thr_grids,
                               county_id_full,
                               map_df,
                               analysis_start,
                               analysis_end,
                               return_periods):
    """Archived notebook note for 01_build_county_return_period_flood_events.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    years_all = np.asarray(years_all, dtype=int)
    Ny, rows, cols = S_annual_max.shape

    # Archived notebook metadata.
    year_to_idx = {int(y): i for i, y in enumerate(years_all)}

    analysis_years = [int(y) for y in years_all
                      if analysis_start <= y <= analysis_end and int(y) in year_to_idx]
    analysis_years = sorted(set(analysis_years))
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    all_year_dfs = []

    valid_mask = county_id_full > 0

    for y in analysis_years:
        idx = year_to_idx[y]
        S_year = S_annual_max[idx]  # (rows, cols)

        df_year = map_df.copy()
        df_year.insert(0, "year", y)

        for T in return_periods:
            thr = thr_grids[T]  # (rows, cols)
            # Original notebook comment normalized for the public code archive.
            event_grid = (S_year >= thr) & np.isfinite(thr) & valid_mask

            cids_event = county_id_full[event_grid]
            if cids_event.size > 0:
                uniq_cids = np.unique(cids_event.astype(np.int32))
                flag_dict = {int(cid): 1 for cid in uniq_cids}
            else:
                flag_dict = {}

            colname = f"flood_ge_T{T}"
            df_year[colname] = df_year["county_id"].map(flag_dict).fillna(0).astype(np.int8)

        all_year_dfs.append(df_year)

    df_all = pd.concat(all_year_dfs, ignore_index=True)
    return df_all


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    sample_json = find_sample_json(STOR_P50_ROOT)
    rows, cols, dtp, scl, nan_code, transform, crs = prepare_storge_meta(sample_json)
    ny, nx = rows, cols
    print(f"[INFO] storge P50 grid: {nx} x {ny}, crs={crs}")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    pix_area_full = pixel_area_raster(transform, (ny, nx))

    print("[INFO] Notebook progress message.")
    county_id_full, map_df = rasterize_counties(
        transform, (ny, nx), COUNTY_SHP, COUNTY_ID_FIELD, COUNTY_NAME_FIELD
    )
    df_area = compute_county_area(county_id_full, pix_area_full, map_df)
    area_csv = os.path.join(OUT_DIR, "county_total_area_storage.csv")
    df_area.to_csv(area_csv, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    bin_list = list_storge_bin_files(STOR_P50_ROOT, BASE_START_YEAR, BASE_END_YEAR)
    if not bin_list:
        raise RuntimeError("未找到任何 storge P50 bin 文件，请检查 STOR_P50_ROOT 与年份设置。")

    print("[INFO] Notebook progress message.")
    years_all, S_annual_max = compute_annual_max_storage(
        bin_list, rows, cols, dtp, scl, nan_code
    )

    # Gumbel return-period processing.
    print("[INFO] Notebook progress message.")
    thr_grids = compute_return_thresholds_gumbel(
        S_annual_max, years_all, BASE_START_YEAR, BASE_END_YEAR, RETURN_PERIODS
    )

    # Original notebook comment normalized for the public code archive.
    thr_path = os.path.join(OUT_DIR, "storge_return_thresholds_gumbel.npz")
    np.savez_compressed(thr_path, years=years_all, **{f"thr_T{T}": thr_grids[T] for T in RETURN_PERIODS})
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    df_events = compute_county_year_events(
        years_all,
        S_annual_max,
        thr_grids,
        county_id_full,
        map_df,
        ANALYSIS_START_YEAR,
        ANALYSIS_END_YEAR,
        RETURN_PERIODS
    )

    out_csv = os.path.join(OUT_DIR, f"county_flood_events_T10_20_50_100_{ANALYSIS_START_YEAR}_{ANALYSIS_END_YEAR}.csv")
    df_events.to_csv(out_csv, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
