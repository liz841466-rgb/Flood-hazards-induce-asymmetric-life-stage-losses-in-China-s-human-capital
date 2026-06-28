#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_monthly_schooling_seasonality.

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

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
SCHOOL_SHP = Path("/home/ll/jupyter_notebook/gis_data/Child/china_school_L3/china_school_L3.shp")
COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
ENSEMBLE_BASE = Path("/home/ll/jupyter_notebook/result/ensemble_daily_bin_p50")

EDU_BM_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

YEAR_START = 1980
YEAR_END   = 2020
DEPTH_THR  = 1.0  # m

SCHOOL_AGE_MIN = 6
SCHOOL_AGE_MAX = 15

OUT_DIR = Path("/home/ll/jupyter_notebook/result/ensemble_school")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_COUNTY_YM = OUT_DIR / "school_flood_exposure_ge1m_county_year_month.parquet"
OUT_COHORT_M  = OUT_DIR / "school_flood_exposure_ge1m_county_birthyear_month.parquet"

OUT_MICRO = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_month_exposure.parquet"
)

# Original notebook comment normalized for the public code archive.
SAVE_SCHOOL_MONTH_PANEL = False
OUT_SCHOOL_MONTH_DIR = OUT_DIR / "school_month_panels_by_year"
OUT_SCHOOL_MONTH_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
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
        except Exception as e:
            print("[INFO] Notebook progress message.")
            last_err = e
    raise RuntimeError(f"无法读取 {shp_path}") from last_err


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def find_any_meta_json() -> Path:
    for year_dir in sorted(ENSEMBLE_BASE.iterdir()):
        if not year_dir.is_dir():
            continue
        for f in year_dir.iterdir():
            if f.suffix == ".json" and f.name.startswith("ensemble_"):
                return f
    raise FileNotFoundError(f"在 {ENSEMBLE_BASE} 下未找到 ensemble_*.json")


def parse_transform(tr):
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(tr, dict):
        need = ["a", "b", "c", "d", "e", "f"]
        if not all(k in tr for k in need):
            raise ValueError(f"transform dict 缺少键: {need}, got={tr.keys()}")
        return Affine(tr["a"], tr["b"], tr["c"], tr["d"], tr["e"], tr["f"])

    if isinstance(tr, (list, tuple)):
        if len(tr) == 6:
            return Affine(*tr)
        if len(tr) == 4:
            c, f, a, e = tr
            return Affine(a, 0.0, c, 0.0, e, f)

    raise ValueError(f"无法解析 transform 字段：{tr}")


def load_meta(meta_path: Path) -> dict:
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    rows = int(meta["rows"])
    cols = int(meta["cols"])
    compress = meta.get("compress", None)
    compact_mode = meta.get("compact_mode", "float16")

    transform = parse_transform(meta["transform"])

    band_meta = meta["bands"][0]
    band_dtype = band_meta.get("dtype", None)
    scale = band_meta.get("scale", 1.0)
    offset = band_meta.get("offset", 0.0)
    nan_code = band_meta.get("nan", None)

    return dict(
        rows=rows, cols=cols, transform=transform,
        compress=compress, compact_mode=compact_mode,
        band_dtype=band_dtype, scale=scale, offset=offset, nan_code=nan_code
    )


def find_bin_for_date(date: dt.date) -> Path | None:
    year_dir = ENSEMBLE_BASE / f"{date.year}"
    if not year_dir.is_dir():
        return None
    base = year_dir / f"ensemble_{date:%Y%m%d}_p50.bin"
    for ext in ["", ".zst", ".gz"]:
        fp = Path(str(base) + ext)
        if fp.is_file():
            return fp
    return None


def read_p50_grid(bin_path: Path, meta: dict) -> np.ndarray:
    rows = meta["rows"]
    cols = meta["cols"]
    compress = meta["compress"]
    compact_mode = meta["compact_mode"]
    scale = meta["scale"]
    offset = meta["offset"]
    nan_code = meta["nan_code"]

    if compress == "zstd":
        import zstandard as zstd
        with open(bin_path, "rb") as f:
            data = zstd.ZstdDecompressor().decompress(f.read())
    elif compress == "gzip":
        import gzip
        with gzip.open(bin_path, "rb") as f:
            data = f.read()
    else:
        with open(bin_path, "rb") as f:
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

    return arr


# =========================
# County-level processing note.
# =========================
def load_county_gdf() -> gpd.GeoDataFrame:
    print("[INFO] Notebook progress message.")
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("county shapefile 缺少 CRS，请先写入 EPSG:4326 或可转换 CRS。")
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


def prepare_school_points(meta: dict) -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    gdf = read_shp_safe(SCHOOL_SHP)

    if "CI" not in gdf.columns:
        raise KeyError("学校 shapefile 缺少 CI 字段")
    if "build_year" not in gdf.columns:
        raise KeyError("学校 shapefile 缺少 build_year 字段")

    n0 = len(gdf)
    gdf = gdf[gdf["CI"].isin(["L1", "L2"])].copy()
    print("[INFO] Notebook progress message.")

    gdf = gdf[~gdf["build_year"].isna()].copy()
    print("[INFO] Notebook progress message.")

    gdf = gdf.to_crs(epsg=4326)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    if "prov" in gdf.columns and "sid" in gdf.columns:
        gdf["school_id"] = gdf["prov"].astype(str) + "_" + gdf["sid"].astype(str)
    else:
        gdf["school_id"] = gdf.index.astype(str)

    # row/col
    rows, cols = rasterio.transform.rowcol(
        meta["transform"],
        gdf["lon"].values,
        gdf["lat"].values
    )
    gdf["row"] = rows
    gdf["col"] = cols

    # Original notebook comment normalized for the public code archive.
    mask_in = (
        (gdf["row"] >= 0) & (gdf["row"] < meta["rows"]) &
        (gdf["col"] >= 0) & (gdf["col"] < meta["cols"])
    )
    gdf = gdf.loc[mask_in].copy()

    # County-level processing note.
    county = load_county_gdf()
    print("[INFO] Notebook progress message.")
    gdf_join = gpd.sjoin(gdf, county, how="left", predicate="within")
    gdf_join = gdf_join.dropna(subset=["county_code"]).copy()
    gdf_join["county_code"] = pd.to_numeric(gdf_join["county_code"], errors="coerce").astype("Int64")

    df = gdf_join[["school_id", "lon", "lat", "build_year", "row", "col", "county_code"]].copy()
    df["build_year"] = pd.to_numeric(df["build_year"], errors="coerce").astype(int)

    print("[INFO] Notebook progress message.")
    return df.reset_index(drop=True)


# =========================
# County-level processing note.
# =========================
def build_county_year_month(meta: dict, df_sch: pd.DataFrame) -> pd.DataFrame:
    sch_ids = df_sch["school_id"].to_numpy()
    sch_rows = df_sch["row"].to_numpy()
    sch_cols = df_sch["col"].to_numpy()
    build_years = df_sch["build_year"].to_numpy()
    sch_county = df_sch["county_code"].to_numpy()

    n_sch = len(df_sch)
    recs_county = []
    all_years = range(YEAR_START, YEAR_END + 1)

    for year in all_years:
        exist_mask = build_years <= year
        n_exist = int(exist_mask.sum())
        if n_exist == 0:
            continue

        print("[INFO] Notebook progress message.")

        # Original notebook comment normalized for the public code archive.
        exposed_m = np.zeros((n_sch, 12), dtype=bool)
        days_ge_m = np.zeros((n_sch, 12), dtype=np.int16)
        nday_data_m = np.zeros((n_sch, 12), dtype=np.int16)

        cur = dt.date(year, 1, 1)
        end = dt.date(year, 12, 31)
        one = dt.timedelta(days=1)

        while cur <= end:
            bin_path = find_bin_for_date(cur)
            if bin_path is None:
                cur += one
                continue

            grid = read_p50_grid(bin_path, meta)
            vals = grid[sch_rows, sch_cols]  # Original notebook comment normalized for the public code archive.

            m = cur.month - 1

            # Original notebook comment normalized for the public code archive.
            mask_data = exist_mask & np.isfinite(vals)
            if mask_data.any():
                nday_data_m[mask_data, m] += 1

                mask_ge = mask_data & (vals >= DEPTH_THR)
                if mask_ge.any():
                    exposed_m[mask_ge, m] = True
                    days_ge_m[mask_ge, m] += 1

            cur += one

        # Original notebook comment normalized for the public code archive.
        if SAVE_SCHOOL_MONTH_PANEL:
            school_recs = []
            idx_exist = np.where(exist_mask)[0]
            for idx in idx_exist:
                for month in range(1, 13):
                    mm = month - 1
                    school_recs.append({
                        "school_id": sch_ids[idx],
                        "lon": float(df_sch.loc[idx, "lon"]),
                        "lat": float(df_sch.loc[idx, "lat"]),
                        "build_year": int(build_years[idx]),
                        "county_code": int(sch_county[idx]),
                        "year": int(year),
                        "month": int(month),
                        "exposed_ge1m": int(exposed_m[idx, mm]),
                        "days_ge1m": int(days_ge_m[idx, mm]),
                        "n_days_data": int(nday_data_m[idx, mm]),
                    })
            df_school_y = pd.DataFrame.from_records(school_recs)
            out_y = OUT_SCHOOL_MONTH_DIR / f"school_month_panel_{year}.parquet"
            df_school_y.to_parquet(out_y, index=False)
            print(f"[DONE] school×year×month saved: {out_y}")

        # County-level processing note.
        idx_exist = np.where(exist_mask)[0]
        for month in range(1, 13):
            mm = month - 1
            tmp = pd.DataFrame({
                "county_code": sch_county[idx_exist],
                "exposed": exposed_m[idx_exist, mm].astype(int),
                "days": days_ge_m[idx_exist, mm].astype(np.int32),
            })

            g = tmp.groupby("county_code", as_index=False).agg(
                n_school=("exposed", "size"),
                n_school_exposed_ge1m=("exposed", "sum"),
                share_exposed_ge1m=("exposed", "mean"),
                mean_days_ge1m=("days", "mean"),
            )
            g["year"] = int(year)
            g["month"] = int(month)
            recs_county.append(g)

        print(f"[INFO] {year} done.")

    df_cym = pd.concat(recs_county, ignore_index=True) if recs_county else pd.DataFrame()
    df_cym = df_cym[["county_code", "year", "month", "n_school", "n_school_exposed_ge1m",
                     "share_exposed_ge1m", "mean_days_ge1m"]].copy()

    df_cym.to_parquet(OUT_COUNTY_YM, index=False)
    print(f"[DONE] county×year×month saved: {OUT_COUNTY_YM}  shape={df_cym.shape}")
    return df_cym


# =========================
# County-level processing note.
# =========================
def build_cohort_month(df_cym: pd.DataFrame, birth_min: int, birth_max: int) -> pd.DataFrame:
    print("[INFO] Notebook progress message.")

    pieces = []
    for age in range(SCHOOL_AGE_MIN, SCHOOL_AGE_MAX + 1):
        tmp = df_cym.copy()
        tmp["age"] = age
        tmp["birth_year"] = tmp["year"] - age
        pieces.append(tmp)

    df_exp = pd.concat(pieces, ignore_index=True)
    df_exp = df_exp[(df_exp["birth_year"] >= birth_min) & (df_exp["birth_year"] <= birth_max)].copy()

    agg = (
        df_exp.groupby(["county_code", "birth_year", "month"], as_index=False)
        .agg(
            F_school_month_n_years=("year", "nunique"),
            F_school_month_any_exposed_ge1m=("share_exposed_ge1m", lambda x: int((x > 0).any())),
            F_school_month_mean_share_ge1m=("share_exposed_ge1m", "mean"),
            F_school_month_mean_days_ge1m=("mean_days_ge1m", "mean"),
            F_school_month_n_flood_years=("share_exposed_ge1m", lambda x: int((x > 0).sum())),
        )
    )
    agg["F_school_month_mean_share"] = agg["F_school_month_mean_share_ge1m"]

    agg.to_parquet(OUT_COHORT_M, index=False)
    print(f"[DONE] cohort(month) saved: {OUT_COHORT_M}  shape={agg.shape}")
    return agg


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def merge_to_micro_wide(df_cohort_m: pd.DataFrame) -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    edu = pd.read_parquet(EDU_BM_PARQUET)
    print("[INFO] Notebook progress message.")

    if "birth_year" not in edu.columns:
        raise KeyError("微观数据缺少 birth_year")

    # County-level processing note.
    if "county_code" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["county_code"], errors="coerce").astype("Int64")
    elif "M2" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    else:
        raise KeyError("微观数据缺少 county_code 或 M2")

    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    dfm = df_cohort_m.copy()
    dfm["county_code"] = pd.to_numeric(dfm["county_code"], errors="coerce").astype("Int64")
    dfm["birth_year"] = pd.to_numeric(dfm["birth_year"], errors="coerce").astype("Int64")
    dfm["month"] = pd.to_numeric(dfm["month"], errors="coerce").astype(int)

    # Original notebook comment normalized for the public code archive.
    val_col = "F_school_month_n_flood_years"

    wide = dfm.pivot_table(
        index=["county_code", "birth_year"],
        columns="month",
        values=val_col,
        aggfunc="first",
    ).reset_index()

    # Original notebook comment normalized for the public code archive.
    new_cols = {}
    for m in range(1, 13):
        if m in wide.columns:
            new_cols[m] = f"F_month{m:02d}_n_flood_years"
    wide = wide.rename(columns=new_cols)

    merged = edu.merge(
        wide,
        how="left",
        on=["county_code", "birth_year"],
        validate="m:1",
    )

    # Original notebook comment normalized for the public code archive.
    for m in range(1, 13):
        c = f"F_month{m:02d}_n_flood_years"
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    OUT_MICRO.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_MICRO, index=False)
    print("[INFO] Notebook progress message.")
    return merged


def main():
    meta_json = find_any_meta_json()
    print(f"[META] using: {meta_json}")
    meta = load_meta(meta_json)
    print(f"[INFO] grid={meta['rows']}x{meta['cols']} compact_mode={meta['compact_mode']} compress={meta['compress']}")

    df_sch = prepare_school_points(meta)

    df_cym = build_county_year_month(meta, df_sch)

    edu = pd.read_parquet(EDU_BM_PARQUET)
    birth_min = int(pd.to_numeric(edu["birth_year"], errors="coerce").min())
    birth_max = int(pd.to_numeric(edu["birth_year"], errors="coerce").max())
    print("[INFO] Notebook progress message.")

    df_cohort_m = build_cohort_month(df_cym, birth_min, birth_max)

    merge_to_micro_wide(df_cohort_m)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

IN_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_month_exposure.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_month_mechanism_FE"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "school_month_mechanism_FE_monthly.csv"

Y_VAR = "edu_years"

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True
SAMPLES = ["rural", "urban"]

CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])

MONTH_VARS = [f"F_month{m:02d}_n_flood_years" for m in range(1, 13)]


def sig_label_one_star(p: float) -> str:
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    return "*" if p < 0.1 else ""


def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"].astype("Int64") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df


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
    return df


def prepare_sample(df_all: pd.DataFrame, sample_tag: str) -> pd.DataFrame:
    df = df_all.copy()

    num_cols = ["M2", "M38", "birth_year", "age_2015"] + CONTROL_VARS + MONTH_VARS
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)

    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()
    dfm = dfm.dropna(subset=[Y_VAR, "M2", "birth_year"])

    # prov_birth_fe
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str) + "_" +
        dfm["birth_year"].astype("Int64").astype(str)
    )

    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    for c in CONTROL_VARS:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # Original notebook comment normalized for the public code archive.
    for v in MONTH_VARS:
        if v in dfm.columns:
            dfm[v] = dfm[v].fillna(0)

    return dfm.reset_index(drop=True)


def run_monthly_regs(df_all: pd.DataFrame) -> pd.DataFrame:
    records = []
    for sample in SAMPLES:
        dfm = prepare_sample(df_all, sample)
        n = len(dfm)
        print(f"[FEOLS] sample={sample}, N={n}")
        if n < 200:
            print("[INFO] Notebook progress message.")
            continue

        for m in range(1, 13):
            xvar = f"F_month{m:02d}_n_flood_years"
            if xvar not in dfm.columns:
                print("[INFO] Notebook progress message.")
                continue

            fml = (
                f"{Y_VAR} ~ {xvar} + {CONTROL_FML} + "
                f"i(M2, birth_year_c) | M2 + prov_birth_fe"
            )

            try:
                fit = feols(fml, dfm, vcov={"CRV1": "M2"})
            except Exception as e:
                print("[INFO] Notebook progress message.")
                continue

            tidy = normalize_tidy(fit)
            row = tidy[tidy["Term"] == xvar]
            if row.empty:
                continue
            row = row.iloc[0]

            est = float(row["Estimate"])
            se  = float(row["StdError"])
            pv  = float(row["PValue"]) if "PValue" in row.index else np.nan

            records.append({
                "sample": sample,
                "month": m,
                "Term": xvar,
                "Estimate": est,
                "StdError": se,
                "PValue": pv,
                "nobs": int(n),
            })

    return pd.DataFrame(records)


def plot_month_line(df: pd.DataFrame, sample: str):
    out = OUT_DIR / f"school_month_mechanism_monthly_line_{sample}.png"
    sub = df[df["sample"] == sample].sort_values("month").copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(sig_label_one_star)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(
        sub["month"].values,
        sub["Estimate"].values,
        yerr=z * sub["StdError"].values,
        marker="o",
        linestyle="-",
        capsize=3,
        linewidth=1.4,
    )

    ax.axhline(0.0, linestyle="--", linewidth=1)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("月份")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title(f"月份—教育损失（{sample}；每个月单独回归）")

    # Original notebook comment normalized for the public code archive.
    y_range = np.nanmax(np.abs(np.r_[sub["CI_low"].values, sub["CI_high"].values]))
    if not np.isfinite(y_range) or y_range == 0:
        y_range = 1.0
    dy = 0.01 * y_range

    for x, y, e, sig in zip(sub["month"].values, sub["Estimate"].values,
                            z * sub["StdError"].values, sub["sig"].values):
        if sig:
            ax.text(x, y + e + dy, sig, ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.show()
    print(f"[DONE] {out}")


def main():
    print(f"[STEP] read: {IN_PARQUET}")
    df = pd.read_parquet(IN_PARQUET)
    print(f"[INFO] shape={df.shape}")

    res = run_monthly_regs(df)
    if res.empty:
        print("[INFO] Notebook progress message.")
        return

    res.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[DONE] saved: {OUT_CSV}")
    print(res.head())

    plot_month_line(res, "rural")
    plot_month_line(res, "urban")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =============================================================================
BASE_DIR = Path("/home/ll/jupyter_notebook/result/windows/school_periods")

IN_SLIM_PARQUET = BASE_DIR / "data" / "edu_micro_2015_BM_school_month_exposure_slim.parquet"
IN_MONTHLY_CSV  = BASE_DIR / "output" / "school_month_mechanism_FE_monthly.csv"

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
Y_VAR = "edu_years"
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True
SAMPLES = ["rural", "urban"]

CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])
MONTH_VARS = [f"F_month{m:02d}_n_flood_years" for m in range(1, 13)]


def sig_label_one_star(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    return "*" if p < 0.1 else ""


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
    return df.rename(columns=rename)


def prepare_sample(df_all: pd.DataFrame, sample_tag: str) -> pd.DataFrame:
    df = df_all.copy()
    num_cols = ["M2", "M38", "birth_year", "age_2015"] + CONTROL_VARS + MONTH_VARS + [Y_VAR]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()
    dfm = dfm.dropna(subset=[Y_VAR, "M2", "birth_year"])

    # prov_birth_fe
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str) + "_" +
        dfm["birth_year"].astype("Int64").astype(str)
    )

    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    for c in CONTROL_VARS:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # Original notebook comment normalized for the public code archive.
    for v in MONTH_VARS:
        if v in dfm.columns:
            dfm[v] = dfm[v].fillna(0)

    return dfm.reset_index(drop=True)


def run_monthly_regs_from_parquet(df_all: pd.DataFrame) -> pd.DataFrame:
    try:
        from pyfixest.estimation import feols
    except Exception as e:
        raise RuntimeError(
            "未能导入 pyfixest。若你只想画图，请先把 monthly.csv 复制到新目录；"
            "若需要在新设备回归，请安装 pyfixest 并确保依赖完整。"
        ) from e

    records = []
    for sample in SAMPLES:
        dfm = prepare_sample(df_all, sample)
        n = len(dfm)
        print(f"[FEOLS] sample={sample}, N={n}")
        if n < 200:
            print("[INFO] Notebook progress message.")
            continue

        for m in range(1, 13):
            xvar = f"F_month{m:02d}_n_flood_years"
            if xvar not in dfm.columns:
                continue

            fml = (
                f"{Y_VAR} ~ {xvar} + {CONTROL_FML} + "
                f"i(M2, birth_year_c) | M2 + prov_birth_fe"
            )

            try:
                fit = feols(fml, dfm, vcov={"CRV1": "M2"})
            except Exception as e:
                print("[INFO] Notebook progress message.")
                continue

            tidy = normalize_tidy(fit)
            row = tidy[tidy["Term"] == xvar]
            if row.empty:
                continue
            row = row.iloc[0]

            records.append({
                "sample": sample,
                "month": m,
                "Term": xvar,
                "Estimate": float(row["Estimate"]),
                "StdError": float(row["StdError"]),
                "PValue": float(row["PValue"]) if "PValue" in row.index else np.nan,
                "nobs": int(n),
            })

    return pd.DataFrame(records)


def plot_month_line(df: pd.DataFrame, sample: str):
    out = OUT_DIR / f"school_month_mechanism_monthly_line_{sample}.png"
    sub = df[df["sample"] == sample].sort_values("month").copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(sig_label_one_star)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(
        sub["month"].values,
        sub["Estimate"].values,
        yerr=z * sub["StdError"].values,
        marker="o",
        linestyle="-",
        capsize=3,
        linewidth=1.4,
    )
    ax.axhline(0.0, linestyle="--", linewidth=1)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("月份")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title(f"月份—教育损失（{sample}；每个月单独回归）")

    y_range = np.nanmax(np.abs(np.r_[sub["CI_low"].values, sub["CI_high"].values]))
    if not np.isfinite(y_range) or y_range == 0:
        y_range = 1.0
    dy = 0.01 * y_range

    for x, y, e, sig in zip(sub["month"].values, sub["Estimate"].values,
                            z * sub["StdError"].values, sub["sig"].values):
        if sig:
            ax.text(x, y + e + dy, sig, ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.close(fig)
    print(f"[DONE] {out}")


def main():
    # Original notebook comment normalized for the public code archive.
    if IN_MONTHLY_CSV.exists():
        print(f"[STEP] read monthly csv: {IN_MONTHLY_CSV}")
        res = pd.read_csv(IN_MONTHLY_CSV)
    else:
        # Original notebook comment normalized for the public code archive.
        if not IN_SLIM_PARQUET.exists():
            raise FileNotFoundError(
                f"缺少输入：{IN_MONTHLY_CSV} 与 {IN_SLIM_PARQUET} 均不存在。"
            )
        print(f"[STEP] read slim parquet: {IN_SLIM_PARQUET}")
        df = pd.read_parquet(IN_SLIM_PARQUET)

        print("[STEP] run monthly FE regressions (requires pyfixest)")
        res = run_monthly_regs_from_parquet(df)

        # Original notebook comment normalized for the public code archive.
        OUT_CSV = BASE_DIR / "output" / "school_month_mechanism_FE_monthly.csv"
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        res.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f"[DONE] saved monthly csv: {OUT_CSV}")

    # Original notebook comment normalized for the public code archive.
    plot_month_line(res, "rural")
    plot_month_line(res, "urban")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
BASE_DIR = Path("/home/ll/jupyter_notebook/result/windows/school_periods")

# =============================================================================
CSV_NEW = BASE_DIR / "output" / "school_month_mechanism_FE_monthly.csv"

# =============================================================================
CSV_ORIG = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_month_mechanism_FE/school_month_mechanism_FE_monthly.csv"
)

# =============================================================================
OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sig_label_one_star(p: float) -> str:
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    return "*" if p < 0.1 else ""


def find_input_csv() -> Path:
    # Original notebook comment normalized for the public code archive.
    if CSV_NEW.exists():
        return CSV_NEW

    # Original notebook comment normalized for the public code archive.
    if CSV_ORIG.exists():
        return CSV_ORIG

    # Original notebook comment normalized for the public code archive.
    root = Path("/home/ll/jupyter_notebook/result")
    hits = list(root.rglob("school_month_mechanism_FE_monthly.csv"))
    if hits:
        # Original notebook comment normalized for the public code archive.
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        "没有找到输入 CSV：school_month_mechanism_FE_monthly.csv\n"
        "你需要先把该 CSV 放到：\n"
        f"  {CSV_NEW}\n"
        "或确保原始输出路径存在：\n"
        f"  {CSV_ORIG}\n"
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    rename = {}
    for c in df.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc == "estimate":
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p"]:
            rename[c] = "PValue"
        elif lc == "term":
            rename[c] = "Term"
    df = df.rename(columns=rename)

    need = {"sample", "month", "Estimate", "StdError"}
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"CSV 缺少必要列：{miss}；现有列={list(df.columns)}")

    if "PValue" not in df.columns:
        df["PValue"] = np.nan

    # Original notebook comment normalized for the public code archive.
    for c in ["month", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def plot_month_line(df: pd.DataFrame, sample: str):
    out = OUT_DIR / f"school_month_mechanism_monthly_line_{sample}.png"
    sub = df[df["sample"] == sample].sort_values("month").copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(sig_label_one_star)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(
        sub["month"].values,
        sub["Estimate"].values,
        yerr=z * sub["StdError"].values,
        marker="o",
        linestyle="-",
        capsize=3,
        linewidth=1.4,
    )

    ax.axhline(0.0, linestyle="--", linewidth=1)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("月份")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title(f"月份—教育损失（{sample}）")

    # Original notebook comment normalized for the public code archive.
    y_range = np.nanmax(np.abs(np.r_[sub["CI_low"].values, sub["CI_high"].values]))
    if not np.isfinite(y_range) or y_range == 0:
        y_range = 1.0
    dy = 0.01 * y_range

    for x, y, e, sig in zip(
        sub["month"].values,
        sub["Estimate"].values,
        z * sub["StdError"].values,
        sub["sig"].values,
    ):
        if sig:
            ax.text(x, y + e + dy, sig, ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.show()
    print(f"[DONE] {out}")


def main():
    csv_path = find_input_csv()
    print("[INFO] Notebook progress message.")

    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    plot_month_line(df, "rural")
    plot_month_line(df, "urban")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
IN_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_month_exposure.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_month_joint_FE"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "school_month_joint_FE.csv"
OUT_WALD = OUT_DIR / "school_month_joint_FE_waldtests.csv"
OUT_PNG_RURAL = OUT_DIR / "school_month_joint_line_rural.png"
OUT_PNG_URBAN = OUT_DIR / "school_month_joint_line_urban.png"

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
Y_VAR = "edu_years"

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True
SAMPLES = ["rural", "urban"]

CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])

MONTH_VARS = [f"F_month{m:02d}_n_flood_years" for m in range(1, 13)]
VCOV_SPEC = {"CRV1": "M2"}  # Original notebook comment normalized for the public code archive.

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"].astype("Int64") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    if "is_migrant" not in df.columns and "M38" in df.columns:
        # Original notebook comment normalized for the public code archive.
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df

def normalize_tidy(res) -> pd.DataFrame:
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    if "PValue" not in df.columns:
        df["PValue"] = np.nan
    return df

def prepare_sample(df_all: pd.DataFrame, sample_tag: str) -> pd.DataFrame:
    df = df_all.copy()

    num_cols = ["M2", "M38", "birth_year", "age_2015"] + CONTROL_VARS + MONTH_VARS + [Y_VAR]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)

    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()
    dfm = dfm.dropna(subset=[Y_VAR, "M2", "birth_year"])

    # prov_birth_fe
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str) + "_" +
        dfm["birth_year"].astype("Int64").astype(str)
    )

    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in CONTROL_VARS:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # Original notebook comment normalized for the public code archive.
    for v in MONTH_VARS:
        if v in dfm.columns:
            dfm[v] = pd.to_numeric(dfm[v], errors="coerce").fillna(0)

    return dfm.reset_index(drop=True)

def build_R_joint_zero(coef_names, month_terms):
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    k = len(coef_names)
    idx_map = {n: i for i, n in enumerate(coef_names)}
    keep = [t for t in month_terms if t in idx_map]
    m = len(keep)
    R = np.zeros((m, k), dtype=float)
    for r, t in enumerate(keep):
        R[r, idx_map[t]] = 1.0
    q = np.zeros(m, dtype=float)
    return R, q, keep

def build_R_all_equal(coef_names, month_terms):
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    k = len(coef_names)
    idx_map = {n: i for i, n in enumerate(coef_names)}
    keep = [t for t in month_terms if t in idx_map]
    if len(keep) <= 1:
        return None, None, keep

    base = keep[0]
    m = len(keep) - 1
    R = np.zeros((m, k), dtype=float)
    for r, t in enumerate(keep[1:], start=0):
        R[r, idx_map[base]] = 1.0
        R[r, idx_map[t]] = -1.0
    q = np.zeros(m, dtype=float)
    return R, q, keep

def plot_month_line(df_coef: pd.DataFrame, sample: str, out_png: Path):
    sub = df_coef[df_coef["sample"] == sample].sort_values("month").copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.errorbar(
        sub["month"].values,
        sub["Estimate"].values,
        yerr=z * sub["StdError"].values,
        marker="o",
        linestyle="-",
        capsize=3,
        linewidth=1.4,
    )
    ax.axhline(0.0, linestyle="--", linewidth=1)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("月份")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title(f"月份异质性（{sample}；12个月联合回归）")

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close(fig)
    print(f"[DONE] {out_png}")

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def run_joint_month_model(df_all: pd.DataFrame):
    coef_records = []
    wald_records = []

    for sample in SAMPLES:
        dfm = prepare_sample(df_all, sample)
        n = len(dfm)
        print(f"[INFO] sample={sample}, N={n}")
        if n < 500:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        X_FML = " + ".join(MONTH_VARS)
        fml = (
            f"{Y_VAR} ~ {X_FML} + {CONTROL_FML} + "
            f"i(M2, birth_year_c) | M2 + prov_birth_fe"
        )

        try:
            fit = feols(fml, dfm, vcov=VCOV_SPEC)
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        tidy = normalize_tidy(fit)
        for m in range(1, 13):
            term = f"F_month{m:02d}_n_flood_years"
            row = tidy[tidy["Term"] == term]
            if row.empty:
                coef_records.append({
                    "sample": sample, "month": m, "Term": term,
                    "Estimate": np.nan, "StdError": np.nan, "PValue": np.nan,
                    "nobs": int(n), "status": "dropped_or_missing"
                })
                continue
            row = row.iloc[0]
            coef_records.append({
                "sample": sample, "month": m, "Term": term,
                "Estimate": float(row.get("Estimate", np.nan)),
                "StdError": float(row.get("StdError", np.nan)),
                "PValue": float(row.get("PValue", np.nan)),
                "nobs": int(n), "status": "ok"
            })

        # Original notebook comment normalized for the public code archive.
        coef_names = list(fit.coef().index)
        month_terms = [f"F_month{m:02d}_n_flood_years" for m in range(1, 13)]

        # Original notebook comment normalized for the public code archive.
        R0, q0, keep0 = build_R_joint_zero(coef_names, month_terms)
        if len(keep0) >= 1:
            out0 = fit.wald_test(R=R0, q=q0, distribution="F")
            wald_records.append({
                "sample": sample,
                "test": "H0: all month betas = 0",
                "n_constraints": int(R0.shape[0]),
                "kept_terms": ",".join(keep0),
                "wald_stat": float(out0.get("statistic", np.nan)) if isinstance(out0, pd.Series) else np.nan,
                "p_value": float(out0.get("p_value", np.nan)) if isinstance(out0, pd.Series) else np.nan,
                "nobs": int(n),
            })
        else:
            wald_records.append({
                "sample": sample, "test": "H0: all month betas = 0",
                "n_constraints": 0, "kept_terms": "",
                "wald_stat": np.nan, "p_value": np.nan, "nobs": int(n),
            })

        # Original notebook comment normalized for the public code archive.
        Re, qe, keepe = build_R_all_equal(coef_names, month_terms)
        if Re is not None and Re.shape[0] >= 1:
            oute = fit.wald_test(R=Re, q=qe, distribution="F")
            wald_records.append({
                "sample": sample,
                "test": "H0: all month betas equal",
                "n_constraints": int(Re.shape[0]),
                "kept_terms": ",".join(keepe),
                "wald_stat": float(oute.get("statistic", np.nan)) if isinstance(oute, pd.Series) else np.nan,
                "p_value": float(oute.get("p_value", np.nan)) if isinstance(oute, pd.Series) else np.nan,
                "nobs": int(n),
            })
        else:
            wald_records.append({
                "sample": sample, "test": "H0: all month betas equal",
                "n_constraints": 0, "kept_terms": ",".join(keepe),
                "wald_stat": np.nan, "p_value": np.nan, "nobs": int(n),
            })

    df_coef = pd.DataFrame.from_records(coef_records)
    df_wald = pd.DataFrame.from_records(wald_records)
    return df_coef, df_wald

def summarize_negative(df_coef: pd.DataFrame):
    """Archived notebook note for 03_monthly_schooling_seasonality.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    z = 1.96
    out = []
    for sample in SAMPLES:
        sub = df_coef[(df_coef["sample"] == sample) & (df_coef["status"] == "ok")].copy()
        if sub.empty:
            continue
        sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
        n_neg = int((sub["CI_high"] < 0).sum())
        out.append({"sample": sample, "n_months_CI_high_lt_0": n_neg, "n_months_total": int(len(sub))})
    return pd.DataFrame(out)

def main():
    print(f"[STEP] read: {IN_PARQUET}")
    df = pd.read_parquet(IN_PARQUET)
    print(f"[INFO] raw shape: {df.shape}")

    df_coef, df_wald = run_joint_month_model(df)

    df_coef.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    df_wald.to_csv(OUT_WALD, index=False, encoding="utf-8-sig")
    print(f"[DONE] saved coef: {OUT_CSV}")
    print(f"[DONE] saved wald: {OUT_WALD}")

    # Original notebook comment normalized for the public code archive.
    neg = summarize_negative(df_coef)
    if not neg.empty:
        print("[INFO] Months with 95% CI upper bound < 0:")
        print(neg)

    # Original notebook comment normalized for the public code archive.
    plot_month_line(df_coef, "rural", OUT_PNG_RURAL)
    plot_month_line(df_coef, "urban", OUT_PNG_URBAN)

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.
