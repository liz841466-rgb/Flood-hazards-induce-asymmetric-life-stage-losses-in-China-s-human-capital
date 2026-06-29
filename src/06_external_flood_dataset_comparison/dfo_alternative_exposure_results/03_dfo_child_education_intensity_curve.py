#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

CSV_PATH = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/"
    "flood_dfo_rep/batch_oneclick/batch_DFO_severity_spatial_sample_results.csv"
)
OUT_DIR = CSV_PATH.parent / "severity_curve_from_batch"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHA = 0.10  # Original notebook comment normalized for the public code archive.
SAMPLES = ["all", "rural", "urban"]  # Original notebook comment normalized for the public code archive.


# =============================================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def _find_col(df: pd.DataFrame, candidates, contains=False):
    cols = df.columns
    for c in candidates:
        if c in cols:
            return c
    if contains:
        for c in cols:
            cl = c.lower()
            if any(k in cl for k in candidates):
                return c
    raise KeyError(f"Cannot find column among: {candidates}")


def _get_cols(d: pd.DataFrame):
    est_col = _find_col(d, ["Estimate", "estimate"], contains=True)
    se_col = _find_col(d, ["StdError", "std.error", "std_error", "se"], contains=True)
    p_col = _find_col(d, ["PValue", "pvalue", "p_value", "Pr(>|t|)"], contains=True)
    return est_col, se_col, p_col


def parse_sev_option(x) -> float:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        v = float(str(x).strip())
        return v
    except Exception:
        return np.nan


# =============================================================================

def aggregate_across_spatial(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df.copy()

    # Original notebook comment normalized for the public code archive.
    d = d[(d["model"] == "linear") & (d["exposure_mode"] == "severe100")].copy()
    if d.empty:
        raise ValueError("筛选 severe100 & linear 后为空，请检查 CSV。")

    # Original notebook comment normalized for the public code archive.
    if "sev_option" not in d.columns:
        raise KeyError("CSV 中缺少 sev_option 列。")

    d["sev_val"] = d["sev_option"].apply(parse_sev_option)
    d = d[np.isfinite(d["sev_val"])].copy()

    if "sample_urban" not in d.columns:
        raise KeyError("CSV 中缺少 sample_urban 列。")
    if "spatial_prefix" not in d.columns:
        raise KeyError("CSV 中缺少 spatial_prefix 列。")

    est_col, se_col, p_col = _get_cols(d)

    group_cols = ["sample_urban", "sev_val"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g[est_col].to_numpy(dtype=float)
        se = g[se_col].to_numpy(dtype=float)
        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta = float(np.sum(w * est) / np.sum(w))
        se_star = float(np.sqrt(1.0 / np.sum(w)))
        t = beta / se_star if se_star > 0 else np.nan
        p = 2.0 * (1.0 - norm_cdf(abs(t))) if np.isfinite(t) else np.nan

        ci_low = beta - 1.96 * se_star
        ci_high = beta + 1.96 * se_star

        return pd.Series(
            {
                "Estimate": beta,
                "StdError": se_star,
                "PValue": p,
                "CI_low": ci_low,
                "CI_high": ci_high,
                "n_spec": len(g),
                "spatial_list": ";".join(
                    sorted(g["spatial_prefix"].astype(str).unique())
                ),
            }
        )

    df_agg = (
        d.groupby(group_cols, as_index=False)
        .apply(agg_one)
    )

    df_agg = df_agg.sort_values(["sample_urban", "sev_val"]).reset_index(drop=True)

    print("[INFO] Notebook progress message.")
    print(df_agg.head())

    return df_agg


# =============================================================================

def build_severity_points(df_agg: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = []

    for sample in sorted(df_agg["sample_urban"].unique()):
        sub = df_agg[df_agg["sample_urban"] == sample].copy()

        def pick_row(s_target):
            ss = sub[np.isclose(sub["sev_val"], s_target)]
            if ss.empty:
                return None
            return ss.iloc[0]

        r1 = pick_row(1.0)
        r15 = pick_row(1.5)
        r2 = pick_row(2.0)

        if r1 is None or r15 is None:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        rows.append(
            dict(
                sample=sample,
                sev_group="sev1",
                s=1.0,
                Estimate=r1["Estimate"],
                StdError=r1["StdError"],
                PValue=r1["PValue"],
                CI_low=r1["CI_low"],
                CI_high=r1["CI_high"],
            )
        )

        # Original notebook comment normalized for the public code archive.
        rows.append(
            dict(
                sample=sample,
                sev_group="sev1.5",
                s=1.5,
                Estimate=r15["Estimate"],
                StdError=r15["StdError"],
                PValue=r15["PValue"],
                CI_low=r15["CI_low"],
                CI_high=r15["CI_high"],
            )
        )

        # Original notebook comment normalized for the public code archive.
        if r2 is not None:
            est15 = float(r15["Estimate"])
            se15 = float(r15["StdError"])
            est2 = float(r2["Estimate"])
            se2 = float(r2["StdError"])

            var15 = max(se15 ** 2, 1e-12)
            var2 = max(se2 ** 2, 1e-12)
            w15 = 1.0 / var15
            w2 = 1.0 / var2

            beta_mix = (w15 * est15 + w2 * est2) / (w15 + w2)
            se_mix = float(np.sqrt(1.0 / (w15 + w2)))
            t_mix = beta_mix / se_mix if se_mix > 0 else np.nan
            p_mix = 2.0 * (1.0 - norm_cdf(abs(t_mix))) if np.isfinite(t_mix) else np.nan

            # Original notebook comment normalized for the public code archive.
            s_mix = float((w15 * 1.5 + w2 * 2.0) / (w15 + w2))
            ci_low = beta_mix - 1.96 * se_mix
            ci_high = beta_mix + 1.96 * se_mix

            rows.append(
                dict(
                    sample=sample,
                    sev_group="sev1.5+2",
                    s=s_mix,
                    Estimate=beta_mix,
                    StdError=se_mix,
                    PValue=p_mix,
                    CI_low=ci_low,
                    CI_high=ci_high,
                )
            )
        else:
            print("[INFO] Notebook progress message.")

    df_pts = pd.DataFrame(rows)
    df_pts = df_pts.sort_values(["sample", "s"]).reset_index(drop=True)

    print("[INFO] Notebook progress message.")
    print(df_pts.head())

    return df_pts


# =============================================================================

def plot_severity_curve(df_pts: pd.DataFrame, sample: str):
    sub = df_pts[df_pts["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub = sub.sort_values("s")
    s_vals = sub["s"].to_numpy(float)
    beta = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)
    ci_low = sub["CI_low"].to_numpy(float)
    ci_high = sub["CI_high"].to_numpy(float)
    labels = sub["sev_group"].tolist()

    if len(s_vals) < 2:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = np.nanmin(ci_low)
    y_max = np.nanmax(ci_high)
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.10 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    # Original notebook comment normalized for the public code archive.
    if len(s_vals) >= 3:
        poly = np.poly1d(np.polyfit(s_vals, beta, deg=2))
    else:
        poly = np.poly1d(np.polyfit(s_vals, beta, deg=1))

    s_grid = np.linspace(s_vals.min(), s_vals.max(), 200)
    beta_grid = poly(s_grid)

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(
        s_grid,
        beta_grid,
        color="black",
        label="β(s) 插值曲线",
    )

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([beta - ci_low, ci_high - beta])
    ax.errorbar(
        s_vals,
        beta,
        yerr=yerr,
        fmt="o",
        capsize=4,
        color="black",
        linestyle="none",
        label="sev1 / sev1.5 / sev1.5+2",
    )

    # Original notebook comment normalized for the public code archive.
    for sx, by, pv in zip(s_vals, beta, p_vals):
        star = stars_for_p(pv)
        if star and np.isfinite(by):
            ax.text(
                sx,
                by + star_offset,
                star,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Original notebook comment normalized for the public code archive.
    xticks = list(s_vals)
    xticklabels = []
    for lab, s in zip(labels, s_vals):
        if lab == "sev1":
            xticklabels.append("sev1\n(中等洪水)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(较严重洪水)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(s≈{s:.2f})")
        else:
            xticklabels.append(lab)

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(s_vals.min() - 0.05, s_vals.max() + 0.05)
    ax.set_ylim(y_lower, y_upper)

    ax.set_xlabel("DFO 严重程度 s")
    ax.set_ylabel("Coefficient on DFO share（线性模型）")
    ax.set_title(
        "DFO 严重程度非线性效应（sev1 → sev1.5 → sev1.5+2）\n"
        f"sample = {sample}"
    )

    ax.legend()
    plt.tight_layout()

    out_png = OUT_DIR / f"severity_curve_sev1_sev15_sev15plus2_sample_{sample}.png"
    plt.savefig(out_png, dpi=300)
    plt.show()
    print(f"[INFO] Saved figure: {out_png}")


# ========= main =========

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df_res = pd.read_csv(CSV_PATH)
    print(f"[INFO] Loaded batch results: {df_res.shape}")

    # Original notebook comment normalized for the public code archive.
    df_agg = aggregate_across_spatial(df_res)

    # Original notebook comment normalized for the public code archive.
    df_pts = build_severity_points(df_agg)

    if df_pts.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    for samp in SAMPLES:
        if samp not in df_pts["sample"].unique():
            print("[INFO] Notebook progress message.")
            continue
        plot_severity_curve(df_pts, sample=samp)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))

OUT_DIR = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood_dfo_rep/severity_curve_edu"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

# External flood dataset comparison note.
DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

MIN_AGE, MAX_AGE = 0, 15          # Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000 # Original notebook comment normalized for the public code archive.
AGE_MIN, AGE_MAX = 15, 35         # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"
FULL_COVER_TH = 0.99

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SEV_OPTIONS_CURVE = ["1", "1.5", ">=1.5"]
USE_SEVERITY = True
SEV_STR_KEYWORD = ""   # Original notebook comment normalized for the public code archive.

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
SAMPLES = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
CAT_COLS = ["M34", "M37", "M15", "M16"]


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc.startswith("estimate"):
            rename_map[c] = "Estimate"
        if "stderr" in lc or "stderror" in lc or "std_error" in lc or lc == "std":
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"

    res = res.rename(columns=rename_map)

    # Original notebook comment normalized for the public code archive.
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


# ================================
# External flood dataset comparison note.
# ================================
def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


def load_counties() -> gpd.GeoDataFrame:
    gdf_c = gpd.read_file(COUNTY_SHP)
    if gdf_c.crs is None:
        gdf_c = gdf_c.set_crs(epsg=4326)
    else:
        gdf_c = gdf_c.to_crs(epsg=4326)
    gdf_c = _make_valid(gdf_c)

    gdf_c["county_code"] = gdf_c[COUNTY_ID_FIELD].astype(str)

    df_area = pd.read_csv(COUNTY_AREA_CSV)
    df_area["county_code"] = df_area["county_code"].astype(str)

    gdf_c = gdf_c.merge(
        df_area[["county_id", "county_code"]],
        on="county_code",
        how="inner"
    )
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print(f"[INFO] Counties matched: {gdf_c.shape[0]}")
    return gdf_c


def load_dfo_raw() -> gpd.GeoDataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gpd.read_file(DFO_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf = _make_valid(gdf).reset_index(drop=True)
    gdf["event_id"] = np.arange(len(gdf), dtype=int)

    # Original notebook comment normalized for the public code archive.
    gdf["BEGAN_dt"] = pd.to_datetime(gdf.get("BEGAN"), errors="coerce")
    gdf["ENDED_dt"] = pd.to_datetime(gdf.get("ENDED"), errors="coerce")
    miss_end = gdf["ENDED_dt"].isna() & gdf["BEGAN_dt"].notna()
    gdf.loc[miss_end, "ENDED_dt"] = gdf.loc[miss_end, "BEGAN_dt"]

    # Original notebook comment normalized for the public code archive.
    gdf["mid_date"] = gdf["BEGAN_dt"]
    has_both = gdf["BEGAN_dt"].notna() & gdf["ENDED_dt"].notna()
    gdf.loc[has_both, "mid_date"] = (
        gdf.loc[has_both, "BEGAN_dt"]
        + (gdf.loc[has_both, "ENDED_dt"] - gdf.loc[has_both, "BEGAN_dt"]) / 2
    )
    gdf["year"] = gdf["mid_date"].dt.year
    gdf = gdf.dropna(subset=["year"]).copy()
    gdf["year"] = gdf["year"].astype(int)

    # Original notebook comment normalized for the public code archive.
    gdf["duration_days"] = (gdf["ENDED_dt"] - gdf["BEGAN_dt"]).dt.days + 1
    gdf.loc[gdf["duration_days"].isna(), "duration_days"] = 1
    gdf["duration_days"] = gdf["duration_days"].clip(lower=1)

    # Original notebook comment normalized for the public code archive.
    sev_col = None
    for c in ["SEVERITY", "Severity", "severity"]:
        if c in gdf.columns:
            sev_col = c
            break

    if sev_col is None:
        gdf["severity_raw"] = np.nan
        gdf["severity_code"] = np.nan
        print("[WARN] No severity column found in DFO.")
    else:
        gdf["severity_raw"] = gdf[sev_col]
        gdf["severity_code"] = pd.to_numeric(gdf[sev_col], errors="coerce")
        print(f"[INFO] Severity column = {sev_col}")
        print(gdf["severity_code"].value_counts(dropna=False).head())

    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) &
              (gdf["year"] <= DFO_END_YEAR)].copy()
    print(f"[INFO] DFO events {DFO_START_YEAR}-{DFO_END_YEAR}: {len(gdf)}")
    return gdf


def apply_severity_flag(gdf_raw: gpd.GeoDataFrame,
                        sev_option: str,
                        use_severity: bool = True,
                        sev_str_keyword: str = "") -> gpd.GeoDataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf_raw.copy()

    if (not use_severity) or ("severity_code" not in gdf.columns):
        gdf["is_severe_100yr"] = 0
        return gdf

    sev_num = gdf["severity_code"]
    raw = gdf.get("severity_raw", sev_num)

    if sev_option == "1":
        is_num = np.isclose(sev_num, 1.0, equal_nan=False)
    elif sev_option in ("1.5", "1_5", "1.50"):
        is_num = np.isclose(sev_num, 1.5, equal_nan=False)
    elif sev_option == "2":
        is_num = np.isclose(sev_num, 2.0, equal_nan=False)
    elif sev_option == ">=1.5":
        is_num = sev_num >= 1.5
    else:
        raise ValueError(f"Unknown sev_option={sev_option}")

    if sev_str_keyword:
        is_str = raw.astype(str).str.contains(sev_str_keyword, case=False, na=False)
    else:
        is_str = pd.Series(False, index=gdf.index)

    gdf["is_severe_100yr"] = (is_num | is_str).astype(int)
    print(f"[INFO] sev_option={sev_option}, severe events = {int(gdf['is_severe_100yr'].sum())}")
    return gdf


# ================================
# County-level processing note.
# ================================
def build_dfo_county_year_panel(gdf_dfo: gpd.GeoDataFrame,
                                gdf_c: gpd.GeoDataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()
    c_proj["area_cnt"] = c_proj.geometry.area

    # ------ 3.1 centroid baseline ------
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner",
        predicate="within"
    )
    cent_join["severe_duration_row"] = cent_join["duration_days"] * cent_join["is_severe_100yr"]

    df_cent = (
        cent_join.groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(
            flooded_times_centroid=("event_id", "nunique"),
            duration_days_centroid=("duration_days", "sum"),
            severe_times_centroid=("is_severe_100yr", "sum"),
            severe_duration_centroid=("severe_duration_row", "sum"),
        )
    )
    df_cent["flooded_any_centroid"] = (df_cent["flooded_times_centroid"] > 0).astype(int)
    df_cent["severe_any_centroid"]  = (df_cent["severe_times_centroid"] > 0).astype(int)

    # ------ 3.2 area overlay ------
    inter = gpd.overlay(
        c_proj[["county_id", "county_code", "area_cnt", "geometry"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="intersection",
        keep_geom_type=True
    )
    inter["intersect_area"] = inter.geometry.area
    inter["cover_ratio"] = inter["intersect_area"] / inter["area_cnt"]
    inter["severe_duration_row"] = inter["duration_days"] * inter["is_severe_100yr"]

    # area50
    inter_a50 = inter[inter["cover_ratio"] >= 0.5].copy()
    df_a50 = (
        inter_a50.groupby(["county_id","county_code","year"], as_index=False)
        .agg(
            flooded_times_area50=("event_id","nunique"),
            duration_days_area50=("duration_days","sum"),
            severe_times_area50=("is_severe_100yr","sum"),
            severe_duration_area50=("severe_duration_row","sum"),
        )
    )
    df_a50["flooded_any_area50"] = (df_a50["flooded_times_area50"]>0).astype(int)
    df_a50["severe_any_area50"]  = (df_a50["severe_times_area50"]>0).astype(int)

    # full-cover
    inter_full = inter[inter["cover_ratio"] >= FULL_COVER_TH].copy()
    df_fullcov = (
        inter_full.groupby(["county_id","county_code","year"], as_index=False)
        .agg(
            flooded_times_full=("event_id","nunique"),
            duration_days_full=("duration_days","sum"),
            severe_times_full=("is_severe_100yr","sum"),
            severe_duration_full=("severe_duration_row","sum"),
        )
    )
    df_fullcov["flooded_any_full"] = (df_fullcov["flooded_times_full"]>0).astype(int)
    df_fullcov["severe_any_full"]  = (df_fullcov["severe_times_full"]>0).astype(int)

    # =============================================================================
    all_counties = gdf_c[["county_id","county_code"]].drop_duplicates()
    all_years = pd.DataFrame({"year": np.arange(DFO_START_YEAR, DFO_END_YEAR+1, dtype=int)})
    full_index = (all_counties.assign(key=1)
                             .merge(all_years.assign(key=1), on="key")
                             .drop(columns="key"))

    out = (full_index
           .merge(df_cent, on=["county_id","county_code","year"], how="left")
           .merge(df_a50, on=["county_id","county_code","year"], how="left")
           .merge(df_fullcov, on=["county_id","county_code","year"], how="left"))

    val_cols = [c for c in out.columns if c not in ["county_id","county_code","year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    int_cols = [c for c in val_cols if c.startswith(
        ("flooded_", "severe_", "duration_", "flooded_times", "severe_times")
    )]
    for c in int_cols:
        out[c] = out[c].astype(int)

    print(f"[INFO] county×year panel shape: {out.shape}")
    return out


def build_county_birthyear_exposure(df_flood: pd.DataFrame,
                                    county_col="county_code") -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_flood.copy()
    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    ages = np.arange(MIN_AGE, MAX_AGE+1, dtype=int)
    rep = np.repeat(df.index.values, len(ages))
    age_vec = np.tile(ages, len(df))

    exp = df.loc[rep].copy()
    exp["age_in_year"] = age_vec
    exp["birth_year"] = exp["year"] - exp["age_in_year"]
    exp = exp[(exp["birth_year"] >= BIRTH_MIN) &
              (exp["birth_year"] <= BIRTH_MAX)].copy()

    group_cols = [county_col, "birth_year"]
    agg = {"n_years_window": ("year","nunique")}

    def add_measure(prefix):
        any_col   = f"flooded_any_{prefix}"
        sev_any   = f"severe_any_{prefix}"

        if any_col in exp.columns:
            agg[f"years_{any_col}"] = (any_col, "sum")
            agg[f"share_{any_col}"] = (any_col, "mean")

        if sev_any in exp.columns:
            agg[f"years_{sev_any}"] = (sev_any, "sum")
            agg[f"share_{sev_any}"] = (sev_any, "mean")

    for p in ["centroid", "area50", "full"]:
        add_measure(p)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()
    print(f"[INFO] county×birth_year exposure shape: {cohort.shape}")
    return cohort


def merge_exposure_to_micro(df_cohort: pd.DataFrame,
                            county_col="county_code") -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    edu = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] raw edu_micro shape: {edu.shape}")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[(edu["age_2015"] >= AGE_MIN) & (edu["age_2015"] <= AGE_MAX)]

    edu = edu[(edu["birth_year"] >= BIRTH_MIN) &
              (edu["birth_year"] <= BIRTH_MAX)].copy()

    cohort = df_cohort.copy()
    cohort[county_col] = pd.to_numeric(cohort[county_col], errors="coerce").astype("Int64")
    cohort = cohort.rename(columns={county_col:"county_code"})

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort, how="left",
        on=["county_code","birth_year"],
        validate="m:1"
    )

    exp_cols = [c for c in merged.columns
                if c.startswith(("years_","share_"))] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print(f"[INFO] merged micro shape: {merged.shape}")
    return merged


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def load_and_prepare_for_reg(df_micro: pd.DataFrame,
                             main_share: str,
                             main_years: str,
                             sample_type: str) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_micro.copy()

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16",
        "edu_years", main_share, main_years
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    mask &= (df["is_migrant"] == 0)

    # rural / urban / all
    if sample_type == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_type == "urban":
        mask &= (df["is_urban"] == 1)
    else:
        # Original notebook comment normalized for the public code archive.
        pass

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    required = ["edu_years", main_share, main_years, "M2", "birth_year"]
    cat_present = [c for c in CAT_COLS if c in dfm.columns]
    dfm = dfm.dropna(subset=required + cat_present)

    # FE: province×birth_year + county FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in cat_present:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce").astype("Int64")
        dfm[c] = dfm[c].astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.reset_index(drop=True)
    print(f"[SAMPLE] {sample_type}, main={main_share}, N={len(dfm)}")
    return dfm


def run_linear(dfm: pd.DataFrame, main_share: str):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fml = (
        f"edu_years ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].str.contains(main_share, na=False)].copy()
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
    }


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def aggregate_for_curve(df_res: pd.DataFrame, s_mix: float) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = []
    for (sample_type, sev_opt), g in df_res.groupby(["sample_type", "sev_option"]):
        est = g["Estimate"].to_numpy(dtype=float)
        se  = g["StdError"].to_numpy(dtype=float)
        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta = float(np.sum(w * est) / np.sum(w))
        se_star = float(np.sqrt(1.0 / np.sum(w)))
        t = beta / se_star if se_star > 0 else np.nan
        p = 2.0 * (1.0 - norm_cdf(abs(t))) if np.isfinite(t) else np.nan
        ci_low = beta - 1.96 * se_star
        ci_high = beta + 1.96 * se_star

        if sev_opt == "1":
            s = 1.0
            label = "sev1"
        elif sev_opt == "1.5":
            s = 1.5
            label = "sev1.5"
        elif sev_opt == ">=1.5":
            s = s_mix
            label = "sev1.5+2"
        else:
            continue

        rows.append(
            dict(
                sample_type=sample_type,
                sev_option=sev_opt,
                sev_label=label,
                s=s,
                Estimate=beta,
                StdError=se_star,
                PValue=p,
                CI_low=ci_low,
                CI_high=ci_high,
                n_spec=len(g),
            )
        )

    df_pts = pd.DataFrame(rows)
    if not df_pts.empty:
        df_pts = df_pts.sort_values(["sample_type", "s"]).reset_index(drop=True)

    print("[INFO] aggregated severity points preview:")
    print(df_pts.head())
    return df_pts


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def plot_severity_curve(df_pts: pd.DataFrame, sample_type: str):
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print(f"[WARN] sample_type={sample_type} has no points, skip plot.")
        return

    sub = sub.sort_values("s")
    s_vals = sub["s"].to_numpy(float)
    beta   = sub["Estimate"].to_numpy(float)
    se     = sub["StdError"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)
    ci_low = sub["CI_low"].to_numpy(float)
    ci_high= sub["CI_high"].to_numpy(float)
    labels = sub["sev_label"].tolist()

    if len(s_vals) < 2:
        print(f"[WARN] sample_type={sample_type} has <2 points, cannot draw curve.")
        return

    y_min = np.nanmin(ci_low)
    y_max = np.nanmax(ci_high)
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.12 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    # Original notebook comment normalized for the public code archive.
    if len(s_vals) >= 3:
        poly = np.poly1d(np.polyfit(s_vals, beta, deg=2))
    else:
        poly = np.poly1d(np.polyfit(s_vals, beta, deg=1))

    s_grid = np.linspace(s_vals.min(), s_vals.max(), 200)
    beta_grid = poly(s_grid)

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(s_grid, beta_grid, color="black", label="β(s) 插值曲线")

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([beta - ci_low, ci_high - beta])
    ax.errorbar(
        s_vals,
        beta,
        yerr=yerr,
        fmt="o",
        capsize=4,
        color="black",
        linestyle="none",
        label="sev1 / sev1.5 / sev1.5+2",
    )

    # Original notebook comment normalized for the public code archive.
    for sx, by, pv in zip(s_vals, beta, p_vals):
        star = stars_for_p(pv)
        if star and np.isfinite(by):
            ax.text(
                sx,
                by + star_offset,
                star,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Original notebook comment normalized for the public code archive.
    xticks = list(s_vals)
    xticklabels = []
    for lab, s in zip(labels, s_vals):
        if lab == "sev1":
            xticklabels.append("sev1\n(severity=1)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(severity=1.5)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(severity≥1.5, s≈{s:.2f})")
        else:
            xticklabels.append(lab)

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(s_vals.min() - 0.05, s_vals.max() + 0.05)
    ax.set_ylim(y_lower, y_upper)

    ax.set_xlabel("DFO 严重程度 s（基于 severity 定义 severe）")
    ax.set_ylabel("Coefficient on share_severe_any (线性模型)")
    ax.set_title(
        "DFO 严重程度曲线 β(s)：sev1 → sev1.5 → sev1.5+2\n"
        f"sample = {sample_type}"
    )

    ax.legend()
    plt.tight_layout()

    out_png = OUT_DIR / f"severity_curve_edu_sev1_sev15_sev15plus2_sample_{sample_type}.png"
    plt.savefig(out_png, dpi=300)
    plt.show()
    print(f"[INFO] Saved figure: {out_png}")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    # =============================================================================
    gdf_c = load_counties()
    gdf_dfo_raw = load_dfo_raw()

    # Original notebook comment normalized for the public code archive.
    if "severity_code" in gdf_dfo_raw.columns:
        mask_ge = gdf_dfo_raw["severity_code"] >= 1.5
        if mask_ge.any():
            s_mix = float(gdf_dfo_raw.loc[mask_ge, "severity_code"].mean())
        else:
            s_mix = 1.75
    else:
        s_mix = 1.75
    s_mix = min(max(s_mix, 1.5), 2.0)
    print(f"[INFO] global s_mix for severity≥1.5 ≈ {s_mix:.3f}")

    results = []

    # =============================================================================
    for sev_opt in SEV_OPTIONS_CURVE:
        print(f"\n[PIPELINE] Building micro & regressions for sev_option={sev_opt} ...")
        # External flood dataset comparison note.
        gdf_dfo = apply_severity_flag(
            gdf_dfo_raw,
            sev_option=sev_opt,
            use_severity=USE_SEVERITY,
            sev_str_keyword=SEV_STR_KEYWORD,
        )
        # 7.2.2 county×year panel
        df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
        # County-level processing note.
        df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
        # Original notebook comment normalized for the public code archive.
        df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")

        # Original notebook comment normalized for the public code archive.
        for spatial in SPATIAL_PREFIXES:
            main_share = f"share_severe_any_{spatial}"
            main_years = f"years_severe_any_{spatial}"

            if (main_share not in df_micro.columns) or (main_years not in df_micro.columns):
                print(f"[SKIP] Missing exposure cols for spatial={spatial}, sev={sev_opt}")
                continue

            for sample_type in SAMPLES:
                df_reg = load_and_prepare_for_reg(df_micro, main_share, main_years, sample_type)
                if len(df_reg) < 50:
                    print(f"[WARN] sample={sample_type}, spatial={spatial}, sev={sev_opt}: N<50, skip.")
                    continue

                lin = run_linear(df_reg, main_share)
                if lin is None:
                    print(f"[WARN] No linear coef for {main_share}, sample={sample_type}, spatial={spatial}, sev={sev_opt}")
                    continue

                results.append(
                    dict(
                        sev_option=sev_opt,
                        spatial_prefix=spatial,
                        sample_type=sample_type,
                        **lin,
                    )
                )

    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("[WARN] No regression results, abort.")
        return

    print("\n[INFO] raw regression results preview:")
    print(df_res.head())

    # =============================================================================
    df_pts = aggregate_for_curve(df_res, s_mix=s_mix)
    if df_pts.empty:
        print("[WARN] No aggregated severity points, abort.")
        return

    # Original notebook comment normalized for the public code archive.
    out_pts_csv = OUT_DIR / "severity_curve_points_edu.csv"
    df_pts.to_csv(out_pts_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Saved severity points table: {out_pts_csv}")

    # =============================================================================
    for sample_type in SAMPLES:
        if sample_type not in df_pts["sample_type"].unique():
            print(f"[INFO] sample_type={sample_type} not in df_pts, skip plotting.")
            continue
        plot_severity_curve(df_pts, sample_type=sample_type)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood_dfo_rep/severity_curve_edu_beta"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

# External flood dataset comparison note.
DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

MIN_AGE, MAX_AGE = 0, 15          # Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000 # Original notebook comment normalized for the public code archive.
AGE_MIN, AGE_MAX = 15, 35         # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"
FULL_COVER_TH = 0.99

# Original notebook comment normalized for the public code archive.
SEV_OPTIONS_CURVE = ["1", "1.5", ">=1.5"]
USE_SEVERITY = True
SEV_STR_KEYWORD = ""   # Original notebook comment normalized for the public code archive.

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
SAMPLES = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
CAT_COLS = ["M34", "M37", "M15", "M16"]


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc.startswith("estimate"):
            rename_map[c] = "Estimate"
        if "stderr" in lc or "stderror" in lc or "std_error" in lc or lc == "std":
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"

    res = res.rename(columns=rename_map)

    # Original notebook comment normalized for the public code archive.
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


# ================================
# External flood dataset comparison note.
# ================================
def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


def load_counties() -> gpd.GeoDataFrame:
    gdf_c = gpd.read_file(COUNTY_SHP)
    if gdf_c.crs is None:
        gdf_c = gdf_c.set_crs(epsg=4326)
    else:
        gdf_c = gdf_c.to_crs(epsg=4326)
    gdf_c = _make_valid(gdf_c)

    gdf_c["county_code"] = gdf_c[COUNTY_ID_FIELD].astype(str)

    df_area = pd.read_csv(COUNTY_AREA_CSV)
    df_area["county_code"] = df_area["county_code"].astype(str)

    gdf_c = gdf_c.merge(
        df_area[["county_id", "county_code"]],
        on="county_code",
        how="inner"
    )
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print(f"[INFO] Counties matched: {gdf_c.shape[0]}")
    return gdf_c


def load_dfo_raw() -> gpd.GeoDataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gpd.read_file(DFO_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf = _make_valid(gdf).reset_index(drop=True)
    gdf["event_id"] = np.arange(len(gdf), dtype=int)

    # Original notebook comment normalized for the public code archive.
    gdf["BEGAN_dt"] = pd.to_datetime(gdf.get("BEGAN"), errors="coerce")
    gdf["ENDED_dt"] = pd.to_datetime(gdf.get("ENDED"), errors="coerce")
    miss_end = gdf["ENDED_dt"].isna() & gdf["BEGAN_dt"].notna()
    gdf.loc[miss_end, "ENDED_dt"] = gdf.loc[miss_end, "BEGAN_dt"]

    # Original notebook comment normalized for the public code archive.
    gdf["mid_date"] = gdf["BEGAN_dt"]
    has_both = gdf["BEGAN_dt"].notna() & gdf["ENDED_dt"].notna()
    gdf.loc[has_both, "mid_date"] = (
        gdf.loc[has_both, "BEGAN_dt"]
        + (gdf.loc[has_both, "ENDED_dt"] - gdf.loc[has_both, "BEGAN_dt"]) / 2
    )
    gdf["year"] = gdf["mid_date"].dt.year
    gdf = gdf.dropna(subset=["year"]).copy()
    gdf["year"] = gdf["year"].astype(int)

    # Original notebook comment normalized for the public code archive.
    gdf["duration_days"] = (gdf["ENDED_dt"] - gdf["BEGAN_dt"]).dt.days + 1
    gdf.loc[gdf["duration_days"].isna(), "duration_days"] = 1
    gdf["duration_days"] = gdf["duration_days"].clip(lower=1)

    # Original notebook comment normalized for the public code archive.
    sev_col = None
    for c in ["SEVERITY", "Severity", "severity"]:
        if c in gdf.columns:
            sev_col = c
            break

    if sev_col is None:
        gdf["severity_raw"] = np.nan
        gdf["severity_code"] = np.nan
        print("[WARN] No severity column found in DFO.")
    else:
        gdf["severity_raw"] = gdf[sev_col]
        gdf["severity_code"] = pd.to_numeric(gdf[sev_col], errors="coerce")
        print(f"[INFO] Severity column = {sev_col}")
        print(gdf["severity_code"].value_counts(dropna=False).head())

    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) &
              (gdf["year"] <= DFO_END_YEAR)].copy()
    print(f"[INFO] DFO events {DFO_START_YEAR}-{DFO_END_YEAR}: {len(gdf)}")
    return gdf


def apply_severity_flag(gdf_raw: gpd.GeoDataFrame,
                        sev_option: str,
                        use_severity: bool = True,
                        sev_str_keyword: str = "") -> gpd.GeoDataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf_raw.copy()

    if (not use_severity) or ("severity_code" not in gdf.columns):
        gdf["is_severe_100yr"] = 0
        return gdf

    sev_num = gdf["severity_code"]
    raw = gdf.get("severity_raw", sev_num)

    if sev_option == "1":
        is_num = np.isclose(sev_num, 1.0, equal_nan=False)
    elif sev_option in ("1.5", "1_5", "1.50"):
        is_num = np.isclose(sev_num, 1.5, equal_nan=False)
    elif sev_option == "2":
        is_num = np.isclose(sev_num, 2.0, equal_nan=False)
    elif sev_option == ">=1.5":
        is_num = sev_num >= 1.5
    else:
        raise ValueError(f"Unknown sev_option={sev_option}")

    if sev_str_keyword:
        is_str = raw.astype(str).str.contains(sev_str_keyword, case=False, na=False)
    else:
        is_str = pd.Series(False, index=gdf.index)

    gdf["is_severe_100yr"] = (is_num | is_str).astype(int)
    print(f"[INFO] sev_option={sev_option}, severe events = {int(gdf['is_severe_100yr'].sum())}")
    return gdf


# ================================
# County-level processing note.
# ================================
def build_dfo_county_year_panel(gdf_dfo: gpd.GeoDataFrame,
                                gdf_c: gpd.GeoDataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()
    c_proj["area_cnt"] = c_proj.geometry.area

    # ------ 3.1 centroid baseline ------
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner",
        predicate="within"
    )
    cent_join["severe_duration_row"] = cent_join["duration_days"] * cent_join["is_severe_100yr"]

    df_cent = (
        cent_join.groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(
            flooded_times_centroid=("event_id", "nunique"),
            duration_days_centroid=("duration_days", "sum"),
            severe_times_centroid=("is_severe_100yr", "sum"),
            severe_duration_centroid=("severe_duration_row", "sum"),
        )
    )
    df_cent["flooded_any_centroid"] = (df_cent["flooded_times_centroid"] > 0).astype(int)
    df_cent["severe_any_centroid"]  = (df_cent["severe_times_centroid"] > 0).astype(int)

    # ------ 3.2 area overlay ------
    inter = gpd.overlay(
        c_proj[["county_id", "county_code", "area_cnt", "geometry"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="intersection",
        keep_geom_type=True
    )
    inter["intersect_area"] = inter.geometry.area
    inter["cover_ratio"] = inter["intersect_area"] / inter["area_cnt"]
    inter["severe_duration_row"] = inter["duration_days"] * inter["is_severe_100yr"]

    # area50
    inter_a50 = inter[inter["cover_ratio"] >= 0.5].copy()
    df_a50 = (
        inter_a50.groupby(["county_id","county_code","year"], as_index=False)
        .agg(
            flooded_times_area50=("event_id","nunique"),
            duration_days_area50=("duration_days","sum"),
            severe_times_area50=("is_severe_100yr","sum"),
            severe_duration_area50=("severe_duration_row","sum"),
        )
    )
    df_a50["flooded_any_area50"] = (df_a50["flooded_times_area50"]>0).astype(int)
    df_a50["severe_any_area50"]  = (df_a50["severe_times_area50"]>0).astype(int)

    # full-cover
    inter_full = inter[inter["cover_ratio"] >= FULL_COVER_TH].copy()
    df_fullcov = (
        inter_full.groupby(["county_id","county_code","year"], as_index=False)
        .agg(
            flooded_times_full=("event_id","nunique"),
            duration_days_full=("duration_days","sum"),
            severe_times_full=("is_severe_100yr","sum"),
            severe_duration_full=("severe_duration_row","sum"),
        )
    )
    df_fullcov["flooded_any_full"] = (df_fullcov["flooded_times_full"]>0).astype(int)
    df_fullcov["severe_any_full"]  = (df_fullcov["severe_times_full"]>0).astype(int)

    # =============================================================================
    all_counties = gdf_c[["county_id","county_code"]].drop_duplicates()
    all_years = pd.DataFrame({"year": np.arange(DFO_START_YEAR, DFO_END_YEAR+1, dtype=int)})
    full_index = (all_counties.assign(key=1)
                             .merge(all_years.assign(key=1), on="key")
                             .drop(columns="key"))

    out = (full_index
           .merge(df_cent, on=["county_id","county_code","year"], how="left")
           .merge(df_a50, on=["county_id","county_code","year"], how="left")
           .merge(df_fullcov, on=["county_id","county_code","year"], how="left"))

    val_cols = [c for c in out.columns if c not in ["county_id","county_code","year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    int_cols = [c for c in val_cols if c.startswith(
        ("flooded_", "severe_", "duration_", "flooded_times", "severe_times")
    )]
    for c in int_cols:
        out[c] = out[c].astype(int)

    print(f"[INFO] county×year panel shape: {out.shape}")
    return out


def build_county_birthyear_exposure(df_flood: pd.DataFrame,
                                    county_col="county_code") -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_flood.copy()
    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    ages = np.arange(MIN_AGE, MAX_AGE+1, dtype=int)
    rep = np.repeat(df.index.values, len(ages))
    age_vec = np.tile(ages, len(df))

    exp = df.loc[rep].copy()
    exp["age_in_year"] = age_vec
    exp["birth_year"] = exp["year"] - exp["age_in_year"]
    exp = exp[(exp["birth_year"] >= BIRTH_MIN) &
              (exp["birth_year"] <= BIRTH_MAX)].copy()

    group_cols = [county_col, "birth_year"]
    agg = {"n_years_window": ("year","nunique")}

    def add_measure(prefix):
        any_col   = f"flooded_any_{prefix}"
        sev_any   = f"severe_any_{prefix}"

        if any_col in exp.columns:
            agg[f"years_{any_col}"] = (any_col, "sum")
            agg[f"share_{any_col}"] = (any_col, "mean")

        if sev_any in exp.columns:
            agg[f"years_{sev_any}"] = (sev_any, "sum")
            agg[f"share_{sev_any}"] = (sev_any, "mean")

    for p in ["centroid", "area50", "full"]:
        add_measure(p)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()
    print(f"[INFO] county×birth_year exposure shape: {cohort.shape}")
    return cohort


def merge_exposure_to_micro(df_cohort: pd.DataFrame,
                            county_col="county_code") -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    edu = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] raw edu_micro shape: {edu.shape}")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[(edu["age_2015"] >= AGE_MIN) & (edu["age_2015"] <= AGE_MAX)]

    edu = edu[(edu["birth_year"] >= BIRTH_MIN) &
              (edu["birth_year"] <= BIRTH_MAX)].copy()

    cohort = df_cohort.copy()
    cohort[county_col] = pd.to_numeric(cohort[county_col], errors="coerce").astype("Int64")
    cohort = cohort.rename(columns={county_col:"county_code"})

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort, how="left",
        on=["county_code","birth_year"],
        validate="m:1"
    )

    exp_cols = [c for c in merged.columns
                if c.startswith(("years_","share_"))] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print(f"[INFO] merged micro shape: {merged.shape}")
    return merged


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def load_and_prepare_for_reg(df_micro: pd.DataFrame,
                             main_share: str,
                             main_years: str,
                             sample_type: str) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_micro.copy()

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16",
        "edu_years", main_share, main_years
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    mask &= (df["is_migrant"] == 0)

    # rural / urban / all
    if sample_type == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_type == "urban":
        mask &= (df["is_urban"] == 1)
    else:
        # Original notebook comment normalized for the public code archive.
        pass

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    required = ["edu_years", main_share, main_years, "M2", "birth_year"]
    cat_present = [c for c in CAT_COLS if c in dfm.columns]
    dfm = dfm.dropna(subset=required + cat_present)

    # FE: province×birth_year + county FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in cat_present:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce").astype("Int64")
        dfm[c] = dfm[c].astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.reset_index(drop=True)
    print(f"[SAMPLE] {sample_type}, main={main_share}, N={len(dfm)}")
    return dfm


def run_linear(dfm: pd.DataFrame, main_share: str):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fml = (
        f"edu_years ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].str.contains(main_share, na=False)].copy()
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
    }


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def aggregate_for_curve(df_res: pd.DataFrame, s_mix: float) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = []
    for (sample_type, sev_opt), g in df_res.groupby(["sample_type", "sev_option"]):
        est = g["Estimate"].to_numpy(dtype=float)
        se  = g["StdError"].to_numpy(dtype=float)
        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta = float(np.sum(w * est) / np.sum(w))
        se_star = float(np.sqrt(1.0 / np.sum(w)))
        t = beta / se_star if se_star > 0 else np.nan
        p = 2.0 * (1.0 - norm_cdf(abs(t))) if np.isfinite(t) else np.nan
        ci_low = beta - 1.96 * se_star
        ci_high = beta + 1.96 * se_star

        if sev_opt == "1":
            s = 1.0
            label = "sev1"
        elif sev_opt == "1.5":
            s = 1.5
            label = "sev1.5"
        elif sev_opt == ">=1.5":
            s = s_mix
            label = "sev1.5+2"
        else:
            continue

        rows.append(
            dict(
                sample_type=sample_type,
                sev_option=sev_opt,
                sev_label=label,
                s=s,
                Estimate=beta,
                StdError=se_star,
                PValue=p,
                CI_low=ci_low,
                CI_high=ci_high,
                n_spec=len(g),
            )
        )

    df_pts = pd.DataFrame(rows)
    if not df_pts.empty:
        df_pts = df_pts.sort_values(["sample_type", "s"]).reset_index(drop=True)

    print("[INFO] aggregated severity points preview:")
    print(df_pts.head())
    return df_pts


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_continuous_beta_from_points(sub: pd.DataFrame):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("至少需要 2 个严重程度点才能构造连续 β(s)。")

    # Original notebook comment normalized for the public code archive.
    deg = n - 1

    # Original notebook comment normalized for the public code archive.
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T   # shape (n, deg+1)

    # Original notebook comment normalized for the public code archive.
    var_vals = se_vals**2
    var_vals[var_vals <= 0] = 1e-12
    Cov_B = np.diag(var_vals)

    # Original notebook comment normalized for the public code archive.
    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals          # (deg+1,)
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    # Original notebook comment normalized for the public code archive.
    s_min, s_max = float(s_vals.min()), float(s_vals.max())
    s_grid = np.linspace(s_min, s_max, 201)

    # Original notebook comment normalized for the public code archive.
    Phi = np.vstack([s_grid**k for k in range(deg + 1)]).T   # (len_grid, deg+1)

    beta_grid = Phi @ gamma                                  # (len_grid,)
    # Original notebook comment normalized for the public code archive.
    var_grid = np.einsum("ij,jk,ik->i", Phi, Cov_gamma, Phi)
    var_grid = np.maximum(var_grid, 0.0)
    se_grid = np.sqrt(var_grid)

    ci_low_grid = beta_grid - 1.96 * se_grid
    ci_high_grid = beta_grid + 1.96 * se_grid

    return s_grid, beta_grid, ci_low_grid, ci_high_grid, gamma, Cov_gamma


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def plot_severity_curve(df_pts: pd.DataFrame, sample_type: str):
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print(f"[WARN] sample_type={sample_type} has no points, skip plot.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(float)
    beta   = sub["Estimate"].to_numpy(float)
    se     = sub["StdError"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)
    ci_low = sub["CI_low"].to_numpy(float)
    ci_high= sub["CI_high"].to_numpy(float)
    labels = sub["sev_label"].tolist()

    if len(s_vals) < 2:
        print(f"[WARN] sample_type={sample_type} has <2 points, cannot draw curve.")
        return

    # =============================================================================
    try:
        s_grid, beta_grid, ci_low_grid, ci_high_grid, gamma, Cov_gamma = \
            build_continuous_beta_from_points(sub)
    except Exception as e:
        print(f"[WARN] build_continuous_beta_from_points failed for sample={sample_type}: {e}")
        return

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    y_min = np.nanmin([ci_low.min(), ci_low_grid.min()])
    y_max = np.nanmax([ci_high.max(), ci_high_grid.max()])
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.12 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(s_grid, beta_grid, label="β(s) 连续函数")
    ax.fill_between(s_grid, ci_low_grid, ci_high_grid, alpha=0.25, label="95% CI (β(s))")

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([beta - ci_low, ci_high - beta])
    ax.errorbar(
        s_vals,
        beta,
        yerr=yerr,
        fmt="o",
        capsize=4,
        linestyle="none",
        color="black",
        label="sev1 / sev1.5 / sev1.5+2",
    )

    # Original notebook comment normalized for the public code archive.
    for sx, by, pv in zip(s_vals, beta, p_vals):
        star = stars_for_p(pv)
        if star and np.isfinite(by):
            ax.text(
                sx,
                by + star_offset,
                star,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Original notebook comment normalized for the public code archive.
    xticks = list(s_vals)
    xticklabels = []
    for lab, s in zip(labels, s_vals):
        if lab == "sev1":
            xticklabels.append("sev1\n(severity=1)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(severity=1.5)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(severity≥1.5, s≈{s:.2f})")
        else:
            xticklabels.append(lab)

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(s_vals.min() - 0.05, s_vals.max() + 0.05)
    ax.set_ylim(y_lower, y_upper)

    ax.set_xlabel("DFO 严重程度 s（基于 severity 定义 severe）")
    ax.set_ylabel("Coefficient on share_severe_any (线性模型)")
    ax.set_title(
        "DFO 严重程度连续效应 β(s)：sev1 → sev1.5 → sev1.5+2\n"
        f"sample = {sample_type}"
    )

    ax.legend()
    plt.tight_layout()

    out_png = OUT_DIR / f"severity_curve_edu_beta_sample_{sample_type}.png"
    plt.savefig(out_png, dpi=300)
    plt.show()
    print(f"[INFO] Saved figure: {out_png}")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    # =============================================================================
    gdf_c = load_counties()
    gdf_dfo_raw = load_dfo_raw()

    # Original notebook comment normalized for the public code archive.
    if "severity_code" in gdf_dfo_raw.columns:
        mask_ge = gdf_dfo_raw["severity_code"] >= 1.5
        if mask_ge.any():
            s_mix = float(gdf_dfo_raw.loc[mask_ge, "severity_code"].mean())
        else:
            s_mix = 1.75
    else:
        s_mix = 1.75
    s_mix = min(max(s_mix, 1.5), 2.0)
    print(f"[INFO] global s_mix for severity≥1.5 ≈ {s_mix:.3f}")

    results = []

    # =============================================================================
    for sev_opt in SEV_OPTIONS_CURVE:
        print(f"\n[PIPELINE] Building micro & regressions for sev_option={sev_opt} ...")
        # External flood dataset comparison note.
        gdf_dfo = apply_severity_flag(
            gdf_dfo_raw,
            sev_option=sev_opt,
            use_severity=USE_SEVERITY,
            sev_str_keyword=SEV_STR_KEYWORD,
        )
        # 8.2.2 county×year panel
        df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
        # County-level processing note.
        df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
        # Original notebook comment normalized for the public code archive.
        df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")

        # Original notebook comment normalized for the public code archive.
        for spatial in SPATIAL_PREFIXES:
            main_share = f"share_severe_any_{spatial}"
            main_years = f"years_severe_any_{spatial}"

            if (main_share not in df_micro.columns) or (main_years not in df_micro.columns):
                print(f"[SKIP] Missing exposure cols for spatial={spatial}, sev={sev_opt}")
                continue

            for sample_type in SAMPLES:
                df_reg = load_and_prepare_for_reg(df_micro, main_share, main_years, sample_type)
                if len(df_reg) < 50:
                    print(f"[WARN] sample={sample_type}, spatial={spatial}, sev={sev_opt}: N<50, skip.")
                    continue

                lin = run_linear(df_reg, main_share)
                if lin is None:
                    print(f"[WARN] No linear coef for {main_share}, sample={sample_type}, spatial={spatial}, sev={sev_opt}")
                    continue

                results.append(
                    dict(
                        sev_option=sev_opt,
                        spatial_prefix=spatial,
                        sample_type=sample_type,
                        **lin,
                    )
                )

    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("[WARN] No regression results, abort.")
        return

    print("\n[INFO] raw regression results preview:")
    print(df_res.head())

    # Original notebook comment normalized for the public code archive.
    out_reg_csv = OUT_DIR / "severity_curve_edu_beta_reg_results.csv"
    df_res.to_csv(out_reg_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Saved regression results: {out_reg_csv}")

    # =============================================================================
    df_pts = aggregate_for_curve(df_res, s_mix=s_mix)
    if df_pts.empty:
        print("[WARN] No aggregated severity points, abort.")
        return

    # Original notebook comment normalized for the public code archive.
    out_pts_csv = OUT_DIR / "severity_curve_edu_beta_points.csv"
    df_pts.to_csv(out_pts_csv, index=False, encoding="utf-8-sig")
    print(f"[INFO] Saved severity points table: {out_pts_csv}")

    # =============================================================================
    for sample_type in SAMPLES:
        if sample_type not in df_pts["sample_type"].unique():
            print(f"[INFO] sample_type={sample_type} not in df_pts, skip plotting.")
            continue
        plot_severity_curve(df_pts, sample_type=sample_type)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"  # Original notebook comment normalized for the public code archive.
OUT_DIR = Path(BASE_DIR) / "result/impact_assessment/flood_dfo_rep/severity_curve_edu_beta"

PTS_CSV = OUT_DIR / "severity_curve_edu_beta_points.csv"     # Original notebook comment normalized for the public code archive.
REG_CSV = OUT_DIR / "severity_curve_edu_beta_reg_results.csv"  # Original notebook comment normalized for the public code archive.


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def stars_for_p(p):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_continuous_beta_from_points(sub: pd.DataFrame):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("至少需要 2 个严重程度点才能构造连续 β(s)。")

    # Original notebook comment normalized for the public code archive.
    deg = n - 1

    # Original notebook comment normalized for the public code archive.
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T   # shape (n, deg+1)

    # Original notebook comment normalized for the public code archive.
    var_vals = se_vals**2
    var_vals[var_vals <= 0] = 1e-12
    Cov_B = np.diag(var_vals)

    # Original notebook comment normalized for the public code archive.
    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals          # (deg+1,)
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    # Original notebook comment normalized for the public code archive.
    s_min, s_max = float(s_vals.min()), float(s_vals.max())
    s_grid = np.linspace(s_min, s_max, 201)

    # Original notebook comment normalized for the public code archive.
    Phi = np.vstack([s_grid**k for k in range(deg + 1)]).T   # (len_grid, deg+1)

    # Original notebook comment normalized for the public code archive.
    beta_grid = Phi @ gamma
    # Original notebook comment normalized for the public code archive.
    var_grid = np.einsum("ij,jk,ik->i", Phi, Cov_gamma, Phi)
    var_grid = np.maximum(var_grid, 0.0)
    se_grid = np.sqrt(var_grid)

    ci_low_grid = beta_grid - 1.96 * se_grid
    ci_high_grid = beta_grid + 1.96 * se_grid

    return (
        s_vals,        # Original notebook comment normalized for the public code archive.
        beta_vals,     # Original notebook comment normalized for the public code archive.
        se_vals,       # Original notebook comment normalized for the public code archive.
        s_grid,        # Original notebook comment normalized for the public code archive.
        beta_grid,     # Original notebook comment normalized for the public code archive.
        ci_low_grid,   # Original notebook comment normalized for the public code archive.
        ci_high_grid,  # Original notebook comment normalized for the public code archive.
        gamma,         # Original notebook comment normalized for the public code archive.
        Cov_gamma,     # Original notebook comment normalized for the public code archive.
    )


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def plot_severity_curve_for_sample(df_pts: pd.DataFrame, sample_type: str):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub.sort_values("s").copy()

    # Original notebook comment normalized for the public code archive.
    (
        s_vals,
        beta_vals,
        se_vals,
        s_grid,
        beta_grid,
        ci_low_grid,
        ci_high_grid,
        gamma,
        Cov_gamma,
    ) = build_continuous_beta_from_points(sub)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    ci_low_points = sub["CI_low"].to_numpy(dtype=float)
    ci_high_points = sub["CI_high"].to_numpy(dtype=float)
    labels = sub["sev_label"].tolist()
    p_vals = sub["PValue"].to_numpy(dtype=float)

    # Original notebook comment normalized for the public code archive.
    y_min = np.nanmin([ci_low_points.min(), ci_low_grid.min()])
    y_max = np.nanmax([ci_high_points.max(), ci_high_grid.max()])
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.12 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(s_grid, beta_grid, color="black",label="β(s) 连续函数")
    ax.fill_between(s_grid, ci_low_grid, ci_high_grid,
                            color="red",
                            alpha=0.18, label="95% CI (β(s))")

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([
        beta_vals - ci_low_points,
        ci_high_points - beta_vals,
    ])
    ax.errorbar(
        s_vals,
        beta_vals,
        yerr=yerr,
        fmt="o",
        capsize=4,
        linestyle="none",
        color="black",
        label="sev1 / sev1.5 / sev1.5+2",
    )

    # Original notebook comment normalized for the public code archive.
    for sx, by, pv in zip(s_vals, beta_vals, p_vals):
        star = stars_for_p(pv)
        if star and np.isfinite(by):
            ax.text(
                sx,
                by + star_offset,
                star,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Original notebook comment normalized for the public code archive.
    xticks = list(s_vals)
    xticklabels = []
    for lab, s in zip(labels, s_vals):
        if lab == "sev1":
            xticklabels.append("sev1\n(severity=1)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(severity=1.5)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(severity≥1.5,\ns≈{s:.2f})")
        else:
            xticklabels.append(lab)

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(s_vals.min() - 0.05, s_vals.max() + 0.05)
    ax.set_ylim(y_lower, y_upper)

    ax.set_xlabel("DFO 严重程度 s（基于 severity 定义 severe）")
    ax.set_ylabel("Coefficient on share_severe_any (线性模型)")
    ax.set_title(
        "DFO 严重程度连续效应 β(s)：sev1 → sev1.5 → sev1.5+2\n"
        f"sample = {sample_type}"
    )

    ax.legend()
    plt.tight_layout()

    # Original notebook comment normalized for the public code archive.
    out_png = OUT_DIR / f"severity_curve_edu_beta_sample_{sample_type}.png"
    plt.savefig(out_png, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    # Original notebook comment normalized for the public code archive.
    if not PTS_CSV.exists():
        raise FileNotFoundError(f"未找到点表文件：{PTS_CSV}")
    df_pts = pd.read_csv(PTS_CSV)

    print("[INFO] Notebook progress message.")
    print(df_pts.head())

    # Original notebook comment normalized for the public code archive.
    for sample_type in ["all", "rural", "urban"]:
        if sample_type not in df_pts["sample_type"].unique():
            print("[INFO] Notebook progress message.")
            continue
        print("[INFO] Notebook progress message.")
        plot_severity_curve_for_sample(df_pts, sample_type)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import statsmodels.api as sm


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))

OUT_DIR = Path(os.path.join(
    BASE_DIR,
    "result/impact_assessment/flood_dfo_rep",
    "severity_poly_beta"
))
OUT_DIR.mkdir(parents=True, exist_ok=True)

# External flood dataset comparison note.
DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015
MIN_AGE, MAX_AGE = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"
FULL_COVER_TH = 0.99

# Original notebook comment normalized for the public code archive.
AGE_MIN_2015, AGE_MAX_2015 = 15, 35

# Original notebook comment normalized for the public code archive.
S_MIN, S_MAX = 1.0, 2.0

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# ================================
# External flood dataset comparison note.
# ================================
def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


def load_counties() -> gpd.GeoDataFrame:
    gdf_c = gpd.read_file(COUNTY_SHP)
    if gdf_c.crs is None:
        gdf_c = gdf_c.set_crs(epsg=4326)
    else:
        gdf_c = gdf_c.to_crs(epsg=4326)
    gdf_c = _make_valid(gdf_c)

    gdf_c["county_code"] = gdf_c[COUNTY_ID_FIELD].astype(str)

    df_area = pd.read_csv(COUNTY_AREA_CSV)
    df_area["county_code"] = df_area["county_code"].astype(str)

    gdf_c = gdf_c.merge(
        df_area[["county_id", "county_code"]],
        on="county_code",
        how="inner"
    )
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print("[INFO] Notebook progress message.")
    return gdf_c


def load_dfo_with_severity() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DFO_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)
    gdf = _make_valid(gdf).reset_index(drop=True)

    gdf["event_id"] = np.arange(len(gdf), dtype=int)

    # Original notebook comment normalized for the public code archive.
    gdf["BEGAN_dt"] = pd.to_datetime(gdf.get("BEGAN"), errors="coerce")
    gdf["ENDED_dt"] = pd.to_datetime(gdf.get("ENDED"), errors="coerce")
    miss_end = gdf["ENDED_dt"].isna() & gdf["BEGAN_dt"].notna()
    gdf.loc[miss_end, "ENDED_dt"] = gdf.loc[miss_end, "BEGAN_dt"]

    # Original notebook comment normalized for the public code archive.
    gdf["mid_date"] = gdf["BEGAN_dt"]
    has_both = gdf["BEGAN_dt"].notna() & gdf["ENDED_dt"].notna()
    gdf.loc[has_both, "mid_date"] = (
        gdf.loc[has_both, "BEGAN_dt"]
        + (gdf.loc[has_both, "ENDED_dt"] - gdf.loc[has_both, "BEGAN_dt"]) / 2
    )
    gdf["year"] = gdf["mid_date"].dt.year
    gdf = gdf.dropna(subset=["year"]).copy()
    gdf["year"] = gdf["year"].astype(int)

    # Original notebook comment normalized for the public code archive.
    gdf["duration_days"] = (gdf["ENDED_dt"] - gdf["BEGAN_dt"]).dt.days + 1
    gdf.loc[gdf["duration_days"].isna(), "duration_days"] = 1
    gdf["duration_days"] = gdf["duration_days"].clip(lower=1)

    # Original notebook comment normalized for the public code archive.
    sev_col = None
    for c in ["SEVERITY", "Severity", "severity"]:
        if c in gdf.columns:
            sev_col = c
            break

    if sev_col is None:
        print("[INFO] Notebook progress message.")
        gdf["severity_code"] = np.nan
    else:
        sev_num = pd.to_numeric(gdf[sev_col], errors="coerce")
        gdf["severity_code"] = sev_num
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        print(sev_num.value_counts(dropna=False).head())

    # Original notebook comment normalized for the public code archive.
    sev_num = gdf["severity_code"]
    gdf["sev1_flag"]  = np.isclose(sev_num, 1.0,  equal_nan=False).astype(int)
    gdf["sev15_flag"] = np.isclose(sev_num, 1.5, equal_nan=False).astype(int)
    gdf["sev2_flag"]  = np.isclose(sev_num, 2.0,  equal_nan=False).astype(int)

    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) & (gdf["year"] <= DFO_END_YEAR)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# ================================
# External flood dataset comparison note.
# ================================
def build_dfo_county_year_severity(
    gdf_dfo: gpd.GeoDataFrame,
    gdf_c: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")

    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()
    c_proj["area_cnt"] = c_proj.geometry.area

    # ---------- 3.1 centroid ----------
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[
            ["event_id", "year", "severity_code", "sev1_flag", "sev15_flag", "sev2_flag", "geometry"]
        ],
        how="inner",
        predicate="within"
    )

    df_cent = (
        cent_join.groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(
            flooded_times_centroid=("event_id", "nunique"),
            sev1_years_centroid=("sev1_flag", "sum"),
            sev15_years_centroid=("sev15_flag", "sum"),
            sev2_years_centroid=("sev2_flag", "sum"),
        )
    )
    df_cent["flooded_any_centroid"] = (df_cent["flooded_times_centroid"] > 0).astype(int)
    df_cent["sev1_any_centroid"]    = (df_cent["sev1_years_centroid"] > 0).astype(int)
    df_cent["sev15_any_centroid"]   = (df_cent["sev15_years_centroid"] > 0).astype(int)
    df_cent["sev2_any_centroid"]    = (df_cent["sev2_years_centroid"] > 0).astype(int)

    # =============================================================================
    inter = gpd.overlay(
        c_proj[["county_id", "county_code", "area_cnt", "geometry"]],
        dfo_proj[
            ["event_id", "year", "severity_code", "sev1_flag", "sev15_flag", "sev2_flag", "geometry"]
        ],
        how="intersection",
        keep_geom_type=True
    )
    inter["intersect_area"] = inter.geometry.area
    inter["cover_ratio"] = inter["intersect_area"] / inter["area_cnt"]

    # area50
    inter_a50 = inter[inter["cover_ratio"] >= 0.5].copy()
    df_a50 = (
        inter_a50.groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(
            flooded_times_area50=("event_id", "nunique"),
            sev1_years_area50=("sev1_flag", "sum"),
            sev15_years_area50=("sev15_flag", "sum"),
            sev2_years_area50=("sev2_flag", "sum"),
        )
    )
    df_a50["flooded_any_area50"] = (df_a50["flooded_times_area50"] > 0).astype(int)
    df_a50["sev1_any_area50"]    = (df_a50["sev1_years_area50"] > 0).astype(int)
    df_a50["sev15_any_area50"]   = (df_a50["sev15_years_area50"] > 0).astype(int)
    df_a50["sev2_any_area50"]    = (df_a50["sev2_years_area50"] > 0).astype(int)

    # full-cover
    inter_full = inter[inter["cover_ratio"] >= FULL_COVER_TH].copy()
    df_full = (
        inter_full.groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(
            flooded_times_full=("event_id", "nunique"),
            sev1_years_full=("sev1_flag", "sum"),
            sev15_years_full=("sev15_flag", "sum"),
            sev2_years_full=("sev2_flag", "sum"),
        )
    )
    df_full["flooded_any_full"] = (df_full["flooded_times_full"] > 0).astype(int)
    df_full["sev1_any_full"]    = (df_full["sev1_years_full"] > 0).astype(int)
    df_full["sev15_any_full"]   = (df_full["sev15_years_full"] > 0).astype(int)
    df_full["sev2_any_full"]    = (df_full["sev2_years_full"] > 0).astype(int)

    # =============================================================================
    all_counties = gdf_c[["county_id", "county_code"]].drop_duplicates()
    all_years = pd.DataFrame({
        "year": np.arange(DFO_START_YEAR, DFO_END_YEAR + 1, dtype=int)
    })

    full_index = (
        all_counties.assign(key=1)
        .merge(all_years.assign(key=1), on="key")
        .drop(columns="key")
    )

    out = (
        full_index
        .merge(df_cent,  on=["county_id", "county_code", "year"], how="left")
        .merge(df_a50,   on=["county_id", "county_code", "year"], how="left")
        .merge(df_full,  on=["county_id", "county_code", "year"], how="left")
    )

    val_cols = [c for c in out.columns if c not in ["county_id", "county_code", "year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return out


# ================================
# County-level processing note.
# ================================
def build_cohort_severity_exposure(
    df_cy: pd.DataFrame,
    county_col: str = "county_code"
) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_cy.copy()
    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    ages = np.arange(MIN_AGE, MAX_AGE + 1, dtype=int)
    rep = np.repeat(df.index.values, len(ages))
    age_vec = np.tile(ages, len(df))

    exp = df.loc[rep].copy()
    exp["age_in_year"] = age_vec
    exp["birth_year"] = exp["year"] - exp["age_in_year"]

    exp = exp[
        (exp["birth_year"] >= BIRTH_MIN) & (exp["birth_year"] <= BIRTH_MAX)
    ].copy()

    group_cols = [county_col, "birth_year"]
    agg = {
        "n_years_window": ("year", "nunique"),
    }

    def add_sev_measure(sev_label: str, prefix: str):
        col_any = f"{sev_label}_any_{prefix}"   # e.g. sev1_any_centroid
        if col_any in exp.columns:
            agg[f"years_{col_any}"] = (col_any, "sum")
            agg[f"share_{col_any}"] = (col_any, "mean")

    for sev_label in ["sev1", "sev15", "sev2"]:
        for prefix in ["centroid", "area50", "full"]:
            add_sev_measure(sev_label, prefix)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()

    print("[INFO] Notebook progress message.")
    return cohort


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def merge_severity_to_micro(df_cohort: pd.DataFrame) -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[edu["age_2015"].between(AGE_MIN_2015, AGE_MAX_2015)]

    edu = edu[
        (edu["birth_year"] >= BIRTH_MIN) & (edu["birth_year"] <= BIRTH_MAX)
    ].copy()

    cohort = df_cohort.copy()
    cohort["county_code"] = pd.to_numeric(
        cohort["county_code"], errors="coerce"
    ).astype("Int64")

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort,
        how="left",
        left_on=["county_code", "birth_year"],
        right_on=["county_code", "birth_year"],
        validate="m:1",
    )

    # Original notebook comment normalized for the public code archive.
    exp_cols = [
        c for c in merged.columns
        if c.startswith(("years_sev", "share_sev"))
    ] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return merged


def build_agg_poly_exposure(df_micro: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_micro.copy()

    # Original notebook comment normalized for the public code archive.
    sev1_cols = [c for c in df.columns if c.startswith("share_sev1_any_")]
    sev15_cols = [c for c in df.columns if c.startswith("share_sev15_any_")]
    sev2_cols = [c for c in df.columns if c.startswith("share_sev2_any_")]

    if not sev1_cols or not sev15_cols or not sev2_cols:
        raise ValueError("严重度 share 列不齐全，请检查 cohort 暴露构造。")

    df["E1_agg"] = df[sev1_cols].mean(axis=1, skipna=True)
    df["E15_agg"] = df[sev15_cols].mean(axis=1, skipna=True)
    df["E2_agg"] = df[sev2_cols].mean(axis=1, skipna=True)

    df[["E1_agg", "E15_agg", "E2_agg"]] = df[["E1_agg", "E15_agg", "E2_agg"]].fillna(0.0)
    df[["E1_agg", "E15_agg", "E2_agg"]] = df[["E1_agg", "E15_agg", "E2_agg"]].astype("float64")

    # Original notebook comment normalized for the public code archive.
    df["X0"] = df["E1_agg"] + df["E15_agg"] + df["E2_agg"]
    df["X1"] = 1.0 * df["E1_agg"] + 1.5 * df["E15_agg"] + 2.0 * df["E2_agg"]
    df["X2"] = 1.0**2 * df["E1_agg"] + 1.5**2 * df["E15_agg"] + 2.0**2 * df["E2_agg"]

    return df


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


def prepare_micro_for_fe(df_micro_poly: pd.DataFrame) -> pd.DataFrame:
    df = df_micro_poly.copy()

    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")
    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        df = df[df["age_2015"].between(AGE_MIN_2015, AGE_MAX_2015)]

    df = df[
        (df["birth_year"] >= BIRTH_MIN) & (df["birth_year"] <= BIRTH_MAX)
    ].copy()

    df = build_is_urban_is_migrant(df)

    # Original notebook comment normalized for the public code archive.
    df = df[df["is_migrant"] == 0].copy()

    # Fixed-effects regression helper.
    df["prov_code"] = (df["M2"] // 10000).astype(int)
    df["prov_birth_fe"] = (
        df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    )

    df["birth_year_c"] = df["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in ["E1_agg", "E15_agg", "E2_agg", "X0", "X1", "X2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype("float64")

    df["edu_years"] = df["edu_years"].astype("float64")

    print("[INFO] Notebook progress message.")
    return df


# ================================
# County-level processing note.
# ================================
def demean_two_fe(df: pd.DataFrame, cols, fe1: str, fe2: str) -> pd.DataFrame:
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    X = df[cols].astype("float64")

    g1_means = X.groupby(df[fe1]).transform("mean")
    g2_means = X.groupby(df[fe2]).transform("mean")
    mu = X.mean()

    X_dm = X - g1_means - g2_means + mu
    X_dm.columns = [f"{c}_dm" for c in cols]

    df = pd.concat([df, X_dm], axis=1)
    return df


def fe_reg_twoFE_county_cluster(
    df: pd.DataFrame,
    y_col: str,
    x_cols,
    fe1: str,
    fe2: str,
    cluster_col: str
):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].astype("float64")
    X_dm_cols = [f"{c}_dm" for c in x_cols]
    X = df[X_dm_cols].astype("float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

    return fit


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def run_poly_severity_beta_curve(df_micro_poly: pd.DataFrame):
    """Archived notebook note for 03_dfo_child_education_intensity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = prepare_micro_for_fe(df_micro_poly)

    sample_specs = {
        "all":   None,
        "rural": 0,
        "urban": 1,
    }

    for sample_name, urb_val in sample_specs.items():
        if urb_val is None:
            sub = df.copy()
        else:
            sub = df[df["is_urban"] == urb_val].copy()

        if len(sub) < 500 or sub["M2"].nunique() < 30:
            print(
                f"[WARN] sample={sample_name} 样本量或县数过小 "
                f"(N={len(sub)}, N_county={sub['M2'].nunique()}), 跳过。"
            )
            continue

        # Original notebook comment normalized for the public code archive.
        sev_ge = sub["E15_agg"] + sub["E2_agg"]
        mask_ge = sev_ge > 0
        if mask_ge.any():
            s_mix_vals = (
                (1.5 * sub.loc[mask_ge, "E15_agg"] + 2.0 * sub.loc[mask_ge, "E2_agg"])
                / sev_ge[mask_ge]
            )
            s_mix = float(s_mix_vals.mean())
        else:
            s_mix = 1.75
        s_mix = min(max(s_mix, 1.5), 2.0)
        print("[INFO] Notebook progress message.")

        # Fixed-effects regression helper.
        x_cols = ["X0", "X1", "X2", "birth_year_c"]
        fit = fe_reg_twoFE_county_cluster(
            sub,
            y_col="edu_years",
            x_cols=x_cols,
            fe1="M2",
            fe2="prov_birth_fe",
            cluster_col="M2",
        )

        # Original notebook comment normalized for the public code archive.
        gamma_idx = [f"{c}_dm" for c in ["X0", "X1", "X2"]]
        missing = [g for g in gamma_idx if g not in fit.params.index]
        if missing:
            raise KeyError(f"回归结果中缺少参数列: {missing}")

        gamma = fit.params[gamma_idx].to_numpy(dtype="float64")
        Sigma = fit.cov_params().loc[gamma_idx, gamma_idx].to_numpy(dtype="float64")

        print("[INFO] Notebook progress message.")
        print(fit.params[gamma_idx])

        # Original notebook comment normalized for the public code archive.
        s_grid = np.linspace(S_MIN, S_MAX, 201)
        beta_s, se_s = [], []

        for s in s_grid:
            v = np.array([1.0, s, s**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            se_b = float(np.sqrt(var_b))
            beta_s.append(b)
            se_s.append(se_b)

        beta_s = np.array(beta_s)
        se_s = np.array(se_s)
        ci_low = beta_s - 1.96 * se_s
        ci_high = beta_s + 1.96 * se_s

        # Original notebook comment normalized for the public code archive.
        s_points = np.array([1.0, 1.5, s_mix], dtype="float64")
        labels = ["sev1", "sev1.5", "sev1.5+2"]

        beta_pts, se_pts, p_pts = [], [], []

        for s in s_points:
            v = np.array([1.0, s, s**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            se_b = float(np.sqrt(var_b))
            if se_b > 0:
                t_b = b / se_b
                p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
            else:
                p_b = np.nan
            beta_pts.append(b)
            se_pts.append(se_b)
            p_pts.append(p_b)

        beta_pts = np.array(beta_pts)
        se_pts = np.array(se_pts)
        ci_pts_low = beta_pts - 1.96 * se_pts
        ci_pts_high = beta_pts + 1.96 * se_pts

        # =============================================================================
        fig, ax = plt.subplots(figsize=(6, 4))

        # Original notebook comment normalized for the public code archive.
        ax.plot(s_grid, beta_s, label="β(s) 估计")
        ax.fill_between(s_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        # Original notebook comment normalized for the public code archive.
        ax.errorbar(
            s_points,
            beta_pts,
            yerr=[beta_pts - ci_pts_low, ci_pts_high - beta_pts],
            fmt="o",
            capsize=4,
            linestyle="none",
            color="black",
            label="sev1 / sev1.5 / sev1.5+2"
        )

        # Original notebook comment normalized for the public code archive.
        y_range = (ci_high.max() - ci_low.min())
        y_range = y_range if y_range > 0 else 1.0
        offset = 0.03 * y_range

        for sx, by, pp, lab in zip(s_points, beta_pts, p_pts, labels):
            star = stars_for_p(pp)
            if star:
                ax.text(
                    sx,
                    by + offset,
                    star,
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlim(S_MIN, S_MAX)
        ax.set_xlabel("DFO 洪水严重程度 s（1=sev1, 1.5=sev1.5, 2=sev2）")
        ax.set_ylabel("边际效应 β(s)：严重度为 s 的 DFO 暴露对受教育年限的影响")

        ax.set_title(
            "DFO 严重程度 s 的非线性效应 β(s)\n"
            f"(儿童教育，sample={sample_name})"
        )

        ax.set_xticks(s_points)
        ax.set_xticklabels(
            [
                "sev1\n(中等洪水)",
                "sev1.5\n(较严重洪水)",
                f"sev1.5+2\n(平均 s≈{s_mix:.2f})",
            ]
        )

        ax.legend()
        plt.tight_layout()

        out_png = OUT_DIR / f"beta_s_curve_edu_DFO_sample_{sample_name}.png"
        plt.savefig(out_png, dpi=300)
        plt.show()
        print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    # External flood dataset comparison note.
    gdf_c = load_counties()
    gdf_dfo = load_dfo_with_severity()

    # County-level processing note.
    df_cy = build_dfo_county_year_severity(gdf_dfo, gdf_c)
    df_cy.to_csv(OUT_DIR / "county_year_severity_panel_DFO.csv",
                 index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # County-level processing note.
    df_cohort = build_cohort_severity_exposure(df_cy, county_col="county_code")
    df_cohort.to_csv(OUT_DIR / "county_birthyear_severity_DFO.csv",
                     index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_micro = merge_severity_to_micro(df_cohort)
    df_micro_poly = build_agg_poly_exposure(df_micro)
    df_micro_poly.to_parquet(
        OUT_DIR / "edu_micro_2015_with_severity_poly_DFO.parquet",
        index=False
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    run_poly_severity_beta_curve(df_micro_poly)


if __name__ == "__main__":
    main()
