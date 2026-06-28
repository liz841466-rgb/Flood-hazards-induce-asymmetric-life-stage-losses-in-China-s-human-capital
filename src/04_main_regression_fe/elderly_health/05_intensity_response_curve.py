#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)
RES_CSV = OUT_DIR / "fe_health_index_z_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

Y_VAR = "health_index_z"
SAMPLES = ["all", "rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]


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


# =============================================================================

def read_fe_result() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)

    needed = [
        "Y_var", "window", "T", "sample",
        "Estimate", "Std. Error", "Pr(>|t|)",
        "2.5%", "97.5%", "N"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df = df[df["Y_var"] == Y_VAR].copy()
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")

    for col in ["Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%", "N"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["window", "T", "Estimate", "Std. Error", "sample"])
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


def aggregate_across_window(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 05_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_cols = ["Y_var", "sample", "T"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g["Estimate"].to_numpy(float)
        se = g["Std. Error"].to_numpy(float)

        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            t_val = np.nan
            p_val = np.nan

        ci_low = beta_w - 1.96 * se_w
        ci_high = beta_w + 1.96 * se_w

        win_list = sorted(g["window"].astype(int).unique().tolist())

        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_window": len(win_list),
                "window_list": ",".join(str(w) for w in win_list),
                "N_min": g["N"].min(),
                "N_max": g["N"].max(),
            }
        )

    print("[INFO] Notebook progress message.")
    df_T = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one)
    )

    df_T = df_T.sort_values(["sample", "T"]).reset_index(drop=True)
    out_path = OUT_DIR / "fe_health_index_z_Tall_windowAgg_over_T.csv"
    df_T.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    print(df_T.head(12))
    return df_T


# =============================================================================

def plot_beta_T_curve(df_T: pd.DataFrame, sample: str):
    """Archived notebook note for 05_intensity_response_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_T[(df_T["Y_var"] == Y_VAR) & (df_T["sample"] == sample)].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub[sub["T"].isin(T_LIST)].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub = sub.sort_values("T")
    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)

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
    ci_pts_low = est - 1.96 * se
    ci_pts_high = est + 1.96 * se
    p_vals = []
    for b, s in zip(est, se):
        if s > 0:
            t_b = b / s
            p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
        else:
            p_b = np.nan
        p_vals.append(p_b)
    p_vals = np.array(p_vals)

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6, 4))

    # Original notebook comment normalized for the public code archive.
    ax.plot(T_grid, beta_grid, label="β(T) 估计")
    ax.fill_between(T_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

    # Original notebook comment normalized for the public code archive.
    ax.errorbar(
        T_vals,
        est,
        yerr=[est - ci_pts_low, ci_pts_high - est],
        fmt="o",
        linestyle="none",
        capsize=4,
        color="black",
        label="各返回期点 (聚合后)",
    )

    # Original notebook comment normalized for the public code archive.
    y_min = min(ci_low.min(), ci_pts_low.min())
    y_max = max(ci_high.max(), ci_pts_high.max())
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.05 * (y_max - y_min if y_max > y_min else 1.0)
    y_range = (y_max - y_min) if y_max > y_min else 1.0
    offset = 0.03 * y_range

    for T, b, p in zip(T_vals, est, p_vals):
        star = stars_for_p(p)
        if star:
            ax.text(
                T,
                b + offset,
                star,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Original notebook comment normalized for the public code archive.
    ax.set_xscale("log")
    ax.set_xlim(T_min * 0.9, T_max * 1.1)
    ax.set_xticks(T_LIST)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.set_xlabel("洪水返回期 T（年）")
    ax.set_ylabel("系数 β(T) 对 health_index_z 的影响")
    ax.set_title(f"洪水返回期 T 的非线性强度效应 β(T)（sample={sample}）")

    ax.legend()
    plt.tight_layout()
    plt.show()


# ========= main =========

def main():
    df_fe = read_fe_result()
    df_Tagg = aggregate_across_window(df_fe)

    for sample in SAMPLES:
        plot_beta_T_curve(df_Tagg, sample=sample)


if __name__ == "__main__":
    main()
