#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 08_figure3_ab_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot beta(T) curves as separate SVG figures:

    1) Education panel only  -> SVG
    2) Health panel only     -> SVG

Inside each figure:
    - rural curve
    - urban curve

Data directory:
    BASE_DIR = E:\impact_assessment_child_order\data\figue2

Required files:
    1) storage_BM_linear_allT.csv
       - education regression results

    2) fe_health_index_z_Tall_windowAgg_over_T.csv
       - health regression results aggregated across windows

Notes:
    - Weighted polynomial meta-regression on log(T):
          beta(T) ≈ γ0 + γ1 log(T) + γ2 log(T)^2
    - x-axis is log-scale with ticks at T = 2, 5, 10, 20, 50, 100
    - Rural and urban elements are slightly dodged horizontally on log-x
    - Each figure uses symmetric y-axis around 0
"""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D


# =========================================================
# Global style
# =========================================================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams["svg.fonttype"] = "none"   # keep text editable in SVG


# =========================================================
# Paths & configuration
# =========================================================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")

STORAGE_CSV = BASE_DIR / "storage_BM_linear_allT.csv"
HEALTH_AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T.csv"

PLOT_DIR = BASE_DIR / "plots_by_outcome_rural_urban"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR_HEALTH = "health_index_z"

# Only compare rural and urban
SAMPLES_TO_PLOT = ["rural", "urban"]

T_LIST = [2, 5, 10, 20, 50, 100]

SAVE_SINGLE_SVGS = True
PRINT_WLS_SUMMARY = False


# =========================================================
# Figure style
# =========================================================
FIG_SIZE = (116.079 / 25.4, 79.044 / 25.4)   # mm -> inch

EDU_COLORS = {
    "rural": "#88b7d4",
    "urban": "#e45f4e",
}

HEALTH_COLORS = {
    "rural": "#88b7d4",
    "urban": "#e45f4e",
}

SAMPLE_LINESTYLE = {
    "rural": "--",
    "urban": "-",
}

BAND_FILL_ALPHA = 0.18
BAND_EDGE_ALPHA = 0.95
BAND_EDGE_WIDTH = 0.35

LINE_WIDTH = 1.8
LINE_ALPHA = 1.0

ERR_LINEWIDTH = 2.3
ERR_ALPHA = 0.88

POINT_SIZE = 46
POINT_ALPHA = 1.0

STAR_FONT_SIZE = 0

ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.0
ZERO_LINE_ALPHA = 0.85

TITLE_SIZE = 14
YLABEL_SIZE = 13
TICK_SIZE = 10
LEGEND_SIZE = 13

# log-x dodge for rural / urban
LOG_X_DODGE_SAMPLE = 0.04
SAMPLE_XMULT = {
    "rural": float(np.exp(-LOG_X_DODGE_SAMPLE)),
    "urban": float(np.exp(+LOG_X_DODGE_SAMPLE)),
}


# =========================================================
# Helpers
# =========================================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
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
    return mcolors.to_rgba(color, alpha=alpha)


def shift_x_log(x, xmult: float):
    x = np.asarray(x, dtype="float64")
    return x * xmult


# =========================================================
# Meta-regression for beta(T)
# =========================================================
def fit_beta_T_curve(
    T_vals_raw,
    est_raw,
    se_raw,
    ci_low_pts=None,
    ci_high_pts=None,
    p_vals=None,
    T_grid_n: int = 200,
):
    T_vals = np.asarray(T_vals_raw, dtype="float64")
    est = np.asarray(est_raw, dtype="float64")
    se = np.asarray(se_raw, dtype="float64")

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
                z = b / s
                p_b = 2.0 * (1.0 - norm_cdf(abs(z)))
            else:
                p_b = np.nan
            p_tmp.append(p_b)
        p_vals = np.asarray(p_tmp, dtype="float64")
    else:
        p_vals = np.asarray(p_vals, dtype="float64")

    order = np.argsort(T_vals)
    T_vals = T_vals[order]
    est = est[order]
    se = se[order]
    ci_low_pts = ci_low_pts[order]
    ci_high_pts = ci_high_pts[order]
    p_vals = p_vals[order]

    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

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

    if PRINT_WLS_SUMMARY:
        print(fit.summary())

    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

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

    beta_grid = np.asarray(beta_grid, dtype="float64")
    se_grid = np.asarray(se_grid, dtype="float64")
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


# =========================================================
# Load data
# =========================================================
def load_storage_lin() -> pd.DataFrame:
    print(f"[READ] Education results: {STORAGE_CSV}")
    df = pd.read_csv(STORAGE_CSV)

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["StdError"] = pd.to_numeric(df["StdError"], errors="coerce")

    if "CI_low" in df.columns:
        df["CI_low"] = pd.to_numeric(df["CI_low"], errors="coerce")
    if "CI_high" in df.columns:
        df["CI_high"] = pd.to_numeric(df["CI_high"], errors="coerce")
    if "PValue" in df.columns:
        df["PValue"] = pd.to_numeric(df["PValue"], errors="coerce")

    df = df.dropna(subset=["T", "Estimate", "StdError"])
    df["T"] = df["T"].astype(int)

    print("[INFO] Education head:")
    print(df.head())
    return df


def load_health_Tagg() -> pd.DataFrame:
    print(f"[READ] Health aggregated results: {HEALTH_AGG_CSV}")
    df = pd.read_csv(HEALTH_AGG_CSV)

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")
    df["2.5%"] = pd.to_numeric(df["2.5%"], errors="coerce")
    df["97.5%"] = pd.to_numeric(df["97.5%"], errors="coerce")
    df["Pr(>|t|)"] = pd.to_numeric(df["Pr(>|t|)"], errors="coerce")

    df = df.dropna(subset=["T", "Estimate", "Std. Error"])
    df["T"] = df["T"].astype(int)

    print("[INFO] Health head:")
    print(df.head())
    return df


# =========================================================
# Build curves
# =========================================================
def get_education_curve(df_storage: pd.DataFrame, sample: str):
    sub = df_storage[
        (df_storage["sample"] == sample)
        & (df_storage["T"].isin(T_LIST))
    ].copy()

    if sub.empty:
        print(f"[WARN] education sample={sample} is empty.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)
    ci_low_pts = sub["CI_low"].to_numpy(float) if "CI_low" in sub.columns else None
    ci_high_pts = sub["CI_high"].to_numpy(float) if "CI_high" in sub.columns else None
    p_vals = sub["PValue"].to_numpy(float) if "PValue" in sub.columns else None

    print(f"[INFO] Fit education beta(T), sample={sample}")
    return fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )


def get_health_curve(df_health: pd.DataFrame, sample: str):
    sub = df_health.copy()

    if "Y_var" in sub.columns:
        sub = sub[sub["Y_var"] == Y_VAR_HEALTH]

    sub = sub[
        (sub["sample"] == sample)
        & (sub["T"].isin(T_LIST))
    ].copy()

    if sub.empty:
        print(f"[WARN] health sample={sample} is empty.")
        return None

    sub = sub.sort_values("T")

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)
    ci_low_pts = sub["2.5%"].to_numpy(float)
    ci_high_pts = sub["97.5%"].to_numpy(float)
    p_vals = sub["Pr(>|t|)"].to_numpy(float)

    print(f"[INFO] Fit health beta(T), sample={sample}")
    return fit_beta_T_curve(
        T_vals,
        est,
        se,
        ci_low_pts=ci_low_pts,
        ci_high_pts=ci_high_pts,
        p_vals=p_vals,
    )


def build_curves_by_sample(df_storage: pd.DataFrame, df_health: pd.DataFrame):
    curves_edu = {}
    curves_health = {}

    for s in SAMPLES_TO_PLOT:
        curves_edu[s] = get_education_curve(df_storage, s)
        curves_health[s] = get_health_curve(df_health, s)

    return curves_edu, curves_health


# =========================================================
# Panel plotting helpers
# =========================================================
def compute_symmetric_ylim(curve_dict: dict, pad_factor: float = 1.06):
    vals = [0.0]
    for curve in curve_dict.values():
        if curve is None:
            continue
        vals.extend(curve["ci_low"].tolist())
        vals.extend(curve["ci_high"].tolist())
        vals.extend(curve["ci_pts_low"].tolist())
        vals.extend(curve["ci_pts_high"].tolist())

    vals = np.asarray(vals, dtype="float64")
    vals = vals[np.isfinite(vals)]

    if vals.size == 0:
        return -1.0, 1.0

    max_abs = float(max(np.max(np.abs(vals)), 1e-6))
    lim = max_abs * pad_factor
    return -lim, lim


def draw_panel(
    ax,
    curve_dict: dict,
    panel_title: str,
    ylabel: str,
    color_dict: dict,
    y_on_right: bool = False,
):
    for sample in SAMPLES_TO_PLOT:
        curve = curve_dict.get(sample, None)
        if curve is None:
            continue

        color = color_dict[sample]
        linestyle = SAMPLE_LINESTYLE[sample]
        xmult = SAMPLE_XMULT[sample]

        xg = shift_x_log(curve["T_grid"], xmult)
        xp = shift_x_log(curve["T_vals"], xmult)

        ax.plot(
            xg,
            curve["beta_grid"],
            color=rgba(color, LINE_ALPHA),
            linewidth=LINE_WIDTH,
            linestyle=linestyle,
            zorder=2,
            label=sample.capitalize(),
        )

        ax.fill_between(
            xg,
            curve["ci_low"],
            curve["ci_high"],
            facecolor=rgba(color, BAND_FILL_ALPHA),
            edgecolor=rgba(color, BAND_EDGE_ALPHA),
            linewidth=BAND_EDGE_WIDTH,
            zorder=1,
        )

        for x, lo, hi in zip(xp, curve["ci_pts_low"], curve["ci_pts_high"]):
            ax.vlines(
                x,
                lo,
                hi,
                color=rgba(color, ERR_ALPHA),
                linewidth=ERR_LINEWIDTH,
                zorder=3,
            )

        ax.scatter(
            xp,
            curve["est"],
            color=rgba(color, POINT_ALPHA),
            s=POINT_SIZE,
            zorder=4,
        )

    y_min, y_max = compute_symmetric_ylim(curve_dict, pad_factor=1.06)
    ax.set_ylim(y_min, y_max)

    if STAR_FONT_SIZE > 0:
        y_range = y_max - y_min
        y_offset = 0.03 * y_range
        for sample in SAMPLES_TO_PLOT:
            curve = curve_dict.get(sample, None)
            if curve is None:
                continue
            xmult = SAMPLE_XMULT[sample]
            xp = shift_x_log(curve["T_vals"], xmult)

            for x, b, p in zip(xp, curve["est"], curve["p_vals"]):
                s = stars_for_p(p)
                if s and np.isfinite(b):
                    ax.text(
                        x,
                        b + y_offset,
                        s,
                        ha="center",
                        va="bottom",
                        fontsize=STAR_FONT_SIZE,
                        zorder=5,
                    )

    all_shifted_x = []
    for sample in SAMPLES_TO_PLOT:
        curve = curve_dict.get(sample, None)
        if curve is None:
            continue
        xmult = SAMPLE_XMULT[sample]
        all_shifted_x.extend(shift_x_log(curve["T_grid"], xmult).tolist())
        all_shifted_x.extend(shift_x_log(curve["T_vals"], xmult).tolist())

    all_shifted_x = np.asarray(all_shifted_x, dtype="float64")
    all_shifted_x = all_shifted_x[np.isfinite(all_shifted_x)]

    if all_shifted_x.size > 0:
        xmin = float(np.min(all_shifted_x))
        xmax = float(np.max(all_shifted_x))
    else:
        xmin = min(T_LIST)
        xmax = max(T_LIST)

    ax.set_xscale("log")
    ax.set_xlim(xmin * 0.9, xmax * 1.1)
    ax.set_xticks(T_LIST)
    ax.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.xaxis.set_major_formatter(mticker.ScalarFormatter())

    ax.axhline(
        0,
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        alpha=ZERO_LINE_ALPHA,
        color="black",
    )

    ax.set_title(panel_title, fontsize=TITLE_SIZE)
    ax.set_ylabel(ylabel, fontsize=YLABEL_SIZE)

    yfmt = mticker.FormatStrFormatter("%.1f")
    ax.yaxis.set_major_formatter(yfmt)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(0.5)

    if y_on_right:
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.tick_params(axis="y", labelright=True, right=True, labelleft=False, left=False)
    else:
        ax.yaxis.set_label_position("left")
        ax.yaxis.tick_left()
        ax.tick_params(axis="y", labelleft=True, left=True, labelright=False, right=False)

    legend_handles = []
    for sample in SAMPLES_TO_PLOT:
        if curve_dict.get(sample, None) is None:
            continue
        legend_handles.append(
            Line2D(
                [0], [0],
                color=color_dict[sample],
                lw=LINE_WIDTH,
                linestyle=SAMPLE_LINESTYLE[sample],
                label=sample.capitalize(),
            )
        )
    if legend_handles:
        ax.legend(
            handles=legend_handles,
            frameon=False,
            fontsize=LEGEND_SIZE,
            loc="upper right",
        )


# =========================================================
# Separate SVG export
# =========================================================
def plot_single_panel_svg(
    curve_dict: dict,
    panel_title: str,
    ylabel: str,
    color_dict: dict,
    out_name: str,
    y_on_right: bool = False,
):
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    draw_panel(
        ax=ax,
        curve_dict=curve_dict,
        panel_title=panel_title,
        ylabel=ylabel,
        color_dict=color_dict,
        y_on_right=y_on_right,
    )

    ax.set_xlabel("Return level", fontsize=YLABEL_SIZE)

    plt.tight_layout()

    out_svg = PLOT_DIR / out_name
    fig.savefig(out_svg, format="svg")
    print(f"[SAVE] SVG saved: {out_svg}")

    plt.show()
    plt.close(fig)


# =========================================================
# Main
# =========================================================
def main():
    df_storage = load_storage_lin()
    df_health = load_health_Tagg()

    curves_edu, curves_health = build_curves_by_sample(df_storage, df_health)

    print("\n[INFO] Start exporting separate SVG figures ...")

    if SAVE_SINGLE_SVGS:
        # Education: y-axis on RIGHT
        plot_single_panel_svg(
            curve_dict=curves_edu,
            panel_title="",
            ylabel="Education loss",
            color_dict=EDU_COLORS,
            out_name="betaT_education_rural_urban.svg",
            y_on_right=True,
        )

        # Health: y-axis on LEFT
        plot_single_panel_svg(
            curve_dict=curves_health,
            panel_title="",
            ylabel="Health loss",
            color_dict=HEALTH_COLORS,
            out_name="betaT_health_rural_urban.svg",
            y_on_right=False,
        )

    print("[DONE] Finished.")


if __name__ == "__main__":
    main()
