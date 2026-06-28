#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_prepare_charls_60plus_health_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health")

# Original notebook comment normalized for the public code archive.
INPUT_FILES = {
    2011: dict(
        chi = BASE / "2011" / "2011_chi_result.dta",
        age = BASE / "2011" / "2011_age_region.dta",     # Original notebook comment normalized for the public code archive.
    ),
    2013: dict(
        chi = BASE / "2013" / "2013_chi_result_fixedID.dta",
        age = BASE / "2013" / "2013_age_region.dta",
    ),
    2015: dict(
        chi = BASE / "2015" / "2015_chi_result_fixedID.dta",
        age = BASE / "2015" / "2015_age_region.dta",
    ),
    2018: dict(
        chi = BASE / "2018" / "2018_chi_result_fixedID.dta",
        age = BASE / "2018" / "2018_age_region.dta",
    ),
    2020: dict(
        chi = BASE / "2020" / "2020_chi_result_fixedID.dta",
        age = BASE / "2020" / "2020_age_region.dta",
    ),
}

OUT_PANEL_60 = BASE / "charls_outputs_60plus" / "charls_health_panel_60plus.parquet"


# =============================================================================
def standardize_id(df):
    if "ID12" in df.columns:
        df["ID12"] = df["ID12"].astype(str).str.strip()
    elif "ID" in df.columns:
        df["ID12"] = df["ID"].astype(str).str.strip()
    else:
        raise ValueError("找不到 ID12 / ID 列")
    return df


# =============================================================================
def load_age_block(year: int, path_age: Path) -> pd.DataFrame:
    print(f"[READ-AGE] {year} <- {path_age}")
    age = pd.read_stata(path_age, convert_categoricals=False)
    age = standardize_id(age)

    # Original notebook comment normalized for the public code archive.
    age_candidates = [
        f"age_{year}",
        "age_2011","age_2013","age_2015","age_2018","age_2020",
        "age","年龄"
    ]
    age_col = None
    for c in age_candidates:
        if c in age.columns:
            age_col = c
            break
    if age_col is None:
        # Original notebook comment normalized for the public code archive.
        tmp = [c for c in age.columns if c.lower().startswith("age")]
        if len(tmp) == 1:
            age_col = tmp[0]

    if age_col is None:
        raise ValueError(f"{year} 的 age_region 找不到年龄列。列名前20个：{age.columns.tolist()[:20]}")

    age["age"] = pd.to_numeric(age[age_col], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    keep_cols = ["ID12", "age"]
    if "birth_year" in age.columns:
        age["birth_year"] = pd.to_numeric(age["birth_year"], errors="coerce")
        keep_cols.append("birth_year")

    # City-level processing note.
    for c in ["province", "city", "city_code", "urban_nbs", "areatype"]:
        if c in age.columns and c not in keep_cols:
            keep_cols.append(c)

    age = age[keep_cols].copy()
    return age


# =============================================================================
def normalize_health_cols(df, year):
    """Archived notebook note for 01_prepare_charls_60plus_health_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    if "overall_index_0_100" in df.columns:
        return df

    # Original notebook comment normalized for the public code archive.
    cand = [c for c in df.columns if "0_100" in c]
    if len(cand) == 0:
        # Original notebook comment normalized for the public code archive.
        print("[INFO] Notebook progress message.")
        return df

    if len(cand) != 4:
        print("[INFO] Notebook progress message.")
        # Original notebook comment normalized for the public code archive.
        cand = cand[:4]

    cand_sorted = sorted(cand)
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    mapping = {
        cand_sorted[0]: "body_index_0_100",
        cand_sorted[1]: "mental_index_0_100",
        cand_sorted[2]: "social_index_0_100",
        cand_sorted[3]: "overall_index_0_100",
    }
    print("[INFO] Notebook progress message.")
    df = df.rename(columns=mapping)

    # Original notebook comment normalized for the public code archive.
    for c in mapping.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# =============================================================================
def read_wave(year: int, chi_path: Path, age_path: Path) -> pd.DataFrame:
    print(f"[READ-CHI] {year} <- {chi_path}")
    chi = pd.read_stata(chi_path, convert_categoricals=False)
    chi = standardize_id(chi)
    chi = normalize_health_cols(chi, year)

    # =============================================================================
    if "city_code" in chi.columns:
        chi["city_code"] = pd.to_numeric(chi["city_code"], errors="coerce").astype("Int64")
    elif "citycode" in chi.columns:
        chi["city_code"] = pd.to_numeric(chi["citycode"], errors="coerce").astype("Int64")
    elif "citycode_int" in chi.columns:
        chi["city_code"] = pd.to_numeric(chi["citycode_int"], errors="coerce").astype("Int64")

    for c in ["province", "city"]:
        if c in chi.columns:
            chi[c] = chi[c].astype(str).str.strip()
    for c in ["urban_nbs", "areatype"]:
        if c in chi.columns:
            chi[c] = pd.to_numeric(chi[c], errors="coerce").astype("Int64")

    # ======================================================
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # ======================================================
    age_col_chi = None
    age_candidates_chi = [
        f"age_{year}",   # age_2011, age_2015 ...
        "age", "年龄",    # Original notebook comment normalized for the public code archive.
        "__",            # Original notebook comment normalized for the public code archive.
    ]
    for c in age_candidates_chi:
        if c in chi.columns:
            age_col_chi = c
            break

    if age_col_chi is not None:
        chi["age"] = pd.to_numeric(chi[age_col_chi], errors="coerce")

        # Original notebook comment normalized for the public code archive.
        birth_candidates = ["birth_year", "出生年", "___"]
        for c in birth_candidates:
            if c in chi.columns:
                chi["birth_year"] = pd.to_numeric(chi[c], errors="coerce")
                break

        df = chi  # Original notebook comment normalized for the public code archive.

    else:
        # ==================================================
        # Original notebook comment normalized for the public code archive.
        # ==================================================
        print("[INFO] Notebook progress message.")
        age = load_age_block(year, age_path)
        df = chi.merge(age, on="ID12", how="left", validate="1:1")
        df["age"] = pd.to_numeric(df["age"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["year"] = year

    # Original notebook comment normalized for the public code archive.
    health_cols = [
        "overall_index_0_100",
        "body_index_0_100",
        "mental_index_0_100",
        "social_index_0_100",
    ]
    keep = ["ID12", "year", "age", "birth_year", "city_code", "province", "city",
            "urban_nbs", "areatype"] + health_cols
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df["age"] >= 60]
    print("[INFO] Notebook progress message.")

    return df


def build_panel_60plus():
    all_waves = []
    for year, paths in INPUT_FILES.items():
        wdf = read_wave(year, paths["chi"], paths["age"])
        all_waves.append(wdf)

    panel = pd.concat(all_waves, ignore_index=True)
    print("[INFO] Notebook progress message.")

    # Fixed-effects regression helper.
    counts = panel.groupby("ID12")["year"].nunique()
    keep_ids = counts[counts >= 2].index
    panel_2plus = panel[panel["ID12"].isin(keep_ids)].copy()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if "overall_index_0_100" in panel_2plus.columns:
        panel_2plus["health_z"] = panel_2plus.groupby("year")["overall_index_0_100"] \
            .transform(lambda x: (x - x.mean()) / x.std(ddof=0))

    OUT_PANEL_60.parent.mkdir(parents=True, exist_ok=True)
    panel_2plus.to_parquet(OUT_PANEL_60, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    build_panel_60plus()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
import pandas as pd

panel_path = "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_outputs_60plus/charls_health_panel_60plus.parquet"
panel = pd.read_parquet(panel_path)

# Original notebook comment normalized for the public code archive.
num_cols_mean = [
    "age",
    "birth_year",
    "overall_index_0_100",
    "body_index_0_100",
    "mental_index_0_100",
    "social_index_0_100",
]

# Original notebook comment normalized for the public code archive.
cat_cols_first = [
    "city_code",
    "province",
    "city",
    "urban_nbs",
    "areatype",
]

agg_dict = {c: "mean" for c in num_cols_mean}
agg_dict.update({c: "first" for c in cat_cols_first})

panel_collapsed = (
    panel
    .groupby(["ID12", "year"], as_index=False)
    .agg(agg_dict)
)

print("[INFO] Notebook progress message.", panel_collapsed.shape)
print("[INFO] Notebook progress message.",
      panel_collapsed.duplicated(subset=["ID12", "year"]).sum())

# Original notebook comment normalized for the public code archive.
panel_collapsed["health_z"] = (
    panel_collapsed
    .groupby("year")["overall_index_0_100"]
    .transform(lambda x: (x - x.mean()) / x.std(ddof=0))
)

out_path = panel_path.replace(".parquet", "_collapsed.parquet")
panel_collapsed.to_parquet(out_path, index=False)
print("[INFO] Notebook progress message.", out_path)
