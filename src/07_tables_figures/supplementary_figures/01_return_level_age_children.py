#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_return_level_age_children.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from __future__ import annotations
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization only:
Side-by-side bars (rural vs urban) with 95% CI error bars for age-bin coefficients.

Input CSV must contain at least:
  - sample  (rural/urban)
  - Estimate
and either:
  - bin_l, bin_r
or:
  - Term like "X_bin_00_01"

Optional:
  - CI_low, CI_high (preferred)
  - StdError (if CI_* not provided)
  - PValue (for significance stars)
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================================================
# 0. CONFIG
# =========================================================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\return_level_children")
IN_DIR = BASE_DIR
IN_CSV = BASE_DIR / "allfloods_agebins_rural_urban_results.csv"

OUT_PNG = IN_DIR / "ALLfloods_agebins_bar_rural_urban.png"
OUT_SVG = IN_DIR / "ALLfloods_agebins_bar_rural_urban.svg"  # optional

# Plot switches
SHOW_TITLE  = True
SHOW_LEGEND = True
SHOW_STARS  = True

# Axis labels
X_LABEL = "Age bin (years)"
Y_LABEL = "Coefficient on edu_years"

# Figure style (optional)
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False


# =========================================================
# 1. Helpers
# =========================================================

def stars_for_p(p) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""

def ensure_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure bin_l and bin_r exist.
    If missing, try to parse from Term: X_bin_00_01 (or similar).
    """
    out = df.copy()

    if ("bin_l" in out.columns) and ("bin_r" in out.columns):
        out["bin_l"] = pd.to_numeric(out["bin_l"], errors="coerce")
        out["bin_r"] = pd.to_numeric(out["bin_r"], errors="coerce")
        return out

    if "Term" not in out.columns:
        raise ValueError("Input CSV must contain (bin_l, bin_r) OR a 'Term' column to parse bins.")

    # Parse patterns like: X_bin_00_01
    pat = re.compile(r"X_bin_(\d{2})_(\d{2})")
    lr = out["Term"].astype(str).str.extract(pat)
    out["bin_l"] = pd.to_numeric(lr[0], errors="coerce")
    out["bin_r"] = pd.to_numeric(lr[1], errors="coerce")

    if out["bin_l"].isna().all() or out["bin_r"].isna().all():
        raise ValueError("Failed to parse bin_l/bin_r from Term. Please check Term format (e.g., X_bin_00_01).")

    return out

def ensure_ci(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure CI_low and CI_high exist. Prefer existing CI_*.
    If absent but StdError exists, compute CI_* = Estimate +/- 1.96*StdError.
    """
    out = df.copy()
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")

    if ("CI_low" in out.columns) and ("CI_high" in out.columns):
        out["CI_low"] = pd.to_numeric(out["CI_low"], errors="coerce")
        out["CI_high"] = pd.to_numeric(out["CI_high"], errors="coerce")
        return out

    if "StdError" not in out.columns:
        raise ValueError("Need (CI_low, CI_high) or StdError to draw error bars.")

    out["StdError"] = pd.to_numeric(out["StdError"], errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]
    return out


# =========================================================
# 2. Main plot function
# =========================================================

def plot_side_by_side_bars(df: pd.DataFrame, out_png: Path, out_svg: Path | None = None) -> None:
    df = ensure_bins(df)
    df = ensure_ci(df)

    # Basic checks
    needed = {"sample", "Estimate", "CI_low", "CI_high", "bin_l", "bin_r"}
    missing = sorted(list(needed - set(df.columns)))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Build bin label/order
    df["bin_l"] = pd.to_numeric(df["bin_l"], errors="coerce")
    df["bin_r"] = pd.to_numeric(df["bin_r"], errors="coerce")
    df = df.dropna(subset=["bin_l", "bin_r", "Estimate", "CI_low", "CI_high", "sample"]).copy()

    df["bin_l"] = df["bin_l"].astype(int)
    df["bin_r"] = df["bin_r"].astype(int)
    df["bin_label"] = df.apply(lambda r: f"{r['bin_l']}\u2013{r['bin_r']}", axis=1)

    # Order bins by (bin_l, bin_r)
    bins_sorted = (
        df[["bin_l", "bin_r", "bin_label"]]
        .drop_duplicates()
        .sort_values(["bin_l", "bin_r"])
    )
    bin_order = bins_sorted["bin_label"].tolist()

    # Enforce sample order
    df["sample"] = df["sample"].astype(str).str.lower()
    df = df[df["sample"].isin(["rural", "urban"])].copy()

    # Pivot to wide
    df["bin_label"] = pd.Categorical(df["bin_label"], categories=bin_order, ordered=True)
    df["sample"] = pd.Categorical(df["sample"], categories=["rural", "urban"], ordered=True)

    est = df.pivot(index="bin_label", columns="sample", values="Estimate").reindex(bin_order)
    lo  = df.pivot(index="bin_label", columns="sample", values="CI_low").reindex(bin_order)
    hi  = df.pivot(index="bin_label", columns="sample", values="CI_high").reindex(bin_order)
    pv  = None
    if "PValue" in df.columns:
        pv = df.pivot(index="bin_label", columns="sample", values="PValue").reindex(bin_order)

    x = np.arange(len(bin_order))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    ax.axhline(0, linestyle="--", linewidth=1)

    for j, s in enumerate(["rural", "urban"]):
        if s not in est.columns:
            continue

        y = est[s].to_numpy(dtype=float)
        ylo = lo[s].to_numpy(dtype=float)
        yhi = hi[s].to_numpy(dtype=float)
        yerr = np.vstack([y - ylo, yhi - y])

        xpos = x + (j - 0.5) * width
        ax.bar(xpos, y, width=width, label=s)
        ax.errorbar(xpos, y, yerr=yerr, fmt="none", capsize=4, linewidth=1)

        # Significance stars (optional)
        if SHOW_STARS and (pv is not None) and (s in pv.columns):
            pvals = pd.to_numeric(pv[s], errors="coerce").to_numpy(dtype=float)
            # Offset based on current y-range
            y0, y1 = ax.get_ylim()
            off = 0.03 * (y1 - y0 if y1 > y0 else 1.0)
            for xi, yi, pi in zip(xpos, y, pvals):
                st = stars_for_p(pi)
                if st and np.isfinite(yi):
                    ax.text(
                        xi,
                        yi + (off if yi >= 0 else -off),
                        st,
                        ha="center",
                        va=("bottom" if yi >= 0 else "top"),
                        fontsize=11
                    )

    ax.set_xticks(x)
    ax.set_xticklabels(bin_order, rotation=0)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)

    if SHOW_TITLE:
        ax.set_title("All floods (no return period, no severity) | Age bins | Rural vs Urban")

    if SHOW_LEGEND:
        ax.legend(title="sample")
    else:
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()

    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=300)
    if out_svg is not None:
        plt.savefig(out_svg)
    plt.show()


# =========================================================
# 3. Run
# =========================================================

def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    plot_side_by_side_bars(df, OUT_PNG, out_svg=OUT_SVG)
    print(f"[DONE] Saved: {OUT_PNG}")
    print(f"[DONE] Saved: {OUT_SVG}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization only (horizontal layout):
Age bins on Y-axis (tall figure), coefficients on X-axis (short width).
Side-by-side horizontal bars (rural vs urban) with 95% CI error bars.

Input CSV must contain at least:
  - sample  (rural/urban)
  - Estimate
and either:
  - bin_l, bin_r
or:
  - Term like "X_bin_00_01"

Optional:
  - CI_low, CI_high (preferred)
  - StdError (if CI_* not provided)
  - PValue (for significance stars)
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================================================
# 0. CONFIG
# =========================================================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\return_level_children")
IN_CSV   = BASE_DIR / "allfloods_agebins_rural_urban_results.csv"

OUT_PNG  = BASE_DIR / "ALLfloods_agebins_barh_rural_urban.png"
OUT_SVG  = BASE_DIR / "ALLfloods_agebins_barh_rural_urban.svg"  # optional

# Plot switches
SHOW_TITLE  = True
SHOW_LEGEND = True
SHOW_STARS  = True

# Layout (tall & narrow)
FIGSIZE = (6.4, 9.2)   # (width, height)

# Y ordering: if True, youngest bin shown at the top
YOUNGEST_ON_TOP = True

# Axis labels
X_LABEL = "Coefficient on edu_years"
Y_LABEL = "Age bin (years)"

# Style
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False


# =========================================================
# 1. Helpers
# =========================================================

def stars_for_p(p) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""

def ensure_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure bin_l and bin_r exist.
    If missing, parse from Term like: X_bin_00_01
    """
    out = df.copy()

    if ("bin_l" in out.columns) and ("bin_r" in out.columns):
        out["bin_l"] = pd.to_numeric(out["bin_l"], errors="coerce")
        out["bin_r"] = pd.to_numeric(out["bin_r"], errors="coerce")
        return out

    if "Term" not in out.columns:
        raise ValueError("Input CSV must contain (bin_l, bin_r) OR a 'Term' column to parse bins.")

    pat = re.compile(r"X_bin_(\d{2})_(\d{2})")
    lr = out["Term"].astype(str).str.extract(pat)
    out["bin_l"] = pd.to_numeric(lr[0], errors="coerce")
    out["bin_r"] = pd.to_numeric(lr[1], errors="coerce")

    if out["bin_l"].isna().all() or out["bin_r"].isna().all():
        raise ValueError("Failed to parse bin_l/bin_r from Term (expecting X_bin_00_01 style).")

    return out

def ensure_ci(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure CI_low and CI_high exist.
    Prefer existing CI_*; otherwise compute from StdError.
    """
    out = df.copy()
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")

    if ("CI_low" in out.columns) and ("CI_high" in out.columns):
        out["CI_low"] = pd.to_numeric(out["CI_low"], errors="coerce")
        out["CI_high"] = pd.to_numeric(out["CI_high"], errors="coerce")
        return out

    if "StdError" not in out.columns:
        raise ValueError("Need (CI_low, CI_high) or StdError to draw 95% CI error bars.")

    out["StdError"] = pd.to_numeric(out["StdError"], errors="coerce")
    out["CI_low"]  = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]
    return out


# =========================================================
# 2. Plot (horizontal, age on Y axis)
# =========================================================

def plot_side_by_side_barh(df: pd.DataFrame, out_png: Path, out_svg: Path | None = None) -> None:
    df = ensure_bins(df)
    df = ensure_ci(df)

    needed = {"sample", "Estimate", "CI_low", "CI_high", "bin_l", "bin_r"}
    missing = sorted(list(needed - set(df.columns)))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Clean + build labels
    df["sample"] = df["sample"].astype(str).str.lower()
    df = df[df["sample"].isin(["rural", "urban"])].copy()

    df["bin_l"] = pd.to_numeric(df["bin_l"], errors="coerce")
    df["bin_r"] = pd.to_numeric(df["bin_r"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["CI_low"] = pd.to_numeric(df["CI_low"], errors="coerce")
    df["CI_high"] = pd.to_numeric(df["CI_high"], errors="coerce")

    df = df.dropna(subset=["bin_l", "bin_r", "Estimate", "CI_low", "CI_high", "sample"]).copy()
    df["bin_l"] = df["bin_l"].astype(int)
    df["bin_r"] = df["bin_r"].astype(int)
    df["bin_label"] = df.apply(lambda r: f"{r['bin_l']}\u2013{r['bin_r']}", axis=1)

    # Order by age (bin_l, bin_r)
    bins_sorted = (
        df[["bin_l", "bin_r", "bin_label"]]
        .drop_duplicates()
        .sort_values(["bin_l", "bin_r"])
    )
    bin_order = bins_sorted["bin_label"].tolist()

    # Wide matrices for plotting
    df["bin_label"] = pd.Categorical(df["bin_label"], categories=bin_order, ordered=True)
    df["sample"] = pd.Categorical(df["sample"], categories=["rural", "urban"], ordered=True)

    est = df.pivot(index="bin_label", columns="sample", values="Estimate").reindex(bin_order)
    lo  = df.pivot(index="bin_label", columns="sample", values="CI_low").reindex(bin_order)
    hi  = df.pivot(index="bin_label", columns="sample", values="CI_high").reindex(bin_order)

    pv = None
    if "PValue" in df.columns:
        pv = df.pivot(index="bin_label", columns="sample", values="PValue").reindex(bin_order)

    n = len(bin_order)
    y = np.arange(n)
    height = 0.36

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Reference line at 0
    ax.axvline(0, linestyle="--", linewidth=1)

    for j, s in enumerate(["rural", "urban"]):
        if s not in est.columns:
            continue

        xval = est[s].to_numpy(dtype=float)
        xlo  = lo[s].to_numpy(dtype=float)
        xhi  = hi[s].to_numpy(dtype=float)

        y_pos = y + (j - 0.5) * height

        # Bars
        ax.barh(y_pos, xval, height=height, label=s)

        # Horizontal error bars (95% CI)
        xerr = np.vstack([xval - xlo, xhi - xval])
        ax.errorbar(xval, y_pos, xerr=xerr, fmt="none", capsize=4, linewidth=1)

        # Significance stars (optional)
        if SHOW_STARS and (pv is not None) and (s in pv.columns):
            pvals = pd.to_numeric(pv[s], errors="coerce").to_numpy(dtype=float)

            # Offset in x-direction based on x-limits
            x0, x1 = ax.get_xlim()
            off = 0.02 * (x1 - x0 if x1 > x0 else 1.0)

            for xi, yi, pi in zip(xval, y_pos, pvals):
                st = stars_for_p(pi)
                if not st or not np.isfinite(xi):
                    continue
                if xi >= 0:
                    ax.text(xi + off, yi, st, va="center", ha="left", fontsize=11)
                else:
                    ax.text(xi - off, yi, st, va="center", ha="right", fontsize=11)

    # Y ticks centered on bins
    ax.set_yticks(y)
    ax.set_yticklabels(bin_order)
    ax.set_ylabel(Y_LABEL)
    ax.set_xlabel(X_LABEL)

    if YOUNGEST_ON_TOP:
        ax.invert_yaxis()

    if SHOW_TITLE:
        ax.set_title("All floods (no return period, no severity) | Age bins | Rural vs Urban")

    if SHOW_LEGEND:
        ax.legend(title="sample", loc="best")
    else:
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()

    plt.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=300)
    if out_svg is not None:
        plt.savefig(out_svg)

    plt.show()
    plt.close(fig)


# =========================================================
# 3. Run
# =========================================================

def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    plot_side_by_side_barh(df, OUT_PNG, out_svg=OUT_SVG)

    print(f"[DONE] Saved: {OUT_PNG}")
    print(f"[DONE] Saved: {OUT_SVG}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization only (horizontal layout):
Age bins on Y-axis (tall figure), coefficients on X-axis (short width).
Side-by-side horizontal bars (rural vs urban) with 95% CI error bars.

Input CSV must contain at least:
  - sample  (rural/urban)
  - Estimate
and either:
  - bin_l, bin_r
or:
  - Term like "X_bin_00_01"

Optional:
  - CI_low, CI_high (preferred)
  - StdError (if CI_* not provided)
  - PValue (for significance stars)
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================================================
# 0. CONFIG
# =========================================================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\return_level_children")
IN_CSV   = BASE_DIR / "allfloods_agebins_rural_urban_results.csv"

OUT_PNG  = BASE_DIR / "ALLfloods_agebins_barh_rural_urban.png"
OUT_SVG  = BASE_DIR / "ALLfloods_agebins_barh_rural_urban.svg"  # optional

# Plot switches
SHOW_TITLE  = True
SHOW_LEGEND = False  # do NOT show legend
SHOW_STARS  = True

# Colors (as requested)
RURAL_COLOR = "#D9D9D9"
URBAN_COLOR = "#595959"

# Layout (tall & narrow)
FIGSIZE = (6.4, 9.2)   # (width, height)

# Y ordering: if True, youngest bin shown at the top
YOUNGEST_ON_TOP = True

# Axis labels
X_LABEL = "Coefficient on edu_years"
Y_LABEL = "Age bin (years)"

# Style
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False


# =========================================================
# 1. Helpers
# =========================================================

def stars_for_p(p) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""

def ensure_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure bin_l and bin_r exist.
    If missing, parse from Term like: X_bin_00_01
    """
    out = df.copy()

    if ("bin_l" in out.columns) and ("bin_r" in out.columns):
        out["bin_l"] = pd.to_numeric(out["bin_l"], errors="coerce")
        out["bin_r"] = pd.to_numeric(out["bin_r"], errors="coerce")
        return out

    if "Term" not in out.columns:
        raise ValueError("Input CSV must contain (bin_l, bin_r) OR a 'Term' column to parse bins.")

    pat = re.compile(r"X_bin_(\d{2})_(\d{2})")
    lr = out["Term"].astype(str).str.extract(pat)
    out["bin_l"] = pd.to_numeric(lr[0], errors="coerce")
    out["bin_r"] = pd.to_numeric(lr[1], errors="coerce")

    if out["bin_l"].isna().all() or out["bin_r"].isna().all():
        raise ValueError("Failed to parse bin_l/bin_r from Term (expecting X_bin_00_01 style).")

    return out

def ensure_ci(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure CI_low and CI_high exist.
    Prefer existing CI_*; otherwise compute from StdError.
    """
    out = df.copy()
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")

    if ("CI_low" in out.columns) and ("CI_high" in out.columns):
        out["CI_low"] = pd.to_numeric(out["CI_low"], errors="coerce")
        out["CI_high"] = pd.to_numeric(out["CI_high"], errors="coerce")
        return out

    if "StdError" not in out.columns:
        raise ValueError("Need (CI_low, CI_high) or StdError to draw 95% CI error bars.")

    out["StdError"] = pd.to_numeric(out["StdError"], errors="coerce")
    out["CI_low"]  = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]
    return out


# =========================================================
# 2. Plot (horizontal, age on Y axis)
# =========================================================

def plot_side_by_side_barh(df: pd.DataFrame, out_png: Path, out_svg: Path | None = None) -> None:
    df = ensure_bins(df)
    df = ensure_ci(df)

    needed = {"sample", "Estimate", "CI_low", "CI_high", "bin_l", "bin_r"}
    missing = sorted(list(needed - set(df.columns)))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Clean + build labels
    df["sample"] = df["sample"].astype(str).str.lower()
    df = df[df["sample"].isin(["rural", "urban"])].copy()

    df["bin_l"] = pd.to_numeric(df["bin_l"], errors="coerce")
    df["bin_r"] = pd.to_numeric(df["bin_r"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["CI_low"] = pd.to_numeric(df["CI_low"], errors="coerce")
    df["CI_high"] = pd.to_numeric(df["CI_high"], errors="coerce")

    df = df.dropna(subset=["bin_l", "bin_r", "Estimate", "CI_low", "CI_high", "sample"]).copy()
    df["bin_l"] = df["bin_l"].astype(int)
    df["bin_r"] = df["bin_r"].astype(int)
    df["bin_label"] = df.apply(lambda r: f"{r['bin_l']}\u2013{r['bin_r']}", axis=1)

    # Order by age (bin_l, bin_r)
    bins_sorted = (
        df[["bin_l", "bin_r", "bin_label"]]
        .drop_duplicates()
        .sort_values(["bin_l", "bin_r"])
    )
    bin_order = bins_sorted["bin_label"].tolist()

    # Wide matrices for plotting
    df["bin_label"] = pd.Categorical(df["bin_label"], categories=bin_order, ordered=True)
    df["sample"] = pd.Categorical(df["sample"], categories=["rural", "urban"], ordered=True)

    est = df.pivot(index="bin_label", columns="sample", values="Estimate").reindex(bin_order)
    lo  = df.pivot(index="bin_label", columns="sample", values="CI_low").reindex(bin_order)
    hi  = df.pivot(index="bin_label", columns="sample", values="CI_high").reindex(bin_order)

    pv = None
    if "PValue" in df.columns:
        pv = df.pivot(index="bin_label", columns="sample", values="PValue").reindex(bin_order)

    n = len(bin_order)
    y = np.arange(n)
    height = 0.36

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Reference line at 0
    ax.axvline(0, linestyle="--", linewidth=1, color="grey")

    color_map = {"rural": RURAL_COLOR, "urban": URBAN_COLOR}

    for j, s in enumerate(["rural", "urban"]):
        if s not in est.columns:
            continue

        xval = est[s].to_numpy(dtype=float)
        xlo  = lo[s].to_numpy(dtype=float)
        xhi  = hi[s].to_numpy(dtype=float)

        y_pos = y + (j - 0.5) * height

        # Bars with requested colors
        ax.barh(y_pos, xval, height=height, color=color_map[s], edgecolor="black", linewidth=0.6)

        # Horizontal error bars (95% CI)
        xerr = np.vstack([xval - xlo, xhi - xval])
        ax.errorbar(xval, y_pos, xerr=xerr, fmt="none", capsize=4, linewidth=1, color="black")

        # Significance stars (optional)
        if SHOW_STARS and (pv is not None) and (s in pv.columns):
            pvals = pd.to_numeric(pv[s], errors="coerce").to_numpy(dtype=float)

            # Offset in x-direction based on x-limits
            x0, x1 = ax.get_xlim()
            off = 0.02 * (x1 - x0 if x1 > x0 else 1.0)

            for xi, yi, pi in zip(xval, y_pos, pvals):
                st = stars_for_p(pi)
                if not st or not np.isfinite(xi):
                    continue
                if xi >= 0:
                    ax.text(xi + off, yi, st, va="center", ha="left", fontsize=11)
                else:
                    ax.text(xi - off, yi, st, va="center", ha="right", fontsize=11)

    # Y ticks centered on bins
    ax.set_yticks(y)
    ax.set_yticklabels(bin_order)
    ax.set_ylabel(Y_LABEL)
    ax.set_xlabel(X_LABEL)

    if YOUNGEST_ON_TOP:
        ax.invert_yaxis()

    if SHOW_TITLE:
        ax.set_title("All floods (no return period, no severity) | Age bins | Rural vs Urban")

    # Do NOT show legend
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()

    plt.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=300)
    if out_svg is not None:
        plt.savefig(out_svg)

    plt.show()
    plt.close(fig)


# =========================================================
# 3. Run
# =========================================================

def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    plot_side_by_side_barh(df, OUT_PNG, out_svg=OUT_SVG)

    print(f"[DONE] Saved: {OUT_PNG}")
    print(f"[DONE] Saved: {OUT_SVG}")

if __name__ == "__main__":
    main()
