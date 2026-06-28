#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_figure2_high_low_risk_robustness_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_figure2_high_low_risk_robustness_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib import rcParams
from matplotlib.patches import Rectangle

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\high_low_sensitivety")
OUT_DIR = BASE_DIR / "replot"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
EDU_SUMMARY_CSV = BASE_DIR / "edu_sig_subset_summary_strict.csv"
EDU_SUMMARY_PARQUET = BASE_DIR / "edu_sig_subset_summary_strict.parquet"

OLDER_SUMMARY_CSV = BASE_DIR / "older_sig_subset_summary_strict.csv"
OLDER_SUMMARY_PARQUET = BASE_DIR / "older_sig_subset_summary_strict.parquet"

# Original notebook comment normalized for the public code archive.
EDU_OUT_PNG = OUT_DIR / "edu_sig_subset_heatmap_strict_replot.png"
OLDER_OUT_PNG = OUT_DIR / "older_sig_subset_heatmap_strict_replot.png"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
FONT_FAMILY = "Times New Roman"
USE_MINUS_FIX = True   # Original notebook comment normalized for the public code archive.

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
FS_GLOBAL = 20         # Original notebook comment normalized for the public code archive.
FS_TICK = 20           # Original notebook comment normalized for the public code archive.
FS_LABEL = 24          # Original notebook comment normalized for the public code archive.
FS_CELL = 16           # Original notebook comment normalized for the public code archive.
FS_CBAR_LABEL = 18     # Original notebook comment normalized for the public code archive.
FS_CBAR_TICK = 16      # Original notebook comment normalized for the public code archive.

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
FIG_W = 13.0
FIG_H = 9.0
SAVE_DPI = 300

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
XLAB = "Return level"
YLAB = "Sample × risk areas"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
CBAR_LABEL = "Pooled effect within significant subset"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
GRID_LINEWIDTH = 1.5
BORDER_LINEWIDTH = 2.0
BORDER_COLOR = "gray"
BORDER_STYLE = "--"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
MIN_SIG_EDU = 3
MIN_SIG_OLDER = 9
REL_TOL = 0.30

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
T_ORDER = [2, 5, 10, 20, 50, 100]

ROW_ORDER = [
    ("all", "low"),
    ("all", "high"),
    ("rural", "low"),
    ("rural", "high"),
    ("urban", "low"),
    ("urban", "high"),
]

ROW_LABELS = [
    "All × Low-risk",
    "All × High-risk",
    "Rural × Low-risk",
    "Rural × High-risk",
    "Urban × Low-risk",
    "Urban × High-risk",
]

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
HEATMAP_CMAP = "RdBu_r"

# -------------------------
# Original notebook comment normalized for the public code archive.
# -------------------------
TIGHT_LAYOUT_RECT = [0.02, 0.02, 0.98, 0.98]

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
rcParams["font.family"] = FONT_FAMILY
rcParams["font.size"] = FS_GLOBAL
if USE_MINUS_FIX:
    rcParams["axes.unicode_minus"] = False

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def fmt_beta(x):
    if pd.isna(x):
        return "NA"
    x = float(x)
    ax = abs(x)
    if ax >= 1:
        return f"{x:+.2f}"
    elif ax >= 0.1:
        return f"{x:+.2f}"
    else:
        return f"{x:+.3f}"


def fmt_count(n, N):
    if pd.isna(n) or pd.isna(N) or N <= 0:
        return "NA"
    return f"{int(n)}/{int(N)}"


def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def read_summary_file(csv_path: Path, parquet_path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_figure2_high_low_risk_robustness_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if csv_path.exists():
        print(f"[READ CSV] {csv_path}")
        return pd.read_csv(csv_path)

    if parquet_path.exists():
        print(f"[READ PARQUET] {parquet_path}")
        return pd.read_parquet(parquet_path)

    raise FileNotFoundError(
        f"Neither CSV nor parquet file exists:\n"
        f"  CSV: {csv_path}\n"
        f"  PARQUET: {parquet_path}"
    )

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def build_heatmap_matrices(summary_df: pd.DataFrame):
    """Archived notebook note for 05_figure2_high_low_risk_robustness_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    nrow = len(ROW_ORDER)
    ncol = len(T_ORDER)

    beta_mat = np.full((nrow, ncol), np.nan, dtype=float)
    text_mat = [["" for _ in range(ncol)] for _ in range(nrow)]
    sufficient_mat = np.zeros((nrow, ncol), dtype=bool)

    for i, (sample_type, risk_group) in enumerate(ROW_ORDER):
        for j, T in enumerate(T_ORDER):
            sub = summary_df[
                (summary_df["sample_type"] == sample_type) &
                (summary_df["risk_group"] == risk_group) &
                (np.isclose(summary_df["T"], T))
            ].copy()

            if sub.empty:
                text_mat[i][j] = "NA"
                continue

            row = sub.iloc[0]

            n_spec = row["n_spec"]
            n_sig = row["n_sig"]
            beta_ivw_sig = row["beta_ivw_sig"]
            sign_same_sig_n = row["sign_same_sig_n"]
            close_sig_n = row["close_sig_n"]
            signal_status = row["signal_status"]

            sufficient_mat[i, j] = (signal_status == "sufficient-signal")

            if signal_status == "sufficient-signal" and pd.notna(beta_ivw_sig):
                beta_mat[i, j] = float(beta_ivw_sig)

            if signal_status != "sufficient-signal":
                text_mat[i][j] = "insufficient"

            else:
                text_mat[i][j] = (
                    f"sig {fmt_count(n_sig, n_spec)}\n"
                    f"sign {fmt_count(sign_same_sig_n, n_sig)}\n"
                    f"close {fmt_count(close_sig_n, n_sig)}\n"
                    f"β={fmt_beta(beta_ivw_sig)}"
                )

    return beta_mat, text_mat, sufficient_mat

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def plot_sig_subset_heatmap(
    summary_df: pd.DataFrame,
    out_png: Path,
):
    beta_mat, text_mat, sufficient_mat = build_heatmap_matrices(summary_df)

    vals = beta_mat[np.isfinite(beta_mat)]
    if vals.size == 0:
        vabs = 1.0
    else:
        vabs = float(np.nanmax(np.abs(vals)))
        if (not np.isfinite(vabs)) or (vabs == 0):
            vabs = 1.0

    norm = TwoSlopeNorm(vmin=-vabs, vcenter=0.0, vmax=vabs)

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    im = ax.imshow(beta_mat, cmap=HEATMAP_CMAP, norm=norm, aspect="auto")

    # -------------------------
    # Original notebook comment normalized for the public code archive.
    # -------------------------
    ax.set_xticks(np.arange(len(T_ORDER)))
    ax.set_xticklabels(
        [str(t) for t in T_ORDER],
        fontsize=FS_TICK,
        fontname=FONT_FAMILY
    )

    ax.set_yticks(np.arange(len(ROW_LABELS)))
    ax.set_yticklabels(
        ROW_LABELS,
        fontsize=FS_TICK,
        fontname=FONT_FAMILY,
        rotation=0
    )

    # -------------------------
    # Original notebook comment normalized for the public code archive.
    # -------------------------
    ax.set_xlabel(XLAB, fontsize=FS_LABEL, fontname=FONT_FAMILY)
    ax.set_ylabel(YLAB, fontsize=FS_LABEL, fontname=FONT_FAMILY)

    # -------------------------
    # Original notebook comment normalized for the public code archive.
    # -------------------------
    ax.set_xticks(np.arange(-0.5, len(T_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROW_LABELS), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=GRID_LINEWIDTH)
    ax.tick_params(which="minor", bottom=False, left=False)

    # -------------------------
    # Original notebook comment normalized for the public code archive.
    # -------------------------
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            if not sufficient_mat[i, j]:
                rect = Rectangle(
                    (j - 0.5, i - 0.5),
                    1,
                    1,
                    fill=False,
                    edgecolor=BORDER_COLOR,
                    linewidth=BORDER_LINEWIDTH,
                    linestyle=BORDER_STYLE,
                )
                ax.add_patch(rect)

    # -------------------------
    # Original notebook comment normalized for the public code archive.
    # -------------------------
    for i in range(beta_mat.shape[0]):
        for j in range(beta_mat.shape[1]):
            val = beta_mat[i, j]
            txt = text_mat[i][j]

            if np.isfinite(val) and abs(val) > 0.55 * vabs:
                text_color = "white"
            else:
                text_color = "black"

            ax.text(
                j, i, txt,
                ha="center",
                va="center",
                fontsize=FS_CELL,
                color=text_color,
                fontname=FONT_FAMILY
            )

    # -------------------------
    # colorbar
    # -------------------------
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label(CBAR_LABEL, fontsize=FS_CBAR_LABEL, fontname=FONT_FAMILY)

    for tick in cbar.ax.get_yticklabels():
        tick.set_fontname(FONT_FAMILY)
        tick.set_fontsize(FS_CBAR_TICK)

    # Original notebook comment normalized for the public code archive.
    plt.tight_layout(rect=TIGHT_LAYOUT_RECT)
    fig.savefig(out_png, dpi=SAVE_DPI, bbox_inches="tight")
    plt.close(fig)

    print(f"[SAVED] {out_png}")

# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================

def run_education():
    df = read_summary_file(EDU_SUMMARY_CSV, EDU_SUMMARY_PARQUET)
    df = safe_numeric(
        df,
        ["T", "n_spec", "n_sig", "beta_ivw_sig", "sign_same_sig_n", "close_sig_n"]
    )

    plot_sig_subset_heatmap(
        summary_df=df,
        out_png=EDU_OUT_PNG,
    )


def run_older():
    df = read_summary_file(OLDER_SUMMARY_CSV, OLDER_SUMMARY_PARQUET)
    df = safe_numeric(
        df,
        ["T", "n_spec", "n_sig", "beta_ivw_sig", "sign_same_sig_n", "close_sig_n"]
    )

    plot_sig_subset_heatmap(
        summary_df=df,
        out_png=OLDER_OUT_PNG,
    )


def main():
    print("=" * 80)
    print("[STEP] Replot education")
    print("=" * 80)
    run_education()

    print("\n" + "=" * 80)
    print("[STEP] Replot older health")
    print("=" * 80)
    run_older()

    print("\n[ALL DONE]")
    print(f"[OUT] {OUT_DIR}")


if __name__ == "__main__":
    main()
