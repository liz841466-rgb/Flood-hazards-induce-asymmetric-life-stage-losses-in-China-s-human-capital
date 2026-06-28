#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_dfo_child_elderly_result_loss_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from __future__ import annotations
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot-only (DFO severity curves):

Inputs (must exist in DATA_DIR):
  1) severity_poly_health_curve.csv
       columns: sample, s, beta, ci_low, ci_high
  2) severity_poly_health_points.csv
       columns: sample, sev_label, s, beta, ci_low, ci_high, pvalue
  3) severity_curve_edu_beta_points.csv
       columns: sample_type, s, Estimate, StdError, CI_low, CI_high, sev_label, PValue

Outputs (saved into DATA_DIR):
  - severity_poly_health_sample_all.png
  - severity_poly_health_sample_urban.png
  - severity_poly_health_sample_rural.png
  - severity_curve_edu_beta_sample_all.png
  - severity_curve_edu_beta_sample_rural.png
  - severity_curve_edu_beta_sample_urban.png
"""


from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# User configuration
# =========================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\DFO")

HEALTH_CURVE_CSV = DATA_DIR / "severity_poly_health_curve.csv"
HEALTH_POINTS_CSV = DATA_DIR / "severity_poly_health_points.csv"

EDU_POINTS_CSV = DATA_DIR / "severity_curve_edu_beta_points.csv"

SHOW_FIGURES = True  # set False for batch / headless runs


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update(
    {
        "figure.dpi": 300,
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 11,
    }
)


# =========================
# Helpers
# =========================
def require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"{name} is missing required columns: {sorted(missing)}")


def stars_for_p(p) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def format_sev_ticks(labels: list[str], s_vals: np.ndarray) -> list[str]:
    out = []
    for lab, s in zip(labels, s_vals):
        if lab == "sev1":
            out.append("sev1\n(s=1.0)")
        elif lab == "sev1.5":
            out.append("sev1.5\n(s=1.5)")
        elif lab == "sev1.5+2":
            out.append(f"sev1.5+2\n(s≈{s:.2f})")
        else:
            out.append(str(lab))
    return out


# =========================
# Health: use provided poly curve CSV + points CSV
# =========================
def plot_health_one(curve: pd.DataFrame, pts: pd.DataFrame, sample: str) -> None:
    c = curve[curve["sample"] == sample].copy()
    p = pts[pts["sample"] == sample].copy()
    if c.empty or p.empty:
        print(f"[SKIP] health sample='{sample}' has no curve/points rows.")
        return

    c = c.sort_values("s")
    p = p.sort_values("s")

    s_grid = c["s"].to_numpy(dtype=float)
    beta_grid = c["beta"].to_numpy(dtype=float)
    ci_low = c["ci_low"].to_numpy(dtype=float)
    ci_high = c["ci_high"].to_numpy(dtype=float)

    s_pts = p["s"].to_numpy(dtype=float)
    beta_pts = p["beta"].to_numpy(dtype=float)
    ci_pts_low = p["ci_low"].to_numpy(dtype=float)
    ci_pts_high = p["ci_high"].to_numpy(dtype=float)
    pvals = p["pvalue"].to_numpy(dtype=float)
    sev_labels = p["sev_label"].astype(str).tolist()

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    ax.plot(s_grid, beta_grid, color="black", label="β(s)")
    ax.fill_between(s_grid, ci_low, ci_high, alpha=0.22, label="95% CI")

    ax.errorbar(
        s_pts,
        beta_pts,
        yerr=[beta_pts - ci_pts_low, ci_pts_high - beta_pts],
        fmt="o",
        capsize=4,
        linestyle="none",
        color="black",
        label="Representative points",
    )

    y_span = float(np.nanmax(ci_high) - np.nanmin(ci_low))
    y_span = y_span if np.isfinite(y_span) and y_span > 0 else 1.0
    star_offset = 0.03 * y_span

    for sx, by, pv in zip(s_pts, beta_pts, pvals):
        st = stars_for_p(pv)
        if st:
            ax.text(sx, by + star_offset, st, ha="center", va="bottom", fontsize=10)

    ax.set_xticks(list(s_pts))
    ax.set_xticklabels(format_sev_ticks(sev_labels, s_pts))

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(float(np.nanmin(s_grid)), float(np.nanmax(s_grid)))
    ax.set_xlabel("DFO severity (s)")
    ax.set_ylabel("Marginal effect β(s) on health_index_z")
    ax.set_title(f"Nonlinear effect of DFO severity: β(s)\nSample = {sample}")
    ax.legend()
    plt.tight_layout()

    out_png = DATA_DIR / f"severity_poly_health_sample_{sample}.png"
    plt.savefig(out_png, dpi=300)
    if SHOW_FIGURES:
        plt.show()
    plt.close(fig)
    print(f"[OK] Saved: {out_png}")


def plot_health() -> None:
    if not HEALTH_CURVE_CSV.exists():
        raise FileNotFoundError(f"Missing file: {HEALTH_CURVE_CSV}")
    if not HEALTH_POINTS_CSV.exists():
        raise FileNotFoundError(f"Missing file: {HEALTH_POINTS_CSV}")

    curve = pd.read_csv(HEALTH_CURVE_CSV)
    pts = pd.read_csv(HEALTH_POINTS_CSV)

    require_columns(curve, {"sample", "s", "beta", "ci_low", "ci_high"}, "severity_poly_health_curve.csv")
    require_columns(
        pts,
        {"sample", "sev_label", "s", "beta", "ci_low", "ci_high", "pvalue"},
        "severity_poly_health_points.csv",
    )

    for sample in ["all", "urban", "rural"]:
        plot_health_one(curve, pts, sample)


# =========================
# Education: build continuous β(s) from point estimates (small n)
# =========================
def build_continuous_beta_from_points(sub: pd.DataFrame):
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("At least 2 severity points are required to build a continuous β(s).")

    # Exact polynomial interpolation (degree = n-1); n is small here (typically 3).
    deg = n - 1
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T

    var_vals = np.maximum(se_vals**2, 1e-12)
    Cov_B = np.diag(var_vals)

    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    s_grid = np.linspace(float(s_vals.min()), float(s_vals.max()), 201)
    Phi = np.vstack([s_grid**k for k in range(deg + 1)]).T

    beta_grid = Phi @ gamma
    var_grid = np.einsum("ij,jk,ik->i", Phi, Cov_gamma, Phi)
    var_grid = np.maximum(var_grid, 0.0)
    se_grid = np.sqrt(var_grid)

    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    return s_vals, beta_vals, s_grid, beta_grid, ci_low, ci_high


def plot_edu_one(df_pts: pd.DataFrame, sample_type: str) -> None:
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print(f"[SKIP] edu sample_type='{sample_type}' has no rows.")
        return

    sub = sub.sort_values("s").copy()
    s_vals, beta_vals, s_grid, beta_grid, ci_low_grid, ci_high_grid = build_continuous_beta_from_points(sub)

    ci_low_points = sub["CI_low"].to_numpy(dtype=float)
    ci_high_points = sub["CI_high"].to_numpy(dtype=float)
    labels = sub["sev_label"].astype(str).tolist()
    p_vals = sub["PValue"].to_numpy(dtype=float)

    y_min = float(np.nanmin([ci_low_points.min(), ci_low_grid.min()]))
    y_max = float(np.nanmax([ci_high_points.max(), ci_high_grid.max()]))
    pad = 0.12 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    star_offset = 0.04 * (y_upper - y_lower)

    fig, ax = plt.subplots(figsize=(6.0, 4.5))

    ax.plot(s_grid, beta_grid, color="black", label="β(s)")
    ax.fill_between(s_grid, ci_low_grid, ci_high_grid, alpha=0.18, label="95% CI")

    yerr = np.vstack([beta_vals - ci_low_points, ci_high_points - beta_vals])
    ax.errorbar(
        s_vals,
        beta_vals,
        yerr=yerr,
        fmt="o",
        capsize=4,
        linestyle="none",
        color="black",
        label="Representative points",
    )

    for sx, by, pv in zip(s_vals, beta_vals, p_vals):
        st = stars_for_p(pv)
        if st:
            ax.text(sx, by + star_offset, st, ha="center", va="bottom", fontsize=10)

    ax.set_xticks(list(s_vals))
    ax.set_xticklabels(format_sev_ticks(labels, s_vals))

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_xlim(float(s_vals.min()) - 0.05, float(s_vals.max()) + 0.05)
    ax.set_ylim(y_lower, y_upper)

    ax.set_xlabel("DFO severity (s)")
    ax.set_ylabel("Coefficient on share_severe_any (edu_beta)")
    ax.set_title(f"Continuous effect of DFO severity: β(s)\nSample = {sample_type}")
    ax.legend()
    plt.tight_layout()

    out_png = DATA_DIR / f"severity_curve_edu_beta_sample_{sample_type}.png"
    plt.savefig(out_png, dpi=300)
    if SHOW_FIGURES:
        plt.show()
    plt.close(fig)
    print(f"[OK] Saved: {out_png}")


def plot_edu() -> None:
    if not EDU_POINTS_CSV.exists():
        raise FileNotFoundError(f"Missing file: {EDU_POINTS_CSV}")

    df_pts = pd.read_csv(EDU_POINTS_CSV)
    require_columns(
        df_pts,
        {"sample_type", "s", "Estimate", "StdError", "CI_low", "CI_high", "sev_label", "PValue"},
        "severity_curve_edu_beta_points.csv",
    )

    for st in ["all", "rural", "urban"]:
        plot_edu_one(df_pts, st)


# =========================
# Main
# =========================
def main() -> None:
    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    plot_health()
    plot_edu()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DFO severity joint plot (Education + Health) using twinx.

Enhancement (per your request):
- Make the x-axis *evenly spaced by category* (sev1 / sev1.5 / sev1.5+2),
  so "sev1.5" is visually centered (not at the true numeric s=1.5 position).
- This is done via a monotone piecewise-linear "warp" from s -> x_index.

Inputs (must exist in DATA_DIR):
  1) severity_poly_health_curve.csv
       columns: sample, s, beta, ci_low, ci_high
  2) severity_poly_health_points.csv
       columns: sample, sev_label, s, beta, ci_low, ci_high, pvalue
  3) severity_curve_edu_beta_points.csv
       columns: sample_type, s, Estimate, StdError, CI_low, CI_high, sev_label, PValue

Outputs (saved into DATA_DIR):
  - severity_dfo_twinx_betaTstyle_sample_all.png
  - severity_dfo_twinx_betaTstyle_sample_urban.png
  - severity_dfo_twinx_betaTstyle_sample_rural.png
"""


from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# User configuration
# =========================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\DFO")

HEALTH_CURVE_CSV  = DATA_DIR / "severity_poly_health_curve.csv"
HEALTH_POINTS_CSV = DATA_DIR / "severity_poly_health_points.csv"
EDU_POINTS_CSV    = DATA_DIR / "severity_curve_edu_beta_points.csv"

SHOW_FIGURES = True  # Set False for batch / headless runs

# Do not show legend/title for now
SHOW_LEGEND = False
SHOW_TITLE  = False

# Align x by severity label (so sev1.5+2 is at one location)
ALIGN_S_BY_LABEL = True
CANONICAL_S_SOURCE = "health"  # "health" (recommended) or "mean"

# Preferred order of categories on x-axis
SEV_ORDER = ["sev1", "sev1.5", "sev1.5+2"]

# NEW: If True, x axis becomes evenly spaced categories (sev1 / sev1.5 / sev1.5+2)
# so "sev1.5" is in the middle visually.
USE_EVEN_SPACED_X = True


# =========================
# beta(T)-style appearance
# =========================
EDU_COLOR = "#8c510a"     # Education main color (brown)
HLT_COLOR = "#01665e"     # Health main color (teal)
CI_ALPHA  = 0.18
LINE_W    = 2.0
MARKER_SZ = 6.5
CAPSIZE   = 4

FORCE_SYMMETRIC_Y = True
Y_PAD_RATIO = 0.08        # 8% padding for symmetric ylim

# Axis text must be black
AXIS_TEXT_COLOR = "black"

# Zero line (keep as in many beta(T) figures)
ZERO_LINE_COLOR = "#1f77b4"
ZERO_LINE_STYLE = "--"
ZERO_LINE_W     = 1.2


# =========================
# Global plotting style (match beta(T) common settings)
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 18,
    "axes.labelsize": 18,
    "axes.titlesize": 18,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 15,
})


# =========================
# Helpers
# =========================
def require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"{name} is missing required columns: {sorted(missing)}")


def stars_for_p(p) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def format_sev_ticks(labels: list[str], s_vals: np.ndarray) -> list[str]:
    """
    X tick labels: show only severity1 / severity1.5 / severity1.5+2
    (no parentheses, no s values).
    """
    out = []
    for lab in labels:
        lab = str(lab)
        if lab.startswith("sev"):
            out.append(lab.replace("sev", "severity", 1))
        else:
            out.append(lab)
    return out


def symmetric_ylim_from_arrays(low: np.ndarray, high: np.ndarray, pad_ratio: float = Y_PAD_RATIO) -> tuple[float, float]:
    m = float(np.nanmax(np.abs(np.r_[low, high])))
    if not np.isfinite(m) or m <= 0:
        m = 1.0
    m = m * (1.0 + pad_ratio)
    return -m, m


def canonical_s_by_label(hp: pd.DataFrame, ep: pd.DataFrame) -> dict[str, float]:
    """
    Build a mapping sev_label -> canonical s.
    - source = "health": use health points' mean s for each label
    - source = "mean"  : use mean s across health+education points for each label
    """
    hp2 = hp.copy()
    ep2 = ep.copy()

    hp2["sev_label"] = hp2["sev_label"].astype(str)
    ep2["sev_label"] = ep2["sev_label"].astype(str)

    if CANONICAL_S_SOURCE.lower() == "mean":
        both = pd.concat(
            [
                hp2[["sev_label", "s"]].rename(columns={"s": "s_val"}),
                ep2[["sev_label", "s"]].rename(columns={"s": "s_val"}),
            ],
            axis=0,
            ignore_index=True,
        )
        m = both.groupby("sev_label")["s_val"].mean()
        return {k: float(v) for k, v in m.items()}

    # default: health
    m = hp2.groupby("sev_label")["s"].mean()
    return {k: float(v) for k, v in m.items()}


# =========================
# Education curve: build continuous beta(s) from representative points
# =========================
def build_continuous_beta_from_points(sub: pd.DataFrame):
    """
    Exact polynomial interpolation (degree = n-1) using representative points.
    Propagate uncertainty from point StdError (diagonal covariance).
    """
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("At least 2 severity points are required to build a continuous education beta(s).")

    deg = n - 1
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T

    var_vals = np.maximum(se_vals**2, 1e-12)
    Cov_B = np.diag(var_vals)

    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    s_grid = np.linspace(float(s_vals.min()), float(s_vals.max()), 201)
    Phi = np.vstack([s_grid**k for k in range(deg + 1)]).T

    beta_grid = Phi @ gamma
    var_grid = np.einsum("ij,jk,ik->i", Phi, Cov_gamma, Phi)
    var_grid = np.maximum(var_grid, 0.0)
    se_grid = np.sqrt(var_grid)

    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    return s_vals, beta_vals, s_grid, beta_grid, ci_low, ci_high


# =========================
# Main joint plot (beta(T)-style)
# =========================
def plot_joint_one(
    health_curve: pd.DataFrame,
    health_pts: pd.DataFrame,
    edu_pts: pd.DataFrame,
    sample: str
) -> None:

    # Subset (case-insensitive)
    hc = health_curve[health_curve["sample"].astype(str).str.lower() == sample].copy()
    hp = health_pts[health_pts["sample"].astype(str).str.lower() == sample].copy()
    ep = edu_pts[edu_pts["sample_type"].astype(str).str.lower() == sample].copy()

    if hc.empty or hp.empty or ep.empty:
        print(f"[SKIP] sample='{sample}' missing rows (health_curve/health_points/edu_points).")
        return

    hc = hc.sort_values("s")
    hp = hp.sort_values("s")
    ep = ep.sort_values("s")

    # Ensure label is string
    hp["sev_label"] = hp["sev_label"].astype(str)
    ep["sev_label"] = ep["sev_label"].astype(str)

    # Align s by label (fix duplicated 'sev1.5+2' locations)
    if ALIGN_S_BY_LABEL:
        c_map = canonical_s_by_label(hp, ep)

        # Education points: overwrite s for plotting & fitting
        ep_fit = ep.copy()
        ep_fit["s"] = ep_fit["sev_label"].map(c_map).fillna(ep_fit["s"])

        # Health points: keep as-is (already consistent with health curve),
        # but points to plot use canonical s
        hp_plot = hp.copy()
        hp_plot["s_plot"] = hp_plot["sev_label"].map(c_map).fillna(hp_plot["s"])
    else:
        ep_fit = ep.copy()
        hp_plot = hp.copy()
        hp_plot["s_plot"] = hp_plot["s"]

    # ---- Health (continuous provided) ----
    s_h_grid = hc["s"].to_numpy(dtype=float)
    h_beta_grid = hc["beta"].to_numpy(dtype=float)
    h_ci_low = hc["ci_low"].to_numpy(dtype=float)
    h_ci_high = hc["ci_high"].to_numpy(dtype=float)

    s_h_pts = hp_plot["s_plot"].to_numpy(dtype=float)
    h_beta_pts = hp_plot["beta"].to_numpy(dtype=float)
    h_ci_pts_low = hp_plot["ci_low"].to_numpy(dtype=float)
    h_ci_pts_high = hp_plot["ci_high"].to_numpy(dtype=float)
    h_pvals = hp_plot["pvalue"].to_numpy(dtype=float)

    # ---- Education (continuous built from points) ----
    s_e_pts, e_beta_pts, s_e_grid, e_beta_grid, e_ci_low_grid, e_ci_high_grid = build_continuous_beta_from_points(ep_fit)
    e_ci_pts_low = ep_fit["CI_low"].to_numpy(dtype=float)
    e_ci_pts_high = ep_fit["CI_high"].to_numpy(dtype=float)
    e_pvals = ep_fit["PValue"].to_numpy(dtype=float)

    # ---- X ticks: enforce one tick per sev_label in SEV_ORDER ----
    if ALIGN_S_BY_LABEL:
        c_map = canonical_s_by_label(hp, ep)
        labels_in_data = set(hp["sev_label"].unique()).union(set(ep["sev_label"].unique()))
        ordered_labels = [lab for lab in SEV_ORDER if lab in labels_in_data]
        remaining = [lab for lab in sorted(labels_in_data) if lab not in ordered_labels]
        ordered_labels += remaining

        tick_s = [float(c_map.get(lab, np.nan)) for lab in ordered_labels]
        tick_pairs = [(lab, s) for lab, s in zip(ordered_labels, tick_s) if np.isfinite(s)]

        # IMPORTANT: np.interp requires xp sorted ascending, so keep a sorted version by s
        tick_pairs = sorted(tick_pairs, key=lambda x: x[1])

        ordered_labels = [p[0] for p in tick_pairs]
        tick_s = [p[1] for p in tick_pairs]
        tick_labels = format_sev_ticks(ordered_labels, np.array(tick_s, dtype=float))
    else:
        tick_s = sorted(set(np.r_[s_h_pts, s_e_pts].tolist()))
        tick_labels = [f"{v:.2f}" for v in tick_s]

    # -------------------------
    # NEW: Optional x-warp to evenly-spaced categorical positions
    # sev1, sev1.5, sev1.5+2 -> 0, 1, 2 ... (1.5 is visually centered)
    # -------------------------
    if USE_EVEN_SPACED_X:
        s_anchor = np.array(tick_s, dtype=float)
        x_anchor = np.arange(len(s_anchor), dtype=float)

        def warp_s(arr):
            arr = np.asarray(arr, dtype=float)
            if len(s_anchor) < 2:
                return arr.copy()

            # interior interpolation
            x = np.interp(arr, s_anchor, x_anchor)

            # linear extrapolation on both sides (safer than clamping)
            left = arr < s_anchor[0]
            right = arr > s_anchor[-1]
            if left.any():
                slope = (x_anchor[1] - x_anchor[0]) / (s_anchor[1] - s_anchor[0])
                x[left] = x_anchor[0] + (arr[left] - s_anchor[0]) * slope
            if right.any():
                slope = (x_anchor[-1] - x_anchor[-2]) / (s_anchor[-1] - s_anchor[-2])
                x[right] = x_anchor[-1] + (arr[right] - s_anchor[-1]) * slope

            return x

        # Warp all x used for plotting
        x_e_grid = warp_s(s_e_grid)
        x_e_pts  = warp_s(s_e_pts)
        x_h_grid = warp_s(s_h_grid)
        x_h_pts  = warp_s(s_h_pts)

        x_ticks = x_anchor.tolist()
        x_ticklabels = tick_labels
        x_margin = 0.20
    else:
        # Original numeric axis
        x_e_grid, x_e_pts = s_e_grid, s_e_pts
        x_h_grid, x_h_pts = s_h_grid, s_h_pts
        x_ticks = tick_s
        x_ticklabels = tick_labels
        x_margin = 0.05

    # Figure
    fig, axL = plt.subplots(figsize=(7.6, 5.2))
    axR = axL.twinx()

    # Education: line + CI + points
    axL.plot(x_e_grid, e_beta_grid, color=EDU_COLOR, linewidth=LINE_W)
    axL.fill_between(x_e_grid, e_ci_low_grid, e_ci_high_grid, color=EDU_COLOR, alpha=CI_ALPHA, linewidth=0)
    axL.errorbar(
        x_e_pts, e_beta_pts,
        yerr=[e_beta_pts - e_ci_pts_low, e_ci_pts_high - e_beta_pts],
        fmt="o",
        markersize=MARKER_SZ,
        markerfacecolor=EDU_COLOR,
        markeredgecolor=EDU_COLOR,
        markeredgewidth=1.3,
        ecolor=EDU_COLOR,
        elinewidth=1.2,
        capsize=CAPSIZE,
        linestyle="none",
    )

    # Health: line + CI + points
    axR.plot(x_h_grid, h_beta_grid, color=HLT_COLOR, linewidth=LINE_W)
    axR.fill_between(x_h_grid, h_ci_low, h_ci_high, color=HLT_COLOR, alpha=CI_ALPHA, linewidth=0)
    axR.errorbar(
        x_h_pts, h_beta_pts,
        yerr=[h_beta_pts - h_ci_pts_low, h_ci_pts_high - h_beta_pts],
        fmt="o",
        markersize=MARKER_SZ,
        markerfacecolor=HLT_COLOR,
        markeredgecolor=HLT_COLOR,
        markeredgewidth=1.3,
        ecolor=HLT_COLOR,
        elinewidth=1.2,
        capsize=CAPSIZE,
        linestyle="none",
    )

    # Zero lines
    axL.axhline(0, linestyle=ZERO_LINE_STYLE, linewidth=ZERO_LINE_W, color=ZERO_LINE_COLOR)
    axR.axhline(0, linestyle=ZERO_LINE_STYLE, linewidth=ZERO_LINE_W, color=ZERO_LINE_COLOR)

    # Symmetric y-lims
    if FORCE_SYMMETRIC_Y:
        e_ymin, e_ymax = symmetric_ylim_from_arrays(
            np.r_[e_ci_pts_low, e_ci_low_grid],
            np.r_[e_ci_pts_high, e_ci_high_grid]
        )
        h_ymin, h_ymax = symmetric_ylim_from_arrays(
            np.r_[h_ci_pts_low, h_ci_low],
            np.r_[h_ci_pts_high, h_ci_high]
        )
        axL.set_ylim(e_ymin, e_ymax)
        axR.set_ylim(h_ymin, h_ymax)

    # Stars (kept as-is; note fontsize=0 means invisible; adjust if you want them visible)
    e_span = axL.get_ylim()[1] - axL.get_ylim()[0]
    h_span = axR.get_ylim()[1] - axR.get_ylim()[0]
    e_star_offset = 0.04 * e_span
    h_star_offset = 0.04 * h_span

    for sx, by, pv in zip(x_e_pts, e_beta_pts, e_pvals):
        st = stars_for_p(pv)
        if st:
            axL.text(float(sx), float(by) + e_star_offset, st,
                     ha="center", va="bottom", fontsize=0, color=EDU_COLOR)

    for sx, by, pv in zip(x_h_pts, h_beta_pts, h_pvals):
        st = stars_for_p(pv)
        if st:
            axR.text(float(sx), float(by) + h_star_offset, st,
                     ha="center", va="bottom", fontsize=0, color=HLT_COLOR)

    # X axis
    axL.set_xticks(x_ticks)
    axL.set_xticklabels(x_ticklabels)
    axL.set_xlim(min(x_ticks) - x_margin, max(x_ticks) + x_margin)
    axL.set_xlabel("DFO severity", color=AXIS_TEXT_COLOR)

    # Y labels in BLACK
    axL.set_ylabel("Education effect", color=AXIS_TEXT_COLOR)
    axR.set_ylabel("Health effect", color=AXIS_TEXT_COLOR)

    # Y tick colors in BLACK
    axL.tick_params(axis="y", colors=AXIS_TEXT_COLOR)
    axR.tick_params(axis="y", colors=AXIS_TEXT_COLOR)
    axL.tick_params(axis="x", colors=AXIS_TEXT_COLOR)

    # Remove title / legend for now
    if SHOW_TITLE:
        axL.set_title(f"Nonlinear effects of DFO severity: Education vs. Health\nSample = {sample}")
    if SHOW_LEGEND:
        axL.legend(loc="best", frameon=True)

    plt.tight_layout()

    out_png = DATA_DIR / f"severity_dfo_twinx_betaTstyle_sample_{sample}.png"
    plt.savefig(out_png, dpi=300)
    if SHOW_FIGURES:
        plt.show()
    plt.close(fig)

    print(f"[OK] Saved: {out_png}")


def main() -> None:
    for fp in [HEALTH_CURVE_CSV, HEALTH_POINTS_CSV, EDU_POINTS_CSV]:
        if not fp.exists():
            raise FileNotFoundError(f"Missing file: {fp}")

    health_curve = pd.read_csv(HEALTH_CURVE_CSV)
    health_pts = pd.read_csv(HEALTH_POINTS_CSV)
    edu_pts = pd.read_csv(EDU_POINTS_CSV)

    require_columns(health_curve, {"sample", "s", "beta", "ci_low", "ci_high"}, "severity_poly_health_curve.csv")
    require_columns(health_pts, {"sample", "sev_label", "s", "beta", "ci_low", "ci_high", "pvalue"}, "severity_poly_health_points.csv")
    require_columns(edu_pts, {"sample_type", "s", "Estimate", "StdError", "CI_low", "CI_high", "sev_label", "PValue"}, "severity_curve_edu_beta_points.csv")

    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] ALIGN_S_BY_LABEL={ALIGN_S_BY_LABEL}, USE_EVEN_SPACED_X={USE_EVEN_SPACED_X}, CANONICAL_S_SOURCE={CANONICAL_S_SOURCE}")

    for sample in ["all", "urban", "rural"]:
        plot_joint_one(health_curve, health_pts, edu_pts, sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DFO severity joint plot (Education + Health) using twinx.

Your requested display change:
- ONLY move the *sev1.5* position to the visual midpoint between sev1 and sev1.5+2 on the x-axis.
- All computations (beta, CI, fitting) still use the original s values.
- We do this by applying a monotone piecewise-linear x-warp ONLY for plotting:
    warp(sev1)      = sev1 (unchanged)
    warp(sev1.5+2)  = sev1.5+2 (unchanged)
    warp(sev1.5)    = midpoint between the above two (visual centering)

Additional display changes you requested:
- Left y-axis fixed to [-1.2, 1.2], but ticks shown only from -1.0 to 1.0
- Right y-axis fixed to [-1.2, 1.2], but ticks shown only from -1.0 to 1.0
- Do NOT show y-axis titles

Inputs (must exist in DATA_DIR):
  1) severity_poly_health_curve.csv
       columns: sample, s, beta, ci_low, ci_high
  2) severity_poly_health_points.csv
       columns: sample, sev_label, s, beta, ci_low, ci_high, pvalue
  3) severity_curve_edu_beta_points.csv
       columns: sample_type, s, Estimate, StdError, CI_low, CI_high, sev_label, PValue

Outputs (saved into DATA_DIR):
  - severity_dfo_twinx_betaTstyle_sample_all.png
  - severity_dfo_twinx_betaTstyle_sample_urban.png
  - severity_dfo_twinx_betaTstyle_sample_rural.png
"""


from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =========================
# User configuration
# =========================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\DFO")

HEALTH_CURVE_CSV  = DATA_DIR / "severity_poly_health_curve.csv"
HEALTH_POINTS_CSV = DATA_DIR / "severity_poly_health_points.csv"
EDU_POINTS_CSV    = DATA_DIR / "severity_curve_edu_beta_points.csv"

SHOW_FIGURES = True   # Set False for batch / headless runs

# Do not show legend/title for now
SHOW_LEGEND = False
SHOW_TITLE  = False

# Align x by severity label (so sev1.5+2 appears at one location)
ALIGN_S_BY_LABEL = True
CANONICAL_S_SOURCE = "health"  # "health" (recommended) or "mean"

# Preferred order of categories on x-axis
SEV_ORDER = ["sev1", "sev1.5", "sev1.5+2"]

# ONLY move sev1.5 to the visual midpoint between sev1 and sev1.5+2
MOVE_ONLY_SEV1_5_TO_MIDDLE = True


# =========================
# beta(T)-style appearance
# =========================
EDU_COLOR = "#8c510a"     # Education main color (brown)
HLT_COLOR = "#01665e"     # Health main color (teal)
CI_ALPHA  = 0.18
LINE_W    = 3.5
MARKER_SZ = 6.5
CAPSIZE   = 6

# Fixed y-axis display as requested
FIXED_YLIM = (-1.8, 1.8)
#FIXED_YTICKS = np.arange(-1.0, 1.01, 0.5)   # only show ticks from -1.0 to 1.0
FIXED_YTICKS = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5])

# Axis text must be black
AXIS_TEXT_COLOR = "black"

# Zero line
ZERO_LINE_COLOR = "#1f77b4"
ZERO_LINE_STYLE = "--"
ZERO_LINE_W     = 1.2


# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 20,
    "axes.labelsize": 20,
    "axes.titlesize": 20,
    "xtick.labelsize": 23,
    "ytick.labelsize": 23,
    "legend.fontsize": 20,
})


# =========================
# Helpers
# =========================
def require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"{name} is missing required columns: {sorted(missing)}")


def stars_for_p(p) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def format_sev_ticks(labels: list[str]) -> list[str]:
    out = []
    for lab in labels:
        lab = str(lab)
        if lab.startswith("sev"):
            out.append(lab.replace("sev", "severity", 1))
        else:
            out.append(lab)
    return out


def canonical_s_by_label(hp: pd.DataFrame, ep: pd.DataFrame) -> dict[str, float]:
    """
    Build a mapping sev_label -> canonical s.
    - source = "health": use health points' mean s for each label
    - source = "mean"  : use mean s across health+education points for each label
    """
    hp2 = hp.copy()
    ep2 = ep.copy()

    hp2["sev_label"] = hp2["sev_label"].astype(str)
    ep2["sev_label"] = ep2["sev_label"].astype(str)

    if CANONICAL_S_SOURCE.lower() == "mean":
        both = pd.concat(
            [
                hp2[["sev_label", "s"]].rename(columns={"s": "s_val"}),
                ep2[["sev_label", "s"]].rename(columns={"s": "s_val"}),
            ],
            axis=0,
            ignore_index=True,
        )
        m = both.groupby("sev_label")["s_val"].mean()
        return {k: float(v) for k, v in m.items()}

    m = hp2.groupby("sev_label")["s"].mean()
    return {k: float(v) for k, v in m.items()}


def make_sev15_mid_warp(c_map: dict[str, float]):
    """
    Piecewise-linear warp that keeps sev1 and sev1.5+2 fixed,
    but maps sev1.5 to their midpoint.
    If any required anchor is missing or degenerate, returns identity.
    """
    need = ("sev1", "sev1.5", "sev1.5+2")
    if not all(k in c_map for k in need):
        return lambda a: np.asarray(a, dtype=float)

    s1 = float(c_map["sev1"])
    s2 = float(c_map["sev1.5"])
    s3 = float(c_map["sev1.5+2"])

    anchors = sorted([(s1, "sev1"), (s2, "sev1.5"), (s3, "sev1.5+2")], key=lambda x: x[0])
    s1 = anchors[0][0]
    s2 = anchors[1][0]
    s3 = anchors[2][0]

    if not (np.isfinite(s1) and np.isfinite(s2) and np.isfinite(s3)):
        return lambda a: np.asarray(a, dtype=float)
    if not (s1 < s2 < s3):
        return lambda a: np.asarray(a, dtype=float)

    x1 = s1
    x3 = s3
    x2 = (x1 + x3) / 2.0

    mL = (x2 - x1) / (s2 - s1)
    mR = (x3 - x2) / (s3 - s2)

    def warp(arr):
        arr = np.asarray(arr, dtype=float)
        x = arr.copy()

        left = arr <= s2
        right = ~left

        x[left] = x1 + (arr[left] - s1) * mL
        x[right] = x2 + (arr[right] - s2) * mR
        return x

    return warp


# =========================
# Education curve: build continuous beta(s) from representative points
# =========================
def build_continuous_beta_from_points(sub: pd.DataFrame):
    """
    Exact polynomial interpolation (degree = n-1) using representative points.
    Propagate uncertainty from point StdError (diagonal covariance).
    """
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("At least 2 severity points are required to build a continuous education beta(s).")

    deg = n - 1
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T

    var_vals = np.maximum(se_vals**2, 1e-12)
    Cov_B = np.diag(var_vals)

    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    s_grid = np.linspace(float(s_vals.min()), float(s_vals.max()), 201)
    Phi = np.vstack([s_grid**k for k in range(deg + 1)]).T

    beta_grid = Phi @ gamma
    var_grid = np.einsum("ij,jk,ik->i", Phi, Cov_gamma, Phi)
    var_grid = np.maximum(var_grid, 0.0)
    se_grid = np.sqrt(var_grid)

    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    return s_vals, beta_vals, s_grid, beta_grid, ci_low, ci_high


# =========================
# Main joint plot
# =========================
def plot_joint_one(
    health_curve: pd.DataFrame,
    health_pts: pd.DataFrame,
    edu_pts: pd.DataFrame,
    sample: str
) -> None:

    hc = health_curve[health_curve["sample"].astype(str).str.lower() == sample].copy()
    hp = health_pts[health_pts["sample"].astype(str).str.lower() == sample].copy()
    ep = edu_pts[edu_pts["sample_type"].astype(str).str.lower() == sample].copy()

    if hc.empty or hp.empty or ep.empty:
        print(f"[SKIP] sample='{sample}' missing rows (health_curve/health_points/edu_points).")
        return

    hc = hc.sort_values("s")
    hp = hp.sort_values("s")
    ep = ep.sort_values("s")

    hp["sev_label"] = hp["sev_label"].astype(str)
    ep["sev_label"] = ep["sev_label"].astype(str)

    # Align s by label
    if ALIGN_S_BY_LABEL:
        c_map = canonical_s_by_label(hp, ep)

        ep_fit = ep.copy()
        ep_fit["s"] = ep_fit["sev_label"].map(c_map).fillna(ep_fit["s"])

        hp_plot = hp.copy()
        hp_plot["s_plot"] = hp_plot["sev_label"].map(c_map).fillna(hp_plot["s"])
    else:
        c_map = canonical_s_by_label(hp, ep)
        ep_fit = ep.copy()
        hp_plot = hp.copy()
        hp_plot["s_plot"] = hp_plot["s"]

    # ---- Health ----
    s_h_grid = hc["s"].to_numpy(dtype=float)
    h_beta_grid = hc["beta"].to_numpy(dtype=float)
    h_ci_low = hc["ci_low"].to_numpy(dtype=float)
    h_ci_high = hc["ci_high"].to_numpy(dtype=float)

    s_h_pts = hp_plot["s_plot"].to_numpy(dtype=float)
    h_beta_pts = hp_plot["beta"].to_numpy(dtype=float)
    h_ci_pts_low = hp_plot["ci_low"].to_numpy(dtype=float)
    h_ci_pts_high = hp_plot["ci_high"].to_numpy(dtype=float)
    h_pvals = hp_plot["pvalue"].to_numpy(dtype=float)

    # ---- Education ----
    s_e_pts, e_beta_pts, s_e_grid, e_beta_grid, e_ci_low_grid, e_ci_high_grid = build_continuous_beta_from_points(ep_fit)
    e_ci_pts_low = ep_fit["CI_low"].to_numpy(dtype=float)
    e_ci_pts_high = ep_fit["CI_high"].to_numpy(dtype=float)
    e_pvals = ep_fit["PValue"].to_numpy(dtype=float)

    # ---- Tick labels/order ----
    labels_in_data = set(hp["sev_label"].unique()).union(set(ep["sev_label"].unique()))
    ordered_labels = [lab for lab in SEV_ORDER if lab in labels_in_data]
    remaining = [lab for lab in sorted(labels_in_data) if lab not in ordered_labels]
    ordered_labels += remaining

    tick_s = []
    for lab in ordered_labels:
        if lab in c_map and np.isfinite(c_map[lab]):
            tick_s.append(float(c_map[lab]))
        else:
            s_candidates = []
            s_candidates += hp.loc[hp["sev_label"] == lab, "s"].tolist()
            s_candidates += ep.loc[ep["sev_label"] == lab, "s"].tolist()
            s_candidates = [float(x) for x in s_candidates if pd.notna(x)]
            tick_s.append(float(np.mean(s_candidates)) if len(s_candidates) else np.nan)

    tick_pairs = [(lab, s) for lab, s in zip(ordered_labels, tick_s) if np.isfinite(s)]
    tick_pairs = sorted(tick_pairs, key=lambda x: x[1])

    ordered_labels = [p[0] for p in tick_pairs]
    tick_s = [p[1] for p in tick_pairs]
    tick_labels = format_sev_ticks(ordered_labels)

    # ---- X warp ----
    if MOVE_ONLY_SEV1_5_TO_MIDDLE:
        warp_x = make_sev15_mid_warp(c_map)
    else:
        warp_x = lambda a: np.asarray(a, dtype=float)

    x_h_grid = warp_x(s_h_grid)
    x_h_pts  = warp_x(s_h_pts)
    x_e_grid = warp_x(s_e_grid)
    x_e_pts  = warp_x(s_e_pts)

    x_ticks = warp_x(np.array(tick_s, dtype=float)).tolist()

    # Figure
    fig, axL = plt.subplots(figsize=(7.6, 6.2))
    axR = axL.twinx()

    # Education
    axL.plot(x_e_grid, e_beta_grid, color=EDU_COLOR, linewidth=LINE_W)
    axL.fill_between(x_e_grid, e_ci_low_grid, e_ci_high_grid, color=EDU_COLOR, alpha=CI_ALPHA, linewidth=0)
    axL.errorbar(
        x_e_pts, e_beta_pts,
        yerr=[e_beta_pts - e_ci_pts_low, e_ci_pts_high - e_beta_pts],
        fmt="o",
        markersize=MARKER_SZ,
        markerfacecolor=EDU_COLOR,
        markeredgecolor=EDU_COLOR,
        markeredgewidth=1.3,
        ecolor=EDU_COLOR,
        elinewidth=1.2,
        capsize=CAPSIZE,
        linestyle="none",
    )

    # Health
    axR.plot(x_h_grid, h_beta_grid, color=HLT_COLOR, linewidth=LINE_W)
    axR.fill_between(x_h_grid, h_ci_low, h_ci_high, color=HLT_COLOR, alpha=CI_ALPHA, linewidth=0)
    axR.errorbar(
        x_h_pts, h_beta_pts,
        yerr=[h_beta_pts - h_ci_pts_low, h_ci_pts_high - h_beta_pts],
        fmt="o",
        markersize=MARKER_SZ,
        markerfacecolor=HLT_COLOR,
        markeredgecolor=HLT_COLOR,
        markeredgewidth=1.3,
        ecolor=HLT_COLOR,
        elinewidth=1.2,
        capsize=CAPSIZE,
        linestyle="none",
    )

    # Zero lines
    axL.axhline(0, linestyle=ZERO_LINE_STYLE, linewidth=ZERO_LINE_W, color=ZERO_LINE_COLOR)
    axR.axhline(0, linestyle=ZERO_LINE_STYLE, linewidth=ZERO_LINE_W, color=ZERO_LINE_COLOR)

    # Fixed y-limits and ticks
    axL.set_ylim(FIXED_YLIM)
    axR.set_ylim(FIXED_YLIM)

    axL.set_yticks(FIXED_YTICKS)
    axR.set_yticks(FIXED_YTICKS)

    axL.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    axR.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

    # Stars (currently hidden as fontsize=0; keep your original behavior)
    e_span = axL.get_ylim()[1] - axL.get_ylim()[0]
    h_span = axR.get_ylim()[1] - axR.get_ylim()[0]
    e_star_offset = 0.04 * e_span
    h_star_offset = 0.04 * h_span

    for sx, by, pv in zip(x_e_pts, e_beta_pts, e_pvals):
        st = stars_for_p(pv)
        if st:
            axL.text(float(sx), float(by) + e_star_offset, st,
                     ha="center", va="bottom", fontsize=0, color=EDU_COLOR)

    for sx, by, pv in zip(x_h_pts, h_beta_pts, h_pvals):
        st = stars_for_p(pv)
        if st:
            axR.text(float(sx), float(by) + h_star_offset, st,
                     ha="center", va="bottom", fontsize=0, color=HLT_COLOR)

    # X axis
    axL.set_xticks(x_ticks)
    axL.set_xticklabels(tick_labels)

    xmin = float(np.nanmin(np.r_[x_h_grid, x_e_grid, x_ticks]))
    xmax = float(np.nanmax(np.r_[x_h_grid, x_e_grid, x_ticks]))
    axL.set_xlim(xmin - 0.05, xmax + 0.05)

    # No y-axis titles
    axL.set_ylabel("")
    axR.set_ylabel("")
    # Tick display
    axL.tick_params(axis="y", colors=AXIS_TEXT_COLOR, labelleft=False)
    axR.tick_params(axis="y", colors=AXIS_TEXT_COLOR, labelright=False)
    axL.tick_params(axis="x", colors=AXIS_TEXT_COLOR)

    # Tick colors in black
    axL.tick_params(axis="y", colors=AXIS_TEXT_COLOR)
    axR.tick_params(axis="y", colors=AXIS_TEXT_COLOR)
    axL.tick_params(axis="x", colors=AXIS_TEXT_COLOR)

    if SHOW_TITLE:
        axL.set_title(f"Nonlinear effects of DFO severity: Education vs. Health\nSample = {sample}")
    if SHOW_LEGEND:
        axL.legend(loc="best", frameon=True)

    plt.tight_layout()

    out_png = DATA_DIR / f"severity_dfo_twinx_betaTstyle_sample_{sample}.png"
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    if SHOW_FIGURES:
        plt.show()
    plt.close(fig)

    print(f"[OK] Saved: {out_png}")


def main() -> None:
    for fp in [HEALTH_CURVE_CSV, HEALTH_POINTS_CSV, EDU_POINTS_CSV]:
        if not fp.exists():
            raise FileNotFoundError(f"Missing file: {fp}")

    health_curve = pd.read_csv(HEALTH_CURVE_CSV)
    health_pts = pd.read_csv(HEALTH_POINTS_CSV)
    edu_pts = pd.read_csv(EDU_POINTS_CSV)

    require_columns(health_curve, {"sample", "s", "beta", "ci_low", "ci_high"}, "severity_poly_health_curve.csv")
    require_columns(health_pts, {"sample", "sev_label", "s", "beta", "ci_low", "ci_high", "pvalue"}, "severity_poly_health_points.csv")
    require_columns(edu_pts, {"sample_type", "s", "Estimate", "StdError", "CI_low", "CI_high", "sev_label", "PValue"}, "severity_curve_edu_beta_points.csv")

    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] ALIGN_S_BY_LABEL={ALIGN_S_BY_LABEL}, MOVE_ONLY_SEV1_5_TO_MIDDLE={MOVE_ONLY_SEV1_5_TO_MIDDLE}, CANONICAL_S_SOURCE={CANONICAL_S_SOURCE}")
    print(f"[INFO] FIXED_YLIM={FIXED_YLIM}, FIXED_YTICKS={FIXED_YTICKS.tolist()}")

    for sample in ["all", "urban", "rural"]:
        plot_joint_one(health_curve, health_pts, edu_pts, sample)


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

# ====== Config ======
OUT_PNG = Path(r"E:\impact_assessment_child_order\data\supplement\DFO") / "legend_points_edu_health.png"

# Original notebook comment normalized for the public code archive.
EDU_COLOR = "#8c510a"
HLT_COLOR = "#01665e"

FONT_SIZE = 28
MARKER_SIZE = 16  # Original notebook comment normalized for the public code archive.
TRANSPARENT_BG = False  # Original notebook comment normalized for the public code archive.
# ====================

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(6.0, 1.6))
ax.axis("off")

# Original notebook comment normalized for the public code archive.
handles = [
    Line2D([], [], linestyle="None", marker="o",
           markersize=MARKER_SIZE, markerfacecolor=EDU_COLOR, markeredgecolor=EDU_COLOR,
           label="Education loss"),
    Line2D([], [], linestyle="None", marker="o",
           markersize=MARKER_SIZE, markerfacecolor=HLT_COLOR, markeredgecolor=HLT_COLOR,
           label="Health loss"),
]

ax.legend(
    handles=handles,
    loc="center left",
    frameon=False,
    ncol=1,
    fontsize=FONT_SIZE,
    handletextpad=0.8,
    labelspacing=0.6,
    borderaxespad=0.0,
)

plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=TRANSPARENT_BG)
plt.close(fig)

print(f"[OK] Saved: {OUT_PNG}")
