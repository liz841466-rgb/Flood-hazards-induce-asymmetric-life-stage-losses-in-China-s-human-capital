#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_construct_three_channel_indices.

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
import numpy as np
import pandas as pd

BASE = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health")
FILE = BASE / "Health_investment_with_Access_panel_2011_2020_citycode.xlsx"

print("[INFO] Notebook progress message.", FILE)
df = pd.read_excel(FILE, sheet_name="Sheet1")

# Original notebook comment normalized for the public code archive.
df = df[df["year"].between(2011, 2018)].copy()
print("[INFO] Notebook progress message.", len(df))


# =============================================================================

def zscore(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_construct_three_channel_indices.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = s.astype(float)
    mu = s.mean(skipna=True)
    sigma = s.std(skipna=True)
    if pd.isna(sigma) or sigma == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - mu) / sigma


def safe_log1p(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_construct_three_channel_indices.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = s.astype(float)
    s = s.where(s >= 0, np.nan)
    return np.log1p(s)


# =============================================================================

# Original notebook comment normalized for the public code archive.
oop_cols = [
    "outpt_month_oop",
    "outpt_last_oop",
    "inp_year_oop",
    "inp_last_oop",
    "self_treat_oop"
]
df["oop_total"] = df[oop_cols].fillna(0).sum(axis=1)
df["oop_total_log"] = safe_log1p(df["oop_total"])

# Original notebook comment normalized for the public code archive.
df["oop_share_med"] = np.where(
    df["hh_med_year"] > 0,
    df["oop_total"] / df["hh_med_year"],
    np.nan
)
df["oop_share_health"] = np.where(
    df["hh_health_year"] > 0,
    df["oop_total"] / df["hh_health_year"],
    np.nan
)

# Original notebook comment normalized for the public code archive.
for c in ["oop_share_med", "oop_share_health"]:
    df.loc[df[c] > 20, c] = 20

# Original notebook comment normalized for the public code archive.
fin_vars = ["oop_total_log", "oop_share_med", "oop_share_health"]
for v in fin_vars:
    df[f"z_{v}"] = zscore(df[v])

df["fin_burden_index_raw"] = df[[f"z_{v}" for v in fin_vars]].mean(axis=1, skipna=True)
df["fin_burden_index"] = zscore(df["fin_burden_index_raw"])


# =============================================================================

# Original notebook comment normalized for the public code archive.
df["log_outpt_visits"] = safe_log1p(df["ed005_visits"].fillna(0))
df["log_outpt_month_total"] = safe_log1p(df["outpt_month_total"].fillna(0))
df["log_inp_year_total"] = safe_log1p(df["inp_year_total"].fillna(0))

util_vars = [
    "has_outpt",          # 0/1
    "inp_any",            # 0/1
    "log_outpt_visits",
    "log_outpt_month_total",
    "log_inp_year_total"
]

for v in util_vars:
    df[f"z_{v}"] = zscore(df[v])

df["utilization_index_raw"] = df[[f"z_{v}" for v in util_vars]].mean(axis=1, skipna=True)
df["utilization_index"] = zscore(df["utilization_index_raw"])


# =============================================================================

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
df["outpt_walk_bad"] = df["outpt_walk"].map({1: 0, 0: 1})
df["outpt_homevisit_bad"] = df["outpt_homevisit"].map({1: 0, 0: 1})
df["inp_walk_bad"] = df["inp_walk"].map({1: 0, 0: 1})

# Original notebook comment normalized for the public code archive.
dist_time_cost_cols = [
    "outpt_dist_single_unc",
    "outpt_time_single_unc",
    "outpt_cost_single_unc",
    "inp_dist_single_unc",
    "inp_time_single_unc",
    "inp_cost_single_unc",
]

for v in dist_time_cost_cols:
    df[f"log_{v}"] = safe_log1p(df[v])

access_vars = [
    "log_outpt_dist_single_unc",
    "log_outpt_time_single_unc",
    "log_outpt_cost_single_unc",
    "log_inp_dist_single_unc",
    "log_inp_time_single_unc",
    "log_inp_cost_single_unc",
    "outpt_walk_bad",
    "outpt_homevisit_bad",
    "inp_walk_bad"
]

for v in access_vars:
    df[f"z_{v}"] = zscore(df[v])

df["poor_access_index_raw"] = df[[f"z_{v}" for v in access_vars]].mean(axis=1, skipna=True)
df["poor_access_index"] = zscore(df["poor_access_index_raw"])


# =============================================================================
print("[INFO] Notebook progress message.")
summary = (
    df.groupby("year")[["fin_burden_index", "utilization_index", "poor_access_index"]]
      .describe()
)
print(summary)


# =============================================================================
OUT_PARQUET = BASE / "Health_channels_index_2011_2018.parquet"
OUT_XLSX = BASE / "Health_channels_index_2011_2018.xlsx"

df_out = df[[
    "ID12", "year", "city_code",
    "fin_burden_index",
    "utilization_index",
    "poor_access_index"
]].copy()

df_out.to_parquet(OUT_PARQUET, index=False)
df_out.to_excel(OUT_XLSX, index=False, sheet_name="Sheet1")

print("[INFO] Notebook progress message.")
print("  -", OUT_PARQUET)
print("  -", OUT_XLSX)
