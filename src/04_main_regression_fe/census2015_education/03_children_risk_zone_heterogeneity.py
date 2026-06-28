#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import os
import re
import json
import gzip
import math
import warnings
import datetime as dt

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.crs import CRS

warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. CONFIG
# =========================================================

ENSEMBLE_BASE = Path("/home/ll/jupyter_notebook/result/ensemble_daily_bin_p50")

YEAR_START = 1980
YEAR_END   = 2020

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path("/home/ll/jupyter_notebook/result/fixed_rp_maps")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INTER_DIR = OUT_DIR / "intermediate"
INTER_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
RETURN_PERIODS = [20, 50, 100]

# Original notebook comment normalized for the public code archive.
MIN_VALID_YEARS = 20

# Original notebook comment normalized for the public code archive.
CLIP_NEGATIVE_TO_ZERO = True

# Original notebook comment normalized for the public code archive.
NODATA = -9999.0

# Original notebook comment normalized for the public code archive.
MMAP_PATH = INTER_DIR / f"annual_max_depth_{YEAR_START}_{YEAR_END}.f32.mmap"
YEARS_NPY = INTER_DIR / "annual_max_years.npy"
VALID_YEARS_TIF = INTER_DIR / "annual_max_valid_years.tif"

# Original notebook comment normalized for the public code archive.
OUT_TIF_MAP = {
    20: OUT_DIR / "rp20_inundation_depth_p50.tif",
    50: OUT_DIR / "rp50_inundation_depth_p50.tif",
    100: OUT_DIR / "rp100_inundation_depth_p50.tif",
}

# Original notebook comment normalized for the public code archive.
SKIP_IF_ANNUAL_MAX_EXISTS = False

# Gumbel return-period processing.
ROW_BLOCK = 256


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

DATE_PATTERN = re.compile(r"^ensemble_(\d{8})_p50\.bin(?:\.zst|\.gz)?$")


def find_any_meta_json(base_dir: Path) -> Path:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for year_dir in sorted(base_dir.iterdir()):
        if not year_dir.is_dir():
            continue
        for f in sorted(year_dir.iterdir()):
            if f.name.startswith("ensemble_") and f.name.endswith(".json"):
                return f
    raise FileNotFoundError(f"在 {base_dir} 下未找到任何 ensemble_*.json 元数据文件。")


def load_meta(meta_path: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    rows = int(meta["rows"])
    cols = int(meta["cols"])

    # Original notebook comment normalized for the public code archive.
    c, f0, a, e = meta["transform"]
    transform = Affine(a, 0.0, c, 0.0, e, f0)

    crs = CRS.from_string(meta.get("crs", "EPSG:4326"))
    compact_mode = meta.get("compact_mode", "float16")
    band_meta = meta["bands"][0]

    scale = band_meta.get("scale", 1.0)
    offset = band_meta.get("offset", 0.0)
    nan_code = band_meta.get("nan", None)

    return {
        "rows": rows,
        "cols": cols,
        "transform": transform,
        "crs": crs,
        "compact_mode": compact_mode,
        "scale": scale,
        "offset": offset,
        "nan_code": nan_code,
    }


def list_daily_files_for_year(year_dir: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    files = []
    for f in sorted(year_dir.iterdir()):
        if not f.is_file():
            continue
        m = DATE_PATTERN.match(f.name)
        if m:
            files.append(f)
    return files


def parse_date_from_filename(fp: Path):
    m = DATE_PATTERN.match(fp.name)
    if m is None:
        return None
    return dt.datetime.strptime(m.group(1), "%Y%m%d").date()


def read_daily_grid(bin_path: Path, meta: dict) -> np.ndarray:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    compact_mode = meta["compact_mode"]
    rows = meta["rows"]
    cols = meta["cols"]
    scale = meta["scale"]
    offset = meta["offset"]
    nan_code = meta["nan_code"]

    # Original notebook comment normalized for the public code archive.
    if bin_path.suffix == ".zst":
        import zstandard as zstd
        with open(bin_path, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            raw = dctx.decompress(f.read())
    elif bin_path.suffix == ".gz":
        with gzip.open(bin_path, "rb") as f:
            raw = f.read()
    else:
        with open(bin_path, "rb") as f:
            raw = f.read()

    # Original notebook comment normalized for the public code archive.
    if compact_mode == "float16":
        arr = np.frombuffer(raw, dtype=np.dtype("<f2")).reshape(rows, cols).astype("float32")
    elif compact_mode == "u16_q01m":
        q = np.frombuffer(raw, dtype=np.dtype("<u2")).reshape(rows, cols)
        arr = q.astype("float32")
        if nan_code is not None:
            arr[q == nan_code] = np.nan
        arr = arr * scale + offset
    else:
        raise ValueError(f"未知 compact_mode: {compact_mode}")

    return arr


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def build_annual_max_stack(meta: dict):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    years = list(range(YEAR_START, YEAR_END + 1))
    n_years = len(years)
    rows, cols = meta["rows"], meta["cols"]

    if MMAP_PATH.exists() and YEARS_NPY.exists() and SKIP_IF_ANNUAL_MAX_EXISTS:
        print("[INFO] Notebook progress message.")
        return years

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"[INFO] shape = ({n_years}, {rows}, {cols})")

    # Original notebook comment normalized for the public code archive.
    mm = np.memmap(
        MMAP_PATH,
        mode="w+",
        dtype="float32",
        shape=(n_years, rows, cols),
    )

    for yi, year in enumerate(years):
        year_dir = ENSEMBLE_BASE / f"{year}"
        if not year_dir.exists():
            print("[INFO] Notebook progress message.")
            mm[yi, :, :] = np.nan
            continue

        daily_files = list_daily_files_for_year(year_dir)
        print("[INFO] Notebook progress message.")

        # Original notebook comment normalized for the public code archive.
        year_max = np.full((rows, cols), -np.inf, dtype="float32")
        n_used = 0

        for fp in daily_files:
            try:
                grid = read_daily_grid(fp, meta)
            except Exception as e:
                print("[INFO] Notebook progress message.")
                continue

            # Original notebook comment normalized for the public code archive.
            year_max = np.maximum(year_max, np.where(np.isfinite(grid), grid, -np.inf))
            n_used += 1

            if n_used % 50 == 0:
                print("[INFO] Notebook progress message.")

        # Original notebook comment normalized for the public code archive.
        year_max[~np.isfinite(year_max)] = np.nan

        mm[yi, :, :] = year_max
        mm.flush()

        finite_share = np.isfinite(year_max).mean()
        print(f"[DONE] {year}: used_days={n_used}, finite_share={finite_share:.4f}")

    np.save(YEARS_NPY, np.array(years, dtype=np.int32))
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    return years


# =========================================================
# Gumbel return-period processing.
# =========================================================

def gumbel_return_level_from_mean_std(mean, std, T):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    euler_gamma = 0.5772156649015329
    beta = std * np.sqrt(6.0) / np.pi
    mu = mean - euler_gamma * beta

    p = 1.0 - 1.0 / float(T)
    q = mu - beta * np.log(-np.log(p))
    return q


def fit_gumbel_maps(meta: dict, years):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows, cols = meta["rows"], meta["cols"]
    n_years = len(years)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    mm = np.memmap(
        MMAP_PATH,
        mode="r",
        dtype="float32",
        shape=(n_years, rows, cols),
    )

    # Original notebook comment normalized for the public code archive.
    out_maps = {
        T: np.full((rows, cols), np.nan, dtype="float32")
        for T in RETURN_PERIODS
    }
    valid_years_map = np.zeros((rows, cols), dtype="uint16")

    for r0 in range(0, rows, ROW_BLOCK):
        r1 = min(r0 + ROW_BLOCK, rows)
        block = mm[:, r0:r1, :].astype("float64")  # shape=(n_years, block_rows, cols)

        valid = np.isfinite(block)
        n_valid = valid.sum(axis=0).astype("int16")
        valid_years_map[r0:r1, :] = n_valid.astype("uint16")

        # mean
        mean = np.nanmean(block, axis=0)

        # Original notebook comment normalized for the public code archive.
        std = np.nanstd(block, axis=0, ddof=1)

        # Original notebook comment normalized for the public code archive.
        # 1) n_valid < MIN_VALID_YEARS -> NaN
        # =============================================================================
        # Gumbel return-period processing.
        enough = n_valid >= MIN_VALID_YEARS
        zero_std = enough & np.isfinite(mean) & (std == 0)
        pos_std = enough & np.isfinite(mean) & np.isfinite(std) & (std > 0)

        for T in RETURN_PERIODS:
            out_block = np.full(mean.shape, np.nan, dtype="float64")

            # std=0 -> q_T = mean
            out_block[zero_std] = mean[zero_std]

            # Gumbel return-period processing.
            if np.any(pos_std):
                q = gumbel_return_level_from_mean_std(mean[pos_std], std[pos_std], T)
                out_block[pos_std] = q

            if CLIP_NEGATIVE_TO_ZERO:
                out_block = np.where(np.isfinite(out_block) & (out_block < 0), 0.0, out_block)

            out_maps[T][r0:r1, :] = out_block.astype("float32")

        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    write_geotiff(
        out_path=VALID_YEARS_TIF,
        arr=valid_years_map.astype("float32"),
        transform=meta["transform"],
        crs=meta["crs"],
        nodata=NODATA,
        dtype="float32",
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    for T in RETURN_PERIODS:
        out_path = OUT_TIF_MAP[T]
        write_geotiff(
            out_path=out_path,
            arr=out_maps[T],
            transform=meta["transform"],
            crs=meta["crs"],
            nodata=NODATA,
            dtype="float32",
        )
        print("[INFO] Notebook progress message.")


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def write_geotiff(out_path: Path, arr: np.ndarray, transform, crs, nodata=-9999.0, dtype="float32"):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = np.array(arr, copy=True)

    # NaN -> nodata
    out = np.where(np.isfinite(out), out, nodata).astype(dtype)

    profile = {
        "driver": "GTiff",
        "height": out.shape[0],
        "width": out.shape[1],
        "count": 1,
        "dtype": dtype,
        "crs": crs,
        "transform": transform,
        "nodata": nodata,
        "compress": "LZW",
        "tiled": True,
    }

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(out, 1)


# =========================================================
# 5. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    meta_json = find_any_meta_json(ENSEMBLE_BASE)
    print("[INFO] Notebook progress message.")

    meta = load_meta(meta_json)
    print(
        f"[INFO] rows={meta['rows']}, cols={meta['cols']}, "
        f"compact_mode={meta['compact_mode']}, crs={meta['crs']}"
    )

    # Step 1: annual maxima
    years = build_annual_max_stack(meta)

    # Archived notebook metadata.
    fit_gumbel_maps(meta, years)

    print("\n[ALL DONE]")
    for T in RETURN_PERIODS:
        print(f"  RP{T}: {OUT_TIF_MAP[T]}")
    print(f"  Valid years map: {VALID_YEARS_TIF}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import json
import math
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine


# =========================================================
# 0. CONFIG
# =========================================================

# =============================================================================
# Original notebook comment normalized for the public code archive.
RASTER_MODE = "geotiff"

# =============================================================================
# Original notebook comment normalized for the public code archive.
RP100_TIF = Path(
    "/home/ll/jupyter_notebook/result/fixed_rp_maps/"
    "rp100_inundation_depth_p50.tif"
)

# Original notebook comment normalized for the public code archive.
RP100_BIN = Path(
    "/home/ll/jupyter_notebook/result/fixed_rp_maps/"
    "rp100_inundation_depth_p50.bin"
)
RP100_JSON = Path(
    "/home/ll/jupyter_notebook/result/fixed_rp_maps/"
    "rp100_inundation_depth_p50.bin.json"
)

# =============================================================================
COUNTY_SHP = Path(
    "/home/ll/jupyter_notebook/gis_data/China/country/country.shp"
)

# Original notebook comment normalized for the public code archive.
COUNTY_CODE_FIELD = None  # County-level processing note.

# =============================================================================
RP_LABEL = "RP100"
DEPTH_THRESHOLD = 0.3  # Original notebook comment normalized for the public code archive.

# =============================================================================
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/flood_risk_zone_rp100_dgt03"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "county_risk_zone_rp100_dgt03.csv"
OUT_PARQUET = OUT_DIR / "county_risk_zone_rp100_dgt03.parquet"
OUT_GPKG = OUT_DIR / "county_risk_zone_rp100_dgt03.gpkg"

# Original notebook comment normalized for the public code archive.
EARTH_RADIUS_KM = 6371.0088


# =========================================================
# 1. HELPERS
# =========================================================

def detect_county_code_field(gdf: gpd.GeoDataFrame, preferred=None):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if preferred is not None:
        if preferred not in gdf.columns:
            raise KeyError(f"指定的县代码字段不存在：{preferred}")
        return preferred

    candidates = ["county_code", "县代码", "code", "CODE", "adcode", "PAC"]
    for c in candidates:
        if c in gdf.columns:
            return c

    raise KeyError(
        "无法自动识别县代码字段。请手动设置 COUNTY_CODE_FIELD。"
    )


def load_raster_geotiff(fp: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with rasterio.open(fp) as src:
        depth = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs

        nodata = src.nodata
        if nodata is not None:
            depth = np.where(depth == nodata, np.nan, depth)

    return depth, transform, crs


def load_raster_binjson(bin_fp: Path, json_fp: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with open(json_fp, "r", encoding="utf-8") as f:
        meta = json.load(f)

    rows = int(meta["rows"])
    cols = int(meta["cols"])
    transform_list = meta["transform"]  # [c, f, a, e]
    c, f0, a, e = transform_list
    transform = Affine(a, 0.0, c, 0.0, e, f0)

    crs = meta.get("crs", "EPSG:4326")
    compact_mode = meta.get("compact_mode", "float16")
    band_meta = meta["bands"][0]

    scale = band_meta.get("scale", 1.0)
    offset = band_meta.get("offset", 0.0)
    nan_code = band_meta.get("nan", None)

    # Original notebook comment normalized for the public code archive.
    with open(bin_fp, "rb") as f:
        data = f.read()

    if compact_mode == "float16":
        arr = np.frombuffer(data, dtype=np.dtype("<f2")).reshape(rows, cols).astype("float32")
    elif compact_mode == "u16_q01m":
        raw = np.frombuffer(data, dtype=np.dtype("<u2")).reshape(rows, cols)
        arr = raw.astype("float32")
        if nan_code is not None:
            arr[raw == nan_code] = np.nan
        arr = arr * scale + offset
    else:
        raise ValueError(f"未知 compact_mode: {compact_mode}")

    return arr, transform, rasterio.crs.CRS.from_string(crs)


def load_risk_depth_raster():
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if RASTER_MODE == "geotiff":
        if not RP100_TIF.exists():
            raise FileNotFoundError(f"找不到 RP100 tif: {RP100_TIF}")
        depth, transform, crs = load_raster_geotiff(RP100_TIF)
    elif RASTER_MODE == "binjson":
        if not RP100_BIN.exists():
            raise FileNotFoundError(f"找不到 RP100 bin: {RP100_BIN}")
        if not RP100_JSON.exists():
            raise FileNotFoundError(f"找不到 RP100 json: {RP100_JSON}")
        depth, transform, crs = load_raster_binjson(RP100_BIN, RP100_JSON)
    else:
        raise ValueError("RASTER_MODE 必须是 'geotiff' 或 'binjson'")

    if crs is None:
        raise ValueError("输入栅格没有 CRS，无法继续。")

    return depth, transform, crs


def pixel_area_km2_by_row(transform: Affine, nrows: int, ncols: int, crs):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not crs.is_geographic:
        raise ValueError(
            "当前脚本按经纬度网格计算像元面积。"
            "请提供 EPSG:4326/地理坐标系栅格，或自行扩展到投影坐标系。"
        )

    dlon_deg = abs(transform.a)
    dlon_rad = np.deg2rad(dlon_deg)

    row_index = np.arange(nrows)
    lat_top = transform.f + row_index * transform.e
    lat_bottom = transform.f + (row_index + 1) * transform.e

    lat_top_rad = np.deg2rad(lat_top)
    lat_bottom_rad = np.deg2rad(lat_bottom)

    area_row = (
        (EARTH_RADIUS_KM ** 2)
        * dlon_rad
        * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
    )

    return area_row.reshape(-1, 1).astype("float64")


def load_counties(target_crs):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("COUNTY_SHP 缺少 CRS，请先写入坐标系。")

    code_col = detect_county_code_field(gdf, preferred=COUNTY_CODE_FIELD)
    gdf = gdf.to_crs(target_crs).copy()

    gdf["county_code"] = pd.to_numeric(gdf[code_col], errors="coerce").astype("Int64")
    gdf = gdf.dropna(subset=["county_code", "geometry"]).copy()

    # Original notebook comment normalized for the public code archive.
    gdf = gdf.reset_index(drop=True)
    gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

    return gdf[["county_code", "raster_id", "geometry"]]


def rasterize_counties(gdf_county, out_shape, transform):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    shapes = [(geom, rid) for geom, rid in zip(gdf_county.geometry, gdf_county["raster_id"])]
    rid_grid = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype="int32",
        all_touched=False
    )
    return rid_grid


def assign_terciles_ranked(df, value_col):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = df.copy()
    valid = out[value_col].notna()

    sub = out.loc[valid].sort_values([value_col, "county_code"]).reset_index(drop=True)
    n = len(sub)
    if n < 3:
        raise ValueError("有效县数量少于 3，无法构造 tercile 分组。")

    pos = np.arange(n)
    tercile = np.floor(3 * pos / n).astype(int) + 1  # 1,2,3

    sub["risk_tercile"] = tercile
    sub["risk_group"] = sub["risk_tercile"].map({
        1: "low",
        2: "middle",
        3: "high"
    })

    out = out.merge(
        sub[["county_code", "risk_tercile", "risk_group"]],
        on="county_code",
        how="left"
    )
    out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
    return out


# =========================================================
# 2. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    depth, transform, crs = load_risk_depth_raster()
    nrows, ncols = depth.shape
    print(f"[INFO] Raster shape = {nrows} x {ncols}, CRS = {crs}")

    print("[INFO] Notebook progress message.")
    gdf_county = load_counties(crs)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    rid_grid = rasterize_counties(
        gdf_county=gdf_county,
        out_shape=depth.shape,
        transform=transform
    )

    print("[INFO] Notebook progress message.")
    area_row = pixel_area_km2_by_row(transform, nrows, ncols, crs)
    area_grid = np.broadcast_to(area_row, depth.shape)

    # Original notebook comment normalized for the public code archive.
    rid_flat = rid_grid.ravel()
    area_flat = area_grid.ravel()
    depth_flat = depth.ravel()

    # County-level processing note.
    in_county = rid_flat > 0

    # Original notebook comment normalized for the public code archive.
    total_area = np.bincount(
        rid_flat[in_county],
        weights=area_flat[in_county],
        minlength=len(gdf_county) + 1
    )

    # Original notebook comment normalized for the public code archive.
    inund_mask = in_county & np.isfinite(depth_flat) & (depth_flat > DEPTH_THRESHOLD)
    inund_area = np.bincount(
        rid_flat[inund_mask],
        weights=area_flat[inund_mask],
        minlength=len(gdf_county) + 1
    )

    # Original notebook comment normalized for the public code archive.
    df = gdf_county[["county_code", "raster_id"]].copy()
    df["county_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
    df["inund_area_km2_rp100_dgt03"] = df["raster_id"].map(lambda x: float(inund_area[x]))

    df["risk_area_share_rp100_dgt03"] = np.where(
        df["county_total_area_km2_raster"] > 0,
        df["inund_area_km2_rp100_dgt03"] / df["county_total_area_km2_raster"],
        np.nan
    )

    df["rp_label"] = RP_LABEL
    df["depth_threshold_m"] = DEPTH_THRESHOLD

    print("[INFO] Notebook progress message.")
    df = assign_terciles_ranked(df, value_col="risk_area_share_rp100_dgt03")

    # Original notebook comment normalized for the public code archive.
    out_cols = [
        "county_code",
        "rp_label",
        "depth_threshold_m",
        "county_total_area_km2_raster",
        "inund_area_km2_rp100_dgt03",
        "risk_area_share_rp100_dgt03",
        "risk_tercile",
        "risk_group",
        "top_bottom_sample",
    ]
    df_out = df[out_cols].copy()

    df_out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    df_out.to_parquet(OUT_PARQUET, index=False)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    gdf_map = gdf_county.merge(df_out, on="county_code", how="left")
    gdf_map.to_file(OUT_GPKG, layer="risk_zone", driver="GPKG")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("\n[SUMMARY] risk_group count:")
    print(df_out["risk_group"].value_counts(dropna=False).sort_index())

    print("\n[SUMMARY] area share by group:")
    print(
        df_out.groupby("risk_group", dropna=False)["risk_area_share_rp100_dgt03"]
        .describe()
    )

    print("\n[HEAD]")
    print(df_out.head())


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)


# =========================================================
# 0. CONFIG
# =========================================================

# =============================================================================
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# =============================================================================
RISK_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/flood_risk_zone_rp100_dgt03/"
    "county_risk_zone_rp100_dgt03.parquet"
)

# =============================================================================
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/edu_years_highlow_risk_rp100_dgt03"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = OUT_DIR / "edu_years_highlow_risk_linear_allT.csv"
OUT_FIG = OUT_DIR / "coefplot_edu_years_high_vs_low_risk.png"

# =============================================================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True
RISK_GROUPS = ["low", "high"]
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

DEPVAR = "edu_years"
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"


# =========================================================
# 1. HELPERS
# =========================================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = pd.to_numeric(df["M2"], errors="coerce") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
        df.loc[pd.isna(df["M2"]), "is_urban"] = np.nan

    if "is_migrant" not in df.columns and "M38" in df.columns:
        M38 = pd.to_numeric(df["M38"], errors="coerce")
        df["is_migrant"] = np.where(M38 == 1, 0, 1)
        df.loc[pd.isna(M38), "is_migrant"] = np.nan

    return df


def detect_T_list(df):
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except Exception:
                continue
    return sorted(ts) if ts else T_LIST_DEFAULT


def normalize_tidy(res):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"

    res = res.rename(columns=rename_map)

    if "StdError" not in res.columns:
        for c in res.columns:
            if "std" in c.lower():
                res = res.rename(columns={c: "StdError"})
                break

    if "PValue" not in res.columns:
        for c in res.columns:
            if c.lower().startswith("p"):
                res = res.rename(columns={c: "PValue"})
                break

    return res


def get_nobs(fit, fallback_df):
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                v = getattr(fit, attr)
                if isinstance(v, (int, float)):
                    return int(v)
            except Exception:
                pass
    return int(len(fallback_df))


def load_risk_table():
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df_risk = pd.read_parquet(RISK_PARQUET)

    need_cols = [
        "county_code",
        "risk_area_share_rp100_dgt03",
        "risk_group",
        "top_bottom_sample",
    ]
    miss = [c for c in need_cols if c not in df_risk.columns]
    if miss:
        raise KeyError(f"风险表缺少列：{miss}")

    df_risk["county_code"] = pd.to_numeric(df_risk["county_code"], errors="coerce").astype("Int64")
    df_risk = df_risk[df_risk["risk_group"].isin(RISK_GROUPS)].copy()

    return df_risk[
        ["county_code", "risk_area_share_rp100_dgt03", "risk_group"]
    ].drop_duplicates(subset=["county_code"])


def prepare_sample(df_all, main_share, main_years, risk_group):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_all.copy()

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3", "M51",
        DEPVAR, main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    # county_code
    if "county_code" in df.columns:
        df["county_code"] = pd.to_numeric(df["county_code"], errors="coerce").astype("Int64")
    else:
        df["county_code"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")

    mask = pd.Series(True, index=df.index)

    # top vs bottom tercile
    mask &= (df["risk_group"] == risk_group)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df.loc[mask].copy()

    # Original notebook comment normalized for the public code archive.
    need_cols = ["M2", "county_code", "birth_year", DEPVAR, main_share, main_years]
    dfm = dfm.dropna(subset=need_cols)

    # province × birth FE
    dfm["M2"] = pd.to_numeric(dfm["M2"], errors="coerce")
    dfm = dfm.dropna(subset=["M2"])
    dfm["M2"] = dfm["M2"].astype(np.int64)

    dfm["birth_year"] = pd.to_numeric(dfm["birth_year"], errors="coerce")
    dfm = dfm.dropna(subset=["birth_year"])
    dfm["birth_year"] = dfm["birth_year"].astype(np.int64)

    dfm["prov_code"] = (dfm["M2"] // 10000).astype(np.int64)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in ["M34", "M37", "M15", "M16"]:
        if c not in dfm.columns:
            raise KeyError(f"缺少控制变量：{c}")
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # outcome
    dfm[DEPVAR] = pd.to_numeric(dfm[DEPVAR], errors="coerce")
    dfm = dfm.dropna(subset=[DEPVAR])

    return dfm.reset_index(drop=True)


def run_linear(dfm, main_share):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fml = (
        f"{DEPVAR} ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].astype(str).str.contains(main_share, na=False)].copy()
    if key.empty:
        return None

    row = key.iloc[0]
    est = float(row["Estimate"])
    se  = float(row.get("StdError", np.nan))
    pv  = float(row.get("PValue", np.nan))

    return {
        "Estimate": est,
        "StdError": se,
        "PValue": pv,
        "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
        "mean_depvar": float(dfm[DEPVAR].mean()),
    }


# =========================================================
# 2. PLOTTING
# =========================================================

def plot_high_vs_low(out_df, save_path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    dfp = out_df.copy()
    if dfp.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    dfp["T"] = pd.to_numeric(dfp["T"], errors="coerce")
    dfp = dfp.dropna(subset=["T"]).sort_values(["risk_group", "T"])

    fig, ax = plt.subplots(figsize=(8.0, 5.2))

    style_map = {
        "low":  {"color": "#1f77b4", "label": "Low-risk counties"},
        "high": {"color": "#d62728", "label": "High-risk counties"},
    }

    for rg in RISK_GROUPS:
        sub = dfp[dfp["risk_group"] == rg].copy()
        if sub.empty:
            continue

        xs = sub["T"].to_numpy(float)
        ys = sub["Estimate"].to_numpy(float)
        lo = sub["CI_low"].to_numpy(float)
        hi = sub["CI_high"].to_numpy(float)

        yerr = np.vstack([ys - lo, hi - ys])

        ax.errorbar(
            xs, ys, yerr=yerr,
            fmt="o-", capsize=4, lw=1.6, ms=6,
            color=style_map[rg]["color"],
            label=style_map[rg]["label"]
        )

    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks(sorted(dfp["T"].dropna().unique()))
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(plt.NullFormatter())

    ax.set_xlabel("Flood return period T (years, log scale)")
    ax.set_ylabel("Effect of childhood flood exposure on years of schooling")
    ax.set_title(
        "Flood exposure and children's years of schooling\n"
        "Comparison between low- and high-background-risk counties"
    )
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(save_path, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 3. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    risk = load_risk_table()
    print("[INFO] Notebook progress message.")

    # county_code
    if "county_code" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["county_code"], errors="coerce").astype("Int64")
    else:
        edu["county_code"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")

    print("[INFO] Notebook progress message.")
    df_all = edu.merge(
        risk,
        how="left",
        on="county_code",
        validate="m:1"
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    T_list = detect_T_list(df_all)
    print("[INFO] Notebook progress message.")

    results = []

    for T in T_list:
        T_str = str(int(T)) if float(T).is_integer() else str(T)
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print("[INFO] Notebook progress message.")
            continue

        print("\n====================================================")
        print(f"[PANEL] T = {T_str}")
        print("====================================================")

        for rg in RISK_GROUPS:
            dfm = prepare_sample(df_all, main_share, main_years, rg)
            print(f"[SAMPLE] risk_group = {rg:>4s} | N = {len(dfm):,}")

            if len(dfm) == 0:
                continue

            res = run_linear(dfm, main_share)
            if res is None:
                continue

            results.append({
                "T": float(T),
                "T_str": T_str,
                "risk_group": rg,
                "depvar": DEPVAR,
                "main_share": main_share,
                "main_years": main_years,
                "age_min": AGE_MIN,
                "age_max": AGE_MAX,
                "birth_min": BIRTH_MIN,
                "birth_max": BIRTH_MAX,
                "only_non_migrant": ONLY_NON_MIGRANT,
                **res
            })

    out = pd.DataFrame(results)
    if out.empty:
        print("[INFO] Notebook progress message.")
        return

    out = out.sort_values(["risk_group", "T"]).reset_index(drop=True)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    print(out.head())

    plot_high_vs_low(out, OUT_FIG)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)


# =========================================================
# 0. CONFIG
# =========================================================

# =============================================================================
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# =============================================================================
RISK_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/flood_risk_zone_rp100_dgt03/"
    "county_risk_zone_rp100_dgt03.parquet"
)

# =============================================================================
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/edu_years_highlow_risk_rp100_dgt03_all_rural_urban"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = OUT_DIR / "edu_years_highlow_risk_linear_allT_all_rural_urban.csv"

OUT_FIG_COMBINED = OUT_DIR / "coefplot_edu_years_high_vs_low_risk_all_rural_urban.png"
OUT_FIG_ALL      = OUT_DIR / "coefplot_edu_years_high_vs_low_risk_all.png"
OUT_FIG_RURAL    = OUT_DIR / "coefplot_edu_years_high_vs_low_risk_rural.png"
OUT_FIG_URBAN    = OUT_DIR / "coefplot_edu_years_high_vs_low_risk_urban.png"

# =============================================================================
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
RISK_GROUPS = ["low", "high"]

# Original notebook comment normalized for the public code archive.
SAMPLE_TYPES = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
DEPVAR = "edu_years"

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# Original notebook comment normalized for the public code archive.
STAR_10 = 0.10
STAR_05 = 0.05
STAR_01 = 0.01


# =========================================================
# 1. HELPERS
# =========================================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = pd.to_numeric(df["M2"], errors="coerce") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
        df.loc[pd.isna(df["M2"]), "is_urban"] = np.nan

    if "is_migrant" not in df.columns and "M38" in df.columns:
        M38 = pd.to_numeric(df["M38"], errors="coerce")
        df["is_migrant"] = np.where(M38 == 1, 0, 1)
        df.loc[pd.isna(M38), "is_migrant"] = np.nan

    return df


def detect_T_list(df):
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except Exception:
                continue
    return sorted(ts) if ts else T_LIST_DEFAULT


def normalize_tidy(res):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"

    res = res.rename(columns=rename_map)

    if "StdError" not in res.columns:
        for c in res.columns:
            if "std" in c.lower():
                res = res.rename(columns={c: "StdError"})
                break

    if "PValue" not in res.columns:
        for c in res.columns:
            if c.lower().startswith("p"):
                res = res.rename(columns={c: "PValue"})
                break

    return res


def get_nobs(fit, fallback_df):
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                v = getattr(fit, attr)
                if isinstance(v, (int, float)):
                    return int(v)
            except Exception:
                pass
    return int(len(fallback_df))


def stars_for_p(p):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < STAR_01:
        return "***"
    elif p < STAR_05:
        return "**"
    elif p < STAR_10:
        return "*"
    else:
        return ""


def load_risk_table():
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df_risk = pd.read_parquet(RISK_PARQUET)

    need_cols = [
        "county_code",
        "risk_area_share_rp100_dgt03",
        "risk_group",
        "top_bottom_sample",
    ]
    miss = [c for c in need_cols if c not in df_risk.columns]
    if miss:
        raise KeyError(f"风险表缺少列：{miss}")

    df_risk["county_code"] = pd.to_numeric(
        df_risk["county_code"], errors="coerce"
    ).astype("Int64")

    df_risk = df_risk[df_risk["risk_group"].isin(RISK_GROUPS)].copy()

    return df_risk[
        ["county_code", "risk_area_share_rp100_dgt03", "risk_group"]
    ].drop_duplicates(subset=["county_code"])


def prepare_sample(df_all, main_share, main_years, risk_group, sample_type):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_all.copy()

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3", "M51",
        DEPVAR, main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    # county_code
    if "county_code" in df.columns:
        df["county_code"] = pd.to_numeric(df["county_code"], errors="coerce").astype("Int64")
    else:
        df["county_code"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")

    mask = pd.Series(True, index=df.index)

    # top vs bottom tercile
    mask &= (df["risk_group"] == risk_group)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    # all / rural / urban
    if sample_type == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_type == "urban":
        mask &= (df["is_urban"] == 1)
    elif sample_type == "all":
        pass
    else:
        raise ValueError(f"未知 sample_type: {sample_type}")

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df.loc[mask].copy()

    # Original notebook comment normalized for the public code archive.
    need_cols = ["M2", "county_code", "birth_year", DEPVAR, main_share, main_years]
    dfm = dfm.dropna(subset=need_cols)

    # province × birth FE
    dfm["M2"] = pd.to_numeric(dfm["M2"], errors="coerce")
    dfm = dfm.dropna(subset=["M2"])
    dfm["M2"] = dfm["M2"].astype(np.int64)

    dfm["birth_year"] = pd.to_numeric(dfm["birth_year"], errors="coerce")
    dfm = dfm.dropna(subset=["birth_year"])
    dfm["birth_year"] = dfm["birth_year"].astype(np.int64)

    dfm["prov_code"] = (dfm["M2"] // 10000).astype(np.int64)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in ["M34", "M37", "M15", "M16"]:
        if c not in dfm.columns:
            raise KeyError(f"缺少控制变量：{c}")
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # outcome
    dfm[DEPVAR] = pd.to_numeric(dfm[DEPVAR], errors="coerce")
    dfm = dfm.dropna(subset=[DEPVAR])

    return dfm.reset_index(drop=True)


def run_linear(dfm, main_share):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fml = (
        f"{DEPVAR} ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].astype(str).str.contains(main_share, na=False)].copy()
    if key.empty:
        return None

    row = key.iloc[0]
    est = float(row["Estimate"])
    se  = float(row.get("StdError", np.nan))
    pv  = float(row.get("PValue", np.nan))

    return {
        "Estimate": est,
        "StdError": se,
        "PValue": pv,
        "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
        "mean_depvar": float(dfm[DEPVAR].mean()),
    }


# =========================================================
# 2. PLOTTING
# =========================================================

def compute_global_ylims(out_df):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    vals = pd.concat([
        out_df["CI_low"].replace([np.inf, -np.inf], np.nan),
        out_df["CI_high"].replace([np.inf, -np.inf], np.nan),
    ], axis=0).dropna()

    if vals.empty:
        return (-1, 1)

    ymin = vals.min()
    ymax = vals.max()
    yr = ymax - ymin
    pad = 0.10 * yr if yr > 0 else 0.2
    return (ymin - pad, ymax + pad)


def plot_one_panel(ax, sub_df, sample_type, ylims=None):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    style_map = {
        "low":  {"color": "#1f77b4", "label": "Low-risk counties",  "xmult": 0.94},
        "high": {"color": "#d62728", "label": "High-risk counties", "xmult": 1.06},
    }

    # Original notebook comment normalized for the public code archive.
    vals = pd.concat([
        sub_df["CI_low"].replace([np.inf, -np.inf], np.nan),
        sub_df["CI_high"].replace([np.inf, -np.inf], np.nan),
    ], axis=0).dropna()

    if vals.empty:
        y_offset = 0.05
    else:
        y_range = vals.max() - vals.min()
        y_offset = 0.04 * y_range if y_range > 0 else 0.05

    for rg in RISK_GROUPS:
        sub = sub_df[sub_df["risk_group"] == rg].copy()
        if sub.empty:
            continue

        sub["T"] = pd.to_numeric(sub["T"], errors="coerce")
        sub = sub.dropna(subset=["T"]).sort_values("T")

        xs_base = sub["T"].to_numpy(float)
        xs = xs_base * style_map[rg]["xmult"]

        ys = sub["Estimate"].to_numpy(float)
        lo = sub["CI_low"].to_numpy(float)
        hi = sub["CI_high"].to_numpy(float)
        pv = sub["PValue"].to_numpy(float)

        yerr = np.vstack([ys - lo, hi - ys])

        ax.errorbar(
            xs, ys, yerr=yerr,
            fmt="o-", capsize=4, lw=1.8, ms=7,
            color=style_map[rg]["color"],
            label=style_map[rg]["label"]
        )

        # Original notebook comment normalized for the public code archive.
        for x, y, p in zip(xs, ys, pv):
            s = stars_for_p(p)
            if s:
                ax.text(
                    x, y + y_offset, s,
                    ha="center", va="bottom",
                    fontsize=11, color=style_map[rg]["color"]
                )

    ax.axhline(0, color="gray", linestyle="--", linewidth=1)

    ax.set_xscale("log")
    ticks = sorted(sub_df["T"].dropna().unique())
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(NullFormatter())

    if ylims is not None:
        ax.set_ylim(*ylims)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(title_map.get(sample_type, sample_type), fontsize=13)


def plot_combined_three_panels(out_df, save_path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6), sharey=True)

    ylims = compute_global_ylims(out_df)

    for ax, sample_type in zip(axes, SAMPLE_TYPES):
        sub_df = out_df[out_df["sample_type"] == sample_type].copy()

        if sub_df.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        plot_one_panel(ax, sub_df, sample_type, ylims=ylims)
        ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)

    axes[0].set_ylabel("Effect of childhood flood exposure on years of schooling", fontsize=13)

    # Original notebook comment normalized for the public code archive.
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 1.02)
        )

    fig.suptitle(
        "Flood exposure and children's years of schooling\n"
        "Comparison between low- and high-background-risk counties",
        fontsize=18, y=1.08
    )
    fig.text(
        0.5, -0.02,
        "Notes: *** p<0.01, ** p<0.05, * p<0.10. Error bars are 95% confidence intervals.",
        ha="center", fontsize=11
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single_sample(out_df, sample_type, save_path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub_df = out_df[out_df["sample_type"] == sample_type].copy()
    if sub_df.empty:
        print("[INFO] Notebook progress message.")
        return

    fig, ax = plt.subplots(figsize=(8.2, 5.5))
    ylims = compute_global_ylims(sub_df)

    plot_one_panel(ax, sub_df, sample_type, ylims=ylims)

    ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)
    ax.set_ylabel("Effect of childhood flood exposure on years of schooling", fontsize=13)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(
        "Flood exposure and children's years of schooling\n"
        f"Comparison between low- and high-background-risk counties ({title_map.get(sample_type, sample_type)})",
        fontsize=16
    )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=False, fontsize=12, loc="best")

    fig.text(
        0.5, -0.02,
        "Notes: *** p<0.01, ** p<0.05, * p<0.10. Error bars are 95% confidence intervals.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 3. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    risk = load_risk_table()
    print("[INFO] Notebook progress message.")

    # county_code
    if "county_code" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["county_code"], errors="coerce").astype("Int64")
    else:
        edu["county_code"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")

    print("[INFO] Notebook progress message.")
    df_all = edu.merge(
        risk,
        how="left",
        on="county_code",
        validate="m:1"
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    T_list = detect_T_list(df_all)
    print("[INFO] Notebook progress message.")

    results = []

    for T in T_list:
        T_str = str(int(T)) if float(T).is_integer() else str(T)
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print("[INFO] Notebook progress message.")
            continue

        print("\n====================================================")
        print(f"[PANEL] T = {T_str}")
        print("====================================================")

        for sample_type in SAMPLE_TYPES:
            for rg in RISK_GROUPS:
                dfm = prepare_sample(df_all, main_share, main_years, rg, sample_type)
                print(
                    f"[SAMPLE] sample_type = {sample_type:>5s} | "
                    f"risk_group = {rg:>4s} | N = {len(dfm):,}"
                )

                if len(dfm) == 0:
                    continue

                res = run_linear(dfm, main_share)
                if res is None:
                    continue

                results.append({
                    "T": float(T),
                    "T_str": T_str,
                    "sample_type": sample_type,
                    "risk_group": rg,
                    "depvar": DEPVAR,
                    "main_share": main_share,
                    "main_years": main_years,
                    "age_min": AGE_MIN,
                    "age_max": AGE_MAX,
                    "birth_min": BIRTH_MIN,
                    "birth_max": BIRTH_MAX,
                    "only_non_migrant": ONLY_NON_MIGRANT,
                    **res
                })

    out = pd.DataFrame(results)
    if out.empty:
        print("[INFO] Notebook progress message.")
        return

    out = out.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    print(out.head())

    # Original notebook comment normalized for the public code archive.
    plot_combined_three_panels(out, OUT_FIG_COMBINED)

    # Original notebook comment normalized for the public code archive.
    plot_single_sample(out, "all", OUT_FIG_ALL)
    plot_single_sample(out, "rural", OUT_FIG_RURAL)
    plot_single_sample(out, "urban", OUT_FIG_URBAN)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter

# =========================================================
# 0. PATHS
# =========================================================

# Original notebook comment normalized for the public code archive.
IN_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "edu_years_highlow_risk_rp100_dgt03_all_rural_urban/"
    "edu_years_highlow_risk_linear_allT_all_rural_urban.csv"
)

# Original notebook comment normalized for the public code archive.
PLOT_DIR = Path("/home/ll/jupyter_notebook/impact/windows/绘图/Gumbel/高低风险分区")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
OUT_PLOTDATA_ALL = PLOT_DIR / "plotdata_edu_years_highlow_all_rural_urban.csv"
OUT_PLOTDATA_SUB = {
    "all":   PLOT_DIR / "plotdata_edu_years_highlow_all.csv",
    "rural": PLOT_DIR / "plotdata_edu_years_highlow_rural.csv",
    "urban": PLOT_DIR / "plotdata_edu_years_highlow_urban.csv",
}

# Original notebook comment normalized for the public code archive.
OUT_FIG_COMBINED = PLOT_DIR / "coefplot_edu_years_high_vs_low_risk_all_rural_urban.png"
OUT_FIG_SINGLE = {
    "all":   PLOT_DIR / "coefplot_edu_years_high_vs_low_risk_all.png",
    "rural": PLOT_DIR / "coefplot_edu_years_high_vs_low_risk_rural.png",
    "urban": PLOT_DIR / "coefplot_edu_years_high_vs_low_risk_urban.png",
}

# Original notebook comment normalized for the public code archive.
SAMPLE_TYPES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]

# Original notebook comment normalized for the public code archive.
STAR_10 = 0.10
STAR_05 = 0.05
STAR_01 = 0.01


# =========================================================
# 1. HELPERS
# =========================================================

def stars_for_p(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < STAR_01:
        return "***"
    elif p < STAR_05:
        return "**"
    elif p < STAR_10:
        return "*"
    else:
        return ""


def load_and_prepare_plot_data(in_csv: Path) -> pd.DataFrame:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not in_csv.exists():
        raise FileNotFoundError(f"找不到输入结果表：{in_csv}")

    df = pd.read_csv(in_csv)

    required_cols = [
        "T", "T_str", "sample_type", "risk_group", "depvar",
        "Estimate", "StdError", "PValue", "CI_low", "CI_high",
        "nobs", "mean_depvar"
    ]
    miss = [c for c in required_cols if c not in df.columns]
    if miss:
        raise KeyError(f"输入结果表缺少列：{miss}")

    # Original notebook comment normalized for the public code archive.
    for c in ["T", "Estimate", "StdError", "PValue", "CI_low", "CI_high", "nobs", "mean_depvar"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["sample_type"] = df["sample_type"].astype(str)
    df["risk_group"] = df["risk_group"].astype(str)
    df["star"] = df["PValue"].apply(stars_for_p)

    # Original notebook comment normalized for the public code archive.
    xmult_map = {
        "low": 0.94,
        "high": 1.06,
    }
    df["xmult"] = df["risk_group"].map(xmult_map)
    df["x_plot"] = df["T"] * df["xmult"]

    # Original notebook comment normalized for the public code archive.
    df = df.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)
    return df


def export_plot_data(df: pd.DataFrame):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df.to_csv(OUT_PLOTDATA_ALL, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    for s in SAMPLE_TYPES:
        sub = df[df["sample_type"] == s].copy()
        sub.to_csv(OUT_PLOTDATA_SUB[s], index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")


def compute_global_ylims(df: pd.DataFrame):
    vals = pd.concat([
        df["CI_low"].replace([np.inf, -np.inf], np.nan),
        df["CI_high"].replace([np.inf, -np.inf], np.nan),
    ], axis=0).dropna()

    if vals.empty:
        return (-1, 1)

    ymin = vals.min()
    ymax = vals.max()
    yr = ymax - ymin
    pad = 0.10 * yr if yr > 0 else 0.2
    return (ymin - pad, ymax + pad)


def plot_one_panel(ax, sub_df: pd.DataFrame, sample_type: str, ylims=None):
    style_map = {
        "low":  {"color": "#1f77b4", "label": "Low-risk counties"},
        "high": {"color": "#d62728", "label": "High-risk counties"},
    }

    vals = pd.concat([
        sub_df["CI_low"].replace([np.inf, -np.inf], np.nan),
        sub_df["CI_high"].replace([np.inf, -np.inf], np.nan),
    ], axis=0).dropna()

    if vals.empty:
        y_offset = 0.05
    else:
        y_range = vals.max() - vals.min()
        y_offset = 0.04 * y_range if y_range > 0 else 0.05

    for rg in RISK_GROUPS:
        g = sub_df[sub_df["risk_group"] == rg].copy()
        if g.empty:
            continue

        g = g.sort_values("T")
        xs = g["x_plot"].to_numpy(float)
        ys = g["Estimate"].to_numpy(float)
        lo = g["CI_low"].to_numpy(float)
        hi = g["CI_high"].to_numpy(float)
        stars = g["star"].tolist()

        yerr = np.vstack([ys - lo, hi - ys])

        ax.errorbar(
            xs, ys, yerr=yerr,
            fmt="o-", capsize=4, lw=1.8, ms=7,
            color=style_map[rg]["color"],
            label=style_map[rg]["label"]
        )

        for x, y, st in zip(xs, ys, stars):
            if st:
                ax.text(
                    x, y + y_offset, st,
                    ha="center", va="bottom",
                    fontsize=11, color=style_map[rg]["color"]
                )

    ax.axhline(0, color="gray", linestyle="--", linewidth=1)

    ax.set_xscale("log")
    ticks = sorted(sub_df["T"].dropna().unique())
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(NullFormatter())

    if ylims is not None:
        ax.set_ylim(*ylims)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(title_map.get(sample_type, sample_type), fontsize=13)


def plot_combined_from_exported_csv(plot_csv: Path, out_png: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(plot_csv)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6), sharey=True)
    ylims = compute_global_ylims(df)

    for ax, s in zip(axes, SAMPLE_TYPES):
        sub = df[df["sample_type"] == s].copy()
        if sub.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        plot_one_panel(ax, sub, s, ylims=ylims)
        ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)

    axes[0].set_ylabel("Effect of childhood flood exposure on years of schooling", fontsize=13)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 1.02)
        )

    fig.suptitle(
        "Flood exposure and children's years of schooling\n"
        "Comparison between low- and high-background-risk counties",
        fontsize=18, y=1.08
    )
    fig.text(
        0.5, -0.02,
        "Notes: *** p<0.01, ** p<0.05, * p<0.10. Error bars are 95% confidence intervals.",
        ha="center", fontsize=11
    )

    plt.tight_layout()
    plt.savefig(out_png, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single_from_exported_csv(plot_csv: Path, sample_type: str, out_png: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(plot_csv)
    if df.empty:
        print("[INFO] Notebook progress message.")
        return

    fig, ax = plt.subplots(figsize=(8.2, 5.5))
    ylims = compute_global_ylims(df)

    plot_one_panel(ax, df, sample_type, ylims=ylims)

    ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)
    ax.set_ylabel("Effect of childhood flood exposure on years of schooling", fontsize=13)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(
        "Flood exposure and children's years of schooling\n"
        f"Comparison between low- and high-background-risk counties ({title_map.get(sample_type, sample_type)})",
        fontsize=16
    )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=False, fontsize=12, loc="best")

    fig.text(
        0.5, -0.02,
        "Notes: *** p<0.01, ** p<0.05, * p<0.10. Error bars are 95% confidence intervals.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(out_png, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 2. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    df_plot = load_and_prepare_plot_data(IN_CSV)

    print("[INFO] Notebook progress message.")
    export_plot_data(df_plot)

    print("[INFO] Notebook progress message.")
    plot_combined_from_exported_csv(OUT_PLOTDATA_ALL, OUT_FIG_COMBINED)

    print("[INFO] Notebook progress message.")
    for s in SAMPLE_TYPES:
        plot_single_from_exported_csv(
            OUT_PLOTDATA_SUB[s],
            sample_type=s,
            out_png=OUT_FIG_SINGLE[s]
        )

    print("\n[ALL DONE]")
    print(f"[OUT DIR] {PLOT_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

IN_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "edu_years_highlow_risk_rp100_dgt03_all_rural_urban/"
    "edu_years_highlow_risk_linear_allT_all_rural_urban.csv"
)

OUT_DIR = Path("/home/ll/jupyter_notebook/impact/windows/绘图/Gumbel/高低风险分区_betaT")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_POINTS_CSV = OUT_DIR / "betaT_edu_years_highlow_points.csv"
OUT_GRID_CSV   = OUT_DIR / "betaT_edu_years_highlow_grid.csv"

OUT_FIG_COMBINED = OUT_DIR / "betaT_edu_years_highlow_all_rural_urban.png"
OUT_FIG_ALL      = OUT_DIR / "betaT_edu_years_highlow_all.png"
OUT_FIG_RURAL    = OUT_DIR / "betaT_edu_years_highlow_rural.png"
OUT_FIG_URBAN    = OUT_DIR / "betaT_edu_years_highlow_urban.png"

DEPVAR = "edu_years"
SAMPLE_TYPES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
STAR_10 = 0.10
STAR_05 = 0.05
STAR_01 = 0.01


# =========================================================
# 1. SMALL TOOLS
# =========================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if np.isnan(p):
        return ""
    if p < STAR_01:
        return "***"
    elif p < STAR_05:
        return "**"
    elif p < STAR_10:
        return "*"
    else:
        return ""

def load_points(in_csv: Path) -> pd.DataFrame:
    if not in_csv.exists():
        raise FileNotFoundError(f"找不到输入结果表：{in_csv}")

    df = pd.read_csv(in_csv)

    required_cols = [
        "T", "T_str", "sample_type", "risk_group", "depvar",
        "Estimate", "StdError", "PValue", "CI_low", "CI_high",
        "nobs", "mean_depvar"
    ]
    miss = [c for c in required_cols if c not in df.columns]
    if miss:
        raise KeyError(f"输入结果表缺少列：{miss}")

    df = df[df["depvar"] == DEPVAR].copy()

    for c in ["T", "Estimate", "StdError", "PValue", "CI_low", "CI_high", "nobs", "mean_depvar"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["sample_type"] = df["sample_type"].astype(str)
    df["risk_group"] = df["risk_group"].astype(str)

    df = df.dropna(subset=["T", "Estimate", "StdError", "sample_type", "risk_group"])
    df["T"] = df["T"].astype(float)
    df["star"] = df["PValue"].apply(stars_for_p)

    df = df.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)
    df.to_csv(OUT_POINTS_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df


# =========================================================
# 2. FIT β(T) FOR EACH (sample_type, risk_group)
# =========================================================

def fit_beta_curve(sub: pd.DataFrame):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("T").copy()

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)

    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    if len(T_vals) >= 3:
        X = np.column_stack([np.ones_like(logT), logT, logT ** 2])
        degree = 2
    elif len(T_vals) == 2:
        X = np.column_stack([np.ones_like(logT), logT])
        degree = 1
    else:
        X = np.ones((len(logT), 1))
        degree = 0

    model = sm.WLS(est, X, weights=w)
    fit = model.fit()

    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), 200)
    T_grid = np.exp(logT_grid)

    def design_vec(lt: float) -> np.ndarray:
        if degree == 2:
            return np.array([1.0, lt, lt**2], dtype="float64")
        elif degree == 1:
            return np.array([1.0, lt], dtype="float64")
        else:
            return np.array([1.0], dtype="float64")

    beta_grid = []
    se_grid = []

    for lt in logT_grid:
        v = design_vec(lt)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)
        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.array(beta_grid)
    se_grid = np.array(se_grid)
    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    grid_df = pd.DataFrame({
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "se_grid": se_grid,
        "ci_low": ci_low,
        "ci_high": ci_high,
    })

    fit_info = {
        "degree": degree,
        "fit_summary": fit.summary().as_text(),
    }

    return fit_info, grid_df


def build_all_grids(df_points: pd.DataFrame):
    grid_list = []

    for sample_type in SAMPLE_TYPES:
        for risk_group in RISK_GROUPS:
            sub = df_points[
                (df_points["sample_type"] == sample_type) &
                (df_points["risk_group"] == risk_group) &
                (df_points["T"].isin(T_LIST))
            ].copy()

            if sub.empty:
                print("[INFO] Notebook progress message.")
                continue

            fit_info, grid_df = fit_beta_curve(sub)

            print("\n" + "=" * 80)
            print(f"[INFO] β(T) WLS meta-regression: sample_type={sample_type}, risk_group={risk_group}")
            print("=" * 80)
            print(fit_info["fit_summary"])

            grid_df["sample_type"] = sample_type
            grid_df["risk_group"] = risk_group
            grid_list.append(grid_df)

    if not grid_list:
        raise RuntimeError("没有任何成功拟合的 β(T) 曲线。")

    df_grid = pd.concat(grid_list, ignore_index=True)
    df_grid.to_csv(OUT_GRID_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df_grid


# =========================================================
# 3. PLOTTING
# =========================================================

def compute_global_ylim(df_points: pd.DataFrame, df_grid: pd.DataFrame):
    vals = []

    vals.extend(df_points["CI_low"].dropna().tolist())
    vals.extend(df_points["CI_high"].dropna().tolist())
    vals.extend(df_grid["ci_low"].dropna().tolist())
    vals.extend(df_grid["ci_high"].dropna().tolist())

    vals = np.array(vals, dtype=float)
    vals = vals[np.isfinite(vals)]

    if vals.size == 0:
        return (-1, 1)

    ymin = vals.min()
    ymax = vals.max()
    yr = ymax - ymin
    pad = 0.08 * yr if yr > 0 else 0.2
    return (ymin - pad, ymax + pad)


def plot_one_panel(ax, df_points: pd.DataFrame, df_grid: pd.DataFrame, sample_type: str, ylims=None):
    style_map = {
        "low":  {"color": "#1f77b4", "label": "Low-risk counties"},
        "high": {"color": "#d62728", "label": "High-risk counties"},
    }

    sub_points = df_points[df_points["sample_type"] == sample_type].copy()
    sub_grid = df_grid[df_grid["sample_type"] == sample_type].copy()

    if sub_points.empty or sub_grid.empty:
        ax.text(0.5, 0.5, f"No data: {sample_type}", ha="center", va="center", transform=ax.transAxes)
        return

    vals = []
    vals.extend(sub_points["CI_low"].dropna().tolist())
    vals.extend(sub_points["CI_high"].dropna().tolist())
    vals.extend(sub_grid["ci_low"].dropna().tolist())
    vals.extend(sub_grid["ci_high"].dropna().tolist())
    vals = np.array(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = vals.max() - vals.min() if vals.size > 0 else 1.0
    offset = 0.03 * yr if yr > 0 else 0.03

    for rg in RISK_GROUPS:
        color = style_map[rg]["color"]

        g = sub_grid[sub_grid["risk_group"] == rg].copy().sort_values("T_grid")
        ax.plot(
            g["T_grid"].to_numpy(float),
            g["beta_grid"].to_numpy(float),
            color=color,
            linewidth=2.0,
            label=style_map[rg]["label"]
        )
        ax.fill_between(
            g["T_grid"].to_numpy(float),
            g["ci_low"].to_numpy(float),
            g["ci_high"].to_numpy(float),
            color=color,
            alpha=0.18
        )

        p = sub_points[sub_points["risk_group"] == rg].copy().sort_values("T")
        if not p.empty:
            xmult = 0.96 if rg == "low" else 1.04
            T_vals = p["T"].to_numpy(float) * xmult
            est = p["Estimate"].to_numpy(float)
            lo = p["CI_low"].to_numpy(float)
            hi = p["CI_high"].to_numpy(float)

            ax.errorbar(
                T_vals,
                est,
                yerr=[est - lo, hi - est],
                fmt="o",
                linestyle="none",
                capsize=4,
                color=color
            )

            for T0, b, st in zip(T_vals, est, p["star"].tolist()):
                if st:
                    ax.text(
                        T0,
                        b + offset,
                        st,
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        color=color
                    )

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)
    ax.set_xticks(T_LIST)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    if ylims is not None:
        ax.set_ylim(*ylims)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(title_map.get(sample_type, sample_type), fontsize=13)


def plot_combined(df_points: pd.DataFrame, df_grid: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), sharey=True)
    ylims = compute_global_ylim(df_points, df_grid)

    for ax, sample_type in zip(axes, SAMPLE_TYPES):
        plot_one_panel(ax, df_points, df_grid, sample_type=sample_type, ylims=ylims)
        ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)

    axes[0].set_ylabel("β(T): effect on years of schooling", fontsize=13)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 1.02)
        )

    fig.suptitle(
        "Nonlinear severity profile β(T) of childhood flood exposure on years of schooling\n"
        "Comparison between low- and high-background-risk counties",
        fontsize=17, y=1.08
    )
    fig.text(
        0.5, -0.02,
        "Notes: β(T) is estimated by inverse-variance weighted WLS over return periods; "
        "shaded bands denote 95% CI; stars: *** p<0.01, ** p<0.05, * p<0.10.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(OUT_FIG_COMBINED, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_points: pd.DataFrame, df_grid: pd.DataFrame, sample_type: str, out_path: Path):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    sub_points = df_points[df_points["sample_type"] == sample_type].copy()
    sub_grid = df_grid[df_grid["sample_type"] == sample_type].copy()
    ylims = compute_global_ylim(sub_points, sub_grid)

    plot_one_panel(ax, df_points, df_grid, sample_type=sample_type, ylims=ylims)

    ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)
    ax.set_ylabel("β(T): effect on years of schooling", fontsize=13)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(
        "Nonlinear severity profile β(T) of childhood flood exposure on years of schooling\n"
        f"Comparison between low- and high-background-risk counties ({title_map.get(sample_type, sample_type)})",
        fontsize=14
    )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=False, fontsize=11, loc="best")

    fig.text(
        0.5, -0.03,
        "Notes: shaded bands denote 95% CI; stars: *** p<0.01, ** p<0.05, * p<0.10.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 4. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")
    df_points = load_points(IN_CSV)

    print("[INFO] Notebook progress message.")
    df_grid = build_all_grids(df_points)

    print("[INFO] Notebook progress message.")
    plot_combined(df_points, df_grid)

    print("[INFO] Notebook progress message.")
    plot_single(df_points, df_grid, sample_type="all", out_path=OUT_FIG_ALL)
    plot_single(df_points, df_grid, sample_type="rural", out_path=OUT_FIG_RURAL)
    plot_single(df_points, df_grid, sample_type="urban", out_path=OUT_FIG_URBAN)

    print("\n[ALL DONE]")
    print(f"[OUT DIR] {OUT_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

# =============================================================================
FIXED_RP_DIR = Path("/home/ll/jupyter_notebook/result/fixed_rp_maps")
RP_TIF_MAP = {
    20: FIXED_RP_DIR / "rp20_inundation_depth_p50.tif",
    50: FIXED_RP_DIR / "rp50_inundation_depth_p50.tif",
    100: FIXED_RP_DIR / "rp100_inundation_depth_p50.tif",
}

# =============================================================================
COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
COUNTY_CODE_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"
CITY_CODE_FIELD_IN_COUNTY = "市代码"
CITY_NAME_FIELD_IN_COUNTY = "市"

# =============================================================================
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# =============================================================================
BASE_OUT = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")
OUT_DIR = BASE_OUT / "children_education"
COUNTY_CONT_DIR = OUT_DIR / "county_continuous_risk"
COUNTY_CLASS_DIR = OUT_DIR / "county_risk_classified"
REG_DIR = OUT_DIR / "regression_results"

for p in [OUT_DIR, COUNTY_CONT_DIR, COUNTY_CLASS_DIR, REG_DIR]:
    p.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = REG_DIR / "edu_robustness_27scenarios_all_results.csv"
OUT_MASTER_PARQUET = REG_DIR / "edu_robustness_27scenarios_all_results.parquet"
OUT_SCENARIO_SUMMARY = REG_DIR / "edu_robustness_27scenarios_summary.csv"

# =============================================================================
RP_LIST = [20, 50, 100]
DEPTH_LIST = [0.1, 0.3, 0.5]
SHARE_CUTOFF_LIST = [0.5, 0.6, 0.7]

# =============================================================================
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True

RISK_GROUPS = ["low", "high"]
SAMPLE_TYPES = ["all", "rural", "urban"]
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

DEPVAR = "edu_years"
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# =============================================================================
EARTH_RADIUS_KM = 6371.0088

# =========================================================
# 1. SMALL TOOLS
# =========================================================

def scenario_tag(rp: int, depth_thr: float, share_cutoff: float) -> str:
    dtag = f"d{int(round(depth_thr * 100)):03d}"   # 0.1 -> d010
    stag = f"s{int(round(share_cutoff * 100)):03d}" # 0.5 -> s050
    return f"rp{rp}_{dtag}_{stag}"

def county_continuous_tag(rp: int, depth_thr: float) -> str:
    dtag = f"d{int(round(depth_thr * 100)):03d}"
    return f"rp{rp}_{dtag}"

def normalize_county_code_numeric(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return x.astype("Int64")

def normalize_code_str(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    x = x.str.replace(r"\.0$", "", regex=True)
    return x

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def detect_T_list(df):
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                ts.add(float(c.replace("share_flood_ge_T", "")))
            except Exception:
                pass
    return sorted(ts) if ts else T_LIST_DEFAULT

def get_nobs(fit, fallback_df):
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                v = getattr(fit, attr)
                if isinstance(v, (int, float)):
                    return int(v)
            except Exception:
                pass
    return int(len(fallback_df))

def normalize_tidy(res):
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
    res = res.rename(columns=rename_map)

    if "StdError" not in res.columns:
        for c in res.columns:
            if "std" in c.lower():
                res = res.rename(columns={c: "StdError"})
                break

    if "PValue" not in res.columns:
        for c in res.columns:
            if c.lower().startswith("p"):
                res = res.rename(columns={c: "PValue"})
                break

    return res

# =========================================================
# 2. RASTER / COUNTY RISK
# =========================================================

def load_raster_geotiff(fp: Path):
    with rasterio.open(fp) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs

def pixel_area_km2_by_row(transform: Affine, nrows: int, crs):
    if not crs.is_geographic:
        raise ValueError("当前脚本按经纬度网格计算像元面积，请保证输入栅格 CRS 为地理坐标系。")

    dlon_deg = abs(transform.a)
    dlon_rad = np.deg2rad(dlon_deg)

    row_index = np.arange(nrows)
    lat_top = transform.f + row_index * transform.e
    lat_bottom = transform.f + (row_index + 1) * transform.e

    lat_top_rad = np.deg2rad(lat_top)
    lat_bottom_rad = np.deg2rad(lat_bottom)

    area_row = (
        (EARTH_RADIUS_KM ** 2)
        * dlon_rad
        * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
    )
    return area_row.reshape(-1, 1).astype("float64")

def load_counties_for_raster(target_crs):
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("COUNTY_SHP 缺少 CRS。")

    required_cols = [
        COUNTY_CODE_FIELD, COUNTY_NAME_FIELD,
        CITY_CODE_FIELD_IN_COUNTY, CITY_NAME_FIELD_IN_COUNTY,
        "geometry"
    ]
    miss = [c for c in required_cols if c not in gdf.columns]
    if miss:
        raise KeyError(f"county.shp 缺少字段: {miss}")

    gdf = gdf.to_crs(target_crs).copy()
    gdf["county_code"] = normalize_county_code_numeric(gdf[COUNTY_CODE_FIELD])
    gdf["county_name"] = gdf[COUNTY_NAME_FIELD].astype(str).str.strip()
    gdf["city_code"] = normalize_code_str(gdf[CITY_CODE_FIELD_IN_COUNTY])
    gdf["city_name"] = gdf[CITY_NAME_FIELD_IN_COUNTY].astype(str).str.strip()

    gdf = gdf.dropna(subset=["county_code", "geometry"]).copy()
    gdf = gdf.reset_index(drop=True)
    gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

    return gdf[["county_code", "county_name", "city_code", "city_name", "raster_id", "geometry"]]

def rasterize_counties(gdf_county, out_shape, transform):
    shapes = [(geom, rid) for geom, rid in zip(gdf_county.geometry, gdf_county["raster_id"])]
    rid_grid = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype="int32",
        all_touched=False
    )
    return rid_grid

def build_county_continuous_risk(rp: int, depth_thr: float) -> pd.DataFrame:
    out_parquet = COUNTY_CONT_DIR / f"county_continuous_risk_{county_continuous_tag(rp, depth_thr)}.parquet"
    out_csv = COUNTY_CONT_DIR / f"county_continuous_risk_{county_continuous_tag(rp, depth_thr)}.csv"

    if out_parquet.exists():
        df = pd.read_parquet(out_parquet)
        return df

    tif = RP_TIF_MAP[rp]
    if not tif.exists():
        raise FileNotFoundError(f"找不到固定 RP 栅格: {tif}")

    print(f"[COUNTY CONT] RP={rp}, depth>{depth_thr}m")
    depth, transform, crs = load_raster_geotiff(tif)
    nrows, ncols = depth.shape

    gdf_county = load_counties_for_raster(crs)
    rid_grid = rasterize_counties(gdf_county, depth.shape, transform)

    area_row = pixel_area_km2_by_row(transform, nrows, crs)
    area_grid = np.broadcast_to(area_row, depth.shape)

    rid_flat = rid_grid.ravel()
    area_flat = area_grid.ravel()
    depth_flat = depth.ravel()

    in_county = rid_flat > 0

    total_area = np.bincount(
        rid_flat[in_county],
        weights=area_flat[in_county],
        minlength=len(gdf_county) + 1
    )

    inund_mask = in_county & np.isfinite(depth_flat) & (depth_flat > depth_thr)
    inund_area = np.bincount(
        rid_flat[inund_mask],
        weights=area_flat[inund_mask],
        minlength=len(gdf_county) + 1
    )

    df = gdf_county[["county_code", "county_name", "city_code", "city_name", "raster_id"]].copy()
    df["rp"] = rp
    df["depth_threshold_m"] = depth_thr
    df["county_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
    df["inund_area_km2"] = df["raster_id"].map(lambda x: float(inund_area[x]))
    df["risk_area_share"] = np.where(
        df["county_total_area_km2_raster"] > 0,
        df["inund_area_km2"] / df["county_total_area_km2_raster"],
        np.nan
    )

    df = df.drop(columns=["raster_id"]).copy()
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[SAVED] {out_parquet}")
    return df

def classify_county_risk_by_share_cutoff(df_county_cont: pd.DataFrame, share_cutoff: float) -> pd.DataFrame:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = df_county_cont.copy()
    out["share_cutoff"] = share_cutoff
    out["risk_group"] = pd.NA
    out["risk_rank_pct"] = np.nan

    valid = out["risk_area_share"].notna()
    sub = out.loc[valid].copy()
    sub = sub.sort_values(["risk_area_share", "county_code"]).reset_index(drop=True)

    n = len(sub)
    if n == 0:
        return out

    if n == 1:
        sub["risk_rank_pct"] = 1.0
    else:
        sub["risk_rank_pct"] = np.arange(n, dtype=float) / (n - 1)

    low_cut = 1.0 - share_cutoff
    high_cut = share_cutoff

    sub["risk_group"] = np.where(
        sub["risk_rank_pct"] >= high_cut, "high",
        np.where(sub["risk_rank_pct"] < low_cut, "low", "middle")
    )

    out = out.drop(columns=["risk_group", "risk_rank_pct"], errors="ignore")
    out = out.merge(
        sub[["county_code", "risk_rank_pct", "risk_group"]],
        on="county_code",
        how="left",
        validate="1:1"
    )
    out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
    return out

# =========================================================
# 3. EDUCATION DATA
# =========================================================

def build_is_urban_is_migrant(df):
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = pd.to_numeric(df["M2"], errors="coerce") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
        df.loc[pd.isna(df["M2"]), "is_urban"] = np.nan

    if "is_migrant" not in df.columns and "M38" in df.columns:
        M38 = pd.to_numeric(df["M38"], errors="coerce")
        df["is_migrant"] = np.where(M38 == 1, 0, 1)
        df.loc[pd.isna(M38), "is_migrant"] = np.nan
    return df

def load_edu_base() -> pd.DataFrame:
    print(f"[READ] EDU: {EDU_PARQUET}")
    df = pd.read_parquet(EDU_PARQUET)

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3", "M51", DEPVAR
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    if "county_code" in df.columns:
        df["county_code"] = normalize_county_code_numeric(df["county_code"])
    else:
        df["county_code"] = normalize_county_code_numeric(df["M2"])

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce")

    df = df.dropna(subset=["county_code", "M2", "birth_year"]).copy()
    df["M2"] = df["M2"].astype(np.int64)
    df["birth_year"] = df["birth_year"].astype(np.int64)

    df["prov_code"] = (df["M2"] // 10000).astype(np.int64)
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(str)
    df["birth_year_c"] = df["birth_year"] - 1995

    return df.reset_index(drop=True)

def prepare_sample(df_all, main_share, main_years, risk_group, sample_type):
    df = df_all.copy()

    mask = pd.Series(True, index=df.index)

    mask &= (df["risk_group"] == risk_group)

    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    if sample_type == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_type == "urban":
        mask &= (df["is_urban"] == 1)
    elif sample_type == "all":
        pass
    else:
        raise ValueError(f"未知 sample_type: {sample_type}")

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df.loc[mask].copy()

    need_cols = ["M2", "county_code", "birth_year", DEPVAR, main_share, main_years]
    dfm = dfm.dropna(subset=need_cols)

    for c in ["M34", "M37", "M15", "M16"]:
        if c not in dfm.columns:
            raise KeyError(f"缺少控制变量：{c}")
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm[DEPVAR] = pd.to_numeric(dfm[DEPVAR], errors="coerce")
    dfm = dfm.dropna(subset=[DEPVAR])

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
    fml = (
        f"{DEPVAR} ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].astype(str).str.contains(main_share, na=False)].copy()
    if key.empty:
        return None

    row = key.iloc[0]
    est = float(row["Estimate"])
    se = float(row.get("StdError", np.nan))
    pv = float(row.get("PValue", np.nan))

    return {
        "Estimate": est,
        "StdError": se,
        "PValue": pv,
        "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
        "mean_depvar": float(dfm[DEPVAR].mean()),
    }

# =========================================================
# 4. MAIN
# =========================================================

def main():
    # =============================================================================
    edu = load_edu_base()
    T_list = detect_T_list(edu)
    print("[INFO] Notebook progress message.")

    all_results = []
    scenario_summary = []

    # Original notebook comment normalized for the public code archive.
    county_cont_cache = {}

    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            county_cont = build_county_continuous_risk(rp, depth_thr)
            county_cont_cache[(rp, depth_thr)] = county_cont

    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            county_cont = county_cont_cache[(rp, depth_thr)]

            for share_cutoff in SHARE_CUTOFF_LIST:
                scen = scenario_tag(rp, depth_thr, share_cutoff)
                print("\n" + "=" * 90)
                print(f"[SCENARIO] {scen}")
                print("=" * 90)

                # =============================================================================
                county_cls = classify_county_risk_by_share_cutoff(county_cont, share_cutoff)
                county_cls["scenario"] = scen

                out_county_parquet = COUNTY_CLASS_DIR / f"county_risk_{scen}.parquet"
                out_county_csv = COUNTY_CLASS_DIR / f"county_risk_{scen}.csv"
                county_cls.to_parquet(out_county_parquet, index=False)
                county_cls.to_csv(out_county_csv, index=False, encoding="utf-8-sig")

                print("[INFO] Notebook progress message.")
                print(county_cls["risk_group"].value_counts(dropna=False).sort_index())

                risk_small = county_cls[
                    ["county_code", "risk_area_share", "risk_rank_pct", "risk_group", "top_bottom_sample"]
                ].drop_duplicates("county_code").copy()

                df_all = edu.merge(
                    risk_small,
                    on="county_code",
                    how="left",
                    validate="m:1"
                )

                # Original notebook comment normalized for the public code archive.
                scenario_summary.append({
                    "scenario": scen,
                    "rp": rp,
                    "depth_threshold_m": depth_thr,
                    "share_cutoff": share_cutoff,
                    "n_county_total": int(county_cls["county_code"].nunique()),
                    "n_county_low": int((county_cls["risk_group"] == "low").sum()),
                    "n_county_middle": int((county_cls["risk_group"] == "middle").sum()),
                    "n_county_high": int((county_cls["risk_group"] == "high").sum()),
                    "n_micro_merged": int(len(df_all)),
                    "n_micro_in_lowhigh": int(df_all["risk_group"].isin(["low", "high"]).sum()),
                })

                # =============================================================================
                for T in T_list:
                    T_str = str(int(T)) if float(T).is_integer() else str(T)
                    main_ret = f"flood_ge_T{T_str}"
                    main_share = f"share_{main_ret}"
                    main_years = f"years_{main_ret}"

                    if main_share not in df_all.columns or main_years not in df_all.columns:
                        print("[INFO] Notebook progress message.")
                        continue

                    for sample_type in SAMPLE_TYPES:
                        for rg in RISK_GROUPS:
                            try:
                                dfm = prepare_sample(df_all, main_share, main_years, rg, sample_type)
                                n_sample = len(dfm)
                                print(
                                    f"[RUN] {scen} | T={T_str:>3s} | sample={sample_type:>5s} | "
                                    f"risk={rg:>4s} | N={n_sample:,}"
                                )

                                if n_sample == 0:
                                    continue

                                res = run_linear(dfm, main_share)
                                if res is None:
                                    continue

                                all_results.append({
                                    "scenario": scen,
                                    "rp": rp,
                                    "depth_threshold_m": depth_thr,
                                    "share_cutoff": share_cutoff,
                                    "sample_type": sample_type,
                                    "risk_group": rg,
                                    "T": float(T),
                                    "T_str": T_str,
                                    "depvar": DEPVAR,
                                    "main_share": main_share,
                                    "main_years": main_years,
                                    "age_min": AGE_MIN,
                                    "age_max": AGE_MAX,
                                    "birth_min": BIRTH_MIN,
                                    "birth_max": BIRTH_MAX,
                                    "only_non_migrant": ONLY_NON_MIGRANT,
                                    **res
                                })

                            except Exception as e:
                                print(
                                    f"[ERROR] {scen} | T={T_str} | sample={sample_type} | risk={rg} -> {e}"
                                )
                                continue

                # Original notebook comment normalized for the public code archive.
                if all_results:
                    pd.DataFrame(all_results).to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
                    pd.DataFrame(all_results).to_parquet(OUT_MASTER_PARQUET, index=False)

                pd.DataFrame(scenario_summary).to_csv(OUT_SCENARIO_SUMMARY, index=False, encoding="utf-8-sig")

    # =============================================================================
    out = pd.DataFrame(all_results)
    summ = pd.DataFrame(scenario_summary)

    if out.empty:
        print("[INFO] Notebook progress message.")
    else:
        out = out.sort_values(["scenario", "sample_type", "risk_group", "T"]).reset_index(drop=True)
        out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
        out.to_parquet(OUT_MASTER_PARQUET, index=False)
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        print(out.head())

    if not summ.empty:
        summ = summ.sort_values(["rp", "depth_threshold_m", "share_cutoff"]).reset_index(drop=True)
        summ.to_csv(OUT_SCENARIO_SUMMARY, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")

    print("\n[ALL DONE] Children education robustness analysis finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
import statsmodels.api as sm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

# =============================================================================
FIXED_RP_DIR = Path("/home/ll/jupyter_notebook/result/fixed_rp_maps")
RP_TIF_MAP = {
    20: FIXED_RP_DIR / "rp20_inundation_depth_p50.tif",
    50: FIXED_RP_DIR / "rp50_inundation_depth_p50.tif",
    100: FIXED_RP_DIR / "rp100_inundation_depth_p50.tif",
}

# =============================================================================
COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
COUNTY_CODE_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"
CITY_CODE_FIELD_IN_COUNTY = "市代码"
CITY_NAME_FIELD_IN_COUNTY = "市"

# =============================================================================
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# =============================================================================
BASE_OUT = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")
OUT_DIR = BASE_OUT / "older_health"
COUNTY_CONT_DIR = OUT_DIR / "county_continuous_risk"
COUNTY_CLASS_DIR = OUT_DIR / "county_risk_classified"
CITY_CLASS_DIR = OUT_DIR / "city_risk_classified"
REG_DIR = OUT_DIR / "regression_results"

for p in [OUT_DIR, COUNTY_CONT_DIR, COUNTY_CLASS_DIR, CITY_CLASS_DIR, REG_DIR]:
    p.mkdir(parents=True, exist_ok=True)

OUT_FE_DETAIL_CSV = REG_DIR / "older_health_robustness_27scenarios_window_specific.csv"
OUT_FE_DETAIL_PARQUET = REG_DIR / "older_health_robustness_27scenarios_window_specific.parquet"

OUT_FE_AGG_CSV = REG_DIR / "older_health_robustness_27scenarios_window_aggregated.csv"
OUT_FE_AGG_PARQUET = REG_DIR / "older_health_robustness_27scenarios_window_aggregated.parquet"

OUT_SCENARIO_SUMMARY = REG_DIR / "older_health_robustness_27scenarios_summary.csv"

# =============================================================================
RP_LIST = [20, 50, 100]
DEPTH_LIST = [0.1, 0.3, 0.5]
SHARE_CUTOFF_LIST = [0.5, 0.6, 0.7]

# =============================================================================
Y_VAR = "health_index_z"
ID_COL = "pid12"
CITY_COL = "city_code"
YEAR_COL = "year"
PROV_COL = "province"

RISK_GROUPS = ["low", "high"]
SAMPLE_SPECS = {
    "all": None,
    "urban": 1,
    "rural": 0,
}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

MIN_NOBS = 100
MIN_NCITY = 10

# =============================================================================
EARTH_RADIUS_KM = 6371.0088

# =========================================================
# 1. SMALL TOOLS
# =========================================================

def scenario_tag(rp: int, depth_thr: float, share_cutoff: float) -> str:
    dtag = f"d{int(round(depth_thr * 100)):03d}"
    stag = f"s{int(round(share_cutoff * 100)):03d}"
    return f"rp{rp}_{dtag}_{stag}"

def county_continuous_tag(rp: int, depth_thr: float) -> str:
    dtag = f"d{int(round(depth_thr * 100)):03d}"
    return f"rp{rp}_{dtag}"

def normalize_county_code_numeric(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return x.astype("Int64")

def normalize_code_str(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    x = x.str.replace(r"\.0$", "", regex=True)
    return x

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

# =========================================================
# 2. RASTER / COUNTY RISK
# =========================================================

def load_raster_geotiff(fp: Path):
    with rasterio.open(fp) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs

def pixel_area_km2_by_row(transform: Affine, nrows: int, crs):
    if not crs.is_geographic:
        raise ValueError("当前脚本按经纬度网格计算像元面积，请保证输入栅格 CRS 为地理坐标系。")

    dlon_deg = abs(transform.a)
    dlon_rad = np.deg2rad(dlon_deg)

    row_index = np.arange(nrows)
    lat_top = transform.f + row_index * transform.e
    lat_bottom = transform.f + (row_index + 1) * transform.e

    lat_top_rad = np.deg2rad(lat_top)
    lat_bottom_rad = np.deg2rad(lat_bottom)

    area_row = (
        (EARTH_RADIUS_KM ** 2)
        * dlon_rad
        * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
    )
    return area_row.reshape(-1, 1).astype("float64")

def load_counties_for_raster(target_crs):
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("COUNTY_SHP 缺少 CRS。")

    required_cols = [
        COUNTY_CODE_FIELD, COUNTY_NAME_FIELD,
        CITY_CODE_FIELD_IN_COUNTY, CITY_NAME_FIELD_IN_COUNTY,
        "geometry"
    ]
    miss = [c for c in required_cols if c not in gdf.columns]
    if miss:
        raise KeyError(f"county.shp 缺少字段: {miss}")

    gdf = gdf.to_crs(target_crs).copy()
    gdf["county_code"] = normalize_county_code_numeric(gdf[COUNTY_CODE_FIELD])
    gdf["county_name"] = gdf[COUNTY_NAME_FIELD].astype(str).str.strip()
    gdf["city_code"] = normalize_code_str(gdf[CITY_CODE_FIELD_IN_COUNTY])
    gdf["city_name"] = gdf[CITY_NAME_FIELD_IN_COUNTY].astype(str).str.strip()

    gdf = gdf.dropna(subset=["county_code", "geometry"]).copy()
    gdf = gdf.reset_index(drop=True)
    gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

    return gdf[["county_code", "county_name", "city_code", "city_name", "raster_id", "geometry"]]

def rasterize_counties(gdf_county, out_shape, transform):
    shapes = [(geom, rid) for geom, rid in zip(gdf_county.geometry, gdf_county["raster_id"])]
    rid_grid = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype="int32",
        all_touched=False
    )
    return rid_grid

def build_county_continuous_risk(rp: int, depth_thr: float) -> pd.DataFrame:
    out_parquet = COUNTY_CONT_DIR / f"county_continuous_risk_{county_continuous_tag(rp, depth_thr)}.parquet"
    out_csv = COUNTY_CONT_DIR / f"county_continuous_risk_{county_continuous_tag(rp, depth_thr)}.csv"

    if out_parquet.exists():
        return pd.read_parquet(out_parquet)

    tif = RP_TIF_MAP[rp]
    if not tif.exists():
        raise FileNotFoundError(f"找不到固定 RP 栅格: {tif}")

    print(f"[COUNTY CONT] RP={rp}, depth>{depth_thr}m")
    depth, transform, crs = load_raster_geotiff(tif)
    nrows, ncols = depth.shape

    gdf_county = load_counties_for_raster(crs)
    rid_grid = rasterize_counties(gdf_county, depth.shape, transform)

    area_row = pixel_area_km2_by_row(transform, nrows, crs)
    area_grid = np.broadcast_to(area_row, depth.shape)

    rid_flat = rid_grid.ravel()
    area_flat = area_grid.ravel()
    depth_flat = depth.ravel()

    in_county = rid_flat > 0

    total_area = np.bincount(
        rid_flat[in_county],
        weights=area_flat[in_county],
        minlength=len(gdf_county) + 1
    )

    inund_mask = in_county & np.isfinite(depth_flat) & (depth_flat > depth_thr)
    inund_area = np.bincount(
        rid_flat[inund_mask],
        weights=area_flat[inund_mask],
        minlength=len(gdf_county) + 1
    )

    df = gdf_county[["county_code", "county_name", "city_code", "city_name", "raster_id"]].copy()
    df["rp"] = rp
    df["depth_threshold_m"] = depth_thr
    df["county_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
    df["inund_area_km2"] = df["raster_id"].map(lambda x: float(inund_area[x]))
    df["risk_area_share"] = np.where(
        df["county_total_area_km2_raster"] > 0,
        df["inund_area_km2"] / df["county_total_area_km2_raster"],
        np.nan
    )

    df = df.drop(columns=["raster_id"]).copy()
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[SAVED] {out_parquet}")
    return df

def classify_county_risk_by_share_cutoff(df_county_cont: pd.DataFrame, share_cutoff: float) -> pd.DataFrame:
    out = df_county_cont.copy()
    out["share_cutoff"] = share_cutoff
    out["risk_group"] = pd.NA
    out["risk_rank_pct"] = np.nan

    valid = out["risk_area_share"].notna()
    sub = out.loc[valid].copy()
    sub = sub.sort_values(["risk_area_share", "county_code"]).reset_index(drop=True)

    n = len(sub)
    if n == 0:
        return out

    if n == 1:
        sub["risk_rank_pct"] = 1.0
    else:
        sub["risk_rank_pct"] = np.arange(n, dtype=float) / (n - 1)

    low_cut = 1.0 - share_cutoff
    high_cut = share_cutoff

    sub["risk_group"] = np.where(
        sub["risk_rank_pct"] >= high_cut, "high",
        np.where(sub["risk_rank_pct"] < low_cut, "low", "middle")
    )

    out = out.drop(columns=["risk_group", "risk_rank_pct"], errors="ignore")
    out = out.merge(
        sub[["county_code", "risk_rank_pct", "risk_group"]],
        on="county_code",
        how="left",
        validate="1:1"
    )
    out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
    return out

def classify_city_risk(row, threshold):
    sh = row["share_high_area_in_city"]
    sl = row["share_low_area_in_city"]
    if pd.notna(sh) and sh >= threshold:
        return "high"
    if pd.notna(sl) and sl >= threshold:
        return "low"
    return "middle"

def aggregate_county_to_city(df_county_cls: pd.DataFrame, share_cutoff: float) -> pd.DataFrame:
    df = df_county_cls.copy()
    df = df[df["city_code"].notna()].copy()

    df["county_area_km2_weight"] = pd.to_numeric(df["county_total_area_km2_raster"], errors="coerce")
    df["risk_area_share"] = pd.to_numeric(df["risk_area_share"], errors="coerce")

    df["area_high_km2"] = np.where(df["risk_group"] == "high", df["county_area_km2_weight"], 0.0)
    df["area_low_km2"] = np.where(df["risk_group"] == "low", df["county_area_km2_weight"], 0.0)
    df["area_middle_km2"] = np.where(df["risk_group"] == "middle", df["county_area_km2_weight"], 0.0)

    df["risk_x_area"] = df["risk_area_share"] * df["county_area_km2_weight"]

    group_cols = ["city_code"]
    rows = []

    for city_code, g in df.groupby(group_cols, dropna=False):
        total_area = g["county_area_km2_weight"].sum(min_count=1)
        high_area = g["area_high_km2"].sum(min_count=1)
        low_area = g["area_low_km2"].sum(min_count=1)
        middle_area = g["area_middle_km2"].sum(min_count=1)

        risk_num = g["risk_x_area"].sum(min_count=1)
        risk_den = g["county_area_km2_weight"].sum(min_count=1)
        risk_cont = risk_num / risk_den if pd.notna(risk_den) and risk_den > 0 else np.nan

        rows.append({
            "city_code": city_code,
            "city_name": g["city_name"].dropna().iloc[0] if g["city_name"].notna().any() else pd.NA,
            "n_counties_total": int(g["county_code"].nunique()),
            "n_counties_high": int((g["risk_group"] == "high").sum()),
            "n_counties_middle": int((g["risk_group"] == "middle").sum()),
            "n_counties_low": int((g["risk_group"] == "low").sum()),
            "city_total_area_km2_raster": total_area,
            "city_high_county_area_km2": high_area,
            "city_middle_county_area_km2": middle_area,
            "city_low_county_area_km2": low_area,
            "share_high_area_in_city": high_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_middle_area_in_city": middle_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_low_area_in_city": low_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "risk_area_share_city": risk_cont,
        })

    df_city = pd.DataFrame(rows)
    if df_city.empty:
        return df_city

    df_city["share_cutoff"] = share_cutoff
    df_city["risk_group"] = df_city.apply(classify_city_risk, axis=1, threshold=share_cutoff)
    df_city["risk_tercile"] = df_city["risk_group"].map({"low": 1, "middle": 2, "high": 3}).astype("Int64")
    df_city["top_bottom_sample"] = df_city["risk_group"].isin(["low", "high"]).astype(int)
    return df_city

# =========================================================
# 3. HEALTH PANEL / FE
# =========================================================

def demean_two_fe(df, cols, fe1, fe2):
    df = df.copy()
    g1 = df.groupby(fe1)
    g2 = df.groupby(fe2)
    mu = df[cols].mean()

    for col in cols:
        df[f"{col}_dm"] = (
            df[col]
            - g1[col].transform("mean")
            - g2[col].transform("mean")
            + mu[col]
        )
    return df

def fe_reg_twoFE_city_cluster(df, y_col, x_cols, fe1, fe2, cluster_col):
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

    ci_low, ci_high = fit.conf_int().T
    res = pd.DataFrame(
        {
            "Estimate": fit.params,
            "Std. Error": fit.bse,
            "t value": fit.tvalues,
            "Pr(>|t|)": fit.pvalues,
            "2.5%": ci_low,
            "97.5%": ci_high,
        },
        index=x_cols,
    )
    return res

def load_health_base() -> pd.DataFrame:
    print(f"[READ] HEALTH PANEL: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    df[CITY_COL] = normalize_code_str(df[CITY_COL])
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CITY_COL, YEAR_COL]).copy()
    df["age2"] = df["age"] ** 2

    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] base panel -> N={len(df):,}, N_id={df[ID_COL].nunique():,}, "
        f"N_city={df[CITY_COL].nunique():,}, N_year={df[YEAR_COL].nunique():,}"
    )
    return df.reset_index(drop=True)

def aggregate_across_window(detail_df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "scenario", "rp", "depth_threshold_m", "share_cutoff",
        "sample", "risk_group", "T"
    ]
    rows = []

    for keys, g in detail_df.groupby(group_cols, dropna=False):
        est = g["Estimate"].to_numpy(float)
        se = g["Std. Error"].to_numpy(float)

        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            t_val = np.nan
            p_val = np.nan

        ci_low = beta_w - 1.96 * se_w
        ci_high = beta_w + 1.96 * se_w

        scenario, rp, depth_thr, share_cutoff, sample, risk_group, T = keys

        rows.append({
            "scenario": scenario,
            "rp": rp,
            "depth_threshold_m": depth_thr,
            "share_cutoff": share_cutoff,
            "sample": sample,
            "risk_group": risk_group,
            "T": T,
            "Estimate": beta_w,
            "Std. Error": se_w,
            "t value": t_val,
            "Pr(>|t|)": p_val,
            "2.5%": ci_low,
            "97.5%": ci_high,
            "n_window": int(g["window"].nunique()),
            "window_list": ",".join(str(int(x)) for x in sorted(g["window"].unique())),
            "N_min": int(g["N"].min()),
            "N_max": int(g["N"].max()),
            "N_id_min": int(g["N_id"].min()),
            "N_id_max": int(g["N_id"].max()),
            "N_city_min": int(g["N_city"].min()),
            "N_city_max": int(g["N_city"].max()),
        })

    out = pd.DataFrame(rows)
    return out.sort_values(["scenario", "sample", "risk_group", "T"]).reset_index(drop=True)

# =========================================================
# 4. MAIN
# =========================================================

def main():
    health_base = load_health_base()

    county_cont_cache = {}
    detail_rows = []
    scenario_summary = []

    # Original notebook comment normalized for the public code archive.
    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            county_cont_cache[(rp, depth_thr)] = build_county_continuous_risk(rp, depth_thr)

    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            county_cont = county_cont_cache[(rp, depth_thr)]

            for share_cutoff in SHARE_CUTOFF_LIST:
                scen = scenario_tag(rp, depth_thr, share_cutoff)
                print("\n" + "=" * 90)
                print(f"[SCENARIO] {scen}")
                print("=" * 90)

                # =============================================================================
                county_cls = classify_county_risk_by_share_cutoff(county_cont, share_cutoff)
                county_cls["scenario"] = scen

                out_county_parquet = COUNTY_CLASS_DIR / f"county_risk_{scen}.parquet"
                out_county_csv = COUNTY_CLASS_DIR / f"county_risk_{scen}.csv"
                county_cls.to_parquet(out_county_parquet, index=False)
                county_cls.to_csv(out_county_csv, index=False, encoding="utf-8-sig")

                # =============================================================================
                city_cls = aggregate_county_to_city(county_cls, share_cutoff)
                city_cls["scenario"] = scen
                city_cls["rp"] = rp
                city_cls["depth_threshold_m"] = depth_thr

                out_city_parquet = CITY_CLASS_DIR / f"city_risk_{scen}.parquet"
                out_city_csv = CITY_CLASS_DIR / f"city_risk_{scen}.csv"
                city_cls.to_parquet(out_city_parquet, index=False)
                city_cls.to_csv(out_city_csv, index=False, encoding="utf-8-sig")

                print("[INFO] Notebook progress message.")
                print(city_cls["risk_group"].value_counts(dropna=False).sort_index())

                risk_city_small = city_cls[
                    ["city_code", "risk_group", "risk_area_share_city", "top_bottom_sample"]
                ].drop_duplicates("city_code").copy()

                # Original notebook comment normalized for the public code archive.
                df_scen = health_base.merge(
                    risk_city_small,
                    how="left",
                    left_on=CITY_COL,
                    right_on="city_code",
                    validate="m:1"
                )
                df_scen = df_scen[df_scen["risk_group"].isin(RISK_GROUPS)].copy()

                scenario_summary.append({
                    "scenario": scen,
                    "rp": rp,
                    "depth_threshold_m": depth_thr,
                    "share_cutoff": share_cutoff,
                    "n_city_total": int(city_cls["city_code"].nunique()),
                    "n_city_low": int((city_cls["risk_group"] == "low").sum()),
                    "n_city_middle": int((city_cls["risk_group"] == "middle").sum()),
                    "n_city_high": int((city_cls["risk_group"] == "high").sum()),
                    "n_panel_merged": int(len(df_scen)),
                    "n_panel_lowhigh": int(df_scen["risk_group"].isin(["low", "high"]).sum()),
                })

                # =============================================================================
                for sample_name, group_val in SAMPLE_SPECS.items():
                    for risk_group in RISK_GROUPS:
                        sub_base = df_scen.copy()

                        if group_val is not None:
                            sub_base = sub_base[sub_base["urban_group"] == group_val].copy()

                        sub_base = sub_base[sub_base["risk_group"] == risk_group].copy()

                        waves_sub = sub_base.groupby(ID_COL)[YEAR_COL].nunique()
                        keep_ids_sub = waves_sub[waves_sub >= 2].index
                        sub_base = sub_base[sub_base[ID_COL].isin(keep_ids_sub)].copy()

                        print(
                            f"[BASE] {scen} | sample={sample_name:>5s} | risk={risk_group:>4s} | "
                            f"N={len(sub_base):,} | N_id={sub_base[ID_COL].nunique():,} | "
                            f"N_city={sub_base[CITY_COL].nunique():,}"
                        )

                        if len(sub_base) < MIN_NOBS or sub_base[CITY_COL].nunique() < MIN_NCITY:
                            continue

                        for window in WINDOW_LIST:
                            for T in T_LIST:
                                exp_col = f"share_flood_T{T}_{window}y"
                                if exp_col not in sub_base.columns:
                                    continue

                                sub = sub_base.dropna(subset=[exp_col]).copy()
                                if len(sub) < MIN_NOBS or sub[CITY_COL].nunique() < MIN_NCITY:
                                    continue

                                try:
                                    res = fe_reg_twoFE_city_cluster(
                                        sub,
                                        y_col=Y_VAR,
                                        x_cols=[exp_col, "age", "age2"],
                                        fe1=ID_COL,
                                        fe2="prov_year",
                                        cluster_col=CITY_COL,
                                    )

                                    row = res.loc[exp_col].copy()
                                    detail_rows.append({
                                        "scenario": scen,
                                        "rp": rp,
                                        "depth_threshold_m": depth_thr,
                                        "share_cutoff": share_cutoff,
                                        "Y_var": Y_VAR,
                                        "window": window,
                                        "T": T,
                                        "exposure": exp_col,
                                        "sample": sample_name,
                                        "risk_group": risk_group,
                                        "Estimate": float(row["Estimate"]),
                                        "Std. Error": float(row["Std. Error"]),
                                        "t value": float(row["t value"]),
                                        "Pr(>|t|)": float(row["Pr(>|t|)"]),
                                        "2.5%": float(row["2.5%"]),
                                        "97.5%": float(row["97.5%"]),
                                        "N": int(len(sub)),
                                        "N_id": int(sub[ID_COL].nunique()),
                                        "N_year": int(sub[YEAR_COL].nunique()),
                                        "N_city": int(sub[CITY_COL].nunique()),
                                        "mean_depvar": float(sub[Y_VAR].mean()),
                                    })

                                    print(
                                        f"[RUN] {scen} | sample={sample_name:>5s} | risk={risk_group:>4s} | "
                                        f"window={window:>2d} | T={T:>3d} | "
                                        f"beta={float(row['Estimate']): .6f} | p={float(row['Pr(>|t|)']):.4f}"
                                    )

                                except Exception as e:
                                    print(
                                        f"[ERROR] {scen} | sample={sample_name} | risk={risk_group} | "
                                        f"window={window} | T={T} -> {e}"
                                    )
                                    continue

                # Original notebook comment normalized for the public code archive.
                if detail_rows:
                    pd.DataFrame(detail_rows).to_csv(OUT_FE_DETAIL_CSV, index=False, encoding="utf-8-sig")
                    pd.DataFrame(detail_rows).to_parquet(OUT_FE_DETAIL_PARQUET, index=False)

                pd.DataFrame(scenario_summary).to_csv(OUT_SCENARIO_SUMMARY, index=False, encoding="utf-8-sig")

    # =============================================================================
    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(scenario_summary)

    if detail_df.empty:
        print("[INFO] Notebook progress message.")
        return

    detail_df = detail_df.sort_values(
        ["scenario", "sample", "risk_group", "window", "T"]
    ).reset_index(drop=True)
    detail_df.to_csv(OUT_FE_DETAIL_CSV, index=False, encoding="utf-8-sig")
    detail_df.to_parquet(OUT_FE_DETAIL_PARQUET, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    agg_df = aggregate_across_window(detail_df)
    agg_df.to_csv(OUT_FE_AGG_CSV, index=False, encoding="utf-8-sig")
    agg_df.to_parquet(OUT_FE_AGG_PARQUET, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    if not summary_df.empty:
        summary_df = summary_df.sort_values(["rp", "depth_threshold_m", "share_cutoff"]).reset_index(drop=True)
        summary_df.to_csv(OUT_SCENARIO_SUMMARY, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")

    print("\n[ALL DONE] Older health robustness analysis finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 26
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import math

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS
# =========================================================

BASE_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")

EDU_CSV = (
    BASE_DIR
    / "children_education_corrected"
    / "regression_results"
    / "edu_robustness_corrected_9scenarios_all_results.csv"
)

OLDER_CSV = (
    BASE_DIR
    / "older_health_corrected"
    / "regression_results"
    / "older_health_corrected_27scenarios_window_aggregated.csv"
)

OUT_DIR = BASE_DIR / "robustness_summary_two_metrics"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EDU_SUMMARY_CSV = OUT_DIR / "edu_robustness_summary.csv"
EDU_SUMMARY_PARQUET = OUT_DIR / "edu_robustness_summary.parquet"
EDU_FIG_PNG = OUT_DIR / "edu_robustness_heatmap.png"
EDU_FIG_PDF = OUT_DIR / "edu_robustness_heatmap.pdf"

OLDER_SUMMARY_CSV = OUT_DIR / "older_health_robustness_summary.csv"
OLDER_SUMMARY_PARQUET = OUT_DIR / "older_health_robustness_summary.parquet"
OLDER_FIG_PNG = OUT_DIR / "older_health_robustness_heatmap.png"
OLDER_FIG_PDF = OUT_DIR / "older_health_robustness_heatmap.pdf"

# =========================================================
# 1. GLOBAL CONFIG
# =========================================================

T_ORDER = [2, 5, 10, 20, 50, 100]
SAMPLE_ORDER = ["all", "rural", "urban"]
RISK_ORDER = ["low", "high"]

ROW_ORDER = [
    ("all", "low"),
    ("all", "high"),
    ("rural", "low"),
    ("rural", "high"),
    ("urban", "low"),
    ("urban", "high"),
]

ROW_LABELS = [
    "All × Low-risk",
    "All × High-risk",
    "Rural × Low-risk",
    "Rural × High-risk",
    "Urban × Low-risk",
    "Urban × High-risk",
]

# Original notebook comment normalized for the public code archive.
ALPHA = 0.05

# Original notebook comment normalized for the public code archive.
ROBUST_STRONG = 0.70
ROBUST_MODERATE = 0.40

# =========================================================
# 2. SMALL TOOLS
# =========================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def sign_nozero(x, eps=1e-12):
    if pd.isna(x):
        return np.nan
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def classify_robustness(p):
    if pd.isna(p):
        return pd.NA
    if p >= ROBUST_STRONG:
        return "strong"
    elif p >= ROBUST_MODERATE:
        return "moderate"
    else:
        return "weak"


def fmt_beta(x):
    if pd.isna(x):
        return "NA"
    ax = abs(float(x))
    if ax >= 1:
        return f"{x:+.2f}"
    elif ax >= 0.1:
        return f"{x:+.2f}"
    else:
        return f"{x:+.3f}"


def fmt_prop(n, J):
    if pd.isna(n) or pd.isna(J) or J <= 0:
        return "NA"
    return f"{int(n)}/{int(J)}"


# =========================================================
# 3. CORE METRIC
# =========================================================

def compute_two_metrics_summary(
    df: pd.DataFrame,
    sample_col: str,
    risk_col: str,
    T_col: str,
    beta_col: str,
    se_col: str,
    p_col: str,
    outcome_name: str,
) -> pd.DataFrame:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    need_cols = [sample_col, risk_col, T_col, beta_col, se_col, p_col]
    miss = [c for c in need_cols if c not in df.columns]
    if miss:
        raise KeyError(f"{outcome_name} 缺少必要列: {miss}")

    df = df.copy()
    df = safe_numeric(df, [T_col, beta_col, se_col, p_col])

    df = df.dropna(subset=[sample_col, risk_col, T_col, beta_col, se_col, p_col]).copy()
    df = df[df[se_col] > 0].copy()

    rows = []

    for (sample, risk_group, T), g in df.groupby([sample_col, risk_col, T_col], dropna=False):
        g = g.copy()

        beta = g[beta_col].to_numpy(float)
        se = g[se_col].to_numpy(float)
        pval = g[p_col].to_numpy(float)

        var = se ** 2
        var[var <= 0] = np.nan
        ok = np.isfinite(beta) & np.isfinite(var) & (var > 0) & np.isfinite(pval)

        beta = beta[ok]
        se = se[ok]
        pval = pval[ok]

        J = len(beta)
        if J == 0:
            continue

        w = 1.0 / (se ** 2)
        beta_ivw = np.sum(w * beta) / np.sum(w)
        se_ivw = np.sqrt(1.0 / np.sum(w))
        z_ivw = beta_ivw / se_ivw if se_ivw > 0 else np.nan
        p_ivw = 2.0 * (1.0 - norm_cdf(abs(z_ivw))) if np.isfinite(z_ivw) else np.nan
        ci_low = beta_ivw - 1.96 * se_ivw if np.isfinite(se_ivw) else np.nan
        ci_high = beta_ivw + 1.96 * se_ivw if np.isfinite(se_ivw) else np.nan

        main_sign = sign_nozero(beta_ivw)
        signs = np.array([sign_nozero(x) for x in beta], dtype=float)

        sig_same = (pval < ALPHA) & (signs == main_sign) & np.isfinite(signs)
        sig_same_n = int(np.sum(sig_same))
        sig_same_prop = sig_same_n / J if J > 0 else np.nan

        rows.append({
            "outcome": outcome_name,
            "sample_type": str(sample),
            "risk_group": str(risk_group),
            "T": float(T),
            "n_spec": int(J),
            "beta_ivw": float(beta_ivw),
            "se_ivw": float(se_ivw),
            "p_ivw": float(p_ivw) if np.isfinite(p_ivw) else np.nan,
            "ci_low_ivw": float(ci_low) if np.isfinite(ci_low) else np.nan,
            "ci_high_ivw": float(ci_high) if np.isfinite(ci_high) else np.nan,
            "main_sign": int(main_sign) if np.isfinite(main_sign) else pd.NA,
            "sig_same_n": int(sig_same_n),
            "sig_same_prop": float(sig_same_prop),
            "robustness_level": classify_robustness(sig_same_prop),
        })

    out = pd.DataFrame(rows)

    if not out.empty:
        out["T"] = pd.to_numeric(out["T"], errors="coerce")
        out = out.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)

    return out


# =========================================================
# 4. HEATMAP
# =========================================================

def build_heatmap_matrices(summary_df: pd.DataFrame):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    nrow = len(ROW_ORDER)
    ncol = len(T_ORDER)

    beta_mat = np.full((nrow, ncol), np.nan, dtype=float)
    prop_mat = np.full((nrow, ncol), np.nan, dtype=float)
    text_mat = [["" for _ in range(ncol)] for _ in range(nrow)]

    for i, (sample_type, risk_group) in enumerate(ROW_ORDER):
        for j, T in enumerate(T_ORDER):
            sub = summary_df[
                (summary_df["sample_type"] == sample_type) &
                (summary_df["risk_group"] == risk_group) &
                (np.isclose(summary_df["T"], T))
            ].copy()

            if sub.empty:
                text_mat[i][j] = "NA"
                continue

            row = sub.iloc[0]
            beta_ivw = row["beta_ivw"]
            sig_same_n = row["sig_same_n"]
            n_spec = row["n_spec"]
            prop = row["sig_same_prop"]

            beta_mat[i, j] = beta_ivw
            prop_mat[i, j] = prop

            text_mat[i][j] = (
                f"{fmt_prop(sig_same_n, n_spec)}\n"
                f"β={fmt_beta(beta_ivw)}"
            )

    return beta_mat, prop_mat, text_mat


def plot_dual_heatmap(summary_df: pd.DataFrame, outcome_name: str, out_png: Path, out_pdf: Path):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    beta_mat, prop_mat, text_mat = build_heatmap_matrices(summary_df)

    # Original notebook comment normalized for the public code archive.
    vals = beta_mat[np.isfinite(beta_mat)]
    if vals.size == 0:
        vabs = 1.0
    else:
        vabs = np.nanmax(np.abs(vals))
        if not np.isfinite(vabs) or vabs == 0:
            vabs = 1.0

    norm = TwoSlopeNorm(vmin=-vabs, vcenter=0.0, vmax=vabs)

    fig, ax = plt.subplots(figsize=(12.5, 8.8))

    im = ax.imshow(beta_mat, cmap="RdBu_r", norm=norm, aspect="auto")

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(np.arange(len(T_ORDER)))
    ax.set_xticklabels([str(t) for t in T_ORDER], fontsize=11)

    ax.set_yticks(np.arange(len(ROW_LABELS)))
    ax.set_yticklabels(ROW_LABELS, fontsize=11)

    ax.set_xlabel("Flood return period T", fontsize=12)
    ax.set_ylabel("Sample × risk group", fontsize=12)

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(np.arange(-0.5, len(T_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROW_LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Original notebook comment normalized for the public code archive.
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            val = beta_mat[i, j]
            txt = text_mat[i][j]

            # Original notebook comment normalized for the public code archive.
            if np.isfinite(val) and abs(val) > 0.55 * vabs:
                text_color = "white"
            else:
                text_color = "black"

            ax.text(
                j, i, txt,
                ha="center", va="center",
                fontsize=10.5,
                color=text_color
            )

    # Original notebook comment normalized for the public code archive.
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Inverse-variance-weighted pooled effect", fontsize=12)

    # Original notebook comment normalized for the public code archive.
    title_map = {
        "education": "Children's education robustness summary",
        "older_health": "Older adults' health robustness summary",
    }

    fig.suptitle(
        title_map.get(outcome_name, outcome_name),
        fontsize=16,
        y=0.97
    )

    note = (
        "Cell fill = inverse-variance-weighted pooled effect; "
        "cell text = significant-and-same-sign count / total specifications + pooled effect.\n"
        f"Significant-and-same-sign means p < {ALPHA:.2f} and same sign as pooled effect."
    )

    fig.text(0.5, 0.02, note, ha="center", fontsize=10)

    plt.tight_layout(rect=[0.02, 0.06, 0.98, 0.94])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[SAVED] {out_png}")
    print(f"[SAVED] {out_pdf}")


# =========================================================
# 5. EDUCATION PIPELINE
# =========================================================

def run_education():
    print(f"[READ] Education result file: {EDU_CSV}")
    edu = pd.read_csv(EDU_CSV)

    summary = compute_two_metrics_summary(
        df=edu,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        p_col="PValue",
        outcome_name="education",
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(EDU_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(EDU_SUMMARY_PARQUET, index=False)

    print(f"[DONE] Education summary saved: {EDU_SUMMARY_CSV}")
    print(f"[DONE] Education summary saved: {EDU_SUMMARY_PARQUET}")
    print(summary.head())

    plot_dual_heatmap(
        summary_df=summary,
        outcome_name="education",
        out_png=EDU_FIG_PNG,
        out_pdf=EDU_FIG_PDF,
    )


# =========================================================
# 6. OLDER HEALTH PIPELINE
# =========================================================

def run_older_health():
    print(f"[READ] Older-health result file: {OLDER_CSV}")
    older = pd.read_csv(OLDER_CSV)

    # Original notebook comment normalized for the public code archive.
    older = older.rename(columns={
        "sample": "sample_type",
        "Std. Error": "StdError",
        "Pr(>|t|)": "PValue",
        "2.5%": "CI_low",
        "97.5%": "CI_high",
    })

    summary = compute_two_metrics_summary(
        df=older,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        p_col="PValue",
        outcome_name="older_health",
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(OLDER_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(OLDER_SUMMARY_PARQUET, index=False)

    print(f"[DONE] Older-health summary saved: {OLDER_SUMMARY_CSV}")
    print(f"[DONE] Older-health summary saved: {OLDER_SUMMARY_PARQUET}")
    print(summary.head())

    plot_dual_heatmap(
        summary_df=summary,
        outcome_name="older_health",
        out_png=OLDER_FIG_PNG,
        out_pdf=OLDER_FIG_PDF,
    )


# =========================================================
# 7. MAIN
# =========================================================

def main():
    print("=" * 90)
    print("[STEP] Education robustness summary")
    print("=" * 90)
    run_education()

    print("\n" + "=" * 90)
    print("[STEP] Older-health robustness summary")
    print("=" * 90)
    run_older_health()

    print("\n[ALL DONE]")
    print(f"[OUT DIR] {OUT_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 29
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import math

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS
# =========================================================

BASE_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")

EDU_CSV = (
    BASE_DIR
    / "children_education_corrected"
    / "regression_results"
    / "edu_robustness_corrected_9scenarios_all_results.csv"
)

OLDER_CSV = (
    BASE_DIR
    / "older_health_corrected"
    / "regression_results"
    / "older_health_corrected_27scenarios_window_aggregated.csv"
)

OUT_DIR = BASE_DIR / "robustness_summary_same_sign_close"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EDU_SUMMARY_CSV = OUT_DIR / "edu_same_sign_close_summary.csv"
EDU_SUMMARY_PARQUET = OUT_DIR / "edu_same_sign_close_summary.parquet"
EDU_FIG_PNG = OUT_DIR / "edu_same_sign_close_heatmap.png"
EDU_FIG_PDF = OUT_DIR / "edu_same_sign_close_heatmap.pdf"

OLDER_SUMMARY_CSV = OUT_DIR / "older_same_sign_close_summary.csv"
OLDER_SUMMARY_PARQUET = OUT_DIR / "older_same_sign_close_summary.parquet"
OLDER_FIG_PNG = OUT_DIR / "older_same_sign_close_heatmap.png"
OLDER_FIG_PDF = OUT_DIR / "older_same_sign_close_heatmap.pdf"

# =========================================================
# 1. GLOBAL CONFIG
# =========================================================

T_ORDER = [2, 5, 10, 20, 50, 100]

ROW_ORDER = [
    ("all", "low"),
    ("all", "high"),
    ("rural", "low"),
    ("rural", "high"),
    ("urban", "low"),
    ("urban", "high"),
]

ROW_LABELS = [
    "All × Low-risk",
    "All × High-risk",
    "Rural × Low-risk",
    "Rural × High-risk",
    "Urban × Low-risk",
    "Urban × High-risk",
]

# Original notebook comment normalized for the public code archive.
REL_TOL = 0.30

# Original notebook comment normalized for the public code archive.
SIGN_EPS = 1e-12

# =========================================================
# 2. SMALL TOOLS
# =========================================================

def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def sign_nozero(x, eps=SIGN_EPS):
    if pd.isna(x):
        return np.nan
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def fmt_beta(x):
    if pd.isna(x):
        return "NA"
    ax = abs(float(x))
    if ax >= 1:
        return f"{x:+.2f}"
    if ax >= 0.1:
        return f"{x:+.2f}"
    return f"{x:+.3f}"


def fmt_count(n, J):
    if pd.isna(n) or pd.isna(J) or J <= 0:
        return "NA"
    return f"{int(n)}/{int(J)}"


def classify_strength(prop):
    if pd.isna(prop):
        return pd.NA
    if prop >= 0.70:
        return "strong"
    elif prop >= 0.40:
        return "moderate"
    else:
        return "weak"


# =========================================================
# 3. CORE SUMMARY
# =========================================================

def compute_same_sign_close_summary(
    df: pd.DataFrame,
    sample_col: str,
    risk_col: str,
    T_col: str,
    beta_col: str,
    se_col: str,
    outcome_name: str,
) -> pd.DataFrame:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    need = [sample_col, risk_col, T_col, beta_col, se_col]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"{outcome_name} 缺少必要列: {miss}")

    df = df.copy()
    df = safe_numeric(df, [T_col, beta_col, se_col])
    df = df.dropna(subset=[sample_col, risk_col, T_col, beta_col, se_col]).copy()
    df = df[df[se_col] > 0].copy()

    # outcome-level floor
    abs_beta_all = df[beta_col].abs()
    abs_beta_all = abs_beta_all[np.isfinite(abs_beta_all) & (abs_beta_all > 0)]
    if len(abs_beta_all) == 0:
        floor = 1e-6
    else:
        floor = float(np.quantile(abs_beta_all, 0.10))
        floor = max(floor, 1e-6)

    rows = []

    for (sample, risk_group, T), g in df.groupby([sample_col, risk_col, T_col], dropna=False):
        g = g.copy()

        beta = g[beta_col].to_numpy(float)
        se = g[se_col].to_numpy(float)

        ok = np.isfinite(beta) & np.isfinite(se) & (se > 0)
        beta = beta[ok]
        se = se[ok]

        J = len(beta)
        if J == 0:
            continue

        # IVW pooled effect
        w = 1.0 / (se ** 2)
        beta_ivw = float(np.sum(w * beta) / np.sum(w))
        se_ivw = float(np.sqrt(1.0 / np.sum(w)))
        ci_low = beta_ivw - 1.96 * se_ivw
        ci_high = beta_ivw + 1.96 * se_ivw

        # same sign
        main_sign = sign_nozero(beta_ivw)
        beta_sign = np.array([sign_nozero(x) for x in beta], dtype=float)

        if main_sign == 0:
            same_sign = np.zeros(J, dtype=bool)
        else:
            same_sign = beta_sign == main_sign

        same_sign_n = int(np.sum(same_sign))
        same_sign_prop = same_sign_n / J

        # close
        tol = REL_TOL * max(abs(beta_ivw), floor)
        close = np.abs(beta - beta_ivw) <= tol
        close_n = int(np.sum(close))
        close_prop = close_n / J

        # same-sign AND close
        same_sign_close = same_sign & close
        same_sign_close_n = int(np.sum(same_sign_close))
        same_sign_close_prop = same_sign_close_n / J

        rows.append({
            "outcome": outcome_name,
            "sample_type": str(sample),
            "risk_group": str(risk_group),
            "T": float(T),
            "n_spec": int(J),
            "beta_ivw": beta_ivw,
            "se_ivw": se_ivw,
            "ci_low_ivw": ci_low,
            "ci_high_ivw": ci_high,
            "scale_floor": floor,
            "close_tolerance_abs": tol,
            "main_sign": int(main_sign),
            "same_sign_n": same_sign_n,
            "same_sign_prop": same_sign_prop,
            "close_n": close_n,
            "close_prop": close_prop,
            "same_sign_close_n": same_sign_close_n,
            "same_sign_close_prop": same_sign_close_prop,
            "same_sign_strength": classify_strength(same_sign_prop),
            "close_strength": classify_strength(close_prop),
            "same_sign_close_strength": classify_strength(same_sign_close_prop),
        })

    out = pd.DataFrame(rows)
    if not out.empty:
        out["T"] = pd.to_numeric(out["T"], errors="coerce")
        out = out.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)

    return out


# =========================================================
# 4. HEATMAP
# =========================================================

def build_heatmap_matrices(summary_df: pd.DataFrame):
    nrow = len(ROW_ORDER)
    ncol = len(T_ORDER)

    beta_mat = np.full((nrow, ncol), np.nan, dtype=float)
    text_mat = [["" for _ in range(ncol)] for _ in range(nrow)]

    for i, (sample_type, risk_group) in enumerate(ROW_ORDER):
        for j, T in enumerate(T_ORDER):
            sub = summary_df[
                (summary_df["sample_type"] == sample_type) &
                (summary_df["risk_group"] == risk_group) &
                (np.isclose(summary_df["T"], T))
            ].copy()

            if sub.empty:
                text_mat[i][j] = "NA"
                continue

            row = sub.iloc[0]
            beta_ivw = row["beta_ivw"]
            same_sign_n = row["same_sign_n"]
            close_n = row["close_n"]
            n_spec = row["n_spec"]

            beta_mat[i, j] = beta_ivw
            text_mat[i][j] = (
                f"sign {fmt_count(same_sign_n, n_spec)}\n"
                f"close {fmt_count(close_n, n_spec)}\n"
                f"β={fmt_beta(beta_ivw)}"
            )

    return beta_mat, text_mat


def plot_same_sign_close_heatmap(summary_df: pd.DataFrame, title: str, out_png: Path, out_pdf: Path):
    beta_mat, text_mat = build_heatmap_matrices(summary_df)

    vals = beta_mat[np.isfinite(beta_mat)]
    if vals.size == 0:
        vabs = 1.0
    else:
        vabs = float(np.nanmax(np.abs(vals)))
        if not np.isfinite(vabs) or vabs == 0:
            vabs = 1.0

    norm = TwoSlopeNorm(vmin=-vabs, vcenter=0.0, vmax=vabs)

    fig, ax = plt.subplots(figsize=(12.8, 8.8))
    im = ax.imshow(beta_mat, cmap="RdBu_r", norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(T_ORDER)))
    ax.set_xticklabels([str(t) for t in T_ORDER], fontsize=11)

    ax.set_yticks(np.arange(len(ROW_LABELS)))
    ax.set_yticklabels(ROW_LABELS, fontsize=11)

    ax.set_xlabel("Flood return period T", fontsize=12)
    ax.set_ylabel("Sample × risk group", fontsize=12)

    ax.set_xticks(np.arange(-0.5, len(T_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROW_LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            val = beta_mat[i, j]
            txt = text_mat[i][j]

            if np.isfinite(val) and abs(val) > 0.55 * vabs:
                text_color = "white"
            else:
                text_color = "black"

            ax.text(
                j, i, txt,
                ha="center", va="center",
                fontsize=10.3,
                color=text_color
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Inverse-variance-weighted pooled effect", fontsize=12)

    fig.suptitle(title, fontsize=16, y=0.97)

    note = (
        f"Cell fill = IVW pooled effect; text = same-sign count / total + close count / total + pooled effect.\n"
        f"Close is defined as |β_j - β_IVW| ≤ {REL_TOL:.0%} × max(|β_IVW|, floor), "
        "where floor is the 10th percentile of non-zero absolute effects within each outcome."
    )
    fig.text(0.5, 0.02, note, ha="center", fontsize=10)

    plt.tight_layout(rect=[0.02, 0.06, 0.98, 0.94])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[SAVED] {out_png}")
    print(f"[SAVED] {out_pdf}")


# =========================================================
# 5. EDUCATION
# =========================================================

def run_education():
    print(f"[READ] {EDU_CSV}")
    df = pd.read_csv(EDU_CSV)

    summary = compute_same_sign_close_summary(
        df=df,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        outcome_name="education",
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(EDU_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(EDU_SUMMARY_PARQUET, index=False)

    print(f"[DONE] {EDU_SUMMARY_CSV}")
    print(f"[DONE] {EDU_SUMMARY_PARQUET}")
    print(summary.head())

    plot_same_sign_close_heatmap(
        summary_df=summary,
        title="Children's education robustness summary",
        out_png=EDU_FIG_PNG,
        out_pdf=EDU_FIG_PDF,
    )


# =========================================================
# 6. OLDER HEALTH
# =========================================================

def run_older():
    print(f"[READ] {OLDER_CSV}")
    df = pd.read_csv(OLDER_CSV)

    # Original notebook comment normalized for the public code archive.
    df = df.rename(columns={
        "sample": "sample_type",
        "Std. Error": "StdError",
    })

    summary = compute_same_sign_close_summary(
        df=df,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        outcome_name="older_health",
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(OLDER_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(OLDER_SUMMARY_PARQUET, index=False)

    print(f"[DONE] {OLDER_SUMMARY_CSV}")
    print(f"[DONE] {OLDER_SUMMARY_PARQUET}")
    print(summary.head())

    plot_same_sign_close_heatmap(
        summary_df=summary,
        title="Older adults' health robustness summary",
        out_png=OLDER_FIG_PNG,
        out_pdf=OLDER_FIG_PDF,
    )


# =========================================================
# 7. MAIN
# =========================================================

def main():
    print("=" * 90)
    print("[STEP] Education")
    print("=" * 90)
    run_education()

    print("\n" + "=" * 90)
    print("[STEP] Older health")
    print("=" * 90)
    run_older()

    print("\n[ALL DONE]")
    print(f"[OUT DIR] {OUT_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 32
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import math

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS
# =========================================================

BASE_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")

EDU_CSV = (
    BASE_DIR
    / "children_education_corrected"
    / "regression_results"
    / "edu_robustness_corrected_9scenarios_all_results.csv"
)

OLDER_CSV = (
    BASE_DIR
    / "older_health_corrected"
    / "regression_results"
    / "older_health_corrected_27scenarios_window_aggregated.csv"
)

OUT_DIR = BASE_DIR / "robustness_summary_sig_subset_strict"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EDU_SUMMARY_CSV = OUT_DIR / "edu_sig_subset_summary_strict.csv"
EDU_SUMMARY_PARQUET = OUT_DIR / "edu_sig_subset_summary_strict.parquet"
EDU_FIG_PNG = OUT_DIR / "edu_sig_subset_heatmap_strict.png"
EDU_FIG_PDF = OUT_DIR / "edu_sig_subset_heatmap_strict.pdf"

OLDER_SUMMARY_CSV = OUT_DIR / "older_sig_subset_summary_strict.csv"
OLDER_SUMMARY_PARQUET = OUT_DIR / "older_sig_subset_summary_strict.parquet"
OLDER_FIG_PNG = OUT_DIR / "older_sig_subset_heatmap_strict.png"
OLDER_FIG_PDF = OUT_DIR / "older_sig_subset_heatmap_strict.pdf"

# =========================================================
# 1. GLOBAL CONFIG
# =========================================================

ALPHA = 0.05
REL_TOL = 0.30
SIGN_EPS = 1e-12

# Original notebook comment normalized for the public code archive.
MIN_SIG_EDU = 3       # Original notebook comment normalized for the public code archive.
MIN_SIG_OLDER = 9     # Original notebook comment normalized for the public code archive.

T_ORDER = [2, 5, 10, 20, 50, 100]

ROW_ORDER = [
    ("all", "low"),
    ("all", "high"),
    ("rural", "low"),
    ("rural", "high"),
    ("urban", "low"),
    ("urban", "high"),
]

ROW_LABELS = [
    "All × Low-risk",
    "All × High-risk",
    "Rural × Low-risk",
    "Rural × High-risk",
    "Urban × Low-risk",
    "Urban × High-risk",
]

# =========================================================
# 2. SMALL TOOLS
# =========================================================

def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def sign_nozero(x, eps=SIGN_EPS):
    if pd.isna(x):
        return np.nan
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def fmt_beta(x):
    if pd.isna(x):
        return "NA"
    ax = abs(float(x))
    if ax >= 1:
        return f"{x:+.2f}"
    if ax >= 0.1:
        return f"{x:+.2f}"
    return f"{x:+.3f}"


def fmt_count(n, N):
    if pd.isna(n) or pd.isna(N) or N <= 0:
        return "NA"
    return f"{int(n)}/{int(N)}"


def classify_strength(prop):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(prop):
        return pd.NA
    if prop >= 0.80:
        return "strong"
    elif prop >= 0.60:
        return "moderate"
    else:
        return "weak"


# =========================================================
# 3. CORE SUMMARY
# =========================================================

def compute_sig_subset_summary_strict(
    df: pd.DataFrame,
    sample_col: str,
    risk_col: str,
    T_col: str,
    beta_col: str,
    se_col: str,
    p_col: str,
    outcome_name: str,
    min_sig_required: int,
) -> pd.DataFrame:
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    need = [sample_col, risk_col, T_col, beta_col, se_col, p_col]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"{outcome_name} 缺少必要列: {miss}")

    df = df.copy()
    df = safe_numeric(df, [T_col, beta_col, se_col, p_col])
    df = df.dropna(subset=[sample_col, risk_col, T_col, beta_col, se_col, p_col]).copy()
    df = df[df[se_col] > 0].copy()

    # Fixed-effects regression helper.
    abs_beta_all = df[beta_col].abs()
    abs_beta_all = abs_beta_all[np.isfinite(abs_beta_all) & (abs_beta_all > 0)]
    if len(abs_beta_all) == 0:
        floor = 1e-6
    else:
        floor = float(np.quantile(abs_beta_all, 0.10))
        floor = max(floor, 1e-6)

    rows = []

    for (sample, risk_group, T), g in df.groupby([sample_col, risk_col, T_col], dropna=False):
        g = g.copy()

        beta = g[beta_col].to_numpy(float)
        se = g[se_col].to_numpy(float)
        pval = g[p_col].to_numpy(float)

        ok = np.isfinite(beta) & np.isfinite(se) & (se > 0) & np.isfinite(pval)
        beta = beta[ok]
        se = se[ok]
        pval = pval[ok]

        n_spec = len(beta)
        if n_spec == 0:
            continue

        sig_mask = (pval < ALPHA)
        n_sig = int(np.sum(sig_mask))
        sig_coverage = n_sig / n_spec
        signal_status = "sufficient-signal" if n_sig >= min_sig_required else "insufficient-signal"

        # Original notebook comment normalized for the public code archive.
        beta_ivw_sig = np.nan
        se_ivw_sig = np.nan
        p_ivw_sig = np.nan
        ci_low_ivw_sig = np.nan
        ci_high_ivw_sig = np.nan
        tol_abs = np.nan

        sign_same_sig_n = pd.NA
        sign_same_sig_prop = np.nan
        close_sig_n = pd.NA
        close_sig_prop = np.nan
        sign_close_sig_n = pd.NA
        sign_close_sig_prop = np.nan

        # Original notebook comment normalized for the public code archive.
        if n_sig >= min_sig_required:
            beta_sig = beta[sig_mask]
            se_sig = se[sig_mask]

            # Fixed-effects regression helper.
            w = 1.0 / (se_sig ** 2)
            beta_ivw_sig = float(np.sum(w * beta_sig) / np.sum(w))
            se_ivw_sig = float(np.sqrt(1.0 / np.sum(w)))

            z_ivw_sig = beta_ivw_sig / se_ivw_sig if se_ivw_sig > 0 else np.nan
            p_ivw_sig = 2.0 * (1.0 - norm_cdf(abs(z_ivw_sig))) if np.isfinite(z_ivw_sig) else np.nan
            ci_low_ivw_sig = beta_ivw_sig - 1.96 * se_ivw_sig if np.isfinite(se_ivw_sig) else np.nan
            ci_high_ivw_sig = beta_ivw_sig + 1.96 * se_ivw_sig if np.isfinite(se_ivw_sig) else np.nan

            # Original notebook comment normalized for the public code archive.
            pooled_sign = sign_nozero(beta_ivw_sig)
            sig_signs = np.array([sign_nozero(x) for x in beta_sig], dtype=float)

            if pooled_sign == 0:
                sign_same = np.zeros(n_sig, dtype=bool)
            else:
                sign_same = (sig_signs == pooled_sign)

            sign_same_sig_n = int(np.sum(sign_same))
            sign_same_sig_prop = sign_same_sig_n / n_sig

            # Original notebook comment normalized for the public code archive.
            tol_abs = REL_TOL * max(abs(beta_ivw_sig), floor)
            close = np.abs(beta_sig - beta_ivw_sig) <= tol_abs
            close_sig_n = int(np.sum(close))
            close_sig_prop = close_sig_n / n_sig

            sign_close = sign_same & close
            sign_close_sig_n = int(np.sum(sign_close))
            sign_close_sig_prop = sign_close_sig_n / n_sig

        rows.append({
            "outcome": outcome_name,
            "sample_type": str(sample),
            "risk_group": str(risk_group),
            "T": float(T),

            "n_spec": int(n_spec),
            "n_sig": int(n_sig),
            "sig_coverage": float(sig_coverage),
            "min_sig_required": int(min_sig_required),
            "signal_status": signal_status,

            "beta_ivw_sig": beta_ivw_sig,
            "se_ivw_sig": se_ivw_sig,
            "p_ivw_sig": p_ivw_sig,
            "ci_low_ivw_sig": ci_low_ivw_sig,
            "ci_high_ivw_sig": ci_high_ivw_sig,

            "scale_floor": floor,
            "close_tolerance_abs": tol_abs,

            "sign_same_sig_n": sign_same_sig_n,
            "sign_same_sig_prop": sign_same_sig_prop,

            "close_sig_n": close_sig_n,
            "close_sig_prop": close_sig_prop,

            "sign_close_sig_n": sign_close_sig_n,
            "sign_close_sig_prop": sign_close_sig_prop,

            "sign_strength": classify_strength(sign_same_sig_prop),
            "close_strength": classify_strength(close_sig_prop),
            "sign_close_strength": classify_strength(sign_close_sig_prop),
        })

    out = pd.DataFrame(rows)
    if not out.empty:
        out["T"] = pd.to_numeric(out["T"], errors="coerce")
        out = out.sort_values(["sample_type", "risk_group", "T"]).reset_index(drop=True)

    return out


# =========================================================
# 4. HEATMAP
# =========================================================

def build_heatmap_matrices(summary_df: pd.DataFrame):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    nrow = len(ROW_ORDER)
    ncol = len(T_ORDER)

    beta_mat = np.full((nrow, ncol), np.nan, dtype=float)
    text_mat = [["" for _ in range(ncol)] for _ in range(nrow)]
    sufficient_mat = np.zeros((nrow, ncol), dtype=bool)

    for i, (sample_type, risk_group) in enumerate(ROW_ORDER):
        for j, T in enumerate(T_ORDER):
            sub = summary_df[
                (summary_df["sample_type"] == sample_type) &
                (summary_df["risk_group"] == risk_group) &
                (np.isclose(summary_df["T"], T))
            ].copy()

            if sub.empty:
                text_mat[i][j] = "NA"
                continue

            row = sub.iloc[0]

            n_spec = row["n_spec"]
            n_sig = row["n_sig"]
            beta_ivw_sig = row["beta_ivw_sig"]
            sign_same_sig_n = row["sign_same_sig_n"]
            close_sig_n = row["close_sig_n"]
            signal_status = row["signal_status"]

            sufficient_mat[i, j] = (signal_status == "sufficient-signal")

            if signal_status == "sufficient-signal" and pd.notna(beta_ivw_sig):
                beta_mat[i, j] = float(beta_ivw_sig)

            if signal_status != "sufficient-signal":
                text_mat[i][j] = (
                    f"sig {fmt_count(n_sig, n_spec)}\n"
                    f"insufficient\n"
                    f"β=NA"
                )
            else:
                text_mat[i][j] = (
                    f"sig {fmt_count(n_sig, n_spec)}\n"
                    f"sign {fmt_count(sign_same_sig_n, n_sig)}\n"
                    f"close {fmt_count(close_sig_n, n_sig)}\n"
                    f"β={fmt_beta(beta_ivw_sig)}"
                )

    return beta_mat, text_mat, sufficient_mat


def plot_sig_subset_heatmap(summary_df: pd.DataFrame, title: str, out_png: Path, out_pdf: Path):
    beta_mat, text_mat, sufficient_mat = build_heatmap_matrices(summary_df)

    vals = beta_mat[np.isfinite(beta_mat)]
    if vals.size == 0:
        vabs = 1.0
    else:
        vabs = float(np.nanmax(np.abs(vals)))
        if not np.isfinite(vabs) or vabs == 0:
            vabs = 1.0

    norm = TwoSlopeNorm(vmin=-vabs, vcenter=0.0, vmax=vabs)

    fig, ax = plt.subplots(figsize=(13.0, 9.0))
    im = ax.imshow(beta_mat, cmap="RdBu_r", norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(T_ORDER)))
    ax.set_xticklabels([str(t) for t in T_ORDER], fontsize=11)

    ax.set_yticks(np.arange(len(ROW_LABELS)))
    ax.set_yticklabels(ROW_LABELS, fontsize=11)

    ax.set_xlabel("Flood return period T", fontsize=12)
    ax.set_ylabel("Sample × risk group", fontsize=12)

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(np.arange(-0.5, len(T_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROW_LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Original notebook comment normalized for the public code archive.
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            if not sufficient_mat[i, j]:
                rect = plt.Rectangle(
                    (j - 0.5, i - 0.5), 1, 1,
                    fill=False,
                    edgecolor="gray",
                    linewidth=2.0,
                    linestyle="--",
                )
                ax.add_patch(rect)

    # Original notebook comment normalized for the public code archive.
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            val = beta_mat[i, j]
            txt = text_mat[i][j]

            if np.isfinite(val) and abs(val) > 0.55 * vabs:
                text_color = "white"
            else:
                text_color = "black"

            ax.text(
                j, i, txt,
                ha="center", va="center",
                fontsize=10.0,
                color=text_color
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("IVW pooled effect within significant subset", fontsize=12)

    fig.suptitle(title, fontsize=16, y=0.97)

    note = (
        f"Cell fill = IVW pooled effect computed only when the number of significant specifications reaches the preset threshold "
        f"(education: ≥{MIN_SIG_EDU}; older health: ≥{MIN_SIG_OLDER}). "
        f"Cell text = significant count / total + same-sign count / significant + close count / significant + pooled effect.\n"
        f"Close is defined as |β_j - β_IVW,sig| ≤ {REL_TOL:.0%} × max(|β_IVW,sig|, floor). "
        "Grey dashed border = insufficient signal coverage; in those cells, no cross-specification conditional analysis is performed."
    )

    fig.text(0.5, 0.02, note, ha="center", fontsize=9.6)

    plt.tight_layout(rect=[0.02, 0.06, 0.98, 0.94])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[SAVED] {out_png}")
    print(f"[SAVED] {out_pdf}")


# =========================================================
# 5. EDUCATION
# =========================================================

def run_education():
    print(f"[READ] {EDU_CSV}")
    df = pd.read_csv(EDU_CSV)

    summary = compute_sig_subset_summary_strict(
        df=df,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        p_col="PValue",
        outcome_name="education",
        min_sig_required=MIN_SIG_EDU,
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(EDU_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(EDU_SUMMARY_PARQUET, index=False)

    print(f"[DONE] {EDU_SUMMARY_CSV}")
    print(f"[DONE] {EDU_SUMMARY_PARQUET}")
    print(summary.head())

    plot_sig_subset_heatmap(
        summary_df=summary,
        title="Children's education: conditional robustness within significant specifications (strict)",
        out_png=EDU_FIG_PNG,
        out_pdf=EDU_FIG_PDF,
    )


# =========================================================
# 6. OLDER HEALTH
# =========================================================

def run_older():
    print(f"[READ] {OLDER_CSV}")
    df = pd.read_csv(OLDER_CSV)

    # Original notebook comment normalized for the public code archive.
    df = df.rename(columns={
        "sample": "sample_type",
        "Std. Error": "StdError",
        "Pr(>|t|)": "PValue",
    })

    summary = compute_sig_subset_summary_strict(
        df=df,
        sample_col="sample_type",
        risk_col="risk_group",
        T_col="T",
        beta_col="Estimate",
        se_col="StdError",
        p_col="PValue",
        outcome_name="older_health",
        min_sig_required=MIN_SIG_OLDER,
    )

    if summary.empty:
        print("[INFO] Notebook progress message.")
        return

    summary.to_csv(OLDER_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    summary.to_parquet(OLDER_SUMMARY_PARQUET, index=False)

    print(f"[DONE] {OLDER_SUMMARY_CSV}")
    print(f"[DONE] {OLDER_SUMMARY_PARQUET}")
    print(summary.head())

    plot_sig_subset_heatmap(
        summary_df=summary,
        title="Older adults' health: conditional robustness within significant specifications (strict)",
        out_png=OLDER_FIG_PNG,
        out_pdf=OLDER_FIG_PDF,
    )


# =========================================================
# 7. MAIN
# =========================================================

def main():
    print("=" * 90)
    print("[STEP] Education")
    print("=" * 90)
    run_education()

    print("\n" + "=" * 90)
    print("[STEP] Older health")
    print("=" * 90)
    run_older()

    print("\n[ALL DONE]")
    print(f"[OUT DIR] {OUT_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 34
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS
# =========================================================

BASE_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")
IN_DIR = BASE_DIR / "robustness_summary_sig_subset_strict"
OUT_DIR = IN_DIR / "replot"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EDU_SUMMARY_CSV = IN_DIR / "edu_sig_subset_summary_strict.csv"
OLDER_SUMMARY_CSV = IN_DIR / "older_sig_subset_summary_strict.csv"

EDU_OUT_PNG = OUT_DIR / "edu_sig_subset_heatmap_strict_replot.png"
EDU_OUT_PDF = OUT_DIR / "edu_sig_subset_heatmap_strict_replot.pdf"

OLDER_OUT_PNG = OUT_DIR / "older_sig_subset_heatmap_strict_replot.png"
OLDER_OUT_PDF = OUT_DIR / "older_sig_subset_heatmap_strict_replot.pdf"

# =========================================================
# 1. GLOBAL CONFIG
# =========================================================

MIN_SIG_EDU = 3
MIN_SIG_OLDER = 9
REL_TOL = 0.30

T_ORDER = [2, 5, 10, 20, 50, 100]

ROW_ORDER = [
    ("all", "low"),
    ("all", "high"),
    ("rural", "low"),
    ("rural", "high"),
    ("urban", "low"),
    ("urban", "high"),
]

ROW_LABELS = [
    "All × Low-risk",
    "All × High-risk",
    "Rural × Low-risk",
    "Rural × High-risk",
    "Urban × Low-risk",
    "Urban × High-risk",
]

# =========================================================
# 2. SMALL TOOLS
# =========================================================

def fmt_beta(x):
    if pd.isna(x):
        return "NA"
    x = float(x)
    ax = abs(x)
    if ax >= 1:
        return f"{x:+.2f}"
    elif ax >= 0.1:
        return f"{x:+.2f}"
    else:
        return f"{x:+.3f}"


def fmt_count(n, N):
    if pd.isna(n) or pd.isna(N) or N <= 0:
        return "NA"
    return f"{int(n)}/{int(N)}"


def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# =========================================================
# 3. BUILD HEATMAP MATRICES
# =========================================================

def build_heatmap_matrices(summary_df: pd.DataFrame):
    """Archived notebook note for 03_children_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    nrow = len(ROW_ORDER)
    ncol = len(T_ORDER)

    beta_mat = np.full((nrow, ncol), np.nan, dtype=float)
    text_mat = [["" for _ in range(ncol)] for _ in range(nrow)]
    sufficient_mat = np.zeros((nrow, ncol), dtype=bool)

    for i, (sample_type, risk_group) in enumerate(ROW_ORDER):
        for j, T in enumerate(T_ORDER):
            sub = summary_df[
                (summary_df["sample_type"] == sample_type) &
                (summary_df["risk_group"] == risk_group) &
                (np.isclose(summary_df["T"], T))
            ].copy()

            if sub.empty:
                text_mat[i][j] = "NA"
                continue

            row = sub.iloc[0]

            n_spec = row["n_spec"]
            n_sig = row["n_sig"]
            beta_ivw_sig = row["beta_ivw_sig"]
            sign_same_sig_n = row["sign_same_sig_n"]
            close_sig_n = row["close_sig_n"]
            signal_status = row["signal_status"]

            sufficient_mat[i, j] = (signal_status == "sufficient-signal")

            if signal_status == "sufficient-signal" and pd.notna(beta_ivw_sig):
                beta_mat[i, j] = float(beta_ivw_sig)

            if signal_status != "sufficient-signal":
                text_mat[i][j] = (
                    f"sig {fmt_count(n_sig, n_spec)}\n"
                    f"insufficient\n"
                    f"β=NA"
                )
            else:
                text_mat[i][j] = (
                    f"sig {fmt_count(n_sig, n_spec)}\n"
                    f"sign {fmt_count(sign_same_sig_n, n_sig)}\n"
                    f"close {fmt_count(close_sig_n, n_sig)}\n"
                    f"β={fmt_beta(beta_ivw_sig)}"
                )

    return beta_mat, text_mat, sufficient_mat


# =========================================================
# 4. PLOT
# =========================================================

def plot_sig_subset_heatmap(
    summary_df: pd.DataFrame,
    title: str,
    out_png: Path,
    out_pdf: Path,
    min_sig_required: int,
):
    beta_mat, text_mat, sufficient_mat = build_heatmap_matrices(summary_df)

    vals = beta_mat[np.isfinite(beta_mat)]
    if vals.size == 0:
        vabs = 1.0
    else:
        vabs = float(np.nanmax(np.abs(vals)))
        if (not np.isfinite(vabs)) or (vabs == 0):
            vabs = 1.0

    norm = TwoSlopeNorm(vmin=-vabs, vcenter=0.0, vmax=vabs)

    fig, ax = plt.subplots(figsize=(13.0, 9.0))
    im = ax.imshow(beta_mat, cmap="RdBu_r", norm=norm, aspect="auto")

    ax.set_xticks(np.arange(len(T_ORDER)))
    ax.set_xticklabels([str(t) for t in T_ORDER], fontsize=11)
    ax.set_yticks(np.arange(len(ROW_LABELS)))
    ax.set_yticklabels(ROW_LABELS, fontsize=11)

    ax.set_xlabel("Flood return period T", fontsize=12)
    ax.set_ylabel("Sample × risk group", fontsize=12)

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(np.arange(-0.5, len(T_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROW_LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Original notebook comment normalized for the public code archive.
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            if not sufficient_mat[i, j]:
                rect = plt.Rectangle(
                    (j - 0.5, i - 0.5), 1, 1,
                    fill=False,
                    edgecolor="gray",
                    linewidth=2.0,
                    linestyle="--",
                )
                ax.add_patch(rect)

    # Original notebook comment normalized for the public code archive.
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            val = beta_mat[i, j]
            txt = text_mat[i][j]

            if np.isfinite(val) and abs(val) > 0.55 * vabs:
                text_color = "white"
            else:
                text_color = "black"

            ax.text(
                j, i, txt,
                ha="center", va="center",
                fontsize=10.0,
                color=text_color
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("IVW pooled effect within significant subset", fontsize=12)

    fig.suptitle(title, fontsize=16, y=0.97)

    note = (
        f"Cell fill = IVW pooled effect computed only when the number of significant specifications reaches the preset threshold "
        f"(current threshold = {min_sig_required}). "
        "Cell text = significant count / total + same-sign count / significant + close count / significant + pooled effect.\n"
        f"Close is defined as |β_j - β_IVW,sig| ≤ {REL_TOL:.0%} × max(|β_IVW,sig|, floor). "
        "Grey dashed border = insufficient signal coverage."
    )
    fig.text(0.5, 0.02, note, ha="center", fontsize=9.6)

    plt.tight_layout(rect=[0.02, 0.06, 0.98, 0.94])
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[SAVED] {out_png}")
    print(f"[SAVED] {out_pdf}")


# =========================================================
# 5. RUN
# =========================================================

def run_education():
    print(f"[READ] {EDU_SUMMARY_CSV}")
    df = pd.read_csv(EDU_SUMMARY_CSV)
    df = safe_numeric(
        df,
        ["T", "n_spec", "n_sig", "beta_ivw_sig", "sign_same_sig_n", "close_sig_n"]
    )

    plot_sig_subset_heatmap(
        summary_df=df,
        title="Children's education: conditional robustness within significant specifications (strict replot)",
        out_png=EDU_OUT_PNG,
        out_pdf=EDU_OUT_PDF,
        min_sig_required=MIN_SIG_EDU,
    )


def run_older():
    print(f"[READ] {OLDER_SUMMARY_CSV}")
    df = pd.read_csv(OLDER_SUMMARY_CSV)
    df = safe_numeric(
        df,
        ["T", "n_spec", "n_sig", "beta_ivw_sig", "sign_same_sig_n", "close_sig_n"]
    )

    plot_sig_subset_heatmap(
        summary_df=df,
        title="Older adults' health: conditional robustness within significant specifications (strict replot)",
        out_png=OLDER_OUT_PNG,
        out_pdf=OLDER_OUT_PDF,
        min_sig_required=MIN_SIG_OLDER,
    )


def main():
    print("=" * 80)
    print("[STEP] Replot education")
    print("=" * 80)
    run_education()

    print("\n" + "=" * 80)
    print("[STEP] Replot older health")
    print("=" * 80)
    run_older()

    print("\n[ALL DONE]")
    print(f"[OUT] {OUT_DIR}")


if __name__ == "__main__":
    main()
