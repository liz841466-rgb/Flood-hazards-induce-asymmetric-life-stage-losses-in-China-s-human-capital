#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

OUT_DIR = os.path.join(BASE_DIR, "result/impact_assessment/flood_dfo_rep")
os.makedirs(OUT_DIR, exist_ok=True)

DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

OUT_FLOOD_CSV   = os.path.join(OUT_DIR, "county_year_panel_DFO_rep.csv")
OUT_COHORT_CSV  = os.path.join(OUT_DIR, "county_birthyear_exposure_DFO_rep.csv")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))
OUT_MICRO_PARQUET = Path(os.path.join(OUT_DIR, "edu_micro_2015_with_floodexp_DFO_rep.parquet"))

# Original notebook comment normalized for the public code archive.
MIN_AGE, MAX_AGE = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
FULL_COVER_TH = 0.99

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
# Original notebook comment normalized for the public code archive.
USE_SEVERITY = True

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SEV_OPTION = "2"

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SEV_STR_KEYWORD = "100"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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

    gdf_c = gdf_c.merge(df_area[["county_id", "county_code"]], on="county_code", how="inner")
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print("[INFO] Notebook progress message.")
    return gdf_c


def load_dfo() -> gpd.GeoDataFrame:
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

    # Original notebook comment normalized for the public code archive.
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
        gdf["severity_code"] = np.nan
        gdf["is_severe_100yr"] = 0
        print("[INFO] Notebook progress message.")
    else:
        raw = gdf[sev_col]
        sev_num = pd.to_numeric(raw, errors="coerce")
        gdf["severity_code"] = sev_num

        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

        if not USE_SEVERITY:
            gdf["is_severe_100yr"] = 0
            print("[INFO] Notebook progress message.")
        else:
            # Original notebook comment normalized for the public code archive.
            if SEV_OPTION == "1":
                is_100_num = np.isclose(sev_num, 1.0, equal_nan=False)
            elif SEV_OPTION in ("1.5", "1_5", "1.50"):
                is_100_num = np.isclose(sev_num, 1.5, equal_nan=False)
            elif SEV_OPTION == "2":
                is_100_num = np.isclose(sev_num, 2.0, equal_nan=False)
            elif SEV_OPTION == ">=1.5":
                is_100_num = sev_num >= 1.5
            else:
                raise ValueError(f"未知 SEV_OPTION: {SEV_OPTION}，允许值为 '1'/'1.5'/'2'/'>=1.5'")

            # Original notebook comment normalized for the public code archive.
            if SEV_STR_KEYWORD:
                is_100_str = raw.astype(str).str.contains(SEV_STR_KEYWORD, case=False, na=False)
            else:
                is_100_str = pd.Series(False, index=gdf.index)

            gdf["is_severe_100yr"] = (is_100_num | is_100_str).astype(int)

            n_severe = int(gdf["is_severe_100yr"].sum())
            print("[INFO] Notebook progress message.")

    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) & (gdf["year"] <= DFO_END_YEAR)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# ================================
# 2. DFO → county×year（centroid / area50 / full-cover）
# ================================
def build_dfo_county_year_panel(gdf_dfo: gpd.GeoDataFrame, gdf_c: gpd.GeoDataFrame) -> pd.DataFrame:
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()

    c_proj["area_cnt"] = c_proj.geometry.area

    # ------------------------------------------------
    # Original notebook comment normalized for the public code archive.
    # ------------------------------------------------
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner", predicate="within"
    )

    # Original notebook comment normalized for the public code archive.
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

    # ------------------------------------------------
    # Original notebook comment normalized for the public code archive.
    # ------------------------------------------------
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

    # ------------------------------------------------
    # County-level processing note.
    # ------------------------------------------------
    all_counties = gdf_c[["county_id","county_code"]].drop_duplicates()
    all_years = pd.DataFrame({"year": np.arange(DFO_START_YEAR, DFO_END_YEAR+1, dtype=int)})

    full_index = (
        all_counties.assign(key=1)
        .merge(all_years.assign(key=1), on="key")
        .drop(columns="key")
    )

    out = (
        full_index
        .merge(df_cent, on=["county_id","county_code","year"], how="left")
        .merge(df_a50, on=["county_id","county_code","year"], how="left")
        .merge(df_fullcov, on=["county_id","county_code","year"], how="left")
    )

    # Original notebook comment normalized for the public code archive.
    val_cols = [c for c in out.columns if c not in ["county_id","county_code","year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    int_cols = [c for c in val_cols if c.startswith(("flooded_", "severe_", "duration_", "flooded_times", "severe_times"))]
    for c in int_cols:
        out[c] = out[c].astype(int)

    print("[INFO] Notebook progress message.")
    return out


# ================================
# County-level processing note.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame, county_col="county_code") -> pd.DataFrame:
    df = df_flood.copy()
    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    ages = np.arange(MIN_AGE, MAX_AGE+1, dtype=int)
    rep = np.repeat(df.index.values, len(ages))
    age_vec = np.tile(ages, len(df))

    exp = df.loc[rep].copy()
    exp["age_in_year"] = age_vec
    exp["birth_year"] = exp["year"] - exp["age_in_year"]

    exp = exp[(exp["birth_year"] >= BIRTH_MIN) & (exp["birth_year"] <= BIRTH_MAX)].copy()
    group_cols = [county_col, "birth_year"]

    agg = {
        "n_years_window": ("year","nunique"),
    }

    # Original notebook comment normalized for the public code archive.
    def add_measure(prefix):
        any_col   = f"flooded_any_{prefix}"
        times_col = f"flooded_times_{prefix}"
        dur_col   = f"duration_days_{prefix}"
        sev_any   = f"severe_any_{prefix}"
        sev_times = f"severe_times_{prefix}"
        sev_dur   = f"severe_duration_{prefix}"

        if any_col in exp.columns:
            agg[f"years_{any_col}"] = (any_col, "sum")
            agg[f"share_{any_col}"] = (any_col, "mean")

        if times_col in exp.columns:
            agg[f"sum_{times_col}"] = (times_col, "sum")
            agg[f"avg_{times_col}"] = (times_col, "mean")

        if dur_col in exp.columns:
            agg[f"sum_{dur_col}"] = (dur_col, "sum")
            agg[f"avg_{dur_col}"] = (dur_col, "mean")

        if sev_any in exp.columns:
            agg[f"years_{sev_any}"] = (sev_any, "sum")
            agg[f"share_{sev_any}"] = (sev_any, "mean")

        if sev_times in exp.columns:
            agg[f"sum_{sev_times}"] = (sev_times, "sum")
            agg[f"avg_{sev_times}"] = (sev_times, "mean")

        if sev_dur in exp.columns:
            agg[f"sum_{sev_dur}"] = (sev_dur, "sum")
            agg[f"avg_{sev_dur}"] = (sev_dur, "mean")

    for p in ["centroid", "area50", "full"]:
        add_measure(p)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()

    # ---------------------------
    # Original notebook comment normalized for the public code archive.
    # ---------------------------
    if "flooded_any_centroid" in exp.columns:
        def seg_share(lo, hi, name):
            m = exp["age_in_year"].between(lo, hi)
            tmp = exp[m].groupby(group_cols)["flooded_any_centroid"].mean().reset_index()
            tmp = tmp.rename(columns={"flooded_any_centroid": name})
            return tmp

        s0_5   = seg_share(0, 5,  "share_flooded_any_age0_5")
        s6_12  = seg_share(6, 12, "share_flooded_any_age6_12")
        s13_15 = seg_share(13, 15,"share_flooded_any_age13_15")

        cohort = cohort.merge(s0_5, on=group_cols, how="left") \
                       .merge(s6_12, on=group_cols, how="left") \
                       .merge(s13_15, on=group_cols, how="left")

        for c in ["share_flooded_any_age0_5","share_flooded_any_age6_12","share_flooded_any_age13_15"]:
            cohort[c] = cohort[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return cohort


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def merge_exposure_to_micro(df_cohort: pd.DataFrame, county_col="county_code") -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[(edu["age_2015"] >= 15) & (edu["age_2015"] <= 30)]

    edu = edu[(edu["birth_year"] >= BIRTH_MIN) & (edu["birth_year"] <= BIRTH_MAX)].copy()

    cohort = df_cohort.copy()
    cohort[county_col] = pd.to_numeric(cohort[county_col], errors="coerce").astype("Int64")
    cohort = cohort.rename(columns={county_col:"county_code"})

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort, how="left",
        on=["county_code","birth_year"],
        validate="m:1"
    )

    exp_cols = [c for c in merged.columns if c.startswith(("years_","share_","sum_","avg_"))] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return merged


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    gdf_c = load_counties()
    gdf_dfo = load_dfo()

    df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
    df_flood.to_csv(OUT_FLOOD_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    print("[DONE] DFO replication exposure pipeline finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

OUT_DIR = os.path.join(BASE_DIR, "result/impact_assessment/flood_dfo_rep")
os.makedirs(OUT_DIR, exist_ok=True)

DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

OUT_FLOOD_CSV   = os.path.join(OUT_DIR, "county_year_panel_DFO_rep.csv")
OUT_COHORT_CSV  = os.path.join(OUT_DIR, "county_birthyear_exposure_DFO_rep.csv")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))
OUT_MICRO_PARQUET = Path(os.path.join(OUT_DIR, "edu_micro_2015_with_floodexp_DFO_rep.parquet"))

# Original notebook comment normalized for the public code archive.
MIN_AGE, MAX_AGE = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000

# Original notebook comment normalized for the public code archive.
EA_CRS = "EPSG:6933"   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
FULL_COVER_TH = 0.99

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
# Original notebook comment normalized for the public code archive.
USE_SEVERITY = True

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SEV_OPTION = "1"

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SEV_STR_KEYWORD = ""


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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

    gdf_c = gdf_c.merge(df_area[["county_id", "county_code"]], on="county_code", how="inner")
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print("[INFO] Notebook progress message.")
    return gdf_c


def load_dfo() -> gpd.GeoDataFrame:
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

    # Original notebook comment normalized for the public code archive.
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
        gdf["severity_code"] = np.nan
        gdf["is_severe_100yr"] = 0
        print("[INFO] Notebook progress message.")
    else:
        raw = gdf[sev_col]
        sev_num = pd.to_numeric(raw, errors="coerce")
        gdf["severity_code"] = sev_num

        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

        if not USE_SEVERITY:
            gdf["is_severe_100yr"] = 0
            print("[INFO] Notebook progress message.")
        else:
            # Original notebook comment normalized for the public code archive.
            if SEV_OPTION == "1":
                is_100_num = np.isclose(sev_num, 1.0, equal_nan=False)
            elif SEV_OPTION in ("1.5", "1_5", "1.50"):
                is_100_num = np.isclose(sev_num, 1.5, equal_nan=False)
            elif SEV_OPTION == "2":
                is_100_num = np.isclose(sev_num, 2.0, equal_nan=False)
            elif SEV_OPTION == ">=1.5":
                is_100_num = sev_num >= 1.5
            else:
                raise ValueError(f"未知 SEV_OPTION: {SEV_OPTION}，允许值为 '1'/'1.5'/'2'/'>=1.5'")

            # Original notebook comment normalized for the public code archive.
            if SEV_STR_KEYWORD:
                is_100_str = raw.astype(str).str.contains(SEV_STR_KEYWORD, case=False, na=False)
            else:
                is_100_str = pd.Series(False, index=gdf.index)

            gdf["is_severe_100yr"] = (is_100_num | is_100_str).astype(int)

            n_severe = int(gdf["is_severe_100yr"].sum())
            print("[INFO] Notebook progress message.")

    gdf = gdf[(gdf["year"] >= DFO_START_YEAR) & (gdf["year"] <= DFO_END_YEAR)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# ================================
# 2. DFO → county×year（centroid / area50 / full-cover）
# ================================
def build_dfo_county_year_panel(gdf_dfo: gpd.GeoDataFrame, gdf_c: gpd.GeoDataFrame) -> pd.DataFrame:
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()

    c_proj["area_cnt"] = c_proj.geometry.area

    # ------------------------------------------------
    # Original notebook comment normalized for the public code archive.
    # ------------------------------------------------
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner", predicate="within"
    )

    # Original notebook comment normalized for the public code archive.
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

    # ------------------------------------------------
    # Original notebook comment normalized for the public code archive.
    # ------------------------------------------------
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

    # ------------------------------------------------
    # County-level processing note.
    # ------------------------------------------------
    all_counties = gdf_c[["county_id","county_code"]].drop_duplicates()
    all_years = pd.DataFrame({"year": np.arange(DFO_START_YEAR, DFO_END_YEAR+1, dtype=int)})

    full_index = (
        all_counties.assign(key=1)
        .merge(all_years.assign(key=1), on="key")
        .drop(columns="key")
    )

    out = (
        full_index
        .merge(df_cent, on=["county_id","county_code","year"], how="left")
        .merge(df_a50, on=["county_id","county_code","year"], how="left")
        .merge(df_fullcov, on=["county_id","county_code","year"], how="left")
    )

    # Original notebook comment normalized for the public code archive.
    val_cols = [c for c in out.columns if c not in ["county_id","county_code","year"]]
    for c in val_cols:
        out[c] = out[c].fillna(0)

    int_cols = [c for c in val_cols if c.startswith(("flooded_", "severe_", "duration_", "flooded_times", "severe_times"))]
    for c in int_cols:
        out[c] = out[c].astype(int)

    print("[INFO] Notebook progress message.")
    return out


# ================================
# County-level processing note.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame, county_col="county_code") -> pd.DataFrame:
    df = df_flood.copy()
    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    ages = np.arange(MIN_AGE, MAX_AGE+1, dtype=int)
    rep = np.repeat(df.index.values, len(ages))
    age_vec = np.tile(ages, len(df))

    exp = df.loc[rep].copy()
    exp["age_in_year"] = age_vec
    exp["birth_year"] = exp["year"] - exp["age_in_year"]

    exp = exp[(exp["birth_year"] >= BIRTH_MIN) & (exp["birth_year"] <= BIRTH_MAX)].copy()
    group_cols = [county_col, "birth_year"]

    agg = {
        "n_years_window": ("year","nunique"),
    }

    # Original notebook comment normalized for the public code archive.
    def add_measure(prefix):
        any_col   = f"flooded_any_{prefix}"
        times_col = f"flooded_times_{prefix}"
        dur_col   = f"duration_days_{prefix}"
        sev_any   = f"severe_any_{prefix}"
        sev_times = f"severe_times_{prefix}"
        sev_dur   = f"severe_duration_{prefix}"

        if any_col in exp.columns:
            agg[f"years_{any_col}"] = (any_col, "sum")
            agg[f"share_{any_col}"] = (any_col, "mean")

        if times_col in exp.columns:
            agg[f"sum_{times_col}"] = (times_col, "sum")
            agg[f"avg_{times_col}"] = (times_col, "mean")

        if dur_col in exp.columns:
            agg[f"sum_{dur_col}"] = (dur_col, "sum")
            agg[f"avg_{dur_col}"] = (dur_col, "mean")

        if sev_any in exp.columns:
            agg[f"years_{sev_any}"] = (sev_any, "sum")
            agg[f"share_{sev_any}"] = (sev_any, "mean")

        if sev_times in exp.columns:
            agg[f"sum_{sev_times}"] = (sev_times, "sum")
            agg[f"avg_{sev_times}"] = (sev_times, "mean")

        if sev_dur in exp.columns:
            agg[f"sum_{sev_dur}"] = (sev_dur, "sum")
            agg[f"avg_{sev_dur}"] = (sev_dur, "mean")

    for p in ["centroid", "area50", "full"]:
        add_measure(p)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()

    # ---------------------------
    # Original notebook comment normalized for the public code archive.
    # ---------------------------
    if "flooded_any_centroid" in exp.columns:
        def seg_share(lo, hi, name):
            m = exp["age_in_year"].between(lo, hi)
            tmp = exp[m].groupby(group_cols)["flooded_any_centroid"].mean().reset_index()
            tmp = tmp.rename(columns={"flooded_any_centroid": name})
            return tmp

        s0_5   = seg_share(0, 5,  "share_flooded_any_age0_5")
        s6_12  = seg_share(6, 12, "share_flooded_any_age6_12")
        s13_15 = seg_share(13, 15,"share_flooded_any_age13_15")

        cohort = cohort.merge(s0_5, on=group_cols, how="left") \
                       .merge(s6_12, on=group_cols, how="left") \
                       .merge(s13_15, on=group_cols, how="left")

        for c in ["share_flooded_any_age0_5","share_flooded_any_age6_12","share_flooded_any_age13_15"]:
            cohort[c] = cohort[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return cohort


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def merge_exposure_to_micro(df_cohort: pd.DataFrame, county_col="county_code") -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[(edu["age_2015"] >= 15) & (edu["age_2015"] <= 30)]

    edu = edu[(edu["birth_year"] >= BIRTH_MIN) & (edu["birth_year"] <= BIRTH_MAX)].copy()

    cohort = df_cohort.copy()
    cohort[county_col] = pd.to_numeric(cohort[county_col], errors="coerce").astype("Int64")
    cohort = cohort.rename(columns={county_col:"county_code"})

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort, how="left",
        on=["county_code","birth_year"],
        validate="m:1"
    )

    exp_cols = [c for c in merged.columns if c.startswith(("years_","share_","sum_","avg_"))] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return merged


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    gdf_c = load_counties()
    gdf_dfo = load_dfo()

    df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
    df_flood.to_csv(OUT_FLOOD_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    print("[DONE] DFO replication exposure pipeline finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

# ================================
# Original notebook comment normalized for the public code archive.
# ================================

# External flood dataset comparison note.
DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood_dfo_rep/"
    "edu_micro_2015_with_floodexp_DFO_rep.parquet"
)

# Original notebook comment normalized for the public code archive.
STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood_dfo_rep/statistics"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------
# Original notebook comment normalized for the public code archive.
# ----------------
# External flood dataset comparison note.
# Original notebook comment normalized for the public code archive.
EXPOSURE_MODE = "severe100"

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SPATIAL_PREFIX = "centroid"

# Original notebook comment normalized for the public code archive.
def _main_cols(mode, prefix):
    if mode == "all_flood":
        any_col = f"flooded_any_{prefix}"
    elif mode == "severe100":
        any_col = f"severe_any_{prefix}"
    else:
        raise ValueError("EXPOSURE_MODE 只能是 all_flood / severe100")
    return f"share_{any_col}", f"years_{any_col}"

MAIN_SHARE, MAIN_YEARS = _main_cols(EXPOSURE_MODE, SPATIAL_PREFIX)

# ----------------
# Original notebook comment normalized for the public code archive.
# ----------------
BIRTH_MIN = 1980
BIRTH_MAX = 2000
AGE_MIN = 15
AGE_MAX = 35

# Original notebook comment normalized for the public code archive.
SAMPLE_URBAN   = "urban"         # "rural" / "urban" / "all"
SAMPLE_MIGRANT = "non_migrant"         # "non_migrant" / "migrant" / "all"
EXCLUDE_IN_SCHOOL = False      # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
RUN_AGE_SEG_ROBUST = False


# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def load_and_prepare_data():
    print("Reading data...")
    df = pd.read_parquet(DATA_PARQUET)
    print(f"Raw shape: {df.shape}")

    # Original notebook comment normalized for the public code archive.
    cols_to_numeric = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        MAIN_SHARE, MAIN_YEARS,
        # Original notebook comment normalized for the public code archive.
        "share_flooded_any_age0_5",
        "share_flooded_any_age6_12",
        "share_flooded_any_age13_15",
    ]
    for c in cols_to_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    if "is_migrant" not in df.columns and "M38" in df.columns:
        # Original notebook comment normalized for the public code archive.
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    # --------------------------
    # Original notebook comment normalized for the public code archive.
    # --------------------------
    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    if SAMPLE_URBAN == "rural":
        mask &= (df["is_urban"] == 0)
    elif SAMPLE_URBAN == "urban":
        mask &= (df["is_urban"] == 1)

    # Original notebook comment normalized for the public code archive.
    if SAMPLE_MIGRANT == "non_migrant":
        mask &= (df["is_migrant"] == 0)
    elif SAMPLE_MIGRANT == "migrant":
        mask &= (df["is_migrant"] == 1)

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= (df["age_2015"] >= AGE_MIN) & (df["age_2015"] <= AGE_MAX)
    if "birth_year" in df.columns:
        mask &= (df["birth_year"] >= BIRTH_MIN) & (df["birth_year"] <= BIRTH_MAX)

    # Original notebook comment normalized for the public code archive.
    if EXCLUDE_IN_SCHOOL and "M52" in df.columns:
        in_school = (df["M52"] == 1)
        print(f"Drop in-school (M52=1): {in_school.sum()} obs")
        mask &= (~in_school)

    df_model = df[mask].copy()

    # Original notebook comment normalized for the public code archive.
    required_cols = ["edu_years", MAIN_SHARE, MAIN_YEARS, "M2", "birth_year"]
    missing = [c for c in required_cols if c not in df_model.columns]
    if missing:
        raise ValueError(f"Missing required cols: {missing}")

    # Original notebook comment normalized for the public code archive.
    cat_cols = ["M34", "M37", "M15", "M16"]
    req_vars = required_cols + [c for c in cat_cols if c in df_model.columns]

    # Original notebook comment normalized for the public code archive.
    df_model = df_model.dropna(subset=req_vars)
    print(f"Final N after dropping NA: {len(df_model)}")

    # --------------------------
    # Original notebook comment normalized for the public code archive.
    # --------------------------
    df_model["prov_code"] = (df_model["M2"] // 10000).astype(int)
    df_model["prov_birth_fe"] = (
        df_model["prov_code"].astype(str) + "_" +
        df_model["birth_year"].astype(int).astype(str)
    )

    # Original notebook comment normalized for the public code archive.
    df_model["birth_year_c"] = df_model["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in cat_cols:
        if c in df_model.columns:
            df_model[c] = df_model[c].astype(int).astype("category")
            df_model[c] = df_model[c].cat.remove_unused_categories()

    # --------------------------
    # Original notebook comment normalized for the public code archive.
    # --------------------------
    df_model["years_main"] = df_model[MAIN_YEARS].fillna(0).astype(int)
    df_model["DFO_1"]   = (df_model["years_main"] == 1).astype(int)
    df_model["DFO_2_3"] = df_model["years_main"].between(2, 3).astype(int)
    df_model["DFO_ge4"] = (df_model["years_main"] >= 4).astype(int)

    return df_model.reset_index(drop=True)


# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def run_analysis():
    df = load_and_prepare_data()

    # Original notebook comment normalized for the public code archive.
    controls = "C(M34) + C(M37) + C(M15) + C(M16)"

    # Original notebook comment normalized for the public code archive.
    def process_tidy(fit_obj):
        res = fit_obj.tidy().reset_index()
        first_col = res.columns[0]
        if first_col != "Term":
            res = res.rename(columns={first_col: "Term"})
        return res

    # =================================================
    # Original notebook comment normalized for the public code archive.
    # =================================================
    print(f"\nFitting linear model using {MAIN_SHARE} ...")
    fml_cont = (
        f"edu_years ~ {MAIN_SHARE} + {controls} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit_cont = feols(fml_cont, data=df, vcov={"CRV1": "M2"})
    res_cont = process_tidy(fit_cont)
    key_cont = res_cont[res_cont["Term"].str.contains(MAIN_SHARE, na=False)]

    print("\n[Linear] Core coefficient(s):")
    print(key_cont)

    out_name = (
        f"res_DFO_{EXPOSURE_MODE}_{SPATIAL_PREFIX}_"
        f"{SAMPLE_URBAN}_{SAMPLE_MIGRANT}_"
        f"excludeSch{EXCLUDE_IN_SCHOOL}_linear.csv"
    )
    key_cont.to_csv(STATS_DIR / out_name, index=False, encoding="utf-8-sig")
    print(f"Saved: {STATS_DIR / out_name}")

    # =================================================
    # External flood dataset comparison note.
    # =================================================
    print("\nFitting nonlinear grouped model ...")
    fml_cat = (
        f"edu_years ~ DFO_1 + DFO_2_3 + DFO_ge4 + "
        f"{controls} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit_cat = feols(fml_cat, data=df, vcov={"CRV1": "M2"})
    res_cat = process_tidy(fit_cat)
    key_cat = res_cat[res_cat["Term"].str.contains("DFO_", na=False)]

    print("\n[Nonlinear] Core coefficient(s):")
    print(key_cat)

    out_name_cat = (
        f"res_DFO_{EXPOSURE_MODE}_{SPATIAL_PREFIX}_"
        f"{SAMPLE_URBAN}_{SAMPLE_MIGRANT}_"
        f"excludeSch{EXCLUDE_IN_SCHOOL}_nonlinear.csv"
    )
    key_cat.to_csv(STATS_DIR / out_name_cat, index=False, encoding="utf-8-sig")
    print(f"Saved: {STATS_DIR / out_name_cat}")

    # =================================================
    # Original notebook comment normalized for the public code archive.
    # share_flooded_any_age0_5 / 6_12 / 13_15
    # =================================================
    if RUN_AGE_SEG_ROBUST:
        seg_cols = [
            "share_flooded_any_age0_5",
            "share_flooded_any_age6_12",
            "share_flooded_any_age13_15",
        ]
        if all(c in df.columns for c in seg_cols):
            print("\nFitting age-segment robustness model (A4) ...")
            fml_seg = (
                "edu_years ~ share_flooded_any_age0_5 + "
                "share_flooded_any_age6_12 + "
                "share_flooded_any_age13_15 + "
                f"{controls} + i(M2, birth_year_c) | M2 + prov_birth_fe"
            )
            fit_seg = feols(fml_seg, data=df, vcov={"CRV1": "M2"})
            res_seg = process_tidy(fit_seg)
            key_seg = res_seg[res_seg["Term"].str.contains("share_flooded_any_age", na=False)]

            print("\n[Age segments] Core coefficient(s):")
            print(key_seg)

            out_name_seg = (
                f"res_DFO_ageSeg_{SAMPLE_URBAN}_{SAMPLE_MIGRANT}_"
                f"excludeSch{EXCLUDE_IN_SCHOOL}.csv"
            )
            key_seg.to_csv(STATS_DIR / out_name_seg, index=False, encoding="utf-8-sig")
            print(f"Saved: {STATS_DIR / out_name_seg}")
        else:
            print("[WARN] Age-segment share columns missing. Skip A4 robustness.")

    print("\n[DONE] DFO exposure regressions finished.")


if __name__ == "__main__":
    run_analysis()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ONE-STOP DFO pipeline + batch regressions + plots
(robust version: fixes IntCastingNaNError)

Generates micro data under:
- severe definition severity ∈ {1, 1.5, 2}
Then runs regressions for:
- exposure: all_flood + severe100(sev=1/1.5/2)
- spatial: centroid / area50 / full
- subsample: rural / urban, only non_migrant
- models: linear share + nonlinear grouped years
Outputs:
- one combined CSV
- two coefficient plots
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

# ================================
# 0. PATHS & GLOBAL PARAMS
# ================================
BASE_DIR = "/home/ll/jupyter_notebook"

COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv")

DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

EDU_PARQUET = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood/edu_micro_2015.parquet"))

OUT_DIR = Path(os.path.join(BASE_DIR, "result/impact_assessment/flood_dfo_rep/batch_oneclick"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_RESULTS_CSV   = OUT_DIR / "batch_DFO_severity_spatial_sample_results.csv"
OUT_PLOT_LINEAR   = OUT_DIR / "coefplot_linear_share.png"
OUT_PLOT_NONLIN   = OUT_DIR / "coefplot_nonlinear_groups.png"

DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

# cohort window
MIN_AGE, MAX_AGE = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000

# equal-area CRS
EA_CRS = "EPSG:6933"
FULL_COVER_TH = 0.99

# severe options to loop
SEV_OPTIONS = ["1", "1.5", "2"]
USE_SEVERITY = True
SEV_STR_KEYWORD = ""   # keep empty to avoid textual fallback

# regression dimensions
SPATIAL_PREFIXES = ["centroid", "area50", "full"]
SAMPLES_URBAN = ["rural", "urban"]   # only these two
EXPOSURE_MODES = ["all_flood", "severe100"]

# sample restrictions
AGE_MIN, AGE_MAX = 15, 35

# controls (same as your previous scripts)
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
CAT_COLS = ["M34", "M37", "M15", "M16"]


# ================================
# 1. BASIC GIS LOAD
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

    gdf_c = gdf_c.merge(df_area[["county_id", "county_code"]],
                        on="county_code", how="inner")
    gdf_c["county_id"] = gdf_c["county_id"].astype(int)

    print(f"[INFO] Counties matched: {gdf_c.shape[0]}")
    return gdf_c


def load_dfo_raw() -> gpd.GeoDataFrame:
    """Load once, parse dates/years/duration/severity_code; without severe flag."""
    gdf = gpd.read_file(DFO_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf = _make_valid(gdf).reset_index(drop=True)
    gdf["event_id"] = np.arange(len(gdf), dtype=int)

    # dates
    gdf["BEGAN_dt"] = pd.to_datetime(gdf.get("BEGAN"), errors="coerce")
    gdf["ENDED_dt"] = pd.to_datetime(gdf.get("ENDED"), errors="coerce")
    miss_end = gdf["ENDED_dt"].isna() & gdf["BEGAN_dt"].notna()
    gdf.loc[miss_end, "ENDED_dt"] = gdf.loc[miss_end, "BEGAN_dt"]

    # mid-year
    gdf["mid_date"] = gdf["BEGAN_dt"]
    has_both = gdf["BEGAN_dt"].notna() & gdf["ENDED_dt"].notna()
    gdf.loc[has_both, "mid_date"] = (
        gdf.loc[has_both, "BEGAN_dt"]
        + (gdf.loc[has_both, "ENDED_dt"] - gdf.loc[has_both, "BEGAN_dt"]) / 2
    )
    gdf["year"] = gdf["mid_date"].dt.year
    gdf = gdf.dropna(subset=["year"]).copy()
    gdf["year"] = gdf["year"].astype(int)

    # duration
    gdf["duration_days"] = (gdf["ENDED_dt"] - gdf["BEGAN_dt"]).dt.days + 1
    gdf.loc[gdf["duration_days"].isna(), "duration_days"] = 1
    gdf["duration_days"] = gdf["duration_days"].clip(lower=1)

    # severity col
    sev_col = None
    for c in ["SEVERITY", "Severity", "severity"]:
        if c in gdf.columns:
            sev_col = c
            break
    if sev_col is None:
        gdf["severity_raw"] = np.nan
        gdf["severity_code"] = np.nan
        print("[WARN] No severity column found.")
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
    """Return a COPY with is_severe_100yr set by sev_option."""
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
# 2. DFO -> county×year panel
# ================================
def build_dfo_county_year_panel(gdf_dfo: gpd.GeoDataFrame,
                               gdf_c: gpd.GeoDataFrame) -> pd.DataFrame:
    c_proj   = gdf_c.to_crs(EA_CRS).copy()
    dfo_proj = gdf_dfo.to_crs(EA_CRS).copy()
    c_proj["area_cnt"] = c_proj.geometry.area

    # 2.1 centroid baseline
    c_cent = c_proj[["county_id", "county_code", "geometry"]].copy()
    c_cent["centroid"] = c_cent.geometry.centroid

    cent_join = gpd.sjoin(
        c_cent.set_geometry("centroid")[["county_id", "county_code", "centroid"]],
        dfo_proj[["event_id", "year", "duration_days", "is_severe_100yr", "geometry"]],
        how="inner", predicate="within"
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

    # 2.2 area overlay
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

    # full index
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

    return out


# ================================
# County-level processing note.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame,
                                    county_col="county_code") -> pd.DataFrame:
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
        times_col = f"flooded_times_{prefix}"
        dur_col   = f"duration_days_{prefix}"
        sev_any   = f"severe_any_{prefix}"
        sev_times = f"severe_times_{prefix}"
        sev_dur   = f"severe_duration_{prefix}"

        if any_col in exp.columns:
            agg[f"years_{any_col}"] = (any_col, "sum")
            agg[f"share_{any_col}"] = (any_col, "mean")
        if times_col in exp.columns:
            agg[f"sum_{times_col}"] = (times_col, "sum")
            agg[f"avg_{times_col}"] = (times_col, "mean")
        if dur_col in exp.columns:
            agg[f"sum_{dur_col}"] = (dur_col, "sum")
            agg[f"avg_{dur_col}"] = (dur_col, "mean")
        if sev_any in exp.columns:
            agg[f"years_{sev_any}"] = (sev_any, "sum")
            agg[f"share_{sev_any}"] = (sev_any, "mean")
        if sev_times in exp.columns:
            agg[f"sum_{sev_times}"] = (sev_times, "sum")
            agg[f"avg_{sev_times}"] = (sev_times, "mean")
        if sev_dur in exp.columns:
            agg[f"sum_{sev_dur}"] = (sev_dur, "sum")
            agg[f"avg_{sev_dur}"] = (sev_dur, "mean")

    for p in ["centroid", "area50", "full"]:
        add_measure(p)

    cohort = exp.groupby(group_cols).agg(**agg).reset_index()
    return cohort


# ================================
# 4. Merge exposure to micro
# ================================
def merge_exposure_to_micro(df_cohort: pd.DataFrame,
                            county_col="county_code") -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
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

    merged = edu.merge(cohort, how="left",
                       on=["county_code","birth_year"],
                       validate="m:1")

    exp_cols = [c for c in merged.columns if c.startswith(("years_","share_","sum_","avg_"))] + ["n_years_window"]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    return merged


# ================================
# 5. REGRESSION HELPERS (FIXED)
# ================================
def main_cols(mode, prefix):
    if mode == "all_flood":
        any_col = f"flooded_any_{prefix}"
    elif mode == "severe100":
        any_col = f"severe_any_{prefix}"
    else:
        raise ValueError("mode must be all_flood / severe100")
    return f"share_{any_col}", f"years_{any_col}"


def load_and_prepare_for_reg(df_micro: pd.DataFrame,
                             main_share: str,
                             main_years: str,
                             sample_urban: str) -> pd.DataFrame:
    """
    FIX:
    - Do NOT cast cat cols via astype(int) before NA handling.
    - Coerce to numeric, drop NA, then Int64->category.
    """
    df = df_micro.copy()

    # numeric conversion brute-force
    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        main_share, main_years
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # is_urban / is_migrant
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    mask = pd.Series(True, index=df.index)

    # only non_migrant
    mask &= (df["is_migrant"] == 0)

    # rural/urban
    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    # windows
    if "age_2015" in df.columns:
        mask &= (df["age_2015"] >= AGE_MIN) & (df["age_2015"] <= AGE_MAX)
    mask &= (df["birth_year"] >= BIRTH_MIN) & (df["birth_year"] <= BIRTH_MAX)

    dfm = df[mask].copy()

    # required + controls present
    required = ["edu_years", main_share, main_years, "M2", "birth_year"]
    cat_present = [c for c in CAT_COLS if c in dfm.columns]
    drop_cols = required + cat_present

    dfm = dfm.dropna(subset=drop_cols)

    # FE vars
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # categorical controls (safe)
    for c in cat_present:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce").astype("Int64")
        # after dropna, no NA remains; safe to category
        dfm[c] = dfm[c].astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # nonlinear groups
    dfm["years_main"] = dfm[main_years].fillna(0).astype(int)
    dfm["DFO_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["DFO_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["DFO_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)


def tidy_with_term(fit):
    res = fit.tidy().reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    return res


def get_nobs(fit):
    """
    Robust nobs getter for different pyfixest versions.
    Tries several possible attribute names.
    """
    for attr in ["nobs", "n_obs", "N", "_N", "nobs_"]:
        if hasattr(fit, attr):
            v = getattr(fit, attr)
            try:
                return int(v() if callable(v) else v)
            except Exception:
                pass
    # final fallback: length of tidy() sample if available
    try:
        return int(fit.tidy().attrs.get("nobs"))
    except Exception:
        return np.nan


def run_one_reg(df, main_share):
    # linear
    fml_lin = (
        f"edu_years ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit_lin = feols(fml_lin, data=df, vcov={"CRV1": "M2"})
    res_lin = tidy_with_term(fit_lin)
    key_lin = res_lin[res_lin["Term"].str.contains(main_share, na=False)].copy()
    key_lin["model"] = "linear"
    key_lin["nobs"] = get_nobs(fit_lin)

    # nonlinear
    fml_non = (
        f"edu_years ~ DFO_1 + DFO_2_3 + DFO_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit_non = feols(fml_non, data=df, vcov={"CRV1": "M2"})
    res_non = tidy_with_term(fit_non)
    key_non = res_non[res_non["Term"].str.contains('DFO_', na=False)].copy()
    key_non["model"] = "nonlinear"
    key_non["nobs"] = get_nobs(fit_non)

    return pd.concat([key_lin, key_non], ignore_index=True)


# ================================
# 6. PLOTTING
# ================================
def coefplot_linear(df_res: pd.DataFrame, out_png: Path):
    d = df_res[df_res["model"] == "linear"].copy()
    if d.empty:
        print("[WARN] No linear results to plot.")
        return

    # try to find estimate/SE columns robustly
    col_est = next(c for c in d.columns if c.lower().startswith("estimate"))
    col_se  = next(c for c in d.columns if "std" in c.lower())

    d["label"] = d["exposure_label"]
    d["xcat"] = d["spatial_prefix"] + "_" + d["sample_urban"]

    xcats = sorted(d["xcat"].unique())
    labels = sorted(d["label"].unique())

    xbase = np.arange(len(xcats))
    width = 0.15 if len(labels) > 1 else 0.0

    plt.figure()
    for i, lab in enumerate(labels):
        sub = d[d["label"] == lab].set_index("xcat").reindex(xcats)
        x = xbase + (i - (len(labels)-1)/2)*width
        y = sub[col_est].values
        se = sub[col_se].values
        plt.errorbar(x, y, yerr=1.96*se, fmt="o", label=lab)

    plt.axhline(0, linewidth=1)
    plt.xticks(xbase, xcats, rotation=45, ha="right")
    plt.ylabel("Coefficient (linear share)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"[INFO] Saved linear coefplot: {out_png}")


def coefplot_nonlinear(df_res: pd.DataFrame, out_png: Path):
    d = df_res[df_res["model"] == "nonlinear"].copy()
    if d.empty:
        print("[WARN] No nonlinear results to plot.")
        return

    col_est = next(c for c in d.columns if c.lower().startswith("estimate"))
    col_se  = next(c for c in d.columns if "std" in c.lower())

    d["label"] = d["exposure_label"]
    d["xcat"] = d["spatial_prefix"] + "_" + d["sample_urban"]
    terms = ["DFO_1", "DFO_2_3", "DFO_ge4"]

    xcats = sorted(d["xcat"].unique())
    labels = sorted(d["label"].unique())

    grid = [(t, xc) for t in terms for xc in xcats]
    xbase = np.arange(len(grid))
    width = 0.15 if len(labels) > 1 else 0.0

    plt.figure()
    for i, lab in enumerate(labels):
        sub = d[d["label"] == lab].copy()
        sub = sub.set_index(["Term", "xcat"]).reindex(grid)
        x = xbase + (i - (len(labels)-1)/2)*width
        y = sub[col_est].values
        se = sub[col_se].values
        plt.errorbar(x, y, yerr=1.96*se, fmt="o", label=lab)

    plt.axhline(0, linewidth=1)
    xticklabels = [f"{t}:{xc}" for (t, xc) in grid]
    plt.xticks(xbase, xticklabels, rotation=90, ha="center")
    plt.ylabel("Coefficient (nonlinear groups)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"[INFO] Saved nonlinear coefplot: {out_png}")


# ================================
# 7. MAIN ONE-CLICK RUN
# ================================
def main():
    # 7.1 load GIS once
    gdf_c = load_counties()
    gdf_dfo_raw = load_dfo_raw()

    # 7.2 generate micro under each sev_option
    micro_by_sev = {}
    for sev_opt in SEV_OPTIONS:
        print(f"\n[PIPELINE] Building micro with SEV_OPTION={sev_opt} ...")
        gdf_dfo = apply_severity_flag(gdf_dfo_raw, sev_opt,
                                      use_severity=USE_SEVERITY,
                                      sev_str_keyword=SEV_STR_KEYWORD)
        df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
        df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
        df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")

        micro_by_sev[sev_opt] = df_micro

        out_micro = OUT_DIR / f"edu_micro_2015_with_floodexp_DFO_sev{sev_opt}.parquet"
        df_micro.to_parquet(out_micro, index=False)
        print(f"[INFO] Saved micro: {out_micro}")

    # 7.3 choose one for all_flood (identical across sev)
    micro_all = micro_by_sev["2"]

    # 7.4 batch regressions
    results = []
    for spatial in SPATIAL_PREFIXES:
        for sample_urban in SAMPLES_URBAN:

            # ---- all_flood regressions
            main_share, main_years = main_cols("all_flood", spatial)
            df_reg = load_and_prepare_for_reg(micro_all,
                                              main_share, main_years,
                                              sample_urban)
            key = run_one_reg(df_reg, main_share)
            key["exposure_mode"] = "all_flood"
            key["sev_option"] = "all"
            key["spatial_prefix"] = spatial
            key["sample_urban"] = sample_urban
            key["exposure_label"] = f"all_{spatial}"
            results.append(key)

            # ---- severe regressions per sev_option
            for sev_opt in SEV_OPTIONS:
                micro = micro_by_sev[sev_opt]
                main_share, main_years = main_cols("severe100", spatial)

                df_reg = load_and_prepare_for_reg(micro,
                                                  main_share, main_years,
                                                  sample_urban)
                key = run_one_reg(df_reg, main_share)
                key["exposure_mode"] = "severe100"
                key["sev_option"] = sev_opt
                key["spatial_prefix"] = spatial
                key["sample_urban"] = sample_urban
                key["exposure_label"] = f"sev{sev_opt}_{spatial}"
                results.append(key)

    df_res = pd.concat(results, ignore_index=True)

    # standardize column names if needed
    rename_map = {}
    for c in df_res.columns:
        cl = c.lower()
        if cl == "estimate":
            rename_map[c] = "Estimate"
        if "std" in cl and "error" in cl:
            rename_map[c] = "StdError"
        if "pvalue" in cl or "p-value" in cl or "pr(" in cl:
            rename_map[c] = "PValue"
    if rename_map:
        df_res = df_res.rename(columns=rename_map)

    df_res.to_csv(OUT_RESULTS_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[INFO] Saved combined results: {OUT_RESULTS_CSV}")

    # 7.5 plots
    coefplot_linear(df_res, OUT_PLOT_LINEAR)
    coefplot_nonlinear(df_res, OUT_PLOT_NONLIN)

    print("\n[DONE] One-click pipeline + regressions + plots finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
CSV_PATH = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/"
    "flood_dfo_rep/batch_oneclick/batch_DFO_severity_spatial_sample_results.csv"
)

OUT_DIR = CSV_PATH.parent
ALPHA = 0.10  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
MARKERS = {
    "centroid": "o",
    "area50": "s",
    "full": "^",
}

# Original notebook comment normalized for the public code archive.
X_OFFSETS = {
    "centroid": -0.18,
    "area50": 0.0,
    "full": 0.18,
}

# Original notebook comment normalized for the public code archive.
FIGSIZE = (6.8, 4.6)
LEGEND_OUT = "right"  # "right" or "bottom"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def _find_col(df, candidates, contains=False):
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


def _get_cols(d):
    est_col = _find_col(d, ["Estimate", "estimate"], contains=True)
    se_col  = _find_col(d, ["StdError", "std.error", "std_error", "se"], contains=True)
    p_col   = _find_col(d, ["PValue", "pvalue", "p_value", "Pr(>|t|)"], contains=True)
    return est_col, se_col, p_col


def _subset_label(exposure_mode, sev_option):
    if exposure_mode == "all_flood":
        return "all"
    return f"sev{sev_option}"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def plot_one_panel(df_res, exposure_mode, sev_option, ylims, out_png):
    """Archived notebook note for 02_dfo_child_education_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    d = df_res[df_res["model"] == "linear"].copy()
    d = d[(d["exposure_mode"] == exposure_mode)].copy()
    if exposure_mode == "severe100":
        d = d[d["sev_option"].astype(str) == str(sev_option)].copy()
    else:
        # all_flood：sev_option=all
        pass

    if d.empty:
        print(f"[WARN] Empty panel: {exposure_mode}, sev={sev_option}")
        return

    est_col, se_col, p_col = _get_cols(d)

    # Original notebook comment normalized for the public code archive.
    xcats = ["rural", "urban"]
    xbase = np.arange(len(xcats))

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Original notebook comment normalized for the public code archive.
    y_rng = ylims[1] - ylims[0]
    star_offset = 0.03 * y_rng

    for spatial in ["centroid", "area50", "full"]:
        sub = d[d["spatial_prefix"] == spatial].copy()
        if sub.empty:
            continue

        # Original notebook comment normalized for the public code archive.
        sub = sub.set_index("sample_urban").reindex(xcats)

        y  = sub[est_col].to_numpy()
        se = sub[se_col].to_numpy()
        pv = sub[p_col].to_numpy()

        x = xbase + X_OFFSETS[spatial]

        ax.errorbar(
            x, y, yerr=1.96*se,
            fmt=MARKERS[spatial],
            capsize=3,
            linestyle="none",
            label=spatial
        )

        # Original notebook comment normalized for the public code archive.
        for xi, yi, sei, pvi in zip(x, y, se, pv):
            if np.isfinite(pvi) and (pvi < ALPHA):
                ax.text(
                    xi, yi + 1.96*sei + star_offset, "*",
                    ha="center", va="bottom", fontsize=12
                )

    ax.axhline(0, linewidth=1)
    ax.set_xticks(xbase)
    ax.set_xticklabels(xcats, rotation=0)
    ax.set_ylabel("Coefficient (linear share)")
    ax.set_ylim(*ylims)

    title = _subset_label(exposure_mode, sev_option)
    ax.set_title(title)

    # Original notebook comment normalized for the public code archive.
    if LEGEND_OUT == "right":
        ax.legend(
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0.0,
            frameon=False,
            title="spatial"
        )
        fig.tight_layout(rect=[0, 0, 0.82, 1])
    else:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=3,
            frameon=False,
            title="spatial"
        )
        fig.tight_layout(rect=[0, 0.08, 1, 1])

    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print(f"[INFO] Saved: {out_png}")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df_res = pd.read_csv(CSV_PATH)
    print(f"[INFO] Loaded results: {df_res.shape}")

    # Original notebook comment normalized for the public code archive.
    dlin = df_res[df_res["model"] == "linear"].copy()
    est_col, se_col, _ = _get_cols(dlin)

    # Original notebook comment normalized for the public code archive.
    y_min = (dlin[est_col] - 1.96*dlin[se_col]).min()
    y_max = (dlin[est_col] + 1.96*dlin[se_col]).max()
    pad = 0.08 * (y_max - y_min) if np.isfinite(y_max - y_min) else 0.2
    ylims = (y_min - pad, y_max + pad)

    # Original notebook comment normalized for the public code archive.
    panels = [
        ("all_flood", "all"),
        ("severe100", "1"),
        ("severe100", "1.5"),
        ("severe100", "2"),
    ]

    for mode, sev in panels:
        out_png = OUT_DIR / f"coefplot_linear_{mode}_sev{sev}.png"
        plot_one_panel(df_res, mode, sev, ylims, out_png)


if __name__ == "__main__":
    main()
