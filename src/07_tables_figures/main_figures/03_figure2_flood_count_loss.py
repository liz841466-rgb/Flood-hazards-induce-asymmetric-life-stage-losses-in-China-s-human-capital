#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_figure2_flood_count_loss.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scheme B: Wedge-shaped uncertainty bands for more/fewer flood events
(all return periods overlaid in one figure), plus a separate legend
figure where colors represent return periods T.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ========== global style (Times New Roman, 300 dpi) ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300

# ========== paths & configuration ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")

RES_TAGG = BASE_DIR / (
    "fe_piecewise_health_index_z_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_meanSplit_Tagg.csv"
)

PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR = "health_index_z"

# return periods (order)
T_LIST = [2, 5, 10, 20, 50, 100]

# samples
SAMPLES = ["all", "rural", "urban"]

# range of Δk (relative to mean frequency)
K_MAX_MORE = 2   # Δk > 0: up to +K_MAX_MORE floods
K_MAX_LESS = 2   # Δk < 0: down to -K_MAX_LESS floods

# z-value for two-sided 95% CI
Z_ALPHA_2 = 1.96

# colors for each return period T (line + band)
T_COLORS = {
    2:   "#016450",
    5:   "#02818a",
    10:  "#3690c0",
    20:  "#67a9cf",
    50:  "#a6bddb",
    100: "#d0d1e6",
}

# band transparency
BAND_ALPHA = 0.50

# figure size
FIG_SIZE = (7, 4.5)

# symmetric x-limits padding
X_PAD = 0.1  # padding beyond max(|Δk|)

# whether to show generic (line + band) legend on main plot
SHOW_MAIN_LEGEND = False

# ===== font sizes (edit here to tune figure text) =====
TITLE_FONTSIZE  = 14   # figure title
LABEL_FONTSIZE  = 12   # x / y axis labels
TICK_FONTSIZE   = 15   # tick labels on both axes
LEGEND_FONTSIZE = 10   # standalone legend figure
STAR_FONTSIZE   = 0    # significance stars; set 0 to hide


# ========== helpers ==========

def read_Tagg() -> pd.DataFrame:
    print(f"[READ] aggregated piecewise FE results: {RES_TAGG}")
    df = pd.read_csv(RES_TAGG)

    need_cols = [
        "Y_var", "sample", "T",
        "beta_below", "se_below", "p_below",
        "beta_above", "se_above", "p_above",
        "N_bar_mean",
    ]
    miss = [c for c in need_cols if c not in df.columns]
    if miss:
        raise KeyError(f"Missing required columns in Tagg results: {miss}")

    # keep target outcome
    df = df[df["Y_var"] == Y_VAR].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce").astype(int)
    df["N_bar_mean"] = pd.to_numeric(df["N_bar_mean"], errors="coerce")

    for col in [
        "beta_below", "se_below", "p_below",
        "beta_above", "se_above", "p_above"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep selected return periods
    df = df[df["T"].isin(T_LIST)].copy()
    df = df.sort_values(["sample", "T"])

    print("[INFO] example rows:")
    print(df.head())
    return df


def stars_for_p(p: float) -> str:
    """Return significance stars based on p-value."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def plot_piecewise_band_k_overlay(
    df_Tagg: pd.DataFrame,
    sample: str = "all",
    k_max_more: int = K_MAX_MORE,
    k_max_less: int = K_MAX_LESS,
    z_value: float = Z_ALPHA_2,
):
    """
    For a given sample ("all" / "rural" / "urban"), overlay wedge-shaped bands
    for all return periods T on a single figure.
    """
    sub = df_Tagg[df_Tagg["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows, skip plotting.")
        return

    # keep T in desired order
    T_used = [T for T in T_LIST if T in sub["T"].unique()]
    sub = sub[sub["T"].isin(T_used)].copy()
    sub = sub.sort_values("T")

    if len(T_used) == 0:
        print(f"[WARN] sample={sample} has no requested return periods, skip plotting.")
        return

    # ---- compute global y-range for all bands ----
    y_all = []

    for _, row in sub.iterrows():
        beta_above = row["beta_above"]
        se_above = row["se_above"]
        beta_below = row["beta_below"]
        se_below = row["se_below"]

        dk_less = np.arange(-k_max_less, 1)        # ≤ 0
        dk_more = np.arange(0, k_max_more + 1)     # ≥ 0

        mu_less = dk_less * beta_below
        se_less = np.abs(dk_less) * se_below
        ci_less_low = mu_less - z_value * se_less
        ci_less_high = mu_less + z_value * se_less

        mu_more = dk_more * beta_above
        se_more = np.abs(dk_more) * se_above
        ci_more_low = mu_more - z_value * se_more
        ci_more_high = mu_more + z_value * se_more

        y_all.extend(ci_less_low)
        y_all.extend(ci_less_high)
        y_all.extend(ci_more_low)
        y_all.extend(ci_more_high)

    y_all = np.array([y for y in y_all if np.isfinite(y)])
    if y_all.size == 0:
        print(f"[WARN] sample={sample} all y are NaN, skip plotting.")
        return

    y_min = y_all.min()
    y_max = y_all.max()
    y_pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)

    dk_min = -k_max_less
    dk_max = k_max_more

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    sample_label = sample.upper()  # e.g., "ALL", "RURAL", "URBAN"

    # ===== draw wedges and lines for each T =====
    for T in T_used:
        row_T = sub[sub["T"] == T].iloc[0]

        beta_above = row_T.beta_above
        se_above = row_T.se_above
        beta_below = row_T.beta_below
        se_below = row_T.se_below

        color = T_COLORS.get(T, "#000000")  # fallback: black

        dk_less = np.arange(-k_max_less, 0 + 1)   # ≤ 0
        dk_more = np.arange(0, k_max_more + 1)    # ≥ 0

        mu_less = dk_less * beta_below
        se_less = np.abs(dk_less) * se_below
        ci_less_low = mu_less - z_value * se_less
        ci_less_high = mu_less + z_value * se_less

        mu_more = dk_more * beta_above
        se_more = np.abs(dk_more) * se_above
        ci_more_low = mu_more - z_value * se_more
        ci_more_high = mu_more + z_value * se_more

        ax.fill_between(
            dk_less, ci_less_low, ci_less_high,
            alpha=BAND_ALPHA,
            color=color,
            linewidth=0,
        )
        ax.plot(
            dk_less, mu_less,
            color=color,
            linestyle="-",
            linewidth=1.5,
        )

        ax.fill_between(
            dk_more, ci_more_low, ci_more_high,
            alpha=BAND_ALPHA,
            color=color,
            linewidth=0,
        )
        ax.plot(
            dk_more, mu_more,
            color=color,
            linestyle="-",
            linewidth=1.5,
        )

        # significance stars at Δk = ±1 (only if STAR_FONTSIZE > 0)
        if STAR_FONTSIZE > 0:
            if 1 <= k_max_more:
                star_above = stars_for_p(row_T.p_above)
                if star_above:
                    y_star = beta_above * 1
                    ax.text(
                        1.02,
                        y_star,
                        star_above,
                        color=color,
                        fontsize=STAR_FONTSIZE,
                        ha="left",
                        va="bottom",
                    )

            if 1 <= k_max_less:
                star_below = stars_for_p(row_T.p_below)
                if star_below:
                    y_star = beta_below * (-1)
                    ax.text(
                        -1.02,
                        y_star,
                        star_below,
                        color=color,
                        fontsize=STAR_FONTSIZE,
                        ha="right",
                        va="bottom",
                    )

    # ===== reference lines & axes =====
    ax.axvline(0, color="gray", linestyle="--", linewidth=1, alpha=0.8)
    ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.8)

    # symmetric x-limits around 0
    x_max_abs = max(abs(dk_min), abs(dk_max))
    ax.set_xlim(-x_max_abs - X_PAD, x_max_abs + X_PAD)

    # Original notebook comment normalized for the public code archive.
    x_ticks = np.arange(-k_max_less, k_max_more + 1, 1)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([f"{int(x)}" for x in x_ticks])

    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Original notebook comment normalized for the public code archive.
    # ax.set_xlabel(r"Change in flood count $\Delta k$ (negative = fewer, positive = more)",
    #               fontsize=LABEL_FONTSIZE)
    # ax.set_ylabel("Change in health index Δhealth_index_z",
    #               fontsize=LABEL_FONTSIZE)
    ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)

    # Original notebook comment normalized for the public code archive.
    # ax.set_title(f"{sample_label}", fontsize=TITLE_FONTSIZE)

    # optional generic legend (line + band)
    if SHOW_MAIN_LEGEND:
        line_dummy = Line2D(
            [], [], color="black", linewidth=1.5,
            label=r"Expected effect $E[\Delta Y(\Delta k)]$",
        )
        band_dummy = Patch(
            facecolor="black",
            alpha=BAND_ALPHA,
            label="95% confidence interval",
        )
        ax.legend(
            handles=[line_dummy, band_dummy],
            loc="upper left",
            frameon=False,
            fontsize=LEGEND_FONTSIZE,
        )

    plt.tight_layout()

    out_fp = PLOT_DIR / f"health_wedge_bands_sample_{sample}.png"
    fig.savefig(out_fp, dpi=300)
    print(f"[SAVE] figure saved: {out_fp}")

    plt.show()
    plt.close(fig)


def make_return_period_legend():
    """
    Create a standalone legend figure where colors represent return periods T.
    Saved to PLOT_DIR / 'legend_return_periods.png'.
    """
    handles = []
    for T in T_LIST:
        color = T_COLORS.get(T, "#000000")
        h = Line2D(
            [0], [0],
            color=color,
            linewidth=4,
            label=f"T = {T}",
        )
        handles.append(h)

    fig, ax = plt.subplots(figsize=(4.5, 1.5))
    ax.axis("off")

    ax.legend(
        handles=handles,
        loc="center",
        ncol=3,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    plt.tight_layout()

    out_fp = PLOT_DIR / "legend_return_periods.png"
    fig.savefig(out_fp, dpi=300)
    print(f"[SAVE] return-period legend saved: {out_fp}")

    plt.show()
    plt.close(fig)


# ========== main ==========

def main():
    df_Tagg = read_Tagg()

    for sample in SAMPLES:
        print(f"\n================ sample = {sample} ================")
        plot_piecewise_band_k_overlay(
            df_Tagg,
            sample=sample,
            k_max_more=K_MAX_MORE,
            k_max_less=K_MAX_LESS,
            z_value=Z_ALPHA_2,
        )

    make_return_period_legend()
    print("[DONE] all wedge-band plots and legend finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate two standalone legend figures with transparent background:

1) legend_line_band.png
   - Shows a solid line (expected effect) and a shaded band (95% CI).

2) legend_return_periods.png
   - Shows colors corresponding to different return periods T.

All saved to:
    E:/impact_assessment_child_order/data/figue2/plots_twinx
"""

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ========== global style (Times New Roman, 300 dpi) ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300

# ========== paths & config ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")
PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
T_COLORS = {
    2:   "#016450",
    5:   "#02818a",
    10:  "#3690c0",
    20:  "#67a9cf",
    50:  "#a6bddb",
    100: "#d0d1e6",
}

LEGEND_FONTSIZE = 14


def make_line_band_legend():
    """Archived notebook note for 03_figure2_flood_count_loss.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(figsize=(2.8, 1.2))

    # Original notebook comment normalized for the public code archive.
    fig.patch.set_alpha(0.0)
    ax.set_axis_off()

    # Original notebook comment normalized for the public code archive.
    line = Line2D(
        [0], [0],
        color="black",
        linewidth=1.8,
        label="Expected effect"
    )

    # Original notebook comment normalized for the public code archive.
    band = Patch(
        facecolor="black",
        alpha=0.30,
        label="95% CI"
    )

    ax.legend(
        handles=[line, band],
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    # Original notebook comment normalized for the public code archive.
    out_fp = PLOT_DIR / "legend_line_band_2.png"
    fig.savefig(
        out_fp,
        dpi=300,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )
    print(f"[SAVE] line+band legend saved: {out_fp}")

    plt.close(fig)


def make_return_period_legend():
    """Archived notebook note for 03_figure2_flood_count_loss.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(4.5, 1.5))

    # Original notebook comment normalized for the public code archive.
    fig.patch.set_alpha(0.0)
    ax.set_axis_off()

    handles = []
    for T in T_LIST:
        color = T_COLORS.get(T, "#000000")
        h = Line2D(
            [0], [0],
            color=color,
            linewidth=4,
            label=f"T = {T}",
        )
        handles.append(h)

    ax.legend(
        handles=handles,
        loc="center",
        ncol=3,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    out_fp = PLOT_DIR / "legend_return_periods_2.png"
    fig.savefig(
        out_fp,
        dpi=300,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )
    print(f"[SAVE] return-period legend saved: {out_fp}")

    plt.close(fig)


def main():
    make_line_band_legend()
    make_return_period_legend()
    print("[DONE] both legend figures generated.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Children's education side · Scheme B:
Wedge-shaped uncertainty bands for more/fewer flood events (all return
periods overlaid in one figure).

Based on storage_BM_piecewise_edu_Tagg.csv:

  For each return period T and sample "sample":

      ΔY_more(Δk) = Δk * beta_above        (in high-frequency region: more floods)
      ΔY_less(Δk) = Δk * beta_below        (in low-frequency region: fewer floods, Δk < 0)

  Under linearity:

      se[ΔY_more(Δk)] = |Δk| * se_above
      se[ΔY_less(Δk)] = |Δk| * se_below

  Figure (one panel per sample, all T overlaid):

      * x-axis: Δk (change in flood count relative to mean; negative=fewer, positive=more)
      * y-axis: change in years of schooling Δedu_years
      * solid colored line: expected effect E[ΔY(Δk)]
      * shaded wedge: 95% confidence interval (uncertainty increases with |Δk|)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ========== global style: Times New Roman, 300 dpi ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300

# ========== paths & configuration ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")

RES_TAGG = BASE_DIR / "storage_BM_piecewise_edu_Tagg.csv"

OUT_DIR = BASE_DIR / "plots_twinx"
OUT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR = "edu_years"
T_LIST = [2, 5, 10, 20, 50, 100]
SAMPLES = ["all", "rural", "urban"]

# range of Δk: how many more/fewer floods
K_MAX_MORE = 2
K_MAX_LESS = 2

# z-value for 95% CI
Z_ALPHA_2 = 1.96

# colors for each return period T (line + band)
T_COLORS = {
    2:   "#6e016b",
    5:   "#88419d",
    10:  "#8c6bb1",
    20:  "#8c96c6",
    50:  "#9ebcda",
    100: "#bfd3e6",
}


BAND_ALPHA = 0.20

# figure size
FIG_SIZE = (7, 4.5)

# symmetric padding for x-axis around 0
X_PAD = 0.3

# ===== font sizes (edit here) =====
TITLE_FONTSIZE  = 14   # figure title
LABEL_FONTSIZE  = 12   # x / y axis labels
TICK_FONTSIZE   = 15   # tick labels
LEGEND_FONTSIZE = 10   # legend in separate figure
STAR_FONTSIZE   = 0    # significance stars; 0 = effectively hide

# ================================= helpers =================================

def read_Tagg():
    print(f"[READ] piecewise FE results: {RES_TAGG}")
    df = pd.read_csv(RES_TAGG)

    need = [
        "Y_var", "sample", "T", "N_bar_mean",
        "beta_below", "se_below", "p_below",
        "beta_above", "se_above", "p_above",
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"Tagg file missing columns: {miss}")

    df = df[df["Y_var"] == Y_VAR].copy()
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["N_bar_mean"] = pd.to_numeric(df["N_bar_mean"], errors="coerce")

    for c in [
        "beta_below", "se_below", "p_below",
        "beta_above", "se_above", "p_above",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df[df["T"].isin(T_LIST)].copy()
    df = df.sort_values(["sample", "T"])
    print("[INFO] Tagg head:")
    print(df.head())
    return df


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def plot_piecewise_band_k_overlay(
    df_Tagg: pd.DataFrame,
    sample: str = "all",
    k_max_more: int = K_MAX_MORE,
    k_max_less: int = K_MAX_LESS,
    z_value: float = Z_ALPHA_2,
):
    """
    For a given sample ("all" / "rural" / "urban"), overlay wedges for all
    return periods T on a single figure:

        Δk  ->  change in years of schooling Δedu_years
    """

    sub = df_Tagg[df_Tagg["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows; skip.")
        return

    T_used = [T for T in T_LIST if T in sub["T"].unique()]
    sub = sub[sub["T"].isin(T_used)].copy()
    sub = sub.sort_values("T")

    if len(T_used) == 0:
        print(f"[WARN] sample={sample} has no requested return periods.")
        return

    # ==== global y-range for all wedges ====
    y_all = []

    for _, row in sub.iterrows():
        beta_above = row["beta_above"]
        se_above = row["se_above"]
        beta_below = row["beta_below"]
        se_below = row["se_below"]

        dk_less = np.arange(-k_max_less, 1)          # <= 0
        dk_more = np.arange(0, k_max_more + 1)       # >= 0

        mu_less = dk_less * beta_below
        se_less = np.abs(dk_less) * se_below
        ci_less_low = mu_less - z_value * se_less
        ci_less_high = mu_less + z_value * se_less

        mu_more = dk_more * beta_above
        se_more = np.abs(dk_more) * se_above
        ci_more_low = mu_more - z_value * se_more
        ci_more_high = mu_more + z_value * se_more

        y_all.extend(ci_less_low)
        y_all.extend(ci_less_high)
        y_all.extend(ci_more_low)
        y_all.extend(ci_more_high)

    y_all = np.array([y for y in y_all if np.isfinite(y)])
    if y_all.size == 0:
        print(f"[WARN] sample={sample} has all-NaN y.")
        return

    y_min = y_all.min()
    y_max = y_all.max()
    y_pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)

    dk_min = -k_max_less
    dk_max = k_max_more

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    sample_label = sample.upper()  # "ALL", "RURAL", "URBAN"

    # ==== draw wedges for each T ====
    for T in T_used:
        row_T = sub[sub["T"] == T].iloc[0]

        beta_above = row_T.beta_above
        se_above = row_T.se_above
        beta_below = row_T.beta_below
        se_below = row_T.se_below

        color = T_COLORS.get(int(T), "#000000")

        dk_less = np.arange(-k_max_less, 0 + 1)     # <= 0
        dk_more = np.arange(0, k_max_more + 1)      # >= 0

        # fewer floods: ΔY = β_below * Δk
        mu_less = dk_less * beta_below
        se_less = np.abs(dk_less) * se_below
        ci_less_low = mu_less - z_value * se_less
        ci_less_high = mu_less + z_value * se_less

        # more floods: ΔY = β_above * Δk
        mu_more = dk_more * beta_above
        se_more = np.abs(dk_more) * se_above
        ci_more_low = mu_more - z_value * se_more
        ci_more_high = mu_more + z_value * se_more

        # fewer-flood wedge + center line
        ax.fill_between(
            dk_less, ci_less_low, ci_less_high,
            alpha=BAND_ALPHA,
            color=color,
            linewidth=0,
        )
        ax.plot(
            dk_less, mu_less,
            color=color,
            linestyle="-",
            linewidth=1.5,
        )

        # more-flood wedge + center line
        ax.fill_between(
            dk_more, ci_more_low, ci_more_high,
            alpha=BAND_ALPHA,
            color=color,
            linewidth=0,
        )
        ax.plot(
            dk_more, mu_more,
            color=color,
            linestyle="-",
            linewidth=1.5,
        )

        # significance stars at Δk = ±1 (only if STAR_FONTSIZE > 0)
        if STAR_FONTSIZE > 0:
            if 1 <= k_max_more:
                star_above = stars_for_p(row_T.p_above)
                if star_above and np.isfinite(beta_above):
                    y_star = beta_above * 1
                    ax.text(
                        1.02,
                        y_star,
                        star_above,
                        color=color,
                        fontsize=STAR_FONTSIZE,
                        ha="left",
                        va="bottom",
                    )

            if 1 <= k_max_less:
                star_below = stars_for_p(row_T.p_below)
                if star_below and np.isfinite(beta_below):
                    y_star = beta_below * (-1)
                    ax.text(
                        -1.02,
                        y_star,
                        star_below,
                        color=color,
                        fontsize=STAR_FONTSIZE,
                        ha="right",
                        va="bottom",
                    )

    # reference lines & axes
    ax.axvline(0, color="gray", linestyle="--", linewidth=1, alpha=0.8)
    ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.8)

    # symmetric x-limits around 0
    x_max_abs = max(abs(dk_min), abs(dk_max))
    ax.set_xlim(-x_max_abs - X_PAD, x_max_abs + X_PAD)

    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # labels & ticks
    #ax.set_xlabel(r"Change in flood count $\Delta k$ (negative = fewer, positive = more)",fontsize=LABEL_FONTSIZE,)
    #ax.set_ylabel(r"Change in years of schooling $\Delta \mathrm{edu\_years}$",fontsize=LABEL_FONTSIZE,)
    ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)

    #ax.set_title(f"{sample_label}",fontsize=TITLE_FONTSIZE,)

    plt.tight_layout()
    fig_path = OUT_DIR / f"edu_storage_BM_wedge_sample_{sample}.png"
    fig.savefig(fig_path, dpi=300)
    plt.show()
    print(f"[DONE] sample={sample} figure saved: {fig_path}")


def make_return_period_legend():
    """
    Stand-alone legend figure where colors represent return period T.
    Saved as 'legend_return_periods_edu.png' in OUT_DIR.
    """
    handles = []
    for T in T_LIST:
        color = T_COLORS.get(T, "#000000")
        h = Line2D(
            [0], [0],
            color=color,
            linewidth=4,
            label=f"T = {T}",
        )
        handles.append(h)

    fig, ax = plt.subplots(figsize=(4.5, 1.5))
    ax.axis("off")

    ax.legend(
        handles=handles,
        loc="center",
        ncol=3,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    plt.tight_layout()
    out_fp = OUT_DIR / "legend_return_periods_edu.png"
    fig.savefig(out_fp, dpi=300)
    print(f"[SAVE] return-period legend (education) saved: {out_fp}")

    plt.show()
    plt.close(fig)


# =============== main ===============

def main():
    df_Tagg = read_Tagg()
    for s in SAMPLES:
        plot_piecewise_band_k_overlay(
            df_Tagg,
            sample=s,
            k_max_more=K_MAX_MORE,
            k_max_less=K_MAX_LESS,
        )

    make_return_period_legend()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate two standalone legend figures with transparent background:

1) legend_line_band.png
   - Shows a solid line (expected effect) and a shaded band (95% CI).

2) legend_return_periods.png
   - Shows colors corresponding to different return periods T.

All saved to:
    E:/impact_assessment_child_order/data/figue2/plots_twinx
"""

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ========== global style (Times New Roman, 300 dpi) ==========

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300

# ========== paths & config ==========

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2")
PLOT_DIR = BASE_DIR / "plots_twinx"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
T_COLORS = {
    2:   "#6e016b",
    5:   "#88419d",
    10:  "#8c6bb1",
    20:  "#8c96c6",
    50:  "#9ebcda",
    100: "#bfd3e6",
}


LEGEND_FONTSIZE = 16


def make_line_band_legend():
    """Archived notebook note for 03_figure2_flood_count_loss.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(figsize=(2.8, 1.2))

    # Original notebook comment normalized for the public code archive.
    fig.patch.set_alpha(0.0)
    ax.set_axis_off()

    # Original notebook comment normalized for the public code archive.
    line = Line2D(
        [0], [0],
        color="black",
        linewidth=1.8,
        label="Expected effect"
    )

    # Original notebook comment normalized for the public code archive.
    band = Patch(
        facecolor="black",
        alpha=0.30,
        label="95% CI"
    )

    ax.legend(
        handles=[line, band],
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    # Original notebook comment normalized for the public code archive.
    out_fp = PLOT_DIR / "legend_line_band.png"
    fig.savefig(
        out_fp,
        dpi=600,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )
    print(f"[SAVE] line+band legend saved: {out_fp}")

    plt.close(fig)


def make_return_period_legend():
    """Archived notebook note for 03_figure2_flood_count_loss.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(4.5, 1.5))

    # Original notebook comment normalized for the public code archive.
    fig.patch.set_alpha(0.0)
    ax.set_axis_off()

    handles = []
    for T in T_LIST:
        color = T_COLORS.get(T, "#000000")
        h = Line2D(
            [0], [0],
            color=color,
            linewidth=4,
            label=f"T = {T}",
        )
        handles.append(h)

    ax.legend(
        handles=handles,
        loc="center",
        ncol=3,
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
    )

    out_fp = PLOT_DIR / "legend_return_periods.png"
    fig.savefig(
        out_fp,
        dpi=600,
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.05,
    )
    print(f"[SAVE] return-period legend saved: {out_fp}")

    plt.close(fig)


def main():
    make_line_band_legend()
    make_return_period_legend()
    print("[DONE] both legend figures generated.")


if __name__ == "__main__":
    main()
