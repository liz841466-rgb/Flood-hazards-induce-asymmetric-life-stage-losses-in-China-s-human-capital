#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_extract_euluc_clcd_for_school_points.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_extract_euluc_clcd_for_school_points.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol

# =============================================================================

# Original notebook comment normalized for the public code archive.
PROV_NAME = "云南省"
PROV_SLUG = "yunnan"

# Original notebook comment normalized for the public code archive.
CLCD_ROOT    = rf"D:\GISdata\landcover"                 # Original notebook comment normalized for the public code archive.
EULUC_SHP    = rf"D:\GISdata\EULUC\24{PROV_SLUG}.shp"   # Original notebook comment normalized for the public code archive.
SCHOOL_SHP   = rf"D:\GISdata\CHINA_SCHOOL\yunnan_小学_中学.shp"

OUT_DIR      = rf"D:\GISdata\school_result\clcd_simple"
os.makedirs(OUT_DIR, exist_ok=True)

OUT_SHP      = os.path.join(OUT_DIR, f"{PROV_SLUG}_school_clcd_simple.shp")
OUT_XLSX     = os.path.join(OUT_DIR, f"{PROV_SLUG}_school_clcd_simple.xlsx")

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
EULUC_MASK_CLASSES = [7]   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
LATEST_YEAR_REQUIRED = 2024

# =============================================================================

def index_clcd_files():
    """Archived notebook note for 06_extract_euluc_clcd_for_school_points.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pattern = re.compile(
        rf"CLCD_v01_(\d{{4}})_albert_{PROV_SLUG}\.tif$",
        re.IGNORECASE
    )
    year_files = {}
    ref_crs = ref_transform = None
    ref_w = ref_h = None
    ref_nodata = None

    for root, _, files in os.walk(CLCD_ROOT):
        for fname in files:
            m = pattern.search(fname)
            if not m:
                continue
            year = int(m.group(1))
            path = os.path.join(root, fname)
            with rasterio.open(path) as src:
                if ref_crs is None:
                    ref_crs = src.crs
                    ref_transform = src.transform
                    ref_w, ref_h = src.width, src.height
                    ref_nodata = src.nodata
                else:
                    if src.crs != ref_crs:
                        raise ValueError(f"{fname} CRS 不一致")
                    if (src.transform != ref_transform or
                        src.width != ref_w or src.height != ref_h):
                        raise ValueError(f"{fname} 网格参数不一致")
            year_files[year] = path

    if not year_files:
        raise RuntimeError(f"未在 {CLCD_ROOT} 找到 {PROV_SLUG} 的 CLCD_v01_YYYY_albert_{PROV_SLUG}.tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)

    if LATEST_YEAR_REQUIRED not in years:
        print("[INFO] Notebook progress message.")
    return years, year_files, ref_crs, ref_transform, ref_w, ref_h, ref_nodata


def earliest_stable_year_equal_cur(values, years, nodata=None):
    """Archived notebook note for 06_extract_euluc_clcd_for_school_points.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    vals = np.array(values)
    yrs = np.array(years)
    if len(vals) == 0:
        return None

    val_cur = vals[-1]
    if nodata is not None and val_cur == nodata:
        return None
    if np.isnan(val_cur):
        return None
    # Original notebook comment normalized for the public code archive.
    if int(val_cur) == 0:
        return None

    # Original notebook comment normalized for the public code archive.
    i = len(vals) - 1
    # Original notebook comment normalized for the public code archive.
    while i >= 0:
        v = vals[i]
        if np.isnan(v):
            break
        if nodata is not None and v == nodata:
            break
        if v != val_cur:
            break
        i -= 1
    start_idx = i + 1

    if start_idx >= len(vals):  # Original notebook comment normalized for the public code archive.
        return None

    return int(yrs[start_idx])


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    (years,
     year_files,
     clcd_crs,
     clcd_transform,
     _, _, clcd_nodata) = index_clcd_files()

    # Original notebook comment normalized for the public code archive.
    if not os.path.exists(EULUC_SHP):
        raise FileNotFoundError(f"未找到省级 EULUC：{EULUC_SHP}")
    euluc = gpd.read_file(EULUC_SHP)
    if euluc.crs is None:
        raise ValueError("EULUC 缺少 CRS")
    # Original notebook comment normalized for the public code archive.
    if euluc.crs != clcd_crs:
        euluc = euluc.to_crs(clcd_crs)

    if "Class" not in euluc.columns:
        raise ValueError("EULUC 缺少 Class 字段")

    if EULUC_MASK_CLASSES is not None:
        mask = euluc["Class"].isin(EULUC_MASK_CLASSES)
        euluc = euluc[mask].copy()
        print("[INFO] Notebook progress message.")
        if euluc.empty:
            raise RuntimeError("EULUC 掩膜后为空，请检查 Class 或配置")

    # Original notebook comment normalized for the public code archive.
    if not os.path.exists(SCHOOL_SHP):
        raise FileNotFoundError(f"未找到学校点数据：{SCHOOL_SHP}")
    schools = gpd.read_file(SCHOOL_SHP)
    if schools.crs is None:
        raise ValueError("学校点缺少 CRS")
    # Original notebook comment normalized for the public code archive.
    if schools.crs != clcd_crs:
        schools = schools.to_crs(clcd_crs)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    schools = gpd.sjoin(schools, euluc[["Class", "geometry"]],
                        how="left", predicate="within")
    # Original notebook comment normalized for the public code archive.
    if "index_right" in schools.columns:
        schools = schools.drop(columns=["index_right"])
    # Original notebook comment normalized for the public code archive.
    in_mask = ~schools["Class"].isna()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    points = [(geom.x, geom.y) if geom is not None else (np.nan, np.nan)
              for geom in schools.geometry]

    n = len(schools)
    t = len(years)
    clcd_ts = np.full((n, t), np.nan, dtype=float)

    print("[INFO] Notebook progress message.")
    for j, y in enumerate(years):
        path = year_files[y]
        with rasterio.open(path) as src:
            # Original notebook comment normalized for the public code archive.
            vals = []
            for (x, yo) in points:
                if np.isnan(x) or np.isnan(yo):
                    vals.append(np.nan)
                else:
                    try:
                        v = next(src.sample([(x, yo)]))[0]
                    except StopIteration:
                        v = np.nan
                    # Original notebook comment normalized for the public code archive.
                    if clcd_nodata is not None and v == clcd_nodata:
                        v = np.nan
                    vals.append(float(v) if v is not None else np.nan)
            clcd_ts[:, j] = np.array(vals, dtype=float)

    # Original notebook comment normalized for the public code archive.
    build_year = np.full(n, np.nan, dtype=float)
    latest_year = max(years)

    for i in range(n):
        if not in_mask.iloc[i]:
            continue
        series = clcd_ts[i, :]
        by = earliest_stable_year_equal_cur(series, years, nodata=None)
        # Original notebook comment normalized for the public code archive.
        if by is not None:
            # Original notebook comment normalized for the public code archive.
            build_year[i] = by

    # Original notebook comment normalized for the public code archive.
    out = schools.copy()
    out["build_year_clcd"] = build_year
    # Original notebook comment normalized for the public code archive.
    out["in_euluc_mask"] = in_mask
    out["has_build_year"] = ~np.isnan(build_year)

    # Original notebook comment normalized for the public code archive.
    # Shapefile output note.
    out.to_file(OUT_SHP, encoding="utf-8")
    out.drop(columns="geometry").to_excel(OUT_XLSX, index=False)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.", OUT_SHP)
    print("[INFO] Notebook progress message.", OUT_XLSX)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()
