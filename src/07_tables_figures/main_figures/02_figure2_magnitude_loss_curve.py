#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================

BASE_DIR = Path(
    r"E:\impact_assessment_child_order\data\figue2"
)

STORAGE_CSV = BASE_DIR / "storage_BM_linear_allT.csv"
HEALTH_AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T.csv"

# Original notebook comment normalized for the public code archive.
PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR_HEALTH = "health_index_z"
SAMPLES = ["all", "rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]

SAVE_FIG = True


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

def fit_beta_T_curve(
    T_vals_raw,
    est_raw,
    se_raw,
    ci_low_pts=None,
    ci_high_pts=None,
    p_vals=None,
    T_grid_n: int = 200,
):
    """Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    T_vals = np.asarray(T_vals_raw, dtype="float64")
    est = np.asarray(est_raw, dtype="float64")
    se = np.asarray(se_raw, dtype="float64")

    # Original notebook comment normalized for the public code archive.
    if ci_low_pts is None or ci_high_pts is None:
        ci_low_pts = est - 1.96 * se
        ci_high_pts = est + 1.96 * se
    else:
        ci_low_pts = np.asarray(ci_low_pts, dtype="float64")
        ci_high_pts = np.asarray(ci_high_pts, dtype="float64")

    if p_vals is None:
        p_tmp = []
        for b, s in zip(est, se):
            if s > 0:
                t_b = b / s
                p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
            else:
                p_b = np.nan
            p_tmp.append(p_b)
        p_vals = np.asarray(p_tmp)
    else:
        p_vals = np.asarray(p_vals, dtype="float64")

    # Original notebook comment normalized for the public code archive.
    order = np.argsort(T_vals)
    T_vals = T_vals[order]
    est = est[order]
    se = se[order]
    ci_low_pts = ci_low_pts[order]
    ci_high_pts = ci_high_pts[order]
    p_vals = p_vals[order]

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

    print(fit.summary())

    # Original notebook comment normalized for the public code archive.
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), T_grid_n)
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

    return {
        "T_vals": T_vals,
        "est": est,
        "se": se,
        "ci_pts_low": ci_low_pts,
        "ci_pts_high": ci_high_pts,
        "p_vals": p_vals,
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "fit": fit,
    }


# =============================================================================

def load_storage_lin() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df_lin = pd.read_csv(STORAGE_CSV)

    # Original notebook comment normalized for the public code archive.
    df_lin["T"] = pd.to_numeric(df_lin["T"], errors="coerce")
    df_lin = df_lin.dropna(subset=["T", "Estimate", "StdError"])
    df_lin["T"] = df_lin["T"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df_lin.head())
    return df_lin


def get_storage_curve(df_lin: pd.DataFrame, sample: str):
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    ci_low_pts = sub["CI_low"].to_numpy(float) if "CI_low" in sub.columns else None
    ci_high_pts = sub["CI_high"].to_numpy(float) if "CI_high" in sub.columns else None
    p_vals = sub["PValue"].to_numpy(float) if "PValue" in sub.columns else None

    print(f"\n[INFO] CaMa storage β(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# =============================================================================

def load_health_Tagg() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df_Tagg = pd.read_csv(HEALTH_AGG_CSV)

    df_Tagg["T"] = pd.to_numeric(df_Tagg["T"], errors="coerce")
    df_Tagg = df_Tagg.dropna(subset=["T"])
    df_Tagg["T"] = df_Tagg["T"].astype(int)

    print("[INFO] Notebook progress message.")
    print(df_Tagg.head())
    return df_Tagg


def get_health_curve(df_Tagg: pd.DataFrame, sample: str):
    sub = df_Tagg[
        (df_Tagg.get("Y_var", Y_VAR_HEALTH) == Y_VAR_HEALTH)
        & (df_Tagg["sample"] == sample)
        & (df_Tagg["T"].isin(T_LIST))
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)
    ci_low_pts = sub["2.5%"].to_numpy(float)
    ci_high_pts = sub["97.5%"].to_numpy(float)
    p_vals = sub["Pr(>|t|)"].to_numpy(float)

    print(f"\n[INFO] CaMa-Flood health β(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# =============================================================================

def plot_twinx(curve_storage, curve_health, sample: str):
    """Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))
    ax2 = ax1.twinx()  # Original notebook comment normalized for the public code archive.

    # =============================================================================
    ax1.plot(
        curve_storage["T_grid"],
        curve_storage["beta_grid"],
        label="教育 β(T) – CaMa storage",
    )
    ax1.fill_between(
        curve_storage["T_grid"],
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        alpha=0.8,
    )
    ax1.errorbar(
        curve_storage["T_vals"],
        curve_storage["est"],
        yerr=[
            curve_storage["est"] - curve_storage["ci_pts_low"],
            curve_storage["ci_pts_high"] - curve_storage["est"],
        ],
        fmt="o",
        capsize=4,
        linestyle="none",
        label="教育点估计",
    )

    # =============================================================================
    ax2.plot(
        curve_health["T_grid"],
        curve_health["beta_grid"],
        linestyle="--",
        label="健康 β(T) – CaMa",
    )
    ax2.fill_between(
        curve_health["T_grid"],
        curve_health["ci_low"],
        curve_health["ci_high"],
        alpha=0.18,
    )
    ax2.errorbar(
        curve_health["T_vals"],
        curve_health["est"],
        yerr=[
            curve_health["est"] - curve_health["ci_pts_low"],
            curve_health["ci_pts_high"] - curve_health["est"],
        ],
        fmt="s",
        capsize=4,
        linestyle="none",
        label="健康点估计",
    )

    # =============================================================================
    vals1 = np.concatenate([
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        curve_storage["ci_pts_low"],
        curve_storage["ci_pts_high"],
        np.array([0.0]),
    ])
    y1_min_raw = np.nanmin(vals1)
    y1_max_raw = np.nanmax(vals1)
    max_abs1 = float(max(abs(y1_min_raw), abs(y1_max_raw), 1e-6))
    pad_factor1 = 1.05
    y1_min = -max_abs1 * pad_factor1
    y1_max = max_abs1 * pad_factor1
    ax1.set_ylim(y1_min, y1_max)

    vals2 = np.concatenate([
        curve_health["ci_low"],
        curve_health["ci_high"],
        curve_health["ci_pts_low"],
        curve_health["ci_pts_high"],
        np.array([0.0]),
    ])
    y2_min_raw = np.nanmin(vals2)
    y2_max_raw = np.nanmax(vals2)
    max_abs2 = float(max(abs(y2_min_raw), abs(y2_max_raw), 1e-6))
    pad_factor2 = 1.05
    y2_min = -max_abs2 * pad_factor2
    y2_max = max_abs2 * pad_factor2
    ax2.set_ylim(y2_min, y2_max)

    # Original notebook comment normalized for the public code archive.
    y1_range = y1_max - y1_min
    offset1 = 0.03 * y1_range
    for T, b, p in zip(
        curve_storage["T_vals"], curve_storage["est"], curve_storage["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b):
            ax1.text(T, b + offset1, s, ha="center", va="bottom", fontsize=10)

    # Original notebook comment normalized for the public code archive.
    y2_range = y2_max - y2_min
    offset2 = 0.03 * y2_range
    for T, b, p in zip(
        curve_health["T_vals"], curve_health["est"], curve_health["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b):
            ax2.text(T, b + offset2, s, ha="center", va="bottom", fontsize=10)

    # =============================================================================
    T_all = np.concatenate([curve_storage["T_vals"], curve_health["T_vals"]])
    T_min, T_max = T_all.min(), T_all.max()
    ax1.set_xscale("log")
    ax1.set_xlim(T_min * 0.9, T_max * 1.1)
    ax1.set_xticks(T_LIST)
    ax1.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax1.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    # Original notebook comment normalized for the public code archive.
    ax1.axhline(0, linestyle="--", linewidth=1)

    ax1.set_xlabel("洪水返回期 T（年，log 标度）")
    ax1.set_ylabel("β(T) – 教育 (CaMa)")
    ax2.set_ylabel("β(T) – 健康 (CaMa)")

    ax1.set_title(
        "洪水返回期 T 的非线性效应 β(T)\n"
        f"教育 vs 健康（sample={sample}，双 y 轴，0 对齐）"
    )

    # Original notebook comment normalized for the public code archive.
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="best")

    plt.tight_layout()

    if SAVE_FIG:
        fig_path = PLOT_DIR / f"betaT_edu_health_twinx_sample_{sample}.png"
        fig.savefig(fig_path, dpi=200)
        print("[INFO] Notebook progress message.")

    plt.show()
    plt.close(fig)


# ========= main =========

def main():
    df_storage_lin = load_storage_lin()
    df_health_Tagg = load_health_Tagg()

    for sample in SAMPLES:
        print(f"\n================ sample={sample} ================")
        curve_storage = get_storage_curve(df_storage_lin, sample)
        curve_health = get_health_curve(df_health_Tagg, sample)

        if curve_storage is None or curve_health is None:
            print("[INFO] Notebook progress message.")
            continue

        plot_twinx(curve_storage, curve_health, sample)

    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors


# ========== global style (English only, Times New Roman, 300 dpi) ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


# ========== paths & configuration ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")

STORAGE_CSV = BASE_DIR / "storage_BM_linear_allT.csv"
HEALTH_AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T.csv"

PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR_HEALTH = "health_index_z"

# Only draw these samples for now
SAMPLES = ["rural"]
# SAMPLES = ["all"]
# SAMPLES = ["all", "rural", "urban"]

T_LIST = [2, 5, 10, 20, 50, 100]

SAVE_FIG = True


# ========== plotting style configuration ==========

# figure size
FIG_SIZE = (6.5, 4.5)

# main line colors
EDU_LINE_COLOR = "#8c510a"      # education series
HEALTH_LINE_COLOR = "#01665e"    # health series

# uncertainty band fill colors
EDU_BAND_FILL_COLOR = "#bf812d"
HEALTH_BAND_FILL_COLOR = "#35978f"

# ---- key: fill and edge are controlled separately here ----
# fill transparency
EDU_BAND_FILL_ALPHA = 0.22
HEALTH_BAND_FILL_ALPHA = 0.22

# edge transparency
EDU_BAND_EDGE_ALPHA = 0.95
HEALTH_BAND_EDGE_ALPHA = 0.95

# edge width
EDU_BAND_EDGE_WIDTH = 0.3
HEALTH_BAND_EDGE_WIDTH = 0.3

# line style
EDU_LINE_WIDTH = 1.5
HEALTH_LINE_WIDTH = 1.5
EDU_LINE_ALPHA = 1.0
HEALTH_LINE_ALPHA = 1.0

# error bar (vertical line) style
EDU_ERR_LINEWIDTH = 2.5
HEALTH_ERR_LINEWIDTH = 2.5
EDU_ERR_ALPHA = 0.9
HEALTH_ERR_ALPHA = 0.9

# point (central estimate) style
EDU_POINT_SIZE = 50
HEALTH_POINT_SIZE = 50
EDU_POINT_ALPHA = 1.0
HEALTH_POINT_ALPHA = 1.0

# significance stars
STAR_FONT_SIZE = 0

# axis / reference line style
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.0
ZERO_LINE_ALPHA = 0.8

# title / label size
TITLE_SIZE = 16
YLABEL_SIZE = 18
TICK_SIZE = 14


# ========== helpers ==========

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    """Return significance stars based on p-value."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def rgba(color: str, alpha: float):
    """Convert a color to RGBA tuple with given alpha."""
    return mcolors.to_rgba(color, alpha=alpha)


# ========== meta-regression for beta(T) ==========

def fit_beta_T_curve(
    T_vals_raw,
    est_raw,
    se_raw,
    ci_low_pts=None,
    ci_high_pts=None,
    p_vals=None,
    T_grid_n: int = 200,
):
    """
    Given discrete (T, beta_hat, SE), fit a weighted polynomial meta-regression
    in log(T) and return beta(T) + 95% CI on a dense grid.
    """
    T_vals = np.asarray(T_vals_raw, dtype="float64")
    est = np.asarray(est_raw, dtype="float64")
    se = np.asarray(se_raw, dtype="float64")

    # pointwise CI / p-values
    if ci_low_pts is None or ci_high_pts is None:
        ci_low_pts = est - 1.96 * se
        ci_high_pts = est + 1.96 * se
    else:
        ci_low_pts = np.asarray(ci_low_pts, dtype="float64")
        ci_high_pts = np.asarray(ci_high_pts, dtype="float64")

    if p_vals is None:
        p_tmp = []
        for b, s in zip(est, se):
            if s > 0:
                t_b = b / s
                p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
            else:
                p_b = np.nan
            p_tmp.append(p_b)
        p_vals = np.asarray(p_tmp)
    else:
        p_vals = np.asarray(p_vals, dtype="float64")

    # sort by T
    order = np.argsort(T_vals)
    T_vals = T_vals[order]
    est = est[order]
    se = se[order]
    ci_low_pts = ci_low_pts[order]
    ci_high_pts = ci_high_pts[order]
    p_vals = p_vals[order]

    # WLS weights
    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    # choose polynomial degree by number of points
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

    print(fit.summary())

    # continuous T grid
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), T_grid_n)
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

    return {
        "T_vals": T_vals,
        "est": est,
        "se": se,
        "ci_pts_low": ci_low_pts,
        "ci_pts_high": ci_high_pts,
        "p_vals": p_vals,
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "fit": fit,
    }


# ========== CaMa storage (education) ==========

def load_storage_lin() -> pd.DataFrame:
    print(f"[READ] CaMa storage linear results: {STORAGE_CSV}")
    df_lin = pd.read_csv(STORAGE_CSV)

    df_lin["T"] = pd.to_numeric(df_lin["T"], errors="coerce")
    df_lin = df_lin.dropna(subset=["T", "Estimate", "StdError"])
    df_lin["T"] = df_lin["T"].astype(int)

    print("[INFO] CaMa storage head:")
    print(df_lin.head())
    return df_lin


def get_storage_curve(df_lin: pd.DataFrame, sample: str):
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] storage sample={sample} is empty, skip.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    ci_low_pts = sub["CI_low"].to_numpy(float) if "CI_low" in sub.columns else None
    ci_high_pts = sub["CI_high"].to_numpy(float) if "CI_high" in sub.columns else None
    p_vals = sub["PValue"].to_numpy(float) if "PValue" in sub.columns else None

    print(f"\n[INFO] CaMa storage beta(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# ========== Tall health (aggregated) ==========

def load_health_Tagg() -> pd.DataFrame:
    print(f"[READ] Tall health aggregated results: {HEALTH_AGG_CSV}")
    df_Tagg = pd.read_csv(HEALTH_AGG_CSV)

    df_Tagg["T"] = pd.to_numeric(df_Tagg["T"], errors="coerce")
    df_Tagg = df_Tagg.dropna(subset=["T"])
    df_Tagg["T"] = df_Tagg["T"].astype(int)

    print("[INFO] Tall health aggregated head:")
    print(df_Tagg.head())
    return df_Tagg


def get_health_curve(df_Tagg: pd.DataFrame, sample: str):
    sub = df_Tagg[
        (df_Tagg.get("Y_var", Y_VAR_HEALTH) == Y_VAR_HEALTH)
        & (df_Tagg["sample"] == sample)
        & (df_Tagg["T"].isin(T_LIST))
    ].copy()

    if sub.empty:
        print(f"[WARN] health sample={sample} is empty, skip.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)
    ci_low_pts = sub["2.5%"].to_numpy(float)
    ci_high_pts = sub["97.5%"].to_numpy(float)
    p_vals = sub["Pr(>|t|)"].to_numpy(float)

    print(f"\n[INFO] Health beta(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# ========== plotting (dual y-axis, 0-aligned) ==========

def plot_twinx(curve_storage, curve_health, sample: str):
    """
    Plot education vs. health beta(T) with dual y-axis (twinx).

      - Left y-axis:  education loss (CaMa storage)
      - Right y-axis: health loss (Tall health)

    Both y-axes are symmetric around 0.
    """
    fig, ax1 = plt.subplots(figsize=FIG_SIZE)
    ax2 = ax1.twinx()  # shared x-axis

    # ===== left axis: education =====
    ax1.plot(
        curve_storage["T_grid"],
        curve_storage["beta_grid"],
        label="Education loss (CaMa)",
        color=rgba(EDU_LINE_COLOR, EDU_LINE_ALPHA),
        linewidth=EDU_LINE_WIDTH,
        zorder=2,
    )

    ax1.fill_between(
        curve_storage["T_grid"],
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        facecolor=rgba(EDU_BAND_FILL_COLOR, EDU_BAND_FILL_ALPHA),   # fill alpha
        edgecolor=rgba(EDU_LINE_COLOR, EDU_BAND_EDGE_ALPHA),        # edge alpha
        linewidth=EDU_BAND_EDGE_WIDTH,
        zorder=1,
    )

    for x, est, lo, hi in zip(
        curve_storage["T_vals"],
        curve_storage["est"],
        curve_storage["ci_pts_low"],
        curve_storage["ci_pts_high"],
    ):
        ax1.vlines(
            x,
            lo,
            hi,
            color=rgba(EDU_LINE_COLOR, EDU_ERR_ALPHA),
            linewidth=EDU_ERR_LINEWIDTH,
            zorder=3,
        )

    ax1.scatter(
        curve_storage["T_vals"],
        curve_storage["est"],
        color=rgba(EDU_LINE_COLOR, EDU_POINT_ALPHA),
        s=EDU_POINT_SIZE,
        zorder=4,
    )

    # ===== right axis: health =====
    ax2.plot(
        curve_health["T_grid"],
        curve_health["beta_grid"],
        label="Health loss (CaMa)",
        color=rgba(HEALTH_LINE_COLOR, HEALTH_LINE_ALPHA),
        linewidth=HEALTH_LINE_WIDTH,
        zorder=2,
    )

    ax2.fill_between(
        curve_health["T_grid"],
        curve_health["ci_low"],
        curve_health["ci_high"],
        facecolor=rgba(HEALTH_BAND_FILL_COLOR, HEALTH_BAND_FILL_ALPHA),   # fill alpha
        edgecolor=rgba(HEALTH_LINE_COLOR, HEALTH_BAND_EDGE_ALPHA),        # edge alpha
        linewidth=HEALTH_BAND_EDGE_WIDTH,
        zorder=1,
    )

    for x, est, lo, hi in zip(
        curve_health["T_vals"],
        curve_health["est"],
        curve_health["ci_pts_low"],
        curve_health["ci_pts_high"],
    ):
        ax2.vlines(
            x,
            lo,
            hi,
            color=rgba(HEALTH_LINE_COLOR, HEALTH_ERR_ALPHA),
            linewidth=HEALTH_ERR_LINEWIDTH,
            zorder=3,
        )

    ax2.scatter(
        curve_health["T_vals"],
        curve_health["est"],
        color=rgba(HEALTH_LINE_COLOR, HEALTH_POINT_ALPHA),
        s=HEALTH_POINT_SIZE,
        zorder=4,
    )

    # ===== y-limits: symmetric around 0 =====
    vals1 = np.concatenate([
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        curve_storage["ci_pts_low"],
        curve_storage["ci_pts_high"],
        np.array([0.0]),
    ])
    y1_min_raw = np.nanmin(vals1)
    y1_max_raw = np.nanmax(vals1)
    max_abs1 = float(max(abs(y1_min_raw), abs(y1_max_raw), 1e-6))
    pad_factor1 = 1.05
    y1_min = -max_abs1 * pad_factor1
    y1_max = max_abs1 * pad_factor1
    ax1.set_ylim(y1_min, y1_max)

    vals2 = np.concatenate([
        curve_health["ci_low"],
        curve_health["ci_high"],
        curve_health["ci_pts_low"],
        curve_health["ci_pts_high"],
        np.array([0.0]),
    ])
    y2_min_raw = np.nanmin(vals2)
    y2_max_raw = np.nanmax(vals2)
    max_abs2 = float(max(abs(y2_min_raw), abs(y2_max_raw), 1e-6))
    pad_factor2 = 1.05
    y2_min = -max_abs2 * pad_factor2
    y2_max = max_abs2 * pad_factor2
    ax2.set_ylim(y2_min, y2_max)

    # force y-axis tick labels to keep 1 decimal place
    yfmt = mticker.FormatStrFormatter('%.1f')
    ax1.yaxis.set_major_formatter(yfmt)
    ax2.yaxis.set_major_formatter(yfmt)

    # ===== significance stars =====
    y1_range = y1_max - y1_min
    offset1 = 0.03 * y1_range
    for T, b, p in zip(
        curve_storage["T_vals"], curve_storage["est"], curve_storage["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b) and STAR_FONT_SIZE > 0:
            ax1.text(
                T,
                b + offset1,
                s,
                ha="center",
                va="bottom",
                fontsize=STAR_FONT_SIZE,
                zorder=5,
            )

    y2_range = y2_max - y2_min
    offset2 = 0.03 * y2_range
    for T, b, p in zip(
        curve_health["T_vals"], curve_health["est"], curve_health["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b) and STAR_FONT_SIZE > 0:
            ax2.text(
                T,
                b + offset2,
                s,
                ha="center",
                va="bottom",
                fontsize=STAR_FONT_SIZE,
                zorder=5,
            )

    # ===== x-axis settings =====
    T_all = np.concatenate([curve_storage["T_vals"], curve_health["T_vals"]])
    T_min, T_max = T_all.min(), T_all.max()
    ax1.set_xscale("log")
    ax1.set_xlim(T_min * 0.9, T_max * 1.1)

    ax1.set_xticks(T_LIST)
    ax1.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax1.xaxis.set_minor_locator(mticker.NullLocator())  # no minor ticks
    ax1.xaxis.set_major_formatter(mticker.ScalarFormatter())

    # reference line at 0
    ax1.axhline(
        0,
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        alpha=ZERO_LINE_ALPHA,
    )

    # labels & title
    # ax1.set_xlabel("Return level")
    # ax1.set_ylabel("Education loss", fontsize=YLABEL_SIZE)
    #ax2.set_ylabel("Health loss", fontsize=YLABEL_SIZE)
    ax1.set_title(sample.upper(), fontsize=TITLE_SIZE)

    ax1.tick_params(axis="x", labelsize=TICK_SIZE)
    ax1.tick_params(axis="y", labelsize=TICK_SIZE)
    ax2.tick_params(axis="y", labelsize=TICK_SIZE)

    plt.tight_layout()

    if SAVE_FIG:
        fig_path = PLOT_DIR / f"betaT_edu_health_twinx_sample_{sample}.png"
        fig.savefig(fig_path, dpi=300)
        print(f"[SAVE] twinx plot saved (overwritten if existed): {fig_path}")

    plt.show()
    plt.close(fig)


# ========== main ==========

def main():
    df_storage_lin = load_storage_lin()
    df_health_Tagg = load_health_Tagg()

    for sample in SAMPLES:
        print(f"\n================ sample={sample} ================")
        curve_storage = get_storage_curve(df_storage_lin, sample)
        curve_health = get_health_curve(df_health_Tagg, sample)

        if curve_storage is None or curve_health is None:
            print(f"[WARN] sample={sample} missing curve info, skip plotting.")
            continue

        plot_twinx(curve_storage, curve_health, sample)

    print("[DONE] All requested twinx plots finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_figure2_magnitude_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors


# ========== global style (English only, Times New Roman, 300 dpi) ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


# ========== paths & configuration ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")

STORAGE_CSV = BASE_DIR / "storage_BM_linear_allT.csv"
HEALTH_AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T.csv"

PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR_HEALTH = "health_index_z"

# Only draw these samples for now
SAMPLES = ["all"]
# SAMPLES = ["all"]
# SAMPLES = ["all", "rural", "urban"]

T_LIST = [2, 5, 10, 20, 50, 100]

SAVE_FIG = True


# ========== plotting style configuration ==========

# figure size
FIG_SIZE = (6.5, 5.2)

# main line colors
EDU_LINE_COLOR = "#8c510a"       # education series
HEALTH_LINE_COLOR = "#01665e"    # health series

# uncertainty band fill colors
EDU_BAND_FILL_COLOR = "#bf812d"
HEALTH_BAND_FILL_COLOR = "#35978f"

# fill transparency
EDU_BAND_FILL_ALPHA = 0.22
HEALTH_BAND_FILL_ALPHA = 0.22

# edge transparency
EDU_BAND_EDGE_ALPHA = 0.95
HEALTH_BAND_EDGE_ALPHA = 0.95

# edge width
EDU_BAND_EDGE_WIDTH = 0.3
HEALTH_BAND_EDGE_WIDTH = 0.3

# line style
EDU_LINE_WIDTH = 1.5
HEALTH_LINE_WIDTH = 1.5
EDU_LINE_ALPHA = 1.0
HEALTH_LINE_ALPHA = 1.0

# error bar (vertical line) style
EDU_ERR_LINEWIDTH = 2.5
HEALTH_ERR_LINEWIDTH = 2.5
EDU_ERR_ALPHA = 0.9
HEALTH_ERR_ALPHA = 0.9

# point (central estimate) style
EDU_POINT_SIZE = 50
HEALTH_POINT_SIZE = 50
EDU_POINT_ALPHA = 1.0
HEALTH_POINT_ALPHA = 1.0

# significance stars
STAR_FONT_SIZE = 0

# axis / reference line style
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.0
ZERO_LINE_ALPHA = 0.8

# title / label size
TITLE_SIZE = 16
YLABEL_SIZE = 18
TICK_SIZE = 18

# ----- horizontal dodge on log-x axis -----
# use symmetric multiplicative shifts on a log scale
# exp(±0.04) ≈ 0.9608 and 1.0408
LOG_X_DODGE = 0.04
EDU_XMULT = float(np.exp(-LOG_X_DODGE))
HEALTH_XMULT = float(np.exp(LOG_X_DODGE))


# ========== helpers ==========

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    """Return significance stars based on p-value."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def rgba(color: str, alpha: float):
    """Convert a color to RGBA tuple with given alpha."""
    return mcolors.to_rgba(color, alpha=alpha)


def shift_x_log(x, xmult: float):
    """Multiplicative shift for log-scale x-axis."""
    x = np.asarray(x, dtype="float64")
    return x * xmult


# ========== meta-regression for beta(T) ==========

def fit_beta_T_curve(
    T_vals_raw,
    est_raw,
    se_raw,
    ci_low_pts=None,
    ci_high_pts=None,
    p_vals=None,
    T_grid_n: int = 200,
):
    """
    Given discrete (T, beta_hat, SE), fit a weighted polynomial meta-regression
    in log(T) and return beta(T) + 95% CI on a dense grid.
    """
    T_vals = np.asarray(T_vals_raw, dtype="float64")
    est = np.asarray(est_raw, dtype="float64")
    se = np.asarray(se_raw, dtype="float64")

    # pointwise CI / p-values
    if ci_low_pts is None or ci_high_pts is None:
        ci_low_pts = est - 1.96 * se
        ci_high_pts = est + 1.96 * se
    else:
        ci_low_pts = np.asarray(ci_low_pts, dtype="float64")
        ci_high_pts = np.asarray(ci_high_pts, dtype="float64")

    if p_vals is None:
        p_tmp = []
        for b, s in zip(est, se):
            if s > 0:
                t_b = b / s
                p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
            else:
                p_b = np.nan
            p_tmp.append(p_b)
        p_vals = np.asarray(p_tmp)
    else:
        p_vals = np.asarray(p_vals, dtype="float64")

    # sort by T
    order = np.argsort(T_vals)
    T_vals = T_vals[order]
    est = est[order]
    se = se[order]
    ci_low_pts = ci_low_pts[order]
    ci_high_pts = ci_high_pts[order]
    p_vals = p_vals[order]

    # WLS weights
    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    # choose polynomial degree by number of points
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

    print(fit.summary())

    # continuous T grid
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), T_grid_n)
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

    return {
        "T_vals": T_vals,
        "est": est,
        "se": se,
        "ci_pts_low": ci_low_pts,
        "ci_pts_high": ci_high_pts,
        "p_vals": p_vals,
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "fit": fit,
    }


# ========== CaMa storage (education) ==========

def load_storage_lin() -> pd.DataFrame:
    print(f"[READ] CaMa storage linear results: {STORAGE_CSV}")
    df_lin = pd.read_csv(STORAGE_CSV)

    df_lin["T"] = pd.to_numeric(df_lin["T"], errors="coerce")
    df_lin = df_lin.dropna(subset=["T", "Estimate", "StdError"])
    df_lin["T"] = df_lin["T"].astype(int)

    print("[INFO] CaMa storage head:")
    print(df_lin.head())
    return df_lin


def get_storage_curve(df_lin: pd.DataFrame, sample: str):
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] storage sample={sample} is empty, skip.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    ci_low_pts = sub["CI_low"].to_numpy(float) if "CI_low" in sub.columns else None
    ci_high_pts = sub["CI_high"].to_numpy(float) if "CI_high" in sub.columns else None
    p_vals = sub["PValue"].to_numpy(float) if "PValue" in sub.columns else None

    print(f"\n[INFO] CaMa storage beta(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# ========== Tall health (aggregated) ==========

def load_health_Tagg() -> pd.DataFrame:
    print(f"[READ] Tall health aggregated results: {HEALTH_AGG_CSV}")
    df_Tagg = pd.read_csv(HEALTH_AGG_CSV)

    df_Tagg["T"] = pd.to_numeric(df_Tagg["T"], errors="coerce")
    df_Tagg = df_Tagg.dropna(subset=["T"])
    df_Tagg["T"] = df_Tagg["T"].astype(int)

    print("[INFO] Tall health aggregated head:")
    print(df_Tagg.head())
    return df_Tagg


def get_health_curve(df_Tagg: pd.DataFrame, sample: str):
    sub = df_Tagg[
        (df_Tagg.get("Y_var", Y_VAR_HEALTH) == Y_VAR_HEALTH)
        & (df_Tagg["sample"] == sample)
        & (df_Tagg["T"].isin(T_LIST))
    ].copy()

    if sub.empty:
        print(f"[WARN] health sample={sample} is empty, skip.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)
    ci_low_pts = sub["2.5%"].to_numpy(float)
    ci_high_pts = sub["97.5%"].to_numpy(float)
    p_vals = sub["Pr(>|t|)"].to_numpy(float)

    print(f"\n[INFO] Health beta(T) meta-regression for sample={sample}")
    curve = fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )
    return curve


# ========== plotting (dual y-axis, 0-aligned) ==========

def plot_twinx(curve_storage, curve_health, sample: str):
    """
    Plot education vs. health beta(T) with dual y-axis (twinx).

      - Left y-axis:  education loss (CaMa storage)
      - Right y-axis: health loss (Tall health)

    Both y-axes are symmetric around 0.

    IMPORTANT:
      All visual elements are horizontally shifted on the log-x axis:
        education -> slightly left
        health    -> slightly right
    """
    fig, ax1 = plt.subplots(figsize=FIG_SIZE)
    ax2 = ax1.twinx()  # shared x-axis

    # ===== shifted x coordinates (same idea as previous crossed plot) =====
    xg_edu = shift_x_log(curve_storage["T_grid"], EDU_XMULT)
    xp_edu = shift_x_log(curve_storage["T_vals"], EDU_XMULT)

    xg_health = shift_x_log(curve_health["T_grid"], HEALTH_XMULT)
    xp_health = shift_x_log(curve_health["T_vals"], HEALTH_XMULT)

    # ===== left axis: education =====
    ax1.plot(
        xg_edu,
        curve_storage["beta_grid"],
        label="Education loss (CaMa)",
        color=rgba(EDU_LINE_COLOR, EDU_LINE_ALPHA),
        linewidth=EDU_LINE_WIDTH,
        zorder=2,
    )

    ax1.fill_between(
        xg_edu,
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        facecolor=rgba(EDU_BAND_FILL_COLOR, EDU_BAND_FILL_ALPHA),
        edgecolor=rgba(EDU_LINE_COLOR, EDU_BAND_EDGE_ALPHA),
        linewidth=EDU_BAND_EDGE_WIDTH,
        zorder=1,
    )

    for x, lo, hi in zip(
        xp_edu,
        curve_storage["ci_pts_low"],
        curve_storage["ci_pts_high"],
    ):
        ax1.vlines(
            x,
            lo,
            hi,
            color=rgba(EDU_LINE_COLOR, EDU_ERR_ALPHA),
            linewidth=EDU_ERR_LINEWIDTH,
            zorder=3,
        )

    ax1.scatter(
        xp_edu,
        curve_storage["est"],
        color=rgba(EDU_LINE_COLOR, EDU_POINT_ALPHA),
        s=EDU_POINT_SIZE,
        zorder=4,
    )

    # ===== right axis: health =====
    ax2.plot(
        xg_health,
        curve_health["beta_grid"],
        label="Health loss (CaMa)",
        color=rgba(HEALTH_LINE_COLOR, HEALTH_LINE_ALPHA),
        linewidth=HEALTH_LINE_WIDTH,
        zorder=2,
    )

    ax2.fill_between(
        xg_health,
        curve_health["ci_low"],
        curve_health["ci_high"],
        facecolor=rgba(HEALTH_BAND_FILL_COLOR, HEALTH_BAND_FILL_ALPHA),
        edgecolor=rgba(HEALTH_LINE_COLOR, HEALTH_BAND_EDGE_ALPHA),
        linewidth=HEALTH_BAND_EDGE_WIDTH,
        zorder=1,
    )

    for x, lo, hi in zip(
        xp_health,
        curve_health["ci_pts_low"],
        curve_health["ci_pts_high"],
    ):
        ax2.vlines(
            x,
            lo,
            hi,
            color=rgba(HEALTH_LINE_COLOR, HEALTH_ERR_ALPHA),
            linewidth=HEALTH_ERR_LINEWIDTH,
            zorder=3,
        )

    ax2.scatter(
        xp_health,
        curve_health["est"],
        color=rgba(HEALTH_LINE_COLOR, HEALTH_POINT_ALPHA),
        s=HEALTH_POINT_SIZE,
        zorder=4,
    )

    # ===== y-limits: symmetric around 0 =====
    vals1 = np.concatenate([
        curve_storage["ci_low"],
        curve_storage["ci_high"],
        curve_storage["ci_pts_low"],
        curve_storage["ci_pts_high"],
        np.array([0.0]),
    ])
    y1_min_raw = np.nanmin(vals1)
    y1_max_raw = np.nanmax(vals1)
    max_abs1 = float(max(abs(y1_min_raw), abs(y1_max_raw), 1e-6))
    pad_factor1 = 1.05
    y1_min = -max_abs1 * pad_factor1
    y1_max = max_abs1 * pad_factor1
    ax1.set_ylim(y1_min, y1_max)

    vals2 = np.concatenate([
        curve_health["ci_low"],
        curve_health["ci_high"],
        curve_health["ci_pts_low"],
        curve_health["ci_pts_high"],
        np.array([0.0]),
    ])
    y2_min_raw = np.nanmin(vals2)
    y2_max_raw = np.nanmax(vals2)
    max_abs2 = float(max(abs(y2_min_raw), abs(y2_max_raw), 1e-6))
    pad_factor2 = 1.05
    y2_min = -max_abs2 * pad_factor2
    y2_max = max_abs2 * pad_factor2
    ax2.set_ylim(y2_min, y2_max)

    # force y-axis tick labels to keep 1 decimal place
    yfmt = mticker.FormatStrFormatter("%.1f")
    ax1.yaxis.set_major_formatter(yfmt)
    ax2.yaxis.set_major_formatter(yfmt)

    # ===== significance stars =====
    y1_range = y1_max - y1_min
    offset1 = 0.03 * y1_range
    for T, b, p in zip(
        xp_edu, curve_storage["est"], curve_storage["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b) and STAR_FONT_SIZE > 0:
            ax1.text(
                T,
                b + offset1,
                s,
                ha="center",
                va="bottom",
                fontsize=STAR_FONT_SIZE,
                zorder=5,
            )

    y2_range = y2_max - y2_min
    offset2 = 0.03 * y2_range
    for T, b, p in zip(
        xp_health, curve_health["est"], curve_health["p_vals"]
    ):
        s = stars_for_p(p)
        if s and np.isfinite(b) and STAR_FONT_SIZE > 0:
            ax2.text(
                T,
                b + offset2,
                s,
                ha="center",
                va="bottom",
                fontsize=STAR_FONT_SIZE,
                zorder=5,
            )

    # ===== x-axis settings =====
    # use shifted x-range so nothing is clipped
    T_all_shifted = np.concatenate([xg_edu, xg_health, xp_edu, xp_health])
    T_min, T_max = float(np.nanmin(T_all_shifted)), float(np.nanmax(T_all_shifted))

    ax1.set_xscale("log")
    ax1.set_xlim(T_min * 0.9, T_max * 1.1)

    ax1.set_xticks(T_LIST)
    ax1.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax1.xaxis.set_minor_locator(mticker.NullLocator())  # no minor ticks
    ax1.xaxis.set_major_formatter(mticker.ScalarFormatter())

    # reference line at 0
    ax1.axhline(
        0,
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        alpha=ZERO_LINE_ALPHA,
    )

    # labels & title
    # ax1.set_xlabel("Return level")
    # ax1.set_ylabel("Education loss", fontsize=YLABEL_SIZE)
    #ax2.set_ylabel("Health loss", fontsize=YLABEL_SIZE)
    ax1.set_title(sample.upper(), fontsize=TITLE_SIZE)

    ax1.tick_params(axis="x", labelsize=TICK_SIZE)
    ax1.tick_params(axis="y", labelsize=TICK_SIZE)
    ax2.tick_params(axis="y", labelsize=TICK_SIZE)

    plt.tight_layout()

    if SAVE_FIG:
        fig_path = PLOT_DIR / f"betaT_edu_health_twinx_sample_{sample}.png"
        #fig.savefig(fig_path, dpi=300)
        fig.savefig(fig_path, dpi=300, bbox_inches="tight", pad_inches=0.01)
        print(f"[SAVE] twinx plot saved (overwritten if existed): {fig_path}")

    plt.show()
    plt.close(fig)


# ========== main ==========

def main():
    df_storage_lin = load_storage_lin()
    df_health_Tagg = load_health_Tagg()

    for sample in SAMPLES:
        print(f"\n================ sample={sample} ================")
        curve_storage = get_storage_curve(df_storage_lin, sample)
        curve_health = get_health_curve(df_health_Tagg, sample)

        if curve_storage is None or curve_health is None:
            print(f"[WARN] sample={sample} missing curve info, skip plotting.")
            continue

        plot_twinx(curve_storage, curve_health, sample)

    print("[DONE] All requested twinx plots finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Original notebook comment normalized for the public code archive.
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["figure.dpi"] = 300

# Original notebook comment normalized for the public code archive.
PLOT_DIR = Path(r"E:\impact_assessment_child_order\data\figue2\plots_twinx")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Original notebook comment normalized for the public code archive.
# EDU_LINE_COLOR = "#8c510a"
# HEALTH_LINE_COLOR = "#01665e"
EDU_LEGEND_COLOR = "#8c510a"
HEALTH_LEGEND_COLOR = "#01665e"

LEGEND_FONTSIZE = 12
LEGEND_MARKERSIZE = 6


def save_point_only_legend():
    fig, ax = plt.subplots(figsize=(2.5, 1.0))
    ax.axis("off")

    handles = [
        Line2D(
            [], [],
            marker="o",
            linestyle="None",
            markersize=LEGEND_MARKERSIZE,
            markerfacecolor=EDU_LEGEND_COLOR,
            markeredgecolor=EDU_LEGEND_COLOR,
            label="Education loss",
        ),
        Line2D(
            [], [],
            marker="o",
            linestyle="None",
            markersize=LEGEND_MARKERSIZE,
            markerfacecolor=HEALTH_LEGEND_COLOR,
            markeredgecolor=HEALTH_LEGEND_COLOR,
            label="Health loss",
        ),
    ]

    ax.legend(
        handles=handles,
        loc="center",
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
        ncol=2,
    )

    fig.tight_layout()

    out_fp = PLOT_DIR / "legend_points_only.png"
    fig.savefig(out_fp, dpi=300, bbox_inches="tight", transparent=True)
    print(f"[SAVE] legend saved to: {out_fp}")

    plt.close(fig)


if __name__ == "__main__":
    save_point_only_legend()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
import numpy as np
import matplotlib.pyplot as plt

grad = np.linspace(0, 1, 512)[None, :]

plt.figure(figsize=(7, 1.2))
plt.imshow(grad, aspect="auto", cmap="cividis")
plt.yticks([])
plt.xticks([0, 128, 256, 384, 511], ["0.00", "0.25", "0.50", "0.75", "1.00"])
plt.title("Matplotlib colormap: cividis")
plt.tight_layout()
plt.show()
