#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# DFO shapefile
DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

# Original notebook comment normalized for the public code archive.
CITY_SHP = os.path.join(BASE_DIR, "gis_data/China/city/city.shp")
CITY_ID_FIELD = "市代码"  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# External flood dataset comparison note.
DFO_START_YEAR = 1980
DFO_END_YEAR   = 2020

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"
FULL_COVER_TH = 0.99

# Original notebook comment normalized for the public code archive.
SEV_OPTIONS = ["1", "1.5", "2"]
SEV_LABELS = {
    "1": "sev1",
    "1.5": "sev1_5",
    "2": "sev2",
}

# Original notebook comment normalized for the public code archive.
SPATIAL_PREFIXES = ["centroid", "area50", "full"]


# =============================================================================

def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].buffer(0)
    return gdf


# =============================================================================

def load_cities() -> gpd.GeoDataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf_city = gpd.read_file(CITY_SHP)
    if gdf_city.crs is None:
        gdf_city = gdf_city.set_crs(epsg=4326)
    else:
        gdf_city = gdf_city.to_crs(epsg=4326)
    gdf_city = _make_valid(gdf_city)

    # Original notebook comment normalized for the public code archive.
    gdf_city["city_code"] = gdf_city[CITY_ID_FIELD].astype(str)

    # City-level processing note.
    gdf_city["city_id"] = gdf_city["city_code"].factorize()[0].astype(int)

    print("[INFO] Notebook progress message.")
    return gdf_city


def load_dfo_raw() -> gpd.GeoDataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

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
        print("[INFO] Notebook progress message.")
        gdf["severity_raw"] = np.nan
        gdf["severity_code"] = np.nan
    else:
        gdf["severity_raw"] = gdf[sev_col]
        gdf["severity_code"] = pd.to_numeric(gdf[sev_col], errors="coerce")
        print("[INFO] Notebook progress message.")
        print(gdf["severity_code"].value_counts(dropna=False).head())

    # Original notebook comment normalized for the public code archive.
    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) &
              (gdf["year"] <= DFO_END_YEAR)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def apply_severity_flag(gdf_raw: gpd.GeoDataFrame,
                        sev_option: str) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf_raw.copy()

    if "severity_code" not in gdf.columns:
        gdf["is_severe_100yr"] = 0
        return gdf

    sev_num = gdf["severity_code"]

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

    gdf["is_severe_100yr"] = is_num.astype(int)
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def build_dfo_city_year_panel(gdf_dfo: gpd.GeoDataFrame,
                              gdf_city: gpd.GeoDataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    c_proj   = gdf_city.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()
    c_proj["area_city"] = c_proj.geometry.area

    # ---------- 1) centroid ----------
    c_cent = c_proj[["city_id", "city_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["city_id", "city_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner", predicate="within"
    )
    cent_join["severe_duration_row"] = (
        cent_join["duration_days"] * cent_join["is_severe_100yr"]
    )

    df_cent = (
        cent_join.groupby(["city_id", "city_code", "year"], as_index=False)
        .agg(
            flooded_times_centroid=("event_id", "nunique"),
            duration_days_centroid=("duration_days", "sum"),
            severe_times_centroid=("is_severe_100yr", "sum"),
            severe_duration_centroid=("severe_duration_row", "sum"),
        )
    )
    df_cent["flooded_any_centroid"] = (df_cent["flooded_times_centroid"] > 0).astype(int)
    df_cent["severe_any_centroid"]  = (df_cent["severe_times_centroid"] > 0).astype(int)

    # =============================================================================
    inter = gpd.overlay(
        c_proj[["city_id", "city_code", "area_city", "geometry"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    inter["intersect_area"] = inter.geometry.area
    inter["cover_ratio"] = inter["intersect_area"] / inter["area_city"]
    inter["severe_duration_row"] = inter["duration_days"] * inter["is_severe_100yr"]

    # ---------- 2.1 area50 ----------
    inter_a50 = inter[inter["cover_ratio"] >= 0.5].copy()
    df_a50 = (
        inter_a50.groupby(["city_id","city_code","year"], as_index=False)
        .agg(
            flooded_times_area50=("event_id","nunique"),
            duration_days_area50=("duration_days","sum"),
            severe_times_area50=("is_severe_100yr","sum"),
            severe_duration_area50=("severe_duration_row","sum"),
        )
    )
    df_a50["flooded_any_area50"] = (df_a50["flooded_times_area50"]>0).astype(int)
    df_a50["severe_any_area50"]  = (df_a50["severe_times_area50"]>0).astype(int)

    # =============================================================================
    inter_full = inter[inter["cover_ratio"] >= FULL_COVER_TH].copy()
    df_full = (
        inter_full.groupby(["city_id","city_code","year"], as_index=False)
        .agg(
            flooded_times_full=("event_id","nunique"),
            duration_days_full=("duration_days","sum"),
            severe_times_full=("is_severe_100yr","sum"),
            severe_duration_full=("severe_duration_row","sum"),
        )
    )
    df_full["flooded_any_full"] = (df_full["flooded_times_full"]>0).astype(int)
    df_full["severe_any_full"]  = (df_full["severe_times_full"]>0).astype(int)

    # =============================================================================
    all_cities = gdf_city[["city_id","city_code"]].drop_duplicates()
    all_years = pd.DataFrame(
        {"year": np.arange(DFO_START_YEAR, DFO_END_YEAR+1, dtype=int)}
    )
    full_index = (all_cities.assign(key=1)
                            .merge(all_years.assign(key=1), on="key")
                            .drop(columns="key"))

    out = (full_index
           .merge(df_cent,  on=["city_id","city_code","year"], how="left")
           .merge(df_a50,   on=["city_id","city_code","year"], how="left")
           .merge(df_full,  on=["city_id","city_code","year"], how="left"))

    val_cols = [c for c in out.columns if c not in ["city_id","city_code","year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    int_cols = [c for c in val_cols if c.startswith(
        ("flooded_", "severe_", "duration_", "flooded_times", "severe_times")
    )]
    for c in int_cols:
        out[c] = out[c].astype(int)

    return out


# =============================================================================

def build_city_year_all_sev() -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf_city = load_cities()
    gdf_dfo_raw = load_dfo_raw()

    df_city_all = None

    for i, sev_opt in enumerate(SEV_OPTIONS):
        print("\n" + "=" * 50)
        print("[INFO] Notebook progress message.")
        gdf_dfo = apply_severity_flag(gdf_dfo_raw, sev_option=sev_opt)
        df_cy = build_dfo_city_year_panel(gdf_dfo, gdf_city)

        label = SEV_LABELS[sev_opt]

        # Original notebook comment normalized for the public code archive.
        rename_map = {}
        for col in df_cy.columns:
            if col.startswith("severe_"):
                rename_map[col] = f"{col}_{label}"
        df_cy = df_cy.rename(columns=rename_map)

        if df_city_all is None:
            df_city_all = df_cy
        else:
            keep_cols = ["city_id","city_code","year"] + list(rename_map.values())
            df_city_all = df_city_all.merge(
                df_cy[keep_cols],
                on=["city_id","city_code","year"],
                how="left",
                validate="1:1",
            )

    out_path = OUT_DIR / "dfo_city_year_1980_2020_all_sev.parquet"
    df_city_all.to_parquet(out_path, index=False)
    print("[INFO] Notebook progress message.")
    return df_city_all


def main():
    build_city_year_all_sev()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
CITY_YEAR_PARQUET = OUT_DIR / "dfo_city_year_1980_2020_all_sev.parquet"

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
WINDOW_LIST = [5, 10, 20, 30]
SEV_LABELS = {
    "1": "sev1",
    "1.5": "sev1_5",
    "2": "sev2",
}


def build_city_rolling_exposure():
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(CITY_YEAR_PARQUET)

    df = df.sort_values(["city_code", "year"]).reset_index(drop=True)
    df["city_code"] = pd.to_numeric(df["city_code"], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    for prefix in SPATIAL_PREFIXES:
        base_col = f"flooded_any_{prefix}"
        if base_col not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        for window in WINDOW_LIST:
            out_col = f"share_DFO_any_{prefix}_{window}y"
            df[out_col] = (
                df.groupby("city_code")[base_col]
                  .rolling(window=window, min_periods=1)
                  .mean()
                  .reset_index(level=0, drop=True)
            )
            print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    for prefix in SPATIAL_PREFIXES:
        for lab in SEV_LABELS.values():
            sev_col = f"severe_any_{prefix}_{lab}"
            if sev_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for window in WINDOW_LIST:
                out_col = f"share_DFO_{lab}_{prefix}_{window}y"
                df[out_col] = (
                    df.groupby("city_code")[sev_col]
                      .rolling(window=window, min_periods=1)
                      .mean()
                      .reset_index(level=0, drop=True)
                )
                print("[INFO] Notebook progress message.")

    out_path = OUT_DIR / "dfo_city_rolling_1980_2020_allsev_5_10_20_30y.parquet"
    df.to_parquet(out_path, index=False)
    print("[INFO] Notebook progress message.")

    return df


def main():
    build_city_rolling_exposure()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd

# Original notebook comment normalized for the public code archive.
PANEL_LONG_IDX = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/"
    "charls_health_panel_long_with_index.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DFO_ROLL_PARQUET = OUT_DIR / "dfo_city_rolling_1980_2020_allsev_5_10_20_30y.parquet"


def merge_charls_with_dfo():
    print("[INFO] Notebook progress message.")
    panel = pd.read_parquet(PANEL_LONG_IDX)

    # Original notebook comment normalized for the public code archive.
    panel["age"] = pd.to_numeric(panel["age"], errors="coerce")
    panel = panel[panel["age"] >= 60].copy()

    # City-level processing note.
    if "city_code" not in panel.columns:
        raise KeyError("CHARLS 面板中不存在 city_code，请确认已生成城市代码。")

    panel["city_code"] = pd.to_numeric(panel["city_code"], errors="coerce").astype("Int64")
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")

    print(f"[READ] DFO city rolling exposure: {DFO_ROLL_PARQUET}")
    dfo = pd.read_parquet(DFO_ROLL_PARQUET)
    dfo["city_code"] = pd.to_numeric(dfo["city_code"], errors="coerce").astype("Int64")
    dfo["year"] = pd.to_numeric(dfo["year"], errors="coerce").astype("Int64")

    # City-level processing note.
    exp_cols = [c for c in dfo.columns if c.startswith("share_DFO_")]
    keep_cols = ["city_code", "year"] + exp_cols

    merged = panel.merge(
        dfo[keep_cols],
        how="left",
        on=["city_code", "year"],
        validate="m:1",
    )

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    out_parquet = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"
    out_xlsx    = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.xlsx"

    merged.to_parquet(out_parquet, index=False)
    merged.to_excel(out_xlsx, index=False)

    print("[INFO] Notebook progress message.")
    return merged


def main():
    merge_charls_with_dfo()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
Y_VAR = "health_index_z"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"      # CHARLS processing note.
CLUSTER_COL = "city_code"  # Original notebook comment normalized for the public code archive.

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
WINDOW_LIST = [5, 10, 20, 30]
SEV_LABELS = {
    "1": "sev1",
    "1.5": "sev1_5",
    "2": "sev2",
}


# =============================================================================
def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


def fe_reg_twoFE_city_cluster(df: pd.DataFrame,
                              y_col: str,
                              x_cols,
                              fe1: str,
                              fe2: str,
                              cluster_col: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
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


# =============================================================================
def run_individual_fe_city_cluster_DFO():
    print(f"[READ] merged panel with DFO: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    base_cols = [Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    df = df.dropna(subset=base_cols).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL,
            how="left",
        )
    else:
        df["urban_group"] = 1  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    # External flood dataset comparison note.
    exposure_list = []
    for prefix in SPATIAL_PREFIXES:
        for window in WINDOW_LIST:
            exposure_list.append(f"share_DFO_any_{prefix}_{window}y")
            for lab in SEV_LABELS.values():
                exposure_list.append(f"share_DFO_{lab}_{prefix}_{window}y")

    all_rows = []

    for exp_col in exposure_list:
        if exp_col not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        for sample_name, group_val in sample_specs.items():
            if group_val is None:
                sub = df.copy()
            else:
                sub = df[df["urban_group"] == group_val].copy()

            # Original notebook comment normalized for the public code archive.
            waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

            if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                print(
                    f"[WARN] exp={exp_col}, sample={sample_name} 样本量或城市数过小 "
                    f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                )
                continue

            x_cols = [exp_col, "age", "age2"]

            res = fe_reg_twoFE_city_cluster(
                sub,
                y_col=Y_VAR,
                x_cols=x_cols,
                fe1=ID_COL,
                fe2="prov_year",
                cluster_col=CLUSTER_COL,
            )

            row = res.loc[exp_col].copy()
            row["Y_var"] = Y_VAR
            row["exposure"] = exp_col
            row["sample"] = sample_name
            row["N"] = len(sub)
            row["N_id"] = sub[ID_COL].nunique()
            row["N_year"] = sub[YEAR_COL].nunique()
            row["N_city"] = sub[CLUSTER_COL].nunique()

            print("\n" + "=" * 40)
            print(
                f"[RESULT] (prov×year FE, city cluster) Y={Y_VAR}, "
                f"exp={exp_col}, sample={sample_name}"
            )
            print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

            all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "exposure", "sample"])

    out_path = OUT_DIR / f"fe_{Y_VAR}_DFO_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


def main():
    run_individual_fe_city_cluster_DFO()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)

IN_CSV = OUT_DIR / "fe_health_index_z_DFO_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
OUT_CSV = OUT_DIR / "fe_health_index_z_DFO_5_10_20_30y_pid12_provYearFE_cityCluster_prefixAgg.csv"

Y_VAR = "health_index_z"

TYPES = ["sev1", "sev1_5", "sev2"]
PREFIXES = ["centroid", "area50", "full"]
SAMPLES = ["all", "urban", "rural"]

# Original notebook comment normalized for the public code archive.
EXPO_PATTERN = re.compile(
    r"^share_DFO_"
    r"(any|sev1|sev1_5|sev2)_"
    r"(centroid|area50|full)_"
    r"(\d+)y$"
)


# =============================================================================

def norm_cdf(z: float) -> float:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


# =============================================================================
def parse_exposure_name(s: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not isinstance(s, str):
        return None, None, None
    m = EXPO_PATTERN.match(s)
    if m is None:
        return None, None, None
    type_, prefix, window = m.groups()
    return type_, prefix, int(window)


def read_raw_results() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(IN_CSV)

    needed = [
        "Y_var", "exposure", "sample",
        "Estimate", "Std. Error", "t value", "Pr(>|t|)",
        "2.5%", "97.5%", "N", "N_id", "N_year", "N_city",
    ]
    miss = [c for c in needed if c not in df.columns]
    if miss:
        raise KeyError(f"输入结果缺少必要列: {miss}")

    # Original notebook comment normalized for the public code archive.
    parsed = df["exposure"].apply(parse_exposure_name)
    df["type"] = parsed.apply(lambda x: x[0])
    df["prefix"] = parsed.apply(lambda x: x[1])
    df["window"] = parsed.apply(lambda x: x[2])

    # Original notebook comment normalized for the public code archive.
    n_bad = df["type"].isna().sum()
    if n_bad > 0:
        print("[INFO] Notebook progress message.")
        df = df[df["type"].notna()].copy()

    # Original notebook comment normalized for the public code archive.
    for col in ["window", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["Y_var"] == Y_VAR].copy()
    df = df.dropna(subset=["window"])

    df["window"] = df["window"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df.head())

    return df


# =============================================================================

def aggregate_one_group(sub: pd.DataFrame) -> dict:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    k = len(sub)
    betas = sub["Estimate"].astype("float64").to_numpy()
    ses = sub["Std. Error"].astype("float64").to_numpy()

    beta_bar = float(np.mean(betas))

    if k > 0:
        var_agg = float(np.sum(ses ** 2) / (k ** 2))
        se_agg = float(np.sqrt(var_agg))
    else:
        se_agg = float("nan")

    if np.isfinite(se_agg) and se_agg > 0:
        t_val = beta_bar / se_agg
        p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        ci_low = beta_bar - 1.96 * se_agg
        ci_high = beta_bar + 1.96 * se_agg
    else:
        t_val = float("nan")
        p_val = float("nan")
        ci_low = float("nan")
        ci_high = float("nan")

    out = {
        "Y_var": sub["Y_var"].iloc[0],
        "sample": sub["sample"].iloc[0],
        "type": sub["type"].iloc[0],
        "window": int(sub["window"].iloc[0]),
        # Original notebook comment normalized for the public code archive.
        "prefix": "agg",
        "Estimate": beta_bar,
        "Std. Error": se_agg,
        "t value": t_val,
        "Pr(>|t|)": p_val,
        "2.5%": ci_low,
        "97.5%": ci_high,
        # City-level processing note.
        "N": sub["N"].iloc[0],
        "N_id": sub["N_id"].iloc[0],
        "N_city": sub["N_city"].iloc[0],
    }
    return out


def aggregate_prefix(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_keys = ["Y_var", "sample", "type", "window"]
    rows = []

    for key, sub in df_raw.groupby(group_keys, sort=False):
        rows.append(aggregate_one_group(sub))

    df_agg = pd.DataFrame(rows)
    df_agg = df_agg.sort_values(
        ["Y_var", "sample", "type", "window"]
    ).reset_index(drop=True)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(df_agg.head())

    df_agg.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return df_agg


# =============================================================================
def plot_by_sample(df_agg: pd.DataFrame, sample: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_agg[df_agg["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = sub["Estimate"].min()
    y_max = sub["Estimate"].max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    offset = 0.03 * y_range

    label_map = {
        "any": "任意洪水 (any)",
        "sev1": "sev1 中等洪水",
        "sev1_5": "sev1.5 较严重洪水",
        "sev2": "sev2 极端洪水",
    }

    fig, ax = plt.subplots(figsize=(7, 4))

    for t in TYPES:
        tsub = sub[sub["type"] == t].sort_values("window")
        if tsub.empty:
            continue

        x = tsub["window"].values
        y = tsub["Estimate"].values
        yerr_lower = y - tsub["2.5%"].values
        yerr_upper = tsub["97.5%"].values - y

        ax.errorbar(
            x,
            y,
            yerr=[yerr_lower, yerr_upper],
            marker="o",
            linestyle="-",
            capsize=4,
            label=label_map.get(t, t),
        )

        # Original notebook comment normalized for the public code archive.
        p_vals = tsub["Pr(>|t|)"].values
        for xi, yi, pi in zip(x, y, p_vals):
            s = stars_for_p(pi)
            if s:
                ax.text(
                    xi,
                    yi + offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlabel("滚动窗口长度（年）")
    ax.set_ylabel("系数 (health_index_z)")
    ax.set_title(f"DFO 暴露效应（prefix 聚合后）– sample = {sample}")
    ax.legend()
    ax.set_ylim(y_lower, y_upper)
    plt.tight_layout()
    plt.show()


# ========== main ==========

def main():
    df_raw = read_raw_results()
    df_agg = aggregate_prefix(df_raw)

    # Original notebook comment normalized for the public code archive.
    for samp in SAMPLES:
        plot_by_sample(df_agg, sample=samp)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
Y_VAR = "health_index_z"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"      # CHARLS processing note.
CLUSTER_COL = "city_code"  # Original notebook comment normalized for the public code archive.

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
WINDOW_LIST = [5, 10, 20, 30]


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


def fe_reg_twoFE_city_cluster(df: pd.DataFrame,
                              y_col: str,
                              x_cols,
                              fe1: str,
                              fe2: str,
                              cluster_col: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
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


# =============================================================================

def run_fe_sev1_vs_sev15_2():
    print(f"[READ] merged panel with DFO: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    base_cols = [Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    df = df.dropna(subset=base_cols).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL,
            how="left",
        )
    else:
        df["urban_group"] = 1  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # =============================================================================
    sev_pairs = []  # Original notebook comment normalized for the public code archive.

    for prefix in SPATIAL_PREFIXES:
        for window in WINDOW_LIST:
            col_sev1 = f"share_DFO_sev1_{prefix}_{window}y"
            col_sev15 = f"share_DFO_sev1_5_{prefix}_{window}y"
            col_sev2 = f"share_DFO_sev2_{prefix}_{window}y"

            if (col_sev1 not in df.columns) or \
               (col_sev15 not in df.columns) or \
               (col_sev2 not in df.columns):
                print(
                    f"[WARN] 缺少 {col_sev1} 或 {col_sev15} 或 {col_sev2}，"
                    f"prefix={prefix}, window={window} 跳过。"
                )
                continue

            # Original notebook comment normalized for the public code archive.
            col_sev15_2 = f"share_DFO_sev15_2_{prefix}_{window}y"
            df[col_sev15_2] = df[col_sev15].fillna(0) + df[col_sev2].fillna(0)

            sev_pairs.append((prefix, window, col_sev1, col_sev15_2))

    if not sev_pairs:
        print("[INFO] Notebook progress message.")
        return None

    # =============================================================================
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    # =============================================================================
    all_rows = []

    for prefix, window, col_sev1, col_sev15_2 in sev_pairs:
        for sample_name, group_val in sample_specs.items():
            if group_val is None:
                sub = df.copy()
            else:
                sub = df[df["urban_group"] == group_val].copy()

            # Original notebook comment normalized for the public code archive.
            waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

            if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                print(
                    f"[WARN] prefix={prefix}, window={window}, sample={sample_name} "
                    f"样本量或城市数过小 (N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                )
                continue

            x_cols = [col_sev1, col_sev15_2, "age", "age2"]

            res = fe_reg_twoFE_city_cluster(
                sub,
                y_col=Y_VAR,
                x_cols=x_cols,
                fe1=ID_COL,
                fe2="prov_year",
                cluster_col=CLUSTER_COL,
            )

            # External flood dataset comparison note.
            for exp_col, group_label in [(col_sev1, "sev1"), (col_sev15_2, "sev15_2")]:
                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["prefix"] = prefix
                row["window"] = window
                row["group"] = group_label
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                all_rows.append(row)

            print("\n" + "=" * 50)
            print(
                f"[RESULT] Y={Y_VAR}, prefix={prefix}, window={window}y, "
                f"sample={sample_name}"
            )
            print(
                res.loc[[col_sev1, col_sev15_2]][
                    ["Estimate", "Std. Error", "Pr(>|t|)"]
                ]
            )

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "prefix", "window", "group", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "prefix", "window", "group", "sample"])

    out_path = OUT_DIR / (
        f"fe_{Y_VAR}_DFO_sev1_vs_sev15_2_5_10_20_30y_"
        "pid12_provYearFE_cityCluster.csv"
    )
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


def main():
    run_fe_sev1_vs_sev15_2()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
from math import erf, sqrt

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)

# Original notebook comment normalized for the public code archive.
RESULT_CSV = OUT_DIR / (
    "fe_health_index_z_DFO_sev1_vs_sev15_2_5_10_20_30y_"
    "pid12_provYearFE_cityCluster.csv"
)

# =============================================================================

def norm_cdf(x: float) -> float:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


# =============================================================================

def aggregate_across_prefix():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RESULT_CSV)

    # Original notebook comment normalized for the public code archive.
    required_cols = [
        "Y_var", "prefix", "window", "group", "sample",
        "Estimate", "Std. Error",
        "N", "N_id", "N_year", "N_city",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    group_cols = ["Y_var", "window", "group", "sample"]

    def agg_one_group(g: pd.DataFrame) -> pd.Series:
        """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
        est = g["Estimate"].to_numpy(dtype=float)
        se = g["Std. Error"].to_numpy(dtype=float)
        var = se ** 2

        # Original notebook comment normalized for the public code archive.
        var[var <= 0] = 1e-12
        w = 1.0 / var

        # Original notebook comment normalized for the public code archive.
        beta_w = np.sum(w * est) / np.sum(w)
        var_w = 1.0 / np.sum(w)
        se_w = np.sqrt(var_w)

        # Original notebook comment normalized for the public code archive.
        t_val = beta_w / se_w if se_w > 0 else np.nan
        p_val = 2.0 * (1.0 - norm_cdf(abs(t_val))) if np.isfinite(t_val) else np.nan

        # Original notebook comment normalized for the public code archive.
        z_95 = 1.96
        ci_low = beta_w - z_95 * se_w
        ci_high = beta_w + z_95 * se_w

        # Original notebook comment normalized for the public code archive.
        prefix_list = ",".join(sorted(g["prefix"].astype(str).unique()))
        n_prefix = g["prefix"].nunique()

        # Original notebook comment normalized for the public code archive.
        N = g["N"].iloc[0]
        N_id = g["N_id"].iloc[0]
        N_year = g["N_year"].iloc[0]
        N_city = g["N_city"].iloc[0]

        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_prefix": n_prefix,
                "prefix_list": prefix_list,
                "N": N,
                "N_id": N_id,
                "N_year": N_year,
                "N_city": N_city,
            }
        )

    print("[INFO] Notebook progress message.")
    df_agg = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one_group)
    )

    # Original notebook comment normalized for the public code archive.
    df_agg = df_agg.sort_values(
        ["Y_var", "group", "window", "sample"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / (
        "fe_health_index_z_DFO_sev1_vs_sev15_2_5_10_20_30y_"
        "pid12_provYearFE_cityCluster_prefixAgg.csv"
    )
    df_agg.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return df_agg


def main():
    aggregate_across_prefix()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)

AGG_CSV = OUT_DIR / (
    "fe_health_index_z_DFO_sev1_vs_sev15_2_5_10_20_30y_"
    "pid12_provYearFE_cityCluster_prefixAgg.csv"
)

# Original notebook comment normalized for the public code archive.
Y_VAR = "health_index_z"

SAMPLES = ["all", "urban", "rural"]
GROUPS = ["sev1", "sev15_2"]


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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


# =============================================================================

def read_agg_result() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(AGG_CSV)

    # Original notebook comment normalized for the public code archive.
    needed = [
        "Y_var", "sample", "group", "window",
        "Estimate", "Std. Error", "Pr(>|t|)",
        "2.5%", "97.5%"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件中缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")
    df["Pr(>|t|)"] = pd.to_numeric(df["Pr(>|t|)"], errors="coerce")
    df["2.5%"] = pd.to_numeric(df["2.5%"], errors="coerce")
    df["97.5%"] = pd.to_numeric(df["97.5%"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["Y_var"] == Y_VAR].copy()

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["window"])
    df["window"] = df["window"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


# =============================================================================

def plot_severity_by_sample(df_agg: pd.DataFrame, sample: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_agg[df_agg["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = sub["Estimate"].min()
    y_max = sub["Estimate"].max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    offset = 0.03 * y_range  # Original notebook comment normalized for the public code archive.

    fig, ax = plt.subplots(figsize=(6, 4))

    for grp in GROUPS:
        tmp = sub[sub["group"] == grp].sort_values("window")
        if tmp.empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        x = tmp["window"].values
        y = tmp["Estimate"].values
        yerr_lower = y - tmp["2.5%"].values
        yerr_upper = tmp["97.5%"].values - y

        ax.errorbar(
            x, y,
            yerr=[yerr_lower, yerr_upper],
            marker="o",
            linestyle="-",
            capsize=4,
            label=grp
        )

        # Original notebook comment normalized for the public code archive.
        p_vals = tmp["Pr(>|t|)"].values
        for xi, yi, pi in zip(x, y, p_vals):
            s = stars_for_p(pi)
            if s:
                ax.text(
                    xi,
                    yi + offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=10
                )

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlabel("滚动窗口长度（年）")
    ax.set_ylabel("DFO 暴露系数 (Estimate)")
    ax.set_title(f"DFO 严重程度效应（已聚合空间定义）– sample = {sample}")
    ax.legend(title="group (sev level)\nsev1 vs sev15_2")
    ax.set_ylim(y_lower, y_upper)
    plt.tight_layout()
    plt.show()


# ========= main =========

def main():
    df_agg = read_agg_result()

    for samp in SAMPLES:
        plot_severity_by_sample(df_agg, sample=samp)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)

AGG_CSV = OUT_DIR / (
    "fe_health_index_z_DFO_sev1_vs_sev15_2_5_10_20_30y_"
    "pid12_provYearFE_cityCluster_prefixAgg.csv"
)

# Original notebook comment normalized for the public code archive.
Y_VAR = "health_index_z"

SAMPLES = ["all", "urban", "rural"]
GROUPS = ["sev1", "sev15_2"]


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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


def norm_cdf(x: float) -> float:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


# =============================================================================

def read_agg_result() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(AGG_CSV)

    # Original notebook comment normalized for the public code archive.
    needed = [
        "Y_var", "sample", "group", "window",
        "Estimate", "Std. Error", "Pr(>|t|)",
        "2.5%", "97.5%"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件中缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")
    df["Pr(>|t|)"] = pd.to_numeric(df["Pr(>|t|)"], errors="coerce")
    df["2.5%"] = pd.to_numeric(df["2.5%"], errors="coerce")
    df["97.5%"] = pd.to_numeric(df["97.5%"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["Y_var"] == Y_VAR].copy()

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["window"])
    df["window"] = df["window"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


# =============================================================================

def aggregate_across_window(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_cols = ["Y_var", "sample", "group"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g["Estimate"].to_numpy(dtype=float)
        se = g["Std. Error"].to_numpy(dtype=float)
        var = se ** 2

        # Original notebook comment normalized for the public code archive.
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = np.sum(w * est) / np.sum(w)
        var_w = 1.0 / np.sum(w)
        se_w = np.sqrt(var_w)

        # Original notebook comment normalized for the public code archive.
        t_val = beta_w / se_w if se_w > 0 else np.nan
        p_val = 2.0 * (1.0 - norm_cdf(abs(t_val))) if np.isfinite(t_val) else np.nan

        # 95% CI
        z_95 = 1.96
        ci_low = beta_w - z_95 * se_w
        ci_high = beta_w + z_95 * se_w

        # Original notebook comment normalized for the public code archive.
        window_list = sorted(g["window"].astype(int).unique().tolist())
        n_window = len(window_list)
        window_str = ",".join(str(w) for w in window_list)

        # Original notebook comment normalized for the public code archive.
        N_min = g["N"].min() if "N" in g.columns else np.nan
        N_max = g["N"].max() if "N" in g.columns else np.nan

        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_window": n_window,
                "window_list": window_str,
                "N_min": N_min,
                "N_max": N_max,
            }
        )

    print("[INFO] Notebook progress message.")
    df_win = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one)
    )

    # Original notebook comment normalized for the public code archive.
    df_win = df_win.sort_values(
        ["Y_var", "sample", "group"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / (
        "fe_health_index_z_DFO_sev1_vs_sev15_2_"
        "prefixAgg_windowAgg.csv"
    )
    df_win.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    print(df_win)
    return df_win


# =============================================================================

def plot_window_agg_by_sample(df_win: pd.DataFrame, sample: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_win[df_win["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub[sub["group"].isin(GROUPS)].copy()
    sub["group"] = pd.Categorical(sub["group"], categories=GROUPS, ordered=True)
    sub = sub.sort_values("group")

    x_labels = sub["group"].tolist()
    x_pos = np.arange(len(x_labels))

    est = sub["Estimate"].to_numpy()
    ci_low = sub["2.5%"].to_numpy()
    ci_high = sub["97.5%"].to_numpy()
    p_vals = sub["Pr(>|t|)"].to_numpy()

    # Original notebook comment normalized for the public code archive.
    yerr_lower = est - ci_low
    yerr_upper = ci_high - est

    # Original notebook comment normalized for the public code archive.
    y_min = (est - yerr_lower).min()
    y_max = (est + yerr_upper).max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    offset = 0.03 * y_range

    fig, ax = plt.subplots(figsize=(5, 4))

    # Original notebook comment normalized for the public code archive.
    ax.errorbar(
        x_pos,
        est,
        yerr=[yerr_lower, yerr_upper],
        fmt="o-",       # Original notebook comment normalized for the public code archive.
        capsize=5,
    )

    # Original notebook comment normalized for the public code archive.
    for xi, yi, pi in zip(x_pos, est, p_vals):
        s = stars_for_p(pi)
        if s:
            ax.text(
                xi,
                yi + offset,
                s,
                ha="center",
                va="bottom",
                fontsize=11
            )

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["sev1\n(中等洪水)", "sev1.5+2\n(较严重洪水)"])

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylabel("DFO 暴露综合系数 (Estimate)")
    ax.set_title(f"DFO 严重程度综合效应（跨 window & prefix 聚合）– sample = {sample}")
    ax.set_ylim(y_lower, y_upper)

    # Original notebook comment normalized for the public code archive.
    window_info = sub["window_list"].iloc[0] if "window_list" in sub.columns else ""
    ax.text(
        0.99, 0.01,
        f"窗口: {window_info}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8
    )

    plt.tight_layout()
    plt.show()


# ========= main =========

def main():
    # Original notebook comment normalized for the public code archive.
    df_agg = read_agg_result()

    # Original notebook comment normalized for the public code archive.
    df_win = aggregate_across_window(df_agg)

    # Original notebook comment normalized for the public code archive.
    for samp in SAMPLES:
        plot_window_agg_by_sample(df_win, sample=samp)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 25
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)

AGG_CSV = OUT_DIR / (
    "fe_health_index_z_DFO_sev1_vs_sev15_2_5_10_20_30y_"
    "pid12_provYearFE_cityCluster_prefixAgg.csv"
)

Y_VAR = "health_index_z"

SAMPLES = ["all", "urban", "rural"]
GROUPS = ["sev1", "sev15_2"]   # Original notebook comment normalized for the public code archive.


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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


def norm_cdf(x: float) -> float:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


# =============================================================================

def read_agg_result() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(AGG_CSV)

    needed = [
        "Y_var", "sample", "group", "window",
        "Estimate", "Std. Error", "Pr(>|t|)",
        "2.5%", "97.5%", "N"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件中缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    for col in ["Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%", "N"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["Y_var"] == Y_VAR].copy()
    df = df.dropna(subset=["window"])
    df["window"] = df["window"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


# =============================================================================

def aggregate_across_window(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_cols = ["Y_var", "sample", "group"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g["Estimate"].to_numpy(dtype=float)
        se = g["Std. Error"].to_numpy(dtype=float)
        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        # t、p、CI
        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
            ci_low = beta_w - 1.96 * se_w
            ci_high = beta_w + 1.96 * se_w
        else:
            t_val = p_val = ci_low = ci_high = np.nan

        win_list = sorted(g["window"].astype(int).unique().tolist())
        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_window": len(win_list),
                "window_list": ",".join(str(w) for w in win_list),
                "N_min": g["N"].min(),
                "N_max": g["N"].max(),
            }
        )

    print("[INFO] Notebook progress message.")
    df_win = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one)
    )

    df_win = df_win.sort_values(
        ["Y_var", "sample", "group"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / (
        "fe_health_index_z_DFO_sev1_vs_sev15_2_"
        "prefixAgg_windowAgg.csv"
    )
    df_win.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    print(df_win)
    return df_win


# =============================================================================

def plot_window_agg_by_sample(df_win: pd.DataFrame, sample: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_win[df_win["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub[sub["group"].isin(GROUPS)].copy()
    if sub["group"].nunique() < 2:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub["group"] = pd.Categorical(sub["group"], categories=GROUPS, ordered=True)
    sub = sub.sort_values("group")

    x_labels = sub["group"].tolist()
    x_pos = np.arange(len(x_labels))

    est = sub["Estimate"].to_numpy()
    ci_low = sub["2.5%"].to_numpy()
    ci_high = sub["97.5%"].to_numpy()
    p_vals = sub["Pr(>|t|)"].to_numpy()
    se = sub["Std. Error"].to_numpy()

    # Original notebook comment normalized for the public code archive.
    yerr_lower = est - ci_low
    yerr_upper = ci_high - est

    # Original notebook comment normalized for the public code archive.
    y_min = (est - yerr_lower).min()
    y_max = (est + yerr_upper).max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.15 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    offset_point = 0.04 * y_range      # Original notebook comment normalized for the public code archive.
    offset_delta = 0.08 * y_range      # Original notebook comment normalized for the public code archive.

    fig, ax = plt.subplots(figsize=(5.2, 4))

    # Original notebook comment normalized for the public code archive.
    ax.errorbar(
        x_pos,
        est,
        yerr=[yerr_lower, yerr_upper],
        fmt="o-",
        capsize=5,
    )

    # Original notebook comment normalized for the public code archive.
    for xi, yi, pi in zip(x_pos, est, p_vals):
        s = stars_for_p(pi)
        if s:
            ax.text(
                xi,
                yi + offset_point,
                s,
                ha="center",
                va="bottom",
                fontsize=11,
            )

    # =============================================================================
    beta_sev1 = float(est[0])
    beta_sev15_2 = float(est[1])
    se_sev1 = float(se[0])
    se_sev15_2 = float(se[1])

    delta = beta_sev15_2 - beta_sev1
    # Original notebook comment normalized for the public code archive.
    var_delta = se_sev1 ** 2 + se_sev15_2 ** 2
    if var_delta <= 0 or not np.isfinite(var_delta):
        p_delta = np.nan
        ci_d_low = ci_d_high = np.nan
    else:
        se_delta = float(np.sqrt(var_delta))
        t_delta = delta / se_delta
        p_delta = 2.0 * (1.0 - norm_cdf(abs(t_delta)))
        ci_d_low = delta - 1.96 * se_delta
        ci_d_high = delta + 1.96 * se_delta

    star_delta = stars_for_p(p_delta)
    print(
        f"[INFO] sample={sample}: Δ = β(sev1.5+2) - β(sev1) "
        f"= {delta:.4f} (p={p_delta:.4g}), 95%CI=({ci_d_low:.4f},{ci_d_high:.4f})"
    )

    # Original notebook comment normalized for the public code archive.
    mid_x = (x_pos[0] + x_pos[1]) / 2.0
    mid_y = (est[0] + est[1]) / 2.0
    txt = f"Δ = {delta:.3f}{star_delta}"
    ax.text(
        mid_x,
        mid_y + offset_delta,
        txt,
        ha="center",
        va="bottom",
        fontsize=11,
    )

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["sev1\n(中等洪水)", "sev1.5+2\n(较严重洪水)"])
    ax.set_ylabel("DFO 暴露综合系数 (Estimate)")
    ax.set_title(f"DFO 严重程度综合效应（跨 window & prefix 聚合） – sample = {sample}")
    ax.set_ylim(y_lower, y_upper)

    # Original notebook comment normalized for the public code archive.
    win_info = sub["window_list"].iloc[0] if "window_list" in sub.columns else ""
    ax.text(
        0.99, 0.01,
        f"窗口: {win_info}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
    )

    plt.tight_layout()
    plt.show()


# ========= main =========

def main():
    # Original notebook comment normalized for the public code archive.
    df_prefix = read_agg_result()
    # Original notebook comment normalized for the public code archive.
    df_win = aggregate_across_window(df_prefix)
    # Original notebook comment normalized for the public code archive.
    for samp in SAMPLES:
        plot_window_agg_by_sample(df_win, sample=samp)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIX = "area50"
WINDOW = 10

SAMPLES = ["all", "urban", "rural"]


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


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
    df = df.copy()
    X = df[cols].astype("float64")

    g1_means = X.groupby(df[fe1]).transform("mean")
    g2_means = X.groupby(df[fe2]).transform("mean")
    mu = X.mean()

    X_dm = X - g1_means - g2_means + mu
    X_dm.columns = [f"{c}_dm" for c in cols]

    df = pd.concat([df, X_dm], axis=1)
    return df


def fe_reg_twoFE_city_cluster_fit(df: pd.DataFrame,
                                  y_col: str,
                                  x_cols,
                                  fe1: str,
                                  fe2: str,
                                  cluster_col: str):
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_and_plot_severity_curve():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    base_cols = [Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    df = df.dropna(subset=base_cols).copy()

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL, how="left",
        )
    else:
        df["urban_group"] = 1

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )

    # Original notebook comment normalized for the public code archive.
    any_col = f"share_DFO_any_{PREFIX}_{WINDOW}y"
    sev15_col = f"share_DFO_sev1_5_{PREFIX}_{WINDOW}y"
    sev2_col = f"share_DFO_sev2_{PREFIX}_{WINDOW}y"

    for col in [any_col, sev15_col, sev2_col]:
        if col not in df.columns:
            raise KeyError(f"缺少列 {col}，请确认前面的 DFO 面板是否包含该规格。")

    df[any_col] = pd.to_numeric(df[any_col], errors="coerce")
    df[sev15_col] = pd.to_numeric(df[sev15_col], errors="coerce").fillna(0.0)
    df[sev2_col] = pd.to_numeric(df[sev2_col], errors="coerce").fillna(0.0)

    df["sev_total"] = df[sev15_col] + df[sev2_col]

    # Original notebook comment normalized for the public code archive.
    df["ratio"] = np.where(
        df[any_col] > 0,
        df["sev_total"] / df[any_col],
        0.0,
    )
    df["ratio2"] = df["ratio"] ** 2

    # Original notebook comment normalized for the public code archive.
    sample_specs = {"all": None, "urban": 1, "rural": 0}

    # Original notebook comment normalized for the public code archive.
    lambda_grid = np.linspace(0.0, 1.0, 101)

    for sample_name, gval in sample_specs.items():
        if gval is None:
            sub = df.copy()
        else:
            sub = df[df["urban_group"] == gval].copy()

        # Original notebook comment normalized for the public code archive.
        waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
        keep_ids_sub = waves_sub[waves_sub >= 2].index
        sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

        if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
            print(
                f"[WARN] sample={sample_name} N 或 城市数过小 "
                f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
            )
            continue

        # Original notebook comment normalized for the public code archive.
        any0 = float(sub[any_col].mean())
        print(f"[INFO] sample={sample_name}, any0 (mean {any_col}) = {any0:.4f}")

        x_cols = [
            any_col,
            "any_ratio",      # any * ratio
            "any_ratio2",     # any * ratio^2
            "age",
            "age2",
        ]

        # Original notebook comment normalized for the public code archive.
        sub["any_ratio"] = sub[any_col] * sub["ratio"]
        sub["any_ratio2"] = sub[any_col] * sub["ratio2"]

        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        # =============================================================================
        beta = np.asarray(fit.params, dtype="float64")          # Original notebook comment normalized for the public code archive.
        cov = np.asarray(fit.cov_params(), dtype="float64")     # Original notebook comment normalized for the public code archive.

        idx = [0, 1, 2]  # Original notebook comment normalized for the public code archive.
        gamma = beta[idx]                          # (3,)
        Sigma = cov[np.ix_(idx, idx)]              # (3,3)

        # Original notebook comment normalized for the public code archive.
        beta_lambda = []
        se_lambda = []
        for lam in lambda_grid:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            beta_lambda.append(b)
            se_lambda.append(s)

        beta_lambda = np.array(beta_lambda)
        se_lambda = np.array(se_lambda)
        ci_low = beta_lambda - 1.96 * se_lambda
        ci_high = beta_lambda + 1.96 * se_lambda

        # Original notebook comment normalized for the public code archive.
        for lam in [0.0, 1.0]:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            if s > 0:
                t = b / s
                p = 2.0 * (1.0 - norm_cdf(abs(t)))
            else:
                p = np.nan
            print(f"[INFO] sample={sample_name}, λ={lam:.1f}: β={b:.4f}, p={p:.4g}")

        # Original notebook comment normalized for the public code archive.
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(lambda_grid, beta_lambda, label="β(λ) 估计")
        ax.fill_between(lambda_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlabel("严重洪水占比 λ（在总 DFO 暴露中的比例）")
        ax.set_ylabel("DFO 暴露对 health_index_z 的效应 β(λ)")
        ax.set_title(
            f"DFO 严重程度占比 λ 的非线性效应曲线\n"
            f"(prefix={PREFIX}, window={WINDOW}y, sample={sample_name})"
        )
        ax.set_xlim(0, 1)
        ax.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    run_and_plot_severity_curve()


# ------------------------------------------------------------------------------
# Notebook cell 30
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

SPATIAL_PREFIXES = ["centroid", "area50", "full"]
WINDOW_LIST = [5, 10, 20, 30]

SAMPLES = ["all", "urban", "rural"]


# =============================================================================

def norm_cdf(z: float) -> float:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    """Archived notebook note for 04_dfo_elderly_health_regression.

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


def summarize_coef(beta: float, var: float) -> dict:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if var <= 0 or not np.isfinite(var):
        return {
            "Estimate": beta,
            "Std. Error": np.nan,
            "t value": np.nan,
            "Pr(>|t|)": np.nan,
            "2.5%": np.nan,
            "97.5%": np.nan,
        }
    se = float(np.sqrt(var))
    t = beta / se
    p = 2.0 * (1.0 - norm_cdf(abs(t)))
    ci_low = beta - 1.96 * se
    ci_high = beta + 1.96 * se
    return {
        "Estimate": beta,
        "Std. Error": se,
        "t value": t,
        "Pr(>|t|)": p,
        "2.5%": ci_low,
        "97.5%": ci_high,
    }


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

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


def fe_reg_twoFE_city_cluster_fit(df: pd.DataFrame,
                                  y_col: str,
                                  x_cols,
                                  fe1: str,
                                  fe2: str,
                                  cluster_col: str):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_fe_severity_diff():
    print(f"[READ] merged panel with DFO: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    base_cols = [Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    df = df.dropna(subset=base_cols).copy()

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL,
            how="left",
        )
    else:
        df["urban_group"] = 1  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    sample_specs = {"all": None, "urban": 1, "rural": 0}
    all_rows = []

    for prefix in SPATIAL_PREFIXES:
        for window in WINDOW_LIST:
            sev1_col = f"share_DFO_sev1_{prefix}_{window}y"
            sev15_col = f"share_DFO_sev1_5_{prefix}_{window}y"
            sev2_col = f"share_DFO_sev2_{prefix}_{window}y"

            if sev1_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue
            if (sev15_col not in df.columns) or (sev2_col not in df.columns):
                print(
                    f"[WARN] 缺少 {sev15_col} 或 {sev2_col}，"
                    f"prefix={prefix}, window={window}，跳过。"
                )
                continue

            # Original notebook comment normalized for the public code archive.
            sev15_2_col = f"share_DFO_sev15_2_{prefix}_{window}y"
            df[sev15_2_col] = df[sev15_col].fillna(0) + df[sev2_col].fillna(0)

            for sample_name, gval in sample_specs.items():
                if gval is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == gval].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] prefix={prefix}, window={window}, sample={sample_name} "
                        f"样本量或城市数过小 (N={len(sub)}, "
                        f"N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                x_cols = [sev1_col, sev15_2_col, "age", "age2"]

                # Fixed-effects regression helper.
                fit = fe_reg_twoFE_city_cluster_fit(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                # Original notebook comment normalized for the public code archive.
                beta = fit.params
                cov = fit.cov_params()

                # Original notebook comment normalized for the public code archive.
                beta_sev1 = float(beta[0])
                beta_sev15_2 = float(beta[1])
                var_sev1 = float(cov[0, 0])
                var_sev15_2 = float(cov[1, 1])
                cov_12 = float(cov[0, 1])

                # Original notebook comment normalized for the public code archive.
                beta_diff = beta_sev15_2 - beta_sev1
                var_diff = var_sev15_2 + var_sev1 - 2.0 * cov_12

                # Original notebook comment normalized for the public code archive.
                for group_label, b, v in [
                    ("sev1", beta_sev1, var_sev1),
                    ("sev15_2", beta_sev15_2, var_sev15_2),
                    ("sevDiff", beta_diff, var_diff),
                ]:
                    summ = summarize_coef(b, v)
                    row = {
                        "Y_var": Y_VAR,
                        "prefix": prefix,
                        "window": window,
                        "sample": sample_name,
                        "group": group_label,  # sev1 / sev15_2 / sevDiff
                        "Estimate": summ["Estimate"],
                        "Std. Error": summ["Std. Error"],
                        "t value": summ["t value"],
                        "Pr(>|t|)": summ["Pr(>|t|)"],
                        "2.5%": summ["2.5%"],
                        "97.5%": summ["97.5%"],
                        "N": len(sub),
                        "N_id": sub[ID_COL].nunique(),
                        "N_year": sub[YEAR_COL].nunique(),
                        "N_city": sub[CLUSTER_COL].nunique(),
                    }
                    all_rows.append(row)

                print("\n" + "=" * 50)
                print(
                    f"[RESULT] prefix={prefix}, window={window}, sample={sample_name}"
                )
                print(f"  β(sev1)     = {beta_sev1:.4f}")
                print(f"  β(sev15+2)  = {beta_sev15_2:.4f}")
                print(f"  Δ = β_sev15+2 - β_sev1 = {beta_diff:.4f}")

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df.sort_values(
        ["prefix", "window", "sample", "group"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / f"fe_{Y_VAR}_DFO_sev1_vs_sev15_2_withDiff_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

def aggregate_diff_across_specs(df_all: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_all[df_all["group"] == "sevDiff"].copy()
    if df.empty:
        print("[INFO] Notebook progress message.")
        return None

    rows = []
    for (yvar, sample), g in df.groupby(["Y_var", "sample"]):
        betas = g["Estimate"].to_numpy(dtype="float64")
        ses = g["Std. Error"].to_numpy(dtype="float64")
        vars_ = ses ** 2
        vars_[vars_ <= 0] = 1e-12

        w = 1.0 / vars_
        beta_bar = float(np.sum(w * betas) / np.sum(w))
        var_bar = float(1.0 / np.sum(w))
        summ = summarize_coef(beta_bar, var_bar)

        # Original notebook comment normalized for the public code archive.
        spec_list = [
            f"{r['prefix']}_w{int(r['window'])}"
            for _, r in g.iterrows()
        ]
        row = {
            "Y_var": yvar,
            "sample": sample,
            "Estimate": summ["Estimate"],
            "Std. Error": summ["Std. Error"],
            "t value": summ["t value"],
            "Pr(>|t|)": summ["Pr(>|t|)"],
            "2.5%": summ["2.5%"],
            "97.5%": summ["97.5%"],
            "n_specs": len(g),
            "spec_list": "; ".join(spec_list),
        }
        rows.append(row)

    df_agg = pd.DataFrame(rows).sort_values(
        ["Y_var", "sample"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / f"fe_{Y_VAR}_DFO_sevDiff_cityCluster_prefixWindowAgg.csv"
    df_agg.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(df_agg)

    return df_agg


def plot_diff_by_sample(df_agg: pd.DataFrame):
    """Archived notebook note for 04_dfo_elderly_health_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_agg[df_agg["Y_var"] == Y_VAR].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    cat_order = ["all", "urban", "rural"]
    sub["sample"] = pd.Categorical(sub["sample"], categories=cat_order, ordered=True)
    sub = sub.sort_values("sample")

    x_labels = sub["sample"].tolist()
    x_pos = np.arange(len(x_labels))

    est = sub["Estimate"].to_numpy()
    ci_low = sub["2.5%"].to_numpy()
    ci_high = sub["97.5%"].to_numpy()
    p_vals = sub["Pr(>|t|)"].to_numpy()

    yerr_lower = est - ci_low
    yerr_upper = ci_high - est

    # Original notebook comment normalized for the public code archive.
    y_min = (est - yerr_lower).min()
    y_max = (est + yerr_upper).max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    offset = 0.03 * y_range

    fig, ax = plt.subplots(figsize=(6, 4))

    ax.errorbar(
        x_pos,
        est,
        yerr=[yerr_lower, yerr_upper],
        fmt="o-",
        capsize=5,
    )

    # Original notebook comment normalized for the public code archive.
    for xi, yi, pi in zip(x_pos, est, p_vals):
        s = stars_for_p(pi)
        if s:
            ax.text(
                xi,
                yi + offset,
                s,
                ha="center",
                va="bottom",
                fontsize=11,
            )

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["All", "Urban", "Rural"])
    ax.set_ylabel("Δ = β(sev1.5+2) − β(sev1)")
    ax.set_title("DFO 严重程度差值效应 Δ（跨 prefix & window 聚合）")
    plt.tight_layout()
    plt.show()


# ========= main =========

if __name__ == "__main__":
    # Fixed-effects regression helper.
    res_df = run_fe_severity_diff()

    # Original notebook comment normalized for the public code archive.
    if res_df is not None:
        agg_df = aggregate_diff_across_specs(res_df)
        if agg_df is not None:
            plot_diff_by_sample(agg_df)
