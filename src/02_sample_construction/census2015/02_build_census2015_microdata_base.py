#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_build_census2015_microdata_base.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# =============================================================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import warnings

# Original notebook comment normalized for the public code archive.
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# =============================================================================
PATH_DTA = Path(r"E:\project_flood_impact_assessment\census\spss_2015.dta")
OUT_PARQUET = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015.parquet")
OUT_XLSX_SAMPLE = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015_sample.xlsx")

# =============================================================================
VARS_BASE = [
    "M1", "M2",         # Original notebook comment normalized for the public code archive.
    "M35", "M36",       # Original notebook comment normalized for the public code archive.
    "M51", "M52",       # Original notebook comment normalized for the public code archive.
    "M34", "M37",       # Original notebook comment normalized for the public code archive.
    "M3", "M7",         # Original notebook comment normalized for the public code archive.
    "M15", "M16",       # Original notebook comment normalized for the public code archive.
    "M38",              # Original notebook comment normalized for the public code archive.
    "M39", "M40", "M41",# Original notebook comment normalized for the public code archive.
    "M46", "M47", "M48", "M49" # Original notebook comment normalized for the public code archive.
]
CHUNK = 200_000  # Original notebook comment normalized for the public code archive.

# =============================================================================
M51_to_years = {
    1: 0,   # Original notebook comment normalized for the public code archive.
    2: 6,   # Original notebook comment normalized for the public code archive.
    3: 9,   # Original notebook comment normalized for the public code archive.
    4: 12,  # Original notebook comment normalized for the public code archive.
    5: 12,  # Original notebook comment normalized for the public code archive.
    6: 15,  # Original notebook comment normalized for the public code archive.
    7: 16,  # Original notebook comment normalized for the public code archive.
    8: 18   # Original notebook comment normalized for the public code archive.
}

# =============================================================================
try:
    import pyreadstat
    _, meta0 = pyreadstat.read_dta(str(PATH_DTA), row_limit=0)
    has_cols = set(meta0.column_names)
    READ_COLS = [c for c in VARS_BASE if c in has_cols]
except Exception as e:
    print("[INFO] Notebook progress message.")
    READ_COLS = VARS_BASE

print("[INFO] Notebook progress message.")

# =============================================================================
parts = []
reader = pd.read_stata(
    PATH_DTA, iterator=True, chunksize=CHUNK,
    columns=READ_COLS, convert_categoricals=False
)

for i, chunk in enumerate(reader):
    if i % 5 == 0:
        print("[INFO] Notebook progress message.")

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    chunk["M1"] = chunk["M1"].astype(str).str.strip()
    chunk.loc[chunk["M1"].str.lower().isin(["nan", "none", ""]), "M1"] = pd.NA
    
    # Original notebook comment normalized for the public code archive.
    chunk["M2"] = pd.to_numeric(chunk["M2"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    numeric_cols = [
        "M35", "M36", "M51", "M52", "M34", "M37", "M3", "M7", 
        "M15", "M16", "M38", "M39", "M40", "M41", 
        "M46", "M47", "M48", "M49"
    ]
    for c in numeric_cols:
        if c in chunk.columns:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

    # =============================================================================
    if "M51" in chunk.columns:
        # Original notebook comment normalized for the public code archive.
        chunk["edu_years"] = chunk["M51"].map(M51_to_years).astype("float")
        # Original notebook comment normalized for the public code archive.
        chunk["hs_any"] = chunk["M51"].ge(4).astype("Int64")
        # Original notebook comment normalized for the public code archive.
        chunk["hs_general"] = (chunk["M51"] == 4).astype("Int64")

    # =============================================================================
    if "M35" in chunk.columns:
        chunk["birth_year"] = chunk["M35"].astype("Int64")
        chunk["age_2015"] = (2015 - chunk["M35"]).astype("float")

    # =======================================================
    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    # =======================================================
    if "M2" in chunk.columns:
        # Original notebook comment normalized for the public code archive.
        suffix = chunk["M2"] % 100
        
        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        is_urban_condition = (suffix >= 1) & (suffix <= 20)
        
        chunk["is_urban"] = np.where(is_urban_condition, 1, 0)
        chunk.loc[chunk["M2"].isna(), "is_urban"] = pd.NA
        chunk["is_urban"] = chunk["is_urban"].astype("Int64")

    # =======================================================
    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # =======================================================
    if "M38" in chunk.columns:
        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        chunk["is_migrant"] = np.where(chunk["M38"] == 1, 0, 1)
        chunk.loc[chunk["M38"].isna(), "is_migrant"] = pd.NA
        chunk["is_migrant"] = chunk["is_migrant"].astype("Int64")

    # =============================================================================
    keep_candidates = [
        "M1", "M2", "is_urban",           # Original notebook comment normalized for the public code archive.
        "birth_year", "M36", "age_2015",  # Original notebook comment normalized for the public code archive.
        "M34", "M37",                     # Original notebook comment normalized for the public code archive.
        "M51", "edu_years", "hs_any", "hs_general", "M52", # Original notebook comment normalized for the public code archive.
        "is_migrant", "M38", "M39", "M40", "M41", # Original notebook comment normalized for the public code archive.
        "M3", "M7", "M15", "M16",         # Original notebook comment normalized for the public code archive.
        "M46", "M47", "M48", "M49"        # Original notebook comment normalized for the public code archive.
    ]
    # Original notebook comment normalized for the public code archive.
    keep = [c for c in keep_candidates if c in chunk.columns]
    parts.append(chunk[keep])

# =============================================================================
if parts:
    df = pd.concat(parts, ignore_index=True)
    
    # Original notebook comment normalized for the public code archive.
    if "M2" in df.columns:
        df["M2"] = df["M2"].astype("Int64")

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df.to_parquet(OUT_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Excel output note.
    sample = df.sample(n=min(100_000, len(df)), random_state=42)
    with pd.ExcelWriter(OUT_XLSX_SAMPLE, engine="openpyxl") as w:
        sample.to_excel(w, index=False, sheet_name="sample_100k")
        
        # Original notebook comment normalized for the public code archive.
        ws = w.sheets["sample_100k"]
        if "M2" in sample.columns:
            m2_idx = list(sample.columns).index("M2") + 1
            for col in ws.iter_cols(min_col=m2_idx, max_col=m2_idx, min_row=2, max_row=ws.max_row):
                for cell in col:
                    cell.number_format = "0"
    print("[INFO] Notebook progress message.")

else:
    print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd

# =============================================================================
IN_PARQUET = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015.parquet")
OUT_DIR    = Path(r"E:\project_flood_impact_assessment\census\exports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

COHORT_START, COHORT_END = 1985, 2000
MAX_XLSX_ROWS = 1_000_000   # Excel output note.

# Original notebook comment normalized for the public code archive.
df = pd.read_parquet(IN_PARQUET)  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
if "birth_year" not in df.columns:
    df["birth_year"] = pd.to_numeric(df["M35"], errors="coerce")
df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")

# Original notebook comment normalized for the public code archive.
sub = df[df["birth_year"].between(COHORT_START, COHORT_END, inclusive="both")].copy()

# Original notebook comment normalized for the public code archive.
if "M2" in sub.columns:
    sub["M2"] = pd.to_numeric(sub["M2"], errors="coerce").astype("Int64")

# Original notebook comment normalized for the public code archive.
sub_parquet = OUT_DIR / "edu_micro_2015_1985_2000.parquet"
sub.to_parquet(sub_parquet, index=False)

# Original notebook comment normalized for the public code archive.
n = len(sub)
if n == 0:
    print("[INFO] Notebook progress message.")
else:
    parts = (n + MAX_XLSX_ROWS - 1) // MAX_XLSX_ROWS
    for k in range(parts):
        chunk = sub.iloc[k*MAX_XLSX_ROWS : (k+1)*MAX_XLSX_ROWS]
        out_xlsx = OUT_DIR / (f"edu_micro_2015_1985_2000_part{k+1}.xlsx" if parts>1
                              else "edu_micro_2015_1985_2000.xlsx")
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
            chunk.to_excel(w, index=False, sheet_name="data")
            if "M2" in chunk.columns:
                ws = w.sheets["data"]
                col_idx = list(chunk.columns).index("M2") + 1
                # Original notebook comment normalized for the public code archive.
                for col in ws.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2, max_row=ws.max_row):
                    for cell in col:
                        cell.number_format = "0"   # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    counts = sub["birth_year"].value_counts().sort_index().rename_axis("birth_year").to_frame("n")
    counts.to_excel(OUT_DIR / "edu_micro_2015_1985_2000_summary.xlsx", index=True)

    print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd

# =============================================================================
IN_PARQUET = Path(r"E:\project_flood_impact_assessment\census\exports\edu_micro_2015_1985_2000.parquet")
OUT_XLSX   = IN_PARQUET.with_name("county_mean_M51_M52.xlsx")

# Original notebook comment normalized for the public code archive.
use_cols = ["M2", "M51", "M52"]
df = pd.read_parquet(IN_PARQUET, columns=[c for c in use_cols if c in pd.read_parquet(IN_PARQUET, columns=[]).columns]
                     if False else use_cols)  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
df["M2"]  = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
if "M51" in df.columns: df["M51"] = pd.to_numeric(df["M51"], errors="coerce")
if "M52" in df.columns: df["M52"] = pd.to_numeric(df["M52"], errors="coerce")

# Original notebook comment normalized for the public code archive.
df = df[df["M2"].notna()].copy()

# =============================================================================
agg_dict = {
    "n": ("M2", "size"),
    "M51_mean": ("M51", "mean"),
    "M51_valid": ("M51", "count"),
}
if "M52" in df.columns:
    agg_dict.update({
        "M52_mean": ("M52", "mean"),
        "M52_valid": ("M52", "count"),
    })

g = (df.groupby("M2", as_index=False)
       .agg(**agg_dict)
       .sort_values("n", ascending=False))

# Original notebook comment normalized for the public code archive.
for c in [col for col in g.columns if col.endswith("_mean")]:
    g[c] = g[c].round(3)

# =============================================================================
with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
    g.to_excel(w, index=False, sheet_name="county_means")
    ws = w.sheets["county_means"]
    col_idx = list(g.columns).index("M2") + 1
    for col in ws.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2, max_row=ws.max_row):
        for cell in col:
            cell.number_format = "0"

print("[INFO] Notebook progress message.")
