#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_school_period_terms.

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
Visualization of "School inundation: term-count mechanism" regression results
(Plot only; measure == 'term'; k_term up to 18)
==========================================================================

Input (preferred):
  E:\impact_assessment_child_order\data\supplement\school_periods\output\school_term_mechanism_FE_terms.csv

Fallbacks:
  - E:\impact_assessment_child_order\data\supplement\school_periods\school_term_mechanism_FE_terms.csv
  - Recursively search under BASE_DIR for the same filename (pick the most recently modified)

Required columns:
  sample, measure, k_term, Estimate, StdError, PValue

Output:
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    school_term_mechanism_term_line.png

Notes:
  - Two lines: rural vs urban
  - Error bars: 95% CI = 1.96 * StdError
  - Significance stars:
      p < 0.10 : *
      p < 0.05 : **
      p < 0.01 : ***
  - Font: Times New Roman
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 14,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
})

# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")

CSV_NAME = "school_term_mechanism_FE_terms.csv"
CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "school_term_mechanism_term_line.png"


def sig_label(p: float) -> str:
    """Significance stars based on p-value."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def find_input_csv() -> Path:
    """Find input CSV (preferred -> fallback -> recursive search)."""
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"Cannot find input CSV: {CSV_NAME}\n\n"
        "Please place it at one of the following locations:\n"
        f"  1) {CSV_PRIMARY}\n"
        f"  2) {CSV_SECONDARY}\n"
        "Or ensure it exists somewhere under:\n"
        f"  {BASE_DIR}\n"
    )


def prepare_data(csv_path: Path) -> pd.DataFrame:
    """
    Read results; keep sample in {rural, urban}, measure == 'term',
    and k_term in [0, 18].
    """
    print(f"[INFO] Reading: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[INFO] Raw shape: {df.shape}")

    need_cols = ["sample", "measure", "k_term", "Estimate", "StdError", "PValue"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    # keep rural / urban
    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("No rows found for sample in {'rural','urban'}.")

    # keep measure == term
    if not (df["measure"] == "term").any():
        raise RuntimeError("No rows found with measure == 'term'.")
    df = df[df["measure"] == "term"].copy()

    # numeric conversions
    for c in ["k_term", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["k_term", "Estimate", "StdError"]).copy()
    df["k_term"] = df["k_term"].astype(int)

    # limit k_term to [0, 18]
    df = df[(df["k_term"] >= 0) & (df["k_term"] <= 18)].copy()
    if df.empty:
        raise RuntimeError("No data after filtering k_term in [0, 18].")

    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Preview:")
    print(df.head())
    return df


def plot_term_line(df: pd.DataFrame) -> None:
    """Line + error bars (95% CI) + significance stars; rural vs urban."""
    out = OUT_PNG
    z = 1.96

    fig, ax = plt.subplots(figsize=(7.2, 4.6))

    for sample in ["rural", "urban"]:
        s = df[df["sample"] == sample].sort_values("k_term")
        if s.empty:
            continue

        x = s["k_term"].to_numpy()
        y = s["Estimate"].to_numpy()
        yerr = (z * s["StdError"]).to_numpy()

        ax.errorbar(
            x, y,
            yerr=yerr,
            marker="o",
            linestyle="-",
            capsize=3,
            linewidth=1.4,
            label=sample.capitalize(),
        )

        # stars above upper CI
        y_scale = np.nanmax(np.abs(np.r_[s["CI_low"].to_numpy(), s["CI_high"].to_numpy()]))
        if not np.isfinite(y_scale) or y_scale == 0:
            y_scale = 1.0
        dy = 0.01 * y_scale

        for xi, yi, ei, sig in zip(x, y, yerr, s["sig"].to_numpy()):
            if sig:
                ax.text(xi, yi + ei + dy, sig, ha="center", va="bottom", fontsize=11)

    ax.axhline(0.0, linestyle="--", linewidth=1.0, color="black")

    # x-axis 0..18
    ax.set_xticks(list(range(0, 19)))
    ax.set_xticklabels([str(k) for k in range(0, 19)])

    ax.set_xlabel("Number of flooded terms during schooling (terms)")
    ax.set_ylabel("Marginal effect on years of schooling (years)")
    ax.set_title("School inundation mechanism (term count) — term")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.close(fig)
    print(f"[DONE] {out}")


def main():
    csv_path = find_input_csv()
    df = prepare_data(csv_path)
    plot_term_line(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization (plot + OLS fit): School inundation "term-count mechanism"
Scatter only (no error bars, no connecting lines) + linear regression fit
with 95% confidence interval for the mean prediction.

Figure requirements (per your request):
  - All text in Times New Roman
  - Move annotation boxes (custom positions)
  - Do NOT show sample size (N)
  - Wider figure: figsize=(12.8, 4.8)

Input (preferred):
  E:\impact_assessment_child_order\data\supplement\school_periods\output\school_term_mechanism_FE_terms.csv

Fallbacks:
  - E:\impact_assessment_child_order\data\supplement\school_periods\school_term_mechanism_FE_terms.csv
  - Recursively search under BASE_DIR for the same filename (pick the most recently modified)

Required columns:
  sample, measure, k_term, Estimate, StdError, PValue

Output:
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    school_term_mechanism_term_scatter_ols_ci_annot.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import statsmodels.api as sm


# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 16,
    "axes.labelsize": 16,
    "axes.titlesize": 18,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 16,
})

# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")

CSV_NAME = "school_term_mechanism_FE_terms.csv"
CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "school_term_mechanism_term_scatter_ols_ci.png"

# =======================
# Plot params
# =======================
SAMPLE_COLOR = {"rural": "#d9362b", "urban": "#056839"}

X_MIN, X_MAX = 0, 18
LINE_LW = 2.4
CI_ALPHA = 0.18
POINT_SIZE = 90

TITLE = "Effect of Flooded School Terms on Years of Schooling"
XLABEL = "Number of flooded terms during schooling"
YLABEL = "Marginal effect on years of schooling"

# >>> Turn annotation ON/OFF here <<<
SHOW_ANNOT = False

# (only used if SHOW_ANNOT=True)
ANNOT_POS = {
    "rural": (0.02, 0.92, "left", "top"),
    "urban": (0.98, 0.92, "right", "top"),
}


def find_input_csv() -> Path:
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"Cannot find input CSV: {CSV_NAME}\n\n"
        "Please place it at one of the following locations:\n"
        f"  1) {CSV_PRIMARY}\n"
        f"  2) {CSV_SECONDARY}\n"
        "Or ensure it exists somewhere under:\n"
        f"  {BASE_DIR}\n"
    )


def prepare_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    need_cols = ["sample", "measure", "k_term", "Estimate", "StdError", "PValue"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}. Existing columns={list(df.columns)}")

    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("No rows found for sample in {'rural','urban'}.")

    if not (df["measure"] == "term").any():
        raise RuntimeError("No rows found with measure == 'term'.")
    df = df[df["measure"] == "term"].copy()

    for c in ["k_term", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["k_term", "Estimate"]).copy()
    df["k_term"] = df["k_term"].round().astype(int)

    df = df[(df["k_term"] >= X_MIN) & (df["k_term"] <= X_MAX)].copy()
    if df.empty:
        raise RuntimeError(f"No data after filtering k_term in [{X_MIN}, {X_MAX}].")

    return df


def format_p(p: float) -> str:
    if p is None or not np.isfinite(p):
        return "NA"
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def fit_ols_with_mean_ci(x: np.ndarray, y: np.ndarray, x_grid: np.ndarray, alpha: float = 0.05):
    X = sm.add_constant(x.astype(float))
    model = sm.OLS(y.astype(float), X, missing="drop").fit()

    Xg = sm.add_constant(x_grid.astype(float))
    pred = model.get_prediction(Xg).summary_frame(alpha=alpha)

    yhat = pred["mean"].to_numpy()
    lo = pred["mean_ci_lower"].to_numpy()
    hi = pred["mean_ci_upper"].to_numpy()
    return model, yhat, lo, hi


def plot_scatter_with_ols_ci(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    x_grid = np.linspace(X_MIN, X_MAX, 300)

    stats = {}

    for sample in ["rural", "urban"]:
        s = df[df["sample"] == sample].sort_values("k_term")
        if s.empty:
            continue

        x = s["k_term"].to_numpy()
        y = s["Estimate"].to_numpy()
        color = SAMPLE_COLOR.get(sample, "black")

        ax.scatter(
            x, y,
            s=POINT_SIZE,
            marker="o",
            edgecolor="none",
            color=color,
            alpha=0.95,
            label=sample.capitalize(),
            zorder=3
        )

        if np.unique(x).size >= 2 and np.isfinite(y).sum() >= 3:
            model, yhat, lo, hi = fit_ols_with_mean_ci(x, y, x_grid, alpha=0.05)
            ax.plot(x_grid, yhat, linewidth=LINE_LW, color=color, zorder=2)
            ax.fill_between(x_grid, lo, hi, color=color, alpha=CI_ALPHA, linewidth=0, zorder=1)

            # store for optional annotation
            stats[sample] = dict(
                b0=float(model.params[0]),
                b1=float(model.params[1]),
                r2=float(model.rsquared),
                p=float(model.pvalues[1]) if len(model.pvalues) > 1 else np.nan,
                color=color
            )

    ax.axhline(0.0, linestyle="--", linewidth=1.6, color="black", zorder=0)

    ax.set_xlim(X_MIN - 0.5, X_MAX + 0.5)
    ax.set_xticks(list(range(X_MIN, X_MAX + 1)))
    ax.set_xticklabels([str(k) for k in range(X_MIN, X_MAX + 1)])

    ax.set_xlabel(XLABEL)
    ax.set_ylabel(YLABEL)
    ax.set_title(TITLE)

    ax.legend(frameon=False, loc="lower left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # ---- optional annotations ----
    if SHOW_ANNOT:
        for sample in ["rural", "urban"]:
            if sample not in stats:
                continue
            st = stats[sample]
            b0, b1, r2, pval, color = st["b0"], st["b1"], st["r2"], st["p"], st["color"]
            sign = "+" if b1 >= 0 else "-"
            txt = (
                f"{sample.capitalize()}:\n"
                f"y = {b0:.3f} {sign} {abs(b1):.3f}·k\n"
                f"R² = {r2:.3f}\n"
                f"p(slope) = {format_p(pval)}"
            )
            x_af, y_af, ha, va = ANNOT_POS[sample]
            ax.text(
                x_af, y_af, txt,
                transform=ax.transAxes,
                ha=ha, va=va,
                color=color,
                fontsize=18,
                bbox=dict(boxstyle="round,pad=0.30", facecolor="white", edgecolor="none", alpha=0.80),
                zorder=10
            )

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.close(fig)
    print(f"[DONE] {OUT_PNG}")


def main():
    csv_path = find_input_csv()
    print(f"[INFO] Input CSV: {csv_path}")
    df = prepare_data(csv_path)
    plot_scatter_with_ols_ci(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot only (no regression): Month-by-month education-loss coefficient curves
-----------------------------------------------------------------------
Primary input (preferred):
  E:\impact_assessment_child_order\data\supplement\school_periods\output\school_month_mechanism_FE_monthly.csv

Fallbacks:
  - E:\impact_assessment_child_order\data\supplement\school_periods\school_month_mechanism_FE_monthly.csv
  - Recursively search under BASE_DIR for the same filename (pick the most recently modified)

Outputs:
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    school_month_mechanism_monthly_line_rural.png
    school_month_mechanism_monthly_line_urban.png

Notes:
  - 95% CI is computed as Estimate ± 1.96 * StdError
  - Significance marker: "*" if p < 0.1 (one-star rule)
  - Font: Times New Roman
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
})


# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")

CSV_NAME = "school_month_mechanism_FE_monthly.csv"
CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sig_label_one_star(p: float) -> str:
    """Return '*' if p < 0.1, else empty string."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    return "*" if p < 0.1 else ""


def find_input_csv() -> Path:
    # 1) Preferred location
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY

    # 2) Secondary location
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    # 3) Recursive search under BASE_DIR
    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"Cannot find input CSV: {CSV_NAME}\n\n"
        "Please place it at one of the following locations:\n"
        f"  1) {CSV_PRIMARY}\n"
        f"  2) {CSV_SECONDARY}\n"
        "Or ensure it exists somewhere under:\n"
        f"  {BASE_DIR}\n"
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to:
      - sample, month, Estimate, StdError, (optional) PValue
    Compatible with case/space/dot variants.
    """
    rename = {}
    for c in df.columns:
        lc = str(c).lower().replace(" ", "").replace(".", "")
        if lc == "estimate":
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p"]:
            rename[c] = "PValue"
        elif lc == "term":
            rename[c] = "Term"

    df = df.rename(columns=rename)

    required = {"sample", "month", "Estimate", "StdError"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}. Existing columns={list(df.columns)}")

    if "PValue" not in df.columns:
        df["PValue"] = np.nan

    # Force numeric types
    for c in ["month", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Month should be integer-like for plotting; keep NaN as-is
    df["month_int"] = df["month"].round().astype("Int64")

    return df


def plot_month_line(df: pd.DataFrame, sample: str) -> None:
    out = OUT_DIR / f"school_month_mechanism_monthly_line_{sample}.png"

    sub = df[df["sample"].astype(str).str.lower() == sample.lower()].copy()
    sub = sub.dropna(subset=["month_int", "Estimate", "StdError"]).sort_values("month_int")

    if sub.empty:
        print(f"[WARN] No data to plot for sample='{sample}'.")
        return

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(sig_label_one_star)

    x = sub["month_int"].astype(int).to_numpy()
    y = sub["Estimate"].to_numpy()
    yerr = (z * sub["StdError"]).to_numpy()

    fig, ax = plt.subplots(figsize=(7.2, 4.6))

    ax.errorbar(
        x, y,
        yerr=yerr,
        marker="o",
        linestyle="-",
        capsize=3,
        linewidth=1.4,
        markersize=5,
    )

    ax.axhline(0.0, linestyle="--", linewidth=1.0)

    ax.set_xticks(range(1, 13))
    ax.set_xlim(0.5, 12.5)

    ax.set_xlabel("Month")
    ax.set_ylabel("Marginal effect on years of schooling")
    ax.set_title(f"{sample.capitalize()}")

    # Place significance stars above the upper CI
    y_range = np.nanmax(np.abs(np.r_[sub["CI_low"].to_numpy(), sub["CI_high"].to_numpy()]))
    if not np.isfinite(y_range) or y_range == 0:
        y_range = 1.0
    dy = 0.01 * y_range

    for xi, yi, ei, sig in zip(x, y, yerr, sub["sig"].to_numpy()):
        if sig:
            ax.text(xi, yi + ei + dy, sig, ha="center", va="bottom", fontsize=10)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.show()
    print(f"[DONE] {out}")


def main() -> None:
    csv_path = find_input_csv()
    print(f"[INFO] Input CSV: {csv_path}")

    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    plot_month_line(df, "rural")
    plot_month_line(df, "urban")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot only (no regression): Month-by-month education-loss coefficients (Radar chart)
----------------------------------------------------------------------------------
Primary input (preferred):
  E:\impact_assessment_child_order\data\supplement\school_periods\output\school_month_mechanism_FE_monthly.csv

Fallbacks:
  - E:\impact_assessment_child_order\data\supplement\school_periods\school_month_mechanism_FE_monthly.csv
  - Recursively search under BASE_DIR for the same filename (pick the most recently modified)

Outputs:
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    school_month_mechanism_monthly_radar_rural.png
    school_month_mechanism_monthly_radar_urban.png

Notes:
  - 95% CI = Estimate ± 1.96 * StdError (shown as a shaded band)
  - Significance marker: "*" if p < 0.1
  - Radar chart uses an internal positive-radius shift (offset) to handle negative coefficients,
    while radial tick labels are shown in the original (unshifted) scale.
  - Font: Times New Roman
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
})


# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")

CSV_NAME = "school_month_mechanism_FE_monthly.csv"
CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def sig_label_one_star(p: float) -> str:
    """Return '*' if p < 0.1, else empty string."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    return "*" if p < 0.1 else ""


def find_input_csv() -> Path:
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"Cannot find input CSV: {CSV_NAME}\n\n"
        "Please place it at one of the following locations:\n"
        f"  1) {CSV_PRIMARY}\n"
        f"  2) {CSV_SECONDARY}\n"
        "Or ensure it exists somewhere under:\n"
        f"  {BASE_DIR}\n"
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        lc = str(c).lower().replace(" ", "").replace(".", "")
        if lc == "estimate":
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p"]:
            rename[c] = "PValue"
    df = df.rename(columns=rename)

    required = {"sample", "month", "Estimate", "StdError"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}. Existing columns={list(df.columns)}")

    if "PValue" not in df.columns:
        df["PValue"] = np.nan

    for c in ["month", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["month_int"] = df["month"].round().astype("Int64")
    return df


def _nice_ticks(vmin: float, vmax: float, n: int = 5):
    """Create nice-ish linear ticks in original scale."""
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        return np.array([vmin, vmin + 1.0])
    ticks = np.linspace(vmin, vmax, n)
    # round to 2 decimals for readability
    return np.unique(np.round(ticks, 2))


def plot_month_radar(df: pd.DataFrame, sample: str) -> None:
    out = OUT_DIR / f"school_month_mechanism_monthly_radar_{sample}.png"

    sub = df[df["sample"].astype(str).str.lower() == sample.lower()].copy()
    sub = sub.dropna(subset=["month_int", "Estimate", "StdError"]).sort_values("month_int")

    if sub.empty:
        print(f"[WARN] No data to plot for sample='{sample}'.")
        return

    # Ensure we have months 1..12 (if missing months exist, radar will still draw existing points)
    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(sig_label_one_star)

    # angles for 12 months
    N = 12
    theta = np.linspace(0, 2 * np.pi, N, endpoint=False)

    # Map month->index 0..11
    month_idx = (sub["month_int"].astype(int).to_numpy() - 1)
    est = np.full(N, np.nan, dtype=float)
    lo  = np.full(N, np.nan, dtype=float)
    hi  = np.full(N, np.nan, dtype=float)
    sig = np.array([""] * N, dtype=object)

    est[month_idx] = sub["Estimate"].to_numpy()
    lo[month_idx]  = sub["CI_low"].to_numpy()
    hi[month_idx]  = sub["CI_high"].to_numpy()
    sig[month_idx] = sub["sig"].to_numpy()

    # Handle negative values in polar by shifting radii upward
    vmin = np.nanmin(lo)
    vmax = np.nanmax(hi)
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        print(f"[WARN] sample='{sample}' has invalid CI bounds.")
        return

    margin = 0.05 * (vmax - vmin) if vmax > vmin else 0.1
    offset = (-vmin + margin) if vmin < 0 else margin

    est_r = est + offset
    lo_r  = lo + offset
    hi_r  = hi + offset

    # Close the polygon
    theta_c = np.r_[theta, theta[0]]
    est_c   = np.r_[est_r, est_r[0]]
    lo_c    = np.r_[lo_r,  lo_r[0]]
    hi_c    = np.r_[hi_r,  hi_r[0]]

    fig = plt.figure(figsize=(6.6, 6.6))
    ax = plt.subplot(111, polar=True)

    # Put Jan at the top, clockwise
    ax.set_theta_offset(np.pi / 2.0)
    ax.set_theta_direction(-1)

    # X (angle) ticks
    ax.set_xticks(theta)
    ax.set_xticklabels(MONTH_LABELS)

    # CI band (shaded)
    # Build a single polygon: hi forward + lo backward
    band_theta = np.r_[theta_c, theta_c[::-1]]
    band_r = np.r_[hi_c, lo_c[::-1]]
    ax.fill(band_theta, band_r, alpha=0.18, linewidth=0)

    # Main line + markers
    ax.plot(theta_c, est_c, linewidth=1.6, marker="o", markersize=5)

    # "Zero" reference circle (in shifted scale)
    ax.plot(theta_c, np.full_like(theta_c, offset), linestyle="--", linewidth=1.0)

    # Radial ticks shown in original (unshifted) scale
    ticks_orig = _nice_ticks(vmin, vmax, n=5)
    ticks_r = ticks_orig + offset
    ax.set_yticks(ticks_r)
    ax.set_yticklabels([f"{t:.2f}" for t in ticks_orig])

    # Reasonable r-limits
    rmin = max(0.0, (vmin - 0.10 * (vmax - vmin)) + offset)
    rmax = (vmax + 0.10 * (vmax - vmin)) + offset
    ax.set_rlim(rmin, rmax)

    # Title
    ax.set_title(f"Month-by-month effect (Years of schooling) — {sample.capitalize()}", pad=18)

    # Significance stars (outside the upper CI)
    pad = 0.03 * (rmax - rmin)
    for i in range(N):
        if sig[i] == "*" and np.isfinite(hi_r[i]):
            ax.text(theta[i], hi_r[i] + pad, "*", ha="center", va="center", fontsize=12)

    plt.tight_layout()
    plt.savefig(out, dpi=300)
    plt.show()
    print(f"[DONE] {out}")


def main() -> None:
    csv_path = find_input_csv()
    print(f"[INFO] Input CSV: {csv_path}")

    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    plot_month_radar(df, "rural")
    plot_month_radar(df, "urban")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot only (no regression): Month-by-month education-loss coefficients
BAR + ERROR BARS | 1 row × 2 columns (Rural vs Urban) | Unified y-axis
Month order: 2..12 then 1 (i.e., Feb first, Jan last)
---------------------------------------------------------------------
Primary input (preferred):
  E:\impact_assessment_child_order\data\supplement\school_periods\output\school_month_mechanism_FE_monthly.csv

Fallbacks:
  - E:\impact_assessment_child_order\data\supplement\school_periods\school_month_mechanism_FE_monthly.csv
  - Recursively search under BASE_DIR for the same filename (pick the most recently modified)

Output (single combined figure):
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    school_month_mechanism_monthly_bar_rural_urban.png

Color rule:
  - mean > 0  : #f5d0be
  - mean <= 0 : #bed3e2

Error bars:
  - default: 95% CI = 1.96 * StdError (set Z=1.0 for ±1σ)

Significance stars (optional):
  - p < 0.10 : *
  - p < 0.05 : **
  - p < 0.01 : ***

Error bar color:
  - same as bar color (per month)

Font:
  - Times New Roman
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 20,
    "axes.labelsize": 16,
    "axes.titlesize": 16,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
})

# =======================
# User params
# =======================
POS_COLOR = "#f5d0be"
NEG_COLOR = "#bed3e2"

Z = 1.96                 # 95% CI; set to 1.0 for ±1σ
SHOW_SIG_STAR = False
STAR_FONTSIZE = 12

BAR_WIDTH = 0.5
ERROR_LW = 1.2
CAPSIZE = 4
CAPTHICK = 1.2

# Month order: Feb..Dec, then Jan
MONTH_ORDER = list(range(2, 13)) + [1]  # [2,3,...,12,1]
X_POS = np.arange(1, 13)                # fixed plotting positions 1..12
X_LABELS = [str(m) for m in MONTH_ORDER]

# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")

CSV_NAME = "school_month_mechanism_FE_monthly.csv"
CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FIG = OUT_DIR / "school_month_mechanism_monthly_bar_rural_urban.png"


def sig_label_stars(p: float) -> str:
    """Significance stars: p<0.1 '*', p<0.05 '**', p<0.01 '***'."""
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def find_input_csv() -> Path:
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"Cannot find input CSV: {CSV_NAME}\n\n"
        "Please place it at one of the following locations:\n"
        f"  1) {CSV_PRIMARY}\n"
        f"  2) {CSV_SECONDARY}\n"
        "Or ensure it exists somewhere under:\n"
        f"  {BASE_DIR}\n"
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        lc = str(c).lower().replace(" ", "").replace(".", "")
        if lc == "estimate":
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p"]:
            rename[c] = "PValue"
    df = df.rename(columns=rename)

    required = {"sample", "month", "Estimate", "StdError"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}. Existing columns={list(df.columns)}")

    if "PValue" not in df.columns:
        df["PValue"] = np.nan

    for c in ["month", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["month_int"] = df["month"].round().astype("Int64")
    return df


def build_month_frame(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    sub = df[df["sample"].astype(str).str.lower() == sample.lower()].copy()
    sub = sub.dropna(subset=["month_int", "Estimate", "StdError"]).sort_values("month_int")

    # Start from a complete 1..12 frame, then reorder to MONTH_ORDER
    months = np.arange(1, 13)
    tmp = pd.DataFrame({"month_int": months}).merge(
        sub[["month_int", "Estimate", "StdError", "PValue"]],
        on="month_int",
        how="left"
    )

    # Reorder rows: 2..12 then 1
    tmp = tmp.set_index("month_int").reindex(MONTH_ORDER).reset_index()

    tmp["yerr"] = Z * tmp["StdError"]
    tmp["color"] = np.where(tmp["Estimate"] > 0, POS_COLOR, NEG_COLOR)
    tmp["sig"] = tmp["PValue"].apply(sig_label_stars)

    return tmp


def compute_global_ylim(frames: list[pd.DataFrame]) -> tuple[float, float]:
    vals = []
    for t in frames:
        est = t["Estimate"].to_numpy(dtype=float)
        yerr = t["yerr"].to_numpy(dtype=float)
        finite = np.isfinite(est) & np.isfinite(yerr)
        if np.any(finite):
            vals.append(est[finite] - yerr[finite])
            vals.append(est[finite] + yerr[finite])

    if not vals:
        return (-1.0, 1.0)

    allv = np.concatenate(vals)
    vmin = float(np.nanmin(allv))
    vmax = float(np.nanmax(allv))

    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        return (vmin - 1.0, vmax + 1.0)

    pad = 0.08 * (vmax - vmin)
    return (vmin - pad, vmax + pad)


def draw_panel(ax, tmp: pd.DataFrame, title: str, ylim: tuple[float, float], show_ylabel: bool):
    # tmp is already in MONTH_ORDER; we plot it at fixed X_POS=1..12
    est = tmp["Estimate"].to_numpy(dtype=float)
    yerr = tmp["yerr"].to_numpy(dtype=float)
    colors = tmp["color"].to_numpy()
    sigs = tmp["sig"].to_numpy()

    heights = np.nan_to_num(est, nan=0.0)
    alphas = np.where(np.isfinite(est), 1.0, 0.0)

    bars = ax.bar(
        X_POS,
        heights,
        width=BAR_WIDTH,
        color=colors,
        linewidth=0.0,
        zorder=2
    )
    for b, a in zip(bars, alphas):
        b.set_alpha(float(a))

    # per-month errorbars, same color as bar
    for x, y, e in zip(X_POS, est, yerr):
        if not (np.isfinite(y) and np.isfinite(e)):
            continue
        col = POS_COLOR if y > 0 else NEG_COLOR
        ax.errorbar(
            [x], [y],
            yerr=[e],
            fmt="none",
            ecolor=col,
            elinewidth=ERROR_LW,
            capsize=CAPSIZE,
            capthick=CAPTHICK,
            zorder=3
        )

    ax.axhline(0.0, color="grey", linewidth=1.0, zorder=1)

    ax.set_xlim(0.4, 12.6)
    ax.set_xticks(X_POS)
    ax.set_xticklabels(X_LABELS)
    ax.set_xlabel("Month")
    ax.set_title(title)

    if show_ylabel:
        ax.set_ylabel("Marginal effect on years of schooling")
    else:
        ax.set_ylabel("")

    ax.set_ylim(*ylim)

    # significance stars (optional)
    if SHOW_SIG_STAR:
        finite = np.isfinite(est) & np.isfinite(yerr)
        yr = np.nanmax(np.abs(np.r_[est[finite] - yerr[finite], est[finite] + yerr[finite]])) if np.any(finite) else 1.0
        if not np.isfinite(yr) or yr <= 0:
            yr = 1.0
        dy = 0.02 * yr

        for x, y, e, s in zip(X_POS, est, yerr, sigs):
            if s and np.isfinite(y) and np.isfinite(e):
                ax.text(x, y + e + dy, s, ha="center", va="bottom", fontsize=STAR_FONTSIZE)

    # cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    csv_path = find_input_csv()
    print(f"[INFO] Input CSV: {csv_path}")

    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    tmp_rural = build_month_frame(df, "rural")
    tmp_urban = build_month_frame(df, "urban")

    ylim = compute_global_ylim([tmp_rural, tmp_urban])

    fig, axes = plt.subplots(
        1, 2,
        figsize=(12.8, 4.8),
        sharey=True
    )

    draw_panel(axes[0], tmp_rural, "Rural", ylim, show_ylabel=True)
    draw_panel(axes[1], tmp_urban, "Urban", ylim, show_ylabel=False)

    plt.tight_layout()
    plt.savefig(OUT_FIG, dpi=300)
    plt.close(fig)

    print(f"[DONE] {OUT_FIG}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Legend-only figure: Positive vs Negative effects (bar colors)

Outputs:
  E:\impact_assessment_child_order\data\supplement\school_periods\figures\
    legend_school_month_pos_neg.png
    legend_school_month_pos_neg.svg
"""

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# =======================
# Style
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 14,
    "legend.fontsize": 14,
})


# =======================
# Colors (match main figure)
# =======================
POS_COLOR = "#f5d0be"  # mean > 0
NEG_COLOR = "#bed3e2"  # mean <= 0


# =======================
# Paths (Windows)
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")
OUT_DIR = BASE_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "legend_school_month_pos_neg.png"
OUT_SVG = OUT_DIR / "legend_school_month_pos_neg.svg"


def main():
    handles = [
        Patch(facecolor=POS_COLOR, edgecolor="none", label="Positive effect (Estimate > 0)"),
        Patch(facecolor=NEG_COLOR, edgecolor="none", label="Negative effect (Estimate \u2264 0)"),
    ]

    # Legend-only canvas
    fig = plt.figure(figsize=(6.4, 1.2))
    ax = fig.add_subplot(111)
    ax.axis("off")

    ax.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        handlelength=1.8,
        handleheight=1.0,
        columnspacing=1.6,
        borderaxespad=0.0,
    )

    plt.tight_layout(pad=0.2)
    fig.savefig(OUT_PNG, dpi=300, transparent=True)
    fig.savefig(OUT_SVG, transparent=True)
    plt.close(fig)

    print(f"[DONE] {OUT_PNG}")
    print(f"[DONE] {OUT_SVG}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =======================
# Original notebook comment normalized for the public code archive.
# =======================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_periods")
CSV_NAME = "school_term_mechanism_FE_terms.csv"

CSV_PRIMARY = BASE_DIR / "output" / CSV_NAME
CSV_SECONDARY = BASE_DIR / CSV_NAME

X_MIN, X_MAX = 0, 18


def find_input_csv() -> Path:
    if CSV_PRIMARY.exists():
        return CSV_PRIMARY
    if CSV_SECONDARY.exists():
        return CSV_SECONDARY

    hits = list(BASE_DIR.rglob(CSV_NAME))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    raise FileNotFoundError(
        f"找不到文件: {CSV_NAME}\n"
        f"尝试过:\n  {CSV_PRIMARY}\n  {CSV_SECONDARY}"
    )


def prepare_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    need_cols = ["sample", "measure", "k_term", "Estimate", "StdError", "PValue"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"缺少列: {missing}\n现有列: {list(df.columns)}")

    # Original notebook comment normalized for the public code archive.
    df = df[df["sample"].isin(["rural", "urban"])].copy()
    df = df[df["measure"] == "term"].copy()

    for c in ["k_term", "Estimate", "StdError", "PValue"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["k_term", "Estimate"]).copy()
    df["k_term"] = df["k_term"].round().astype(int)
    df = df[(df["k_term"] >= X_MIN) & (df["k_term"] <= X_MAX)].copy()

    if df.empty:
        raise RuntimeError("筛选后没有数据。")

    return df


def print_r2_and_raw_data(df: pd.DataFrame):
    for sample in ["rural", "urban"]:
        s = df[df["sample"] == sample].sort_values("k_term").copy()

        print("\n" + "=" * 80)
        print(f"SAMPLE: {sample.upper()}")
        print("=" * 80)

        print("[INFO] Notebook progress message.")
        print(
            s[["k_term", "Estimate", "StdError", "PValue"]]
            .to_string(index=False)
        )

        if len(s) < 3 or s["k_term"].nunique() < 2:
            print("[INFO] Notebook progress message.")
            continue

        x = s["k_term"].astype(float).to_numpy()
        y = s["Estimate"].astype(float).to_numpy()

        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()

        b0 = float(model.params[0])
        b1 = float(model.params[1])
        r2 = float(model.rsquared)
        p_slope = float(model.pvalues[1])

        # Original notebook comment normalized for the public code archive.
        yhat = model.predict(X)
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2_manual = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

        sign = "+" if b1 >= 0 else "-"

        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        print(f"R² (statsmodels) = {r2:.6f}")
        print(f"R² (manual check) = {r2_manual:.6f}")
        print(f"p-value of slope = {p_slope:.6f}")
        print(f"N = {len(s)}")

        print("[INFO] Notebook progress message.")
        check_df = pd.DataFrame({
            "k_term": x,
            "Estimate_actual": y,
            "Estimate_fitted": yhat,
            "residual": y - yhat
        })
        print(check_df.to_string(index=False))


def main():
    csv_path = find_input_csv()
    print("[INFO] Notebook progress message.")

    df = prepare_data(csv_path)
    print_r2_and_raw_data(df)


if __name__ == "__main__":
    main()
