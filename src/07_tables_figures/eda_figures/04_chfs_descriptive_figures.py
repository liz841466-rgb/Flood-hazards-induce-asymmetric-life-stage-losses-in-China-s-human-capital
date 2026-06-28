#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from __future__ import annotations
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
CHFS_XLSX = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/CHFS/CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_XLSX  = Path("./CHFS_pre_regression_diagnostics_tables.xlsx")

# =============================================================================
VALID_EDU_YEARS = [2010, 2012, 2014]   # Original notebook comment normalized for the public code archive.

# =============================================================================
DO_FLOOD_MERGE = False
FLOOD_CSV = Path("/home/ll/jupyter_notebook/result/county_storage_return_events/county_flood_events_T10_20_50_100_1980_2015.csv")
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOWS = [1, 2, 3, 4, 5]  # Original notebook comment normalized for the public code archive.


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def mean_ci(x: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = int(x.shape[0])
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, ci_low=np.nan, ci_high=np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else np.nan
    return dict(n=n, mean=m, sd=sd, ci_low=m - z * se, ci_high=m + z * se)

def diff_means_ci(x_u: pd.Series, x_r: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    u = pd.to_numeric(x_u, errors="coerce").dropna()
    r = pd.to_numeric(x_r, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu == 0 or nr == 0:
        return dict(diff=np.nan, ci_low=np.nan, ci_high=np.nan, n_u=nu, n_r=nr)

    mu, mr = float(u.mean()), float(r.mean())
    sdu = float(u.std(ddof=1)) if nu > 1 else 0.0
    sdr = float(r.std(ddof=1)) if nr > 1 else 0.0

    diff = mu - mr
    se = np.sqrt((sdu**2) / nu + (sdr**2) / nr)
    return dict(diff=diff, ci_low=diff - z * se, ci_high=diff + z * se, n_u=nu, n_r=nr)

def quantile_summary(x: pd.Series):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if x.empty:
        return dict(N=0, mean=np.nan, sd=np.nan, min=np.nan, p25=np.nan, median=np.nan, p75=np.nan, max=np.nan)
    return dict(
        N=int(x.shape[0]),
        mean=float(x.mean()),
        sd=float(x.std(ddof=1)) if x.shape[0] > 1 else 0.0,
        min=float(x.min()),
        p25=float(x.quantile(0.25)),
        median=float(x.quantile(0.50)),
        p75=float(x.quantile(0.75)),
        max=float(x.max()),
    )


# =========================
# CHFS/CFHS processing note.
# =========================
def load_chfs_panel(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    need_cols = [
        "家庭ID", "来源年份", "county_code",
        "是否农村", "是否有15岁及以下儿童", "15岁及以下儿童数量",
        "家庭可支配收入（元）", "去年教育培训支出（元）",
        "是否有教育负债（原始码1/2）",
        "教育负债余额（元）",  # Original notebook comment normalized for the public code archive.
        "教育培训支出口径年份", "收入口径年份",
    ]

    # Original notebook comment normalized for the public code archive.
    df = ensure_numeric(df, [
        "来源年份", "county_code", "是否农村",
        "是否有15岁及以下儿童", "15岁及以下儿童数量",
        "家庭可支配收入（元）", "去年教育培训支出（元）",
        "是否有教育负债（原始码1/2）",
        "教育负债余额（元）",
        "教育培训支出口径年份", "收入口径年份",
    ])

    # wave / id / rural
    if "家庭ID" not in df.columns:
        raise KeyError("CHFS 表缺少『家庭ID』列。")
    if "来源年份" not in df.columns:
        raise KeyError("CHFS 表缺少『来源年份』列。")
    if "county_code" not in df.columns:
        raise KeyError("CHFS 表缺少『county_code』列。")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # Original notebook comment normalized for the public code archive.
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # Original notebook comment normalized for the public code archive.
    df["has_u15_child"] = np.where(pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce") == 1, 1,
                           np.where(pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce") == 0, 0, np.nan))
    df["n_u15_child"] = pd.to_numeric(df.get("15岁及以下儿童数量"), errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce")
    df["income"] = df["income"].clip(lower=0)
    df["log_income"] = np.log1p(df["income"])

    # Original notebook comment normalized for the public code archive.
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce")
    df["edu_train_total"] = df["edu_train_total"].clip(lower=0)
    df["ln_edu_train_total"] = np.log1p(df["edu_train_total"])
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    # Original notebook comment normalized for the public code archive.
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1,
                          np.where(raw_debt == 2, 0, np.nan))

    # Original notebook comment normalized for the public code archive.
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
        df["ln_edu_debt_balance"] = np.log1p(df["edu_debt_balance"])
    else:
        df["edu_debt_balance"] = np.nan
        df["ln_edu_debt_balance"] = np.nan

    # Original notebook comment normalized for the public code archive.
    if "教育培训支出口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["教育培训支出口径年份"], errors="coerce")
    else:
        df["edu_year"] = np.nan
    if "收入口径年份" in df.columns:
        df["edu_year"] = df["edu_year"].fillna(pd.to_numeric(df["收入口径年份"], errors="coerce"))
    df["edu_year"] = safe_int64(df["edu_year"])

    # CHARLS processing note.
    df["n_u15_child"] = pd.to_numeric(df["n_u15_child"], errors="coerce")
    df["n_u15_child_fill0"] = df["n_u15_child"].fillna(0)
    df["log_childnum"] = np.log1p(df["n_u15_child_fill0"].clip(lower=0))

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["wave", "家庭ID"]).copy()

    return df


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def group_flag(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    g = pd.Series("all", index=df.index, dtype="object")
    g.loc[df["is_rural"] == 1] = "rural"
    g.loc[df["is_rural"] == 0] = "urban"
    # Original notebook comment normalized for the public code archive.
    return g

def count_rows_and_households(df: pd.DataFrame) -> dict:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return dict(
        n_rows=int(df.shape[0]),
        n_hh=int(df["家庭ID"].nunique(dropna=True))
    )

def make_sample_construction(df0: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    steps = []

    def add_step(step_name, dfx):
        # Original notebook comment normalized for the public code archive.
        out = {"step": step_name}
        # Original notebook comment normalized for the public code archive.
        out.update({f"all_{k}": v for k, v in count_rows_and_households(dfx).items()})

        d_r = dfx[dfx["is_rural"] == 1]
        d_u = dfx[dfx["is_rural"] == 0]
        out.update({f"rural_{k}": v for k, v in count_rows_and_households(d_r).items()})
        out.update({f"urban_{k}": v for k, v in count_rows_and_households(d_u).items()})
        steps.append(out)

    # Original notebook comment normalized for the public code archive.
    add_step("Start: CHFS family-year panel (raw)", df0)

    # County-level processing note.
    d1 = df0.dropna(subset=["county_code"])
    add_step("Require non-missing county_code", d1)

    # Original notebook comment normalized for the public code archive.
    d2 = d1.dropna(subset=["edu_year"])
    add_step("Require non-missing edu_year", d2)

    # Original notebook comment normalized for the public code archive.
    if VALID_EDU_YEARS is not None:
        d3 = d2[d2["edu_year"].isin(VALID_EDU_YEARS)].copy()
        add_step(f"Restrict to edu_year in {VALID_EDU_YEARS}", d3)
    else:
        d3 = d2

    # Original notebook comment normalized for the public code archive.
    d4 = d3[pd.to_numeric(d3["has_u15_child"], errors="coerce") == 1].copy()
    add_step("Mechanism core sample: has_u15_child==1", d4)

    # Original notebook comment normalized for the public code archive.
    need_spend = ["has_edu_spend", "log_income", "log_childnum", "county_code", "edu_year"]
    d5a = d4.dropna(subset=need_spend).copy()
    add_step("Spending (extensive): + non-missing {has_edu_spend, log_income, log_childnum, county_code, edu_year}", d5a)

    # Original notebook comment normalized for the public code archive.
    d5b = d5a[pd.to_numeric(d5a["edu_train_total"], errors="coerce") > 0].copy()
    add_step("Spending (intensive): + edu_train_total>0", d5b)

    # Original notebook comment normalized for the public code archive.
    need_debt = ["has_edu_debt", "log_income", "log_childnum", "county_code", "edu_year"]
    d6a = d4.dropna(subset=need_debt).copy()
    add_step("Debt (extensive): + non-missing {has_edu_debt(1/0), log_income, log_childnum, county_code, edu_year}", d6a)

    # Original notebook comment normalized for the public code archive.
    if "edu_debt_balance" in d6a.columns:
        d6b = d6a[pd.to_numeric(d6a["edu_debt_balance"], errors="coerce") > 0].copy()
    else:
        d6b = d6a.iloc[0:0].copy()
    add_step("Debt (intensive): + edu_debt_balance>0", d6b)

    return pd.DataFrame(steps)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def make_wave_households(df_base: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    d = df_base.copy()
    d = d.dropna(subset=["wave", "家庭ID"])
    d = d.sort_values(["wave", "家庭ID"])

    waves = sorted([int(x) for x in d["wave"].dropna().unique().tolist()])
    rows = []
    prev_set = set()

    for w in waves:
        s = set(d.loc[d["wave"] == w, "家庭ID"].dropna().astype(str).unique().tolist())
        n_unique = len(s)
        n_new = len(s - prev_set) if prev_set else n_unique
        rows.append({"wave": w, "unique_households": n_unique, "new_households_vs_prev": n_new})
        prev_set = prev_set.union(s)

    return pd.DataFrame(rows)


# =========================
# Fixed-effects regression helper.
# =========================
def make_fe_unit_sizes(df_mech: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_rows = []

    def add_block(tag, dfx):
        # county cluster size
        g1 = dfx.groupby("county_code").size()
        s1 = quantile_summary(g1)

        # county×edu_year cell size
        g2 = dfx.groupby(["county_code", "edu_year"]).size()
        s2 = quantile_summary(g2)

        # Original notebook comment normalized for the public code archive.
        g3 = dfx.groupby("county_code")["edu_year"].nunique(dropna=True)
        s3 = quantile_summary(g3)
        n_county_ge2 = int((g3 >= 2).sum()) if not g3.empty else 0

        out_rows.append({
            "group": tag,
            "N_rows": int(dfx.shape[0]),
            "N_counties": int(dfx["county_code"].nunique(dropna=True)),
            "N_county_year_cells": int(g2.shape[0]),
            "county_cluster_size_summary": s1,
            "county_year_cell_size_summary": s2,
            "n_edu_years_per_county_summary": s3,
            "N_counties_with_>=2_edu_years": n_county_ge2,
        })

    # all / rural / urban
    add_block("all", df_mech)
    add_block("rural", df_mech[df_mech["is_rural"] == 1])
    add_block("urban", df_mech[df_mech["is_rural"] == 0])

    # Original notebook comment normalized for the public code archive.
    rows2 = []
    for r in out_rows:
        base = {k: v for k, v in r.items() if not k.endswith("_summary")}
        # Original notebook comment normalized for the public code archive.
        for name in ["county_cluster_size", "county_year_cell_size", "n_edu_years_per_county"]:
            summ = r[f"{name}_summary"]
            for kk, vv in summ.items():
                base[f"{name}_{kk}"] = vv
        rows2.append(base)

    return pd.DataFrame(rows2)


# =========================
# CHARLS processing note.
# =========================
def make_mech_summary_charls_style(df_mech_core: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_mech_core.copy()

    # Original notebook comment normalized for the public code archive.
    var_specs = [
        ("has_edu_spend", "Education training spending (extensive): 1(edu_train_total>0)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("ln_edu_train_total", "ln(1 + edu_train_total)"),
        ("has_edu_debt", "Education-related debt (extensive): 1(has debt)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("ln_edu_debt_balance", "ln(1 + edu_debt_balance)"),
        ("income", "Household disposable income (RMB)"),
        ("log_income", "ln(1 + income)"),
        ("n_u15_child", "Number of children aged <=15"),
        ("log_childnum", "ln(1 + #children<=15)"),
    ]

    rows = []
    d_r = d[d["is_rural"] == 1].copy()
    d_u = d[d["is_rural"] == 0].copy()

    for var, label in var_specs:
        if var not in d.columns:
            continue

        # all
        s_all = mean_ci(d[var])
        # rural / urban
        s_r = mean_ci(d_r[var])
        s_u = mean_ci(d_u[var])
        # diff: urban - rural
        s_diff = diff_means_ci(d_u[var], d_r[var])

        rows.append({
            "variable": var,
            "label": label,

            "all_n": s_all["n"],
            "all_mean": s_all["mean"],
            "all_ci_low": s_all["ci_low"],
            "all_ci_high": s_all["ci_high"],

            "rural_n": s_r["n"],
            "rural_mean": s_r["mean"],
            "rural_ci_low": s_r["ci_low"],
            "rural_ci_high": s_r["ci_high"],

            "urban_n": s_u["n"],
            "urban_mean": s_u["mean"],
            "urban_ci_low": s_u["ci_low"],
            "urban_ci_high": s_u["ci_high"],

            "urban_minus_rural": s_diff["diff"],
            "diff_ci_low": s_diff["ci_low"],
            "diff_ci_high": s_diff["ci_high"],
        })

    out = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    extra = []
    if "edu_train_total" in d.columns:
        extra.append({
            "variable": "N(edu_train_total>0)",
            "label": "Availability for intensive margin: edu_train_total>0",
            "all_n": int((pd.to_numeric(d["edu_train_total"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_train_total"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_train_total"], errors="coerce") > 0).sum()),
        })
    if "edu_debt_balance" in d.columns:
        extra.append({
            "variable": "N(edu_debt_balance>0)",
            "label": "Availability for intensive margin: edu_debt_balance>0",
            "all_n": int((pd.to_numeric(d["edu_debt_balance"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_debt_balance"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_debt_balance"], errors="coerce") > 0).sum()),
        })
    if extra:
        out = pd.concat([out, pd.DataFrame(extra)], ignore_index=True)

    return out


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_flood_panel(flood_csv: Path):
    df = pd.read_csv(flood_csv)
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
        df = df.rename(columns={"county_id": "county_code"})
        county_col = "county_code"
    else:
        raise ValueError("洪水文件中找不到 county_code/county_id。")

    df["county_code"] = safe_int64(df["county_code"])
    df["year"] = safe_int64(df["year"])

    for t in T_LIST:
        c = f"flood_ge_T{t}"
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=["county_code", "year"]).copy()
    return df

def build_flood_windows(df_flood: pd.DataFrame, k_list):
    df = df_flood.sort_values(["county_code", "year"]).copy()
    for k in k_list:
        for t in T_LIST:
            base = f"flood_ge_T{t}"
            share = f"share_flood_ge_T{t}_{k}y"
            df[share] = (
                df.groupby("county_code")[base]
                  .rolling(window=k, min_periods=1)
                  .mean()
                  .reset_index(level=0, drop=True)
            )
    return df

def merge_exposure(df_chfs: pd.DataFrame, df_flood_win: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    flood_sub = df_flood_win.rename(columns={"year": "edu_year"}).copy()
    keep_cols = ["county_code", "edu_year"] + [c for c in flood_sub.columns if c.startswith("share_flood_ge_T")]
    flood_sub = flood_sub[keep_cols].copy()

    out = df_chfs.merge(flood_sub, on=["county_code", "edu_year"], how="left", validate="m:1")

    # Original notebook comment normalized for the public code archive.
    share_cols = [c for c in out.columns if c.startswith("share_flood_ge_T")]
    for c in share_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)

    return out

def exposure_summary_table(df_mech: pd.DataFrame) -> pd.DataFrame:
    rows = []
    share_cols = [c for c in df_mech.columns if c.startswith("share_flood_ge_T")]
    if not share_cols:
        return pd.DataFrame()

    for c in share_cols:
        x = pd.to_numeric(df_mech[c], errors="coerce")
        rows.append({
            "exposure": c,
            "N": int(x.notna().sum()),
            "mean": float(x.mean(skipna=True)),
            "sd": float(x.std(skipna=True, ddof=1)) if int(x.notna().sum()) > 1 else 0.0,
            "p25": float(x.quantile(0.25)),
            "median": float(x.quantile(0.50)),
            "p75": float(x.quantile(0.75)),
            "share_nonzero": float((x > 0).mean(skipna=True)),
            "min": float(x.min(skipna=True)),
            "max": float(x.max(skipna=True)),
        })

    return pd.DataFrame(rows).sort_values("exposure").reset_index(drop=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def main():
    print(f"[INFO] Reading CHFS panel: {CHFS_XLSX}")
    df0 = load_chfs_panel(CHFS_XLSX)
    print("[INFO] Notebook progress message.")

    # County-level processing note.
    df_core = df0.dropna(subset=["county_code", "edu_year"]).copy()
    if VALID_EDU_YEARS is not None:
        df_core = df_core[df_core["edu_year"].isin(VALID_EDU_YEARS)].copy()
    df_core = df_core[pd.to_numeric(df_core["has_u15_child"], errors="coerce") == 1].copy()

    # Original notebook comment normalized for the public code archive.
    exposure_tbl = pd.DataFrame()
    if DO_FLOOD_MERGE:
        print(f"[INFO] Reading flood panel: {FLOOD_CSV}")
        f0 = load_flood_panel(FLOOD_CSV)
        fwin = build_flood_windows(f0, K_WINDOWS)
        df_core = merge_exposure(df_core, fwin)
        exposure_tbl = exposure_summary_table(df_core)

    # Original notebook comment normalized for the public code archive.
    sample_tbl = make_sample_construction(df0)

    # Original notebook comment normalized for the public code archive.
    wave_hh_tbl = make_wave_households(df_core)

    # Fixed-effects regression helper.
    fe_tbl = make_fe_unit_sizes(df_core)

    # Original notebook comment normalized for the public code archive.
    mech_tbl = make_mech_summary_charls_style(df_core)

    # Original notebook comment normalized for the public code archive.
    def wave_dist(dfx, tag):
        g = dfx.groupby("wave").agg(
            n_rows=("家庭ID", "size"),
            n_hh=("家庭ID", pd.Series.nunique),
        ).reset_index()
        g["group"] = tag
        return g

    wave_dist_tbl = pd.concat([
        wave_dist(df_core, "all"),
        wave_dist(df_core[df_core["is_rural"] == 1], "rural"),
        wave_dist(df_core[df_core["is_rural"] == 0], "urban"),
    ], ignore_index=True).sort_values(["group", "wave"])

    # Excel output note.
    print(f"[INFO] Writing tables to: {OUT_XLSX}")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        sample_tbl.to_excel(writer, sheet_name="sample_construction", index=False)
        wave_hh_tbl.to_excel(writer, sheet_name="wave_households", index=False)
        fe_tbl.to_excel(writer, sheet_name="fe_unit_sizes", index=False)
        mech_tbl.to_excel(writer, sheet_name="mech_summary_charls_style", index=False)
        wave_dist_tbl.to_excel(writer, sheet_name="wave_distribution_core", index=False)
        if DO_FLOOD_MERGE and not exposure_tbl.empty:
            exposure_tbl.to_excel(writer, sheet_name="exposure_summary", index=False)

    print("[DONE] Pre-regression diagnostics tables exported.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
CHFS_XLSX = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/CHFS/CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")

# Original notebook comment normalized for the public code archive.
OUT_DIR  = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/CHFS")
OUT_XLSX = OUT_DIR / "CHFS_pre_regression_diagnostics_tables.xlsx"

# =============================================================================
VALID_EDU_YEARS = [2010, 2012, 2014]   # Original notebook comment normalized for the public code archive.

# =============================================================================
DO_FLOOD_MERGE = False
FLOOD_CSV = Path(r"/home/ll/jupyter_notebook/result/county_storage_return_events/county_flood_events_T10_20_50_100_1980_2015.csv")
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOWS = [1, 2, 3, 4, 5]  # Original notebook comment normalized for the public code archive.


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def mean_ci(x: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = int(x.shape[0])
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, ci_low=np.nan, ci_high=np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else np.nan
    return dict(n=n, mean=m, sd=sd, ci_low=m - z * se, ci_high=m + z * se)

def diff_means_ci(x_u: pd.Series, x_r: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    u = pd.to_numeric(x_u, errors="coerce").dropna()
    r = pd.to_numeric(x_r, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu == 0 or nr == 0:
        return dict(diff=np.nan, ci_low=np.nan, ci_high=np.nan, n_u=nu, n_r=nr)

    mu, mr = float(u.mean()), float(r.mean())
    sdu = float(u.std(ddof=1)) if nu > 1 else 0.0
    sdr = float(r.std(ddof=1)) if nr > 1 else 0.0

    diff = mu - mr
    se = np.sqrt((sdu**2) / nu + (sdr**2) / nr)
    return dict(diff=diff, ci_low=diff - z * se, ci_high=diff + z * se, n_u=nu, n_r=nr)

def quantile_summary(x: pd.Series):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if x.empty:
        return dict(N=0, mean=np.nan, sd=np.nan, min=np.nan, p25=np.nan, median=np.nan, p75=np.nan, max=np.nan)
    return dict(
        N=int(x.shape[0]),
        mean=float(x.mean()),
        sd=float(x.std(ddof=1)) if x.shape[0] > 1 else 0.0,
        min=float(x.min()),
        p25=float(x.quantile(0.25)),
        median=float(x.quantile(0.50)),
        p75=float(x.quantile(0.75)),
        max=float(x.max()),
    )


# =========================
# CHFS/CFHS processing note.
# =========================
def load_chfs_panel(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    need_cols = [
        "家庭ID", "来源年份", "county_code",
        "是否农村", "是否有15岁及以下儿童", "15岁及以下儿童数量",
        "家庭可支配收入（元）", "去年教育培训支出（元）",
        "是否有教育负债（原始码1/2）",
        "教育负债余额（元）",  # Original notebook comment normalized for the public code archive.
        "教育培训支出口径年份", "收入口径年份",
    ]

    df = ensure_numeric(df, [
        "来源年份", "county_code", "是否农村",
        "是否有15岁及以下儿童", "15岁及以下儿童数量",
        "家庭可支配收入（元）", "去年教育培训支出（元）",
        "是否有教育负债（原始码1/2）",
        "教育负债余额（元）",
        "教育培训支出口径年份", "收入口径年份",
    ])

    if "家庭ID" not in df.columns:
        raise KeyError("CHFS 表缺少『家庭ID』列。")
    if "来源年份" not in df.columns:
        raise KeyError("CHFS 表缺少『来源年份』列。")
    if "county_code" not in df.columns:
        raise KeyError("CHFS 表缺少『county_code』列。")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # Original notebook comment normalized for the public code archive.
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # Original notebook comment normalized for the public code archive.
    df["has_u15_child"] = np.where(pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce") == 1, 1,
                           np.where(pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce") == 0, 0, np.nan))
    df["n_u15_child"] = pd.to_numeric(df.get("15岁及以下儿童数量"), errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce")
    df["income"] = df["income"].clip(lower=0)
    df["log_income"] = np.log1p(df["income"])

    # Original notebook comment normalized for the public code archive.
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce")
    df["edu_train_total"] = df["edu_train_total"].clip(lower=0)
    df["ln_edu_train_total"] = np.log1p(df["edu_train_total"])
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    # Original notebook comment normalized for the public code archive.
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1,
                          np.where(raw_debt == 2, 0, np.nan))

    # Original notebook comment normalized for the public code archive.
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
        df["ln_edu_debt_balance"] = np.log1p(df["edu_debt_balance"])
    else:
        df["edu_debt_balance"] = np.nan
        df["ln_edu_debt_balance"] = np.nan

    # Original notebook comment normalized for the public code archive.
    if "教育培训支出口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["教育培训支出口径年份"], errors="coerce")
    else:
        df["edu_year"] = np.nan
    if "收入口径年份" in df.columns:
        df["edu_year"] = df["edu_year"].fillna(pd.to_numeric(df["收入口径年份"], errors="coerce"))
    df["edu_year"] = safe_int64(df["edu_year"])

    # Original notebook comment normalized for the public code archive.
    df["n_u15_child"] = pd.to_numeric(df["n_u15_child"], errors="coerce")
    df["n_u15_child_fill0"] = df["n_u15_child"].fillna(0)
    df["log_childnum"] = np.log1p(df["n_u15_child_fill0"].clip(lower=0))

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["wave", "家庭ID"]).copy()

    return df


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def count_rows_and_households(df: pd.DataFrame) -> dict:
    return dict(
        n_rows=int(df.shape[0]),
        n_hh=int(df["家庭ID"].nunique(dropna=True))
    )

def make_sample_construction(df_base: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    steps = []

    def add_step(step_name, dfx):
        out = {"step": step_name}
        out.update({f"all_{k}": v for k, v in count_rows_and_households(dfx).items()})

        d_r = dfx[dfx["is_rural"] == 1]
        d_u = dfx[dfx["is_rural"] == 0]
        out.update({f"rural_{k}": v for k, v in count_rows_and_households(d_r).items()})
        out.update({f"urban_{k}": v for k, v in count_rows_and_households(d_u).items()})
        steps.append(out)

    # Original notebook comment normalized for the public code archive.
    add_step("Base: non-missing county_code & edu_year", df_base)

    # Original notebook comment normalized for the public code archive.
    if VALID_EDU_YEARS is not None:
        d1 = df_base[df_base["edu_year"].isin(VALID_EDU_YEARS)].copy()
        add_step(f"Restrict to edu_year in {VALID_EDU_YEARS}", d1)
    else:
        d1 = df_base

    # Original notebook comment normalized for the public code archive.
    d2 = d1[pd.to_numeric(d1["has_u15_child"], errors="coerce") == 1].copy()
    add_step("Mechanism core sample: has_u15_child==1", d2)

    # Original notebook comment normalized for the public code archive.
    need_spend = ["has_edu_spend", "log_income", "log_childnum", "county_code", "edu_year"]
    d3a = d2.dropna(subset=need_spend).copy()
    add_step("Spending (extensive): + non-missing {has_edu_spend, log_income, log_childnum, county_code, edu_year}", d3a)

    # Original notebook comment normalized for the public code archive.
    d3b = d3a[pd.to_numeric(d3a["edu_train_total"], errors="coerce") > 0].copy()
    add_step("Spending (intensive): + edu_train_total>0", d3b)

    # Original notebook comment normalized for the public code archive.
    need_debt = ["has_edu_debt", "log_income", "log_childnum", "county_code", "edu_year"]
    d4a = d2.dropna(subset=need_debt).copy()
    add_step("Debt (extensive): + non-missing {has_edu_debt(1/0), log_income, log_childnum, county_code, edu_year}", d4a)

    # Original notebook comment normalized for the public code archive.
    if "edu_debt_balance" in d4a.columns:
        d4b = d4a[pd.to_numeric(d4a["edu_debt_balance"], errors="coerce") > 0].copy()
    else:
        d4b = d4a.iloc[0:0].copy()
    add_step("Debt (intensive): + edu_debt_balance>0", d4b)

    return pd.DataFrame(steps)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def make_wave_households(df_base: pd.DataFrame) -> pd.DataFrame:
    d = df_base.copy()
    d = d.dropna(subset=["wave", "家庭ID"])
    d = d.sort_values(["wave", "家庭ID"])

    waves = sorted([int(x) for x in d["wave"].dropna().unique().tolist()])
    rows = []
    prev_set = set()

    for w in waves:
        s = set(d.loc[d["wave"] == w, "家庭ID"].dropna().astype(str).unique().tolist())
        n_unique = len(s)
        n_new = len(s - prev_set) if prev_set else n_unique
        rows.append({"wave": w, "unique_households": n_unique, "new_households_vs_prev": n_new})
        prev_set = prev_set.union(s)

    return pd.DataFrame(rows)


# =========================
# Fixed-effects regression helper.
# =========================
def make_fe_unit_sizes(df_mech: pd.DataFrame) -> pd.DataFrame:
    out_rows = []

    def add_block(tag, dfx):
        g1 = dfx.groupby("county_code").size()
        s1 = quantile_summary(g1)

        g2 = dfx.groupby(["county_code", "edu_year"]).size()
        s2 = quantile_summary(g2)

        g3 = dfx.groupby("county_code")["edu_year"].nunique(dropna=True)
        s3 = quantile_summary(g3)
        n_county_ge2 = int((g3 >= 2).sum()) if not g3.empty else 0

        out_rows.append({
            "group": tag,
            "N_rows": int(dfx.shape[0]),
            "N_counties": int(dfx["county_code"].nunique(dropna=True)),
            "N_county_year_cells": int(g2.shape[0]),
            "county_cluster_size_summary": s1,
            "county_year_cell_size_summary": s2,
            "n_edu_years_per_county_summary": s3,
            "N_counties_with_>=2_edu_years": n_county_ge2,
        })

    add_block("all", df_mech)
    add_block("rural", df_mech[df_mech["is_rural"] == 1])
    add_block("urban", df_mech[df_mech["is_rural"] == 0])

    rows2 = []
    for r in out_rows:
        base = {k: v for k, v in r.items() if not k.endswith("_summary")}
        for name in ["county_cluster_size", "county_year_cell_size", "n_edu_years_per_county"]:
            summ = r[f"{name}_summary"]
            for kk, vv in summ.items():
                base[f"{name}_{kk}"] = vv
        rows2.append(base)

    return pd.DataFrame(rows2)


# =========================
# CHARLS processing note.
# =========================
def make_mech_summary_charls_style(df_mech_core: pd.DataFrame) -> pd.DataFrame:
    d = df_mech_core.copy()

    var_specs = [
        ("has_edu_spend", "Education training spending (extensive): 1(edu_train_total>0)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("ln_edu_train_total", "ln(1 + edu_train_total)"),
        ("has_edu_debt", "Education-related debt (extensive): 1(has debt)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("ln_edu_debt_balance", "ln(1 + edu_debt_balance)"),
        ("income", "Household disposable income (RMB)"),
        ("log_income", "ln(1 + income)"),
        ("n_u15_child", "Number of children aged <=15"),
        ("log_childnum", "ln(1 + #children<=15)"),
    ]

    rows = []
    d_r = d[d["is_rural"] == 1].copy()
    d_u = d[d["is_rural"] == 0].copy()

    for var, label in var_specs:
        if var not in d.columns:
            continue

        s_all = mean_ci(d[var])
        s_r = mean_ci(d_r[var])
        s_u = mean_ci(d_u[var])
        s_diff = diff_means_ci(d_u[var], d_r[var])

        rows.append({
            "variable": var,
            "label": label,

            "all_n": s_all["n"],
            "all_mean": s_all["mean"],
            "all_ci_low": s_all["ci_low"],
            "all_ci_high": s_all["ci_high"],

            "rural_n": s_r["n"],
            "rural_mean": s_r["mean"],
            "rural_ci_low": s_r["ci_low"],
            "rural_ci_high": s_r["ci_high"],

            "urban_n": s_u["n"],
            "urban_mean": s_u["mean"],
            "urban_ci_low": s_u["ci_low"],
            "urban_ci_high": s_u["ci_high"],

            "urban_minus_rural": s_diff["diff"],
            "diff_ci_low": s_diff["ci_low"],
            "diff_ci_high": s_diff["ci_high"],
        })

    out = pd.DataFrame(rows)

    extra = []
    if "edu_train_total" in d.columns:
        extra.append({
            "variable": "N(edu_train_total>0)",
            "label": "Availability for intensive margin: edu_train_total>0",
            "all_n": int((pd.to_numeric(d["edu_train_total"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_train_total"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_train_total"], errors="coerce") > 0).sum()),
        })
    if "edu_debt_balance" in d.columns:
        extra.append({
            "variable": "N(edu_debt_balance>0)",
            "label": "Availability for intensive margin: edu_debt_balance>0",
            "all_n": int((pd.to_numeric(d["edu_debt_balance"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_debt_balance"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_debt_balance"], errors="coerce") > 0).sum()),
        })
    if extra:
        out = pd.concat([out, pd.DataFrame(extra)], ignore_index=True)

    return out


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_flood_panel(flood_csv: Path):
    df = pd.read_csv(flood_csv)
    if "county_code" in df.columns:
        pass
    elif "county_id" in df.columns:
        df = df.rename(columns={"county_id": "county_code"})
    else:
        raise ValueError("洪水文件中找不到 county_code/county_id。")

    df["county_code"] = safe_int64(df["county_code"])
    df["year"] = safe_int64(df["year"])

    for t in T_LIST:
        c = f"flood_ge_T{t}"
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=["county_code", "year"]).copy()
    return df

def build_flood_windows(df_flood: pd.DataFrame, k_list):
    df = df_flood.sort_values(["county_code", "year"]).copy()
    for k in k_list:
        for t in T_LIST:
            base = f"flood_ge_T{t}"
            share = f"share_flood_ge_T{t}_{k}y"
            df[share] = (
                df.groupby("county_code")[base]
                  .rolling(window=k, min_periods=1)
                  .mean()
                  .reset_index(level=0, drop=True)
            )
    return df

def merge_exposure(df_chfs: pd.DataFrame, df_flood_win: pd.DataFrame):
    flood_sub = df_flood_win.rename(columns={"year": "edu_year"}).copy()
    keep_cols = ["county_code", "edu_year"] + [c for c in flood_sub.columns if c.startswith("share_flood_ge_T")]
    flood_sub = flood_sub[keep_cols].copy()

    out = df_chfs.merge(flood_sub, on=["county_code", "edu_year"], how="left", validate="m:1")

    share_cols = [c for c in out.columns if c.startswith("share_flood_ge_T")]
    for c in share_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)

    return out

def exposure_summary_table(df_mech: pd.DataFrame) -> pd.DataFrame:
    rows = []
    share_cols = [c for c in df_mech.columns if c.startswith("share_flood_ge_T")]
    if not share_cols:
        return pd.DataFrame()

    for c in share_cols:
        x = pd.to_numeric(df_mech[c], errors="coerce")
        rows.append({
            "exposure": c,
            "N": int(x.notna().sum()),
            "mean": float(x.mean(skipna=True)),
            "sd": float(x.std(skipna=True, ddof=1)) if int(x.notna().sum()) > 1 else 0.0,
            "p25": float(x.quantile(0.25)),
            "median": float(x.quantile(0.50)),
            "p75": float(x.quantile(0.75)),
            "share_nonzero": float((x > 0).mean(skipna=True)),
            "min": float(x.min(skipna=True)),
            "max": float(x.max(skipna=True)),
        })

    return pd.DataFrame(rows).sort_values("exposure").reset_index(drop=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def main():
    print(f"[INFO] Reading CHFS panel: {CHFS_XLSX}")
    df0 = load_chfs_panel(CHFS_XLSX)
    print("[INFO] Notebook progress message.")

    # County-level processing note.
    df_base = df0.dropna(subset=["county_code", "edu_year"]).copy()

    # Fixed-effects regression helper.
    df_core = df_base.copy()
    if VALID_EDU_YEARS is not None:
        df_core = df_core[df_core["edu_year"].isin(VALID_EDU_YEARS)].copy()
    df_core = df_core[pd.to_numeric(df_core["has_u15_child"], errors="coerce") == 1].copy()

    # Original notebook comment normalized for the public code archive.
    exposure_tbl = pd.DataFrame()
    if DO_FLOOD_MERGE:
        print(f"[INFO] Reading flood panel: {FLOOD_CSV}")
        f0 = load_flood_panel(FLOOD_CSV)
        fwin = build_flood_windows(f0, K_WINDOWS)
        df_core = merge_exposure(df_core, fwin)
        exposure_tbl = exposure_summary_table(df_core)

    # County-level processing note.
    sample_tbl = make_sample_construction(df_base)

    # Original notebook comment normalized for the public code archive.
    wave_hh_tbl = make_wave_households(df_core)

    # Fixed-effects regression helper.
    fe_tbl = make_fe_unit_sizes(df_core)

    # Original notebook comment normalized for the public code archive.
    mech_tbl = make_mech_summary_charls_style(df_core)

    # Original notebook comment normalized for the public code archive.
    def wave_dist(dfx, tag):
        g = dfx.groupby("wave").agg(
            n_rows=("家庭ID", "size"),
            n_hh=("家庭ID", pd.Series.nunique),
        ).reset_index()
        g["group"] = tag
        return g

    wave_dist_tbl = pd.concat([
        wave_dist(df_core, "all"),
        wave_dist(df_core[df_core["is_rural"] == 1], "rural"),
        wave_dist(df_core[df_core["is_rural"] == 0], "urban"),
    ], ignore_index=True).sort_values(["group", "wave"])

    # Original notebook comment normalized for the public code archive.
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Excel output note.
    print(f"[INFO] Writing tables to: {OUT_XLSX}")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        sample_tbl.to_excel(writer, sheet_name="sample_construction", index=False)
        wave_hh_tbl.to_excel(writer, sheet_name="wave_households", index=False)
        fe_tbl.to_excel(writer, sheet_name="fe_unit_sizes", index=False)
        mech_tbl.to_excel(writer, sheet_name="mech_summary_charls_style", index=False)
        wave_dist_tbl.to_excel(writer, sheet_name="wave_distribution_core", index=False)
        if DO_FLOOD_MERGE and not exposure_tbl.empty:
            exposure_tbl.to_excel(writer, sheet_name="exposure_summary", index=False)

    print("[DONE] Pre-regression diagnostics tables exported.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
CHFS_XLSX = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/CHFS/CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")

OUT_DIR  = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/CHFS")
FIG_DIR  = OUT_DIR / "figures"
OUT_XLSX = OUT_DIR / "CHFS_pre_regression_diagnostics_tables.xlsx"

# Original notebook comment normalized for the public code archive.
VALID_EDU_YEARS = [2010, 2012, 2014]

# =============================================================================
DO_FLOOD_MERGE = False
FLOOD_CSV = Path(r"/home/ll/jupyter_notebook/result/county_storage_return_events/county_flood_events_T10_20_50_100_1980_2015.csv")
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOWS = [1, 2, 3, 4, 5]


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def mean_ci(x: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = int(x.shape[0])
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, ci_low=np.nan, ci_high=np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else np.nan
    return dict(n=n, mean=m, sd=sd, ci_low=m - z * se, ci_high=m + z * se)

def diff_means_ci(x_u: pd.Series, x_r: pd.Series, z=1.96):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    u = pd.to_numeric(x_u, errors="coerce").dropna()
    r = pd.to_numeric(x_r, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu == 0 or nr == 0:
        return dict(diff=np.nan, ci_low=np.nan, ci_high=np.nan, n_u=nu, n_r=nr)

    mu, mr = float(u.mean()), float(r.mean())
    sdu = float(u.std(ddof=1)) if nu > 1 else 0.0
    sdr = float(r.std(ddof=1)) if nr > 1 else 0.0

    diff = mu - mr
    se = np.sqrt((sdu**2) / nu + (sdr**2) / nr)
    return dict(diff=diff, ci_low=diff - z * se, ci_high=diff + z * se, n_u=nu, n_r=nr)

def quantile_summary(x: pd.Series):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if x.empty:
        return dict(N=0, mean=np.nan, sd=np.nan, min=np.nan, p25=np.nan, median=np.nan, p75=np.nan, max=np.nan)
    return dict(
        N=int(x.shape[0]),
        mean=float(x.mean()),
        sd=float(x.std(ddof=1)) if x.shape[0] > 1 else 0.0,
        min=float(x.min()),
        p25=float(x.quantile(0.25)),
        median=float(x.quantile(0.50)),
        p75=float(x.quantile(0.75)),
        max=float(x.max()),
    )

def fmt_ci(low, high, digits=3):
    if pd.isna(low) or pd.isna(high):
        return ""
    return f"[{low:.{digits}f}, {high:.{digits}f}]"


# =========================
# CHFS/CFHS processing note.
# =========================
def load_chfs_panel(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(df, [
        "来源年份", "county_code", "是否农村",
        "是否有15岁及以下儿童", "15岁及以下儿童数量",
        "家庭可支配收入（元）", "去年教育培训支出（元）",
        "是否有教育负债（原始码1/2）",
        "教育负债余额（元）",
        "教育培训支出口径年份", "收入口径年份",
    ])

    for c in ["家庭ID", "来源年份", "county_code"]:
        if c not in df.columns:
            raise KeyError(f"CHFS 表缺少『{c}』列。")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # rural
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # children
    child_flag = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(child_flag == 1, 1, np.where(child_flag == 0, 0, np.nan))
    df["n_u15_child"] = pd.to_numeric(df.get("15岁及以下儿童数量"), errors="coerce")

    # income
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)
    df["log_income"] = np.log1p(df["income"])

    # edu spend
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["ln_edu_train_total"] = np.log1p(df["edu_train_total"])
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    # edu debt extensive (1/2 coding -> 1/0; others NA)
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))

    # debt balance
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
        df["ln_edu_debt_balance"] = np.log1p(df["edu_debt_balance"])
    else:
        df["edu_debt_balance"] = np.nan
        df["ln_edu_debt_balance"] = np.nan

    # edu_year: prefer spending-year then income-year
    if "教育培训支出口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["教育培训支出口径年份"], errors="coerce")
    else:
        df["edu_year"] = np.nan
    if "收入口径年份" in df.columns:
        df["edu_year"] = df["edu_year"].fillna(pd.to_numeric(df["收入口径年份"], errors="coerce"))
    df["edu_year"] = safe_int64(df["edu_year"])

    # child log
    df["n_u15_child_fill0"] = pd.to_numeric(df["n_u15_child"], errors="coerce").fillna(0).clip(lower=0)
    df["log_childnum"] = np.log1p(df["n_u15_child_fill0"])

    # keep key ids
    df = df.dropna(subset=["wave", "家庭ID"]).copy()
    return df


# =========================
# Excel output note.
# =========================
def _counts(df: pd.DataFrame):
    return int(df.shape[0]), int(df["家庭ID"].nunique(dropna=True))

def make_sample_construction(df_base: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    steps = []

    def add_step(step_label, dfx):
        all_obs, all_hh = _counts(dfx)
        r = dfx[dfx["is_rural"] == 1]
        u = dfx[dfx["is_rural"] == 0]
        r_obs, r_hh = _counts(r)
        u_obs, u_hh = _counts(u)

        steps.append({
            "Sample definition": step_label,
            "All: Observations (hh-year)": all_obs,
            "All: Unique households": all_hh,
            "Rural: Observations (hh-year)": r_obs,
            "Rural: Unique households": r_hh,
            "Urban: Observations (hh-year)": u_obs,
            "Urban: Unique households": u_hh,
        })

    add_step("Baseline panel: non-missing county_code & edu_year", df_base)

    if VALID_EDU_YEARS is not None:
        d1 = df_base[df_base["edu_year"].isin(VALID_EDU_YEARS)].copy()
        add_step(f"Restrict to edu_year ∈ {VALID_EDU_YEARS}", d1)
    else:
        d1 = df_base

    d2 = d1[pd.to_numeric(d1["has_u15_child"], errors="coerce") == 1].copy()
    add_step("Mechanism core sample: households with children aged ≤ 15", d2)

    # spending extensive / intensive
    need_spend = ["has_edu_spend", "log_income", "log_childnum", "county_code", "edu_year"]
    d3a = d2.dropna(subset=need_spend).copy()
    add_step("Spending (extensive): non-missing {has_edu_spend, controls, county_code, edu_year}", d3a)

    d3b = d3a[pd.to_numeric(d3a["edu_train_total"], errors="coerce") > 0].copy()
    add_step("Spending (intensive): edu_train_total > 0", d3b)

    # debt extensive / intensive
    need_debt = ["has_edu_debt", "log_income", "log_childnum", "county_code", "edu_year"]
    d4a = d2.dropna(subset=need_debt).copy()
    add_step("Debt (extensive): non-missing {has_edu_debt, controls, county_code, edu_year}", d4a)

    d4b = d4a[pd.to_numeric(d4a["edu_debt_balance"], errors="coerce") > 0].copy()
    add_step("Debt (intensive): edu_debt_balance > 0", d4b)

    return pd.DataFrame(steps)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def make_wave_households(df_core: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_core.dropna(subset=["wave", "家庭ID"]).copy()
    d = d.sort_values(["wave", "家庭ID"])
    waves = sorted([int(x) for x in d["wave"].dropna().unique().tolist()])

    rows = []
    prev_wave_set = set()
    for w in waves:
        cur_set = set(d.loc[d["wave"] == w, "家庭ID"].dropna().astype(str).unique().tolist())
        unique_hh = len(cur_set)
        new_vs_prev = len(cur_set - prev_wave_set) if prev_wave_set else unique_hh
        rows.append({
            "wave": w,
            "unique_households": unique_hh,
            "new_households_vs_prev_wave": new_vs_prev
        })
        prev_wave_set = cur_set

    return pd.DataFrame(rows)

def plot_wave_households_bar(wave_tbl: pd.DataFrame, out_png: Path, title: str):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if wave_tbl.empty:
        return
    x = wave_tbl["wave"].astype(int).tolist()
    y1 = wave_tbl["unique_households"].astype(float).tolist()
    y2 = wave_tbl["new_households_vs_prev_wave"].astype(float).tolist()

    pos = np.arange(len(x))
    width = 0.40

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(pos - width/2, y1, width, label="Unique households (per wave)")
    ax.bar(pos + width/2, y2, width, label="New households (vs previous wave)")
    ax.set_xticks(pos)
    ax.set_xticklabels([str(i) for i in x])
    ax.set_xlabel("Survey wave (year)")
    ax.set_ylabel("Number of households")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


# =========================
# Fixed-effects regression helper.
# =========================
def make_fe_distributions(df_core: pd.DataFrame, tag: str):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_core.copy()
    if tag == "rural":
        d = d[d["is_rural"] == 1]
    elif tag == "urban":
        d = d[d["is_rural"] == 0]

    s_county = d.groupby("county_code").size()
    s_cell = d.groupby(["county_code", "edu_year"]).size()
    s_years = d.groupby("county_code")["edu_year"].nunique(dropna=True)
    return s_county, s_cell, s_years

def make_fe_unit_sizes_summary(df_core: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tag in ["all", "rural", "urban"]:
        s_county, s_cell, s_years = make_fe_distributions(df_core, tag)
        sum_county = quantile_summary(s_county)
        sum_cell = quantile_summary(s_cell)
        sum_years = quantile_summary(s_years)

        if tag == "all":
            n_rows = int(df_core.shape[0])
        elif tag == "rural":
            n_rows = int(df_core[df_core["is_rural"] == 1].shape[0])
        else:
            n_rows = int(df_core[df_core["is_rural"] == 0].shape[0])

        rows.append({
            "group": tag,
            "N_rows": n_rows,
            "N_counties": int(s_county.shape[0]),
            "N_county_year_cells": int(s_cell.shape[0]),
            "N_counties_with_>=2_edu_years": int((s_years >= 2).sum()) if not s_years.empty else 0,
            **{f"county_cluster_{k}": v for k, v in sum_county.items()},
            **{f"county_year_cell_{k}": v for k, v in sum_cell.items()},
            **{f"n_edu_years_per_county_{k}": v for k, v in sum_years.items()},
        })
    return pd.DataFrame(rows)

def plot_fe_boxplots(df_core: pd.DataFrame, out_dir: Path):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    metrics = [
        ("fe_boxplot_county_cluster_size.png", "Observations per county (cluster size)", 0),
        ("fe_boxplot_county_year_cell_size.png", "Observations per county×edu_year cell", 1),
        ("fe_boxplot_n_edu_years_per_county.png", "Number of edu_years per county (within-variation proxy)", 2),
    ]

    data_all = make_fe_distributions(df_core, "all")
    data_r = make_fe_distributions(df_core, "rural")
    data_u = make_fe_distributions(df_core, "urban")

    for fname, title, idx in metrics:
        sA, sR, sU = data_all[idx], data_r[idx], data_u[idx]

        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        ax.boxplot(
            [sA.dropna().values, sR.dropna().values, sU.dropna().values],
            tick_labels=["All", "Rural", "Urban"],   # Original notebook comment normalized for the public code archive.
            showfliers=True
        )
        ax.set_title(title)
        ax.set_ylabel("Count")
        fig.tight_layout()
        fig.savefig(out_dir / fname, dpi=200)
        plt.close(fig)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
KEEP_ROWS = [
    "N(edu_train_total>0)",
    "has_edu_spend",
    "edu_train_total",
    "N(edu_debt_balance>0)",
    "has_edu_debt",
    "edu_debt_balance",
    "income",
]

def make_mech_summary_filtered(df_core: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_core.copy()
    d_r = d[d["is_rural"] == 1].copy()
    d_u = d[d["is_rural"] == 0].copy()

    rows = []

    # counts rows：*_n = non-missing denom; *_mean = count(>0)
    def add_count_row(row_name, x_all, x_r, x_u, positive_rule):
        xa = pd.to_numeric(x_all, errors="coerce")
        xr = pd.to_numeric(x_r, errors="coerce")
        xu = pd.to_numeric(x_u, errors="coerce")
        rows.append({
            "variable": row_name,
            "label": row_name,
            "all_n": int(xa.notna().sum()),
            "all_mean": int(positive_rule(xa).sum()),
            "all_ci_low": np.nan,
            "all_ci_high": np.nan,
            "rural_n": int(xr.notna().sum()),
            "rural_mean": int(positive_rule(xr).sum()),
            "rural_ci_low": np.nan,
            "rural_ci_high": np.nan,
            "urban_n": int(xu.notna().sum()),
            "urban_mean": int(positive_rule(xu).sum()),
            "urban_ci_low": np.nan,
            "urban_ci_high": np.nan,
            "urban_minus_rural": np.nan,
            "diff_ci_low": np.nan,
            "diff_ci_high": np.nan,
        })

    add_count_row(
        "N(edu_train_total>0)",
        d["edu_train_total"], d_r["edu_train_total"], d_u["edu_train_total"],
        positive_rule=lambda s: (s > 0) & s.notna()
    )
    add_count_row(
        "N(edu_debt_balance>0)",
        d["edu_debt_balance"], d_r["edu_debt_balance"], d_u["edu_debt_balance"],
        positive_rule=lambda s: (s > 0) & s.notna()
    )

    var_map = [
        ("has_edu_spend", "Any education training spending (extensive, 0/1)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("has_edu_debt", "Any education-related debt (extensive, 0/1)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("income", "Household disposable income (RMB)"),
    ]

    for var, label in var_map:
        if var not in d.columns:
            continue
        sA = mean_ci(d[var])
        sR = mean_ci(d_r[var])
        sU = mean_ci(d_u[var])
        sD = diff_means_ci(d_u[var], d_r[var])

        rows.append({
            "variable": var,
            "label": label,
            "all_n": sA["n"], "all_mean": sA["mean"], "all_ci_low": sA["ci_low"], "all_ci_high": sA["ci_high"],
            "rural_n": sR["n"], "rural_mean": sR["mean"], "rural_ci_low": sR["ci_low"], "rural_ci_high": sR["ci_high"],
            "urban_n": sU["n"], "urban_mean": sU["mean"], "urban_ci_low": sU["ci_low"], "urban_ci_high": sU["ci_high"],
            "urban_minus_rural": sD["diff"], "diff_ci_low": sD["ci_low"], "diff_ci_high": sD["ci_high"],
        })

    mech_num = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    mech_num["__ord"] = mech_num["variable"].map({k: i for i, k in enumerate(KEEP_ROWS)})
    mech_num = mech_num[mech_num["__ord"].notna()].sort_values("__ord").drop(columns="__ord").reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    mech_pretty = mech_num.copy()
    mech_pretty["all_CI"] = mech_pretty.apply(lambda r: fmt_ci(r["all_ci_low"], r["all_ci_high"]), axis=1)
    mech_pretty["rural_CI"] = mech_pretty.apply(lambda r: fmt_ci(r["rural_ci_low"], r["rural_ci_high"]), axis=1)
    mech_pretty["urban_CI"] = mech_pretty.apply(lambda r: fmt_ci(r["urban_ci_low"], r["urban_ci_high"]), axis=1)
    mech_pretty["diff_CI"] = mech_pretty.apply(lambda r: fmt_ci(r["diff_ci_low"], r["diff_ci_high"]), axis=1)

    keep_cols = [
        "variable", "label",
        "all_n", "all_mean", "all_CI",
        "rural_n", "rural_mean", "rural_CI",
        "urban_n", "urban_mean", "urban_CI",
        "urban_minus_rural", "diff_CI",
    ]
    mech_pretty = mech_pretty[keep_cols].copy()

    return mech_num, mech_pretty

def plot_forest_urban_minus_rural(mech_num: pd.DataFrame, out_png: Path, title: str):
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = mech_num.copy()
    d = d[pd.to_numeric(d["urban_minus_rural"], errors="coerce").notna()].copy()
    if d.empty:
        return

    # Original notebook comment normalized for the public code archive.
    ylabels = d["label"].tolist()
    diff = pd.to_numeric(d["urban_minus_rural"], errors="coerce").values
    lo = pd.to_numeric(d["diff_ci_low"], errors="coerce").values
    hi = pd.to_numeric(d["diff_ci_high"], errors="coerce").values

    y = np.arange(len(ylabels))[::-1]

    fig, ax = plt.subplots(figsize=(9.2, 0.85 * len(ylabels) + 2.0))
    xerr = np.vstack([diff - lo, hi - diff])
    ax.errorbar(diff, y, xerr=xerr, fmt="o", capsize=3)
    ax.axvline(0, linewidth=1)

    ax.set_yticks(y)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("Urban − Rural difference (mean) with 95% CI")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_flood_panel(flood_csv: Path):
    df = pd.read_csv(flood_csv)
    if "county_code" in df.columns:
        pass
    elif "county_id" in df.columns:
        df = df.rename(columns={"county_id": "county_code"})
    else:
        raise ValueError("洪水文件中找不到 county_code/county_id。")

    df["county_code"] = safe_int64(df["county_code"])
    df["year"] = safe_int64(df["year"])

    for t in T_LIST:
        c = f"flood_ge_T{t}"
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=["county_code", "year"]).copy()
    return df

def build_flood_windows(df_flood: pd.DataFrame, k_list):
    df = df_flood.sort_values(["county_code", "year"]).copy()
    for k in k_list:
        for t in T_LIST:
            base = f"flood_ge_T{t}"
            share = f"share_flood_ge_T{t}_{k}y"
            df[share] = (
                df.groupby("county_code")[base]
                  .rolling(window=k, min_periods=1)
                  .mean()
                  .reset_index(level=0, drop=True)
            )
    return df

def merge_exposure(df_chfs: pd.DataFrame, df_flood_win: pd.DataFrame):
    flood_sub = df_flood_win.rename(columns={"year": "edu_year"}).copy()
    keep_cols = ["county_code", "edu_year"] + [c for c in flood_sub.columns if c.startswith("share_flood_ge_T")]
    flood_sub = flood_sub[keep_cols].copy()

    out = df_chfs.merge(flood_sub, on=["county_code", "edu_year"], how="left", validate="m:1")

    share_cols = [c for c in out.columns if c.startswith("share_flood_ge_T")]
    for c in share_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    return out

def exposure_summary_table(df_mech: pd.DataFrame) -> pd.DataFrame:
    share_cols = [c for c in df_mech.columns if c.startswith("share_flood_ge_T")]
    if not share_cols:
        return pd.DataFrame()

    rows = []
    for c in share_cols:
        x = pd.to_numeric(df_mech[c], errors="coerce")
        rows.append({
            "exposure": c,
            "N": int(x.notna().sum()),
            "mean": float(x.mean(skipna=True)),
            "sd": float(x.std(skipna=True, ddof=1)) if int(x.notna().sum()) > 1 else 0.0,
            "p25": float(x.quantile(0.25)),
            "median": float(x.quantile(0.50)),
            "p75": float(x.quantile(0.75)),
            "share_nonzero": float((x > 0).mean(skipna=True)),
            "min": float(x.min(skipna=True)),
            "max": float(x.max(skipna=True)),
        })
    return pd.DataFrame(rows).sort_values("exposure").reset_index(drop=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading CHFS panel: {CHFS_XLSX}")
    df0 = load_chfs_panel(CHFS_XLSX)

    # County-level processing note.
    df_base = df0.dropna(subset=["county_code", "edu_year"]).copy()

    # Original notebook comment normalized for the public code archive.
    df_core = df_base.copy()
    if VALID_EDU_YEARS is not None:
        df_core = df_core[df_core["edu_year"].isin(VALID_EDU_YEARS)].copy()
    df_core = df_core[pd.to_numeric(df_core["has_u15_child"], errors="coerce") == 1].copy()

    # Original notebook comment normalized for the public code archive.
    exposure_tbl = pd.DataFrame()
    if DO_FLOOD_MERGE:
        print(f"[INFO] Reading flood panel: {FLOOD_CSV}")
        f0 = load_flood_panel(FLOOD_CSV)
        fwin = build_flood_windows(f0, K_WINDOWS)
        df_core = merge_exposure(df_core, fwin)
        exposure_tbl = exposure_summary_table(df_core)

    # =============================================================================
    sample_tbl = make_sample_construction(df_base)

    # =============================================================================
    wave_tbl = make_wave_households(df_core)

    # =============================================================================
    fe_tbl = make_fe_unit_sizes_summary(df_core)

    # =============================================================================
    mech_num, mech_pretty = make_mech_summary_filtered(df_core)

    # =============================================================================
    plot_wave_households_bar(
        wave_tbl,
        FIG_DIR / "wave_households_bar.png",
        title="Sample size by wave (mechanism core sample)"
    )

    # =============================================================================
    plot_forest_urban_minus_rural(
        mech_num,
        FIG_DIR / "forest_urban_minus_rural.png",
        title="Urban − Rural differences (mechanism variables)"
    )

    # =============================================================================
    plot_fe_boxplots(df_core, FIG_DIR)

    # =============================================================================
    print(f"[INFO] Writing Excel to: {OUT_XLSX}")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        sample_tbl.to_excel(writer, sheet_name="sample_construction", index=False)
        wave_tbl.to_excel(writer, sheet_name="wave_households", index=False)
        fe_tbl.to_excel(writer, sheet_name="fe_unit_sizes", index=False)
        mech_pretty.to_excel(writer, sheet_name="mech_summary_charls", index=False)

        sheet = "combined_panels"
        startrow = 0

        pd.DataFrame([["Panel A. Sample construction (counts)"]]).to_excel(
            writer, sheet_name=sheet, index=False, header=False, startrow=startrow
        )
        startrow += 2
        sample_tbl.to_excel(writer, sheet_name=sheet, index=False, startrow=startrow)
        startrow += len(sample_tbl) + 3

        pd.DataFrame([["Panel B. Mechanism variables: mean and 95% CI; Urban−Rural differences (forest plot in figures/)"]]).to_excel(
            writer, sheet_name=sheet, index=False, header=False, startrow=startrow
        )
        startrow += 2
        mech_pretty.to_excel(writer, sheet_name=sheet, index=False, startrow=startrow)

        if DO_FLOOD_MERGE and not exposure_tbl.empty:
            exposure_tbl.to_excel(writer, sheet_name="exposure_summary", index=False)

    print("[DONE] Tables exported.")
    print(f"[DONE] Figures saved to: {FIG_DIR}")
    print("       - wave_households_bar.png")
    print("       - forest_urban_minus_rural.png")
    print("       - fe_boxplot_county_cluster_size.png")
    print("       - fe_boxplot_county_year_cell_size.png")
    print("       - fe_boxplot_n_edu_years_per_county.png")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""


from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
CHFS_XLSX = Path(
    r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS"
    r"\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx"
)

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")
OUT_XLSX = OUT_DIR / "CHFS_pre_regression_diagnostics_tables.xlsx"
FIG_DIR = OUT_DIR / "figure"

# Original notebook comment normalized for the public code archive.
VALID_EDU_YEARS = [2010, 2012, 2014]   # e.g. None

# Original notebook comment normalized for the public code archive.
FOREST_SCALE = "standardized"

# =========================================================
# CHARLS processing note.
# =========================================================
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams.update(
    {
        "font.family": "Times New Roman",
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
    }
)


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def mean_ci(x: pd.Series, z: float = 1.96) -> dict:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = int(x.shape[0])
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, se=np.nan, ci_low=np.nan, ci_high=np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else np.nan
    return dict(n=n, mean=m, sd=sd, se=se, ci_low=m - z * se, ci_high=m + z * se)


def diff_means_ci(u: pd.Series, r: pd.Series, z: float = 1.96) -> dict:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    u = pd.to_numeric(u, errors="coerce").dropna()
    r = pd.to_numeric(r, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu == 0 or nr == 0:
        return dict(diff=np.nan, se=np.nan, ci_low=np.nan, ci_high=np.nan, n_u=nu, n_r=nr, sd_u=np.nan, sd_r=np.nan)
    mu, mr = float(u.mean()), float(r.mean())
    sd_u = float(u.std(ddof=1)) if nu > 1 else 0.0
    sd_r = float(r.std(ddof=1)) if nr > 1 else 0.0
    diff = mu - mr
    se = np.sqrt((sd_u**2) / nu + (sd_r**2) / nr)
    return dict(diff=diff, se=se, ci_low=diff - z * se, ci_high=diff + z * se, n_u=nu, n_r=nr, sd_u=sd_u, sd_r=sd_r)


def pooled_sd(sd_u: float, sd_r: float, n_u: int, n_r: int) -> float:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if n_u + n_r <= 2:
        return np.nan
    den = (n_u + n_r - 2)
    if den <= 0:
        return np.nan
    return float(np.sqrt(((n_u - 1) * (sd_u**2) + (n_r - 1) * (sd_r**2)) / den))


def format_ci(mean: float, low: float, high: float, fmt: str) -> str:
    if np.isnan(mean) or np.isnan(low) or np.isnan(high):
        return ""
    return f"[{low:{fmt}}, {high:{fmt}}]"

def make_group_at_household_level(df: pd.DataFrame, id_col: str = "家庭ID") -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = df.copy()
    if "is_rural" not in out.columns:
        out["is_rural_hh"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
        return out

    tmp = out[[id_col, "is_rural"]].copy()
    tmp["is_rural"] = pd.to_numeric(tmp["is_rural"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    g = tmp.groupby(id_col)["is_rural"].mean().astype("float64")

    is_rural_hh = pd.Series(pd.NA, index=g.index, dtype="Int64")
    is_rural_hh.loc[g > 0.5] = 1
    is_rural_hh.loc[g < 0.5] = 0

    out = out.merge(
        is_rural_hh.rename("is_rural_hh"),
        left_on=id_col,
        right_index=True,
        how="left",
    )
    out["is_rural_hh"] = out["is_rural_hh"].astype("Int64")
    return out


def count_multidim(dfx: pd.DataFrame) -> dict:
    return dict(
        obs=int(dfx.shape[0]),
        hh=int(dfx["家庭ID"].nunique(dropna=True)),
        counties=int(dfx["county_code"].nunique(dropna=True)) if "county_code" in dfx.columns else 0,
    )


# =========================================================
# CHFS/CFHS processing note.
# =========================================================
def load_chfs_panel(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份",
            "county_code",
            "是否农村",
            "是否有15岁及以下儿童",
            "15岁及以下儿童数量",
            "家庭可支配收入（元）",
            "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）",
            "教育负债余额（元）",
            "教育培训支出口径年份",
            "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("CHFS 表缺少『家庭ID』列。")
    if "来源年份" not in df.columns:
        raise KeyError("CHFS 表缺少『来源年份』列。")
    if "county_code" not in df.columns:
        raise KeyError("CHFS 表缺少『county_code』列。")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # Original notebook comment normalized for the public code archive.
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # children
    raw_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(raw_child == 1, 1, np.where(raw_child == 0, 0, np.nan))
    df["n_u15_child"] = pd.to_numeric(df.get("15岁及以下儿童数量"), errors="coerce")
    df["log_childnum"] = np.log1p(df["n_u15_child"].clip(lower=0))  # Original notebook comment normalized for the public code archive.

    # income
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)
    df["log_income"] = np.log1p(df["income"])

    # education spending
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["has_edu_spend"] = np.where(
        df["edu_train_total"].notna(),
        (df["edu_train_total"] > 0).astype(int),
        np.nan,
    )
    df["has_edu_spend"] = safe_int64(df["has_edu_spend"])
    df["ln_edu_train_total"] = np.log1p(df["edu_train_total"])

    # education debt (1/2 coding strict)
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))
    df["has_edu_debt"] = safe_int64(pd.Series(df["has_edu_debt"]))

    # debt balance (optional)
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
    else:
        df["edu_debt_balance"] = np.nan

    # Original notebook comment normalized for the public code archive.
    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    if "收入口径年份" in df.columns:
        edu_year = edu_year.fillna(pd.to_numeric(df.get("收入口径年份"), errors="coerce"))
    df["edu_year"] = safe_int64(edu_year)

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["家庭ID", "wave"]).copy()

    # household-level group
    df = make_group_at_household_level(df, id_col="家庭ID")

    return df


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
def build_mechanism_core_sample(df0: pd.DataFrame) -> pd.DataFrame:
    d = df0.copy()
    d = d.dropna(subset=["county_code", "edu_year"]).copy()
    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()
    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()
    return d


def build_analysis_samples(df_core: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_core.copy()

    # common controls used in your earlier script logic
    base_controls = ["log_income", "log_childnum", "county_code", "edu_year"]

    # spending extensive
    spending_ext = d.dropna(subset=base_controls + ["has_edu_spend"]).copy()

    # spending intensive
    spending_int = spending_ext[pd.to_numeric(spending_ext["edu_train_total"], errors="coerce") > 0].copy()

    # debt extensive
    debt_ext = d.dropna(subset=base_controls + ["has_edu_debt"]).copy()

    # debt intensive
    if "edu_debt_balance" in debt_ext.columns:
        debt_int = debt_ext[pd.to_numeric(debt_ext["edu_debt_balance"], errors="coerce") > 0].copy()
    else:
        debt_int = debt_ext.iloc[0:0].copy()

    return dict(
        core=d,
        spending_ext=spending_ext,
        spending_int=spending_int,
        debt_ext=debt_ext,
        debt_int=debt_int,
    )


def make_sample_construction_used(samples: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    row_specs = [
        ("Mechanism core sample", "Children <=15; non-missing county_code & edu_year; optional edu_year restriction", "core"),
        ("Education spending (extensive margin)", "Non-missing has_edu_spend and controls", "spending_ext"),
        ("Education spending (intensive margin)", "Conditional on edu_train_total > 0", "spending_int"),
        ("Education debt (extensive margin)", "Non-missing has_edu_debt and controls", "debt_ext"),
        ("Education debt (intensive margin)", "Conditional on edu_debt_balance > 0", "debt_int"),
    ]

    out_rows = []
    for name, definition, key in row_specs:
        d = samples[key]

        d_all = d
        d_r = d[d["is_rural_hh"] == 1]
        d_u = d[d["is_rural_hh"] == 0]

        a = count_multidim(d_all)
        r = count_multidim(d_r)
        u = count_multidim(d_u)

        out_rows.append(
            {
                "Sample": name,
                "Definition": definition,
                "All_obs": a["obs"],
                "All_hh": a["hh"],
                "All_counties": a["counties"],
                "Rural_obs": r["obs"],
                "Rural_hh": r["hh"],
                "Rural_counties": r["counties"],
                "Urban_obs": u["obs"],
                "Urban_hh": u["hh"],
                "Urban_counties": u["counties"],
            }
        )

    return pd.DataFrame(out_rows)


# =========================================================
# CHARLS processing note.
# =========================================================
def build_wave_stacked_and_cum_summary(df_core: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    tmp = df_core[["家庭ID", "wave", "is_rural_hh"]].dropna(subset=["家庭ID", "wave"]).copy()
    tmp["wave"] = pd.to_numeric(tmp["wave"], errors="coerce")
    tmp = tmp.dropna(subset=["wave"])
    tmp["wave"] = tmp["wave"].astype(int)

    years = sorted(tmp["wave"].unique())

    # wave unique counts by group
    wave_counts = (
        tmp.dropna(subset=["is_rural_hh"])
        .groupby(["wave", "is_rural_hh"])["家庭ID"]
        .nunique()
        .unstack("is_rural_hh")
        .reindex(years)
        .fillna(0)
        .astype(int)
    )
    # ensure both columns exist: rural=1, urban=0
    if 1 not in wave_counts.columns:
        wave_counts[1] = 0
    if 0 not in wave_counts.columns:
        wave_counts[0] = 0
    wave_counts = wave_counts[[1, 0]]  # rural then urban

    wave_rural = wave_counts[1].values
    wave_urban = wave_counts[0].values

    # Original notebook comment normalized for the public code archive.
    pid_first = (
        tmp.dropna(subset=["is_rural_hh"])
        .groupby("家庭ID")
        .agg(first_wave=("wave", "min"), group=("is_rural_hh", "first"))
    )
    first_rural = pid_first.loc[pid_first["group"] == 1, "first_wave"]
    first_urban = pid_first.loc[pid_first["group"] == 0, "first_wave"]

    cum_rural = [int((first_rural <= y).sum()) for y in years]
    cum_urban = [int((first_urban <= y).sum()) for y in years]
    cum_total = [int((pid_first["first_wave"] <= y).sum()) for y in years]

    # new vs previous wave (per group): new = wave unique - already seen before that wave
    seen_rural, seen_urban = set(), set()
    new_rural, new_urban = [], []
    for y in years:
        s_r = set(tmp[(tmp["wave"] == y) & (tmp["is_rural_hh"] == 1)]["家庭ID"].astype(str).unique())
        s_u = set(tmp[(tmp["wave"] == y) & (tmp["is_rural_hh"] == 0)]["家庭ID"].astype(str).unique())
        new_rural.append(len(s_r - seen_rural))
        new_urban.append(len(s_u - seen_urban))
        seen_rural |= s_r
        seen_urban |= s_u

    out = pd.DataFrame(
        {
            "wave": years,
            "wave_rural_unique": wave_rural,
            "wave_urban_unique": wave_urban,
            "wave_total_unique": wave_rural + wave_urban,
            "cum_rural_unique": cum_rural,
            "cum_urban_unique": cum_urban,
            "cum_total_unique": cum_total,
            "new_rural_unique": new_rural,
            "new_urban_unique": new_urban,
            "new_total_unique": (np.array(new_rural) + np.array(new_urban)).astype(int),
        }
    )
    return out


def plot_wave_stacked_with_cum(summary_df: pd.DataFrame, save_path: Path) -> None:
    years = summary_df["wave"].tolist()
    x = list(range(len(years)))

    wave_rural = summary_df["wave_rural_unique"].tolist()
    wave_urban = summary_df["wave_urban_unique"].tolist()
    total_wave = summary_df["wave_total_unique"].tolist()

    cum_rural = summary_df["cum_rural_unique"].tolist()
    cum_urban = summary_df["cum_urban_unique"].tolist()

    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    bar_width = 0.45

    ax1.bar(x, wave_rural, width=bar_width, label="Rural wave unique")
    ax1.bar(x, wave_urban, width=bar_width, bottom=wave_rural, label="Urban wave unique")

    ax1.set_xlabel("Survey wave (year)")
    ax1.set_ylabel("Wave unique households")

    ax1.set_xticks(x)
    ax1.set_xticklabels([str(y) for y in years])

    # right axis cumulative
    ax2 = ax1.twinx()
    ax2.plot(x, cum_rural, marker="o", label="Rural cumulative unique")
    ax2.plot(x, cum_urban, marker="o", label="Urban cumulative unique")
    ax2.set_ylabel("Cumulative unique households")

    # label totals on top of bars
    max_wave = max(total_wave) if total_wave else 0
    label_offset = 0.02 * max_wave if max_wave > 0 else 0
    for xi, tot in zip(x, total_wave):
        ax1.text(xi, tot + label_offset, f"{tot:,}", ha="center", va="bottom", fontsize=9)

    # legend merge
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(0.02, 0.99), frameon=False)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close(fig)


# =========================================================
# Fixed-effects regression helper.
# =========================================================
def quantile_summary(x: pd.Series) -> dict:
    x = pd.to_numeric(x, errors="coerce").dropna()
    if x.empty:
        return dict(N=0, mean=np.nan, sd=np.nan, min=np.nan, p25=np.nan, median=np.nan, p75=np.nan, max=np.nan)
    return dict(
        N=int(x.shape[0]),
        mean=float(x.mean()),
        sd=float(x.std(ddof=1)) if x.shape[0] > 1 else 0.0,
        min=float(x.min()),
        p25=float(x.quantile(0.25)),
        median=float(x.quantile(0.50)),
        p75=float(x.quantile(0.75)),
        max=float(x.max()),
    )


def make_fe_unit_sizes_table(df_core: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def one_group(tag: str, d: pd.DataFrame) -> dict:
        g_county = d.groupby("county_code").size()
        g_cell = d.groupby(["county_code", "edu_year"]).size()
        g_nyears = d.groupby("county_code")["edu_year"].nunique(dropna=True)

        s1 = quantile_summary(g_county)
        s2 = quantile_summary(g_cell)
        s3 = quantile_summary(g_nyears)

        return {
            "group": tag,
            "N_obs": int(d.shape[0]),
            "N_households": int(d["家庭ID"].nunique(dropna=True)),
            "N_counties": int(d["county_code"].nunique(dropna=True)),
            "N_county_year_cells": int(g_cell.shape[0]),
            "county_cluster_N": s1["N"],
            "county_cluster_median": s1["median"],
            "county_cluster_p25": s1["p25"],
            "county_cluster_p75": s1["p75"],
            "county_cluster_max": s1["max"],
            "county_year_cell_N": s2["N"],
            "county_year_cell_median": s2["median"],
            "county_year_cell_p25": s2["p25"],
            "county_year_cell_p75": s2["p75"],
            "county_year_cell_max": s2["max"],
            "n_edu_years_per_county_N": s3["N"],
            "n_edu_years_per_county_median": s3["median"],
            "n_edu_years_per_county_p25": s3["p25"],
            "n_edu_years_per_county_p75": s3["p75"],
            "n_edu_years_per_county_max": s3["max"],
            "N_counties_with_ge2_edu_years": int((g_nyears >= 2).sum()) if not g_nyears.empty else 0,
        }

    all_g = one_group("All", df_core)
    rural_g = one_group("Rural", df_core[df_core["is_rural_hh"] == 1])
    urban_g = one_group("Urban", df_core[df_core["is_rural_hh"] == 0])
    return pd.DataFrame([all_g, rural_g, urban_g])


def plot_fe_boxplots(df_core: pd.DataFrame, save_prefix: Path) -> None:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    groups = {
        "All": df_core,
        "Rural": df_core[df_core["is_rural_hh"] == 1],
        "Urban": df_core[df_core["is_rural_hh"] == 0],
    }

    def get_arrays(metric: str) -> list[np.ndarray]:
        arrs = []
        for _, d in groups.items():
            if metric == "obs_per_county":
                x = d.groupby("county_code").size()
            elif metric == "obs_per_county_year":
                x = d.groupby(["county_code", "edu_year"]).size()
            elif metric == "n_edu_years_per_county":
                x = d.groupby("county_code")["edu_year"].nunique(dropna=True)
            else:
                raise ValueError(metric)
            arrs.append(pd.to_numeric(x, errors="coerce").dropna().to_numpy())
        return arrs

    def draw(metric: str, title: str, ylabel: str, logy: bool, out_name: str):
        data = get_arrays(metric)
        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        ax.boxplot(
            data,
            tick_labels=list(groups.keys()),  # Original notebook comment normalized for the public code archive.
            showfliers=True,
        )
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        if logy:
            ax.set_yscale("log")
        plt.tight_layout()
        out_path = save_prefix.parent / out_name
        plt.savefig(out_path, dpi=300)
        plt.close(fig)

    save_prefix.parent.mkdir(parents=True, exist_ok=True)
    draw(
        "obs_per_county",
        "County cluster size: observations per county",
        "Count (log scale)",
        True,
        "fe_boxplot_obs_per_county.png",
    )
    draw(
        "obs_per_county_year",
        "County×edu_year cell size: observations per cell",
        "Count (log scale)",
        True,
        "fe_boxplot_obs_per_county_year.png",
    )
    draw(
        "n_edu_years_per_county",
        "Within-variation proxy: # distinct edu_year per county",
        "Count",
        False,
        "fe_boxplot_n_edu_years_per_county.png",
    )


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
def make_mech_summary_used_only(df_core: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df_core.copy()
    d_r = d[d["is_rural_hh"] == 1].copy()
    d_u = d[d["is_rural_hh"] == 0].copy()

    # Original notebook comment normalized for the public code archive.
    var_list = [
        ("has_edu_spend", "Any education training spending (extensive, 0/1)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("has_edu_debt", "Any education-related debt (extensive, 0/1)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("income", "Household disposable income (RMB)"),
    ]

    # Original notebook comment normalized for the public code archive.
    fmt_map = {
        "has_edu_spend": ".3f",
        "has_edu_debt": ".3f",
        "edu_train_total": ",.0f",
        "edu_debt_balance": ",.0f",
        "income": ",.0f",
    }

    rows = []
    for var, label in var_list:
        if var not in d.columns:
            # Original notebook comment normalized for the public code archive.
            rows.append(
                {
                    "Variable": var,
                    "Label": label,
                    "All_n": 0,
                    "All_mean": np.nan,
                    "All_CI": "",
                    "Rural_n": 0,
                    "Rural_mean": np.nan,
                    "Rural_CI": "",
                    "Urban_n": 0,
                    "Urban_mean": np.nan,
                    "Urban_CI": "",
                    "Urban_minus_Rural": np.nan,
                    "Diff_CI": "",
                    "diff_raw": np.nan,
                    "diff_raw_low": np.nan,
                    "diff_raw_high": np.nan,
                    "n_u": 0,
                    "n_r": 0,
                    "sd_u": np.nan,
                    "sd_r": np.nan,
                }
            )
            continue

        s_all = mean_ci(d[var])
        s_r = mean_ci(d_r[var])
        s_u = mean_ci(d_u[var])
        s_diff = diff_means_ci(d_u[var], d_r[var])

        fmt = fmt_map.get(var, ".3f")

        rows.append(
            {
                "Variable": var,
                "Label": label,
                "All_n": s_all["n"],
                "All_mean": s_all["mean"],
                "All_CI": format_ci(s_all["mean"], s_all["ci_low"], s_all["ci_high"], fmt),
                "Rural_n": s_r["n"],
                "Rural_mean": s_r["mean"],
                "Rural_CI": format_ci(s_r["mean"], s_r["ci_low"], s_r["ci_high"], fmt),
                "Urban_n": s_u["n"],
                "Urban_mean": s_u["mean"],
                "Urban_CI": format_ci(s_u["mean"], s_u["ci_low"], s_u["ci_high"], fmt),
                "Urban_minus_Rural": s_diff["diff"],
                "Diff_CI": format_ci(s_diff["diff"], s_diff["ci_low"], s_diff["ci_high"], fmt),
                # Original notebook comment normalized for the public code archive.
                "diff_raw": s_diff["diff"],
                "diff_raw_low": s_diff["ci_low"],
                "diff_raw_high": s_diff["ci_high"],
                "n_u": s_diff["n_u"],
                "n_r": s_diff["n_r"],
                "sd_u": s_diff["sd_u"],
                "sd_r": s_diff["sd_r"],
            }
        )

    out = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    n_spend_pos_all = int((pd.to_numeric(d["edu_train_total"], errors="coerce") > 0).sum()) if "edu_train_total" in d.columns else 0
    n_spend_pos_r = int((pd.to_numeric(d_r["edu_train_total"], errors="coerce") > 0).sum()) if "edu_train_total" in d_r.columns else 0
    n_spend_pos_u = int((pd.to_numeric(d_u["edu_train_total"], errors="coerce") > 0).sum()) if "edu_train_total" in d_u.columns else 0

    n_debt_pos_all = int((pd.to_numeric(d["edu_debt_balance"], errors="coerce") > 0).sum()) if "edu_debt_balance" in d.columns else 0
    n_debt_pos_r = int((pd.to_numeric(d_r["edu_debt_balance"], errors="coerce") > 0).sum()) if "edu_debt_balance" in d_r.columns else 0
    n_debt_pos_u = int((pd.to_numeric(d_u["edu_debt_balance"], errors="coerce") > 0).sum()) if "edu_debt_balance" in d_u.columns else 0

    add_rows = pd.DataFrame(
        [
            {
                "Variable": "N(edu_train_total>0)",
                "Label": "Intensive sample size (count): edu_train_total > 0",
                "All_n": "",
                "All_mean": n_spend_pos_all,
                "All_CI": "",
                "Rural_n": "",
                "Rural_mean": n_spend_pos_r,
                "Rural_CI": "",
                "Urban_n": "",
                "Urban_mean": n_spend_pos_u,
                "Urban_CI": "",
                "Urban_minus_Rural": "",
                "Diff_CI": "",
                "diff_raw": np.nan,
                "diff_raw_low": np.nan,
                "diff_raw_high": np.nan,
                "n_u": 0,
                "n_r": 0,
                "sd_u": np.nan,
                "sd_r": np.nan,
            },
            {
                "Variable": "N(edu_debt_balance>0)",
                "Label": "Intensive sample size (count): edu_debt_balance > 0",
                "All_n": "",
                "All_mean": n_debt_pos_all,
                "All_CI": "",
                "Rural_n": "",
                "Rural_mean": n_debt_pos_r,
                "Rural_CI": "",
                "Urban_n": "",
                "Urban_mean": n_debt_pos_u,
                "Urban_CI": "",
                "Urban_minus_Rural": "",
                "Diff_CI": "",
                "diff_raw": np.nan,
                "diff_raw_low": np.nan,
                "diff_raw_high": np.nan,
                "n_u": 0,
                "n_r": 0,
                "sd_u": np.nan,
                "sd_r": np.nan,
            },
        ]
    )

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    #   N(spend>0), has_edu_spend, edu_train_total, N(debt>0), has_edu_debt, edu_debt_balance, income
    base = out.set_index("Variable")
    final_order = [
        "N(edu_train_total>0)",
        "has_edu_spend",
        "edu_train_total",
        "N(edu_debt_balance>0)",
        "has_edu_debt",
        "edu_debt_balance",
        "income",
    ]
    combined = pd.concat([base.reset_index(), add_rows], ignore_index=True)
    combined = combined.set_index("Variable").reindex(final_order).reset_index()

    return combined


def build_forest_data(mech_tbl: pd.DataFrame, scale: str = "standardized") -> pd.DataFrame:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    tmp = mech_tbl.copy()
    tmp = tmp[~tmp["Variable"].astype(str).str.startswith("N(")].copy()

    out_rows = []
    for _, r in tmp.iterrows():
        var = r["Variable"]
        label = r["Label"]

        diff = pd.to_numeric(r.get("diff_raw"), errors="coerce")
        low = pd.to_numeric(r.get("diff_raw_low"), errors="coerce")
        high = pd.to_numeric(r.get("diff_raw_high"), errors="coerce")

        # Original notebook comment normalized for the public code archive.
        if np.isnan(diff) or np.isnan(low) or np.isnan(high):
            continue

        if scale == "standardized":
            n_u = int(pd.to_numeric(r.get("n_u"), errors="coerce")) if pd.notna(r.get("n_u")) else 0
            n_r = int(pd.to_numeric(r.get("n_r"), errors="coerce")) if pd.notna(r.get("n_r")) else 0
            sd_u = float(pd.to_numeric(r.get("sd_u"), errors="coerce"))
            sd_r = float(pd.to_numeric(r.get("sd_r"), errors="coerce"))
            psd = pooled_sd(sd_u, sd_r, n_u, n_r)
            if np.isnan(psd) or psd == 0:
                continue
            out_rows.append(
                {
                    "Label": label,
                    "effect": diff / psd,
                    "low": low / psd,
                    "high": high / psd,
                    "scale": "SMD (Urban − Rural), 95% CI",
                }
            )

        elif scale == "percent":
            mu_r = float(pd.to_numeric(r.get("Rural_mean"), errors="coerce"))
            # Original notebook comment normalized for the public code archive.
            if var in ("has_edu_spend", "has_edu_debt"):
                out_rows.append(
                    {
                        "Label": label,
                        "effect": diff * 100.0,
                        "low": low * 100.0,
                        "high": high * 100.0,
                        "scale": "Percentage point diff (Urban − Rural), 95% CI",
                    }
                )
            else:
                if np.isnan(mu_r) or mu_r == 0:
                    continue
                out_rows.append(
                    {
                        "Label": label,
                        "effect": (diff / mu_r) * 100.0,
                        "low": (low / mu_r) * 100.0,
                        "high": (high / mu_r) * 100.0,
                        "scale": "% difference vs Rural mean, 95% CI",
                    }
                )
        else:
            raise ValueError("scale must be 'standardized' or 'percent'")

    return pd.DataFrame(out_rows)


def plot_forest(forest_df: pd.DataFrame, save_path: Path) -> None:
    if forest_df.empty:
        return

    labels = forest_df["Label"].tolist()
    eff = forest_df["effect"].tolist()
    low = forest_df["low"].tolist()
    high = forest_df["high"].tolist()
    scale_label = forest_df["scale"].iloc[0]

    y = np.arange(len(labels))[::-1]  # top to bottom

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.axvline(0, linewidth=1)

    # error bars
    xerr = [np.array(eff) - np.array(low), np.array(high) - np.array(eff)]
    ax.errorbar(eff, y, xerr=xerr, fmt="o", capsize=3)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(scale_label)
    ax.set_title("Urban − Rural differences (mechanism variables)")

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close(fig)


# =========================================================
# Excel output note.
# =========================================================
def write_table1_combined(writer: pd.ExcelWriter, panelA: pd.DataFrame, panelB: pd.DataFrame) -> None:
    """Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sheet = "Table1_Sample_and_Mechanism"

    # Panel A
    start = 0
    panelA.to_excel(writer, sheet_name=sheet, index=False, startrow=start)
    start += len(panelA) + 3

    # Panel B
    panelB.to_excel(writer, sheet_name=sheet, index=False, startrow=start)


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading CHFS panel: {CHFS_XLSX}")
    df0 = load_chfs_panel(CHFS_XLSX)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_core = build_mechanism_core_sample(df0)
    print("[INFO] Notebook progress message.")

    # analysis samples
    samples = build_analysis_samples(df_core)

    # Panel A: used sample construction (professional naming)
    panelA = make_sample_construction_used(samples)

    # Wave summary + plot (CHARLS style)
    wave_summary = build_wave_stacked_and_cum_summary(samples["core"])
    wave_fig_path = FIG_DIR / "wave_stacked_with_cum_urban_rural.png"
    plot_wave_stacked_with_cum(wave_summary, wave_fig_path)

    # FE table + boxplots
    fe_tbl = make_fe_unit_sizes_table(samples["core"])
    plot_fe_boxplots(samples["core"], FIG_DIR / "fe_")

    # Panel B: mechanism summary (only required rows/cols)
    panelB = make_mech_summary_used_only(samples["core"])

    # Forest plot (standardized by default; avoids scale dominance)
    forest_df = build_forest_data(panelB, scale=FOREST_SCALE)
    forest_fig = FIG_DIR / f"forest_urban_minus_rural_{FOREST_SCALE}.png"
    plot_forest(forest_df, forest_fig)

    # Write Excel (no MultiIndex)
    print(f"[INFO] Writing Excel to: {OUT_XLSX}")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        # Combined Table1 (Panel A + Panel B)
        write_table1_combined(writer, panelA, panelB)

        # Also keep separate sheets for convenience
        panelA.to_excel(writer, sheet_name="sample_construction_used", index=False)
        panelB.to_excel(writer, sheet_name="mech_summary_used", index=False)
        wave_summary.to_excel(writer, sheet_name="wave_summary_core", index=False)
        fe_tbl.to_excel(writer, sheet_name="fe_unit_sizes", index=False)
        forest_df.to_excel(writer, sheet_name="forest_data", index=False)

    print("[DONE] Exported:")
    print(f"  - Excel: {OUT_XLSX}")
    print("  - Figures (in figure/):")
    print("      wave_stacked_with_cum_urban_rural.png")
    print("      fe_boxplot_obs_per_county.png")
    print("      fe_boxplot_obs_per_county_year.png")
    print("      fe_boxplot_n_edu_years_per_county.png")
    print(f"      forest_urban_minus_rural_{FOREST_SCALE}.png")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS mechanism tables (USED sample only)
----------------------------------------
Outputs Excel (flat columns; no MultiIndex) with:
  1) sample_construction_used
  2) mech_summary_used   (means + 95% CI; Urban-Rural diff + 95% CI)

Key requirement:
  - In mech_summary_used, all numeric columns with decimals are rounded to 2 digits.
  - CI columns are strings like "[a, b]" with 2 digits.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# =========================
# 0) Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_XLSX  = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_mechanism_tables_used.xlsx")

VALID_EDU_YEARS = [2010, 2012, 2014]   # set None to disable restriction


# =========================
# 1) Helpers
# =========================
def ensure_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def mean_ci(x: pd.Series, z=1.96):
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = int(x.shape[0])
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, ci_low=np.nan, ci_high=np.nan)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 0 else np.nan
    return dict(n=n, mean=m, sd=sd, ci_low=m - z * se, ci_high=m + z * se)

def diff_means_ci(x_u: pd.Series, x_r: pd.Series, z=1.96):
    u = pd.to_numeric(x_u, errors="coerce").dropna()
    r = pd.to_numeric(x_r, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu == 0 or nr == 0:
        return dict(diff=np.nan, ci_low=np.nan, ci_high=np.nan, n_u=nu, n_r=nr)

    mu, mr = float(u.mean()), float(r.mean())
    sdu = float(u.std(ddof=1)) if nu > 1 else 0.0
    sdr = float(r.std(ddof=1)) if nr > 1 else 0.0
    diff = mu - mr
    se = np.sqrt((sdu**2) / nu + (sdr**2) / nr)
    return dict(diff=diff, ci_low=diff - z * se, ci_high=diff + z * se, n_u=nu, n_r=nr)

def fmt_ci(low, high, decimals=2):
    if pd.isna(low) or pd.isna(high):
        return ""
    return f"[{low:.{decimals}f}, {high:.{decimals}f}]"

def count_obs_hh(d: pd.DataFrame, id_col="家庭ID"):
    return int(d.shape[0]), int(d[id_col].nunique(dropna=True))


# =========================
# 2) Load + construct variables
# =========================
def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份", "county_code", "是否农村",
            "是否有15岁及以下儿童", "15岁及以下儿童数量",
            "家庭可支配收入（元）", "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）", "教育负债余额（元）",
            "教育培训支出口径年份", "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # children
    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    # edu_year
    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    # income
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)

    # spending amount + extensive indicator (IMPORTANT: do NOT treat missing as 0)
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["has_edu_spend"] = np.where(
        df["edu_train_total"].notna(),
        (df["edu_train_total"] > 0).astype(int),
        np.nan,
    )

    # debt extensive strictly from 1/2 coding
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))

    # debt balance
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
    else:
        df["edu_debt_balance"] = np.nan

    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Household-stable rural/urban classification robust to NA:
      mean(is_rural) > 0.5 => rural
      mean(is_rural) < 0.5 => urban
      all-missing => NA
    """
    out = df.copy()
    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()  # NaN if all missing

    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["county_code", "edu_year"]).copy()
    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()
    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    # keep clear household-level rural/urban classification for comparisons
    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# 3) sample_construction_used (professional labels; USED only)
# =========================
def make_sample_construction_used(df_core: pd.DataFrame) -> pd.DataFrame:
    """
    Focus ONLY on 'used' samples (core + each mechanism model sample).
    Outputs obs/hh for all/rural/urban.
    """
    def slice_group(d, grp):
        if grp == "all":
            return d
        if grp == "rural":
            return d[d["is_rural_hh"] == 1]
        if grp == "urban":
            return d[d["is_rural_hh"] == 0]
        raise ValueError(grp)

    # Define used samples (adjust 'req' to match your actual regression RHS if needed)
    samples = [
        ("Core sample (used in mechanism diagnostics)", df_core),

        ("Spending extensive (requires observed has_edu_spend & income)",
         df_core.dropna(subset=["has_edu_spend", "income"])),

        ("Spending intensive (edu_train_total > 0; income observed)",
         df_core[(pd.to_numeric(df_core["edu_train_total"], errors="coerce") > 0) & df_core["income"].notna()]),

        ("Debt extensive (requires observed has_edu_debt & income)",
         df_core.dropna(subset=["has_edu_debt", "income"])),

        ("Debt intensive (edu_debt_balance > 0; income observed)",
         df_core[(pd.to_numeric(df_core["edu_debt_balance"], errors="coerce") > 0) & df_core["income"].notna()]),
    ]

    rows = []
    for name, d in samples:
        row = {"Sample definition": name}
        for grp in ["all", "rural", "urban"]:
            dd = slice_group(d, grp)
            n_obs, n_hh = count_obs_hh(dd)
            row[f"{grp}_N_obs"] = n_obs
            row[f"{grp}_N_households"] = n_hh
        rows.append(row)

    out = pd.DataFrame(rows)

    # reorder columns
    cols = ["Sample definition",
            "all_N_obs", "all_N_households",
            "rural_N_obs", "rural_N_households",
            "urban_N_obs", "urban_N_households"]
    return out[cols]


# =========================
# 4) mech_summary_used (rows filtered; CI columns; rounding=2)
# =========================
def make_mech_summary_used(df_core: pd.DataFrame, decimals: int = 2) -> pd.DataFrame:
    """
    Keep only requested rows:
      N(edu_train_total>0), has_edu_spend, edu_train_total
      N(edu_debt_balance>0), has_edu_debt, edu_debt_balance
      income

    Columns:
      all_n, all_mean, all_CI
      rural_n, rural_mean, rural_CI
      urban_n, urban_mean, urban_CI
      urban_minus_rural, diff_CI
    """
    d = df_core.copy()
    d_r = d[d["is_rural_hh"] == 1].copy()
    d_u = d[d["is_rural_hh"] == 0].copy()

    var_specs = [
        ("has_edu_spend", "Any education training spending (extensive, 0/1)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("has_edu_debt", "Any education-related debt (extensive, 0/1)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("income", "Household disposable income (RMB)"),
    ]

    rows = []
    for var, label in var_specs:
        if var not in d.columns:
            continue

        s_all = mean_ci(d[var])
        s_r = mean_ci(d_r[var])
        s_u = mean_ci(d_u[var])
        s_diff = diff_means_ci(d_u[var], d_r[var])

        rows.append({
            "Row": var,
            "Label": label,

            "all_n": s_all["n"],
            "all_mean": s_all["mean"],
            "all_CI": fmt_ci(s_all["ci_low"], s_all["ci_high"], decimals),

            "rural_n": s_r["n"],
            "rural_mean": s_r["mean"],
            "rural_CI": fmt_ci(s_r["ci_low"], s_r["ci_high"], decimals),

            "urban_n": s_u["n"],
            "urban_mean": s_u["mean"],
            "urban_CI": fmt_ci(s_u["ci_low"], s_u["ci_high"], decimals),

            "urban_minus_rural": s_diff["diff"],
            "diff_CI": fmt_ci(s_diff["ci_low"], s_diff["ci_high"], decimals),
        })

    out = pd.DataFrame(rows)

    # Add availability count rows (N>0) as requested
    avail_rows = []

    if "edu_train_total" in d.columns:
        avail_rows.append({
            "Row": "N(edu_train_total>0)",
            "Label": "Availability (intensive margin): edu_train_total > 0",
            "all_n": int((pd.to_numeric(d["edu_train_total"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_train_total"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_train_total"], errors="coerce") > 0).sum()),
            "all_mean": np.nan, "all_CI": "",
            "rural_mean": np.nan, "rural_CI": "",
            "urban_mean": np.nan, "urban_CI": "",
            "urban_minus_rural": np.nan, "diff_CI": "",
        })

    if "edu_debt_balance" in d.columns:
        avail_rows.append({
            "Row": "N(edu_debt_balance>0)",
            "Label": "Availability (intensive margin): edu_debt_balance > 0",
            "all_n": int((pd.to_numeric(d["edu_debt_balance"], errors="coerce") > 0).sum()),
            "rural_n": int((pd.to_numeric(d_r["edu_debt_balance"], errors="coerce") > 0).sum()),
            "urban_n": int((pd.to_numeric(d_u["edu_debt_balance"], errors="coerce") > 0).sum()),
            "all_mean": np.nan, "all_CI": "",
            "rural_mean": np.nan, "rural_CI": "",
            "urban_mean": np.nan, "urban_CI": "",
            "urban_minus_rural": np.nan, "diff_CI": "",
        })

    if avail_rows:
        out = pd.concat([pd.DataFrame(avail_rows), out], ignore_index=True)

    # ---- rounding requirement: keep 2 decimals for decimal columns ----
    num_cols = ["all_mean", "rural_mean", "urban_mean", "urban_minus_rural"]
    for c in num_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(decimals)

    # counts as Int64
    for c in ["all_n", "rural_n", "urban_n"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype("Int64")

    # final column order
    cols = [
        "Row", "Label",
        "all_n", "all_mean", "all_CI",
        "rural_n", "rural_mean", "rural_CI",
        "urban_n", "urban_mean", "urban_CI",
        "urban_minus_rural", "diff_CI",
    ]
    return out[cols]


# =========================
# 5) Export
# =========================
def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    df0 = make_household_rural_flag(df0, id_col="家庭ID", is_rural_col="is_rural", out_col="is_rural_hh")

    df_core = build_mechanism_core_sample(df0)
    print("[INFO] Notebook progress message.")

    sample_construction_used = make_sample_construction_used(df_core)
    mech_summary_used = make_mech_summary_used(df_core, decimals=2)

    print(f"[WRITE] {OUT_XLSX}")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        sample_construction_used.to_excel(writer, sheet_name="sample_construction_used", index=False)
        mech_summary_used.to_excel(writer, sheet_name="mech_summary_used", index=False)

    print("[DONE] Tables exported.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# 0) Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_DIR  = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")

VALID_EDU_YEARS = [2010, 2012, 2014]   # set to None to disable restriction

# Wave plot colors (required)
RURAL_COLOR = "#f1a340"
URBAN_COLOR = "#998ec3"

# FE boxplot style (robust for heavy tails)
BOX_WINSOR_Q = 0.99
BOX_LOG1P = True
BOX_WHIS = (5, 95)          # percentile whiskers (sampling-style)
BOX_SHOWMEANS = True

# Forest plot output base name
FOREST_BASENAME = "forest_urban_minus_rural_standardized"


# =========================
# 1) Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


# =========================
# 2) Data loading + core variable construction
# =========================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    # numeric coercion
    df = ensure_numeric(
        df,
        [
            "来源年份", "county_code", "是否农村",
            "是否有15岁及以下儿童", "15岁及以下儿童数量",
            "家庭可支配收入（元）", "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）", "教育负债余额（元）",
            "教育培训支出口径年份", "收入口径年份",
        ],
    )

    # required IDs
    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    # wave and county
    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # time-varying rural flag (0/1/NA)
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    # children indicator
    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    # Fixed-effects regression helper.
    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    # income
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)

    # education training spending
    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    # education debt (extensive) strictly from raw 1/2 coding
    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))

    # debt balance (if missing column, keep NaN)
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
    else:
        df["edu_debt_balance"] = np.nan

    # drop records without essential identifiers
    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Household-stable rural/urban classification robust to NA.

    group mean over 0/1 ignoring NA:
        > threshold => rural (1)
        < threshold => urban (0)
        else => NA
    """
    if is_rural_col not in df.columns:
        raise KeyError(f"Missing column: {is_rural_col}")

    out = df.copy()
    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()  # float, NaN if all NA

    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    """
    Core sample used for mechanism diagnostics/plots:
        - non-missing county_code, edu_year
        - edu_year in VALID_EDU_YEARS (if not None)
        - has_u15_child == 1
        - requires is_rural_hh to identify rural/urban in plots
    """
    d = df.copy()
    d = d.dropna(subset=["county_code", "edu_year"]).copy()

    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()

    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    # keep households with clear classification for rural/urban comparisons
    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# 3) Wave stacked + cumulative (CHARLS-style)
# =========================
def build_stacked_wave_and_cum_summary(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    wave_col: str = "wave",
    is_rural_hh_col: str = "is_rural_hh",
) -> pd.DataFrame:
    needed = [id_col, wave_col, is_rural_hh_col]
    for c in needed:
        if c not in df.columns:
            raise KeyError(f"Missing column: {c}")

    tmp = df[needed].copy()
    tmp[wave_col] = pd.to_numeric(tmp[wave_col], errors="coerce")
    tmp = tmp.dropna(subset=[wave_col])
    tmp[wave_col] = tmp[wave_col].astype(int)

    tmp[is_rural_hh_col] = pd.to_numeric(tmp[is_rural_hh_col], errors="coerce")
    tmp = tmp[tmp[is_rural_hh_col].isin([0, 1])].copy()

    # urban_group: 1 urban (is_rural_hh==0), 0 rural (is_rural_hh==1)
    tmp["urban_group"] = (tmp[is_rural_hh_col] == 0).astype(int)

    years = sorted(tmp[wave_col].unique())

    wave_counts = (
        tmp.groupby([wave_col, "urban_group"])[id_col]
        .nunique()
        .unstack("urban_group")
        .reindex(years)
        .fillna(0)
        .astype(int)
    )
    if 0 not in wave_counts.columns:
        wave_counts[0] = 0
    if 1 not in wave_counts.columns:
        wave_counts[1] = 0
    wave_counts = wave_counts[[0, 1]]  # 0 rural, 1 urban

    wave_rural = wave_counts[0].values
    wave_urban = wave_counts[1].values

    # cumulative unique: first appearance wave per household (with fixed group)
    pid_first = tmp.groupby(id_col).agg(
        first_year=(wave_col, "min"),
        group=("urban_group", "first"),
    )
    first_urban = pid_first.loc[pid_first["group"] == 1, "first_year"]
    first_rural = pid_first.loc[pid_first["group"] == 0, "first_year"]

    cum_urban = [int((first_urban <= y).sum()) for y in years]
    cum_rural = [int((first_rural <= y).sum()) for y in years]
    cum_total = [int((pid_first["first_year"] <= y).sum()) for y in years]

    out = pd.DataFrame(
        {
            "year": years,
            "wave_rural_unique": wave_rural,
            "wave_urban_unique": wave_urban,
            "wave_total_unique": wave_rural + wave_urban,
            "cum_rural_unique": cum_rural,
            "cum_urban_unique": cum_urban,
            "cum_total_unique": cum_total,
        }
    )
    return out


def plot_wave_stacked_with_cum_lines(
    summary_df: pd.DataFrame,
    out_dir: Path,
    fig_name: str = "wave_stacked_with_cum_urban_rural.png",
) -> None:
    years = summary_df["year"].tolist()
    x_pos = list(range(len(years)))

    wave_rural = summary_df["wave_rural_unique"].tolist()
    wave_urban = summary_df["wave_urban_unique"].tolist()
    total_wave = summary_df["wave_total_unique"].tolist()
    cum_rural = summary_df["cum_rural_unique"].tolist()
    cum_urban = summary_df["cum_urban_unique"].tolist()

    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    bar_width = 0.45

    ax1.bar(
        x_pos,
        wave_rural,
        width=bar_width,
        label="Rural wave unique",
        color=RURAL_COLOR,
    )
    ax1.bar(
        x_pos,
        wave_urban,
        width=bar_width,
        bottom=wave_rural,
        label="Urban wave unique",
        color=URBAN_COLOR,
    )

    ax1.set_xlabel("Survey wave (year)")
    ax1.set_ylabel("Wave unique households")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([str(y) for y in years])

    max_wave = max(total_wave) if total_wave else 0
    ax1.set_ylim(0, int(np.ceil(max_wave * 1.15)) if max_wave else 1)

    # total labels above bars
    label_offset = 0.02 * max_wave if max_wave > 0 else 0
    for x, total in zip(x_pos, total_wave):
        ax1.text(x, total + label_offset, f"{total:,}", ha="center", va="bottom", fontsize=9)

    ax2 = ax1.twinx()
    ax2.plot(x_pos, cum_rural, marker="o", label="Rural cumulative unique", color=RURAL_COLOR)
    ax2.plot(x_pos, cum_urban, marker="o", label="Urban cumulative unique", color=URBAN_COLOR)
    ax2.set_ylabel("Cumulative unique households")

    # merged legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(0.02, 0.99), frameon=False)

    plt.tight_layout()
    save_fig(fig, out_dir / fig_name, dpi=300)
    plt.show()
    plt.close(fig)


# =========================
# 4) FE boxplots (obs per cluster / cell)
# =========================
def winsorize_upper(x: pd.Series, q: float = 0.99) -> np.ndarray:
    x = pd.to_numeric(x, errors="coerce").dropna().to_numpy()
    if x.size == 0:
        return x
    cap = float(np.quantile(x, q))
    return np.minimum(x, cap)


def fe_count_series(
    df: pd.DataFrame,
    county_col: str = "county_code",
    edu_year_col: str = "edu_year",
    is_rural_hh_col: str = "is_rural_hh",
) -> dict[str, pd.Series]:
    d = df.copy()
    d[is_rural_hh_col] = pd.to_numeric(d[is_rural_hh_col], errors="coerce")
    d_r = d[d[is_rural_hh_col] == 1]
    d_u = d[d[is_rural_hh_col] == 0]

    return {
        "obs_per_county_all": d.groupby(county_col).size(),
        "obs_per_county_rural": d_r.groupby(county_col).size(),
        "obs_per_county_urban": d_u.groupby(county_col).size(),
        "obs_per_county_year_all": d.groupby([county_col, edu_year_col]).size(),
        "obs_per_county_year_rural": d_r.groupby([county_col, edu_year_col]).size(),
        "obs_per_county_year_urban": d_u.groupby([county_col, edu_year_col]).size(),
    }


def plot_fe_boxplot_counts(
    series_all: pd.Series,
    series_rural: pd.Series,
    series_urban: pd.Series,
    title: str,
    out_dir: Path,
    fig_name: str,
    winsor_q: float = 0.99,
    log1p_transform: bool = True,
    whis: tuple[int, int] = (5, 95),
    showmeans: bool = True,
) -> None:
    a = winsorize_upper(series_all, winsor_q)
    r = winsorize_upper(series_rural, winsor_q)
    u = winsorize_upper(series_urban, winsor_q)

    if log1p_transform:
        a, r, u = np.log1p(a), np.log1p(r), np.log1p(u)
        ylab = "log(1 + count) (winsorized)"
    else:
        ylab = "count (winsorized)"

    fig, ax = plt.subplots(figsize=(7.0, 4.2))

    # Matplotlib 3.9+: tick_labels (not labels)
    ax.boxplot(
        [a, r, u],
        tick_labels=["All", "Rural", "Urban"],
        showfliers=False,
        widths=0.5,
        whis=whis,          # percentile whiskers, sampling-style
        showmeans=showmeans,
        meanline=False,
    )

    ax.set_title(title)
    ax.set_ylabel(ylab)

    plt.tight_layout()
    save_fig(fig, out_dir / fig_name, dpi=300)
    plt.show()
    plt.close(fig)


# =========================
# 5) Forest plot (SMD standardized)
# =========================
def smd_diff_ci(x_urban: pd.Series, x_rural: pd.Series, z: float = 1.96) -> dict:
    """
    Standardized Mean Difference (Urban - Rural) with approximate 95% CI.

    SMD = (mu_u - mu_r) / s_pooled
    SE(SMD) approx = SE(diff) / s_pooled
    SE(diff)=sqrt(su^2/nu + sr^2/nr)
    """
    u = pd.to_numeric(x_urban, errors="coerce").dropna()
    r = pd.to_numeric(x_rural, errors="coerce").dropna()

    nu, nr = int(u.shape[0]), int(r.shape[0])
    if nu < 2 or nr < 2:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    mu, mr = float(u.mean()), float(r.mean())
    su = float(u.std(ddof=1))
    sr = float(r.std(ddof=1))

    denom = nu + nr - 2
    sp2 = ((nu - 1) * su**2 + (nr - 1) * sr**2) / denom if denom > 0 else np.nan
    sp = float(np.sqrt(sp2)) if np.isfinite(sp2) and sp2 > 0 else np.nan
    if not np.isfinite(sp) or sp == 0:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    diff_raw = mu - mr
    se_diff = np.sqrt(su**2 / nu + sr**2 / nr)
    smd = diff_raw / sp
    se_smd = se_diff / sp

    return {
        "n_u": nu,
        "n_r": nr,
        "diff": smd,
        "ci_low": smd - z * se_smd,
        "ci_high": smd + z * se_smd,
    }


def build_forest_df_smd(
    df: pd.DataFrame,
    var_specs: list[tuple[str, str]],
    is_rural_hh_col: str = "is_rural_hh",
) -> pd.DataFrame:
    tmp = df.copy()
    tmp[is_rural_hh_col] = pd.to_numeric(tmp[is_rural_hh_col], errors="coerce")
    d_u = tmp[tmp[is_rural_hh_col] == 0]
    d_r = tmp[tmp[is_rural_hh_col] == 1]

    rows = []
    for var, label in var_specs:
        if var not in tmp.columns:
            continue
        stat = smd_diff_ci(d_u[var], d_r[var])
        rows.append(
            {
                "variable": var,
                "label": label,
                "diff": stat["diff"],
                "ci_low": stat["ci_low"],
                "ci_high": stat["ci_high"],
                "n_urban": stat["n_u"],
                "n_rural": stat["n_r"],
            }
        )
    return pd.DataFrame(rows)


def plot_forest_smd(
    forest_df: pd.DataFrame,
    out_dir: Path,
    fig_base: str = FOREST_BASENAME,
) -> None:
    d = forest_df.dropna(subset=["diff", "ci_low", "ci_high"]).copy()
    if d.empty:
        raise ValueError("No valid rows for forest plot after dropping NA.")

    # top-to-bottom in listed order
    d = d.iloc[::-1].reset_index(drop=True)

    y = np.arange(d.shape[0])
    x = d["diff"].to_numpy()
    xerr_low = x - d["ci_low"].to_numpy()
    xerr_high = d["ci_high"].to_numpy() - x
    xerr = np.vstack([xerr_low, xerr_high])

    fig, ax = plt.subplots(figsize=(10.5, 4.8))

    # 0 line: red dashed (required)
    ax.axvline(0.0, color="red", linestyle="--", linewidth=1.2, zorder=0)

    # error bars: black (required)
    ax.errorbar(
        x,
        y,
        xerr=xerr,
        fmt="o",
        ecolor="black",
        color="black",
        elinewidth=1.2,
        capsize=4,
        capthick=1.2,
        markersize=5.5,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(d["label"].tolist())
    ax.set_xlabel("SMD (Urban − Rural), 95% CI")
    ax.set_title("Urban − Rural differences (standardized)")

    plt.tight_layout()

    # save PNG + SVG
    save_fig(fig, out_dir / f"{fig_base}.png", dpi=300)
    save_fig(fig, out_dir / f"{fig_base}.svg", dpi=300)

    plt.show()
    plt.close(fig)


# =========================
# 6) Main (end-to-end)
# =========================
def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    print("[INFO] Notebook progress message.")

    # household-stable rural/urban flag (fixes NA ambiguity)
    df0 = make_household_rural_flag(df0, id_col="家庭ID", is_rural_col="is_rural", out_col="is_rural_hh")

    # mechanism core sample (the one you actually use)
    df_core = build_mechanism_core_sample(df0)
    print("[INFO] Notebook progress message.")

    # --- 1) wave stacked + cumulative ---
    summary = build_stacked_wave_and_cum_summary(df_core, id_col="家庭ID", wave_col="wave", is_rural_hh_col="is_rural_hh")
    print("[INFO] Wave summary:")
    print(summary.to_string(index=False))
    plot_wave_stacked_with_cum_lines(summary, out_dir=OUT_DIR)

    # --- 2) FE boxplots: obs per county / county×edu_year ---
    counts = fe_count_series(df_core, county_col="county_code", edu_year_col="edu_year", is_rural_hh_col="is_rural_hh")

    plot_fe_boxplot_counts(
        counts["obs_per_county_all"],
        counts["obs_per_county_rural"],
        counts["obs_per_county_urban"],
        title="Observations per county",
        out_dir=OUT_DIR,
        fig_name="fe_boxplot_obs_per_county.png",
        winsor_q=BOX_WINSOR_Q,
        log1p_transform=BOX_LOG1P,
        whis=BOX_WHIS,
        showmeans=BOX_SHOWMEANS,
    )

    plot_fe_boxplot_counts(
        counts["obs_per_county_year_all"],
        counts["obs_per_county_year_rural"],
        counts["obs_per_county_year_urban"],
        title="Observations per county×edu_year cell",
        out_dir=OUT_DIR,
        fig_name="fe_boxplot_obs_per_county_year.png",
        winsor_q=BOX_WINSOR_Q,
        log1p_transform=BOX_LOG1P,
        whis=BOX_WHIS,
        showmeans=BOX_SHOWMEANS,
    )

    # --- 3) forest plot: standardized urban-rural differences (SMD) ---
    var_specs = [
        ("has_edu_spend", "Any education training spending (extensive, 0/1)"),
        ("edu_train_total", "Education training spending amount (RMB)"),
        ("has_edu_debt", "Any education-related debt (extensive, 0/1)"),
        ("edu_debt_balance", "Education debt balance (RMB)"),
        ("income", "Household disposable income (RMB)"),
    ]
    forest_df = build_forest_df_smd(df_core, var_specs, is_rural_hh_col="is_rural_hh")
    plot_forest_smd(forest_df, out_dir=OUT_DIR, fig_base=FOREST_BASENAME)

    print("[DONE] All figures generated.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_DIR  = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")

VALID_EDU_YEARS = [2010, 2012, 2014]  # set None to disable restriction

RURAL_COLOR = "#f1a340"
URBAN_COLOR = "#998ec3"


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


# =========================
# Data loading + core sample
# =========================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份", "county_code", "是否农村",
            "是否有15岁及以下儿童",
            "家庭可支配收入（元）", "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）", "教育负债余额（元）",
            "教育培训支出口径年份", "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    out = df.copy()
    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()  # NaN if all NA
    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["county_code", "edu_year"]).copy()

    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()

    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# Wave summary + plot
# =========================
def build_stacked_wave_and_cum_summary(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    wave_col: str = "wave",
    is_rural_hh_col: str = "is_rural_hh",
) -> pd.DataFrame:
    tmp = df[[id_col, wave_col, is_rural_hh_col]].copy()
    tmp[wave_col] = pd.to_numeric(tmp[wave_col], errors="coerce")
    tmp = tmp.dropna(subset=[wave_col])
    tmp[wave_col] = tmp[wave_col].astype(int)

    tmp[is_rural_hh_col] = pd.to_numeric(tmp[is_rural_hh_col], errors="coerce")
    tmp = tmp[tmp[is_rural_hh_col].isin([0, 1])].copy()

    # urban_group: 1 urban, 0 rural
    tmp["urban_group"] = (tmp[is_rural_hh_col] == 0).astype(int)

    years = sorted(tmp[wave_col].unique())

    wave_counts = (
        tmp.groupby([wave_col, "urban_group"])[id_col]
        .nunique()
        .unstack("urban_group")
        .reindex(years)
        .fillna(0)
        .astype(int)
    )
    if 0 not in wave_counts.columns:
        wave_counts[0] = 0
    if 1 not in wave_counts.columns:
        wave_counts[1] = 0
    wave_counts = wave_counts[[0, 1]]

    wave_rural = wave_counts[0].values
    wave_urban = wave_counts[1].values

    pid_first = tmp.groupby(id_col).agg(
        first_year=(wave_col, "min"),
        group=("urban_group", "first"),
    )
    first_urban = pid_first.loc[pid_first["group"] == 1, "first_year"]
    first_rural = pid_first.loc[pid_first["group"] == 0, "first_year"]

    cum_urban = [int((first_urban <= y).sum()) for y in years]
    cum_rural = [int((first_rural <= y).sum()) for y in years]
    cum_total = [int((pid_first["first_year"] <= y).sum()) for y in years]

    return pd.DataFrame(
        {
            "year": years,
            "wave_rural_unique": wave_rural,
            "wave_urban_unique": wave_urban,
            "wave_total_unique": wave_rural + wave_urban,
            "cum_rural_unique": cum_rural,
            "cum_urban_unique": cum_urban,
            "cum_total_unique": cum_total,
        }
    )


def plot_wave_stacked_with_cum_lines(
    summary_df: pd.DataFrame,
    out_dir: Path,
    fig_name: str = "wave_stacked_with_cum_urban_rural.png",
) -> None:
    years = summary_df["year"].tolist()
    x_pos = list(range(len(years)))

    wave_rural = summary_df["wave_rural_unique"].tolist()
    wave_urban = summary_df["wave_urban_unique"].tolist()
    total_wave = summary_df["wave_total_unique"].tolist()
    cum_rural = summary_df["cum_rural_unique"].tolist()
    cum_urban = summary_df["cum_urban_unique"].tolist()

    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))
    bar_width = 0.45

    ax1.bar(
        x_pos, wave_rural, width=bar_width,
        label="Rural wave unique", color=RURAL_COLOR
    )
    ax1.bar(
        x_pos, wave_urban, width=bar_width, bottom=wave_rural,
        label="Urban wave unique", color=URBAN_COLOR
    )

    ax1.set_xlabel("Survey wave (year)", fontsize=16)
    ax1.set_ylabel("Wave unique households", fontsize=16)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([str(y) for y in years])

    max_wave = max(total_wave) if total_wave else 0
    ax1.set_ylim(0, int(np.ceil(max_wave * 1.15)) if max_wave else 1)

    label_offset = 0.02 * max_wave if max_wave > 0 else 0
    for x, total in zip(x_pos, total_wave):
        ax1.text(x, total + label_offset, f"{total:,}", ha="center", va="bottom", fontsize=10)

    ax2 = ax1.twinx()
    ax2.plot(x_pos, cum_rural, marker="o", label="Rural cumulative unique", color=RURAL_COLOR)
    ax2.plot(x_pos, cum_urban, marker="o", label="Urban cumulative unique", color=URBAN_COLOR)
    ax2.set_ylabel("Cumulative unique households", fontsize=16)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(0.02, 0.99), frameon=False, fontsize=12)

    plt.tight_layout()
    save_fig(fig, out_dir / fig_name, dpi=300)
    plt.show()
    plt.close(fig)


def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    df0 = make_household_rural_flag(df0, out_col="is_rural_hh")
    df_core = build_mechanism_core_sample(df0)

    summary = build_stacked_wave_and_cum_summary(df_core)
    print("[INFO] Wave summary:")
    print(summary.to_string(index=False))

    plot_wave_stacked_with_cum_lines(summary, OUT_DIR)
    print("[DONE] Wave figure generated.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_DIR  = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")

VALID_EDU_YEARS = [2010, 2012, 2014]  # set None to disable restriction

# Robust transform (keep your original intent)
BOX_WINSOR_Q = 0.99
BOX_LOG1P = True

# If you want "sampling-style" whiskers, keep percentile whiskers:
BOX_WHIS = (5, 95)
# If you prefer classical Tukey whiskers, use:
# BOX_WHIS = 1.5

# Style (borrowed from your reference)
BOX_FACE = {"all": "#cde7f0", "rural": "#fdbf6f", "urban": "#cab2d6"}
LINE_COL = {"all": "#3d7da9", "rural": "#ff7f00", "urban": "#6a3d9a"}

BOX_ALPHA = 0.55
BOX_LW = 1.0
MED_LW = 1.0
WHISK_LW = 1.0
CAP_LW = 1.0
WHISK_LS = "--"  # dashed whiskers

GROUP_ORDER = ("all", "rural", "urban")


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


# =========================
# Data loading + core sample
# =========================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份", "county_code", "是否农村",
            "是否有15岁及以下儿童",
            "教育培训支出口径年份", "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Household-stable rural/urban classification robust to NA.
    """
    out = df.copy()
    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()  # NaN if all NA
    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["county_code", "edu_year"]).copy()

    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()

    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# FE distributions
# =========================
def fe_count_series(
    df: pd.DataFrame,
    county_col: str = "county_code",
    edu_year_col: str = "edu_year",
    is_rural_hh_col: str = "is_rural_hh",
) -> dict[str, dict[str, np.ndarray]]:
    """
    Return distributions for 3 groups (all/rural/urban) as numpy arrays.
    """
    d = df.copy()
    d[is_rural_hh_col] = pd.to_numeric(d[is_rural_hh_col], errors="coerce")

    d_all = d
    d_r = d[d[is_rural_hh_col] == 1]
    d_u = d[d[is_rural_hh_col] == 0]

    # series of counts
    s_county_all = d_all.groupby(county_col).size()
    s_county_r = d_r.groupby(county_col).size()
    s_county_u = d_u.groupby(county_col).size()

    s_cell_all = d_all.groupby([county_col, edu_year_col]).size()
    s_cell_r = d_r.groupby([county_col, edu_year_col]).size()
    s_cell_u = d_u.groupby([county_col, edu_year_col]).size()

    return {
        "obs_per_county": {
            "all": s_county_all.astype(float).to_numpy(),
            "rural": s_county_r.astype(float).to_numpy(),
            "urban": s_county_u.astype(float).to_numpy(),
        },
        "obs_per_county_year": {
            "all": s_cell_all.astype(float).to_numpy(),
            "rural": s_cell_r.astype(float).to_numpy(),
            "urban": s_cell_u.astype(float).to_numpy(),
        },
    }


def winsorize_upper_np(x: np.ndarray, q: float = 0.99) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return x
    cap = float(np.quantile(x, q))
    return np.minimum(x, cap)


def transform_box_data(
    data_dict: dict[str, np.ndarray],
    winsor_q: float = 0.99,
    log1p_transform: bool = True,
) -> dict[str, np.ndarray]:
    out = {}
    for g, arr in data_dict.items():
        z = winsorize_upper_np(arr, winsor_q)
        if log1p_transform:
            z = np.log1p(z)
        out[g] = z
    return out


def style_boxplot_artists(bp, labels: list[str]) -> None:
    """
    Apply the reference style:
        - face color with alpha
        - edges/whiskers/caps/median in LINE_COL
        - dashed whiskers
    """
    n = len(labels)

    # boxes + medians
    for i in range(n):
        g = labels[i]
        box = bp["boxes"][i]
        box.set_facecolor(BOX_FACE[g])
        box.set_alpha(BOX_ALPHA)
        box.set_edgecolor(LINE_COL[g])
        box.set_linewidth(BOX_LW)

        med = bp["medians"][i]
        med.set_color(LINE_COL[g])
        med.set_linewidth(MED_LW)

    # whiskers + caps (2 per group)
    for i in range(n):
        g = labels[i]
        w1 = bp["whiskers"][2 * i]
        w2 = bp["whiskers"][2 * i + 1]
        for w in (w1, w2):
            w.set_color(LINE_COL[g])
            w.set_linewidth(WHISK_LW)
            w.set_linestyle(WHISK_LS)

        c1 = bp["caps"][2 * i]
        c2 = bp["caps"][2 * i + 1]
        for c in (c1, c2):
            c.set_color(LINE_COL[g])
            c.set_linewidth(CAP_LW)


def boxplot_3groups(
    data_dict: dict[str, np.ndarray],
    title: str,
    ylabel: str,
    out_path: Path,
    order: tuple[str, str, str] = GROUP_ORDER,
    figsize: tuple[float, float] = (6.6, 3.9),
    dpi: int = 300,
    whis=BOX_WHIS,
) -> None:
    labels = list(order)
    positions = np.arange(1, len(labels) + 1)

    data_for_box = []
    for g in labels:
        x = np.asarray(data_dict.get(g, np.array([])), dtype=float)
        x = x[~np.isnan(x)]
        data_for_box.append(x)

    fig, ax = plt.subplots(figsize=figsize)

    bp = ax.boxplot(
        data_for_box,
        positions=positions,
        widths=0.22,
        patch_artist=True,
        showfliers=False,
        whis=whis,  # can be (5,95) percentile whiskers or 1.5
        boxprops=dict(linewidth=BOX_LW),
        medianprops=dict(linewidth=MED_LW),
        whiskerprops=dict(linewidth=WHISK_LW),
        capprops=dict(linewidth=CAP_LW),
    )

    style_boxplot_artists(bp, labels)

    pretty = {"all": "All", "rural": "Rural", "urban": "Urban"}
    ax.set_xticks(positions)
    ax.set_xticklabels([pretty[g] for g in labels], fontsize=16)

    ax.set_ylabel(ylabel, fontsize=16)
    ax.tick_params(axis="y", labelsize=13)
    ax.set_title(title, fontsize=15, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_fig(fig, out_path, dpi=dpi)
    plt.show()
    plt.close(fig)


# =========================
# Main
# =========================
def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    df0 = make_household_rural_flag(df0, out_col="is_rural_hh")
    df_core = build_mechanism_core_sample(df0)

    dist = fe_count_series(df_core)

    # obs per county
    d1 = transform_box_data(dist["obs_per_county"], winsor_q=BOX_WINSOR_Q, log1p_transform=BOX_LOG1P)
    ylab1 = "log(1 + observations) (winsorized)" if BOX_LOG1P else "observations (winsorized)"
    boxplot_3groups(
        data_dict=d1,
        title="Sample Size per County",
        ylabel=ylab1,
        out_path=OUT_DIR / "fe_boxplot_obs_per_county.png",
        whis=BOX_WHIS,
        figsize=(6.6, 3.9),
    )

    # obs per county × edu_year
    d2 = transform_box_data(dist["obs_per_county_year"], winsor_q=BOX_WINSOR_Q, log1p_transform=BOX_LOG1P)
    ylab2 = "log(1 + observations) (winsorized)" if BOX_LOG1P else "observations (winsorized)"
    boxplot_3groups(
        data_dict=d2,
        title="Sample Size per County × edu_year Cell",
        ylabel=ylab2,
        out_path=OUT_DIR / "fe_boxplot_obs_per_county_year.png",
        whis=BOX_WHIS,
        figsize=(6.9, 3.9),
    )

    print("[DONE] FE boxplots generated.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 24
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_DIR  = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")

VALID_EDU_YEARS = [2010, 2012, 2014]  # set None to disable restriction
FIG_BASE = "forest_urban_minus_rural_standardized"


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


# =========================
# Data loading + core sample
# =========================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份", "county_code", "是否农村",
            "是否有15岁及以下儿童",
            "家庭可支配收入（元）", "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）", "教育负债余额（元）",
            "教育培训支出口径年份", "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])
    df["is_rural"] = safe_int64(df["是否农村"]) if "是否农村" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")

    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    # mechanism vars
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)

    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))

    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
    else:
        df["edu_debt_balance"] = np.nan

    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    out = df.copy()
    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()
    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["county_code", "edu_year"]).copy()

    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()

    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# SMD + forest plotting
# =========================
def smd_diff_ci(x_urban: pd.Series, x_rural: pd.Series, z: float = 1.96) -> dict:
    u = pd.to_numeric(x_urban, errors="coerce").dropna()
    r = pd.to_numeric(x_rural, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])

    if nu < 2 or nr < 2:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    mu, mr = float(u.mean()), float(r.mean())
    su = float(u.std(ddof=1))
    sr = float(r.std(ddof=1))

    denom = nu + nr - 2
    sp2 = ((nu - 1) * su**2 + (nr - 1) * sr**2) / denom if denom > 0 else np.nan
    sp = float(np.sqrt(sp2)) if np.isfinite(sp2) and sp2 > 0 else np.nan
    if not np.isfinite(sp) or sp == 0:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    diff_raw = mu - mr
    se_diff = np.sqrt(su**2 / nu + sr**2 / nr)

    smd = diff_raw / sp
    se_smd = se_diff / sp

    return {
        "n_u": nu,
        "n_r": nr,
        "diff": smd,
        "ci_low": smd - z * se_smd,
        "ci_high": smd + z * se_smd,
    }


def build_forest_df_smd(
    df: pd.DataFrame,
    var_specs: list[tuple[str, str]],
    is_rural_hh_col: str = "is_rural_hh",
) -> pd.DataFrame:
    tmp = df.copy()
    tmp[is_rural_hh_col] = pd.to_numeric(tmp[is_rural_hh_col], errors="coerce")
    d_u = tmp[tmp[is_rural_hh_col] == 0]
    d_r = tmp[tmp[is_rural_hh_col] == 1]

    rows = []
    for var, label in var_specs:
        if var not in tmp.columns:
            continue
        stat = smd_diff_ci(d_u[var], d_r[var])
        rows.append(
            {
                "variable": var,
                "label": label,
                "diff": stat["diff"],
                "ci_low": stat["ci_low"],
                "ci_high": stat["ci_high"],
                "n_urban": stat["n_u"],
                "n_rural": stat["n_r"],
            }
        )
    return pd.DataFrame(rows)


def plot_forest_smd(
    forest_df: pd.DataFrame,
    out_dir: Path,
    fig_base: str = FIG_BASE,
) -> None:
    d = forest_df.dropna(subset=["diff", "ci_low", "ci_high"]).copy()
    if d.empty:
        raise ValueError("No valid rows for forest plot after dropping NA.")

    d = d.iloc[::-1].reset_index(drop=True)

    y = np.arange(d.shape[0])
    x = d["diff"].to_numpy()
    xerr_low = x - d["ci_low"].to_numpy()
    xerr_high = d["ci_high"].to_numpy() - x
    xerr = np.vstack([xerr_low, xerr_high])

    fig, ax = plt.subplots(figsize=(10.5, 4.8))

    ax.axvline(0.0, color="red", linestyle="--", linewidth=1.2, zorder=0)

    ax.errorbar(
        x, y, xerr=xerr,
        fmt="o",
        ecolor="black",
        color="black",
        elinewidth=1.2,
        capsize=4,
        capthick=1.2,
        markersize=5.5,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(d["label"].tolist())
    ax.set_xlabel("SMD (Urban − Rural), 95% CI")
    ax.set_title("Urban − Rural differences (standardized)")

    plt.tight_layout()

    save_fig(fig, out_dir / f"{fig_base}.png", dpi=300)
    save_fig(fig, out_dir / f"{fig_base}.svg", dpi=300)

    plt.show()
    plt.close(fig)


def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    df0 = make_household_rural_flag(df0, out_col="is_rural_hh")
    df_core = build_mechanism_core_sample(df0)

    var_specs = [
        ("has_edu_spend", "has_edu_investment"),
        ("edu_train_total", "edu_train_total"),
        ("has_edu_debt", "has_edu_debt"),
        ("edu_debt_balance", "edu_debt_balance"),
        ("income", "income"),
    ]

    forest_df = build_forest_df_smd(df_core, var_specs)
    plot_forest_smd(forest_df, OUT_DIR, fig_base=FIG_BASE)

    print("[DONE] Forest plot generated.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 25
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_chfs_descriptive_figures.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""


from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Config
# =========================
CHFS_XLSX = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS\CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx")
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\CHFS")

VALID_EDU_YEARS = [2010, 2012, 2014]  # set None to disable restriction

FIG_BASE = "forest_urban_minus_rural_standardized_vertical"

# x-axis label rotation
X_LABEL_ROT = 25


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


# =========================
# Data loading + core sample
# =========================
def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_int64(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_chfs_and_construct_vars(chfs_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(chfs_xlsx)

    df = ensure_numeric(
        df,
        [
            "来源年份",
            "county_code",
            "是否农村",
            "是否有15岁及以下儿童",
            "家庭可支配收入（元）",
            "去年教育培训支出（元）",
            "是否有教育负债（原始码1/2）",
            "教育负债余额（元）",
            "教育培训支出口径年份",
            "收入口径年份",
        ],
    )

    if "家庭ID" not in df.columns:
        raise KeyError("Missing column: 家庭ID")
    if "来源年份" not in df.columns:
        raise KeyError("Missing column: 来源年份")
    if "county_code" not in df.columns:
        raise KeyError("Missing column: county_code")

    # IDs
    df["wave"] = safe_int64(df["来源年份"])
    df["county_code"] = safe_int64(df["county_code"])

    # time-varying rural (0/1/NA)
    df["is_rural"] = (
        safe_int64(df["是否农村"])
        if "是否农村" in df.columns
        else pd.Series(pd.NA, index=df.index, dtype="Int64")
    )

    # children indicator
    tmp_child = pd.to_numeric(df.get("是否有15岁及以下儿童"), errors="coerce")
    df["has_u15_child"] = np.where(tmp_child == 1, 1, np.where(tmp_child == 0, 0, np.nan))

    # edu_year
    edu_year = pd.to_numeric(df.get("教育培训支出口径年份"), errors="coerce")
    edu_year2 = pd.to_numeric(df.get("收入口径年份"), errors="coerce")
    df["edu_year"] = safe_int64(pd.Series(edu_year).fillna(edu_year2))

    # mechanism vars
    df["income"] = pd.to_numeric(df.get("家庭可支配收入（元）"), errors="coerce").clip(lower=0)

    df["edu_train_total"] = pd.to_numeric(df.get("去年教育培训支出（元）"), errors="coerce").clip(lower=0)
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype("Int64")

    raw_debt = pd.to_numeric(df.get("是否有教育负债（原始码1/2）"), errors="coerce")
    df["has_edu_debt"] = np.where(raw_debt == 1, 1, np.where(raw_debt == 2, 0, np.nan))

    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(df["教育负债余额（元）"], errors="coerce").clip(lower=0)
    else:
        df["edu_debt_balance"] = np.nan

    # essential
    df = df.dropna(subset=["家庭ID", "wave"]).copy()
    return df


def make_household_rural_flag(
    df: pd.DataFrame,
    id_col: str = "家庭ID",
    is_rural_col: str = "is_rural",
    out_col: str = "is_rural_hh",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Household-stable rural flag robust to NA:
        mean(is_rural) ignoring NA:
            > threshold => 1 (rural)
            < threshold => 0 (urban)
            else => NA
    """
    out = df.copy()

    tmp = out[[id_col, is_rural_col]].copy()
    tmp[is_rural_col] = pd.to_numeric(tmp[is_rural_col], errors="coerce")

    g = tmp.groupby(id_col)[is_rural_col].mean()  # NaN if all missing

    cond_r = g.notna() & (g > threshold)
    cond_u = g.notna() & (g < threshold)

    hh = pd.Series(np.nan, index=g.index, dtype="float64")
    hh.loc[cond_r] = 1.0
    hh.loc[cond_u] = 0.0

    out = out.merge(hh.rename(out_col), on=id_col, how="left")
    return out


def build_mechanism_core_sample(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["county_code", "edu_year"]).copy()

    if VALID_EDU_YEARS is not None:
        d = d[d["edu_year"].isin(VALID_EDU_YEARS)].copy()

    d = d[pd.to_numeric(d["has_u15_child"], errors="coerce") == 1].copy()

    d["is_rural_hh"] = pd.to_numeric(d["is_rural_hh"], errors="coerce")
    d = d[d["is_rural_hh"].isin([0, 1])].copy()
    return d


# =========================
# SMD + forest plotting
# =========================
def smd_diff_ci(x_urban: pd.Series, x_rural: pd.Series, z: float = 1.96) -> dict:
    """
    Standardized Mean Difference (Urban - Rural) with approx 95% CI.

    SMD = (mu_u - mu_r) / s_pooled
    SE(SMD) approx = SE(diff) / s_pooled
    """
    u = pd.to_numeric(x_urban, errors="coerce").dropna()
    r = pd.to_numeric(x_rural, errors="coerce").dropna()
    nu, nr = int(u.shape[0]), int(r.shape[0])

    if nu < 2 or nr < 2:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    mu, mr = float(u.mean()), float(r.mean())
    su = float(u.std(ddof=1))
    sr = float(r.std(ddof=1))

    denom = nu + nr - 2
    sp2 = ((nu - 1) * su**2 + (nr - 1) * sr**2) / denom if denom > 0 else np.nan
    sp = float(np.sqrt(sp2)) if np.isfinite(sp2) and sp2 > 0 else np.nan
    if not np.isfinite(sp) or sp == 0:
        return {"n_u": nu, "n_r": nr, "diff": np.nan, "ci_low": np.nan, "ci_high": np.nan}

    diff_raw = mu - mr
    se_diff = np.sqrt(su**2 / nu + sr**2 / nr)

    smd = diff_raw / sp
    se_smd = se_diff / sp

    return {
        "n_u": nu,
        "n_r": nr,
        "diff": smd,
        "ci_low": smd - z * se_smd,
        "ci_high": smd + z * se_smd,
    }


def build_forest_df_smd(
    df: pd.DataFrame,
    var_specs: list[tuple[str, str]],
    is_rural_hh_col: str = "is_rural_hh",
) -> pd.DataFrame:
    tmp = df.copy()
    tmp[is_rural_hh_col] = pd.to_numeric(tmp[is_rural_hh_col], errors="coerce")
    d_u = tmp[tmp[is_rural_hh_col] == 0]
    d_r = tmp[tmp[is_rural_hh_col] == 1]

    rows = []
    for var, label in var_specs:
        if var not in tmp.columns:
            continue
        stat = smd_diff_ci(d_u[var], d_r[var])
        rows.append(
            {
                "variable": var,   # raw code (for right side)
                "label": label,    # display label (for bottom)
                "diff": stat["diff"],
                "ci_low": stat["ci_low"],
                "ci_high": stat["ci_high"],
                "n_urban": stat["n_u"],
                "n_rural": stat["n_r"],
            }
        )
    return pd.DataFrame(rows)


def plot_forest_smd_vertical(
    forest_df: pd.DataFrame,
    out_dir: Path,
    fig_base: str = FIG_BASE,
    x_label_rotation: int = X_LABEL_ROT,
) -> None:
    """
    Vertical layout:
        - x-axis: labels (bottom)
        - y-axis: SMD
        - right side: raw variable codes, aligned at each point's y position
    """
    d = forest_df.dropna(subset=["diff", "ci_low", "ci_high"]).copy()
    if d.empty:
        raise ValueError("No valid rows for forest plot after dropping NA.")

    d = d.reset_index(drop=True)

    x = np.arange(d.shape[0])
    y = d["diff"].to_numpy()
    yerr_low = y - d["ci_low"].to_numpy()
    yerr_high = d["ci_high"].to_numpy() - y
    yerr = np.vstack([yerr_low, yerr_high])

    fig, ax = plt.subplots(figsize=(10.0, 4.8))

    # 0 line (horizontal): red dashed (required)
    ax.axhline(0.0, color="red", linestyle="--", linewidth=1.2, zorder=0)

    # error bars: black (required)
    ax.errorbar(
        x, y, yerr=yerr,
        fmt="o",
        ecolor="black",
        color="black",
        elinewidth=1.2,
        capsize=4,
        capthick=1.2,
        markersize=5.5,
        zorder=3,
    )

    # bottom x labels (requested)
    ax.set_xticks(x)
    ax.set_xticklabels(d["label"].tolist(), rotation=x_label_rotation, ha="right")
    ax.set_xlabel("")  # keep clean

    # left y axis
    ax.set_ylabel("SMD (Urban − Rural), 95% CI")
    ax.set_title("Urban − Rural differences (standardized)")

    # grid for readability
    ax.spines["top"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.25)
    ax.set_axisbelow(True)

    # right-side variable codes (requested)
    ax_right = ax.twinx()
    ax_right.set_ylim(ax.get_ylim())

    # Put right ticks at the SAME y-values as the points to visually “attach” labels to points
    ax_right.set_yticks(y)
    ax_right.set_yticklabels(d["variable"].tolist())
    ax_right.set_ylabel("Variable code")

    # Tidy right axis appearance
    ax_right.spines["top"].set_visible(False)
    ax_right.tick_params(axis="y", which="both", length=0, labelsize=10)

    plt.tight_layout()

    save_fig(fig, out_dir / f"{fig_base}.png", dpi=300)
    save_fig(fig, out_dir / f"{fig_base}.svg", dpi=300)

    plt.show()
    plt.close(fig)


def main():
    print(f"[READ] {CHFS_XLSX}")
    df0 = load_chfs_and_construct_vars(CHFS_XLSX)
    df0 = make_household_rural_flag(df0, out_col="is_rural_hh")
    df_core = build_mechanism_core_sample(df0)

    # bottom label uses your requested names; right side uses raw variable codes
    var_specs = [
        ("has_edu_spend", "has_edu_investment"),
        ("edu_train_total", "edu_train_total"),
        ("has_edu_debt", "has_edu_debt"),
        ("edu_debt_balance", "edu_debt_balance"),
        ("income", "income"),
    ]

    forest_df = build_forest_df_smd(df_core, var_specs)
    plot_forest_smd_vertical(forest_df, OUT_DIR, fig_base=FIG_BASE)

    print("[DONE] Vertical forest plot generated.")


if __name__ == "__main__":
    main()
