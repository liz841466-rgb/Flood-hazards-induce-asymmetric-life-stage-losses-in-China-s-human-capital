#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_extract_region_education_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path

# =============================================================================
PATH_DTA = Path(r"E:\project_flood_impact_assessment\census\spss_2015.dta")
OUT_XLSX = Path(r"E:\project_flood_impact_assessment\census\M1_M2_M51.xlsx")

COLS = ["M1", "M2", "M51"]          # Original notebook comment normalized for the public code archive.
CHUNK = 200_000                     # Original notebook comment normalized for the public code archive.
MAX_XLSX_ROWS = 1_048_576           # Excel output note.

# =============================================================================
sheet_idx = 1
startrow = 0                        # Original notebook comment normalized for the public code archive.
total_rows = 0

with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
    # Original notebook comment normalized for the public code archive.
    reader = pd.read_stata(
        PATH_DTA, iterator=True, chunksize=CHUNK,
        columns=COLS, convert_categoricals=False
    )

    for chunk in reader:
        # Original notebook comment normalized for the public code archive.
        if startrow == 0:
            header_flag = True
        else:
            header_flag = False

        if startrow + len(chunk) > MAX_XLSX_ROWS:
            sheet_idx += 1
            startrow = 0
            header_flag = True  # Original notebook comment normalized for the public code archive.

        chunk.to_excel(
            writer,
            sheet_name=f"Sheet{sheet_idx}",
            index=False,
            startrow=startrow,
            header=header_flag
        )
        startrow += len(chunk)
        total_rows += len(chunk)

print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path

# =============================================================================
PATH_DTA = Path(r"E:\project_flood_impact_assessment\census\spss_2015.dta")
OUT_XLSX = Path(r"E:\project_flood_impact_assessment\census\M1M2_M51_mean.xlsx")

COLS = ["M1", "M2", "M51"]
CHUNK = 200_000  # Original notebook comment normalized for the public code archive.

# =============================================================================
agg = None
total_groups_seen = 0

reader = pd.read_stata(
    PATH_DTA, iterator=True, chunksize=CHUNK,
    columns=COLS, convert_categoricals=False
)

for i, chunk in enumerate(reader, 1):
    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    chunk["M1"] = chunk["M1"].astype(str).str.strip()
    # Original notebook comment normalized for the public code archive.
    chunk.loc[chunk["M1"].str.lower().isin(["nan", "none", ""]), "M1"] = pd.NA

    # Original notebook comment normalized for the public code archive.
    chunk["M2"] = pd.to_numeric(chunk["M2"], errors="coerce").astype("Int64")
    # Original notebook comment normalized for the public code archive.
    chunk["M51"] = pd.to_numeric(chunk["M51"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    chunk = chunk.dropna(subset=["M1", "M2"])

    # Original notebook comment normalized for the public code archive.
    g = chunk.groupby(["M1", "M2"]).agg(
        M51_sum=("M51", "sum"),
        M51_cnt=("M51", "count"),   # Original notebook comment normalized for the public code archive.
        N=("M1", "size")            # Original notebook comment normalized for the public code archive.
    )

    total_groups_seen += len(g)

    # Original notebook comment normalized for the public code archive.
    agg = g if agg is None else agg.add(g, fill_value=0)

# Original notebook comment normalized for the public code archive.
result = agg.copy()
result["M51_mean"] = result["M51_sum"] / result["M51_cnt"]
result = (
    result.reset_index()
          .loc[:, ["M1", "M2", "N", "M51_cnt", "M51_mean"]]
          .sort_values(["M1", "M2"], kind="stable")
)

# Original notebook comment normalized for the public code archive.
for c in ["N", "M51_cnt"]:
    result[c] = result[c].round().astype("Int64")

# Original notebook comment normalized for the public code archive.
result["M2"] = result["M2"].astype("Int64")

# =============================================================================
with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
    result.to_excel(writer, sheet_name="mean_by_M1_M2", index=False)
    ws = writer.sheets["mean_by_M1_M2"]
    # Original notebook comment normalized for the public code archive.
    for col in ws.iter_cols(min_col=2, max_col=2, min_row=2, max_row=ws.max_row):
        for cell in col:
            cell.number_format = "0"

print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# =========================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# =========================================
from pathlib import Path
import pandas as pd
import numpy as np

# =============================================================================
PATH_DTA = Path(r"E:\project_flood_impact_assessment\census\spss_2015.dta")
OUT_PARQUET = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015.parquet")
OUT_XLSX_SAMPLE = Path(r"E:\project_flood_impact_assessment\census\edu_micro_2015_sample.xlsx")

# =============================================================================
VARS_BASE = [
    "M1","M2",          # Original notebook comment normalized for the public code archive.
    "M35","M36",        # Original notebook comment normalized for the public code archive.
    "M51","M52",        # Original notebook comment normalized for the public code archive.
    "M34","M37",        # Original notebook comment normalized for the public code archive.
    "M3","M7",          # Original notebook comment normalized for the public code archive.
    "M39","M40","M41",  # Original notebook comment normalized for the public code archive.
    "M46","M47","M48","M49"  # Original notebook comment normalized for the public code archive.
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
except Exception:
    READ_COLS = VARS_BASE  # Original notebook comment normalized for the public code archive.

print("[INFO] Notebook progress message.", READ_COLS)

# =============================================================================
parts = []
reader = pd.read_stata(
    PATH_DTA, iterator=True, chunksize=CHUNK,
    columns=READ_COLS, convert_categoricals=False
)

for chunk in reader:
    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    chunk["M1"] = chunk["M1"].astype(str).str.strip()
    chunk.loc[chunk["M1"].str.lower().isin(["nan","none",""]), "M1"] = pd.NA
    chunk["M2"] = pd.to_numeric(chunk["M2"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    chunk["M51"] = pd.to_numeric(chunk["M51"], errors="coerce")
    chunk["M52"] = pd.to_numeric(chunk["M52"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    for c in ["M35","M36","M34","M37","M3","M7","M39","M40","M41","M46","M47","M48","M49"]:
        if c in chunk.columns:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    chunk["edu_years"] = chunk["M51"].map(M51_to_years).astype("float")
    # Original notebook comment normalized for the public code archive.
    chunk["hs_any"] = chunk["M51"].ge(4).astype("Int64")        # Original notebook comment normalized for the public code archive.
    chunk["hs_general"] = (chunk["M51"] == 4).astype("Int64")   # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    chunk["birth_year"] = chunk["M35"].astype("Int64")
    chunk["age_2015"] = (2015 - chunk["M35"]).astype("float")

    # Original notebook comment normalized for the public code archive.
    keep = [
        "M1","M2","birth_year","M36","M34","M37","M3","M7",
        "M39","M40","M41","M46","M47","M48","M49",
        "M51","edu_years","hs_any","hs_general","M52","age_2015"
    ]
    keep = [c for c in keep if c in chunk.columns]
    parts.append(chunk[keep])

# =============================================================================
df = pd.concat(parts, ignore_index=True)

# Original notebook comment normalized for the public code archive.
df["M2"] = df["M2"].astype("Int64")

df.to_parquet(OUT_PARQUET, index=False)
print("[INFO] Notebook progress message.")

# Excel output note.
sample = df.sample(n=min(100_000, len(df)), random_state=42)
with pd.ExcelWriter(OUT_XLSX_SAMPLE, engine="openpyxl") as w:
    sample.to_excel(w, index=False, sheet_name="sample_100k")
    ws = w.sheets["sample_100k"]
    # Original notebook comment normalized for the public code archive.
    m2_col_idx = list(sample.columns).index("M2") + 1
    for col in ws.iter_cols(min_col=m2_col_idx, max_col=m2_col_idx, min_row=2, max_row=ws.max_row):
        for cell in col:
            cell.number_format = "0"

print("[INFO] Notebook progress message.")
