#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import json
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import Affine

# =============================================================================
SCHOOL_SHP = Path("/home/ll/jupyter_notebook/gis_data/Child/china_school_L3/china_school_L3.shp")
BIN_ROOT   = Path("/home/ll/jupyter_notebook/result/ensemble_daily_bin_p50")

OUT_DIR = Path("/home/ll/jupyter_notebook/result/ensemble_school")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
OUT_TERM_PANEL = OUT_DIR / "school_flood_exposure_ge1m_term_panel.parquet"

# Original notebook comment normalized for the public code archive.
MAKE_ANNUAL_PANEL = False
OUT_ANNUAL_PANEL = OUT_DIR / "school_flood_exposure_ge1m_panel.parquet"

# Original notebook comment normalized for the public code archive.
YEAR_START = 1980
YEAR_END   = 2020  # Original notebook comment normalized for the public code archive.

DEPTH_THR = 1.0  # m

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
FALL_START_MD   = (9, 1)
FALL_END_MD     = (1, 31)
SPRING_START_MD = (3, 1)
SPRING_END_MD   = (7, 31)


# =============================================================================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
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
            print("[INFO] Notebook progress message.")
            last_err = e
    raise RuntimeError(f"无法用多种编码读取 {shp_path}") from last_err


# =============================================================================
def find_any_meta_json() -> Path:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for year_dir in sorted(BIN_ROOT.iterdir()):
        if not year_dir.is_dir():
            continue
        for f in year_dir.iterdir():
            if f.suffix == ".json" and f.name.startswith("ensemble_"):
                return f
    raise FileNotFoundError(f"在 {BIN_ROOT} 下未找到任何 ensemble_*.json 元数据")


def load_meta(meta_path: Path) -> dict:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    rows = int(meta["rows"])
    cols = int(meta["cols"])
    compress = meta.get("compress", None)
    compact_mode = meta.get("compact_mode", "float16")

    tr = meta["transform"]
    if not isinstance(tr, (list, tuple)) or len(tr) != 4:
        raise ValueError(f"meta['transform'] 期望为 4 元素 [c,f,a,e]，但得到：{tr}")
    c, f0, a, e = tr
    transform = Affine(a, 0.0, c,
                       0.0, e, f0)

    band_meta = meta["bands"][0]
    scale = band_meta.get("scale", 1.0)
    offset = band_meta.get("offset", 0.0)
    nan_code = band_meta.get("nan", None)

    return dict(
        rows=rows, cols=cols,
        transform=transform,
        compress=compress,
        compact_mode=compact_mode,
        scale=scale, offset=offset,
        nan_code=nan_code,
    )


def find_bin_for_date(d: dt.date) -> Path | None:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    year_dir = BIN_ROOT / f"{d.year}"
    if not year_dir.is_dir():
        return None

    base = year_dir / f"ensemble_{d:%Y%m%d}_p50.bin"
    for ext in ["", ".zst", ".gz"]:
        fp = Path(str(base) + ext)
        if fp.is_file():
            return fp
    return None


def read_p50_grid(bin_path: Path, meta: dict) -> np.ndarray:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = meta["rows"]
    cols = meta["cols"]
    compress = meta["compress"]
    compact_mode = meta["compact_mode"]
    scale = meta["scale"]
    offset = meta["offset"]
    nan_code = meta["nan_code"]

    # Original notebook comment normalized for the public code archive.
    if compress == "zstd":
        import zstandard as zstd
        with open(bin_path, "rb") as f:
            dctx = zstd.ZstdDecompressor()
            data = dctx.decompress(f.read())
    elif compress == "gzip":
        import gzip
        with gzip.open(bin_path, "rb") as f:
            data = f.read()
    else:
        with open(bin_path, "rb") as f:
            data = f.read()

    # Original notebook comment normalized for the public code archive.
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

    return arr


# =============================================================================
def prepare_school_points(meta: dict) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    gdf = read_shp_safe(SCHOOL_SHP)

    # Original notebook comment normalized for the public code archive.
    ci_col = None
    for cand in ["CI", "ci", "Ci"]:
        if cand in gdf.columns:
            ci_col = cand
            break
    if ci_col is None:
        raise KeyError("学校 shapefile 中缺少 CI 字段（CI/ci/Ci），无法筛选 L1/L2")

    # Original notebook comment normalized for the public code archive.
    if "build_year" not in gdf.columns:
        raise KeyError("学校 shapefile 中缺少 build_year 字段")

    # Original notebook comment normalized for the public code archive.
    before_ci = len(gdf)
    gdf = gdf[gdf[ci_col].isin(["L1", "L2"])].copy()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    gdf["build_year"] = pd.to_numeric(gdf["build_year"], errors="coerce")
    gdf = gdf.dropna(subset=["build_year"]).copy()
    gdf["build_year"] = gdf["build_year"].astype(int)
    print("[INFO] Notebook progress message.")

    # CRS -> 4326
    if gdf.crs is None:
        raise ValueError("学校 shapefile 缺少 CRS；请先补齐或确认其坐标系")
    gdf = gdf.to_crs(epsg=4326)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    # School POI processing note.
    if "prov" in gdf.columns and "sid" in gdf.columns:
        gdf["school_id"] = gdf["prov"].astype(str) + "_" + gdf["sid"].astype(str)
    else:
        gdf["school_id"] = gdf.index.astype(str)

    # row/col
    transform = meta["transform"]
    rows, cols = rasterio.transform.rowcol(transform, gdf["lon"].values, gdf["lat"].values)
    gdf["row"] = np.asarray(rows, dtype=int)
    gdf["col"] = np.asarray(cols, dtype=int)

    # Original notebook comment normalized for the public code archive.
    mask_in = (
        (gdf["row"] >= 0) & (gdf["row"] < meta["rows"]) &
        (gdf["col"] >= 0) & (gdf["col"] < meta["cols"])
    )
    gdf = gdf.loc[mask_in].reset_index(drop=True)

    df = gdf[["school_id", "lon", "lat", "build_year", "row", "col"]].copy()
    print("[INFO] Notebook progress message.")
    return df


# =============================================================================
def daterange(d0: dt.date, d1: dt.date):
    cur = d0
    one = dt.timedelta(days=1)
    while cur <= d1:
        yield cur
        cur += one


# =============================================================================
def compute_term_exposure(
    sch_rows: np.ndarray,
    sch_cols: np.ndarray,
    build_years: np.ndarray,
    meta: dict,
    d0: dt.date,
    d1: dt.date,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    n = len(build_years)
    exposed_any = np.zeros(n, dtype=bool)
    days_ge = np.zeros(n, dtype=np.int16)

    n_days_data = 0

    for day in daterange(d0, d1):
        bin_path = find_bin_for_date(day)
        if bin_path is None:
            continue

        n_days_data += 1
        grid = read_p50_grid(bin_path, meta)  # float32 rows×cols
        vals = grid[sch_rows, sch_cols]

        exist_mask = build_years <= day.year
        hit = exist_mask & np.isfinite(vals) & (vals >= DEPTH_THR)
        if hit.any():
            exposed_any[hit] = True
            days_ge[hit] += 1

    return exposed_any, days_ge, n_days_data


# =============================================================================
def build_term_panel(df_sch: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sch_ids = df_sch["school_id"].to_numpy()
    sch_rows = df_sch["row"].to_numpy(dtype=int)
    sch_cols = df_sch["col"].to_numpy(dtype=int)
    build_years = df_sch["build_year"].to_numpy(dtype=int)

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    ay_start = YEAR_START
    ay_end = YEAR_END - 1  # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")

    records = []

    for ay in range(ay_start, ay_end + 1):
        # =============================================================================
        fall_d0 = dt.date(ay, *FALL_START_MD)
        fall_d1 = dt.date(ay + 1, *FALL_END_MD)

        # =============================================================================
        spring_d0 = dt.date(ay + 1, *SPRING_START_MD)
        spring_d1 = dt.date(ay + 1, *SPRING_END_MD)

        # Original notebook comment normalized for the public code archive.
        fall_exist_idx = np.where(build_years <= fall_d1.year)[0]
        spring_exist_idx = np.where(build_years <= spring_d1.year)[0]

        print(f"[AY] {ay}: fall schools={len(fall_exist_idx)}, spring schools={len(spring_exist_idx)}")

        # --- Fall ---
        fall_exposed, fall_days, fall_ndays = compute_term_exposure(
            sch_rows, sch_cols, build_years, meta, fall_d0, fall_d1
        )
        # Original notebook comment normalized for the public code archive.
        for idx in fall_exist_idx:
            records.append({
                "school_id": sch_ids[idx],
                "lon": float(df_sch.loc[idx, "lon"]),
                "lat": float(df_sch.loc[idx, "lat"]),
                "build_year": int(build_years[idx]),
                "ay": int(ay),
                "term": "fall",
                "window_start": fall_d0.isoformat(),
                "window_end": fall_d1.isoformat(),
                "exposed_ge1m": int(fall_exposed[idx]),
                "days_ge1m": int(fall_days[idx]),
                "n_days_data": int(fall_ndays),
            })

        print(f"  [FALL] ay={ay}: exposed=1 schools={int(np.sum(fall_exposed[fall_exist_idx]))}, n_days_data={fall_ndays}")

        # --- Spring ---
        spring_exposed, spring_days, spring_ndays = compute_term_exposure(
            sch_rows, sch_cols, build_years, meta, spring_d0, spring_d1
        )
        for idx in spring_exist_idx:
            records.append({
                "school_id": sch_ids[idx],
                "lon": float(df_sch.loc[idx, "lon"]),
                "lat": float(df_sch.loc[idx, "lat"]),
                "build_year": int(build_years[idx]),
                "ay": int(ay),
                "term": "spring",
                "window_start": spring_d0.isoformat(),
                "window_end": spring_d1.isoformat(),
                "exposed_ge1m": int(spring_exposed[idx]),
                "days_ge1m": int(spring_days[idx]),
                "n_days_data": int(spring_ndays),
            })

        print(f"  [SPRING] ay={ay}: exposed=1 schools={int(np.sum(spring_exposed[spring_exist_idx]))}, n_days_data={spring_ndays}")

    df_out = pd.DataFrame.from_records(records)
    return df_out


# =============================================================================
def build_annual_panel(df_sch: pd.DataFrame, meta: dict) -> pd.DataFrame:
    sch_ids = df_sch["school_id"].to_numpy()
    sch_rows = df_sch["row"].to_numpy(dtype=int)
    sch_cols = df_sch["col"].to_numpy(dtype=int)
    build_years = df_sch["build_year"].to_numpy(dtype=int)

    records = []
    n_sch = len(df_sch)

    for year in range(YEAR_START, YEAR_END + 1):
        exist_mask_year = build_years <= year
        if not exist_mask_year.any():
            continue

        print(f"[YEAR] {year}: schools={int(exist_mask_year.sum())}")

        exposed_any = np.zeros(n_sch, dtype=bool)
        days_ge = np.zeros(n_sch, dtype=np.int16)
        n_days_data = 0

        d0 = dt.date(year, 1, 1)
        d1 = dt.date(year, 12, 31)

        for day in daterange(d0, d1):
            bin_path = find_bin_for_date(day)
            if bin_path is None:
                continue
            n_days_data += 1

            grid = read_p50_grid(bin_path, meta)
            vals = grid[sch_rows, sch_cols]

            exist_mask_day = build_years <= day.year  # Original notebook comment normalized for the public code archive.
            hit = exist_mask_day & np.isfinite(vals) & (vals >= DEPTH_THR)
            if hit.any():
                exposed_any[hit] = True
                days_ge[hit] += 1

        idx_exist = np.where(exist_mask_year)[0]
        for idx in idx_exist:
            records.append({
                "school_id": sch_ids[idx],
                "lon": float(df_sch.loc[idx, "lon"]),
                "lat": float(df_sch.loc[idx, "lat"]),
                "build_year": int(build_years[idx]),
                "year": int(year),
                "exposed_ge1m": int(exposed_any[idx]),
                "days_ge1m": int(days_ge[idx]),
                "n_days_data": int(n_days_data),
            })

        print(f"  [INFO] year={year}: exposed=1 schools={int(np.sum(exposed_any & exist_mask_year))}, n_days_data={n_days_data}")

    return pd.DataFrame.from_records(records)


# ----------------- 8) main -----------------
def main():
    meta_json = find_any_meta_json()
    print(f"[META] using: {meta_json}")
    meta = load_meta(meta_json)
    print(f"[INFO] grid={meta['rows']}x{meta['cols']}, compact_mode={meta['compact_mode']}, compress={meta['compress']}")

    df_sch = prepare_school_points(meta)

    # Original notebook comment normalized for the public code archive.
    df_term = build_term_panel(df_sch, meta)
    df_term.to_parquet(OUT_TERM_PANEL, index=False)
    print(f"[DONE] term panel saved: {OUT_TERM_PANEL}")
    print(df_term.head())

    # Original notebook comment normalized for the public code archive.
    if MAKE_ANNUAL_PANEL:
        df_annual = build_annual_panel(df_sch, meta)
        df_annual.to_parquet(OUT_ANNUAL_PANEL, index=False)
        print(f"[DONE] annual panel saved: {OUT_ANNUAL_PANEL}")
        print(df_annual.head())


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

# =============================================================================
TERM_PANEL = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_term_panel.parquet"
)

COUNTY_SHP = Path(
    "/home/ll/jupyter_notebook/gis_data/China/country/country.shp"
)

EDU_BM_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

OUT_COUNTY_AY_TERM = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_county_ay_term.parquet"
)

OUT_COHORT_TERM = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_county_birthyear_term.parquet"
)

OUT_EDU_TERM_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_term_exposure.parquet"
)

OUT_EDU_TERM_SAMPLE = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_term_exposure_sample.xlsx"
)

# Original notebook comment normalized for the public code archive.
SCHOOL_AGE_MIN = 6
SCHOOL_AGE_MAX = 15


# =============================================================================
def load_county_shp():
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    gdf = gpd.read_file(COUNTY_SHP)

    if gdf.crs is None:
        raise ValueError("county shapefile 缺少 CRS，请先写入 EPSG:4326。")
    gdf = gdf.to_crs(epsg=4326)

    if "county_code" in gdf.columns:
        code_col = "county_code"
    elif "县代码" in gdf.columns:
        code_col = "县代码"
    else:
        raise KeyError("县级矢量中找不到 county_code 或 县代码 字段。")

    gdf["county_code"] = pd.to_numeric(gdf[code_col], errors="coerce").astype("Int64")
    gdf = gdf.dropna(subset=["county_code"]).copy()
    return gdf[["county_code", "geometry"]]


def attach_county_code(df_term: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    need_cols = ["school_id", "lon", "lat"]
    for c in need_cols:
        if c not in df_term.columns:
            raise KeyError(f"term panel 缺少 {c}")

    gdf_county = load_county_shp()

    schools = df_term[need_cols].drop_duplicates("school_id").copy()
    gdf_school = gpd.GeoDataFrame(
        schools,
        geometry=gpd.points_from_xy(schools["lon"], schools["lat"]),
        crs="EPSG:4326",
    )

    print("[INFO] Notebook progress message.")
    joined = gpd.sjoin(gdf_school, gdf_county, how="left", predicate="within")
    joined = joined.dropna(subset=["county_code"]).copy()
    joined["county_code"] = pd.to_numeric(joined["county_code"], errors="coerce").astype("Int64")

    map_df = joined[["school_id", "county_code"]].copy()

    out = df_term.merge(map_df, on="school_id", how="left", validate="m:1")

    miss = out["county_code"].isna().mean()
    print("[INFO] Notebook progress message.")
    out = out.dropna(subset=["county_code"]).copy()
    out["county_code"] = out["county_code"].astype("Int64")
    return out


def build_county_ay_term(df_term_with_county: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_term_with_county.copy()

    for c in ["ay", "term", "exposed_ge1m", "days_ge1m", "n_days_data"]:
        if c not in df.columns:
            raise KeyError(f"term panel 缺少 {c}")

    df["exposed_ge1m"] = pd.to_numeric(df["exposed_ge1m"], errors="coerce").fillna(0).astype(int)
    df["days_ge1m"] = pd.to_numeric(df["days_ge1m"], errors="coerce").fillna(0).astype(float)
    df["n_days_data"] = pd.to_numeric(df["n_days_data"], errors="coerce").fillna(0).astype(int)

    print("[INFO] Notebook progress message.")
    out = (
        df.groupby(["county_code", "ay", "term"], as_index=False)
          .agg(
              n_school=("school_id", "nunique"),
              n_school_exposed_ge1m=("exposed_ge1m", "sum"),
              share_exposed_ge1m=("exposed_ge1m", "mean"),
              mean_days_ge1m=("days_ge1m", "mean"),
              n_days_data=("n_days_data", "max"),  # Original notebook comment normalized for the public code archive.
          )
    )

    OUT_COUNTY_AY_TERM.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_COUNTY_AY_TERM, index=False)
    print("[INFO] Notebook progress message.")
    print(out.head())
    return out


def build_cohort_from_county_ay_term(df_cat: pd.DataFrame, birth_min: int, birth_max: int) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_cat.copy()

    pieces = []
    for age in range(SCHOOL_AGE_MIN, SCHOOL_AGE_MAX + 1):
        tmp = df.copy()
        tmp["age"] = age

        # Original notebook comment normalized for the public code archive.
        ref_year = np.where(tmp["term"].values == "fall", tmp["ay"].values, tmp["ay"].values + 1)
        tmp["birth_year"] = ref_year - age
        pieces.append(tmp)

    exp = pd.concat(pieces, ignore_index=True)

    # Original notebook comment normalized for the public code archive.
    exp = exp[(exp["birth_year"] >= birth_min) & (exp["birth_year"] <= birth_max)].copy()
    exp["birth_year"] = pd.to_numeric(exp["birth_year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    exp["term_has_flood"] = (exp["share_exposed_ge1m"] > 0).astype(int)

    # County-level processing note.
    g_term = (
        exp.groupby(["county_code", "birth_year", "term"], as_index=False)
           .agg(
               n_terms=("ay", "nunique"),
               any_exposed_ge1m=("term_has_flood", "max"),
               mean_share_ge1m=("share_exposed_ge1m", "mean"),
               mean_days_ge1m=("mean_days_ge1m", "mean"),
               n_flood_terms=("term_has_flood", "sum"),
           )
    )

    # Original notebook comment normalized for the public code archive.
    wide = g_term.pivot(index=["county_code", "birth_year"], columns="term")
    wide.columns = [f"F_school_{t}_{v}" for v, t in wide.columns]  # (var, term) -> suffix
    wide = wide.reset_index()

    # Original notebook comment normalized for the public code archive.
    for c in wide.columns:
        if c.startswith("F_school_"):
            wide[c] = wide[c].fillna(0)

    # Original notebook comment normalized for the public code archive.
    wide["F_school_term_n_terms"] = wide.get("F_school_fall_n_terms", 0) + wide.get("F_school_spring_n_terms", 0)
    wide["F_school_term_any_exposed_ge1m"] = (
        (wide.get("F_school_fall_any_exposed_ge1m", 0) > 0) |
        (wide.get("F_school_spring_any_exposed_ge1m", 0) > 0)
    ).astype(int)

    # Original notebook comment normalized for the public code archive.
    def wavg(x1, n1, x2, n2):
        denom = n1 + n2
        return np.where(denom > 0, (x1 * n1 + x2 * n2) / denom, 0.0)

    fall_n = wide.get("F_school_fall_n_terms", 0).astype(float)
    spr_n  = wide.get("F_school_spring_n_terms", 0).astype(float)

    wide["F_school_term_mean_share_ge1m"] = wavg(
        wide.get("F_school_fall_mean_share_ge1m", 0).astype(float), fall_n,
        wide.get("F_school_spring_mean_share_ge1m", 0).astype(float), spr_n
    )
    wide["F_school_term_mean_days_ge1m"] = wavg(
        wide.get("F_school_fall_mean_days_ge1m", 0).astype(float), fall_n,
        wide.get("F_school_spring_mean_days_ge1m", 0).astype(float), spr_n
    )

    wide["F_school_term_n_flood_terms"] = wide.get("F_school_fall_n_flood_terms", 0) + wide.get("F_school_spring_n_flood_terms", 0)

    # Original notebook comment normalized for the public code archive.
    wide["F_school_term_mean_share"] = wide["F_school_term_mean_share_ge1m"]

    OUT_COHORT_TERM.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(OUT_COHORT_TERM, index=False)
    print("[INFO] Notebook progress message.")
    print(wide.head())
    return wide


def merge_to_micro(df_cohort: pd.DataFrame):
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    edu = pd.read_parquet(EDU_BM_PARQUET)
    print("[INFO] Notebook progress message.")

    if "birth_year" not in edu.columns:
        raise KeyError("教育微观数据缺少 birth_year。")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    # County-level processing note.
    if "county_code" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["county_code"], errors="coerce").astype("Int64")
    elif "M2" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    else:
        raise KeyError("教育微观数据中缺少 county_code 或 M2。")

    dfc = df_cohort.copy()
    dfc["county_code"] = pd.to_numeric(dfc["county_code"], errors="coerce").astype("Int64")
    dfc["birth_year"] = pd.to_numeric(dfc["birth_year"], errors="coerce").astype("Int64")

    merged = edu.merge(dfc, on=["county_code", "birth_year"], how="left", validate="m:1")

    exp_cols = [c for c in merged.columns if c.startswith("F_school_")]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    OUT_EDU_TERM_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_EDU_TERM_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    n_sample = min(100_000, len(merged))
    if n_sample > 0:
        sample = merged.sample(n=n_sample, random_state=42)
        OUT_EDU_TERM_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_excel(OUT_EDU_TERM_SAMPLE, index=False, sheet_name="sample")
        print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    show_cols = ["county_code", "birth_year"] + exp_cols[:20]
    print(merged[show_cols].head())
    return merged


def main():
    print("[INFO] Notebook progress message.")
    df_term = pd.read_parquet(TERM_PANEL)
    print(f"[INFO] term panel shape: {df_term.shape}")
    print(df_term.head())

    # 1) school_id -> county_code
    df_term2 = attach_county_code(df_term)

    # County-level processing note.
    df_cat = build_county_ay_term(df_term2)

    # Original notebook comment normalized for the public code archive.
    edu = pd.read_parquet(EDU_BM_PARQUET)
    birth_min = int(pd.to_numeric(edu["birth_year"], errors="coerce").min())
    birth_max = int(pd.to_numeric(edu["birth_year"], errors="coerce").max())
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_cohort = build_cohort_from_county_ay_term(df_cat, birth_min, birth_max)

    # Original notebook comment normalized for the public code archive.
    merge_to_micro(df_cohort)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path

TERM_PANEL = Path("/home/ll/jupyter_notebook/result/ensemble_school/school_flood_exposure_ge1m_term_panel.parquet")
CAT = Path("/home/ll/jupyter_notebook/result/ensemble_school/school_flood_exposure_ge1m_county_ay_term.parquet")
COHORT = Path("/home/ll/jupyter_notebook/result/ensemble_school/school_flood_exposure_ge1m_county_birthyear_term.parquet")
MICRO = Path("/home/ll/jupyter_notebook/result/impact_assessment/flood/edu_micro_2015_BM_school_term_exposure.parquet")

def quick_qc():
    df_t = pd.read_parquet(TERM_PANEL)
    print("[INFO] Notebook progress message.", (df_t["exposed_ge1m"]==1).mean())
    print("[INFO] Notebook progress message.", (df_t["days_ge1m"]>0).mean())
    print("[QC-1] term panel by term exposed rate:\n", df_t.groupby("term")["exposed_ge1m"].mean())

    df_cat = pd.read_parquet(CAT)
    print("[INFO] Notebook progress message.", (df_cat["share_exposed_ge1m"]>0).mean())
    print("[INFO] Notebook progress message.", (df_cat["mean_days_ge1m"]>0).mean())
    print("[QC-2] top years by share>0 counts:\n", df_cat.assign(pos=(df_cat["share_exposed_ge1m"]>0).astype(int))
                                         .groupby("ay")["pos"].sum().sort_values(ascending=False).head(10))

    df_co = pd.read_parquet(COHORT)
    key = "F_school_term_n_flood_terms"
    print("[INFO] Notebook progress message.", (df_co[key]>0).mean())
    print("[INFO] Notebook progress message.", df_co[key].value_counts().head(20))

    df_m = pd.read_parquet(MICRO)
    print("[INFO] Notebook progress message.", (df_m[key]>0).mean())
    print("[INFO] Notebook progress message.", df_m[key].value_counts().head(20))

quick_qc()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =============================================================================
IN_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_term_exposure.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_term_mechanism_FE"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "school_term_mechanism_FE_terms.csv"

# =============================================================================
Y_VAR = "edu_years"

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True
SAMPLES = ["rural", "urban"]

CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])

# Original notebook comment normalized for the public code archive.
K_MAX = 20

# Original notebook comment normalized for the public code archive.
MEASURES = {
    "term":   "F_school_term_n_flood_terms",
    "spring": "F_school_spring_n_flood_terms",
    "fall":   "F_school_fall_n_flood_terms",
}


# =============================================================================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"].astype("Int64") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df


def add_term_count_dummies(df: pd.DataFrame, src_col: str, prefix: str) -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if src_col not in df.columns:
        raise KeyError(f"数据缺少 {src_col}，请检查 term 暴露合并输出。")

    out = df.copy()
    out[src_col] = pd.to_numeric(out[src_col], errors="coerce").fillna(0)

    out["n_cap"] = out[src_col].clip(lower=0, upper=K_MAX).astype(int)
    for k in range(1, K_MAX + 1):
        out[f"{prefix}{k}"] = (out["n_cap"] == k).astype(int)

    return out


def normalize_tidy(res) -> pd.DataFrame:
    df = res.tidy().reset_index()
    if df.columns[0] != "Term":
        df = df.rename(columns={df.columns[0]: "Term"})

    rename = {}
    for c in df.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename[c] = "PValue"
    df = df.rename(columns=rename)

    if "StdError" not in df.columns:
        for c in df.columns:
            if "std" in c.lower():
                df = df.rename(columns={c: "StdError"})
                break
    if "PValue" not in df.columns:
        for c in df.columns:
            if c.lower().startswith("p"):
                df = df.rename(columns={c: "PValue"})
                break
    return df


def get_nobs(fit, fallback_df: pd.DataFrame) -> int:
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                return int(getattr(fit, attr))
            except Exception:
                pass
    return int(len(fallback_df))


def prepare_sample(df_all: pd.DataFrame, sample_tag: str, src_col: str, prefix: str) -> pd.DataFrame:
    df = df_all.copy()

    num_cols = ["M2", "M38", "birth_year", "age_2015"] + CONTROL_VARS + [src_col]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)
    df = add_term_count_dummies(df, src_col=src_col, prefix=prefix)

    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    # Original notebook comment normalized for the public code archive.
    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()
    dfm = dfm.dropna(subset=[Y_VAR, "M2", "birth_year"])

    # Original notebook comment normalized for the public code archive.
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)

    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str) + "_" +
        dfm["birth_year"].astype("Int64").astype(str)
    )

    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # controls -> category
    for c in CONTROL_VARS:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    return dfm.reset_index(drop=True)


def run_one_measure(df_all: pd.DataFrame, measure: str, src_col: str) -> pd.DataFrame:
    prefix = f"D_{measure}_"
    d_cols = [f"{prefix}{k}" for k in range(1, K_MAX + 1)]

    records = []

    for sample_tag in SAMPLES:
        dfm = prepare_sample(df_all, sample_tag, src_col=src_col, prefix=prefix)
        n = len(dfm)
        print(f"[FEOLS] measure={measure}, sample={sample_tag}, N={n}")
        if n < 200:
            print("[INFO] Notebook progress message.")
            continue

        missing = [c for c in d_cols if c not in dfm.columns]
        if missing:
            raise KeyError(f"measure={measure}, sample={sample_tag} 缺少虚拟变量: {missing}")

        d_part = " + ".join(d_cols)
        fml = (
            f"{Y_VAR} ~ {d_part} + {CONTROL_FML} + "
            f"i(M2, birth_year_c) | M2 + prov_birth_fe"
        )

        try:
            fit = feols(fml, dfm, vcov={"CRV1": "M2"})
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        tidy = normalize_tidy(fit)
        nobs = get_nobs(fit, dfm)

        for k in range(1, K_MAX + 1):
            term_name = f"{prefix}{k}"
            row = tidy[tidy["Term"] == term_name]
            if row.empty:
                continue
            row = row.iloc[0]
            records.append({
                "measure": measure,          # term / spring / fall
                "src_col": src_col,
                "sample": sample_tag,        # rural / urban
                "k_term": k,                 # Original notebook comment normalized for the public code archive.
                "Term": term_name,
                "Estimate": float(row.get("Estimate", np.nan)),
                "StdError": float(row.get("StdError", np.nan)),
                "PValue": float(row.get("PValue", np.nan)),
                "nobs": nobs,
            })

    return pd.DataFrame(records)


def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(IN_PARQUET)
    print(f"[INFO] df shape: {df.shape}")

    all_res = []
    for measure, col in MEASURES.items():
        all_res.append(run_one_measure(df, measure=measure, src_col=col))

    res = pd.concat(all_res, ignore_index=True) if all_res else pd.DataFrame()

    if res.empty:
        print("[INFO] Notebook progress message.")
        return

    res.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    print(res.head(10))


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_term_mechanism_FE/school_term_mechanism_FE_terms.csv"
)
OUT_DIR = RES_CSV.parent


def sig_label(p: float) -> str:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p <= 0.01:
        return "***"
    elif p <= 0.05:
        return "**"
    elif p <= 0.1:
        return "*"
    else:
        return ""


def prepare_data() -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)
    print("[INFO] Notebook progress message.")

    need_cols = ["sample", "measure", "k_term", "Estimate", "StdError", "PValue"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"结果表缺少必要列: {missing}")

    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("结果表中没有 rural/urban。")

    df["k_term"] = pd.to_numeric(df["k_term"], errors="coerce").astype("Int64")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["StdError"] = pd.to_numeric(df["StdError"], errors="coerce")
    df["PValue"] = pd.to_numeric(df["PValue"], errors="coerce")

    df = df.dropna(subset=["k_term", "Estimate", "StdError"]).copy()
    df["k_term"] = df["k_term"].astype(int)

    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


def plot_line(sub: pd.DataFrame, measure: str):
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = OUT_DIR / f"school_term_mechanism_{measure}_line.png"
    fig, ax = plt.subplots(figsize=(7.2, 4.6))

    z = 1.96

    for sample in ["rural", "urban"]:
        s = sub[sub["sample"] == sample].sort_values("k_term")
        if s.empty:
            continue

        x = s["k_term"].values
        y = s["Estimate"].values
        yerr = z * s["StdError"].values

        ax.errorbar(
            x,
            y,
            yerr=yerr,
            marker="o",
            linestyle="-",
            capsize=3,
            linewidth=1.4,
            label=sample,
        )

        # =============================================================================
        # Original notebook comment normalized for the public code archive.
        y_range = np.nanmax(np.abs(np.r_[s["CI_low"].values, s["CI_high"].values]))
        if not np.isfinite(y_range) or y_range == 0:
            y_range = 1.0
        dy = 0.01 * y_range  # Original notebook comment normalized for the public code archive.

        for xi, yi, ei, sig in zip(x, y, yerr, s["sig"].values):
            if sig:
                ax.text(
                    xi,
                    yi + ei + dy,
                    sig,
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    ax.axhline(0.0, linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    ks = sorted(sub["k_term"].unique())
    ax.set_xticks(ks)
    ax.set_xticklabels([str(k) for k in ks])

    ax.set_xlabel("在学期间内被淹学期数（学期）")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title(f"学校淹没机制（学期次数）- {measure}（折线+误差棒）")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.show()
    print(f"[DONE] {out}")


def main():
    df = prepare_data()
    measures = sorted(df["measure"].dropna().unique())
    print(f"[INFO] measures: {measures}")

    for measure in measures:
        sub = df[df["measure"] == measure].copy()
        if sub.empty:
            continue
        plot_line(sub, measure)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_term_mechanism_FE/school_term_mechanism_FE_terms.csv"
)
OUT_DIR = RES_CSV.parent
OUT_PNG = OUT_DIR / "school_term_mechanism_term_line.png"


def sig_label(p: float) -> str:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p <= 0.01:
        return "***"
    elif p <= 0.05:
        return "**"
    elif p <= 0.1:
        return "*"
    return ""


def prepare_data() -> pd.DataFrame:
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)
    print("[INFO] Notebook progress message.")

    need_cols = ["sample", "measure", "k_term", "Estimate", "StdError", "PValue"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"结果表缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("结果表中没有 rural/urban。")

    # Original notebook comment normalized for the public code archive.
    if (df["measure"] == "term").any():
        df = df[df["measure"] == "term"].copy()
    else:
        raise RuntimeError("结果表中未找到 measure == 'term' 的记录。")

    # Original notebook comment normalized for the public code archive.
    df["k_term"] = pd.to_numeric(df["k_term"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["StdError"] = pd.to_numeric(df["StdError"], errors="coerce")
    df["PValue"] = pd.to_numeric(df["PValue"], errors="coerce")

    df = df.dropna(subset=["k_term", "Estimate", "StdError"]).copy()
    df["k_term"] = df["k_term"].astype(int)

    # Original notebook comment normalized for the public code archive.
    df = df[(df["k_term"] >= 0) & (df["k_term"] <= 18)].copy()
    if df.empty:
        raise RuntimeError("过滤到 k_term ∈ [0,18] 后数据为空。")

    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


def plot_term_line(df: pd.DataFrame):
    """Archived notebook note for 04_spring_autumn_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    z = 1.96

    for sample in ["rural", "urban"]:
        s = df[df["sample"] == sample].sort_values("k_term")
        if s.empty:
            continue

        x = s["k_term"].to_numpy()
        y = s["Estimate"].to_numpy()
        yerr = (z * s["StdError"]).to_numpy()

        ax.errorbar(
            x,
            y,
            yerr=yerr,
            marker="o",
            linestyle="-",
            capsize=3,
            linewidth=1.4,
            label=sample,
        )

        # Original notebook comment normalized for the public code archive.
        y_scale = np.nanmax(np.abs(np.r_[s["CI_low"].to_numpy(), s["CI_high"].to_numpy()]))
        if not np.isfinite(y_scale) or y_scale == 0:
            y_scale = 1.0
        dy = 0.01 * y_scale

        for xi, yi, ei, sig in zip(x, y, yerr, s["sig"].to_numpy()):
            if sig:
                ax.text(xi, yi + ei + dy, sig, ha="center", va="bottom", fontsize=9)

    ax.axhline(0.0, linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(list(range(0, 19)))
    ax.set_xticklabels([str(k) for k in range(0, 19)])

    ax.set_xlabel("在学期间内被淹学期数（学期）")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title("学校淹没机制（学期次数）- term（折线+误差棒）")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.show()
    print(f"[DONE] {OUT_PNG}")


def main():
    df = prepare_data()
    plot_term_line(df)


if __name__ == "__main__":
    main()
