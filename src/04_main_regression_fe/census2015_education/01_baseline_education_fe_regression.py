#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import numpy as np

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
# Original notebook comment normalized for the public code archive.
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)


# Original notebook comment normalized for the public code archive.
EDU_PARQUET = Path(
    r"/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_COHORT_CSV = Path(
    r"/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    r"county_birthyear_exposure_storage_T2_5_10_20_50_100.csv"
)
OUT_MICRO_PARQUET = Path(
    r"/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    r"edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet"
)
OUT_MICRO_XLSX_SAMPLE = Path(
    r"/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    r"edu_micro_2015_with_storage_T2_5_10_20_50_100_sample.xlsx"
)

# Original notebook comment normalized for the public code archive.
MIN_AGE = 0
MAX_AGE = 15

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000

# County-level processing note.
# Original notebook comment normalized for the public code archive.
BINARY_COLS = [
    "flood_ge_T2",
    "flood_ge_T5",
    "flood_ge_T10",
    "flood_ge_T20",
    "flood_ge_T50",
    "flood_ge_T100",
]

# Original notebook comment normalized for the public code archive.
COUNT_COLS = []


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def load_flood_panel():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FLOOD_CSV)

    # County-level processing note.
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id 列")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    available_cols = set(df.columns)
    keep_cols = [county_col, "year"]

    for c in BINARY_COLS + COUNT_COLS:
        if c in available_cols:
            keep_cols.append(c)
            if c in BINARY_COLS:
                df[c] = df[c].fillna(0).astype(int)
            else:
                df[c] = df[c].fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df[c] = 0
            keep_cols.append(c)

    df = df[keep_cols].dropna(subset=[county_col, "year"])

    print(
        f"[INFO] 洪水事件面板形状: {df.shape}, "
        f"年份范围: {df['year'].min()}–{df['year'].max()}"
    )
    return df, county_col


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame, county_col: str) -> pd.DataFrame:
    min_flood_year = int(df_flood["year"].min())
    max_flood_year = int(df_flood["year"].max())
    print(
        f"[INFO] 洪水事件面板年份: {min_flood_year}–{max_flood_year}，"
        f"用于构建 0–{MAX_AGE} 岁暴露窗口。"
    )

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

    # Original notebook comment normalized for the public code archive.
    group_cols = [county_col, "birth_year"]
    agg_dict = {"n_years_window": ("year", "nunique")}

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
def merge_exposure_to_micro(df_cohort: pd.DataFrame, county_col: str) -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in edu.columns:
        edu = edu[(edu["age_2015"] >= 15) & (edu["age_2015"] <= 30)]

    # Original notebook comment normalized for the public code archive.
    if BIRTH_MIN is not None:
        edu = edu[edu["birth_year"] >= BIRTH_MIN]
    if BIRTH_MAX is not None:
        edu = edu[edu["birth_year"] <= BIRTH_MAX]

    print("[INFO] Notebook progress message.")

    # County-level processing note.
    cohort = df_cohort.copy()
    if county_col != "county_code":
        cohort = cohort.rename(columns={county_col: "county_code"})
    else:
        cohort["county_code"] = cohort["county_code"].astype("Int64")

    # Original notebook comment normalized for the public code archive.
    edu["county_code"] = edu["M2"]

    # Original notebook comment normalized for the public code archive.
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
        if c.startswith(("years_", "share_", "sum_", "avg_"))
    ] + ["n_years_window"]
    for c in exp_cols:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    # Original notebook comment normalized for the public code archive.
    # Archived notebook metadata.
    if "years_flood_ge_T100" in merged.columns:
        merged["years_T100"] = merged["years_flood_ge_T100"].astype("Int64")

        merged["T100_0"]   = (merged["years_T100"] == 0).astype("Int64")
        merged["T100_1"]   = (merged["years_T100"] == 1).astype("Int64")
        merged["T100_2_3"] = merged["years_T100"].between(2, 3).astype("Int64")
        merged["T100_ge4"] = (merged["years_T100"] >= 4).astype("Int64")

    print("[INFO] Notebook progress message.")
    return merged


def main():
    # Original notebook comment normalized for the public code archive.
    df_flood, county_col = load_flood_panel()

    # Original notebook comment normalized for the public code archive.
    df_cohort = build_county_birthyear_exposure(df_flood, county_col)
    OUT_COHORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_micro = merge_exposure_to_micro(df_cohort, county_col)
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    n_sample = min(100_000, len(df_micro))
    if n_sample > 0:
        sample = df_micro.sample(n=n_sample, random_state=42)
        OUT_MICRO_XLSX_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_excel(OUT_MICRO_XLSX_SAMPLE, index=False, sheet_name="sample")
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM(Gumbel) storage-based flood exposure:
  county×year events  -> county×birth_year (0-15 exposure) -> merge into edu_micro_2015.

Inputs:
  1) BM county×year events panel:
     county_flood_events_T10_20_50_100_1985_2015.csv
     (should contain flood_ge_T2/5/10/20/50/100; if any missing -> filled as 0)
  2) edu_micro_2015.parquet

Outputs (BM-specific):
  county_birthyear_exposure_storage_BM_T2_5_10_20_50_100.csv
  edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet
  edu_micro_2015_with_storage_BM_T2_5_10_20_50_100_sample.xlsx
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ================================
# 0. PATHS & CONFIG (BM)
# ================================

# Original notebook comment normalized for the public code archive.
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)

# Original notebook comment normalized for the public code archive.
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_COHORT_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "county_birthyear_exposure_storage_BM_T2_5_10_20_50_100.csv"
)
OUT_MICRO_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)
OUT_MICRO_XLSX_SAMPLE = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100_sample.xlsx"
)

# Original notebook comment normalized for the public code archive.
MIN_AGE = 0
MAX_AGE = 15

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000

# Original notebook comment normalized for the public code archive.
BINARY_COLS = [
    "flood_ge_T2",
    "flood_ge_T5",
    "flood_ge_T10",
    "flood_ge_T20",
    "flood_ge_T50",
    "flood_ge_T100",
]
COUNT_COLS = []


# ================================
# 1. LOAD BM COUNTY×YEAR EVENTS
# ================================
def load_flood_panel():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id 列")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    keep_cols = [county_col, "year"]
    available = set(df.columns)

    for c in BINARY_COLS + COUNT_COLS:
        if c in available:
            keep_cols.append(c)
            if c in BINARY_COLS:
                df[c] = df[c].fillna(0).astype(int)
            else:
                df[c] = df[c].fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df[c] = 0
            keep_cols.append(c)

    df = df[keep_cols].dropna(subset=[county_col, "year"])
    print(
        f"[INFO] BM 事件面板形状: {df.shape}, "
        f"年份范围: {df['year'].min()}–{df['year'].max()}"
    )
    return df, county_col


# ================================
# County-level processing note.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame, county_col: str) -> pd.DataFrame:
    min_year = int(df_flood["year"].min())
    max_year = int(df_flood["year"].max())
    print("[INFO] Notebook progress message.")

    pieces = []
    for age in range(MIN_AGE, MAX_AGE + 1):
        tmp = df_flood.copy()
        tmp["birth_year"] = tmp["year"] - age
        tmp["age_in_year"] = age
        pieces.append(tmp)
    df_expanded = pd.concat(pieces, ignore_index=True)

    if BIRTH_MIN is not None:
        df_expanded = df_expanded[df_expanded["birth_year"] >= BIRTH_MIN]
    if BIRTH_MAX is not None:
        df_expanded = df_expanded[df_expanded["birth_year"] <= BIRTH_MAX]

    group_cols = [county_col, "birth_year"]
    agg_dict = {"n_years_window": ("year", "nunique")}

    for c in BINARY_COLS:
        if c in df_expanded.columns:
            agg_dict[f"years_{c}"] = (c, "sum")
            agg_dict[f"share_{c}"] = (c, "mean")
    for c in COUNT_COLS:
        if c in df_expanded.columns:
            agg_dict[f"sum_{c}"] = (c, "sum")
            agg_dict[f"avg_{c}"] = (c, "mean")

    df_cohort = df_expanded.groupby(group_cols).agg(**agg_dict).reset_index()
    print("[INFO] Notebook progress message.")
    return df_cohort


# ================================
# 3. MERGE INTO 2015 MICRO DATA
# ================================
def merge_exposure_to_micro(df_cohort: pd.DataFrame, county_col: str) -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    if "age_2015" in edu.columns:
        edu = edu[edu["age_2015"].between(15, 30)]

    if BIRTH_MIN is not None:
        edu = edu[edu["birth_year"] >= BIRTH_MIN]
    if BIRTH_MAX is not None:
        edu = edu[edu["birth_year"] <= BIRTH_MAX]

    print("[INFO] Notebook progress message.")

    cohort = df_cohort.copy()
    if county_col != "county_code":
        cohort = cohort.rename(columns={county_col: "county_code"})
    cohort["county_code"] = cohort["county_code"].astype("Int64")

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort,
        how="left",
        on=["county_code", "birth_year"],
        validate="m:1",
    )

    exp_cols = [
        c for c in merged.columns
        if c.startswith(("years_", "share_", "sum_", "avg_"))
    ] + ["n_years_window"]
    for c in exp_cols:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    # Original notebook comment normalized for the public code archive.
    if "years_flood_ge_T100" in merged.columns:
        merged["years_T100"] = merged["years_flood_ge_T100"].astype("Int64")
        merged["T100_0"]   = (merged["years_T100"] == 0).astype("Int64")
        merged["T100_1"]   = (merged["years_T100"] == 1).astype("Int64")
        merged["T100_2_3"] = merged["years_T100"].between(2, 3).astype("Int64")
        merged["T100_ge4"] = (merged["years_T100"] >= 4).astype("Int64")

    print("[INFO] Notebook progress message.")
    return merged


def main():
    df_flood, county_col = load_flood_panel()

    df_cohort = build_county_birthyear_exposure(df_flood, county_col)
    OUT_COHORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    df_micro = merge_exposure_to_micro(df_cohort, county_col)
    OUT_MICRO_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    n_sample = min(100_000, len(df_micro))
    if n_sample > 0:
        sample = df_micro.sample(n=n_sample, random_state=42)
        OUT_MICRO_XLSX_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_excel(OUT_MICRO_XLSX_SAMPLE, index=False, sheet_name="sample")
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np

# ================================
# Original notebook comment normalized for the public code archive.
# ================================

# Original notebook comment normalized for the public code archive.
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1985_2015.csv"
)

# Original notebook comment normalized for the public code archive.
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_COHORT_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "county_birthyear_exposure_storage_T2_5_10_20_50_100_POT.csv"
)
OUT_MICRO_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100_POT.parquet"
)
OUT_MICRO_XLSX_SAMPLE = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100_POT_sample.xlsx"
)

# Original notebook comment normalized for the public code archive.
MIN_AGE = 0
MAX_AGE = 15

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000

# Original notebook comment normalized for the public code archive.
BINARY_COLS = [
    "flood_ge_T2",
    "flood_ge_T5",
    "flood_ge_T10",
    "flood_ge_T20",
    "flood_ge_T50",
    "flood_ge_T100",
]

COUNT_COLS = []   # Original notebook comment normalized for the public code archive.

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def load_flood_panel():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FLOOD_CSV)

    # Original notebook comment normalized for the public code archive.
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id 列")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    available_cols = set(df.columns)
    keep_cols = [county_col, "year"]

    for c in BINARY_COLS + COUNT_COLS:
        if c in available_cols:
            keep_cols.append(c)
            if c in BINARY_COLS:
                df[c] = df[c].fillna(0).astype(int)
            else:
                df[c] = df[c].fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df[c] = 0
            keep_cols.append(c)

    df = df[keep_cols].dropna(subset=[county_col, "year"])

    print(
        f"[INFO] 事件面板形状: {df.shape}, "
        f"年份范围: {df['year'].min()}–{df['year'].max()}"
    )
    return df, county_col


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def build_county_birthyear_exposure(df_flood: pd.DataFrame, county_col: str) -> pd.DataFrame:
    min_flood_year = int(df_flood["year"].min())
    max_flood_year = int(df_flood["year"].max())
    print(
        f"[INFO] 洪水面板年份: {min_flood_year}–{max_flood_year}，"
        f"用于构建 0–{MAX_AGE} 岁暴露窗口。"
    )

    # Original notebook comment normalized for the public code archive.
    pieces = []
    for age in range(MIN_AGE, MAX_AGE + 1):
        tmp = df_flood.copy()
        tmp["birth_year"] = tmp["year"] - age
        tmp["age_in_year"] = age
        pieces.append(tmp)

    df_expanded = pd.concat(pieces, ignore_index=True)

    # Original notebook comment normalized for the public code archive.
    df_expanded = df_expanded[
        (df_expanded["birth_year"] >= BIRTH_MIN) &
        (df_expanded["birth_year"] <= BIRTH_MAX)
    ].copy()

    # Original notebook comment normalized for the public code archive.
    group_cols = [county_col, "birth_year"]
    agg_dict = {"n_years_window": ("year", "nunique")}

    for c in BINARY_COLS:
        if c in df_expanded.columns:
            agg_dict[f"years_{c}"] = (c, "sum")
            agg_dict[f"share_{c}"] = (c, "mean")

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
def merge_exposure_to_micro(df_cohort: pd.DataFrame, county_col: str) -> pd.DataFrame:
    edu = pd.read_parquet(EDU_PARQUET)
    print("[INFO] Notebook progress message.")

    edu["M2"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in edu.columns:
        edu = edu[(edu["age_2015"] >= 15) & (edu["age_2015"] <= 30)]

    # Original notebook comment normalized for the public code archive.
    edu = edu[(edu["birth_year"] >= BIRTH_MIN) & (edu["birth_year"] <= BIRTH_MAX)]
    print("[INFO] Notebook progress message.")

    cohort = df_cohort.copy()
    if county_col != "county_code":
        cohort = cohort.rename(columns={county_col: "county_code"})
    cohort["county_code"] = pd.to_numeric(cohort["county_code"], errors="coerce").astype("Int64")

    edu["county_code"] = edu["M2"]

    merged = edu.merge(
        cohort,
        how="left",
        left_on=["county_code", "birth_year"],
        right_on=["county_code", "birth_year"],
        validate="m:1",
    )

    exp_cols = [
        c for c in merged.columns
        if c.startswith(("years_", "share_", "sum_", "avg_"))
    ] + ["n_years_window"]

    for c in exp_cols:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    # Original notebook comment normalized for the public code archive.
    if "years_flood_ge_T100" in merged.columns:
        merged["years_T100"] = merged["years_flood_ge_T100"].astype("Int64")
        merged["T100_0"]   = (merged["years_T100"] == 0).astype("Int64")
        merged["T100_1"]   = (merged["years_T100"] == 1).astype("Int64")
        merged["T100_2_3"] = merged["years_T100"].between(2, 3).astype("Int64")
        merged["T100_ge4"] = (merged["years_T100"] >= 4).astype("Int64")

    print("[INFO] Notebook progress message.")
    return merged


def main():
    # Original notebook comment normalized for the public code archive.
    df_flood, county_col = load_flood_panel()

    # Original notebook comment normalized for the public code archive.
    df_cohort = build_county_birthyear_exposure(df_flood, county_col)
    OUT_COHORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_cohort.to_csv(OUT_COHORT_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_micro = merge_exposure_to_micro(df_cohort, county_col)
    OUT_MICRO_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df_micro.to_parquet(OUT_MICRO_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    n_sample = min(100_000, len(df_micro))
    if n_sample > 0:
        sample = df_micro.sample(n=n_sample, random_state=42)
        OUT_MICRO_XLSX_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_excel(OUT_MICRO_XLSX_SAMPLE, index=False, sheet_name="sample")
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

# ================================
# Original notebook comment normalized for the public code archive.
# ================================

# Original notebook comment normalized for the public code archive.
DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet"
)

# Original notebook comment normalized for the public code archive.
STATS_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics")
STATS_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
MAIN_RET = "flood_ge_T2"
MAIN_SHARE = f"share_{MAIN_RET}"        # share_flood_ge_T100
MAIN_YEARS = f"years_{MAIN_RET}"        # years_flood_ge_T100

# Original notebook comment normalized for the public code archive.
BIRTH_MIN = 1980
BIRTH_MAX = 2000
AGE_MIN = 15
AGE_MAX = 35

# Original notebook comment normalized for the public code archive.
SAMPLE_URBAN = "rural"       # "rural" / "urban" / "all"
SAMPLE_MIGRANT = "non_migrant"  # "non_migrant" / "migrant" / "all"
EXCLUDE_IN_SCHOOL = False    # Original notebook comment normalized for the public code archive.

# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def load_and_prepare_data():
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(DATA_PARQUET)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    cols_to_numeric = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        MAIN_SHARE, MAIN_YEARS,
        "years_T100",   # Original notebook comment normalized for the public code archive.
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

    # Original notebook comment normalized for the public code archive.
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
        in_school_mask = (df["M52"] == 1)
        print("[INFO] Notebook progress message.")
        mask &= (~in_school_mask)

    df_model = df[mask].copy()

    # Original notebook comment normalized for the public code archive.
    required_cols = ["edu_years", MAIN_SHARE, MAIN_YEARS, "M2", "birth_year"]
    missing = [c for c in required_cols if c not in df_model.columns]
    if missing:
        raise ValueError(f"数据中缺少关键列: {missing}")

    # Original notebook comment normalized for the public code archive.
    cat_cols = ["M34", "M37", "M15", "M16"]
    req_vars = required_cols + cat_cols
    req_vars = [c for c in req_vars if c in df_model.columns]

    # Original notebook comment normalized for the public code archive.
    df_model = df_model.dropna(subset=req_vars)
    print("[INFO] Notebook progress message.")

    # Fixed-effects regression helper.
    df_model["prov_code"] = (df_model["M2"] // 10000).astype(int)
    df_model["prov_birth_fe"] = (
        df_model["prov_code"].astype(str) + "_" + df_model["birth_year"].astype(str)
    )
    # Original notebook comment normalized for the public code archive.
    df_model["birth_year_c"] = df_model["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in cat_cols:
        if c in df_model.columns:
            df_model[c] = df_model[c].astype(int).astype("category")
            df_model[c] = df_model[c].cat.remove_unused_categories()

    # Original notebook comment normalized for the public code archive.
    if MAIN_YEARS in df_model.columns:
        df_model["years_T100"] = df_model[MAIN_YEARS].astype(int)

        df_model["T100_1"]   = (df_model["years_T100"] == 1).astype(int)
        df_model["T100_2_3"] = df_model["years_T100"].between(2, 3).astype(int)
        df_model["T100_ge4"] = (df_model["years_T100"] >= 4).astype(int)

    return df_model.reset_index(drop=True)


# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def run_analysis():
    df = load_and_prepare_data()

    # Original notebook comment normalized for the public code archive.
    controls = "C(M34) + C(M37) + C(M15) + C(M16)"
    # Original notebook comment normalized for the public code archive.
    # controls = "C(M34) + C(M37) + M3 + C(M15) + C(M16)"

    # ------------------------------------------------------------------
    # Original notebook comment normalized for the public code archive.
    # ------------------------------------------------------------------
    def process_tidy(fit_obj):
        res = fit_obj.tidy()
        res = res.reset_index()
        first_col = res.columns[0]
        if first_col != "Term":
            res = res.rename(columns={first_col: "Term"})
        return res

    # =================================================
    # Original notebook comment normalized for the public code archive.
    # =================================================
    print("[INFO] Notebook progress message.")
    fml_cont = (
        f"edu_years ~ {MAIN_SHARE} + {controls} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )

    fit_cont = feols(fml_cont, data=df, vcov={"CRV1": "M2"})

    res_cont = process_tidy(fit_cont)
    key_cont = res_cont[res_cont["Term"].str.contains("share_", na=False)]

    print("[INFO] Notebook progress message.")
    print(key_cont)

    out_name = (
        f"res_{SAMPLE_URBAN}_{SAMPLE_MIGRANT}_"
        f"excludeSch{EXCLUDE_IN_SCHOOL}_T100_linear.csv"
    )
    key_cont.to_csv(STATS_DIR / out_name, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # =================================================
    # Original notebook comment normalized for the public code archive.
    # =================================================
    if {"T100_1", "T100_2_3", "T100_ge4"}.issubset(df.columns):
        print("[INFO] Notebook progress message.")
        fml_cat = (
            f"edu_years ~ T100_1 + T100_2_3 + T100_ge4 + "
            f"{controls} + i(M2, birth_year_c) | M2 + prov_birth_fe"
        )

        fit_cat = feols(fml_cat, data=df, vcov={"CRV1": "M2"})

        res_cat = process_tidy(fit_cat)
        key_cat = res_cat[res_cat["Term"].str.contains("T100_", na=False)]

        print("[INFO] Notebook progress message.")
        print(key_cat)

        out_name_cat = (
            f"res_{SAMPLE_URBAN}_{SAMPLE_MIGRANT}_"
            f"excludeSch{EXCLUDE_IN_SCHOOL}_T100_nonlinear.csv"
        )
        key_cat.to_csv(STATS_DIR / out_name_cat, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")
    else:
        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    # df["share_T100_c"] = df[MAIN_SHARE] - df[MAIN_SHARE].mean()
    # df["share_T100_sq"] = df["share_T100_c"] ** 2
    # df["share_T100_cu"] = df["share_T100_c"] ** 3
    # Fixed-effects regression helper.

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_analysis()


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CaMa storage-based flood exposure (all T thresholds) × rural/urban (non_migrant)
One-click regressions with PyFixest.

Data:
  edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet
Exposure columns assumed:
  share_flood_ge_T2, years_flood_ge_T2,
  share_flood_ge_T5, years_flood_ge_T5,
  ...
  share_flood_ge_T100, years_flood_ge_T100, etc.

Outputs:
  1) Master regression table: cama_storage_allT_regs.csv
  2) Optional: per-model CSVs (linear / nonlinear) by T & rural/urban.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG
# ================================

DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet"
)

STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/storage_allT_oneclick"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = STATS_DIR / "cama_storage_allT_regs.csv"

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

# Original notebook comment normalized for the public code archive.
ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
SAMPLES_URBAN = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_FALLBACK = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# ================================
# 1. HELPER FUNCTIONS
# ================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df):
    # is_urban from M2
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # is_migrant from M38 (M38=1 -> non_migrant)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df

def detect_T_list(df):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except:
                continue
    if ts:
        return sorted(ts)
    return T_LIST_FALLBACK

def normalize_tidy(res):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)".lower(), "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"

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

def prepare_sample(df, main_share, main_years, sample_urban):
    df = df.copy()

    num_cols = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    # non_migrant only
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    # rural / urban
    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    # age & birth-year
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    # FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # categorical controls (safe casting)
    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    # drop key NA
    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # nonlinear dummies
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
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
    return {
        "Estimate": float(row["Estimate"]),
        "StdError": float(row.get("StdError", np.nan)),
        "PValue": float(row.get("PValue", np.nan)),
        "nobs": get_nobs(fit, dfm),
    }

def run_nonlinear(dfm):
    if not {"T_1", "T_2_3", "T_ge4"}.issubset(dfm.columns):
        return []

    fml = (
        f"edu_years ~ T_1 + T_2_3 + T_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())
    res = res[res["Term"].str.contains("T_", na=False)].copy()

    out_rows = []
    for _, r in res.iterrows():
        est = float(r["Estimate"])
        se  = float(r.get("StdError", np.nan))
        pv  = float(r.get("PValue", np.nan))
        out_rows.append({
            "Term": r["Term"],
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        })
    return out_rows


# ================================
# 2. MAIN PIPELINE
# ================================
def main():
    print(f"[STEP] Load data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)

    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    all_rows = []

    for T in T_list:
        # Original notebook comment normalized for the public code archive.
        T_str = str(T).replace(".0", "")
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] Missing columns for T={T_str}: {main_share}/{main_years}")
            continue

        print(f"\n==============================")
        print(f"[PANEL] T={T_str} ({main_share})")
        print(f"==============================")

        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su)
            print(f"[SAMPLE] {su}, N={len(dfm)}")

            if len(dfm) == 0:
                continue

            # ----- linear
            lin = run_linear(dfm, main_share)
            if lin is not None:
                est, se, pv = lin["Estimate"], lin["StdError"], lin["PValue"]
                all_rows.append({
                    "T_panel": T_str,
                    "model": "linear",
                    "sample_urban": su,
                    "Term": main_share,
                    "Estimate": est,
                    "StdError": se,
                    "PValue": pv,
                    "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
                    "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
                    "nobs": lin["nobs"],
                })

            # ----- nonlinear
            non_rows = run_nonlinear(dfm)
            for nr in non_rows:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "nonlinear",
                    "sample_urban": su,
                    **nr
                })

            # Original notebook comment normalized for the public code archive.
            combo_df = pd.DataFrame([r for r in all_rows if r["T_panel"]==T_str and r["sample_urban"]==su])
            combo_df.to_csv(
                STATS_DIR / f"res_T{T_str}_{su}.csv",
                index=False, encoding="utf-8-sig"
            )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved master table: {OUT_MASTER_CSV}")
    print(out.head(10))


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CaMa storage-based flood exposure (all T thresholds) × rural/urban (non_migrant)
One-click regressions + visualization with PyFixest.

Data:
  edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet

Exposure columns assumed:
  share_flood_ge_T2, years_flood_ge_T2,
  share_flood_ge_T5, years_flood_ge_T5,
  ...
  share_flood_ge_T100, years_flood_ge_T100, etc.

Outputs:
  1) Master regression table: cama_storage_allT_regs.csv
  2) Per-combo CSV: res_T{T}_{rural/urban}.csv
  3) Two coefficient plots (linear share):
     coefplot_storage_linear_urban.png
     coefplot_storage_linear_rural.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG
# ================================

DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100.parquet"
)

STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/storage_allT_oneclick"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = STATS_DIR / "cama_storage_allT_regs.csv"
OUT_FIG_URBAN  = STATS_DIR / "coefplot_storage_linear_urban.png"
OUT_FIG_RURAL  = STATS_DIR / "coefplot_storage_linear_rural.png"

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

# Original notebook comment normalized for the public code archive.
ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
SAMPLES_URBAN = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_FALLBACK = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# Original notebook comment normalized for the public code archive.
SIG_LEVEL = 0.10


# ================================
# 1. HELPER FUNCTIONS
# ================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df):
    # is_urban from M2 (1-20 urban, else rural)
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # is_migrant from M38 (M38=1 -> non_migrant)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df

def detect_T_list(df):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except:
                continue
    if ts:
        return sorted(ts)
    return T_LIST_FALLBACK

def normalize_tidy(res):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)".lower(), "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"

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

def prepare_sample(df, main_share, main_years, sample_urban):
    df = df.copy()

    num_cols = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    # non_migrant only
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    # rural / urban
    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    # age & birth-year
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    # FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # categorical controls (safe casting)
    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    # drop key NA
    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # nonlinear dummies
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
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
        "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
    }

def run_nonlinear(dfm):
    if not {"T_1", "T_2_3", "T_ge4"}.issubset(dfm.columns):
        return []

    fml = (
        f"edu_years ~ T_1 + T_2_3 + T_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())
    res = res[res["Term"].str.contains("T_", na=False)].copy()

    out_rows = []
    for _, r in res.iterrows():
        est = float(r["Estimate"])
        se  = float(r.get("StdError", np.nan))
        pv  = float(r.get("PValue", np.nan))
        out_rows.append({
            "Term": r["Term"],
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        })
    return out_rows


# ================================
# 2. PLOTTING
# ================================
def plot_linear(out_df, T_order, sample_urban, save_path):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    dfp = out_df[(out_df["model"] == "linear") & (out_df["sample_urban"] == sample_urban)].copy()
    if dfp.empty:
        print(f"[WARN] No linear results for {sample_urban}; skip plot.")
        return

    # Original notebook comment normalized for the public code archive.
    dfp["T_panel"] = pd.Categorical(dfp["T_panel"], T_order, ordered=True)
    dfp = dfp.sort_values("T_panel")

    xs = np.arange(len(T_order))
    ys = []
    ylow = []
    yhi = []
    pvs = []
    for t in T_order:
        row = dfp[dfp["T_panel"].astype(str) == str(t)]
        if row.empty:
            ys.append(np.nan); ylow.append(np.nan); yhi.append(np.nan); pvs.append(np.nan)
        else:
            r = row.iloc[0]
            ys.append(r["Estimate"])
            ylow.append(r["CI_low"])
            yhi.append(r["CI_high"])
            pvs.append(r["PValue"])

    ys = np.array(ys, float)
    ylow = np.array(ylow, float)
    yhi = np.array(yhi, float)

    seab = np.vstack([ys - ylow, yhi - ys])

    plt.figure(figsize=(9, 6))
    ax = plt.gca()
    ax.axhline(0, linewidth=1)

    ax.errorbar(xs, ys, yerr=seab, fmt="o", capsize=4)

    # Original notebook comment normalized for the public code archive.
    for x, y, pv in zip(xs, ys, pvs):
        if np.isfinite(pv) and pv < SIG_LEVEL and np.isfinite(y):
            ax.text(x, y + 0.03*(ax.get_ylim()[1]-ax.get_ylim()[0]),
                    "*", ha="center", va="bottom", fontsize=14)

    ax.set_xticks(xs)
    ax.set_xticklabels(T_order)
    ax.set_xlabel("T panel")
    ax.set_ylabel("Coefficient on share_flood_ge_T (linear)")
    ax.set_title(f"{sample_urban} | CaMa storage exposure (linear)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved figure: {save_path}")


# ================================
# 3. MAIN PIPELINE
# ================================
def main():
    print(f"[STEP] Load data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)
    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    # Original notebook comment normalized for the public code archive.
    T_order = [str(t).replace(".0", "") for t in T_list]

    all_rows = []

    for T in T_list:
        T_str = str(T).replace(".0", "")
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] Missing columns for T={T_str}: {main_share}/{main_years}")
            continue

        print(f"\n==============================")
        print(f"[PANEL] T={T_str} ({main_share})")
        print(f"==============================")

        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su)
            print(f"[SAMPLE] {su}, N={len(dfm)}")

            if len(dfm) == 0:
                continue

            # ----- linear
            lin = run_linear(dfm, main_share)
            if lin is not None:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "linear",
                    "sample_urban": su,
                    "Term": main_share,
                    **lin
                })

            # ----- nonlinear
            non_rows = run_nonlinear(dfm)
            for nr in non_rows:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "nonlinear",
                    "sample_urban": su,
                    **nr
                })

            # per-combo csv
            combo_df = pd.DataFrame([r for r in all_rows if r["T_panel"]==T_str and r["sample_urban"]==su])
            combo_df.to_csv(
                STATS_DIR / f"res_T{T_str}_{su}.csv",
                index=False, encoding="utf-8-sig"
            )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved master table: {OUT_MASTER_CSV}")
    print(out.head(10))

    # =========================
    # 4. Visualization (linear only)
    # =========================
    if out.empty:
        print("[WARN] out is empty; skip plots.")
        return

    # Original notebook comment normalized for the public code archive.
    lin_all = out[out["model"]=="linear"].copy()
    ymin = np.nanmin(lin_all["CI_low"].values)
    ymax = np.nanmax(lin_all["CI_high"].values)
    pad = 0.05*(ymax-ymin) if np.isfinite(ymax-ymin) else 0.1
    ylims = (ymin-pad, ymax+pad)

    # Original notebook comment normalized for the public code archive.
    for su, save_p in [("urban", OUT_FIG_URBAN), ("rural", OUT_FIG_RURAL)]:
        plt.figure(figsize=(9, 6))
        ax = plt.gca()
        ax.set_ylim(*ylims)
        plt.close()  # Original notebook comment normalized for the public code archive.

        # Original notebook comment normalized for the public code archive.
        plot_linear(out, T_order, su, save_p)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 22
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CaMa storage-based flood exposure (BM-Gumbel thresholds) × rural/urban (non_migrant)
One-click regressions + visualization with PyFixest.

Data:
  edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet

Exposure columns:
  share_flood_ge_T2, years_flood_ge_T2, ...
  share_flood_ge_T100, years_flood_ge_T100

Outputs (BM):
  1) cama_storage_allT_regs_BM.csv
  2) res_T{T}_{rural/urban}_BM.csv
  3) coefplot_storage_linear_urban_BM.png
     coefplot_storage_linear_rural_BM.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG (BM)
# ================================

DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/storage_allT_oneclick_BM"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = STATS_DIR / "cama_storage_allT_regs_BM.csv"
OUT_FIG_URBAN  = STATS_DIR / "coefplot_storage_linear_urban_BM.png"
OUT_FIG_RURAL  = STATS_DIR / "coefplot_storage_linear_rural_BM.png"

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True
SAMPLES_URBAN = ["rural", "urban"]
T_LIST_FALLBACK = [2, 5, 10, 20, 50, 100]

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# ================================
# 1. HELPERS
# ================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df):
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df

def detect_T_list(df):
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except:
                continue
    return sorted(ts) if ts else T_LIST_FALLBACK

def normalize_tidy(res):
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def prepare_sample(df, main_share, main_years, sample_urban):
    df = df.copy()
    num_cols = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    # fixed effects: county FE + province×birth FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # nonlinear bins (years of exposure)
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
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
        "nobs": get_nobs(fit, dfm),
    }

def run_nonlinear(dfm):
    if not {"T_1", "T_2_3", "T_ge4"}.issubset(dfm.columns):
        return []
    fml = (
        f"edu_years ~ T_1 + T_2_3 + T_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())
    res = res[res["Term"].str.contains("T_", na=False)].copy()

    out_rows = []
    for _, r in res.iterrows():
        est = float(r["Estimate"])
        se  = float(r.get("StdError", np.nan))
        pv  = float(r.get("PValue", np.nan))
        out_rows.append({
            "Term": r["Term"],
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        })
    return out_rows


# ================================
# 2. PLOTTING
# ================================
def plot_linear(out_df, T_order, sample_urban, save_path, ylims=None):
    dfp = out_df[(out_df["model"] == "linear") &
                 (out_df["sample_urban"] == sample_urban)].copy()
    if dfp.empty:
        print(f"[WARN] No linear results for {sample_urban}; skip plot.")
        return

    dfp["T_panel"] = pd.Categorical(dfp["T_panel"], T_order, ordered=True)
    dfp = dfp.sort_values("T_panel")

    xs = np.arange(len(T_order))
    ys, ylow, yhi, pvs = [], [], [], []
    for t in T_order:
        row = dfp[dfp["T_panel"].astype(str) == str(t)]
        if row.empty:
            ys.append(np.nan); ylow.append(np.nan); yhi.append(np.nan); pvs.append(np.nan)
        else:
            r = row.iloc[0]
            ys.append(r["Estimate"])
            ylow.append(r["CI_low"])
            yhi.append(r["CI_high"])
            pvs.append(r["PValue"])

    ys = np.array(ys, float)
    ylow = np.array(ylow, float)
    yhi = np.array(yhi, float)
    seab = np.vstack([ys - ylow, yhi - ys])

    plt.figure(figsize=(9, 6))
    ax = plt.gca()
    ax.axhline(0, linewidth=1)
    if ylims is not None:
        ax.set_ylim(*ylims)

    ax.errorbar(xs, ys, yerr=seab, fmt="o", capsize=4)

    for x, y, pv in zip(xs, ys, pvs):
        if np.isfinite(pv) and pv < SIG_LEVEL and np.isfinite(y):
            ax.text(x, y + 0.03*(ax.get_ylim()[1] - ax.get_ylim()[0]),
                    "*", ha="center", va="bottom", fontsize=14)

    ax.set_xticks(xs)
    ax.set_xticklabels(T_order)
    ax.set_xlabel("T panel")
    ax.set_ylabel("Coefficient on share_flood_ge_T (linear)")
    ax.set_title(f"{sample_urban} | CaMa storage exposure BM-Gumbel (linear)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved figure: {save_path}")


# ================================
# 3. MAIN
# ================================
def main():
    print(f"[STEP] Load BM micro data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)
    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    T_order = [str(t).replace(".0", "") for t in T_list]
    all_rows = []

    for T in T_list:
        T_str = str(T).replace(".0", "")
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] Missing columns for T={T_str}: {main_share}/{main_years}")
            continue

        print(f"\n==============================")
        print(f"[PANEL] T={T_str} ({main_share}) BM")
        print(f"==============================")

        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su)
            print(f"[SAMPLE] {su}, N={len(dfm)}")
            if len(dfm) == 0:
                continue

            lin = run_linear(dfm, main_share)
            if lin is not None:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "linear",
                    "sample_urban": su,
                    "Term": main_share,
                    **lin
                })

            non_rows = run_nonlinear(dfm)
            for nr in non_rows:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "nonlinear",
                    "sample_urban": su,
                    **nr
                })

            combo_df = pd.DataFrame([
                r for r in all_rows
                if r["T_panel"] == T_str and r["sample_urban"] == su
            ])
            combo_df.to_csv(
                STATS_DIR / f"res_T{T_str}_{su}_BM.csv",
                index=False, encoding="utf-8-sig"
            )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved BM master table: {OUT_MASTER_CSV}")
    print(out.head(10))

    if out.empty:
        print("[WARN] out is empty; skip plots.")
        return

    lin_all = out[out["model"] == "linear"].copy()
    ymin = np.nanmin(lin_all["CI_low"].values)
    ymax = np.nanmax(lin_all["CI_high"].values)
    pad = 0.05*(ymax - ymin) if np.isfinite(ymax - ymin) else 0.1
    ylims = (ymin - pad, ymax + pad)

    for su, save_p in [("urban", OUT_FIG_URBAN), ("rural", OUT_FIG_RURAL)]:
        plot_linear(out, T_order, su, save_p, ylims=ylims)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 25
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CaMa storage-based flood exposure regressions (BM-Gumbel), pooled on T2 only.
× rural/urban (non_migrant)
× (optional) river-risk group Low/High, from code2 output

Key change vs original:
  - Do NOT loop over return periods.
  - Use lowest threshold T2 as "overall flood exposure".

Data:
  edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet
Exposure columns used:
  share_flood_ge_T2, years_flood_ge_T2

Outputs:
  1) Master regression table:
     cama_storage_pooled_T2_regs_BM[_with_risk].csv
  2) Per-combo CSV:
     res_pooled_T2_{rural/urban}[_Low/High].csv
  3) Coefficient plots:
     coefplot_storage_linear_{urban/rural}[_Low/High]_pooledT2.png

Notes:
  - If your pyfixest version does not accept C(), replace CONTROL_FML
    with "i(M34)+i(M37)+i(M15)+i(M16)" or just "M34+M37+M15+M16"
    after converting to category (already done below).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG (BM pooled on T2)
# ================================

# BM micro data with exposure columns already merged
DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# Optional: risk zoning table from code2
USE_RISK_SPLIT = False  # <-- set True if you want Low/High splits
RISK_CSV = Path(
    "/home/ll/jupyter_notebook/gis_data/river/county_river_risk_binary.csv"
)
RISK_GROUPS = ["Low", "High"]

# Output directory
STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "storage_pooledT2_oneclick_BM"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = STATS_DIR / (
    "cama_storage_pooled_T2_regs_BM_with_risk.csv"
    if USE_RISK_SPLIT else
    "cama_storage_pooled_T2_regs_BM.csv"
)

# Figures
if USE_RISK_SPLIT:
    OUT_FIG = {
        ("urban", "Low"):  STATS_DIR / "coefplot_storage_linear_urban_Low_pooledT2.png",
        ("urban", "High"): STATS_DIR / "coefplot_storage_linear_urban_High_pooledT2.png",
        ("rural", "Low"):  STATS_DIR / "coefplot_storage_linear_rural_Low_pooledT2.png",
        ("rural", "High"): STATS_DIR / "coefplot_storage_linear_rural_High_pooledT2.png",
    }
else:
    OUT_FIG_URBAN = STATS_DIR / "coefplot_storage_linear_urban_pooledT2.png"
    OUT_FIG_RURAL = STATS_DIR / "coefplot_storage_linear_rural_pooledT2.png"

# Cohort window / sample restrictions
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True
SAMPLES_URBAN = ["rural", "urban"]

# Controls & significance star
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# ================================
# 1. HELPERS
# ================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df):
    # is_urban: M2 last two digits 1-20 are urban
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # is_migrant: M38=1 non-migrant
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df

def normalize_tidy(res):
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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


# ================================
# 2. RISK ZONING (optional)
# ================================

def load_risk_table_external():
    if not RISK_CSV.exists():
        raise FileNotFoundError(f"Risk CSV not found: {RISK_CSV}")
    risk = pd.read_csv(RISK_CSV, dtype={"county_code": str})
    if "risk_group" not in risk.columns:
        raise ValueError("risk_group column not found in risk csv.")

    risk = risk[["county_code", "risk_group"]].dropna()
    risk["county_code"] = risk["county_code"].str.strip().str.zfill(6)
    risk["risk_group"] = risk["risk_group"].astype(str)
    risk = risk[risk["risk_group"].isin(RISK_GROUPS)]
    return risk

def attach_risk_group(df_all):
    df_all = df_all.copy()
    df_all["county_code"] = (
        pd.to_numeric(df_all["M2"], errors="coerce")
        .astype("Int64").astype(str).str.zfill(6)
    )
    risk = load_risk_table_external()
    merged = df_all.merge(risk, how="left", on="county_code", validate="m:1")
    merged["risk_group"] = merged["risk_group"].fillna("Unknown")
    return merged


# ================================
# 3. SAMPLE + REGRESSION
# ================================

def prepare_sample(df, main_share, main_years, sample_urban, risk_group=None):
    df = df.copy()

    num_cols = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        "edu_years", main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    if risk_group is not None:
        mask &= (df["risk_group"] == risk_group)

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    # fixed effects: county FE + province×birth FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # categorical controls
    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    # main vars must exist
    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # nonlinear bins based on years of exposure
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
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
        "nobs": get_nobs(fit, dfm),
    }

def run_nonlinear(dfm):
    if not {"T_1", "T_2_3", "T_ge4"}.issubset(dfm.columns):
        return []
    fml = (
        f"edu_years ~ T_1 + T_2_3 + T_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())
    res = res[res["Term"].str.contains("T_", na=False)].copy()

    out_rows = []
    for _, r in res.iterrows():
        est = float(r["Estimate"])
        se  = float(r.get("StdError", np.nan))
        pv  = float(r.get("PValue", np.nan))
        out_rows.append({
            "Term": r["Term"],
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        })
    return out_rows


# ================================
# 4. PLOTTING (single T2 point)
# ================================

def plot_linear(out_df, T_order, sample_urban, save_path, risk_group=None, ylims=None):
    dfp = out_df[
        (out_df["model"] == "linear") &
        (out_df["sample_urban"] == sample_urban)
    ].copy()
    if risk_group is not None:
        dfp = dfp[dfp["risk_group"] == risk_group]

    if dfp.empty:
        print(f"[WARN] No linear results for {sample_urban}-{risk_group}; skip plot.")
        return

    dfp["T_panel"] = pd.Categorical(dfp["T_panel"], T_order, ordered=True)
    dfp = dfp.sort_values("T_panel")

    xs = np.arange(len(T_order))
    ys, ylow, yhi, pvs = [], [], [], []
    for t in T_order:
        row = dfp[dfp["T_panel"].astype(str) == str(t)]
        if row.empty:
            ys.append(np.nan); ylow.append(np.nan); yhi.append(np.nan); pvs.append(np.nan)
        else:
            r = row.iloc[0]
            ys.append(r["Estimate"])
            ylow.append(r["CI_low"])
            yhi.append(r["CI_high"])
            pvs.append(r["PValue"])

    ys = np.array(ys, float)
    ylow = np.array(ylow, float)
    yhi = np.array(yhi, float)
    seab = np.vstack([ys - ylow, yhi - ys])

    plt.figure(figsize=(7, 5))
    ax = plt.gca()
    ax.axhline(0, linewidth=1)
    if ylims is not None:
        ax.set_ylim(*ylims)

    ax.errorbar(xs, ys, yerr=seab, fmt="o", capsize=4)

    for x, y, pv in zip(xs, ys, pvs):
        if np.isfinite(pv) and pv < SIG_LEVEL and np.isfinite(y):
            ax.text(
                x, y + 0.03*(ax.get_ylim()[1] - ax.get_ylim()[0]),
                "*", ha="center", va="bottom", fontsize=14
            )

    ax.set_xticks(xs)
    ax.set_xticklabels(T_order)
    ax.set_xlabel("Return period panel (pooled on T2)")
    ax.set_ylabel("Coefficient on share_flood_ge_T2 (linear)")
    title = f"{sample_urban}"
    if risk_group is not None:
        title += f" | risk={risk_group}"
    title += " | CaMa storage exposure BM-Gumbel (linear, pooled T2)"
    ax.set_title(title)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved figure: {save_path}")


# ================================
# 5. MAIN (pooled on T2)
# ================================

def main():
    print(f"[STEP] Load BM micro data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    # ensure numeric for global M2/M38 before deriving urban/migrant
    df_all = ensure_numeric(df_all, ["M2", "M38"])
    df_all = build_is_urban_is_migrant(df_all)

    # optional risk split
    if USE_RISK_SPLIT:
        print("[STEP] Attach risk_group ...")
        df_all = attach_risk_group(df_all)
        print(df_all["risk_group"].value_counts(dropna=False))
        df_all = df_all[df_all["risk_group"].isin(RISK_GROUPS)].copy()
        print(f"[INFO] after dropping Unknown: {df_all.shape}")

    # pooled return period = T2
    T_str = "2"
    main_ret   = f"flood_ge_T{T_str}"
    main_share = f"share_{main_ret}"   # share_flood_ge_T2
    main_years = f"years_{main_ret}"   # years_flood_ge_T2

    if main_share not in df_all.columns or main_years not in df_all.columns:
        raise ValueError(f"Missing exposure columns: {main_share}/{main_years}")

    T_order = [T_str]  # single-point plot
    all_rows = []

    print("\n==============================")
    print(f"[PANEL] pooled on T2 ({main_share}) BM")
    print("==============================")

    if USE_RISK_SPLIT:
        for su in SAMPLES_URBAN:
            for rg in RISK_GROUPS:
                dfm = prepare_sample(df_all, main_share, main_years, su, rg)
                print(f"[SAMPLE] {su}-{rg}, N={len(dfm)}")
                if len(dfm) == 0:
                    continue

                lin = run_linear(dfm, main_share)
                if lin is not None:
                    all_rows.append({
                        "T_panel": T_str,
                        "model": "linear",
                        "sample_urban": su,
                        "risk_group": rg,
                        "method": "BM_Gumbel_pooledT2",
                        "Term": main_share,
                        **lin
                    })

                non_rows = run_nonlinear(dfm)
                for nr in non_rows:
                    all_rows.append({
                        "T_panel": T_str,
                        "model": "nonlinear",
                        "sample_urban": su,
                        "risk_group": rg,
                        "method": "BM_Gumbel_pooledT2",
                        **nr
                    })

                combo_df = pd.DataFrame([
                    r for r in all_rows
                    if r["sample_urban"] == su and r["risk_group"] == rg
                ])
                combo_df.to_csv(
                    STATS_DIR / f"res_pooled_T2_{su}_{rg}.csv",
                    index=False, encoding="utf-8-sig"
                )
    else:
        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su, risk_group=None)
            print(f"[SAMPLE] {su}, N={len(dfm)}")
            if len(dfm) == 0:
                continue

            lin = run_linear(dfm, main_share)
            if lin is not None:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "linear",
                    "sample_urban": su,
                    "method": "BM_Gumbel_pooledT2",
                    "Term": main_share,
                    **lin
                })

            non_rows = run_nonlinear(dfm)
            for nr in non_rows:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "nonlinear",
                    "sample_urban": su,
                    "method": "BM_Gumbel_pooledT2",
                    **nr
                })

            combo_df = pd.DataFrame([
                r for r in all_rows if r["sample_urban"] == su
            ])
            combo_df.to_csv(
                STATS_DIR / f"res_pooled_T2_{su}.csv",
                index=False, encoding="utf-8-sig"
            )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved pooled-T2 BM master table: {OUT_MASTER_CSV}")
    print(out.head(10))

    if out.empty:
        print("[WARN] out is empty; skip plots.")
        return

    lin_all = out[out["model"] == "linear"].copy()
    if lin_all.empty:
        print("[WARN] linear empty; skip plots.")
        return

    ymin = np.nanmin(lin_all["CI_low"].values)
    ymax = np.nanmax(lin_all["CI_high"].values)
    pad = 0.05*(ymax - ymin) if np.isfinite(ymax - ymin) else 0.1
    ylims = (ymin - pad, ymax + pad)

    if USE_RISK_SPLIT:
        for su in SAMPLES_URBAN:
            for rg in RISK_GROUPS:
                plot_linear(out, T_order, su, OUT_FIG[(su, rg)], risk_group=rg, ylims=ylims)
    else:
        plot_linear(out, T_order, "urban", OUT_FIG_URBAN, risk_group=None, ylims=ylims)
        plot_linear(out, T_order, "rural", OUT_FIG_RURAL, risk_group=None, ylims=ylims)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 28
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CaMa storage-based flood exposure (all T thresholds) × rural/urban (non_migrant)
One-click regressions + visualization with PyFixest.

【POT/GPD robustness version】
Data:
  edu_micro_2015_with_storage_T2_5_10_20_50_100_POT.parquet

Exposure columns assumed (same names as BM):
  share_flood_ge_T2, years_flood_ge_T2,
  share_flood_ge_T5, years_flood_ge_T5,
  ...
  share_flood_ge_T100, years_flood_ge_T100, etc.

Outputs (POT-tagged):
  1) Master regression table: cama_storage_allT_regs_POT.csv
  2) Per-combo CSV: res_T{T}_{rural/urban}_POT.csv
  3) Two coefficient plots (linear share):
     coefplot_storage_linear_urban_POT.png
     coefplot_storage_linear_rural_POT.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG  (POT version)
# ================================

# Original notebook comment normalized for the public code archive.
DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_T2_5_10_20_50_100_POT.parquet"
)

# Original notebook comment normalized for the public code archive.
STATS_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "storage_allT_oneclick_POT"
)
STATS_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = STATS_DIR / "cama_storage_allT_regs_POT.csv"
OUT_FIG_URBAN  = STATS_DIR / "coefplot_storage_linear_urban_POT.png"
OUT_FIG_RURAL  = STATS_DIR / "coefplot_storage_linear_rural_POT.png"

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

# Original notebook comment normalized for the public code archive.
ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
SAMPLES_URBAN = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_FALLBACK = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# Original notebook comment normalized for the public code archive.
SIG_LEVEL = 0.10


# ================================
# 1. HELPER FUNCTIONS
# ================================

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def build_is_urban_is_migrant(df):
    # is_urban from M2 (1-20 urban, else rural)
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    # is_migrant from M38 (M38=1 -> non_migrant)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df

def detect_T_list(df):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except:
                continue
    if ts:
        return sorted(ts)
    return T_LIST_FALLBACK

def normalize_tidy(res):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)".lower(), "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"

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

def prepare_sample(df, main_share, main_years, sample_urban):
    df = df.copy()

    num_cols = [
        "M2", "M38", "M52", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3",
        main_share, main_years
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    # non_migrant only
    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    # rural / urban
    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)

    # age & birth-year
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df[mask].copy()

    # FE
    dfm["prov_code"] = (dfm["M2"] // 10000).astype(int)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(int).astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # categorical controls (safe casting)
    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    # drop key NA
    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # nonlinear dummies
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
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
        "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
    }

def run_nonlinear(dfm):
    if not {"T_1", "T_2_3", "T_ge4"}.issubset(dfm.columns):
        return []

    fml = (
        f"edu_years ~ T_1 + T_2_3 + T_ge4 + "
        f"{CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())
    res = res[res["Term"].str.contains("T_", na=False)].copy()

    out_rows = []
    for _, r in res.iterrows():
        est = float(r["Estimate"])
        se  = float(r.get("StdError", np.nan))
        pv  = float(r.get("PValue", np.nan))
        out_rows.append({
            "Term": r["Term"],
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96*se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96*se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        })
    return out_rows


# ================================
# 2. PLOTTING
# ================================
def plot_linear(out_df, T_order, sample_urban, save_path):
    """Archived notebook note for 01_baseline_education_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    dfp = out_df[(out_df["model"] == "linear") & (out_df["sample_urban"] == sample_urban)].copy()
    if dfp.empty:
        print(f"[WARN] No linear results for {sample_urban}; skip plot.")
        return

    dfp["T_panel"] = pd.Categorical(dfp["T_panel"], T_order, ordered=True)
    dfp = dfp.sort_values("T_panel")

    xs = np.arange(len(T_order))
    ys, ylow, yhi, pvs = [], [], [], []

    for t in T_order:
        row = dfp[dfp["T_panel"].astype(str) == str(t)]
        if row.empty:
            ys.append(np.nan); ylow.append(np.nan); yhi.append(np.nan); pvs.append(np.nan)
        else:
            r = row.iloc[0]
            ys.append(r["Estimate"])
            ylow.append(r["CI_low"])
            yhi.append(r["CI_high"])
            pvs.append(r["PValue"])

    ys = np.array(ys, float)
    ylow = np.array(ylow, float)
    yhi = np.array(yhi, float)
    seab = np.vstack([ys - ylow, yhi - ys])

    plt.figure(figsize=(9, 6))
    ax = plt.gca()
    ax.axhline(0, linewidth=1)
    ax.errorbar(xs, ys, yerr=seab, fmt="o", capsize=4)

    for x, y, pv in zip(xs, ys, pvs):
        if np.isfinite(pv) and pv < SIG_LEVEL and np.isfinite(y):
            ax.text(x, y + 0.03*(ax.get_ylim()[1]-ax.get_ylim()[0]),
                    "*", ha="center", va="bottom", fontsize=14)

    ax.set_xticks(xs)
    ax.set_xticklabels(T_order)
    ax.set_xlabel("T panel")
    ax.set_ylabel("Coefficient on share_flood_ge_T (linear)")
    ax.set_title(f"{sample_urban} | CaMa storage exposure (linear, POT)")
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved figure: {save_path}")


# ================================
# 3. MAIN PIPELINE
# ================================
def main():
    print(f"[STEP] Load POT micro data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)
    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    T_order = [str(t).replace(".0", "") for t in T_list]
    all_rows = []

    for T in T_list:
        T_str = str(T).replace(".0", "")
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] Missing columns for T={T_str}: {main_share}/{main_years}")
            continue

        print(f"\n==============================")
        print(f"[PANEL] T={T_str} ({main_share})")
        print(f"==============================")

        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su)
            print(f"[SAMPLE] {su}, N={len(dfm)}")

            if len(dfm) == 0:
                continue

            # ----- linear
            lin = run_linear(dfm, main_share)
            if lin is not None:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "linear",
                    "sample_urban": su,
                    "method": "POT_GPD",
                    "Term": main_share,
                    **lin
                })

            # ----- nonlinear
            non_rows = run_nonlinear(dfm)
            for nr in non_rows:
                all_rows.append({
                    "T_panel": T_str,
                    "model": "nonlinear",
                    "sample_urban": su,
                    "method": "POT_GPD",
                    **nr
                })

            # per-combo csv (POT-tagged)
            combo_df = pd.DataFrame([
                r for r in all_rows
                if r["T_panel"] == T_str and r["sample_urban"] == su
            ])
            combo_df.to_csv(
                STATS_DIR / f"res_T{T_str}_{su}_POT.csv",
                index=False, encoding="utf-8-sig"
            )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved master POT table: {OUT_MASTER_CSV}")
    print(out.head(10))

    # =========================
    # 4. Visualization (linear only)
    # =========================
    if out.empty:
        print("[WARN] out is empty; skip plots.")
        return

    lin_all = out[out["model"] == "linear"].copy()
    ymin = np.nanmin(lin_all["CI_low"].values)
    ymax = np.nanmax(lin_all["CI_high"].values)
    pad = 0.05*(ymax-ymin) if np.isfinite(ymax-ymin) else 0.1
    ylims = (ymin-pad, ymax+pad)

    for su, save_p in [("urban", OUT_FIG_URBAN), ("rural", OUT_FIG_RURAL)]:
        plt.figure(figsize=(9, 6))
        ax = plt.gca()
        ax.set_ylim(*ylims)
        plt.close()
        plot_linear(out, T_order, su, save_p)


if __name__ == "__main__":
    main()
