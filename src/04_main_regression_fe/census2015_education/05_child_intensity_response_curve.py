#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG
# ================================

DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/storage_allT_betaT_BM"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True
# Original notebook comment normalized for the public code archive.
SAMPLES_URBAN = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

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
            except Exception:
                continue
    return sorted(ts) if ts else T_LIST_DEFAULT


def normalize_tidy(res):
    """Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    # Original notebook comment normalized for the public code archive.

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

    # Original notebook comment normalized for the public code archive.
    for c in ["M34", "M37", "M15", "M16"]:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.dropna(subset=["edu_years", main_share, main_years, "M2", "birth_year"])

    # Archived notebook metadata.
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)


def run_linear(dfm, main_share):
    """Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


# =============================================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def run_storage_linear_allT():
    print(f"[STEP] Load BM micro data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] raw shape={df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)
    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    all_rows = []

    for T in T_list:
        # Original notebook comment normalized for the public code archive.
        T_str = str(int(T)) if float(T).is_integer() else str(T)
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] Missing columns for T={T_str}: {main_share}/{main_years}")
            continue

        print("\n==============================")
        print(f"[PANEL] T={T_str} ({main_share}) BM")
        print("==============================")

        for su in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, su)
            print(f"[SAMPLE] {su}, N={len(dfm)}")
            if len(dfm) == 0:
                continue

            lin = run_linear(dfm, main_share)
            if lin is not None:
                all_rows.append({
                    "T": float(T),
                    "T_str": T_str,
                    "sample": su,
                    "Term": main_share,
                    **lin
                })

    df_lin = pd.DataFrame(all_rows)
    out_path = OUT_DIR / "storage_BM_linear_allT.csv"
    df_lin.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Saved linear results (all/rural/urban): {out_path}")
    print(df_lin.head())

    return df_lin


# ================================
# Original notebook comment normalized for the public code archive.
# ================================

def plot_beta_T_curve(df_lin: pd.DataFrame, sample: str):
    """Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no results; skip curve.")
        return

    sub = sub.sort_values("T")
    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)

    # Original notebook comment normalized for the public code archive.
    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    # Original notebook comment normalized for the public code archive.
    logT = np.log(T_vals)
    if len(T_vals) >= 3:
        X = np.column_stack([np.ones_like(logT), logT, logT**2])
        degree = 2
    elif len(T_vals) == 2:
        X = np.column_stack([np.ones_like(logT), logT])
        degree = 1
    else:
        X = np.ones((len(logT), 1))
        degree = 0

    import statsmodels.api as sm
    model = sm.WLS(est, X, weights=w)
    fit = model.fit()

    # Original notebook comment normalized for the public code archive.
    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

    print("[INFO] Notebook progress message.")
    print(fit.summary())

    # Original notebook comment normalized for the public code archive.
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), 200)
    T_grid = np.exp(logT_grid)

    def design_vec(lt: float) -> np.ndarray:
        if degree == 2:
            return np.array([1.0, lt, lt**2], dtype="float64")
        elif degree == 1:
            return np.array([1.0, lt], dtype="float64")
        else:
            return np.array([1.0], dtype="float64")

    beta_grid = []
    se_grid = []
    for lt in logT_grid:
        v = design_vec(lt)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)
        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.array(beta_grid)
    se_grid = np.array(se_grid)
    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    # Original notebook comment normalized for the public code archive.
    ci_pts_low = sub["CI_low"].to_numpy(float)
    ci_pts_high = sub["CI_high"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(T_grid, beta_grid, label="β(T) 估计")
    ax.fill_between(T_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([est - ci_pts_low, ci_pts_high - est])
    ax.errorbar(
        T_vals,
        est,
        yerr=yerr,
        fmt="o",
        capsize=4,
        color="black",
        linestyle="none",
        label="各返回期点 (原回归)",
    )

    # Original notebook comment normalized for the public code archive.
    y_min = min(ci_low.min(), ci_pts_low.min())
    y_max = max(ci_high.max(), ci_pts_high.max())
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.06 * (y_max - y_min if y_max > y_min else 1.0)
    y_range = (y_max - y_min) if y_max > y_min else 1.0
    offset = 0.04 * y_range

    for T, b, pv in zip(T_vals, est, p_vals):
        s = stars_for_p(pv)
        if s and np.isfinite(b):
            ax.text(
                T,
                b + offset,
                s,
                ha="center",
                va="bottom",
                fontsize=11,
            )

    # Original notebook comment normalized for the public code archive.
    ax.set_xscale("log")
    ax.set_xlim(T_min * 0.9, T_max * 1.1)
    # Original notebook comment normalized for the public code archive.
    tick_list = sorted(set(int(t) for t in T_vals))
    ax.set_xticks(tick_list)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.set_xlabel("洪水返回期 T（年，log 标度）")
    ax.set_ylabel("系数 β(T)：share_flood_ge_T 对 edu_years 的影响")
    ax.set_title(f"CaMa storage BM：洪水严重程度 T 的非线性效应 β(T)\n(sample={sample})")

    ax.legend()
    plt.tight_layout()

    fig_path = OUT_DIR / f"betaT_storage_BM_sample_{sample}.png"
    plt.savefig(fig_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved β(T) curve figure for sample={sample}: {fig_path}")


# ================================
# 4. main
# ================================

def main():
    df_lin = run_storage_linear_allT()
    if df_lin.empty:
        print("[WARN] No linear results; abort plotting.")
        return

    for sample in SAMPLES_URBAN:
        plot_beta_T_curve(df_lin, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.api as sm
from math import erf, sqrt

# =============================================================================
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/storage_allT_betaT_BM"
)
LIN_CSV = OUT_DIR / "storage_BM_linear_allT.csv"   # Original notebook comment normalized for the public code archive.
SAMPLES = ["all", "rural", "urban"]


# =============================================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / np.sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def plot_beta_T_curve(df_lin: pd.DataFrame, sample: str):
    """Archived notebook note for 05_child_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no results; skip.")
        return

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    ci_pts_low = sub["CI_low"].to_numpy(float)
    ci_pts_high = sub["CI_high"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)

    # Original notebook comment normalized for the public code archive.
    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    # Original notebook comment normalized for the public code archive.
    if len(T_vals) >= 3:
        X = np.column_stack([np.ones_like(logT), logT, logT**2])
        degree = 2
    elif len(T_vals) == 2:
        X = np.column_stack([np.ones_like(logT), logT])
        degree = 1
    else:
        X = np.ones((len(logT), 1))
        degree = 0

    model = sm.WLS(est, X, weights=w)
    fit = model.fit()

    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

    print("[INFO] Notebook progress message.")
    print(fit.summary())

    # Original notebook comment normalized for the public code archive.
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), 200)
    T_grid = np.exp(logT_grid)

    def design_vec(lt: float) -> np.ndarray:
        if degree == 2:
            return np.array([1.0, lt, lt**2], dtype="float64")
        elif degree == 1:
            return np.array([1.0, lt], dtype="float64")
        else:
            return np.array([1.0], dtype="float64")

    beta_grid = []
    se_grid = []
    for lt in logT_grid:
        v = design_vec(lt)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)
        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.array(beta_grid)
    se_grid = np.array(se_grid)
    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    # Original notebook comment normalized for the public code archive.
    ax.plot(T_grid, beta_grid, color="black", label="β(T) 估计")

    # Original notebook comment normalized for the public code archive.
    ax.fill_between(
        T_grid,
        ci_low,
        ci_high,
        color="red",
        alpha=0.18,
        label="95% CI",
    )

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([est - ci_pts_low, ci_pts_high - est])
    ax.errorbar(
        T_vals,
        est,
        yerr=yerr,
        fmt="o",
        capsize=4,
        color="black",
        linestyle="none",
        label="各返回期点",
    )

    # Original notebook comment normalized for the public code archive.
    y_min = min(ci_low.min(), ci_pts_low.min())
    y_max = max(ci_high.max(), ci_pts_high.max())
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.06 * (y_max - y_min if y_max > y_min else 1.0)
    y_range = (y_max - y_min) if y_max > y_min else 1.0
    offset = 0.04 * y_range

    for T, b, pv in zip(T_vals, est, p_vals):
        s = stars_for_p(pv)
        if s and np.isfinite(b):
            ax.text(
                T,
                b + offset,
                s,
                ha="center",
                va="bottom",
                fontsize=11,
            )

    # Original notebook comment normalized for the public code archive.
    ax.set_xscale("log")
    ax.set_xlim(T_min * 0.9, T_max * 1.1)
    ticks = sorted(set(int(t) for t in T_vals))
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.set_xlabel("洪水返回期 T（年，log 标度）")
    ax.set_ylabel("系数 β(T)：share_flood_ge_T 对 edu_years 的影响")
    ax.set_title(
        "CaMa storage BM：洪水严重程度 T 的非线性效应 β(T)\n"
        f"(sample={sample})"
    )

    ax.legend()
    plt.tight_layout()

    fig_path = OUT_DIR / f"betaT_storage_BM_sample_{sample}_redCI.png"
    plt.savefig(fig_path, dpi=200)
    plt.show()
    print(f"[DONE] Saved figure for sample={sample}: {fig_path}")


# ========= main =========

if __name__ == "__main__":
    print(f"[READ] linear results: {LIN_CSV}")
    df_lin = pd.read_csv(LIN_CSV)

    # Original notebook comment normalized for the public code archive.
    df_lin["T"] = pd.to_numeric(df_lin["T"], errors="coerce")
    df_lin = df_lin.dropna(subset=["T", "Estimate", "StdError"])

    for s in SAMPLES:
        plot_beta_T_curve(df_lin, sample=s)
