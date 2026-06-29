#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_prepare_dfo_child_education_data.

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

# Original notebook comment normalized for the public code archive.
COUNTY_SHP      = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"
COUNTY_AREA_CSV = os.path.join(
    BASE_DIR, "result/county_inundation_no_fplain/county_total_area.csv"
)

# External flood dataset comparison note.
DFO_SHP = os.path.join(BASE_DIR, "gis_data/DFO/达特茅斯/中国大陆.shp")

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(BASE_DIR, "result/impact_assessment/flood")
os.makedirs(OUT_DIR, exist_ok=True)

# External flood dataset comparison note.
DFO_START_YEAR = 1980
DFO_END_YEAR   = 2015

# External flood dataset comparison note.
OUT_FLOOD_CSV = os.path.join(OUT_DIR, "county_year_panel_DFO.csv")

# Original notebook comment normalized for the public code archive.
EDU_PARQUET = Path(os.path.join(OUT_DIR, "edu_micro_2015.parquet"))

# Original notebook comment normalized for the public code archive.
OUT_COHORT_CSV = Path(os.path.join(OUT_DIR, "county_birthyear_exposure_DFO.csv"))

# External flood dataset comparison note.
OUT_MICRO_PARQUET = Path(
    os.path.join(OUT_DIR, "edu_micro_2015_with_floodexp_DFO.parquet")
)
OUT_MICRO_XLSX_SAMPLE = Path(
    os.path.join(OUT_DIR, "edu_micro_2015_with_floodexp_DFO_sample.xlsx")
)

# Original notebook comment normalized for the public code archive.
MIN_AGE = 0
MAX_AGE = 15

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000

# External flood dataset comparison note.
BINARY_COLS = ["flooded_any"]      # External flood dataset comparison note.
COUNT_COLS  = ["flooded_times"]    # External flood dataset comparison note.


# ================================
# External flood dataset comparison note.
# ================================
def load_counties() -> gpd.GeoDataFrame:
    """Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf_c = gpd.read_file(COUNTY_SHP)
    if gdf_c.crs is None:
        gdf_c = gdf_c.set_crs(epsg=4326)
    else:
        gdf_c = gdf_c.to_crs(epsg=4326)

    # County-level processing note.
    gdf_c["county_code"] = gdf_c[COUNTY_ID_FIELD].astype(str)

    # County-level processing note.
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


def load_dfo() -> gpd.GeoDataFrame:
    """Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf_dfo = gpd.read_file(DFO_SHP)
    if gdf_dfo.crs is None:
        gdf_dfo = gdf_dfo.set_crs(epsg=4326)
    else:
        gdf_dfo = gdf_dfo.to_crs(epsg=4326)

    gdf_dfo = gdf_dfo.reset_index(drop=True)
    gdf_dfo["event_id"] = np.arange(gdf_dfo.shape[0], dtype=int)

    # Original notebook comment normalized for the public code archive.
    gdf_dfo["BEGAN_dt"] = pd.to_datetime(gdf_dfo["BEGAN"], errors="coerce")
    gdf_dfo["ENDED_dt"] = pd.to_datetime(gdf_dfo["ENDED"], errors="coerce")

    mask_na_end = gdf_dfo["ENDED_dt"].isna() & gdf_dfo["BEGAN_dt"].notna()
    gdf_dfo.loc[mask_na_end, "ENDED_dt"] = gdf_dfo.loc[mask_na_end, "BEGAN_dt"]

    gdf_dfo["mid_date"] = gdf_dfo["BEGAN_dt"]
    has_both = gdf_dfo["BEGAN_dt"].notna() & gdf_dfo["ENDED_dt"].notna()
    gdf_dfo.loc[has_both, "mid_date"] = (
        gdf_dfo.loc[has_both, "BEGAN_dt"] +
        (gdf_dfo.loc[has_both, "ENDED_dt"] - gdf_dfo.loc[has_both, "BEGAN_dt"]) / 2
    )

    gdf_dfo["year"] = gdf_dfo["mid_date"].dt.year
    gdf_dfo = gdf_dfo.dropna(subset=["year"]).copy()
    gdf_dfo["year"] = gdf_dfo["year"].astype(int)

    mask_year = (
        (gdf_dfo["year"] >= DFO_START_YEAR) &
        (gdf_dfo["year"] <= DFO_END_YEAR)
    )
    gdf_dfo = gdf_dfo[mask_year].copy()

    print("[INFO] Notebook progress message.")
    return gdf_dfo


# ================================
# External flood dataset comparison note.
# ================================
def build_dfo_county_year_panel(
    gdf_dfo: gpd.GeoDataFrame,
    gdf_c: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    gdf_c_proj = gdf_c.to_crs(epsg=3857)
    gdf_dfo_proj = gdf_dfo.to_crs(gdf_c_proj.crs)

    # Original notebook comment normalized for the public code archive.
    gdf_c_proj["area_cnt"] = gdf_c_proj.geometry.area

    # County-level processing note.
    # County-level processing note.
    inter = gpd.overlay(
        gdf_c_proj[["county_id", "county_code", "area_cnt", "geometry"]],
        gdf_dfo_proj[["event_id", "year", "geometry"]],
        how="intersection",
        keep_geom_type=True
    )

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    inter["intersect_area"] = inter.geometry.area
    inter["cover_ratio"] = inter["intersect_area"] / inter["area_cnt"]

    # Original notebook comment normalized for the public code archive.
    inter["is_affected"] = inter["cover_ratio"] >= 0.5

    inter_aff = inter[inter["is_affected"]].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    df_panel = (
        inter_aff
        .groupby(["county_id", "county_code", "year"], as_index=False)
        .agg(flooded_times=("event_id", "nunique"))
    )
    df_panel["flooded_any"] = (df_panel["flooded_times"] > 0).astype(int)

    print("[INFO] Notebook progress message.")

    # County-level processing note.
    all_counties = gdf_c[["county_id", "county_code"]].drop_duplicates()
    all_years = pd.DataFrame({
        "year": np.arange(DFO_START_YEAR, DFO_END_YEAR + 1, dtype=int)
    })

    full = (
        all_counties.assign(key=1)
        .merge(all_years.assign(key=1), on="key")
        .drop(columns="key")
    )

    df_full = full.merge(
        df_panel,
        on=["county_id", "county_code", "year"],
        how="left"
    )

    for col in ["flooded_times", "flooded_any"]:
        df_full[col] = df_full[col].fillna(0)

    df_full["flooded_times"] = df_full["flooded_times"].astype(int)
    df_full["flooded_any"]   = df_full["flooded_any"].astype(int)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    return df_full


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_county_birthyear_exposure(
    df_flood: pd.DataFrame,
    county_col: str = "county_code"
) -> pd.DataFrame:
    """Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df_flood = df_flood.copy()
    df_flood[county_col] = pd.to_numeric(
        df_flood[county_col], errors="coerce"
    ).astype("Int64")
    df_flood["year"] = pd.to_numeric(
        df_flood["year"], errors="coerce"
    ).astype("Int64")

    min_flood_year = int(df_flood["year"].min())
    max_flood_year = int(df_flood["year"].max())
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    pieces = []
    for age in range(MIN_AGE, MAX_AGE + 1):
        tmp = df_flood.copy()
        tmp["birth_year"] = tmp["year"] - age
        tmp["age_in_year"] = age
        pieces.append(tmp)

    df_expanded = pd.concat(pieces, ignore_index=True)

    # Original notebook comment normalized for the public code archive.
    if BIRTH_MIN is not None:
        df_expanded = df_expanded[df_expanded["birth_year"] >= BIRTH_MIN]
    if BIRTH_MAX is not None:
        df_expanded = df_expanded[df_expanded["birth_year"] <= BIRTH_MAX]

    print("[INFO] Notebook progress message.")

    group_cols = [county_col, "birth_year"]

    agg_dict = {
        "n_years_window": ("year", "nunique"),  # Original notebook comment normalized for the public code archive.
    }

    # Original notebook comment normalized for the public code archive.
    for c in BINARY_COLS:
        if c in df_expanded.columns:
            agg_dict[f"years_{c}"] = (c, "sum")
            agg_dict[f"share_{c}"] = (c, "mean")

    # Original notebook comment normalized for the public code archive.
    for c in COUNT_COLS:
        if c in df_expanded.columns:
            agg_dict[f"sum_{c}"] = (c, "sum")
            agg_dict[f"avg_{c}"] = (c, "mean")

    df_cohort = df_expanded.groupby(group_cols).agg(**agg_dict).reset_index()

    print("[INFO] Notebook progress message.")
    return df_cohort


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def merge_exposure_to_micro(
    df_cohort: pd.DataFrame,
    county_col: str = "county_code"
) -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(
        edu["birth_year"], errors="coerce"
    ).astype("Int64")

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in edu.columns:
        edu["age_2015"] = pd.to_numeric(edu["age_2015"], errors="coerce")
        edu = edu[(edu["age_2015"] >= 15) & (edu["age_2015"] <= 30)]
        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if BIRTH_MIN is not None:
        edu = edu[edu["birth_year"] >= BIRTH_MIN]
    if BIRTH_MAX is not None:
        edu = edu[edu["birth_year"] <= BIRTH_MAX]
    print("[INFO] Notebook progress message.")

    # County-level processing note.
    cohort = df_cohort.copy()
    cohort[county_col] = pd.to_numeric(
        cohort[county_col], errors="coerce"
    ).astype("Int64")
    cohort = cohort.rename(columns={county_col: "county_code"})

    # County-level processing note.
    edu["county_code"] = edu["M2"]

    # Original notebook comment normalized for the public code archive.
    merged = edu.merge(
        cohort,
        how="left",
        left_on=["county_code", "birth_year"],
        right_on=["county_code", "birth_year"],
        validate="m:1"
    )

    # Original notebook comment normalized for the public code archive.
    exposure_cols = [
        c for c in merged.columns
        if c.startswith(("years_", "share_", "sum_", "avg_"))
    ] + ["n_years_window"]

    for c in exposure_cols:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    return merged


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    print("[INFO] Notebook progress message.")
    gdf_c   = load_counties()
    gdf_dfo = load_dfo()

    print("[INFO] Notebook progress message.")
    df_flood = build_dfo_county_year_panel(gdf_dfo, gdf_c)
    df_flood.to_csv(OUT_FLOOD_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df_cohort = build_county_birthyear_exposure(df_flood, county_col="county_code")
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df_micro = merge_exposure_to_micro(df_cohort, county_col="county_code")

    print("[INFO] Notebook progress message.")
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Excel output note.
    sample_n = min(100_000, len(df_micro))
    sample = df_micro.sample(n=sample_n, random_state=42)
    sample.to_excel(OUT_MICRO_XLSX_SAMPLE, index=False, sheet_name="sample_100k")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_prepare_dfo_child_education_data.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
DATA_PARQUET = Path(
    r"/home/ll/jupyter_notebook/result/impact_assessment/flood/edu_micro_2015_with_floodexp_DFO.parquet"
)

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000


# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
df = pd.read_parquet(DATA_PARQUET)
print("[INFO] Notebook progress message.", df.shape)

# Original notebook comment normalized for the public code archive.
for col in ["M2", "birth_year", "age_2015", "is_urban", "is_migrant",
            "M3", "M7", "M15", "M16", "M34", "M37"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Original notebook comment normalized for the public code archive.
for col in ["share_flooded_any", "sum_flooded_times", "avg_flooded_times",
            "edu_years", "hs_any", "hs_general"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
mask = pd.Series(True, index=df.index)

# Original notebook comment normalized for the public code archive.
if "is_migrant" in df.columns:
    mask &= (df["is_migrant"] == 0)

# Original notebook comment normalized for the public code archive.
if "is_urban" in df.columns:
    mask &= (df["is_urban"] == 0)

# Original notebook comment normalized for the public code archive.
if "age_2015" in df.columns:
    mask &= (df["age_2015"] >= 15) & (df["age_2015"] <= 30)

# Original notebook comment normalized for the public code archive.
if "birth_year" in df.columns:
    mask &= (df["birth_year"] >= BIRTH_MIN) & (df["birth_year"] <= BIRTH_MAX)

df_model = df[mask].copy()
print("[INFO] Notebook progress message.", df_model.shape)

# Original notebook comment normalized for the public code archive.
need_cols_base = [
    "edu_years", "share_flooded_any",
    "M2", "birth_year",
    "M34", "M37", "M3", "M7", "M15", "M16"
]
need_cols_base = [c for c in need_cols_base if c in df_model.columns]
df_model = df_model.dropna(subset=need_cols_base)
print("[INFO] Notebook progress message.", df_model.shape)

# Original notebook comment normalized for the public code archive.
int_like_cols = ["M2", "birth_year", "M3", "M7", "M15", "M16", "M34", "M37"]
for col in int_like_cols:
    if col in df_model.columns:
        df_model[col] = df_model[col].astype("int64")

for col in ["M34", "M37", "M7", "M15", "M16"]:
    if col in df_model.columns:
        df_model[col] = df_model[col].astype("category")

df_model["edu_years"] = df_model["edu_years"].astype("float64")
df_model["share_flooded_any"] = df_model["share_flooded_any"].astype("float64")

# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
# Original notebook comment normalized for the public code archive.
df_model["prov_code"] = (df_model["M2"] // 10000).astype("int64")
df_model["prov_birth"] = (df_model["prov_code"] * 10000 + df_model["birth_year"]).astype("int64")

print("[INFO] Notebook progress message.")
print(df_model[["M2", "prov_code", "birth_year", "prov_birth"]].head(10))


# ==========================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# ==========================
if "years_flooded_any" in df_model.columns:
    df_model["years_flooded_any"] = pd.to_numeric(df_model["years_flooded_any"], errors="coerce").fillna(0).astype(int)
    df_model["flood_1"]   = (df_model["years_flooded_any"] == 1).astype(int)
    df_model["flood_2_3"] = df_model["years_flooded_any"].between(2, 3).astype(int)
    df_model["flood_ge4"] = (df_model["years_flooded_any"] >= 4).astype(int)
    # Original notebook comment normalized for the public code archive.


# ==========================
# Original notebook comment normalized for the public code archive.
# Fixed-effects regression helper.
# ==========================
print("[INFO] Notebook progress message.")

formula_edu = (
    "edu_years ~ share_flooded_any "
    "+ C(M34) + C(M37) + M3 + C(M7) + C(M15) + C(M16) "
    "+ C(M2) + C(prov_birth)"
)

print("[INFO] Notebook progress message.", formula_edu)

model_edu = smf.ols(formula_edu, data=df_model).fit(
    cov_type="cluster",
    cov_kwds={"groups": df_model["M2"].values}  # Original notebook comment normalized for the public code archive.
)

print(model_edu.summary())


# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
if {"flood_1", "flood_2_3", "flood_ge4"}.issubset(df_model.columns):
    print("[INFO] Notebook progress message.")

    formula_edu_cat = (
        "edu_years ~ flood_1 + flood_2_3 + flood_ge4 "
        "+ C(M34) + C(M37) + M3 + C(M7) + C(M15) + C(M16) "
        "+ C(M2) + C(prov_birth)"
    )
    print("[INFO] Notebook progress message.", formula_edu_cat)

    model_edu_cat = smf.ols(formula_edu_cat, data=df_model).fit(
        cov_type="cluster",
        cov_kwds={"groups": df_model["M2"].values}
    )
    print(model_edu_cat.summary())


# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
if "hs_any" in df_model.columns:
    print("[INFO] Notebook progress message.")

    df_hs_any = df_model.dropna(subset=["hs_any"]).copy()
    df_hs_any["hs_any"] = df_hs_any["hs_any"].astype("float64")

    formula_hs_any = (
        "hs_any ~ share_flooded_any "
        "+ C(M34) + C(M37) + M3 + C(M7) + C(M15) + C(M16) "
        "+ C(M2) + C(prov_birth)"
    )
    print("[INFO] Notebook progress message.", formula_hs_any)

    model_hs_any = smf.ols(formula_hs_any, data=df_hs_any).fit(
        cov_type="cluster",
        cov_kwds={"groups": df_hs_any["M2"].values}
    )
    print(model_hs_any.summary())
else:
    print("[INFO] Notebook progress message.")


# ==========================
# Original notebook comment normalized for the public code archive.
# ==========================
if "hs_general" in df_model.columns:
    print("[INFO] Notebook progress message.")

    df_hs_gen = df_model.dropna(subset=["hs_general"]).copy()
    df_hs_gen["hs_general"] = df_hs_gen["hs_general"].astype("float64")

    formula_hs_gen = (
        "hs_general ~ share_flooded_any "
        "+ C(M34) + C(M37) + M3 + C(M7) + C(M15) + C(M16) "
        "+ C(M2) + C(prov_birth)"
    )
    print("[INFO] Notebook progress message.", formula_hs_gen)

    model_hs_gen = smf.ols(formula_hs_gen, data=df_hs_gen).fit(
        cov_type="cluster",
        cov_kwds={"groups": df_hs_gen["M2"].values}
    )
    print(model_hs_gen.summary())
else:
    print("[INFO] Notebook progress message.")
