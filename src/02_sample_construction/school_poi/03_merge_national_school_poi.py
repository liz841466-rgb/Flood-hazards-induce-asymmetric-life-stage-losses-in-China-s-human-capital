#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_merge_national_school_poi.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_merge_national_school_poi.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path

import pandas as pd
import geopandas as gpd


# =============================================================================
BASE_DIR = Path(r"D:\GISdata\school_result\L3")   # Original notebook comment normalized for the public code archive.
OUT_DIR  = Path(r"D:\GISdata\school_result\ALL")  # Original notebook comment normalized for the public code archive.
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
OUT_SHP = OUT_DIR / "china_school_L3.shp"


def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    """Archived notebook note for 03_merge_national_school_poi.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    encodings = [None, "utf-8", "gbk", "gb18030", "latin1"]

    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print("[INFO] Notebook progress message.")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print("[INFO] Notebook progress message.")
            return gdf
        except UnicodeDecodeError as e:
            print("[INFO] Notebook progress message.")
            last_err = e
        except Exception as e:
            # Original notebook comment normalized for the public code archive.
            print("[INFO] Notebook progress message.")
            last_err = e

    # Original notebook comment normalized for the public code archive.
    raise RuntimeError(f"无法用多种编码读取 {shp_path}") from last_err


def main():
    # School POI processing note.
    shp_files = sorted(
        p for p in BASE_DIR.iterdir()
        if p.suffix.lower() == ".shp" and p.name.endswith("_school.shp")
    )

    if not shp_files:
        raise RuntimeError(f"在 {BASE_DIR} 下未找到 *_school.shp")

    print("[INFO] Notebook progress message.", len(shp_files))
    for p in shp_files:
        print("  -", p.name)

    gdfs = []
    all_cols = set()

    # Original notebook comment normalized for the public code archive.
    for shp in shp_files:
        gdf = read_shp_safe(shp)

        # School POI processing note.
        prov = shp.name.replace("_school.shp", "")
        gdf["prov"] = prov   # Original notebook comment normalized for the public code archive.

        gdfs.append(gdf)
        all_cols |= set(gdf.columns)

    # Original notebook comment normalized for the public code archive.
    all_cols = list(all_cols)
    # Original notebook comment normalized for the public code archive.
    if "geometry" in all_cols:
        all_cols = [c for c in all_cols if c != "geometry"] + ["geometry"]

    aligned_gdfs = []
    for gdf in gdfs:
        # Original notebook comment normalized for the public code archive.
        for col in all_cols:
            if col not in gdf.columns:
                gdf[col] = None
        # Original notebook comment normalized for the public code archive.
        aligned_gdfs.append(gdf[all_cols])

    # Original notebook comment normalized for the public code archive.
    g_all = gpd.GeoDataFrame(
        pd.concat(aligned_gdfs, ignore_index=True),
        crs=aligned_gdfs[0].crs  # Original notebook comment normalized for the public code archive.
    )

    # Shapefile output note.
    g_all.to_file(OUT_SHP, encoding="utf-8")
    print("[INFO] Notebook progress message.", OUT_SHP)
    print("[INFO] Notebook progress message.", len(g_all))


if __name__ == "__main__":
    main()
