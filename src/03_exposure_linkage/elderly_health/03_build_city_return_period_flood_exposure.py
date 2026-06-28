#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import warnings
import datetime as dt
import numpy as np
import geopandas as gpd
from rasterio import features
from rasterio.transform import from_origin

warnings.filterwarnings("ignore")

# =============================================================================
PRODUCTS = {
    "jra": {
        "label": "JRA",
        "root": r"/home/ll/cama_flood/CaMa/cmf_v420_pkg/out/JRA_RESOP_1980_2020_V3",
        "start_year": 1980,
        "end_year": 2020,
    },
    "vic": {
        "label": "VIC",
        "root": r"/home/ll/cama_flood/CaMa/cmf_v420_pkg/out/VIC_RESOP_1980_2015_V3",
        "start_year": 1980,
        "end_year": 2015,
    },
    "gldas": {
        "label": "GLDAS",
        "root": r"/home/ll/cama_flood/CaMa/cmf_v420_pkg/out/GLDAS_RESOP_1980_2020_V3",
        "start_year": 1980,
        "end_year": 2020,
    },
    "merra2": {
        "label": "MERRA2",
        "root": r"/home/ll/cama_flood/CaMa/cmf_v420_pkg/out/MERRA2_RESOP_1980_2020_V3",
        "start_year": 1980,
        "end_year": 2020,
    },
    "era5land": {
        "label": "ERA5-Land",
        "root": r"/home/ll/cama_flood/CaMa/cmf_v420_pkg/out/ERA5LAND_RESOP_1980_2020_V3",
        "start_year": 1980,
        "end_year": 2020,
    },
}

ACTIVE_PRODUCTS = ["vic", "merra2", "era5land", "jra", "gldas"]
START_DATE = dt.date(1980, 1, 1)
END_DATE = dt.date(2020, 12, 31)
SHP_PATH = r"/home/ll/jupyter_notebook/gis_data/China/china_2/china_2.shp"
OUT_BASE_BIN = r"/home/ll/jupyter_notebook/result/ensemble_storge_daily_bin_p50"
RES_MIN = 15  # arcmin
WEST, EAST = 68.0, 136.0  # Original notebook comment normalized for the public code archive.
SOUTH, NORTH = 15.0, 54.0  # Original notebook comment normalized for the public code archive.
CRS_EPSG = 4326
THR = None
MISSING_THRESHOLD = 1e19  # CaMa-Flood processing note.
SKIP_IF_EXISTS = False
WRITE_JSON = True
COMPACT_MODE = "float32"  # "float32" / "float16" / "u16_q01m"
U16_NAN_CODE = 65535
COMPRESS = None           # None / "zstd" / "gzip"
ZSTD_LEVEL = 12
ZSTD_THREADS = 4
GZIP_LEVEL = 6
BACKEND = "numpy"
MAX_WORKERS = 8

# =============================================================================
GLOBAL_WIN_MASK = None
GLOBAL_TRANSFORM_WIN = None
GLOBAL_YEAR_META = None  # {prod: {year: {"path": ..., "ndays": ...}}}


# =============================================================================

def build_grid(west, east, south, north, res_min):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ddeg = res_min / 60.0
    nx = int(round((east - west) / ddeg))
    ny = int(round((north - south) / ddeg))
    return nx, ny, ddeg


def build_mask_and_window(shp_path, west, north, ddeg, nx, ny, pad_pix=0):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        raise ValueError("Shapefile 缺少坐标系，请设置 EPSG:4326。")
    gdf = gdf.to_crs(CRS_EPSG)

    transform_full = from_origin(west, north, ddeg, ddeg)

    mask_up = features.rasterize(
        [(geom, 1) for geom in gdf.geometry],
        out_shape=(ny, nx),
        transform=transform_full,
        fill=0,
        default_value=1,
        dtype="uint8",
    ).astype(bool)

    rows = np.where(mask_up.any(axis=1))[0]
    cols = np.where(mask_up.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        raise ValueError("掩膜范围为空，请检查矢量与经纬度范围。")

    r0, r1 = max(rows[0] - pad_pix, 0), min(rows[-1] + 1 + pad_pix, ny)
    c0, c1 = max(cols[0] - pad_pix, 0), min(cols[-1] + 1 + pad_pix, nx)

    win_mask = mask_up[r0:r1, c0:c1]
    transform_win = from_origin(west + c0 * ddeg, north - r0 * ddeg, ddeg, ddeg)

    return gdf, (r0, r1, c0, c1), transform_win, win_mask


# =============================================================================

def compute_p50_with_kofn(stack, kmin):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    valid_cnt = np.isfinite(stack).sum(axis=0)  # (H, W)
    stack[:, valid_cnt < kmin] = np.nan
    p50 = np.nanmedian(stack, axis=0).astype(np.float32)
    return p50, valid_cnt


# =============================================================================

def scan_storge_years(selected_products, nx, ny):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    year_meta = {}
    nc = nx * ny

    print("[INFO] Notebook progress message.")
    for key in selected_products:
        if key not in PRODUCTS:
            print("[INFO] Notebook progress message.")
            continue

        info = PRODUCTS[key]
        label = info["label"]
        root = info["root"]
        y0   = max(info["start_year"], START_DATE.year)
        y1   = min(info["end_year"],   END_DATE.year)

        if not os.path.isdir(root):
            print("[INFO] Notebook progress message.")
            continue

        year_meta[key] = {}
        print(f"\n[PRODUCT] {key:8s} ({label}), root={root}")

        for year in range(y0, y1 + 1):
            fp = os.path.join(root, f"storge{year}.bin")
            if not os.path.isfile(fp):
                print("[INFO] Notebook progress message.")
                continue

            size_bytes = os.path.getsize(fp)
            if size_bytes % 4 != 0:
                print("[INFO] Notebook progress message.")
                continue

            n_float = size_bytes // 4
            if n_float % nc != 0:
                print(
                    f"  - year {year}: n_float={n_float} 不能被 nx*ny={nc} 整除，"
                    f"推断结构可能不是 [day, ny, nx]，请检查。"
                )
                continue

            ndays = n_float // nc
            year_meta[key][year] = {
                "path": fp,
                "ndays": int(ndays),
            }

            if   ndays == 365: mark = "(365d, no-leap 年?)"
            elif ndays == 366: mark = "(366d, leap 年?)"
            elif ndays == 360: mark = "(360d, 30day×12 月?)"
            else:              mark = ""

            print(
                f"  - year {year}: path={os.path.basename(fp)}, "
                f"ndays={ndays} {mark}"
            )

    print("[INFO] Notebook progress message.")
    return year_meta


# =============================================================================

def is_leap_year(year: int) -> bool:
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def per_date_product_slices(cur: dt.date, nx: int, ny: int):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    global GLOBAL_YEAR_META
    if not GLOBAL_YEAR_META:
        return []

    y = cur.year
    slices = []
    for prod, ymeta in GLOBAL_YEAR_META.items():
        meta = ymeta.get(y)
        if meta is None:
            continue  # Original notebook comment normalized for the public code archive.

        ndays = meta["ndays"]

        # Original notebook comment normalized for the public code archive.
        if ndays in (365, 366):
            doy = (cur - dt.date(y, 1, 1)).days + 1  # 1-based
            if doy < 1 or doy > ndays:
                continue
            day_index = doy - 1

        # Original notebook comment normalized for the public code archive.
        elif ndays == 360:
            m, d = cur.month, cur.day
            if d > 30:
                continue  # Original notebook comment normalized for the public code archive.
            doy360 = (m - 1) * 30 + d
            if doy360 < 1 or doy360 > 360:
                continue
            day_index = doy360 - 1

        # Original notebook comment normalized for the public code archive.
        else:
            total_greg = 366 if is_leap_year(y) else 365
            doy = (cur - dt.date(y, 1, 1)).days + 1
            if doy < 1 or doy > total_greg:
                continue
            frac = (doy - 1) / (total_greg - 1)  # 0~1
            day_index = int(round(frac * (ndays - 1)))
            day_index = max(0, min(day_index, ndays - 1))

        slices.append((prod, meta["path"], day_index))

    return slices


def read_storge_one_day(fp: str, nx: int, ny: int, day_index: int):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    nc = nx * ny
    offset = day_index * nc * 4  # float32=4 bytes
    arr = np.fromfile(fp, dtype="<f4", count=nc, offset=offset)
    if arr.size != nc:
        raise IOError(f"读取元素数不足：{fp}, day_index={day_index}, got={arr.size}, expect={nc}")
    return arr.reshape((ny, nx))


# =============================================================================

def _quantize_u16_q01m(x: np.ndarray, nan_code=65535):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = np.full(x.shape, nan_code, dtype=np.uint16)
    msk = np.isfinite(x)
    q = np.rint(x[msk] / 0.01).astype(np.int64)
    q = np.clip(q, 0, nan_code - 1)
    out[msk] = q.astype(np.uint16)
    return out


# =============================================================================

def write_p50_bin_compact(path_base, p50, transform, thr, used_products, kmin, n_prod):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    if COMPRESS == "zstd":
        out_path = path_base + ".zst"
    elif COMPRESS == "gzip":
        out_path = path_base + ".gz"
    else:
        out_path = path_base

    # Original notebook comment normalized for the public code archive.
    if COMPACT_MODE == "float32":
        payload = p50.astype(np.dtype("<f4"), copy=False).tobytes(order="C")
        band_meta = {"name": "p50", "dtype": "float32-le"}
    elif COMPACT_MODE == "float16":
        payload = p50.astype(np.dtype("<f2"), copy=False).tobytes(order="C")
        band_meta = {"name": "p50", "dtype": "float16-le"}
    elif COMPACT_MODE == "u16_q01m":
        payload = _quantize_u16_q01m(p50, U16_NAN_CODE).tobytes(order="C")
        band_meta = {
            "name": "p50",
            "dtype": "uint16",
            "scale": 0.01,
            "offset": 0.0,
            "nan": U16_NAN_CODE,
        }
    else:
        raise ValueError("COMPACT_MODE 必须是 'float32'、'float16' 或 'u16_q01m'")

    # Original notebook comment normalized for the public code archive.
    if COMPRESS == "zstd":
        import zstandard as zstd
        cctx = zstd.ZstdCompressor(level=ZSTD_LEVEL, threads=ZSTD_THREADS)
        with open(out_path, "wb") as fout, cctx.stream_writer(fout) as zw:
            zw.write(payload)
    elif COMPRESS == "gzip":
        import gzip
        with gzip.open(out_path, "wb", compresslevel=GZIP_LEVEL) as gz:
            gz.write(payload)
    else:
        with open(out_path, "wb") as f:
            f.write(payload)

    # Original notebook comment normalized for the public code archive.
    if WRITE_JSON:
        meta = {
            "layout": "band-first",
            "rows": int(p50.shape[0]),
            "cols": int(p50.shape[1]),
            "transform": [
                float(transform.c),
                float(transform.f),
                float(transform.a),
                float(transform.e),
            ],
            "crs": f"EPSG:{CRS_EPSG}",
            "thr": thr,
            "compact_mode": COMPACT_MODE,
            "compress": COMPRESS,
            "zstd_level": ZSTD_LEVEL if COMPRESS == "zstd" else None,
            "zstd_threads": ZSTD_THREADS if COMPRESS == "zstd" else None,
            "gzip_level": GZIP_LEVEL if COMPRESS == "gzip" else None,
            "bands": [band_meta],
            "products_used": used_products,
            "kmin_rule": "ceil(n_prod/2)",
            "kmin_value": int(kmin),
            "n_products_day": int(n_prod)
        }
        with open(out_path + ".json", "w", encoding="utf-8") as jf:
            json.dump(meta, jf, ensure_ascii=False, indent=2)

    return out_path


# =============================================================================

def process_one_day(cur, nx, ny, r0, r1, c0, c1, kmin):
    global GLOBAL_WIN_MASK, GLOBAL_TRANSFORM_WIN
    win_mask = GLOBAL_WIN_MASK
    transform_win = GLOBAL_TRANSFORM_WIN

    out_dir = os.path.join(OUT_BASE_BIN, f"{cur.year}")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"ensemble_storge_{cur:%Y%m%d}_p50.bin")

    # Original notebook comment normalized for the public code archive.
    probes = [base, base + ".zst", base + ".gz"]
    if SKIP_IF_EXISTS and any(os.path.isfile(p) for p in probes):
        return ("skip", str(cur))

    slices = per_date_product_slices(cur, nx, ny)
    if not slices:
        return ("empty", str(cur))

    sub_arrays, used_names = [], []
    for name, fp, day_index in slices:
        try:
            arr = read_storge_one_day(fp, nx, ny, day_index).astype("float32")
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        # CaMa-Flood processing note.
        arr[arr >= MISSING_THRESHOLD] = np.nan

        # Original notebook comment normalized for the public code archive.
        if THR is not None:
            arr[arr <= THR] = np.nan

        sub = arr[r0:r1, c0:c1]
        sub[~win_mask] = np.nan

        sub_arrays.append(sub)
        used_names.append(name)

    if not sub_arrays:
        return ("empty", str(cur))

    stack = np.stack(sub_arrays, axis=0)  # (n_prod, H, W)
    n_prod = stack.shape[0]

    # Original notebook comment normalized for the public code archive.
    p50, valid_cnt = compute_p50_with_kofn(stack, kmin)

    # Original notebook comment normalized for the public code archive.
    write_p50_bin_compact(base, p50, transform_win, THR, used_names, kmin, n_prod)
    return ("done", str(cur), len(used_names))


def main():
    global GLOBAL_WIN_MASK, GLOBAL_TRANSFORM_WIN, GLOBAL_YEAR_META

    os.makedirs(OUT_BASE_BIN, exist_ok=True)

    # Original notebook comment normalized for the public code archive.
    nx, ny, ddeg = build_grid(WEST, EAST, SOUTH, NORTH, RES_MIN)
    print("[INFO] Notebook progress message.")

    gdf, (r0, r1, c0, c1), transform_win, win_mask = build_mask_and_window(
        SHP_PATH, WEST, NORTH, ddeg, nx, ny, pad_pix=0
    )
    H, W = (r1 - r0), (c1 - c0)
    print(f"[INFO] China window size: {H} x {W} (rows x cols)")

    GLOBAL_WIN_MASK = win_mask
    GLOBAL_TRANSFORM_WIN = transform_win

    # Original notebook comment normalized for the public code archive.
    selected_products = []
    for key in ACTIVE_PRODUCTS:
        if key in PRODUCTS:
            selected_products.append(key)
        else:
            print("[INFO] Notebook progress message.")

    selected_products = sorted(set(selected_products))
    print("[INFO] Notebook progress message.")
    for k in selected_products:
        info = PRODUCTS[k]
        print(
            f"  - {k:8s}: {info['label']}, "
            f"years {info['start_year']}-{info['end_year']}, root={info['root']}"
        )

    # Original notebook comment normalized for the public code archive.
    year_meta = scan_storge_years(selected_products, nx, ny)
    GLOBAL_YEAR_META = year_meta

    # Original notebook comment normalized for the public code archive.
    days, d, one = [], START_DATE, dt.timedelta(days=1)
    while d <= END_DATE:
        days.append(d)
        d += one

    # Original notebook comment normalized for the public code archive.
    from collections import defaultdict
    year_days = defaultdict(list)
    for d in days:
        year_days[d.year].append(d)

    # Original notebook comment normalized for the public code archive.
    kmin = 3  # Original notebook comment normalized for the public code archive.
    n_done_all = n_skip_all = n_empty_all = 0
    for year, day_list in year_days.items():
        for cur in day_list:
            status = process_one_day(cur, nx, ny, r0, r1, c0, c1, kmin)
            if status:
                tag = status[0]
                if tag == "done":
                    n_done_all += 1
                elif tag == "skip":
                    n_skip_all += 1
                else:
                    n_empty_all += 1

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_build_city_return_period_flood_exposure.

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

# Original notebook comment normalized for the public code archive.
STOR_P50_ROOT = "/home/ll/jupyter_notebook/result/ensemble_storge_daily_bin_p50"

# Original notebook comment normalized for the public code archive.
CITY_SHP = "/home/ll/jupyter_notebook/gis_data/China/city/city.shp"

# City-level processing note.
# City-level processing note.
CITY_ID_FIELD = "市代码"     
CITY_NAME_FIELD = "市"    

OUT_DIR = "/home/ll/jupyter_notebook/result/impact_assessment/older"
os.makedirs(OUT_DIR, exist_ok=True)

BASE_START_YEAR = 1980
BASE_END_YEAR   = 2020

ANALYSIS_START_YEAR = 1980
ANALYSIS_END_YEAR   = 2020

RETURN_PERIODS = [2, 5, 10, 20, 50, 100]
MIN_YEARS_FOR_FIT = 15

# =============================================================================
DRY_FRAC_MIN   = 0.30   # Original notebook comment normalized for the public code archive.
DRY_COUNTY_MIN = 0.05   # Original notebook comment normalized for the public code archive.


# =============================================================================

def find_sample_json(p50_root):
    pattern = os.path.join(p50_root, "**", "*.bin.json")
    cands = glob(pattern, recursive=True)
    if not cands:
        raise RuntimeError(f"在 {p50_root} 下未找到任何 .bin.json 文件。")
    cands = sorted(cands)
    print("[INFO] Notebook progress message.")
    return cands[0]


def prepare_storge_meta(sample_json):
    import json
    with open(sample_json, "r", encoding="utf-8") as jf:
        meta = json.load(jf)

    rows, cols = int(meta["rows"]), int(meta["cols"])
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
        raise ValueError(f"未知 compact_mode: {compact}")

    x0, y0, dx, dy = meta["transform"]
    transform = Affine(dx, 0, x0, 0, dy, y0)
    crs = meta.get("crs", "EPSG:4326")
    return rows, cols, dtype, scale, nan_code, transform, crs


def pixel_area_raster(transform, shape):
    ny, nx = shape
    geod = Geod(ellps="WGS84")

    xs = transform.c + (np.arange(nx) + 0.5) * transform.a
    ys = transform.f + (np.arange(ny) + 0.5) * transform.e

    x_left  = xs[0]  - 0.5 * transform.a
    x_right = xs[-1] + 0.5 * transform.a

    area = np.zeros((ny, nx), dtype=np.float64)
    for j in range(ny):
        dlon_row = geod.line_length([x_left, x_right], [ys[j], ys[j]]) / nx
        y_top = ys[j] - 0.5 * transform.e
        y_bot = ys[j] + 0.5 * transform.e
        dlat = geod.line_length([xs[0], xs[0]], [y_top, y_bot])
        area[j, :] = dlon_row * dlat
    return area


def rasterize_cities(transform, shape, city_shp, id_field, name_field):
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ny, nx = shape
    gdf = gpd.read_file(city_shp)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    gdf = gdf.to_crs(4326)

    # Original notebook comment normalized for the public code archive.
    candidates = [id_field] if id_field else []
    candidates += [
        "city_code", "CITY_CODE", "citycode", "CITYCODE",
        "adcode", "ADCODE", "GB", "CODE", "code",
        "id", "ID"
    ]
    candidates = [c for c in candidates if c is not None]

    id_col = next((c for c in candidates if c in gdf.columns), None)
    if id_col is None:
        raise ValueError(
            f"市界文件中找不到合适的 ID 字段。请检查 city.shp 列名并设置 CITY_ID_FIELD。"
        )

    ids_raw = gdf[id_col]
    if ids_raw.isna().any():
        raise ValueError(f"市 ID 字段 {id_col} 存在缺失值。")

    ids_as_key = ids_raw.astype(str)
    codes, uniques = pd.factorize(ids_as_key, sort=False)
    cid_per_row = (codes + 1).astype(np.int32)  # internal id from 1

    # Original notebook comment normalized for the public code archive.
    if name_field and name_field in gdf.columns:
        name_map = gdf[[id_col, name_field]].drop_duplicates(subset=[id_col]).copy()
        name_map[id_col] = name_map[id_col].astype(str)
        name_map.columns = ["city_code", "city_name"]
    else:
        name_map = pd.DataFrame(columns=["city_code", "city_name"])

    map_df = pd.DataFrame({
        "city_id": np.arange(1, len(uniques) + 1, dtype=np.int32),
        "city_code": uniques
    })
    if not name_map.empty:
        map_df = map_df.merge(name_map, on="city_code", how="left")

    shapes_iter = ((geom, int(cid)) for geom, cid in zip(gdf.geometry, cid_per_row))
    city_id_full = features.rasterize(
        shapes=shapes_iter,
        out_shape=(ny, nx),
        transform=transform,
        fill=0,
        dtype="int32"
    )
    return city_id_full, map_df


def compute_city_area(city_id_full, pix_area_full, map_df):
    mask = city_id_full > 0
    cids = city_id_full[mask].astype(np.int32)
    weights = pix_area_full[mask]
    max_cid = int(city_id_full.max())

    bc = np.bincount(cids, weights=weights, minlength=max_cid + 1)
    area_m2 = {int(i): float(w) for i, w in enumerate(bc) if i != 0}

    df_area = map_df.copy()
    df_area["area_m2"]  = df_area["city_id"].map(area_m2).fillna(0.0)
    df_area["area_km2"] = df_area["area_m2"] / 1e6
    return df_area


def list_storge_bin_files(p50_root, start_year=None, end_year=None):
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
    n = rows * cols
    with open(bin_path, "rb") as f:
        buf = f.read()
    arr = np.frombuffer(buf, dtype=dtype, count=n)
    if arr.size != n:
        raise RuntimeError(f"{bin_path} 数据长度不匹配。期望 {n}，实际 {arr.size}")
    arr = arr.reshape((rows, cols)).astype(np.float32)

    if nan_code is not None:
        arr[arr == nan_code] = np.nan
    arr = arr * scale

    # Original notebook comment normalized for the public code archive.
    arr = np.where(np.isfinite(arr) & (arr > 0), arr, np.nan)
    return arr


def compute_annual_max_storage(bin_list, rows, cols, dtype, scale, nan_code):
    if not bin_list:
        raise RuntimeError("bin_list 为空。")

    years = sorted({date.year for _, date in bin_list})
    year_to_idx = {y: i for i, y in enumerate(years)}
    Ny = len(years)

    S_annual_max = np.full((Ny, rows, cols), np.nan, dtype=np.float32)

    print("[INFO] Notebook progress message.")
    bin_list_sorted = sorted(bin_list, key=lambda x: x[1])

    prev_year = None
    for bin_path, date in bin_list_sorted:
        y = date.year
        idx = year_to_idx[y]
        if prev_year is None or y != prev_year:
            print("[INFO] Notebook progress message.")
            prev_year = y

        arr = load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code)

        current_max = S_annual_max[idx]
        mask_curr_nan = ~np.isfinite(current_max)
        mask_arr_nan  = ~np.isfinite(arr)

        replace_mask = mask_curr_nan & (~mask_arr_nan)
        current_max[replace_mask] = arr[replace_mask]

        both_valid = (~mask_curr_nan) & (~mask_arr_nan)
        current_max[both_valid] = np.maximum(current_max[both_valid], arr[both_valid])

        S_annual_max[idx] = current_max

    return np.array(years, dtype=int), S_annual_max


# =============================================================================

def compute_city_annual_series(S_annual_max, city_id_full, pix_area_full):
    Ny, rows, cols = S_annual_max.shape
    max_cid = int(city_id_full.max())
    city_series = np.full((Ny, max_cid + 1), np.nan, dtype=np.float32)

    valid_city_mask = city_id_full > 0

    for t in range(Ny):
        S_year = S_annual_max[t]
        mask = valid_city_mask & np.isfinite(S_year)
        if not mask.any():
            continue

        cids = city_id_full[mask].astype(np.int32)
        areas = pix_area_full[mask].astype(np.float64)
        vals  = S_year[mask].astype(np.float64)

        num = np.bincount(cids, weights=areas * vals, minlength=max_cid + 1)
        den = np.bincount(cids, weights=areas, minlength=max_cid + 1)

        with np.errstate(divide="ignore", invalid="ignore"):
            mean_vals = num / den
        mean_vals[den == 0] = np.nan

        city_series[t, :] = mean_vals.astype(np.float32)

    return city_series


def compute_city_return_thresholds_gumbel(city_series, years_all,
                                          base_start, base_end, return_periods):
    years_all = np.asarray(years_all, dtype=int)
    mask_base = (years_all >= base_start) & (years_all <= base_end)
    if not mask_base.any():
        raise RuntimeError("基准期内没有年份，请检查 BASE_START_YEAR/BASE_END_YEAR。")

    S_base = city_series[mask_base]
    Nbase, nC = S_base.shape
    print("[INFO] Notebook progress message.")

    thr_city = {T: np.full((nC,), np.nan, dtype=np.float32) for T in return_periods}

    for cid in range(1, nC):
        series = S_base[:, cid]
        series = series[np.isfinite(series)]
        if series.size < MIN_YEARS_FOR_FIT:
            continue
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
                thr_city[T][cid] = float(q)

    return thr_city


def compute_city_year_events_ruleC1(years_all,
                                    city_series,
                                    thr_city,
                                    map_df,
                                    analysis_start,
                                    analysis_end,
                                    return_periods):
    years_all = np.asarray(years_all, dtype=int)
    year_to_idx = {int(y): i for i, y in enumerate(years_all)}

    analysis_years = [int(y) for y in years_all
                      if analysis_start <= y <= analysis_end and int(y) in year_to_idx]
    analysis_years = sorted(set(analysis_years))
    print("[INFO] Notebook progress message.")

    all_year_dfs = []

    for y in analysis_years:
        idx = year_to_idx[y]
        Sbar_year = city_series[idx]

        df_year = map_df.copy()
        df_year.insert(0, "year", y)

        cids = df_year["city_id"].values.astype(int)

        for T in return_periods:
            thr_vec = thr_city[T]
            flags = np.zeros_like(cids, dtype=np.int8)

            ok_thr = np.isfinite(thr_vec[cids])
            ok_val = np.isfinite(Sbar_year[cids])
            trig = ok_thr & ok_val & (Sbar_year[cids] >= thr_vec[cids])
            flags[trig] = 1

            df_year[f"flood_ge_T{T}"] = flags

        all_year_dfs.append(df_year)

    return pd.concat(all_year_dfs, ignore_index=True)


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    sample_json = find_sample_json(STOR_P50_ROOT)
    rows, cols, dtp, scl, nan_code, transform, crs = prepare_storge_meta(sample_json)
    ny, nx = rows, cols
    print(f"[INFO] storge P50 grid: {nx} x {ny}, crs={crs}")

    print("[INFO] Notebook progress message.")
    pix_area_full = pixel_area_raster(transform, (ny, nx))

    print("[INFO] Notebook progress message.")
    city_id_full, map_df = rasterize_cities(
        transform, (ny, nx), CITY_SHP, CITY_ID_FIELD, CITY_NAME_FIELD
    )
    df_area = compute_city_area(city_id_full, pix_area_full, map_df)
    area_csv = os.path.join(OUT_DIR, "city_total_area_storage.csv")
    df_area.to_csv(area_csv, index=False)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    bin_list = list_storge_bin_files(STOR_P50_ROOT, BASE_START_YEAR, BASE_END_YEAR)
    if not bin_list:
        raise RuntimeError("未找到任何 storge P50 bin 文件，请检查 STOR_P50_ROOT 与年份设置。")

    print("[INFO] Notebook progress message.")
    years_all, S_annual_max = compute_annual_max_storage(
        bin_list, rows, cols, dtp, scl, nan_code
    )

    # =========================================================
    # Original notebook comment normalized for the public code archive.
    # =========================================================
    Ny_base = S_annual_max.shape[0]  # Original notebook comment normalized for the public code archive.
    valid_frac = np.isfinite(S_annual_max).sum(axis=0) / float(Ny_base)  # (rows, cols)
    dry_mask = valid_frac < DRY_FRAC_MIN

    n_dry_pix = int(dry_mask.sum())
    n_all_pix = int(rows * cols)
    print(f"[D1] dry pixels: {n_dry_pix}/{n_all_pix} "
          f"({n_dry_pix/n_all_pix:.3f}), DRY_FRAC_MIN={DRY_FRAC_MIN}")

    # Original notebook comment normalized for the public code archive.
    S_annual_max[:, dry_mask] = np.nan

    # Original notebook comment normalized for the public code archive.
    np.save(os.path.join(OUT_DIR, "dry_mask_pixels_D1.npy"), dry_mask.astype(np.uint8))
    pd.DataFrame({
        "DRY_FRAC_MIN": [DRY_FRAC_MIN],
        "n_dry_pixels": [n_dry_pix],
        "n_all_pixels": [n_all_pix],
        "dry_pixel_share": [n_dry_pix/n_all_pix]
    }).to_csv(os.path.join(OUT_DIR, "dry_mask_pixels_D1_report.csv"), index=False)

    # =========================================================
    # Original notebook comment normalized for the public code archive.
    # =========================================================
    print("[INFO] Notebook progress message.")
    city_series = compute_city_annual_series(
        S_annual_max, city_id_full, pix_area_full
    )  # (Ny, n_cities+1)

    # =========================================================
    # Original notebook comment normalized for the public code archive.
    # =========================================================
    max_cid = int(city_id_full.max())

    # Original notebook comment normalized for the public code archive.
    valid_pixel_any = np.isfinite(S_annual_max).any(axis=0) & (city_id_full > 0)

    cids_valid = city_id_full[valid_pixel_any].astype(np.int32)
    areas_valid = pix_area_full[valid_pixel_any].astype(np.float64)

    cids_total = city_id_full[city_id_full > 0].astype(np.int32)
    areas_total = pix_area_full[city_id_full > 0].astype(np.float64)

    valid_area = np.bincount(cids_valid, weights=areas_valid, minlength=max_cid + 1)
    total_area = np.bincount(cids_total, weights=areas_total, minlength=max_cid + 1)

    with np.errstate(divide="ignore", invalid="ignore"):
        g_frac = valid_area / total_area
    g_frac[total_area == 0] = np.nan

    dry_cities = np.where(g_frac < DRY_COUNTY_MIN)[0]
    dry_cities = dry_cities[dry_cities > 0]  # remove cid=0

    print(f"[D2] dry cities: {len(dry_cities)}/{max_cid} "
          f"({len(dry_cities)/max_cid:.3f}), DRY_COUNTY_MIN={DRY_COUNTY_MIN}")

    # Original notebook comment normalized for the public code archive.
    if len(dry_cities) > 0:
        city_series[:, dry_cities] = np.nan

    # Original notebook comment normalized for the public code archive.
    df_d2 = map_df.copy()
    df_d2["valid_area_frac"] = df_d2["city_id"].map(
        {int(i): float(g_frac[i]) for i in range(len(g_frac))}
    )
    df_d2["is_dry_city_D2"] = df_d2["city_id"].isin(dry_cities).astype(int)
    df_d2.to_csv(os.path.join(OUT_DIR, "dry_cities_D2_report.csv"), index=False)

    # =========================================================
    # Original notebook comment normalized for the public code archive.
    # =========================================================
    print("[INFO] Notebook progress message.")
    thr_city = compute_city_return_thresholds_gumbel(
        city_series, years_all, BASE_START_YEAR, BASE_END_YEAR, RETURN_PERIODS
    )

    thr_path = os.path.join(OUT_DIR, "storge_return_thresholds_city_gumbel.npz")
    np.savez_compressed(
        thr_path,
        years=years_all,
        city_id=map_df["city_id"].values,
        city_code=map_df["city_code"].values,
        **{f"thr_T{T}": thr_city[T] for T in RETURN_PERIODS}
    )
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df_events = compute_city_year_events_ruleC1(
        years_all,
        city_series,
        thr_city,
        map_df,
        ANALYSIS_START_YEAR,
        ANALYSIS_END_YEAR,
        RETURN_PERIODS
    )

    out_csv = os.path.join(
        OUT_DIR,
        f"city_flood_events_T2_5_10_20_50_100_{ANALYSIS_START_YEAR}_{ANALYSIS_END_YEAR}.csv"
    )
    df_events.to_csv(out_csv, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path

flood_5y_path = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/city_flood_Tall_5y_1980_2020.parquet")
df5 = pd.read_parquet(flood_5y_path)

# CHARLS processing note.
df5 = df5[df5["year"].isin([2011, 2013, 2015, 2018, 2020])]

for T in [2, 5, 10, 20, 50, 100]:
    col = f"share_flood_T{T}_5y"
    print(f"\n== T={T} ==")
    print(df5[col].describe())
    print("[INFO] Notebook progress message.", (df5[col] == 0).mean())


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
for T in [2, 5, 10, 20, 50, 100]:
    col = f"share_flood_T{T}_5y"
    tmp = df5.groupby("city_code")[col].agg(["min", "max", "std"])
    print("[INFO] Notebook progress message.")
    print(tmp["std"].describe())


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd

# =============================================================================
ROOT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")

FLOOD_EVENTS = ROOT_DIR / "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"

OUT_DIR = ROOT_DIR / "flood_health_result"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_5Y = OUT_DIR / "city_flood_T10_5y_1980_2020.parquet"

CITY_COL = "city_code"   # City-level processing note.
MAIN_T = 2              # Original notebook comment normalized for the public code archive.

CHARLS_YEARS = [2011, 2013, 2015, 2018, 2020]


def build_5y_exposure():
    print(f"[READ] Flood events: {FLOOD_EVENTS}")
    df = pd.read_csv(FLOOD_EVENTS)

    # Original notebook comment normalized for the public code archive.
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[CITY_COL] = pd.to_numeric(df[CITY_COL], errors="coerce")
    df = df.dropna(subset=["year", CITY_COL])

    col_T = f"flood_ge_T{MAIN_T}"
    if col_T not in df.columns:
        raise ValueError(f"列 {col_T} 不存在，请检查洪水事件文件。")

    # City-level processing note.
    df = df.sort_values([CITY_COL, "year"])

    print(
        f"[INFO] 年份范围: {int(df['year'].min())}–{int(df['year'].max())}, "
        f"城市数: {df[CITY_COL].nunique()}"
    )

    def _add_roll(g):
        g = g.sort_values("year").copy()
        # Original notebook comment normalized for the public code archive.
        g[f"num_flood_T{MAIN_T}_5y"] = (
            g[col_T].rolling(window=5, min_periods=1).sum()
        )
        # Original notebook comment normalized for the public code archive.
        g[f"share_flood_T{MAIN_T}_5y"] = g[f"num_flood_T{MAIN_T}_5y"] / 5.0
        # Original notebook comment normalized for the public code archive.
        g[f"any_flood_T{MAIN_T}_5y"] = (g[f"num_flood_T{MAIN_T}_5y"] > 0).astype(int)
        return g

    df5 = df.groupby(CITY_COL, group_keys=False).apply(_add_roll)

    # CHARLS processing note.
    df5 = df5[df5["year"].isin(CHARLS_YEARS)].copy()

    print(
        f"[INFO] 5年窗口暴露表形状: {df5.shape}, "
        f"年份分布: {df5['year'].value_counts().sort_index().to_dict()}"
    )

    df5.to_parquet(OUT_5Y, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    build_5y_exposure()


# ------------------------------------------------------------------------------
# Notebook cell 24
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd

# =============================================================================
ROOT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")

FLOOD_EVENTS = ROOT_DIR / "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"

OUT_DIR = ROOT_DIR / "flood_health_result"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_5Y = OUT_DIR / "city_flood_Tall_5y_1980_2020.parquet"

CITY_COL = "city_code"               # City-level processing note.
T_LIST = [2, 5, 10, 20, 50, 100]     # Original notebook comment normalized for the public code archive.

# CHARLS processing note.
CHARLS_YEARS = [2011, 2013, 2015, 2018, 2020]


def build_5y_exposure_allT():
    print(f"[READ] Flood events: {FLOOD_EVENTS}")
    df = pd.read_csv(FLOOD_EVENTS)

    # Original notebook comment normalized for the public code archive.
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[CITY_COL] = pd.to_numeric(df[CITY_COL], errors="coerce")
    df = df.dropna(subset=["year", CITY_COL])

    df = df.sort_values([CITY_COL, "year"])

    print(
        f"[INFO] 年份范围: {int(df['year'].min())}–{int(df['year'].max())}, "
        f"城市数: {df[CITY_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    for T in T_LIST:
        col = f"flood_ge_T{T}"
        if col not in df.columns:
            raise ValueError(f"列 {col} 不存在，请检查洪水事件文件。")

    def _add_roll(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("year").copy()
        for T in T_LIST:
            col_T = f"flood_ge_T{T}"
            num_col = f"num_flood_T{T}_5y"
            share_col = f"share_flood_T{T}_5y"
            any_col = f"any_flood_T{T}_5y"

            # Original notebook comment normalized for the public code archive.
            g[num_col] = g[col_T].rolling(window=5, min_periods=1).sum()

            # Original notebook comment normalized for the public code archive.
            g[share_col] = g[num_col] / 5.0

            # Original notebook comment normalized for the public code archive.
            g[any_col] = (g[num_col] > 0).astype(int)

        return g

    # City-level processing note.
    df5 = df.groupby(CITY_COL, group_keys=False).apply(_add_roll)

    # CHARLS processing note.
    df5 = df5[df5["year"].isin(CHARLS_YEARS)].copy()

    print(
        f"[INFO] 5年窗口暴露表形状: {df5.shape}, "
        f"年份分布: {df5['year'].value_counts().sort_index().to_dict()}"
    )

    df5.to_parquet(OUT_5Y, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    build_5y_exposure_allT()


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd

# =============================================================================
ROOT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")

FLOOD_EVENTS = ROOT_DIR / "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"

OUT_DIR = ROOT_DIR / "flood_health_result"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CITY_COL = "city_code"               # City-level processing note.
T_LIST = [2, 5, 10, 20, 50, 100]     # Original notebook comment normalized for the public code archive.

# CHARLS processing note.
CHARLS_YEARS = [2011, 2013, 2015, 2018, 2020]

# Original notebook comment normalized for the public code archive.
WINDOW_LIST = [5, 10, 20, 30]


def _prepare_base_df() -> pd.DataFrame:
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] Flood events: {FLOOD_EVENTS}")
    df = pd.read_csv(FLOOD_EVENTS)

    # Original notebook comment normalized for the public code archive.
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[CITY_COL] = pd.to_numeric(df[CITY_COL], errors="coerce")
    df = df.dropna(subset=["year", CITY_COL])

    df = df.sort_values([CITY_COL, "year"])

    print(
        f"[INFO] 年份范围: {int(df['year'].min())}–{int(df['year'].max())}, "
        f"城市数: {df[CITY_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    for T in T_LIST:
        col = f"flood_ge_T{T}"
        if col not in df.columns:
            raise ValueError(f"列 {col} 不存在，请检查洪水事件文件。")

    return df


def build_Ny_exposure_allT(df_base: pd.DataFrame, window: int) -> None:
    """Archived notebook note for 03_build_city_return_period_flood_exposure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")

    def _add_roll(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("year").copy()
        for T in T_LIST:
            col_T = f"flood_ge_T{T}"

            num_col = f"num_flood_T{T}_{window}y"
            share_col = f"share_flood_T{T}_{window}y"
            any_col = f"any_flood_T{T}_{window}y"

            # Original notebook comment normalized for the public code archive.
            g[num_col] = g[col_T].rolling(window=window, min_periods=1).sum()

            # Original notebook comment normalized for the public code archive.
            g[share_col] = g[num_col] / float(window)

            # Original notebook comment normalized for the public code archive.
            g[any_col] = (g[num_col] > 0).astype(int)

        return g

    dfN = df_base.groupby(CITY_COL, group_keys=False).apply(_add_roll)

    # CHARLS processing note.
    dfN = dfN[dfN["year"].isin(CHARLS_YEARS)].copy()

    print(
        f"[INFO] {window} 年窗口暴露表形状: {dfN.shape}, "
        f"年份分布: {dfN['year'].value_counts().sort_index().to_dict()}"
    )

    out_path = OUT_DIR / f"city_flood_Tall_{window}y_1980_2020.parquet"
    dfN.to_parquet(out_path, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    base_df = _prepare_base_df()
    for w in WINDOW_LIST:
        build_Ny_exposure_allT(base_df, window=w)
