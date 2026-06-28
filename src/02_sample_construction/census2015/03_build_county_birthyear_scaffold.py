#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_build_county_birthyear_scaffold.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# =============================================================================
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# =============================================================================
PATH_PARQUET = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015.parquet")
OUT_DIR      = Path(r"E:\project_flood_impact_assessment\census")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
COHORT_START, COHORT_END = 1985, 2000

# =============================================================================
pf = pq.ParquetFile(PATH_PARQUET)
avail = set(pf.schema_arrow.names)

need = [
    "M1","M2","birth_year","M51","edu_years","hs_any","hs_general","M52",
    "M46","M48"  # Original notebook comment normalized for the public code archive.
]
use_cols = [c for c in need if c in avail]

df = pd.read_parquet(PATH_PARQUET, columns=use_cols, engine="pyarrow")

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "M1" in df.columns:
    df["M1"] = df["M1"].astype(str).str.strip()
    df.loc[df["M1"].str.lower().isin(["nan","none",""]), "M1"] = pd.NA

# Original notebook comment normalized for the public code archive.
for c in [x for x in ["M2","birth_year","M51","edu_years","hs_any","hs_general","M52","M46","M48"] if x in df.columns]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Original notebook comment normalized for the public code archive.
if "M2" in df.columns:
    df["M2"] = df["M2"].astype("Int64")

# =============================================================================
mask = (
    df["M2"].notna() &
    df["birth_year"].between(COHORT_START, COHORT_END) &
    df["M51"].notna()
)
df_an = df.loc[mask].copy()

# Original notebook comment normalized for the public code archive.
if {"M46","M48"}.issubset(df_an.columns):
    df_an["non_migrant"] = ((df_an["M46"] == 1) & (df_an["M48"] == 1)).astype("Int64")
else:
    df_an["non_migrant"] = pd.NA

# Original notebook comment normalized for the public code archive.
OUT_ANALYSIS = OUT_DIR / "analysis_sample.parquet"
df_an.to_parquet(OUT_ANALYSIS, index=False)

# =============================================================================
agg_items = {
    "M51_mean": ("M51", "mean"),
    "N":        ("M2",  "size"),
    "valid_M51":("M51", "count"),
}
if "edu_years" in df_an.columns:
    agg_items["edu_years_mean"] = ("edu_years","mean")
if "hs_any" in df_an.columns:
    agg_items["hs_any_mean"] = ("hs_any","mean")
if "hs_general" in df_an.columns:
    agg_items["hs_general_mean"] = ("hs_general","mean")

cc = (
    df_an.groupby(["M2","birth_year"], as_index=False)
         .agg(**agg_items)
)

# Original notebook comment normalized for the public code archive.
if "M1" in df_an.columns:
    m1_mode = (
        df_an.dropna(subset=["M1"])
             .groupby(["M2","birth_year"])["M1"]
             .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
             .reset_index()
    )
    cc = cc.merge(m1_mode, on=["M2","birth_year"], how="left")

# Original notebook comment normalized for the public code archive.
cc = cc.sort_values(["M2","birth_year"], kind="stable")
for c in [x for x in ["N","valid_M51"] if x in cc.columns]:
    cc[c] = cc[c].round().astype("Int64")
cc["M2"] = cc["M2"].astype("Int64")

# Original notebook comment normalized for the public code archive.
OUT_CC_PQ   = OUT_DIR / "county_cohort_cells.parquet"
OUT_CC_XLSX = OUT_DIR / "county_cohort_cells.xlsx"
cc.to_parquet(OUT_CC_PQ, index=False)

with pd.ExcelWriter(OUT_CC_XLSX, engine="openpyxl") as w:
    cc.to_excel(w, sheet_name="cells", index=False)
    ws = w.sheets["cells"]
    m2_idx = list(cc.columns).index("M2") + 1
    for col in ws.iter_cols(min_col=m2_idx, max_col=m2_idx, min_row=2, max_row=ws.max_row):
        for cell in col:
            cell.number_format = "0"

# =============================================================================
keys = cc.loc[:, ["M2","birth_year"]].drop_duplicates().reset_index(drop=True)

def expand_years(row):
    y0, y1 = int(row["birth_year"]), int(row["birth_year"]) + 15
    return pd.DataFrame({
        "M2": row["M2"],
        "birth_year": row["birth_year"],
        "year": np.arange(y0, y1 + 1, dtype=int)  # Original notebook comment normalized for the public code archive.
    })

scaffold = pd.concat([expand_years(r) for _, r in keys.iterrows()], ignore_index=True)
OUT_SCAFFOLD = OUT_DIR / "county_cohort_years_scaffold.parquet"
scaffold.to_parquet(OUT_SCAFFOLD, index=False)

# =============================================================================
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
