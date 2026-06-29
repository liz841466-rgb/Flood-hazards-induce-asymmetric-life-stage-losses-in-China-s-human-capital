#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import numpy as np
import rasterio as rio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
import pyogrio
from shapely.ops import unary_union
from shapely.geometry import mapping
import csv
import matplotlib.pyplot as plt
from affine import Affine

# =============================================================================
BASE_ROOT       = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD"

GFD_EVT_ROOT    = os.path.join(BASE_ROOT, "events")               # External flood dataset comparison note.
CAMA_UNION_ROOT = os.path.join(BASE_ROOT, "cama_cama_union_raw")  # CaMa-Flood processing note.

CHINA_SHP       = r"/home/ll/jupyter_notebook/gis_data/China/china_2/china_2.shp"
YEARS           = list(range(2000, 2019))

# Original notebook comment normalized for the public code archive.
OUT_EVENT_CSV   = os.path.join(BASE_ROOT, "event_POD_FAR_CSI_stats.csv")
# Original notebook comment normalized for the public code archive.
OUT_POD_HIST    = os.path.join(BASE_ROOT, "event_POD_hist.png")
# Original notebook comment normalized for the public code archive.
OUT_POD_TIF     = os.path.join(BASE_ROOT, "event_POD_series.tif")

# ======================

def parse_event_name(dirname: str):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return dirname

def parse_event_key_from_name(name: str):
    """For printing / CSV: GFD_1627_From_20000830_to_20000910 -> 20000830_20000910"""
    m = re.search(r"From_(\d{8})_to_(\d{8})", name)
    if not m:
        return name
    return f"{m.group(1)}_{m.group(2)}"

def load_china_geom(shp_path):
    gdf = pyogrio.read_dataframe(shp_path, read_geometry=True, force_2d=True)
    if gdf.empty:
        raise RuntimeError("china_2.shp 中没有要素")
    geom = unary_union(gdf.geometry.values)
    if geom.is_empty:
        raise RuntimeError("中国边界几何为空")
    return geom

def make_china_mask_on_gfd(gfd_ds, china_geom):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    h, w = gfd_ds.height, gfd_ds.width
    mask = geometry_mask(
        [mapping(china_geom)],
        out_shape=(h, w),
        transform=gfd_ds.transform,
        invert=True
    )
    return mask

def reproject_cama_union_to_gfd(cama_ds, gfd_ds):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    src = cama_ds.read(1)
    src_nodata = cama_ds.nodata
    if src_nodata is None:
        # Original notebook comment normalized for the public code archive.
        src_nodata = 255

    dst = np.full((gfd_ds.height, gfd_ds.width), 255, dtype=np.uint8)

    reproject(
        source=src,
        destination=dst,
        src_transform=cama_ds.transform,
        src_crs=cama_ds.crs,
        src_nodata=src_nodata,
        dst_transform=gfd_ds.transform,
        dst_crs=gfd_ds.crs,
        dst_nodata=255,
        resampling=Resampling.nearest,
    )
    return dst, 255

def compute_event_stats(gfd_evt_path, cama_union_path, china_geom):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rio.open(gfd_evt_path) as gfd_ds, rio.open(cama_union_path) as cama_ds:
        # External flood dataset comparison note.
        china_mask = make_china_mask_on_gfd(gfd_ds, china_geom)

        # --- GFD bands ---
        b1 = gfd_ds.read(1, masked=True)  # flooded
        b5 = gfd_ds.read(5, masked=True)  # perm water

        # External flood dataset comparison note.
        valid_gfd = (~b1.mask) & (~b5.mask)

        # External flood dataset comparison note.
        is_perm = valid_gfd & (b5.data == 1)

        # =============================================================================
        cama_on_gfd, cama_nodata = reproject_cama_union_to_gfd(cama_ds, gfd_ds)
        cama_valid = (cama_on_gfd != cama_nodata)

        # CaMa-Flood processing note.
        cama_is_flood = (cama_on_gfd == 1)

        # =============================================================================
        # External flood dataset comparison note.
        domain = china_mask & valid_gfd & cama_valid & (~is_perm)

        if not np.any(domain):
            return 0, 0, 0, 0

        # External flood dataset comparison note.
        gfd_flood = domain & (b1.data == 1)
        # CaMa-Flood processing note.
        cama_flood = domain & cama_is_flood

        # Original notebook comment normalized for the public code archive.
        TP = int(np.count_nonzero(gfd_flood & cama_flood))
        FP = int(np.count_nonzero(~gfd_flood & cama_flood))
        FN = int(np.count_nonzero(gfd_flood & ~cama_flood))
        GFD_CN = int(np.count_nonzero(gfd_flood))

        return GFD_CN, TP, FP, FN

def safe_ratio(num, den):
    return float(num) / float(den) if den > 0 else np.nan

def main():
    # Original notebook comment normalized for the public code archive.
    china_geom = load_china_geom(CHINA_SHP)

    # Original notebook comment normalized for the public code archive.
    year_GFD = {y: 0 for y in YEARS}
    year_TP  = {y: 0 for y in YEARS}
    year_FP  = {y: 0 for y in YEARS}
    year_FN  = {y: 0 for y in YEARS}

    total_events = 0      # Original notebook comment normalized for the public code archive.
    used_events  = 0      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    pod_values = []       # Original notebook comment normalized for the public code archive.
    pod_meta   = []       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    os.makedirs(os.path.dirname(OUT_EVENT_CSV), exist_ok=True)
    csv_f = open(OUT_EVENT_CSV, "w", newline="", encoding="utf-8")
    writer = csv.writer(csv_f)
    writer.writerow([
        "year", "event_dir", "event_key",
        "GFD_CN", "TP_CN", "FP_CN", "FN_CN",
        "POD", "FAR", "CSI"
    ])

    print("[INFO] Notebook progress message.")

    for year in YEARS:
        evt_year_dir  = os.path.join(GFD_EVT_ROOT, str(year))
        cama_year_dir = os.path.join(CAMA_UNION_ROOT, str(year))

        if not os.path.isdir(evt_year_dir):
            continue
        if not os.path.isdir(cama_year_dir):
            print("[INFO] Notebook progress message.")
            continue

        for evt_dir in sorted(os.listdir(evt_year_dir)):
            evt_path = os.path.join(evt_year_dir, evt_dir)
            if not os.path.isdir(evt_path):
                continue

            base = parse_event_name(evt_dir)
            key  = parse_event_key_from_name(base)

            gfd_evt_tif = os.path.join(evt_path, f"{base}.tif")
            if not os.path.exists(gfd_evt_tif):
                print("[INFO] Notebook progress message.")
                continue

            cama_union_tif = os.path.join(cama_year_dir, f"{base}_CAMA_union.tif")
            if not os.path.exists(cama_union_tif):
                print("[INFO] Notebook progress message.")
                continue

            total_events += 1

            try:
                GFD_CN, TP_CN, FP_CN, FN_CN = compute_event_stats(
                    gfd_evt_tif, cama_union_tif, china_geom
                )

                # Original notebook comment normalized for the public code archive.
                if (GFD_CN + TP_CN + FP_CN + FN_CN) == 0:
                    print("[INFO] Notebook progress message.")
                    continue

                # External flood dataset comparison note.
                if GFD_CN == 0:
                    print("[INFO] Notebook progress message.")
                    continue

                # External flood dataset comparison note.
                POD = safe_ratio(TP_CN, GFD_CN)          # Original notebook comment normalized for the public code archive.
                FAR = safe_ratio(FP_CN, TP_CN + FP_CN)
                CSI = safe_ratio(TP_CN, TP_CN + FP_CN + FN_CN)

                # Original notebook comment normalized for the public code archive.
                year_GFD[year] += GFD_CN
                year_TP[year]  += TP_CN
                year_FP[year]  += FP_CN
                year_FN[year]  += FN_CN

                used_events += 1

                # Original notebook comment normalized for the public code archive.
                if np.isfinite(POD):
                    pod_values.append(POD)
                    pod_meta.append((year, evt_dir, POD))

                writer.writerow([
                    year, evt_dir, key,
                    GFD_CN, TP_CN, FP_CN, FN_CN,
                    POD, FAR, CSI
                ])

                print(
                    f"[{year}][{key}] "
                    f"GFD_CN={GFD_CN}, TP={TP_CN}, FP={FP_CN}, FN={FN_CN}, "
                    f"POD={POD:.4f} "
                    f"FAR={FAR:.4f} "
                    f"CSI={CSI:.4f}"
                )

            except Exception as e:
                print("[INFO] Notebook progress message.")

    csv_f.close()

    # =============================================================================
    print("[INFO] Notebook progress message.")

    total_GFD = 0
    total_TP  = 0
    total_FP  = 0
    total_FN  = 0

    for y in YEARS:
        D  = year_GFD[y]
        TP = year_TP[y]
        FP = year_FP[y]
        FN = year_FN[y]

        if (D + TP + FP + FN) == 0:
            print("[INFO] Notebook progress message.")
            continue

        pod_y = safe_ratio(TP, D) if D > 0 else np.nan
        far_y = safe_ratio(FP, TP + FP)
        csi_y = safe_ratio(TP, TP + FP + FN)

        print(
            f"{y}: POD={pod_y:.4f}, FAR={far_y:.4f}, CSI={csi_y:.4f} "
            f"(GFD_CN={D}, TP={TP}, FP={FP}, FN={FN})"
        )

        total_GFD += D
        total_TP  += TP
        total_FP  += FP
        total_FN  += FN

    # =============================================================================
    print("[INFO] Notebook progress message.")
    if (total_GFD + total_TP + total_FP + total_FN) == 0:
        print("[INFO] Notebook progress message.")
    else:
        pod_all = safe_ratio(total_TP, total_GFD) if total_GFD > 0 else np.nan
        far_all = safe_ratio(total_FP, total_TP + total_FP)
        csi_all = safe_ratio(total_TP, total_TP + total_FP + total_FN)

        print(
            f"POD_all={pod_all:.4f}, FAR_all={far_all:.4f}, CSI_all={csi_all:.4f}  "
            f"(ΣGFD_CN={total_GFD}, ΣTP={total_TP}, ΣFP={total_FP}, ΣFN={total_FN}, "
            f"使用事件={used_events}/{total_events})"
        )

    # =============================================================================
    pod_arr = np.array(pod_values, dtype=float)
    pod_arr = pod_arr[np.isfinite(pod_arr)]

    if pod_arr.size == 0:
        print("[INFO] Notebook progress message.")
        return

    plt.figure(figsize=(6, 4))
    plt.hist(pod_arr, bins=20, range=(0.0, 1.0), edgecolor="black")
    plt.xlabel("Event-level POD")
    plt.ylabel("Number of events")
    plt.title("Distribution of event-level POD (CaMa vs GFD)")
    plt.tight_layout()
    plt.savefig(OUT_POD_HIST, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    n_events = pod_arr.size
    height = 1
    width = n_events

    # Original notebook comment normalized for the public code archive.
    transform = Affine(1.0, 0.0, 0.0,
                       0.0, -1.0, 0.0)

    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "height": height,
        "width": width,
        "count": 1,
        "crs": None,          # Original notebook comment normalized for the public code archive.
        "transform": transform,
        "compress": "DEFLATE",
        "predictor": 2,
        "zlevel": 6,
        "tiled": False,
        "nodata": -9999.0,
    }

    data_out = np.full((height, width), -9999.0, dtype=np.float32)
    data_out[0, :n_events] = pod_arr.astype(np.float32)

    with rio.open(OUT_POD_TIF, "w", **profile) as dst:
        dst.write(data_out, 1)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import numpy as np
import rasterio as rio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
from rasterio.transform import xy as rio_xy
from affine import Affine
import pyogrio
from shapely.ops import unary_union
from shapely.geometry import mapping
import csv
import matplotlib.pyplot as plt

# =============================================================================
BASE_ROOT       = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD"

GFD_EVT_ROOT    = os.path.join(BASE_ROOT, "events")               # External flood dataset comparison note.
CAMA_UNION_ROOT = os.path.join(BASE_ROOT, "cama_cama_union_raw")  # CaMa-Flood processing note.

CHINA_SHP       = r"/home/ll/jupyter_notebook/gis_data/China/china_2/china_2.shp"
YEARS           = list(range(2000, 2019))

# Original notebook comment normalized for the public code archive.
OUT_EVENT_CSV   = os.path.join(BASE_ROOT, "event_POD_FAR_CSI_stats.csv")
# Original notebook comment normalized for the public code archive.
OUT_POD_HIST    = os.path.join(BASE_ROOT, "event_POD_hist.png")
# Original notebook comment normalized for the public code archive.
OUT_POD_TIF     = os.path.join(BASE_ROOT, "event_POD_map.tif")

# Original notebook comment normalized for the public code archive.
GRID_DX_DEG     = 0.25

# ======================

def parse_event_name(dirname: str):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return dirname

def parse_event_key_from_name(name: str):
    """For printing / CSV: GFD_1627_From_20000830_to_20000910 -> 20000830_20000910"""
    m = re.search(r"From_(\d{8})_to_(\d{8})", name)
    if not m:
        return name
    return f"{m.group(1)}_{m.group(2)}"

def load_china_geom(shp_path):
    gdf = pyogrio.read_dataframe(shp_path, read_geometry=True, force_2d=True)
    if gdf.empty:
        raise RuntimeError("china_2.shp 中没有要素")
    # External flood dataset comparison note.
    geom = unary_union(gdf.geometry.values)
    if geom.is_empty:
        raise RuntimeError("中国边界几何为空")
    return geom

def make_china_mask_on_gfd(gfd_ds, china_geom):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    h, w = gfd_ds.height, gfd_ds.width
    mask = geometry_mask(
        [mapping(china_geom)],
        out_shape=(h, w),
        transform=gfd_ds.transform,
        invert=True
    )
    return mask

def reproject_cama_union_to_gfd(cama_ds, gfd_ds):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    src = cama_ds.read(1)
    src_nodata = cama_ds.nodata
    if src_nodata is None:
        # Original notebook comment normalized for the public code archive.
        src_nodata = 255

    dst = np.full((gfd_ds.height, gfd_ds.width), 255, dtype=np.uint8)

    reproject(
        source=src,
        destination=dst,
        src_transform=cama_ds.transform,
        src_crs=cama_ds.crs,
        src_nodata=src_nodata,
        dst_transform=gfd_ds.transform,
        dst_crs=gfd_ds.crs,
        dst_nodata=255,
        resampling=Resampling.nearest,
    )
    return dst, 255

def compute_event_stats_and_centroid(gfd_evt_path, cama_union_path, china_geom):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rio.open(gfd_evt_path) as gfd_ds, rio.open(cama_union_path) as cama_ds:
        # External flood dataset comparison note.
        china_mask = make_china_mask_on_gfd(gfd_ds, china_geom)

        # --- GFD bands ---
        b1 = gfd_ds.read(1, masked=True)  # flooded
        b5 = gfd_ds.read(5, masked=True)  # perm water

        # External flood dataset comparison note.
        valid_gfd = (~b1.mask) & (~b5.mask)

        # External flood dataset comparison note.
        is_perm = valid_gfd & (b5.data == 1)

        # =============================================================================
        cama_on_gfd, cama_nodata = reproject_cama_union_to_gfd(cama_ds, gfd_ds)
        cama_valid = (cama_on_gfd != cama_nodata)

        # CaMa-Flood processing note.
        cama_is_flood = (cama_on_gfd == 1)

        # =============================================================================
        # External flood dataset comparison note.
        domain = china_mask & valid_gfd & cama_valid & (~is_perm)

        if not np.any(domain):
            return 0, 0, 0, 0, None, None

        # External flood dataset comparison note.
        gfd_flood = domain & (b1.data == 1)
        # CaMa-Flood processing note.
        cama_flood = domain & cama_is_flood

        # Original notebook comment normalized for the public code archive.
        TP = int(np.count_nonzero(gfd_flood & cama_flood))
        FP = int(np.count_nonzero(~gfd_flood & cama_flood))
        FN = int(np.count_nonzero(gfd_flood & ~cama_flood))
        GFD_CN = int(np.count_nonzero(gfd_flood))

        # External flood dataset comparison note.
        if GFD_CN > 0:
            rows, cols = np.where(gfd_flood)
            xs, ys = rio_xy(gfd_ds.transform, rows, cols)
            cent_x = float(np.mean(xs))
            cent_y = float(np.mean(ys))
        else:
            cent_x, cent_y = None, None

        return GFD_CN, TP, FP, FN, cent_x, cent_y

def safe_ratio(num, den):
    return float(num) / float(den) if den > 0 else np.nan

def build_pod_grid_from_events(china_geom, lon_list, lat_list, pod_list,
                               dx_deg=GRID_DX_DEG):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    lon_arr = np.array(lon_list, dtype=float)
    lat_arr = np.array(lat_list, dtype=float)
    pod_arr = np.array(pod_list, dtype=float)

    # Original notebook comment normalized for the public code archive.
    minx, miny, maxx, maxy = china_geom.bounds
    pad = dx_deg   # Original notebook comment normalized for the public code archive.
    minx -= pad
    miny -= pad
    maxx += pad
    maxy += pad

    nx = int(np.ceil((maxx - minx) / dx_deg))
    ny = int(np.ceil((maxy - miny) / dx_deg))

    # Original notebook comment normalized for the public code archive.
    transform = Affine(dx_deg, 0.0, minx,
                       0.0, -dx_deg, maxy)
    crs = "EPSG:4326"

    # Original notebook comment normalized for the public code archive.
    pod_sum = np.zeros((ny, nx), dtype=np.float64)
    pod_cnt = np.zeros((ny, nx), dtype=np.int32)

    for x, y, v in zip(lon_arr, lat_arr, pod_arr):
        if not np.isfinite(v):
            continue
        # Original notebook comment normalized for the public code archive.
        if (x < minx) or (x >= minx + nx * dx_deg):
            continue
        if (y < maxy - ny * dx_deg) or (y >= maxy):
            continue
        col = int((x - minx) / dx_deg)
        row = int((maxy - y) / dx_deg)
        if (row < 0) or (row >= ny) or (col < 0) or (col >= nx):
            continue
        pod_sum[row, col] += v
        pod_cnt[row, col] += 1

    pod_mean = np.full((ny, nx), np.nan, dtype=np.float32)
    valid = pod_cnt > 0
    pod_mean[valid] = (pod_sum[valid] / pod_cnt[valid]).astype(np.float32)

    # Original notebook comment normalized for the public code archive.
    china_mask = geometry_mask(
        [mapping(china_geom)],
        out_shape=(ny, nx),
        transform=transform,
        invert=True
    )
    pod_mean[~china_mask] = np.nan

    return pod_mean, transform, crs

def main():
    # Original notebook comment normalized for the public code archive.
    china_geom = load_china_geom(CHINA_SHP)

    # Original notebook comment normalized for the public code archive.
    year_GFD = {y: 0 for y in YEARS}
    year_TP  = {y: 0 for y in YEARS}
    year_FP  = {y: 0 for y in YEARS}
    year_FN  = {y: 0 for y in YEARS}

    total_events = 0      # Original notebook comment normalized for the public code archive.
    used_events  = 0      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    pod_values = []       # POD
    pod_lons   = []       # Original notebook comment normalized for the public code archive.
    pod_lats   = []       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    os.makedirs(os.path.dirname(OUT_EVENT_CSV), exist_ok=True)
    csv_f = open(OUT_EVENT_CSV, "w", newline="", encoding="utf-8")
    writer = csv.writer(csv_f)
    writer.writerow([
        "year", "event_dir", "event_key",
        "GFD_CN", "TP_CN", "FP_CN", "FN_CN",
        "POD", "FAR", "CSI",
        "cent_lon", "cent_lat"
    ])

    print("[INFO] Notebook progress message.")

    for year in YEARS:
        evt_year_dir  = os.path.join(GFD_EVT_ROOT, str(year))
        cama_year_dir = os.path.join(CAMA_UNION_ROOT, str(year))

        if not os.path.isdir(evt_year_dir):
            continue
        if not os.path.isdir(cama_year_dir):
            print("[INFO] Notebook progress message.")
            continue

        for evt_dir in sorted(os.listdir(evt_year_dir)):
            evt_path = os.path.join(evt_year_dir, evt_dir)
            if not os.path.isdir(evt_path):
                continue

            base = parse_event_name(evt_dir)
            key  = parse_event_key_from_name(base)

            gfd_evt_tif = os.path.join(evt_path, f"{base}.tif")
            if not os.path.exists(gfd_evt_tif):
                print("[INFO] Notebook progress message.")
                continue

            cama_union_tif = os.path.join(cama_year_dir, f"{base}_CAMA_union.tif")
            if not os.path.exists(cama_union_tif):
                print("[INFO] Notebook progress message.")
                continue

            total_events += 1

            try:
                (GFD_CN, TP_CN, FP_CN, FN_CN,
                 cent_x, cent_y) = compute_event_stats_and_centroid(
                    gfd_evt_tif, cama_union_tif, china_geom
                )

                # Original notebook comment normalized for the public code archive.
                if (GFD_CN + TP_CN + FP_CN + FN_CN) == 0:
                    print("[INFO] Notebook progress message.")
                    continue

                # External flood dataset comparison note.
                if GFD_CN == 0:
                    print("[INFO] Notebook progress message.")
                    continue

                # External flood dataset comparison note.
                POD = safe_ratio(TP_CN, GFD_CN)          # Original notebook comment normalized for the public code archive.
                FAR = safe_ratio(FP_CN, TP_CN + FP_CN)
                CSI = safe_ratio(TP_CN, TP_CN + FP_CN + FN_CN)

                # Original notebook comment normalized for the public code archive.
                year_GFD[year] += GFD_CN
                year_TP[year]  += TP_CN
                year_FP[year]  += FP_CN
                year_FN[year]  += FN_CN

                used_events += 1

                # Original notebook comment normalized for the public code archive.
                if np.isfinite(POD) and (cent_x is not None) and (cent_y is not None):
                    pod_values.append(POD)
                    pod_lons.append(cent_x)
                    pod_lats.append(cent_y)

                writer.writerow([
                    year, evt_dir, key,
                    GFD_CN, TP_CN, FP_CN, FN_CN,
                    POD, FAR, CSI,
                    cent_x, cent_y
                ])

                print(
                    f"[{year}][{key}] "
                    f"GFD_CN={GFD_CN}, TP={TP_CN}, FP={FP_CN}, FN={FN_CN}, "
                    f"POD={POD:.4f} "
                    f"FAR={FAR:.4f} "
                    f"CSI={CSI:.4f} "
                    f"cent=({cent_x:.3f}, {cent_y:.3f})"
                )

            except Exception as e:
                print("[INFO] Notebook progress message.")

    csv_f.close()

    # =============================================================================
    print("[INFO] Notebook progress message.")

    total_GFD = 0
    total_TP  = 0
    total_FP  = 0
    total_FN  = 0

    for y in YEARS:
        D  = year_GFD[y]
        TP = year_TP[y]
        FP = year_FP[y]
        FN = year_FN[y]

        if (D + TP + FP + FN) == 0:
            print("[INFO] Notebook progress message.")
            continue

        pod_y = safe_ratio(TP, D) if D > 0 else np.nan
        far_y = safe_ratio(FP, TP + FP)
        csi_y = safe_ratio(TP, TP + FP + FN)

        print(
            f"{y}: POD={pod_y:.4f}, FAR={far_y:.4f}, CSI={csi_y:.4f} "
            f"(GFD_CN={D}, TP={TP}, FP={FP}, FN={FN})"
        )

        total_GFD += D
        total_TP  += TP
        total_FP  += FP
        total_FN  += FN

    # =============================================================================
    print("[INFO] Notebook progress message.")
    if (total_GFD + total_TP + total_FP + total_FN) == 0:
        print("[INFO] Notebook progress message.")
    else:
        pod_all = safe_ratio(total_TP, total_GFD) if total_GFD > 0 else np.nan
        far_all = safe_ratio(total_FP, total_TP + total_FP)
        csi_all = safe_ratio(total_TP, total_TP + total_FP + total_FN)

        print(
            f"POD_all={pod_all:.4f}, FAR_all={far_all:.4f}, CSI_all={csi_all:.4f}  "
            f"(ΣGFD_CN={total_GFD}, ΣTP={total_TP}, ΣFP={total_FP}, ΣFN={total_FN}, "
            f"使用事件={used_events}/{total_events})"
        )

    # =============================================================================
    pod_arr = np.array(pod_values, dtype=float)
    pod_arr = pod_arr[np.isfinite(pod_arr)]

    if pod_arr.size == 0:
        print("[INFO] Notebook progress message.")
        return

    plt.figure(figsize=(6, 4))
    plt.hist(pod_arr, bins=20, range=(0.0, 1.0), edgecolor="black")
    plt.xlabel("Event-level POD")
    plt.ylabel("Number of events")
    plt.title("Distribution of event-level POD (CaMa vs GFD)")
    plt.tight_layout()
    plt.savefig(OUT_POD_HIST, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # =============================================================================
    pod_grid, grid_transform, grid_crs = build_pod_grid_from_events(
        china_geom, pod_lons, pod_lats, pod_values, dx_deg=GRID_DX_DEG
    )

    ny, nx = pod_grid.shape
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "height": ny,
        "width": nx,
        "count": 1,
        "crs": grid_crs,
        "transform": grid_transform,
        "compress": "DEFLATE",
        "predictor": 2,
        "zlevel": 6,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
        "nodata": -9999.0,
    }

    data_out = pod_grid.copy()
    data_out[~np.isfinite(data_out)] = -9999.0

    with rio.open(OUT_POD_TIF, "w", **profile) as dst:
        dst.write(data_out, 1)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import csv
import numpy as np
import rasterio as rio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
import pyogrio
from shapely.ops import unary_union, transform as shp_transform
from shapely.geometry import mapping
from pyproj import Transformer

# ======================
# Original notebook comment normalized for the public code archive.
# ======================
BASE_ROOT       = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD"
GFD_EVT_ROOT    = os.path.join(BASE_ROOT, "events")
CAMA_UNION_ROOT = os.path.join(BASE_ROOT, "cama_cama_union_raw")
CHINA_SHP       = r"/home/ll/jupyter_notebook/gis_data/China/china_2/china_2.shp"
YEARS           = list(range(2000, 2019))  # 2000-2019

CACHE_CSV = os.path.join(BASE_ROOT, "event_POD_cache_2000_2018.csv")
CACHE_NPZ = os.path.join(BASE_ROOT, "event_POD_cache_2000_2018.npz")


# ======================
# Original notebook comment normalized for the public code archive.
# ======================
def parse_event_key_from_name(name: str):
    m = re.search(r"From_(\d{8})_to_(\d{8})", name)
    if not m:
        return name
    return f"{m.group(1)}_{m.group(2)}"

def safe_ratio(num, den):
    return float(num) / float(den) if den > 0 else np.nan

def load_china_geom(shp_path):
    gdf = pyogrio.read_dataframe(shp_path, read_geometry=True, force_2d=True)
    if gdf.empty:
        raise RuntimeError("china_2.shp 中没有要素")
    geom = unary_union(gdf.geometry.values)
    if geom.is_empty:
        raise RuntimeError("中国边界几何为空")
    crs = getattr(gdf, "crs", None)
    return geom, crs

def reproject_geom_if_needed(geom, src_crs, dst_crs):
    if (src_crs is None) or (dst_crs is None):
        return geom
    try:
        s = rio.crs.CRS.from_user_input(src_crs)
        d = rio.crs.CRS.from_user_input(dst_crs)
    except Exception:
        return geom
    if s == d:
        return geom
    transformer = Transformer.from_crs(s, d, always_xy=True)
    return shp_transform(lambda x, y, z=None: transformer.transform(x, y), geom)

def make_china_mask_on_gfd(gfd_ds, china_geom, china_crs):
    gfd_crs = gfd_ds.crs if gfd_ds.crs is not None else "EPSG:4326"
    geom_on_gfd = reproject_geom_if_needed(china_geom, china_crs, gfd_crs)
    mask = geometry_mask(
        [mapping(geom_on_gfd)],
        out_shape=(gfd_ds.height, gfd_ds.width),
        transform=gfd_ds.transform,
        invert=True
    )
    return mask

def reproject_cama_union_to_gfd(cama_ds, gfd_ds):
    src = cama_ds.read(1)
    src_nodata = cama_ds.nodata
    if src_nodata is None:
        src_nodata = 255
    dst = np.full((gfd_ds.height, gfd_ds.width), 255, dtype=np.uint8)
    reproject(
        source=src,
        destination=dst,
        src_transform=cama_ds.transform,
        src_crs=cama_ds.crs,
        src_nodata=src_nodata,
        dst_transform=gfd_ds.transform,
        dst_crs=gfd_ds.crs,
        dst_nodata=255,
        resampling=Resampling.nearest,
    )
    return dst, 255

def compute_event_pod(gfd_evt_path, cama_union_path, china_geom, china_crs):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rio.open(gfd_evt_path) as gfd_ds, rio.open(cama_union_path) as cama_ds:
        china_mask = make_china_mask_on_gfd(gfd_ds, china_geom, china_crs)

        b1 = gfd_ds.read(1, masked=True)  # flooded
        b5 = gfd_ds.read(5, masked=True)  # perm water

        valid_gfd = (~b1.mask) & (~b5.mask)
        is_perm   = valid_gfd & (b5.data == 1)

        cama_on_gfd, cama_nodata = reproject_cama_union_to_gfd(cama_ds, gfd_ds)
        cama_valid    = (cama_on_gfd != cama_nodata)
        cama_is_flood = (cama_on_gfd == 1)

        domain = china_mask & valid_gfd & cama_valid & (~is_perm)
        if not np.any(domain):
            return np.nan, 0, 0, 0, 0

        gfd_flood  = domain & (b1.data == 1)
        cama_flood = domain & cama_is_flood

        TP = int(np.count_nonzero(gfd_flood & cama_flood))
        FP = int(np.count_nonzero(~gfd_flood & cama_flood))
        FN = int(np.count_nonzero(gfd_flood & ~cama_flood))
        GFD_CN = int(np.count_nonzero(gfd_flood))

        if GFD_CN == 0:
            return np.nan, GFD_CN, TP, FP, FN

        POD = safe_ratio(TP, GFD_CN)
        return POD, GFD_CN, TP, FP, FN


# ======================
# Original notebook comment normalized for the public code archive.
# ======================
def main():
    if os.path.exists(CACHE_NPZ) and os.path.exists(CACHE_CSV):
        print("[INFO] Notebook progress message.")
        return

    china_geom, china_crs = load_china_geom(CHINA_SHP)

    rows = []
    pod_list = []
    year_list = []
    key_list  = []

    total_matched = 0
    used_events   = 0

    for year in YEARS:
        evt_year_dir  = os.path.join(GFD_EVT_ROOT, str(year))
        cama_year_dir = os.path.join(CAMA_UNION_ROOT, str(year))
        if (not os.path.isdir(evt_year_dir)) or (not os.path.isdir(cama_year_dir)):
            continue

        for evt_dir in sorted(os.listdir(evt_year_dir)):
            evt_path = os.path.join(evt_year_dir, evt_dir)
            if not os.path.isdir(evt_path):
                continue

            base = evt_dir
            key  = parse_event_key_from_name(base)

            gfd_evt_tif   = os.path.join(evt_path, f"{base}.tif")
            cama_union_tif = os.path.join(cama_year_dir, f"{base}_CAMA_union.tif")
            if (not os.path.exists(gfd_evt_tif)) or (not os.path.exists(cama_union_tif)):
                continue

            total_matched += 1
            try:
                POD, GFD_CN, TP, FP, FN = compute_event_pod(
                    gfd_evt_tif, cama_union_tif, china_geom, china_crs
                )

                rows.append([year, evt_dir, key, GFD_CN, TP, FP, FN, POD])

                if np.isfinite(POD):
                    used_events += 1
                    pod_list.append(float(POD))
                    year_list.append(int(year))
                    key_list.append(key)

            except Exception as e:
                rows.append([year, evt_dir, key, 0, 0, 0, 0, np.nan])
                print("[INFO] Notebook progress message.")

    os.makedirs(os.path.dirname(CACHE_CSV), exist_ok=True)

    # Original notebook comment normalized for the public code archive.
    with open(CACHE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year","event_dir","event_key","GFD_CN","TP","FP","FN","POD"])
        w.writerows(rows)

    # Original notebook comment normalized for the public code archive.
    np.savez_compressed(
        CACHE_NPZ,
        pod=np.array(pod_list, dtype=np.float32),
        year=np.array(year_list, dtype=np.int16),
        event_key=np.array(key_list, dtype="U32"),
    )

    print("[INFO] Notebook progress message.")
    print(f"[SAVE] CSV: {CACHE_CSV}")
    print(f"[SAVE] NPZ: {CACHE_NPZ}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import matplotlib.pyplot as plt

BASE_ROOT = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD"
CACHE_NPZ = os.path.join(BASE_ROOT, "event_POD_cache_2000_2018.npz")
OUT_PNG   = os.path.join(BASE_ROOT, "event_POD_hist_from_cache_2000_2018.png")

def main():
    if not os.path.exists(CACHE_NPZ):
        raise FileNotFoundError(f"找不到缓存：{CACHE_NPZ}（请先运行 make_pod_cache_2000_2018.py）")

    data = np.load(CACHE_NPZ, allow_pickle=False)
    pod = data["pod"].astype(float)

    pod = pod[np.isfinite(pod)]
    if pod.size == 0:
        print("[INFO] Notebook progress message.")
        return

    plt.figure(figsize=(6, 4))
    plt.hist(pod, bins=20, range=(0.0, 1.0), edgecolor="black")
    plt.xlabel("Event-level POD")
    plt.ylabel("Number of events")
    plt.title("Distribution of event-level POD (CaMa vs GFD) | cache 2000–2018")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.close()

    print(f"[SAVE] {OUT_PNG}")
    print(f"[INFO] N={pod.size}, min={pod.min():.4f}, max={pod.max():.4f}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import rasterio as rio

# ======================
# Original notebook comment normalized for the public code archive.
# ======================
BASE_ROOT    = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD"
EVENTS_ROOT  = os.path.join(BASE_ROOT, "events")
OUT_ROOT     = os.path.join(EVENTS_ROOT, "GFD")  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
YEARS = list(range(2000, 2019))

# Original notebook comment normalized for the public code archive.
OUT_NODATA = 255  # uint8 nodata


def extract_one_event(gfd_evt_tif: str, out_tif: str):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rio.open(gfd_evt_tif) as src:
        if src.count < 1:
            raise RuntimeError("输入栅格没有 band1")

        b1 = src.read(1, masked=True)  # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        mask_invalid = np.ma.getmaskarray(b1)

        flood = np.zeros((src.height, src.width), dtype=np.uint8)
        flood[(~mask_invalid) & (b1.data == 1)] = 1
        flood[mask_invalid] = OUT_NODATA

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            count=1,
            dtype="uint8",
            nodata=OUT_NODATA,
            compress="DEFLATE",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            BIGTIFF="IF_SAFER",
        )

        os.makedirs(os.path.dirname(out_tif), exist_ok=True)
        with rio.open(out_tif, "w", **profile) as dst:
            dst.write(flood, 1)


def main():
    total = 0
    saved = 0
    skipped = 0

    for year in YEARS:
        year_dir = os.path.join(EVENTS_ROOT, str(year))
        if not os.path.isdir(year_dir):
            continue

        out_year_dir = os.path.join(OUT_ROOT, str(year))
        os.makedirs(out_year_dir, exist_ok=True)

        for evt_dir in sorted(os.listdir(year_dir)):
            evt_path = os.path.join(year_dir, evt_dir)
            if not os.path.isdir(evt_path):
                continue

            # Original notebook comment normalized for the public code archive.
            gfd_evt_tif = os.path.join(evt_path, f"{evt_dir}.tif")
            if not os.path.exists(gfd_evt_tif):
                skipped += 1
                continue

            total += 1
            out_tif = os.path.join(out_year_dir, f"{evt_dir}_GFD_b1_flood.tif")

            try:
                extract_one_event(gfd_evt_tif, out_tif)
                saved += 1
                if saved % 100 == 0:
                    print(f"[INFO] saved {saved} masks ...")
            except Exception as e:
                skipped += 1
                print("[INFO] Notebook progress message.")

    print("\n[DONE]")
    print(f"  matched events : {total}")
    print(f"  saved masks    : {saved}")
    print(f"  skipped/failed : {skipped}")
    print(f"  output root    : {OUT_ROOT}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import shutil
import numpy as np
import rasterio as rio


IN_ROOT  = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD/events/GFD"
OUT_DIR  = r"/home/ll/jupyter_notebook/gis_data/CAMA_GFD_GWP/GFD/events/GFD/10max"
TOPK     = 10

# External flood dataset comparison note.
NAME_SUFFIX = "_GFD_b1_flood.tif"   # Original notebook comment normalized for the public code archive.


def iter_tifs(root: str):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Original notebook comment normalized for the public code archive.
        if os.path.abspath(dirpath).startswith(os.path.abspath(OUT_DIR)):
            continue

        for fn in filenames:
            if not fn.lower().endswith(".tif"):
                continue
            if NAME_SUFFIX and (not fn.endswith(NAME_SUFFIX)):
                continue
            yield os.path.join(dirpath, fn)


def count_flood_pixels(tif_path: str, flood_value=1):
    """Archived notebook note for 01_event_level_pod_far_csi_validation.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rio.open(tif_path) as ds:
        nodata = ds.nodata
        cnt = 0

        # Original notebook comment normalized for the public code archive.
        band = 1

        for _, window in ds.block_windows(band):
            arr = ds.read(band, window=window)

            if nodata is None:
                cnt += int(np.count_nonzero(arr == flood_value))
            else:
                # Original notebook comment normalized for the public code archive.
                m = (arr != nodata)
                cnt += int(np.count_nonzero(m & (arr == flood_value)))

        return cnt


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    records = []
    files = list(iter_tifs(IN_ROOT))
    if len(files) == 0:
        print("[INFO] Notebook progress message.")
        return

    print("[INFO] Notebook progress message.")

    for i, fp in enumerate(files, 1):
        try:
            c = count_flood_pixels(fp, flood_value=1)
            records.append((c, fp))
        except Exception as e:
            print("[INFO] Notebook progress message.")

        if i % 200 == 0:
            print(f"[INFO] processed {i}/{len(files)}")

    # Original notebook comment normalized for the public code archive.
    records.sort(key=lambda x: x[0], reverse=True)
    top = records[:TOPK]

    if len(top) == 0 or top[0][0] == 0:
        print("[INFO] Notebook progress message.")
        return

    # Fixed-effects regression helper.
    manifest_path = os.path.join(OUT_DIR, "top10_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "flood_pixels", "src_path", "dst_path"])

        for rank, (pix, src) in enumerate(top, 1):
            base = os.path.basename(src)
            dst_name = f"{rank:02d}_pix{pix}_{base}"
            dst = os.path.join(OUT_DIR, dst_name)

            shutil.copy2(src, dst)
            w.writerow([rank, pix, src, dst])

            print(f"[TOP{rank:02d}] pixels={pix} | {base}")

    print("\n[DONE]")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
