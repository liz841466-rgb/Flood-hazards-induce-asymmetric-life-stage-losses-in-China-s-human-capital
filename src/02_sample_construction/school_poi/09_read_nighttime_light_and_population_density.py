#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_read_nighttime_light_and_population_density.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
import os
import re
import rasterio

NIGHT_ROOT = r"D:\GISdata\Night_Light\yunnan"

# Original notebook comment normalized for the public code archive.
YEAR_RE = re.compile(r'.*?(19|20)\d{2}.*\.tif$', re.IGNORECASE)

def main():
    if not os.path.isdir(NIGHT_ROOT):
        raise RuntimeError(f"夜光目录不存在：{NIGHT_ROOT}")

    tif_files = [f for f in os.listdir(NIGHT_ROOT)
                 if f.lower().endswith(".tif")]

    if not tif_files:
        print("[INFO] Notebook progress message.")
        return

    records = []

    for fname in sorted(tif_files):
        m = YEAR_RE.match(fname)
        year = int(re.search(r'(19|20)\d{2}', fname).group()) if m else None

        fpath = os.path.join(NIGHT_ROOT, fname)

        try:
            with rasterio.open(fpath) as src:
                rec = {
                    "year": year,
                    "name": fname,
                    "path": fpath,
                    "width": src.width,
                    "height": src.height,
                    "crs": str(src.crs),
                    "transform": src.transform,
                    "dtype": str(src.dtypes[0]),
                    "count": src.count,
                    "nodata": src.nodata
                }
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        records.append(rec)

    if not records:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    records.sort(key=lambda r: (9999 if r["year"] is None else r["year"], r["name"]))

    print("[INFO] Notebook progress message.")
    for r in records:
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        print(f"  CRS: {r['crs']}")
        print("[INFO] Notebook progress message.")
        print(f"  dtype: {r['dtype']}, nodata: {r['nodata']}")
        print("[INFO] Notebook progress message.")
        print("-" * 60)

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
import os
import re
import rasterio

POP_ROOT = r"D:\GISdata\PopulationDensity\worldpop云南省"

# Original notebook comment normalized for the public code archive.
YEAR_RE = re.compile(r'.*?(19|20)\d{2}.*\.tif$', re.IGNORECASE)

def main():
    if not os.path.isdir(POP_ROOT):
        raise RuntimeError(f"人口密度目录不存在：{POP_ROOT}")

    tif_files = [f for f in os.listdir(POP_ROOT)
                 if f.lower().endswith(".tif")]

    if not tif_files:
        print("[INFO] Notebook progress message.")
        return

    records = []

    for fname in sorted(tif_files):
        m = YEAR_RE.match(fname)
        year = int(re.search(r'(19|20)\d{2}', fname).group()) if m else None

        fpath = os.path.join(POP_ROOT, fname)

        try:
            with rasterio.open(fpath) as src:
                rec = {
                    "year": year,
                    "name": fname,
                    "path": fpath,
                    "width": src.width,
                    "height": src.height,
                    "crs": str(src.crs),
                    "transform": src.transform,
                    "dtype": str(src.dtypes[0]),
                    "count": src.count,
                    "nodata": src.nodata
                }
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        records.append(rec)

    if not records:
        print("[INFO] Notebook progress message.")
        return

    records.sort(key=lambda r: (9999 if r["year"] is None else r["year"], r["name"]))

    print("[INFO] Notebook progress message.")
    for r in records:
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        print(f"  CRS: {r['crs']}")
        print("[INFO] Notebook progress message.")
        print(f"  dtype: {r['dtype']}, nodata: {r['nodata']}")
        print("[INFO] Notebook progress message.")
        print("-" * 60)

if __name__ == "__main__":
    main()
