#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_initial_mechanism_design_and_data_review.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------

# Individual-level variables: outpt_month_oop, inp_year_oop, self_treat_oop.
# Household-level variables: hh_med_year / ge010_6; expenditure-share construction can be handled separately.
# Healthcare-use variables: has_outpt, inp_any, ef001, medicine purchases, visits, hospitalization, and self-treatment spending.
# Time variables: outpt_time_single_unc, inp_time_single_unc, outpt_time_month_unc.
# Distance variables: outpt_dist_single_unc, inp_dist_single_unc.
# Travel-mode variables: outpt_walk, inp_walk, outpt_homevisit.
# Distance variables: outpt_dist_single_unc, inp_dist_single_unc.
# Travel-mode variables: outpt_walk, inp_walk, outpt_homevisit.


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd

# =============================================================================
# Original notebook comment normalized for the public code archive.
# CHARLS processing note.
BASE = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health")

FILE = BASE / "Health_investment_with_Access_panel_2011_2020_citycode.xlsx"

print("[INFO] Notebook progress message.", FILE)

if not FILE.exists():
    raise FileNotFoundError(f"找不到文件：{FILE}\n请检查路径或文件名是否正确。")

# =============================================================================
xls = pd.ExcelFile(FILE)
print("[INFO] Notebook progress message.")
for i, sh in enumerate(xls.sheet_names, start=1):
    print(f"  {i}. {sh}")

# =============================================================================
for sheet_name in xls.sheet_names:
    print("\n" + "="*80)
    print("[INFO] Notebook progress message.")
    print("="*80)

    df = xls.parse(sheet_name)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    print(df.info())

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    print(df.columns.tolist())

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    print(df.head(10))

    # Original notebook comment normalized for the public code archive.
    for cand in ["year", "YEAR", "Year", "wave"]:
        if cand in df.columns:
            print("[INFO] Notebook progress message.")
            print(df[cand].value_counts().sort_index())
            break

    # City-level processing note.
    for cand in ["city_code", "citycode", "city", "city_id"]:
        if cand in df.columns:
            print("[INFO] Notebook progress message.", df[cand].nunique())
            print("[INFO] Notebook progress message.", df[cand].dropna().unique()[:20])
            break

print("[INFO] Notebook progress message.")
