#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba


# =========================================================
# 0. PATHS & CONFIG
# =========================================================

PARENT_DIR = Path(r"E:\impact_assessment_child_order\data\figue2\high_low_risk")

# Original notebook comment normalized for the public code archive.
INPUT_DIR_CANDIDATES = [
    PARENT_DIR / "betaT_edu_years_highlow",
    PARENT_DIR / "betaT_edu_years_highlow_",
    PARENT_DIR,
]

POINTS_NAME = "betaT_edu_years_highlow_points.csv"
GRID_NAME   = "betaT_edu_years_highlow_grid.csv"

OUT_FIG_COMBINED_NAME = "betaT_edu_years_highlow_all_rural_urban.png"
OUT_FIG_ALL_NAME      = "betaT_edu_years_highlow_all.png"
OUT_FIG_RURAL_NAME    = "betaT_edu_years_highlow_rural.png"
OUT_FIG_URBAN_NAME    = "betaT_edu_years_highlow_urban.png"

OUT_LEGEND_PNG_NAME = "legend_betaT_edu_highlow.png"
OUT_LEGEND_SVG_NAME = "legend_betaT_edu_highlow.svg"

SAMPLE_TYPES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]


# ---------------------------------------------------------
# 0A. GLOBAL STYLE
# ---------------------------------------------------------
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.linewidth"] = 1.1

TICK_FONTSIZE = 18
LABEL_FONTSIZE = 16
PANEL_FONTSIZE = 13
STAR_FONTSIZE = 0

COMBINED_FIGSIZE = (13.6, 4.4)
SINGLE_FIGSIZE = (6.5, 4.5)

LINEWIDTH = 2.1
MARKERSIZE = 7.0
MARKEREDGEWIDTH = 0.9
SPINE_LINEWIDTH = 0.8


# ---------------------------------------------------------
# 0B. ZERO LINE STYLE
# ---------------------------------------------------------
ZERO_LINE_COLOR = "#7f7f7f"
ZERO_LINE_ALPHA = 0.90
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.2


# ---------------------------------------------------------
# 0C. FULLY CONFIGURABLE STYLE MAP
# ---------------------------------------------------------
STYLE_MAP = {
    "low": {
        # legend
        "legend_label": "Low-risk counties",

        # main fitted line
        "line_color": "#bf812d",
        "line_alpha": 0.50,
        "line_width": 2.0,
        "line_style": "--",   # "-", "--", "-.", ":", or tuple dash pattern

        # uncertainty band fill
        "band_face_color": "#bf812d",
        "band_face_alpha": 0.20,

        # uncertainty band edge
        "band_edge_color": "#bf812d",
        "band_edge_alpha": 0.20,
        "band_edge_width": 0.8,

        # observed points
        "point_face_color": "#bf812d",
        "point_face_alpha": 1.00,
        "point_edge_color": "#bf812d",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        # error bars (vertical segment)
        "errorbar_color": "#bf812d",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "--",   # Original notebook comment normalized for the public code archive.

        # caps (top/bottom small horizontal lines)
        "cap_color": "#bf812d",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",         # Original notebook comment normalized for the public code archive.
        "cap_half_width_factor": 0.018,

        # stars
        "star_color": "#bf812d",
        "star_alpha": 1.00,
    },

    "high": {
        "legend_label": "High-risk counties",

        "line_color": "#bf812d",
        "line_alpha": 1.00,
        "line_width": 2.3,
        "line_style": "-",

        "band_face_color": "#bf812d",
        "band_face_alpha": 0.40,

        "band_edge_color": "#bf812d",
        "band_edge_alpha": 0.40,
        "band_edge_width": 0.8,

        "point_face_color": "#bf812d",
        "point_face_alpha": 1.00,
        "point_edge_color": "#bf812d",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        "errorbar_color": "#bf812d",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "-",

        "cap_color": "#bf812d",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "star_color": "#bf812d",
        "star_alpha": 1.00,
    },
}


# ---------------------------------------------------------
# 0D. AXIS / FRAME STYLE
# ---------------------------------------------------------
SPINE_COLOR = "#000000"
SPINE_ALPHA = 1.00

TICK_COLOR = "#000000"
TICK_ALPHA = 1.00

LABEL_COLOR = "#000000"
LABEL_ALPHA = 1.00

PANEL_TEXT_COLOR = "#000000"
PANEL_TEXT_ALPHA = 1.00


# =========================================================
# 1. HELPERS
# =========================================================

def rgba(color, alpha):
    return to_rgba(color, alpha)


def locate_input_dir() -> Path:
    for d in INPUT_DIR_CANDIDATES:
        if (d / POINTS_NAME).exists() and (d / GRID_NAME).exists():
            return d
    raise FileNotFoundError(
        "未找到儿童教育 betaT 输入目录。请检查以下候选路径是否存在 points/grid 文件：\n"
        + "\n".join(str(x) for x in INPUT_DIR_CANDIDATES)
    )


def load_data(base_dir: Path):
    points_csv = base_dir / POINTS_NAME
    grid_csv = base_dir / GRID_NAME

    df_points = pd.read_csv(points_csv, encoding="utf-8-sig")
    df_grid = pd.read_csv(grid_csv, encoding="utf-8-sig")

    req_points = ["T", "sample_type", "risk_group", "Estimate", "CI_low", "CI_high"]
    req_grid = ["T_grid", "sample_type", "risk_group", "beta_grid", "ci_low", "ci_high"]

    miss_points = [c for c in req_points if c not in df_points.columns]
    miss_grid = [c for c in req_grid if c not in df_grid.columns]

    if miss_points:
        raise KeyError(f"points 文件缺少列：{miss_points}")
    if miss_grid:
        raise KeyError(f"grid 文件缺少列：{miss_grid}")

    for c in ["T", "Estimate", "CI_low", "CI_high"]:
        df_points[c] = pd.to_numeric(df_points[c], errors="coerce")
    for c in ["T_grid", "beta_grid", "ci_low", "ci_high"]:
        df_grid[c] = pd.to_numeric(df_grid[c], errors="coerce")

    if "PValue" in df_points.columns:
        df_points["PValue"] = pd.to_numeric(df_points["PValue"], errors="coerce")
    if "star" not in df_points.columns:
        df_points["star"] = ""
    else:
        df_points["star"] = df_points["star"].fillna("").astype(str)

    df_points["sample_type"] = df_points["sample_type"].astype(str).str.strip().str.lower()
    df_points["risk_group"] = df_points["risk_group"].astype(str).str.strip().str.lower()
    df_grid["sample_type"] = df_grid["sample_type"].astype(str).str.strip().str.lower()
    df_grid["risk_group"] = df_grid["risk_group"].astype(str).str.strip().str.lower()

    df_points = df_points[
        df_points["sample_type"].isin(SAMPLE_TYPES) &
        df_points["risk_group"].isin(RISK_GROUPS)
    ].copy()

    df_grid = df_grid[
        df_grid["sample_type"].isin(SAMPLE_TYPES) &
        df_grid["risk_group"].isin(RISK_GROUPS)
    ].copy()

    return df_points, df_grid


def compute_global_ylim(df_points: pd.DataFrame, df_grid: pd.DataFrame):
    vals = []
    vals.extend(df_points["CI_low"].dropna().tolist())
    vals.extend(df_points["CI_high"].dropna().tolist())
    vals.extend(df_grid["ci_low"].dropna().tolist())
    vals.extend(df_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]

    if vals.size == 0:
        return (-1.0, 1.0)

    ymin = float(vals.min())
    ymax = float(vals.max())
    yr = ymax - ymin
    pad = 0.08 * yr if yr > 0 else 0.2
    return (ymin - pad, ymax + pad)


def compute_local_offset(sub_points: pd.DataFrame, sub_grid: pd.DataFrame):
    vals = []
    vals.extend(sub_points["CI_low"].dropna().tolist())
    vals.extend(sub_points["CI_high"].dropna().tolist())
    vals.extend(sub_grid["ci_low"].dropna().tolist())
    vals.extend(sub_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = float(vals.max() - vals.min()) if vals.size > 0 else 1.0
    return 0.035 * yr if yr > 0 else 0.03


def style_axis(ax, ylabel=None, ylims=None):
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)

    # Original notebook comment normalized for the public code archive.

    ax.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter([str(t) for t in T_LIST]))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.yaxis.set_minor_locator(mticker.NullLocator())

# Original notebook comment normalized for the public code archive.
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=TICK_FONTSIZE,
        length=4.5,
        width=1.0,
        color=rgba(TICK_COLOR, TICK_ALPHA),
        labelcolor=rgba(TICK_COLOR, TICK_ALPHA),
    )

    if ylabel is not None:
        ax.set_ylabel(
            ylabel,
            fontsize=LABEL_FONTSIZE,
            color=rgba(LABEL_COLOR, LABEL_ALPHA)
        )

    if ylims is not None:
        ax.set_ylim(*ylims)

    # Original notebook comment normalized for the public code archive.
    for side in ["left", "bottom", "top", "right"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(SPINE_LINEWIDTH)
        ax.spines[side].set_color(rgba(SPINE_COLOR, SPINE_ALPHA))

    # Original notebook comment normalized for the public code archive.
    ax.grid(False)

    # Original notebook comment normalized for the public code archive.
    ax.axhline(
        y=0,
        color=rgba(ZERO_LINE_COLOR, ZERO_LINE_ALPHA),
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        zorder=0
    )

    ax.set_xlabel("")


def add_panel_text(ax, txt):
    ax.text(
        0.03, 0.96, txt,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=PANEL_FONTSIZE,
        color=rgba(PANEL_TEXT_COLOR, PANEL_TEXT_ALPHA)
    )


# =========================================================
# 2. PLOTTING
# =========================================================

def plot_one_panel(ax, df_points: pd.DataFrame, df_grid: pd.DataFrame,
                   sample_type: str, ylims=None, ylabel=None, panel_text=None):
    sub_points = df_points[df_points["sample_type"] == sample_type].copy()
    sub_grid = df_grid[df_grid["sample_type"] == sample_type].copy()

    if sub_points.empty or sub_grid.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        style_axis(ax, ylabel=ylabel, ylims=ylims)
        return

    offset = compute_local_offset(sub_points, sub_grid)

    for rg in RISK_GROUPS:
        cfg = STYLE_MAP[rg]

        # Original notebook comment normalized for the public code archive.
        g = sub_grid[sub_grid["risk_group"] == rg].copy().sort_values("T_grid")
        if not g.empty:
            ax.plot(
                g["T_grid"].to_numpy(float),
                g["beta_grid"].to_numpy(float),
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linewidth=cfg["line_width"],
                linestyle=cfg["line_style"],
                zorder=2
            )
            ax.fill_between(
                g["T_grid"].to_numpy(float),
                g["ci_low"].to_numpy(float),
                g["ci_high"].to_numpy(float),
                facecolor=rgba(cfg["band_face_color"], cfg["band_face_alpha"]),
                edgecolor=rgba(cfg["band_edge_color"], cfg["band_edge_alpha"]),
                linewidth=cfg["band_edge_width"],
                zorder=1
            )

        # Original notebook comment normalized for the public code archive.
        p = sub_points[sub_points["risk_group"] == rg].copy().sort_values("T")
        if not p.empty:
            xmult = 0.96 if rg == "low" else 1.04
            T_vals = p["T"].to_numpy(float) * xmult
            est = p["Estimate"].to_numpy(float)
            lo = p["CI_low"].to_numpy(float)
            hi = p["CI_high"].to_numpy(float)

            # Original notebook comment normalized for the public code archive.
            ax.vlines(
                T_vals,
                lo,
                hi,
                colors=rgba(cfg["errorbar_color"], cfg["errorbar_alpha"]),
                linewidth=cfg["errorbar_linewidth"],
                linestyles=cfg["errorbar_linestyle"],
                zorder=3
            )

            # Original notebook comment normalized for the public code archive.
            for x, ylo, yhi in zip(T_vals, lo, hi):
                cap_half = x * cfg["cap_half_width_factor"]

                ax.hlines(
                    ylo,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )
                ax.hlines(
                    yhi,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )

            # Original notebook comment normalized for the public code archive.
            ax.scatter(
                T_vals,
                est,
                s=cfg["marker_size"] ** 2,
                facecolors=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                edgecolors=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                linewidths=cfg["point_edge_width"],
                zorder=4
            )

            # Original notebook comment normalized for the public code archive.
            for T0, b, st in zip(T_vals, est, p["star"].tolist()):
                if not st:
                    continue

                if b >= 0:
                    yy = b + offset
                    va = "bottom"
                else:
                    yy = b - offset
                    va = "top"

                ax.text(
                    T0, yy, st,
                    ha="center", va=va,
                    fontsize=STAR_FONTSIZE,
                    color=rgba(cfg["star_color"], cfg["star_alpha"]),
                    zorder=5
                )

    style_axis(ax, ylabel=ylabel, ylims=ylims)

    if panel_text is not None:
        add_panel_text(ax, panel_text)


def save_standalone_legend(out_dir: Path):
    handles = []
    for rg in RISK_GROUPS:
        cfg = STYLE_MAP[rg]
        handles.append(
            Line2D(
                [0], [0],
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linestyle=cfg["line_style"],
                marker="o",
                linewidth=cfg["line_width"],
                markersize=cfg["marker_size"],
                markerfacecolor=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                markeredgecolor=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                markeredgewidth=cfg["point_edge_width"],
                label=cfg["legend_label"]
            )
        )

    fig = plt.figure(figsize=(4.8, 0.95))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=12,
        handlelength=2.2,
        columnspacing=1.6,
        handletextpad=0.6
    )

    plt.tight_layout()
    plt.savefig(out_dir / OUT_LEGEND_PNG_NAME, dpi=300, bbox_inches="tight", transparent=True)
    plt.savefig(out_dir / OUT_LEGEND_SVG_NAME, bbox_inches="tight", transparent=True)
    plt.close(fig)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


def plot_combined(df_points: pd.DataFrame, df_grid: pd.DataFrame, out_dir: Path):
    fig, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE, sharey=True)
    ylims = compute_global_ylim(df_points, df_grid)

    panel_map = {
        "all": "All",
        "rural": "Rural",
        "urban": "Urban",
    }

    for i, (ax, s) in enumerate(zip(axes, SAMPLE_TYPES)):
        ylabel = "Education loss" if i == 0 else None
        plot_one_panel(
            ax=ax,
            df_points=df_points,
            df_grid=df_grid,
            sample_type=s,
            ylims=ylims,
            ylabel=ylabel,
            panel_text=panel_map[s]
        )

    plt.subplots_adjust(left=0.08, right=0.985, bottom=0.15, top=0.96, wspace=0.10)
    out_path = out_dir / OUT_FIG_COMBINED_NAME
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_points: pd.DataFrame, df_grid: pd.DataFrame, sample_type: str, out_dir: Path):
    fig, ax = plt.subplots(figsize=SINGLE_FIGSIZE)

    sub_points = df_points[df_points["sample_type"] == sample_type].copy()
    sub_grid = df_grid[df_grid["sample_type"] == sample_type].copy()
    ylims = compute_global_ylim(sub_points, sub_grid)

    plot_one_panel(
        ax=ax,
        df_points=df_points,
        df_grid=df_grid,
        sample_type=sample_type,
        ylims=ylims,
        ylabel="",
        panel_text=None
    )

    name_map = {
        "all": OUT_FIG_ALL_NAME,
        "rural": OUT_FIG_RURAL_NAME,
        "urban": OUT_FIG_URBAN_NAME,
    }

    plt.subplots_adjust(left=0.18, right=0.98, bottom=0.16, top=0.97)
    out_path = out_dir / name_map[sample_type]
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 3. MAIN
# =========================================================

def main():
    input_dir = locate_input_dir()
    print("[INFO] Notebook progress message.")

    df_points, df_grid = load_data(input_dir)

    print("[INFO] Notebook progress message.")
    plot_combined(df_points, df_grid, input_dir)

    print("[INFO] Notebook progress message.")
    for s in SAMPLE_TYPES:
        plot_single(df_points, df_grid, s, input_dir)

    print("[INFO] Notebook progress message.")
    save_standalone_legend(input_dir)

    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba


# =========================================================
# 0. PATHS & CONFIG
# =========================================================

PARENT_DIR = Path(r"E:\impact_assessment_child_order\data\figue2\high_low_risk")

# Original notebook comment normalized for the public code archive.
INPUT_DIR_CANDIDATES = [
    PARENT_DIR / "betaT_edu_years_highlow",
    PARENT_DIR / "betaT_edu_years_highlow_",
    PARENT_DIR,
]

POINTS_NAME = "betaT_edu_years_highlow_points.csv"
GRID_NAME   = "betaT_edu_years_highlow_grid.csv"

# Original notebook comment normalized for the public code archive.
OUT_FIG_COMBINED_NAME = "betaT_edu_years_highlow_all_rural_urban_yfix_m3to3.png"
OUT_FIG_ALL_NAME      = "betaT_edu_years_highlow_all_yfix_m3to3.png"
OUT_FIG_RURAL_NAME    = "betaT_edu_years_highlow_rural_yfix_m3to3.png"
OUT_FIG_URBAN_NAME    = "betaT_edu_years_highlow_urban_yfix_m3to3.png"

OUT_LEGEND_PNG_NAME = "legend_betaT_edu_highlow_yfix_m3to3.png"
OUT_LEGEND_SVG_NAME = "legend_betaT_edu_highlow_yfix_m3to3.svg"

SAMPLE_TYPES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]

# =============================================================================
FIXED_YLIMS = (-3.0, 3.0)
FIXED_YTICKS = [-3, -2, -1, 0, 1, 2, 3]


# ---------------------------------------------------------
# 0A. GLOBAL STYLE
# ---------------------------------------------------------
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.linewidth"] = 1.1

TICK_FONTSIZE = 18
LABEL_FONTSIZE = 16
PANEL_FONTSIZE = 13
STAR_FONTSIZE = 0

COMBINED_FIGSIZE = (13.6, 4.4)
SINGLE_FIGSIZE = (6.5, 5.2)

LINEWIDTH = 2.1
MARKERSIZE = 7.0
MARKEREDGEWIDTH = 0.9
SPINE_LINEWIDTH = 0.8


# ---------------------------------------------------------
# 0B. ZERO LINE STYLE
# ---------------------------------------------------------
ZERO_LINE_COLOR = "#7f7f7f"
ZERO_LINE_ALPHA = 0.90
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.2


# ---------------------------------------------------------
# 0C. FULLY CONFIGURABLE STYLE MAP
# ---------------------------------------------------------
STYLE_MAP = {
    "low": {
        "legend_label": "Low-risk counties",

        "line_color": "#bf812d",
        "line_alpha": 0.50,
        "line_width": 2.0,
        "line_style": "--",

        "band_face_color": "#bf812d",
        "band_face_alpha": 0.20,

        "band_edge_color": "#bf812d",
        "band_edge_alpha": 0.20,
        "band_edge_width": 0.8,

        "point_face_color": "#bf812d",
        "point_face_alpha": 1.00,
        "point_edge_color": "#bf812d",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        "errorbar_color": "#bf812d",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "--",

        "cap_color": "#bf812d",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "star_color": "#bf812d",
        "star_alpha": 1.00,
    },

    "high": {
        "legend_label": "High-risk counties",

        "line_color": "#bf812d",
        "line_alpha": 1.00,
        "line_width": 2.3,
        "line_style": "-",

        "band_face_color": "#bf812d",
        "band_face_alpha": 0.40,

        "band_edge_color": "#bf812d",
        "band_edge_alpha": 0.40,
        "band_edge_width": 0.8,

        "point_face_color": "#bf812d",
        "point_face_alpha": 1.00,
        "point_edge_color": "#bf812d",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        "errorbar_color": "#bf812d",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "-",

        "cap_color": "#bf812d",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "star_color": "#bf812d",
        "star_alpha": 1.00,
    },
}


# ---------------------------------------------------------
# 0D. AXIS / FRAME STYLE
# ---------------------------------------------------------
SPINE_COLOR = "#000000"
SPINE_ALPHA = 1.00

TICK_COLOR = "#000000"
TICK_ALPHA = 1.00

LABEL_COLOR = "#000000"
LABEL_ALPHA = 1.00

PANEL_TEXT_COLOR = "#000000"
PANEL_TEXT_ALPHA = 1.00


# =========================================================
# 1. HELPERS
# =========================================================

def rgba(color, alpha):
    return to_rgba(color, alpha)


def locate_input_dir() -> Path:
    for d in INPUT_DIR_CANDIDATES:
        if (d / POINTS_NAME).exists() and (d / GRID_NAME).exists():
            return d
    raise FileNotFoundError(
        "未找到儿童教育 betaT 输入目录。请检查以下候选路径是否存在 points/grid 文件：\n"
        + "\n".join(str(x) for x in INPUT_DIR_CANDIDATES)
    )


def load_data(base_dir: Path):
    points_csv = base_dir / POINTS_NAME
    grid_csv = base_dir / GRID_NAME

    df_points = pd.read_csv(points_csv, encoding="utf-8-sig")
    df_grid = pd.read_csv(grid_csv, encoding="utf-8-sig")

    req_points = ["T", "sample_type", "risk_group", "Estimate", "CI_low", "CI_high"]
    req_grid = ["T_grid", "sample_type", "risk_group", "beta_grid", "ci_low", "ci_high"]

    miss_points = [c for c in req_points if c not in df_points.columns]
    miss_grid = [c for c in req_grid if c not in df_grid.columns]

    if miss_points:
        raise KeyError(f"points 文件缺少列：{miss_points}")
    if miss_grid:
        raise KeyError(f"grid 文件缺少列：{miss_grid}")

    for c in ["T", "Estimate", "CI_low", "CI_high"]:
        df_points[c] = pd.to_numeric(df_points[c], errors="coerce")
    for c in ["T_grid", "beta_grid", "ci_low", "ci_high"]:
        df_grid[c] = pd.to_numeric(df_grid[c], errors="coerce")

    if "PValue" in df_points.columns:
        df_points["PValue"] = pd.to_numeric(df_points["PValue"], errors="coerce")
    if "star" not in df_points.columns:
        df_points["star"] = ""
    else:
        df_points["star"] = df_points["star"].fillna("").astype(str)

    df_points["sample_type"] = df_points["sample_type"].astype(str).str.strip().str.lower()
    df_points["risk_group"] = df_points["risk_group"].astype(str).str.strip().str.lower()
    df_grid["sample_type"] = df_grid["sample_type"].astype(str).str.strip().str.lower()
    df_grid["risk_group"] = df_grid["risk_group"].astype(str).str.strip().str.lower()

    df_points = df_points[
        df_points["sample_type"].isin(SAMPLE_TYPES) &
        df_points["risk_group"].isin(RISK_GROUPS)
    ].copy()

    df_grid = df_grid[
        df_grid["sample_type"].isin(SAMPLE_TYPES) &
        df_grid["risk_group"].isin(RISK_GROUPS)
    ].copy()

    return df_points, df_grid


def compute_local_offset(sub_points: pd.DataFrame, sub_grid: pd.DataFrame):
    vals = []
    vals.extend(sub_points["CI_low"].dropna().tolist())
    vals.extend(sub_points["CI_high"].dropna().tolist())
    vals.extend(sub_grid["ci_low"].dropna().tolist())
    vals.extend(sub_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = float(vals.max() - vals.min()) if vals.size > 0 else 1.0
    return 0.035 * yr if yr > 0 else 0.03


def style_axis(ax, ylabel=None, ylims=FIXED_YLIMS):
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)

    ax.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter([str(t) for t in T_LIST]))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.yaxis.set_minor_locator(mticker.NullLocator())

    # =============================================================================
    ax.set_ylim(*ylims)
    ax.set_yticks(FIXED_YTICKS)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=TICK_FONTSIZE,
        length=4.5,
        width=1.0,
        color=rgba(TICK_COLOR, TICK_ALPHA),
        labelcolor=rgba(TICK_COLOR, TICK_ALPHA),
    )

    if ylabel is not None:
        ax.set_ylabel(
            ylabel,
            fontsize=LABEL_FONTSIZE,
            color=rgba(LABEL_COLOR, LABEL_ALPHA)
        )

    for side in ["left", "bottom", "top", "right"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(SPINE_LINEWIDTH)
        ax.spines[side].set_color(rgba(SPINE_COLOR, SPINE_ALPHA))

    ax.grid(False)

    ax.axhline(
        y=0,
        color=rgba(ZERO_LINE_COLOR, ZERO_LINE_ALPHA),
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        zorder=0
    )

    ax.set_xlabel("")


def add_panel_text(ax, txt):
    ax.text(
        0.03, 0.96, txt,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=PANEL_FONTSIZE,
        color=rgba(PANEL_TEXT_COLOR, PANEL_TEXT_ALPHA)
    )


# =========================================================
# 2. PLOTTING
# =========================================================

def plot_one_panel(ax, df_points: pd.DataFrame, df_grid: pd.DataFrame,
                   sample_type: str, ylims=FIXED_YLIMS, ylabel=None, panel_text=None):
    sub_points = df_points[df_points["sample_type"] == sample_type].copy()
    sub_grid = df_grid[df_grid["sample_type"] == sample_type].copy()

    if sub_points.empty or sub_grid.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        style_axis(ax, ylabel=ylabel, ylims=ylims)
        return

    offset = compute_local_offset(sub_points, sub_grid)

    for rg in RISK_GROUPS:
        cfg = STYLE_MAP[rg]

        # Original notebook comment normalized for the public code archive.
        g = sub_grid[sub_grid["risk_group"] == rg].copy().sort_values("T_grid")
        if not g.empty:
            ax.plot(
                g["T_grid"].to_numpy(float),
                g["beta_grid"].to_numpy(float),
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linewidth=cfg["line_width"],
                linestyle=cfg["line_style"],
                zorder=2
            )
            ax.fill_between(
                g["T_grid"].to_numpy(float),
                g["ci_low"].to_numpy(float),
                g["ci_high"].to_numpy(float),
                facecolor=rgba(cfg["band_face_color"], cfg["band_face_alpha"]),
                edgecolor=rgba(cfg["band_edge_color"], cfg["band_edge_alpha"]),
                linewidth=cfg["band_edge_width"],
                zorder=1
            )

        # Original notebook comment normalized for the public code archive.
        p = sub_points[sub_points["risk_group"] == rg].copy().sort_values("T")
        if not p.empty:
            xmult = 0.96 if rg == "low" else 1.04
            T_vals = p["T"].to_numpy(float) * xmult
            est = p["Estimate"].to_numpy(float)
            lo = p["CI_low"].to_numpy(float)
            hi = p["CI_high"].to_numpy(float)

            ax.vlines(
                T_vals,
                lo,
                hi,
                colors=rgba(cfg["errorbar_color"], cfg["errorbar_alpha"]),
                linewidth=cfg["errorbar_linewidth"],
                linestyles=cfg["errorbar_linestyle"],
                zorder=3
            )

            for x, ylo, yhi in zip(T_vals, lo, hi):
                cap_half = x * cfg["cap_half_width_factor"]

                ax.hlines(
                    ylo,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )
                ax.hlines(
                    yhi,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )

            ax.scatter(
                T_vals,
                est,
                s=cfg["marker_size"] ** 2,
                facecolors=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                edgecolors=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                linewidths=cfg["point_edge_width"],
                zorder=4
            )

            for T0, b, st in zip(T_vals, est, p["star"].tolist()):
                if not st:
                    continue

                if b >= 0:
                    yy = b + offset
                    va = "bottom"
                else:
                    yy = b - offset
                    va = "top"

                ax.text(
                    T0, yy, st,
                    ha="center", va=va,
                    fontsize=STAR_FONTSIZE,
                    color=rgba(cfg["star_color"], cfg["star_alpha"]),
                    zorder=5
                )

    style_axis(ax, ylabel=ylabel, ylims=ylims)

    if panel_text is not None:
        add_panel_text(ax, panel_text)


def save_standalone_legend(out_dir: Path):
    handles = []
    for rg in RISK_GROUPS:
        cfg = STYLE_MAP[rg]
        handles.append(
            Line2D(
                [0], [0],
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linestyle=cfg["line_style"],
                marker="o",
                linewidth=cfg["line_width"],
                markersize=cfg["marker_size"],
                markerfacecolor=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                markeredgecolor=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                markeredgewidth=cfg["point_edge_width"],
                label=cfg["legend_label"]
            )
        )

    fig = plt.figure(figsize=(4.8, 0.95))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=12,
        handlelength=2.2,
        columnspacing=1.6,
        handletextpad=0.6
    )

    plt.tight_layout()
    plt.savefig(out_dir / OUT_LEGEND_PNG_NAME, dpi=300, bbox_inches="tight", transparent=True)
    plt.savefig(out_dir / OUT_LEGEND_SVG_NAME, bbox_inches="tight", transparent=True)
    plt.close(fig)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


def plot_combined(df_points: pd.DataFrame, df_grid: pd.DataFrame, out_dir: Path):
    fig, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE, sharey=True)

    panel_map = {
        "all": "All",
        "rural": "Rural",
        "urban": "Urban",
    }

    for i, (ax, s) in enumerate(zip(axes, SAMPLE_TYPES)):
        ylabel = "Education loss" if i == 0 else None
        plot_one_panel(
            ax=ax,
            df_points=df_points,
            df_grid=df_grid,
            sample_type=s,
            ylims=FIXED_YLIMS,
            ylabel=ylabel,
            panel_text=panel_map[s]
        )

    plt.subplots_adjust(left=0.08, right=0.985, bottom=0.15, top=0.96, wspace=0.10)
    out_path = out_dir / OUT_FIG_COMBINED_NAME
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_points: pd.DataFrame, df_grid: pd.DataFrame, sample_type: str, out_dir: Path):
    fig, ax = plt.subplots(figsize=SINGLE_FIGSIZE)

    plot_one_panel(
        ax=ax,
        df_points=df_points,
        df_grid=df_grid,
        sample_type=sample_type,
        ylims=FIXED_YLIMS,
        ylabel="",
        panel_text=None
    )

    name_map = {
        "all": OUT_FIG_ALL_NAME,
        "rural": OUT_FIG_RURAL_NAME,
        "urban": OUT_FIG_URBAN_NAME,
    }

    plt.subplots_adjust(left=0.18, right=0.98, bottom=0.16, top=0.97)
    out_path = out_dir / name_map[sample_type]
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 3. MAIN
# =========================================================

def main():
    input_dir = locate_input_dir()
    print("[INFO] Notebook progress message.")

    df_points, df_grid = load_data(input_dir)

    print("[INFO] Notebook progress message.")
    plot_combined(df_points, df_grid, input_dir)

    print("[INFO] Notebook progress message.")
    for s in SAMPLE_TYPES:
        plot_single(df_points, df_grid, s, input_dir)

    print("[INFO] Notebook progress message.")
    save_standalone_legend(input_dir)

    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2\high_low_risk\老年健康")

AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T_highlowRisk.csv"
GRID_CSV = BASE_DIR / "betaT_health_index_z_highlowRisk_meta_grid.csv"

OUT_FIG_COMBINED = BASE_DIR / "betaT_health_index_z_highlowRisk_all_rural_urban.png"
OUT_FIG_ALL = BASE_DIR / "betaT_health_index_z_highlowRisk_all.png"
OUT_FIG_RURAL = BASE_DIR / "betaT_health_index_z_highlowRisk_rural.png"
OUT_FIG_URBAN = BASE_DIR / "betaT_health_index_z_highlowRisk_urban.png"

OUT_LEGEND_PNG = BASE_DIR / "legend_betaT_health_highlow.png"
OUT_LEGEND_SVG = BASE_DIR / "legend_betaT_health_highlow.svg"

Y_VAR = "health_index_z"
SAMPLES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]

# ---------------------------------------------------------
# 0A. GLOBAL STYLE
# ---------------------------------------------------------
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.linewidth"] = 1.1

TICK_FONTSIZE = 13
LABEL_FONTSIZE = 16
PANEL_FONTSIZE = 13
STAR_FONTSIZE = 0

COMBINED_FIGSIZE = (13.6, 4.4)
SINGLE_FIGSIZE = (6.5, 4.5)

LINEWIDTH = 2.1
MARKERSIZE = 6.8
MARKEREDGEWIDTH = 0.9
CAPSIZE = 4.0
ERRORBAR_LINEWIDTH = 1.4
SPINE_LINEWIDTH = 0.8

# ---------------------------------------------------------
# 0B. ZERO LINE STYLE
# ---------------------------------------------------------
ZERO_LINE_COLOR = "#7f7f7f"
ZERO_LINE_ALPHA = 0.90
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.0

# ---------------------------------------------------------
# 0C. DEFAULT GROUP STYLE
# Original notebook comment normalized for the public code archive.
# ---------------------------------------------------------
DEFAULT_GROUP_STYLE = {
    "legend_label": "Group",

    # main fitted line
    "line_color": "#01665e",
    "line_alpha": 1.00,
    "line_width": LINEWIDTH,
    "line_style": "-",

    # uncertainty band
    "band_face_color": "#01665e",
    "band_face_alpha": 0.20,
    "band_edge_color": "#01665e",
    "band_edge_alpha": 0.20,
    "band_edge_width": 0.8,

    # observed points
    "point_face_color": "#01665e",
    "point_face_alpha": 1.00,
    "point_edge_color": "#01665e",
    "point_edge_alpha": 1.00,
    "point_edge_width": MARKEREDGEWIDTH,
    "marker_size": MARKERSIZE,

    # Original notebook comment normalized for the public code archive.
    "errorbar_color": "#01665e",
    "errorbar_alpha": 1.00,
    "errorbar_linewidth": ERRORBAR_LINEWIDTH,
    "errorbar_linestyle": "-",

    # Original notebook comment normalized for the public code archive.
    "cap_color": "#01665e",
    "cap_alpha": 1.00,
    "cap_linewidth": ERRORBAR_LINEWIDTH,
    "cap_linestyle": "-",
    "cap_half_width_factor": 0.018,

    # Original notebook comment normalized for the public code archive.
    "capsize": CAPSIZE,

    # stars
    "star_color": "#01665e",
    "star_alpha": 1.00,
}

# ---------------------------------------------------------
# 0D. GROUP STYLE MAP
# Original notebook comment normalized for the public code archive.
# ---------------------------------------------------------
STYLE_MAP = {
    "low": {
        "legend_label": "Low-risk cities",

        "line_color": "#01665e",
        "line_alpha": 0.50,
        "line_width": 1.6,
        "line_style": "--",   # Original notebook comment normalized for the public code archive.

        "band_face_color": "#01665e",
        "band_face_alpha": 0.15,
        "band_edge_color": "#01665e",
        "band_edge_alpha": 0.15,
        "band_edge_width": 0.8,

        "point_face_color": "#01665e",
        "point_face_alpha": 1.00,
        "point_edge_color": "#01665e",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        # Original notebook comment normalized for the public code archive.
        "errorbar_color": "#01665e",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "--",

        # Original notebook comment normalized for the public code archive.
        "cap_color": "#01665e",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "capsize": CAPSIZE,  # Original notebook comment normalized for the public code archive.

        "star_color": "#01665e",
        "star_alpha": 1.00,
    },

    "high": {
        "legend_label": "High-risk cities",

        "line_color": "#01665e",
        "line_alpha": 1.00,
        "line_width": 2.3,
        "line_style": "-",    # Original notebook comment normalized for the public code archive.

        "band_face_color": "#01665e",
        "band_face_alpha": 0.32,
        "band_edge_color": "#01665e",
        "band_edge_alpha": 0.32,
        "band_edge_width": 0.8,

        "point_face_color": "#01665e",
        "point_face_alpha": 1.00,
        "point_edge_color": "#01665e",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        # Original notebook comment normalized for the public code archive.
        "errorbar_color": "#01665e",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "-",

        # Original notebook comment normalized for the public code archive.
        "cap_color": "#01665e",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "capsize": CAPSIZE,  # Original notebook comment normalized for the public code archive.

        "star_color": "#01665e",
        "star_alpha": 1.00,
    },
}

# ---------------------------------------------------------
# 0E. AXIS / FRAME STYLE
# ---------------------------------------------------------
SPINE_COLOR = "#000000"
SPINE_ALPHA = 1.00

TICK_COLOR = "#000000"
TICK_ALPHA = 1.00

LABEL_COLOR = "#000000"
LABEL_ALPHA = 1.00

PANEL_TEXT_COLOR = "#000000"
PANEL_TEXT_ALPHA = 1.00


# =========================================================
# 1. HELPERS
# =========================================================

def rgba(color, alpha):
    return to_rgba(color, alpha)


def get_group_style(group_name: str) -> dict:
    """Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cfg = DEFAULT_GROUP_STYLE.copy()
    cfg.update(STYLE_MAP.get(group_name, {}))
    return cfg


def stars_for_p(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =========================================================
# 2. DATA IO
# =========================================================

def load_data():
    if not AGG_CSV.exists():
        raise FileNotFoundError(f"未找到聚合结果文件：{AGG_CSV}")
    if not GRID_CSV.exists():
        raise FileNotFoundError(f"未找到曲线网格文件：{GRID_CSV}")

    df_agg = pd.read_csv(AGG_CSV, encoding="utf-8-sig")
    df_grid = pd.read_csv(GRID_CSV, encoding="utf-8-sig")

    req_agg = ["Y_var", "sample", "risk_group", "T", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]
    req_grid = ["Y_var", "sample", "risk_group", "T_grid", "beta_grid", "ci_low", "ci_high"]

    miss_agg = [c for c in req_agg if c not in df_agg.columns]
    miss_grid = [c for c in req_grid if c not in df_grid.columns]

    if miss_agg:
        raise KeyError(f"agg 文件缺少列：{miss_agg}")
    if miss_grid:
        raise KeyError(f"grid 文件缺少列：{miss_grid}")

    df_agg = df_agg[df_agg["Y_var"].astype(str) == Y_VAR].copy()
    df_grid = df_grid[df_grid["Y_var"].astype(str) == Y_VAR].copy()

    for c in ["T", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]:
        df_agg[c] = pd.to_numeric(df_agg[c], errors="coerce")
    for c in ["T_grid", "beta_grid", "ci_low", "ci_high"]:
        df_grid[c] = pd.to_numeric(df_grid[c], errors="coerce")

    df_agg["sample"] = df_agg["sample"].astype(str).str.strip().str.lower()
    df_agg["risk_group"] = df_agg["risk_group"].astype(str).str.strip().str.lower()
    df_grid["sample"] = df_grid["sample"].astype(str).str.strip().str.lower()
    df_grid["risk_group"] = df_grid["risk_group"].astype(str).str.strip().str.lower()

    df_agg = df_agg[
        df_agg["sample"].isin(SAMPLES) &
        df_agg["risk_group"].isin(RISK_GROUPS)
    ].copy()

    df_grid = df_grid[
        df_grid["sample"].isin(SAMPLES) &
        df_grid["risk_group"].isin(RISK_GROUPS)
    ].copy()

    return df_agg, df_grid


# =========================================================
# 3. STYLE HELPERS
# =========================================================

def compute_global_ylim(df_agg: pd.DataFrame, df_grid: pd.DataFrame):
    vals = []
    vals.extend(df_agg["2.5%"].dropna().tolist())
    vals.extend(df_agg["97.5%"].dropna().tolist())
    vals.extend(df_grid["ci_low"].dropna().tolist())
    vals.extend(df_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]

    if vals.size == 0:
        return (-0.5, 0.5)

    ymin = float(vals.min())
    ymax = float(vals.max())
    yr = ymax - ymin
    pad = 0.08 * yr if yr > 0 else 0.10
    return (ymin - pad, ymax + pad)


def compute_local_offset(sub_agg: pd.DataFrame, sub_grid: pd.DataFrame):
    vals = []
    vals.extend(sub_agg["2.5%"].dropna().tolist())
    vals.extend(sub_agg["97.5%"].dropna().tolist())
    vals.extend(sub_grid["ci_low"].dropna().tolist())
    vals.extend(sub_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = float(vals.max() - vals.min()) if vals.size > 0 else 1.0
    return 0.035 * yr if yr > 0 else 0.03


def style_axis(ax, ylabel=None, ylims=None):
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)


    ax.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter([str(t) for t in T_LIST]))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.yaxis.set_minor_locator(mticker.NullLocator())

    # Original notebook comment normalized for the public code archive.
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=TICK_FONTSIZE,
        length=4.5,
        width=1.0,
        color=rgba(TICK_COLOR, TICK_ALPHA),
        labelcolor=rgba(TICK_COLOR, TICK_ALPHA),
    )

    if ylabel is not None:
        ax.set_ylabel(
            ylabel,
            fontsize=LABEL_FONTSIZE,
            color=rgba(LABEL_COLOR, LABEL_ALPHA)
        )

    if ylims is not None:
        ax.set_ylim(*ylims)

    for side in ["left", "bottom", "top", "right"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(SPINE_LINEWIDTH)
        ax.spines[side].set_color(rgba(SPINE_COLOR, SPINE_ALPHA))

    ax.grid(False)

    # Original notebook comment normalized for the public code archive.
    ax.axhline(
        y=0,
        color=rgba(ZERO_LINE_COLOR, ZERO_LINE_ALPHA),
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        zorder=0
    )

    ax.set_xlabel("")


def add_panel_text(ax, txt):
    ax.text(
        0.03, 0.96, txt,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=PANEL_FONTSIZE,
        color=rgba(PANEL_TEXT_COLOR, PANEL_TEXT_ALPHA)
    )


# =========================================================
# 4. PLOTTING
# =========================================================

def plot_one_panel(ax, df_agg: pd.DataFrame, df_grid: pd.DataFrame,
                   sample: str, ylims=None, ylabel=None, panel_text=None):
    sub_agg = df_agg[df_agg["sample"] == sample].copy()
    sub_grid = df_grid[df_grid["sample"] == sample].copy()

    if sub_agg.empty or sub_grid.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        style_axis(ax, ylabel=ylabel, ylims=ylims)
        return

    offset = compute_local_offset(sub_agg, sub_grid)

    for rg in RISK_GROUPS:
        cfg = get_group_style(rg)

        # Original notebook comment normalized for the public code archive.
        g = sub_grid[sub_grid["risk_group"] == rg].copy().sort_values("T_grid")
        if not g.empty:
            ax.plot(
                g["T_grid"].to_numpy(float),
                g["beta_grid"].to_numpy(float),
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linewidth=cfg["line_width"],
                linestyle=cfg["line_style"],
                zorder=2
            )
            ax.fill_between(
                g["T_grid"].to_numpy(float),
                g["ci_low"].to_numpy(float),
                g["ci_high"].to_numpy(float),
                facecolor=rgba(cfg["band_face_color"], cfg["band_face_alpha"]),
                edgecolor=rgba(cfg["band_edge_color"], cfg["band_edge_alpha"]),
                linewidth=cfg["band_edge_width"],
                zorder=1
            )

        # Original notebook comment normalized for the public code archive.
        t = sub_agg[sub_agg["risk_group"] == rg].copy().sort_values("T")
        if not t.empty:
            xmult = 0.96 if rg == "low" else 1.04
            T_vals = t["T"].to_numpy(float) * xmult
            est = t["Estimate"].to_numpy(float)
            lo = t["2.5%"].to_numpy(float)
            hi = t["97.5%"].to_numpy(float)

            # Original notebook comment normalized for the public code archive.
            ax.vlines(
                T_vals,
                lo,
                hi,
                colors=rgba(cfg["errorbar_color"], cfg["errorbar_alpha"]),
                linewidth=cfg["errorbar_linewidth"],
                linestyles=cfg["errorbar_linestyle"],
                zorder=3
            )

            # Original notebook comment normalized for the public code archive.
            for x, ylo, yhi in zip(T_vals, lo, hi):
                cap_half = x * cfg["cap_half_width_factor"]

                ax.hlines(
                    ylo,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )
                ax.hlines(
                    yhi,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )

            # Original notebook comment normalized for the public code archive.
            ax.scatter(
                T_vals,
                est,
                s=cfg["marker_size"] ** 2,
                facecolors=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                edgecolors=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                linewidths=cfg["point_edge_width"],
                zorder=4
            )

            # Original notebook comment normalized for the public code archive.
            pvals = t["Pr(>|t|)"].to_numpy(float)
            for T0, b, p in zip(T_vals, est, pvals):
                st = stars_for_p(p)
                if not st:
                    continue
                if b >= 0:
                    yy = b + offset
                    va = "bottom"
                else:
                    yy = b - offset
                    va = "top"

                ax.text(
                    T0, yy, st,
                    ha="center", va=va,
                    fontsize=STAR_FONTSIZE,
                    color=rgba(cfg["star_color"], cfg["star_alpha"]),
                    zorder=5
                )

    style_axis(ax, ylabel=ylabel, ylims=ylims)

    if panel_text is not None:
        add_panel_text(ax, panel_text)


def save_standalone_legend():
    handles = []
    for rg in RISK_GROUPS:
        cfg = get_group_style(rg)
        handles.append(
            Line2D(
                [0], [0],
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linestyle=cfg["line_style"],
                marker="o",
                linewidth=cfg["line_width"],
                markersize=cfg["marker_size"],
                markerfacecolor=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                markeredgecolor=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                markeredgewidth=cfg["point_edge_width"],
                label=cfg["legend_label"]
            )
        )

    fig = plt.figure(figsize=(4.6, 0.95))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=12,
        handlelength=2.2,
        columnspacing=1.6,
        handletextpad=0.6
    )

    plt.tight_layout()
    plt.savefig(OUT_LEGEND_PNG, dpi=300, bbox_inches="tight", transparent=True)
    plt.savefig(OUT_LEGEND_SVG, bbox_inches="tight", transparent=True)
    plt.close(fig)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


def plot_combined(df_agg: pd.DataFrame, df_grid: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE, sharey=True)
    ylims = compute_global_ylim(df_agg, df_grid)

    panel_map = {"all": "All", "rural": "Rural", "urban": "Urban"}

    for i, (ax, s) in enumerate(zip(axes, SAMPLES)):
        ylabel = "Health loss" if i == 0 else None
        plot_one_panel(
            ax=ax,
            df_agg=df_agg,
            df_grid=df_grid,
            sample=s,
            ylims=ylims,
            ylabel=ylabel,
            panel_text=panel_map[s]
        )

    plt.subplots_adjust(left=0.08, right=0.985, bottom=0.15, top=0.96, wspace=0.10)
    plt.savefig(OUT_FIG_COMBINED, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_agg: pd.DataFrame, df_grid: pd.DataFrame, sample: str, out_path: Path):
    fig, ax = plt.subplots(figsize=SINGLE_FIGSIZE)

    sub_agg = df_agg[df_agg["sample"] == sample].copy()
    sub_grid = df_grid[df_grid["sample"] == sample].copy()
    ylims = compute_global_ylim(sub_agg, sub_grid)

    plot_one_panel(
        ax=ax,
        df_agg=df_agg,
        df_grid=df_grid,
        sample=sample,
        ylims=ylims,
        ylabel="",
        panel_text=None
    )

    plt.subplots_adjust(left=0.18, right=0.98, bottom=0.16, top=0.97)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 5. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")

    df_agg, df_grid = load_data()

    plot_combined(df_agg, df_grid)
    plot_single(df_agg, df_grid, "all", OUT_FIG_ALL)
    plot_single(df_agg, df_grid, "rural", OUT_FIG_RURAL)
    plot_single(df_agg, df_grid, "urban", OUT_FIG_URBAN)

    save_standalone_legend()

    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_figure2_high_low_risk_zoning.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figue2\high_low_risk\老年健康")

AGG_CSV = BASE_DIR / "fe_health_index_z_Tall_windowAgg_over_T_highlowRisk.csv"
GRID_CSV = BASE_DIR / "betaT_health_index_z_highlowRisk_meta_grid.csv"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
OUT_FIG_COMBINED = BASE_DIR / "betaT_health_index_z_highlowRisk_all_rural_urban_yfix_m1p5to1p5.png"
OUT_FIG_ALL = BASE_DIR / "betaT_health_index_z_highlowRisk_all_yfix_m1p5to1p5.png"
OUT_FIG_RURAL = BASE_DIR / "betaT_health_index_z_highlowRisk_rural_yfix_m1p5to1p5.png"
OUT_FIG_URBAN = BASE_DIR / "betaT_health_index_z_highlowRisk_urban_yfix_m1p5to1p5.png"

OUT_LEGEND_PNG = BASE_DIR / "legend_betaT_health_highlow_yfix_m1p5to1p5.png"
OUT_LEGEND_SVG = BASE_DIR / "legend_betaT_health_highlow_yfix_m1p5to1p5.svg"

Y_VAR = "health_index_z"
SAMPLES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
FIXED_YLIMS = (-1.5, 1.5)
FIXED_YTICKS = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]

# ---------------------------------------------------------
# 0A. GLOBAL STYLE
# ---------------------------------------------------------
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["axes.linewidth"] = 1.1

TICK_FONTSIZE = 18
LABEL_FONTSIZE = 16
PANEL_FONTSIZE = 13
STAR_FONTSIZE = 0

COMBINED_FIGSIZE = (13.6, 4.4)
SINGLE_FIGSIZE = (6.5, 5.2)

LINEWIDTH = 2.1
MARKERSIZE = 6.8
MARKEREDGEWIDTH = 0.9
CAPSIZE = 4.0
ERRORBAR_LINEWIDTH = 1.4
SPINE_LINEWIDTH = 0.8

# ---------------------------------------------------------
# 0B. ZERO LINE STYLE
# ---------------------------------------------------------
ZERO_LINE_COLOR = "#7f7f7f"
ZERO_LINE_ALPHA = 0.90
ZERO_LINE_STYLE = "--"
ZERO_LINE_WIDTH = 1.0

# ---------------------------------------------------------
# 0C. DEFAULT GROUP STYLE
# ---------------------------------------------------------
DEFAULT_GROUP_STYLE = {
    "legend_label": "Group",

    # main fitted line
    "line_color": "#01665e",
    "line_alpha": 1.00,
    "line_width": LINEWIDTH,
    "line_style": "-",

    # uncertainty band
    "band_face_color": "#01665e",
    "band_face_alpha": 0.20,
    "band_edge_color": "#01665e",
    "band_edge_alpha": 0.20,
    "band_edge_width": 0.8,

    # observed points
    "point_face_color": "#01665e",
    "point_face_alpha": 1.00,
    "point_edge_color": "#01665e",
    "point_edge_alpha": 1.00,
    "point_edge_width": MARKEREDGEWIDTH,
    "marker_size": MARKERSIZE,

    # Original notebook comment normalized for the public code archive.
    "errorbar_color": "#01665e",
    "errorbar_alpha": 1.00,
    "errorbar_linewidth": ERRORBAR_LINEWIDTH,
    "errorbar_linestyle": "-",

    # Original notebook comment normalized for the public code archive.
    "cap_color": "#01665e",
    "cap_alpha": 1.00,
    "cap_linewidth": ERRORBAR_LINEWIDTH,
    "cap_linestyle": "-",
    "cap_half_width_factor": 0.018,

    # Original notebook comment normalized for the public code archive.
    "capsize": CAPSIZE,

    # stars
    "star_color": "#01665e",
    "star_alpha": 1.00,
}

# ---------------------------------------------------------
# 0D. GROUP STYLE MAP
# ---------------------------------------------------------
STYLE_MAP = {
    "low": {
        "legend_label": "Low-risk cities",

        "line_color": "#01665e",
        "line_alpha": 0.50,
        "line_width": 1.6,
        "line_style": "--",   # Original notebook comment normalized for the public code archive.

        "band_face_color": "#01665e",
        "band_face_alpha": 0.15,
        "band_edge_color": "#01665e",
        "band_edge_alpha": 0.15,
        "band_edge_width": 0.8,

        "point_face_color": "#01665e",
        "point_face_alpha": 1.00,
        "point_edge_color": "#01665e",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        # Original notebook comment normalized for the public code archive.
        "errorbar_color": "#01665e",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "--",

        # Original notebook comment normalized for the public code archive.
        "cap_color": "#01665e",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "capsize": CAPSIZE,

        "star_color": "#01665e",
        "star_alpha": 1.00,
    },

    "high": {
        "legend_label": "High-risk cities",

        "line_color": "#01665e",
        "line_alpha": 1.00,
        "line_width": 2.3,
        "line_style": "-",    # Original notebook comment normalized for the public code archive.

        "band_face_color": "#01665e",
        "band_face_alpha": 0.32,
        "band_edge_color": "#01665e",
        "band_edge_alpha": 0.32,
        "band_edge_width": 0.8,

        "point_face_color": "#01665e",
        "point_face_alpha": 1.00,
        "point_edge_color": "#01665e",
        "point_edge_alpha": 1.00,
        "point_edge_width": MARKEREDGEWIDTH,
        "marker_size": MARKERSIZE,

        # Original notebook comment normalized for the public code archive.
        "errorbar_color": "#01665e",
        "errorbar_alpha": 1.00,
        "errorbar_linewidth": 1.8,
        "errorbar_linestyle": "-",

        # Original notebook comment normalized for the public code archive.
        "cap_color": "#01665e",
        "cap_alpha": 1.00,
        "cap_linewidth": 1.8,
        "cap_linestyle": "-",
        "cap_half_width_factor": 0.018,

        "capsize": CAPSIZE,

        "star_color": "#01665e",
        "star_alpha": 1.00,
    },
}

# ---------------------------------------------------------
# 0E. AXIS / FRAME STYLE
# ---------------------------------------------------------
SPINE_COLOR = "#000000"
SPINE_ALPHA = 1.00

TICK_COLOR = "#000000"
TICK_ALPHA = 1.00

LABEL_COLOR = "#000000"
LABEL_ALPHA = 1.00

PANEL_TEXT_COLOR = "#000000"
PANEL_TEXT_ALPHA = 1.00


# =========================================================
# 1. HELPERS
# =========================================================

def rgba(color, alpha):
    return to_rgba(color, alpha)


def get_group_style(group_name: str) -> dict:
    cfg = DEFAULT_GROUP_STYLE.copy()
    cfg.update(STYLE_MAP.get(group_name, {}))
    return cfg


def stars_for_p(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =========================================================
# 2. DATA IO
# =========================================================

def load_data():
    if not AGG_CSV.exists():
        raise FileNotFoundError(f"未找到聚合结果文件：{AGG_CSV}")
    if not GRID_CSV.exists():
        raise FileNotFoundError(f"未找到曲线网格文件：{GRID_CSV}")

    df_agg = pd.read_csv(AGG_CSV, encoding="utf-8-sig")
    df_grid = pd.read_csv(GRID_CSV, encoding="utf-8-sig")

    req_agg = ["Y_var", "sample", "risk_group", "T", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]
    req_grid = ["Y_var", "sample", "risk_group", "T_grid", "beta_grid", "ci_low", "ci_high"]

    miss_agg = [c for c in req_agg if c not in df_agg.columns]
    miss_grid = [c for c in req_grid if c not in df_grid.columns]

    if miss_agg:
        raise KeyError(f"agg 文件缺少列：{miss_agg}")
    if miss_grid:
        raise KeyError(f"grid 文件缺少列：{miss_grid}")

    df_agg = df_agg[df_agg["Y_var"].astype(str) == Y_VAR].copy()
    df_grid = df_grid[df_grid["Y_var"].astype(str) == Y_VAR].copy()

    for c in ["T", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]:
        df_agg[c] = pd.to_numeric(df_agg[c], errors="coerce")
    for c in ["T_grid", "beta_grid", "ci_low", "ci_high"]:
        df_grid[c] = pd.to_numeric(df_grid[c], errors="coerce")

    df_agg["sample"] = df_agg["sample"].astype(str).str.strip().str.lower()
    df_agg["risk_group"] = df_agg["risk_group"].astype(str).str.strip().str.lower()
    df_grid["sample"] = df_grid["sample"].astype(str).str.strip().str.lower()
    df_grid["risk_group"] = df_grid["risk_group"].astype(str).str.strip().str.lower()

    df_agg = df_agg[
        df_agg["sample"].isin(SAMPLES) &
        df_agg["risk_group"].isin(RISK_GROUPS)
    ].copy()

    df_grid = df_grid[
        df_grid["sample"].isin(SAMPLES) &
        df_grid["risk_group"].isin(RISK_GROUPS)
    ].copy()

    return df_agg, df_grid


# =========================================================
# 3. STYLE HELPERS
# =========================================================

def compute_local_offset(sub_agg: pd.DataFrame, sub_grid: pd.DataFrame):
    vals = []
    vals.extend(sub_agg["2.5%"].dropna().tolist())
    vals.extend(sub_agg["97.5%"].dropna().tolist())
    vals.extend(sub_grid["ci_low"].dropna().tolist())
    vals.extend(sub_grid["ci_high"].dropna().tolist())

    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = float(vals.max() - vals.min()) if vals.size > 0 else 1.0
    return 0.035 * yr if yr > 0 else 0.03


def style_axis(ax, ylabel=None, ylims=FIXED_YLIMS):
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)

    ax.xaxis.set_major_locator(mticker.FixedLocator(T_LIST))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter([str(t) for t in T_LIST]))
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    ax.yaxis.set_minor_locator(mticker.NullLocator())

    # Original notebook comment normalized for the public code archive.
    ax.set_ylim(*ylims)
    ax.set_yticks(FIXED_YTICKS)

    # Original notebook comment normalized for the public code archive.
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f'))

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=TICK_FONTSIZE,
        length=4.5,
        width=1.0,
        color=rgba(TICK_COLOR, TICK_ALPHA),
        labelcolor=rgba(TICK_COLOR, TICK_ALPHA),
    )

    if ylabel is not None:
        ax.set_ylabel(
            ylabel,
            fontsize=LABEL_FONTSIZE,
            color=rgba(LABEL_COLOR, LABEL_ALPHA)
        )

    for side in ["left", "bottom", "top", "right"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(SPINE_LINEWIDTH)
        ax.spines[side].set_color(rgba(SPINE_COLOR, SPINE_ALPHA))

    ax.grid(False)

    ax.axhline(
        y=0,
        color=rgba(ZERO_LINE_COLOR, ZERO_LINE_ALPHA),
        linestyle=ZERO_LINE_STYLE,
        linewidth=ZERO_LINE_WIDTH,
        zorder=0
    )

    ax.set_xlabel("")


def add_panel_text(ax, txt):
    ax.text(
        0.03, 0.96, txt,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=PANEL_FONTSIZE,
        color=rgba(PANEL_TEXT_COLOR, PANEL_TEXT_ALPHA)
    )


# =========================================================
# 4. PLOTTING
# =========================================================

def plot_one_panel(ax, df_agg: pd.DataFrame, df_grid: pd.DataFrame,
                   sample: str, ylims=FIXED_YLIMS, ylabel=None, panel_text=None):
    sub_agg = df_agg[df_agg["sample"] == sample].copy()
    sub_grid = df_grid[df_grid["sample"] == sample].copy()

    if sub_agg.empty or sub_grid.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        style_axis(ax, ylabel=ylabel, ylims=ylims)
        return

    offset = compute_local_offset(sub_agg, sub_grid)

    for rg in RISK_GROUPS:
        cfg = get_group_style(rg)

        # Original notebook comment normalized for the public code archive.
        g = sub_grid[sub_grid["risk_group"] == rg].copy().sort_values("T_grid")
        if not g.empty:
            ax.plot(
                g["T_grid"].to_numpy(float),
                g["beta_grid"].to_numpy(float),
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linewidth=cfg["line_width"],
                linestyle=cfg["line_style"],
                zorder=2
            )
            ax.fill_between(
                g["T_grid"].to_numpy(float),
                g["ci_low"].to_numpy(float),
                g["ci_high"].to_numpy(float),
                facecolor=rgba(cfg["band_face_color"], cfg["band_face_alpha"]),
                edgecolor=rgba(cfg["band_edge_color"], cfg["band_edge_alpha"]),
                linewidth=cfg["band_edge_width"],
                zorder=1
            )

        # Original notebook comment normalized for the public code archive.
        t = sub_agg[sub_agg["risk_group"] == rg].copy().sort_values("T")
        if not t.empty:
            xmult = 0.96 if rg == "low" else 1.04
            T_vals = t["T"].to_numpy(float) * xmult
            est = t["Estimate"].to_numpy(float)
            lo = t["2.5%"].to_numpy(float)
            hi = t["97.5%"].to_numpy(float)

            ax.vlines(
                T_vals,
                lo,
                hi,
                colors=rgba(cfg["errorbar_color"], cfg["errorbar_alpha"]),
                linewidth=cfg["errorbar_linewidth"],
                linestyles=cfg["errorbar_linestyle"],
                zorder=3
            )

            for x, ylo, yhi in zip(T_vals, lo, hi):
                cap_half = x * cfg["cap_half_width_factor"]

                ax.hlines(
                    ylo,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )
                ax.hlines(
                    yhi,
                    x - cap_half,
                    x + cap_half,
                    colors=rgba(cfg["cap_color"], cfg["cap_alpha"]),
                    linewidth=cfg["cap_linewidth"],
                    linestyles=cfg["cap_linestyle"],
                    zorder=3
                )

            ax.scatter(
                T_vals,
                est,
                s=cfg["marker_size"] ** 2,
                facecolors=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                edgecolors=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                linewidths=cfg["point_edge_width"],
                zorder=4
            )

            pvals = t["Pr(>|t|)"].to_numpy(float)
            for T0, b, p in zip(T_vals, est, pvals):
                st = stars_for_p(p)
                if not st:
                    continue
                if b >= 0:
                    yy = b + offset
                    va = "bottom"
                else:
                    yy = b - offset
                    va = "top"

                ax.text(
                    T0, yy, st,
                    ha="center", va=va,
                    fontsize=STAR_FONTSIZE,
                    color=rgba(cfg["star_color"], cfg["star_alpha"]),
                    zorder=5
                )

    style_axis(ax, ylabel=ylabel, ylims=ylims)

    if panel_text is not None:
        add_panel_text(ax, panel_text)


def save_standalone_legend():
    handles = []
    for rg in RISK_GROUPS:
        cfg = get_group_style(rg)
        handles.append(
            Line2D(
                [0], [0],
                color=rgba(cfg["line_color"], cfg["line_alpha"]),
                linestyle=cfg["line_style"],
                marker="o",
                linewidth=cfg["line_width"],
                markersize=cfg["marker_size"],
                markerfacecolor=rgba(cfg["point_face_color"], cfg["point_face_alpha"]),
                markeredgecolor=rgba(cfg["point_edge_color"], cfg["point_edge_alpha"]),
                markeredgewidth=cfg["point_edge_width"],
                label=cfg["legend_label"]
            )
        )

    fig = plt.figure(figsize=(4.6, 0.95))
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=12,
        handlelength=2.2,
        columnspacing=1.6,
        handletextpad=0.6
    )

    plt.tight_layout()
    plt.savefig(OUT_LEGEND_PNG, dpi=300, bbox_inches="tight", transparent=True)
    plt.savefig(OUT_LEGEND_SVG, bbox_inches="tight", transparent=True)
    plt.close(fig)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


def plot_combined(df_agg: pd.DataFrame, df_grid: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=COMBINED_FIGSIZE, sharey=True)

    panel_map = {"all": "All", "rural": "Rural", "urban": "Urban"}

    for i, (ax, s) in enumerate(zip(axes, SAMPLES)):
        ylabel = "Health loss" if i == 0 else None
        plot_one_panel(
            ax=ax,
            df_agg=df_agg,
            df_grid=df_grid,
            sample=s,
            ylims=FIXED_YLIMS,
            ylabel=ylabel,
            panel_text=panel_map[s]
        )

    plt.subplots_adjust(left=0.08, right=0.985, bottom=0.15, top=0.96, wspace=0.10)
    plt.savefig(OUT_FIG_COMBINED, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_agg: pd.DataFrame, df_grid: pd.DataFrame, sample: str, out_path: Path):
    fig, ax = plt.subplots(figsize=SINGLE_FIGSIZE)

    plot_one_panel(
        ax=ax,
        df_agg=df_agg,
        df_grid=df_grid,
        sample=sample,
        ylims=FIXED_YLIMS,
        ylabel="",
        panel_text=None
    )

    plt.subplots_adjust(left=0.18, right=0.98, bottom=0.16, top=0.97)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 5. MAIN
# =========================================================

def main():
    print("[INFO] Notebook progress message.")

    df_agg, df_grid = load_data()

    plot_combined(df_agg, df_grid)
    plot_single(df_agg, df_grid, "all", OUT_FIG_ALL)
    plot_single(df_agg, df_grid, "rural", OUT_FIG_RURAL)
    plot_single(df_agg, df_grid, "urban", OUT_FIG_URBAN)

    save_standalone_legend()

    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()
