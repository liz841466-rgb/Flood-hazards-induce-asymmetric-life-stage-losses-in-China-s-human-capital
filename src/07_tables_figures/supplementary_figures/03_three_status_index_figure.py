#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_three_status_index_figure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors

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
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR = OUT_DIR / "fig_health_3dims"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Config
# =======================
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}

SAMPLE = "all"  # all / rural / urban
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

SAVE_FIG = True  # set False if you only want plt.show()

# -----------------------
# Diverging colormap with fixed center color at 0
#   - #f5f5f5 is exactly 0
#   - below: negative (brown)
#   - above: positive (teal/green)
# -----------------------
DIVERGE_COLORS = [
    "#8c510a",
    "#d8b365",
    "#f6e8c3",
    "#f5f5f5",  # 0
    "#c7eae5",
    "#5ab4ac",
    "#01665e",
]
CMAP_DIVERGE = mcolors.LinearSegmentedColormap.from_list(
    "custom_diverge_center0", DIVERGE_COLORS, N=256
)


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def load_fe_csv(y_var: str) -> pd.DataFrame:
    res_csv = OUT_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not res_csv.exists():
        raise FileNotFoundError(f"File not found: {res_csv}")

    df = pd.read_csv(res_csv)

    # Filter sample
    df = df[(df["Y_var"] == y_var) & (df["sample"] == SAMPLE)].copy()

    # Type conversion
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            # If p-values are missing, fill with NaN so code still runs (no stars)
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate", "Std. Error"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    # Keep only target T and windows
    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df


def plot_line_and_heatmap(df: pd.DataFrame, y_var: str):
    yname = Y_LABEL.get(y_var, y_var)

    # =======================
    # Figure 1: Lines by window
    # =======================
    plt.figure(figsize=(6.4, 4.2))

    for w in WINDOW_LIST:
        sub = df[df["window"] == w].sort_values("T")
        if sub.empty:
            continue

        T = sub["T"].to_numpy()
        b = sub["Estimate"].to_numpy()
        se = sub["Std. Error"].to_numpy()

        plt.errorbar(
            T, b, yerr=1.96 * se,
            fmt="o-", capsize=3,
            label=f"Window = {w}y"
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xscale("log")
    plt.xticks(T_LIST, [str(t) for t in T_LIST])
    plt.gca().xaxis.set_minor_formatter(mticker.NullFormatter())

    plt.xlabel("Return period, T (years)")
    plt.ylabel("Coefficient estimate, β")
    plt.title(f"{yname}: β(T) across windows (sample = {SAMPLE})")
    plt.legend(frameon=False)
    plt.tight_layout()

    if SAVE_FIG:
        out_png = FIG_DIR / f"line_{y_var}_sample_{SAMPLE}.png"
        plt.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()

    # =======================
    # Figure 2: Heatmap (window × T)
    # =======================
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )

    vals = mat.to_numpy(dtype=float)

    # Symmetric range around 0 so the center color maps exactly to 0
    max_abs = np.nanmax(np.abs(vals))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

    plt.figure(figsize=(6.4, 4.2))
    im = plt.imshow(vals, aspect="auto", cmap=CMAP_DIVERGE, norm=norm)
    plt.colorbar(im, label="Estimate")

    plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
    plt.yticks(range(len(mat.index)), [str(w) for w in mat.index])

    plt.xlabel("T (years)")
    plt.ylabel("Window (years)")
    plt.title(f"{yname}: coefficient heatmap (sample = {SAMPLE})")

    # Significance stars
    for i, w in enumerate(mat.index):
        for j, t in enumerate(mat.columns):
            p = pmat.loc[w, t] if (w in pmat.index and t in pmat.columns) else np.nan
            st = stars(p)
            if st:
                plt.text(j, i, st, ha="center", va="center", fontsize=11)

    plt.tight_layout()

    if SAVE_FIG:
        out_png = FIG_DIR / f"heatmap_{y_var}_sample_{SAMPLE}.png"
        plt.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()


def main():
    print(f"[INFO] Input directory: {OUT_DIR}")
    print(f"[INFO] Figure output directory: {FIG_DIR} (SAVE_FIG={SAVE_FIG})")

    for y_var in Y_VARS:
        try:
            df = load_fe_csv(y_var)
            if df.empty:
                print(f"[WARN] No usable rows for {y_var} under sample={SAMPLE}. Skipped.")
                continue
            plot_line_and_heatmap(df, y_var)
        except Exception as e:
            print(f"[ERROR] {y_var}: {e}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

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
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR = DATA_DIR / "fig_health_3dims_heatmap_rural_urban"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Config
# =======================
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}

SAMPLES = ["rural", "urban"]  # only plot these two
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

SAVE_FIG = True

# =======================
# Diverging colormap: #f5f5f5 is exactly 0
#   - below 0: brown
#   - above 0: teal/green
# =======================
DIVERGE_COLORS = [
    "#d73027",
    "#fc8d59",
    "#fee090",
    "#f5f5f5",  # 0
    "#e0f3f8",
    "#91bfdb",
    "#4575b4",
]
CMAP_DIVERGE = mcolors.LinearSegmentedColormap.from_list(
    "custom_diverge_center0", DIVERGE_COLORS, N=256
)


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def load_fe_csv(y_var: str, sample: str) -> pd.DataFrame:
    fp = DATA_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    df = pd.read_csv(fp)

    df = df[(df["Y_var"] == y_var) & (df["sample"] == sample)].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate", "Std. Error"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df


def build_matrices(df: pd.DataFrame):
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    return mat, pmat


def compute_shared_max_abs(y_var: str) -> float:
    # Share the same color scale across rural/urban for the same y_var
    vals_all = []
    for s in SAMPLES:
        df = load_fe_csv(y_var, s)
        if df.empty:
            continue
        mat, _ = build_matrices(df)
        vals_all.append(mat.to_numpy(dtype=float))

    if not vals_all:
        return 1.0

    arr = np.concatenate([v.reshape(-1) for v in vals_all])
    max_abs = np.nanmax(np.abs(arr))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    return float(max_abs)


def plot_heatmap_only(df: pd.DataFrame, y_var: str, sample: str, max_abs: float):
    yname = Y_LABEL.get(y_var, y_var)
    sname = SAMPLE_LABEL.get(sample, sample)

    mat, pmat = build_matrices(df)
    vals = mat.to_numpy(dtype=float)

    norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

    plt.figure(figsize=(6.4, 4.2))
    im = plt.imshow(vals, aspect="auto", cmap=CMAP_DIVERGE, norm=norm)
    plt.colorbar(im, label="Estimate")

    plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
    plt.yticks(range(len(mat.index)), [str(w) for w in mat.index])

    plt.xlabel("T (years)")
    plt.ylabel("Window (years)")
    plt.title(f"{yname}: coefficient heatmap ({sname})")

    # Significance stars
    for i, w in enumerate(mat.index):
        for j, t in enumerate(mat.columns):
            p = pmat.loc[w, t] if (w in pmat.index and t in pmat.columns) else np.nan
            st = stars(p)
            if st:
                plt.text(j, i, st, ha="center", va="center", fontsize=11)

    plt.tight_layout()

    if SAVE_FIG:
        out_png = FIG_DIR / f"heatmap_{y_var}_{sample}.png"
        plt.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()


def main():
    print(f"[INFO] Data directory: {DATA_DIR}")
    print(f"[INFO] Figure output directory: {FIG_DIR} (SAVE_FIG={SAVE_FIG})")

    for y_var in Y_VARS:
        try:
            max_abs = compute_shared_max_abs(y_var)
            print(f"[INFO] {y_var}: shared max_abs (rural+urban) = {max_abs:.6g}")

            for s in SAMPLES:
                df = load_fe_csv(y_var, s)
                if df.empty:
                    print(f"[WARN] No usable rows for {y_var} under sample={s}. Skipped.")
                    continue
                plot_heatmap_only(df, y_var, s, max_abs)

        except Exception as e:
            print(f"[ERROR] {y_var}: {e}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

# =======================
# Paths (Windows)
# =======================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR  = DATA_DIR / "fig_health_3dims_heatmap_grid_3x2"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Config
# =======================
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}

SAMPLES = ["rural", "urban"]
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

SAVE_FIG = True
DRAW_STARS = True

# =======================
# Colormaps (continuous, centered at 0)
# =======================
# PHYS_COLORS = [
#     "#d73027", "#fc8d59", "#fee090", "#f5f5f5", "#e0f3f8", "#91bfdb", "#4575b4"
# ]
# MENTAL_COLORS = [
#     "#8c510a", "#d8b365", "#f6e8c3", "#f5f5f5", "#c7eae5", "#5ab4ac", "#01665e"
# ]
# SOCIAL_COLORS = [
#     "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
# ]

PHYS_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
MENTAL_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
SOCIAL_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]

CMAPS = {
    "health_phys": mcolors.LinearSegmentedColormap.from_list("cmap_phys", PHYS_COLORS, N=256),
    "health_mental": mcolors.LinearSegmentedColormap.from_list("cmap_mental", MENTAL_COLORS, N=256),
    "health_social": mcolors.LinearSegmentedColormap.from_list("cmap_social", SOCIAL_COLORS, N=256),
}

def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""

def load_fe_csv(y_var: str, sample: str) -> pd.DataFrame:
    fp = DATA_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    df = pd.read_csv(fp)
    df = df[(df["Y_var"] == y_var) & (df["sample"] == sample)].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df

def build_matrices(df: pd.DataFrame):
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    return mat, pmat

def compute_shared_max_abs(y_var: str) -> float:
    """Within a given y_var, share the same vmin/vmax across rural+urban (for comparability)."""
    vals_all = []
    for s in SAMPLES:
        df = load_fe_csv(y_var, s)
        if df.empty:
            continue
        mat, _ = build_matrices(df)
        vals_all.append(mat.to_numpy(dtype=float).reshape(-1))
    if not vals_all:
        return 1.0
    arr = np.concatenate(vals_all)
    max_abs = np.nanmax(np.abs(arr))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    return float(max_abs)

def plot_grid_3x2():
    fig, axes = plt.subplots(
        nrows=3, ncols=2, figsize=(12.8, 10.5),
        sharex=True, sharey=True, constrained_layout=True
    )

    row_mappables = [None, None, None]

    for i, y_var in enumerate(Y_VARS):
        cmap = CMAPS[y_var]
        max_abs = compute_shared_max_abs(y_var)
        norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

        for j, sample in enumerate(SAMPLES):
            ax = axes[i, j]
            yname = Y_LABEL.get(y_var, y_var)
            sname = SAMPLE_LABEL.get(sample, sample)

            df = load_fe_csv(y_var, sample)
            if df.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
                ax.set_axis_off()
                continue

            mat, pmat = build_matrices(df)
            vals = mat.to_numpy(dtype=float)

            im = ax.imshow(vals, aspect="auto", cmap=cmap, norm=norm, origin="upper")
            row_mappables[i] = im

            ax.set_title(f"{yname} ( {sname} )")

            # Stars
            if DRAW_STARS:
                for rr, w in enumerate(mat.index):
                    for cc, t in enumerate(mat.columns):
                        p = pmat.loc[w, t]
                        st = stars(p)
                        if st:
                            ax.text(cc, rr, st, ha="center", va="center", fontsize=20)

            # Shared ticks, but only show labels on left/bottom to mimic "one x / one y"
            ax.set_xticks(range(len(T_LIST)))
            ax.set_yticks(range(len(WINDOW_LIST)))

            if i == 2:
                ax.set_xticklabels([str(t) for t in T_LIST])
            else:
                ax.set_xticklabels([])

            if j == 0:
                ax.set_yticklabels([str(w) for w in WINDOW_LIST])
            else:
                ax.set_yticklabels([])

        # One colorbar per row (shared by rural+urban)
        cbar = fig.colorbar(
            row_mappables[i],
            ax=axes[i, :].ravel().tolist(),
            shrink=0.95, pad=0.02
        )
        cbar.set_label("Estimate")

    # Global shared axis labels
    fig.supxlabel("T (years)")
    fig.supylabel("Window (years)")

    if SAVE_FIG:
        out_png = FIG_DIR / "heatmap_grid_3x2_rural_urban_rowColorbar.png"
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()

def main():
    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] FIG_DIR : {FIG_DIR}")
    plot_grid_3x2()

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

# =======================
# Paths (Windows)
# =======================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR  = DATA_DIR / "fig_health_3dims_heatmap_1col6rows_oneColorbar"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Shared axes
# =======================
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# =======================
# Panels: 1 column × 6 rows
# =======================
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}

PANELS = [
    ("health_phys", "rural"),
    ("health_phys", "urban"),
    ("health_mental", "rural"),
    ("health_mental", "urban"),
    ("health_social", "rural"),
    ("health_social", "urban"),
]

SAVE_FIG = True
DRAW_STARS = True

def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""

# =======================
# One colormap for the whole figure: Physical Health palette (continuous, centered at 0)
# =======================
DIVERGE_COLORS_PHYS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
CMAP_ONE = mcolors.LinearSegmentedColormap.from_list("cmap_phys_global", DIVERGE_COLORS_PHYS, N=256)

def load_fe_csv(y_var: str, sample: str) -> pd.DataFrame:
    fp = DATA_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    df = pd.read_csv(fp)
    df = df[(df["Y_var"] == y_var) & (df["sample"] == sample)].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df

def build_matrices(df: pd.DataFrame):
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    return mat, pmat

def compute_global_max_abs() -> float:
    """One shared scale across all 6 panels (required for one colorbar)."""
    vals_all = []
    for (y_var, sample) in PANELS:
        df = load_fe_csv(y_var, sample)
        if df.empty:
            continue
        mat, _ = build_matrices(df)
        vals_all.append(mat.to_numpy(dtype=float).reshape(-1))

    if not vals_all:
        return 1.0

    arr = np.concatenate(vals_all)
    max_abs = np.nanmax(np.abs(arr))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    return float(max_abs)

def plot_1col6rows_one_colorbar():
    max_abs = compute_global_max_abs()
    norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

    fig, axes = plt.subplots(
        nrows=len(PANELS), ncols=1,
        figsize=(7.6, 16.2),
        sharex=True, sharey=True,
        constrained_layout=True
    )

    last_im = None

    for i, (y_var, sample) in enumerate(PANELS):
        ax = axes[i]
        yname = Y_LABEL.get(y_var, y_var)
        sname = SAMPLE_LABEL.get(sample, sample)

        df = load_fe_csv(y_var, sample)
        if df.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        mat, pmat = build_matrices(df)
        vals = mat.to_numpy(dtype=float)

        im = ax.imshow(vals, aspect="auto", cmap=CMAP_ONE, norm=norm, origin="upper")
        last_im = im

        ax.set_title(f"{yname}: coefficient heatmap ({sname})")

        # y ticks always shown (shared y)
        ax.set_yticks(range(len(WINDOW_LIST)))
        ax.set_yticklabels([str(w) for w in WINDOW_LIST])

        # x ticks only show labels on bottom panel (shared x)
        ax.set_xticks(range(len(T_LIST)))
        if i == len(PANELS) - 1:
            ax.set_xticklabels([str(t) for t in T_LIST])
        else:
            ax.set_xticklabels([])

        # significance stars
        if DRAW_STARS:
            for rr, w in enumerate(mat.index):
                for cc, t in enumerate(mat.columns):
                    p = pmat.loc[w, t]
                    st = stars(p)
                    if st:
                        ax.text(cc, rr, st, ha="center", va="center", fontsize=20)

    # one global colorbar
    if last_im is not None:
        cbar = fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.98, pad=0.02)
        cbar.set_label("Estimate")

    fig.supxlabel("T (years)")
    fig.supylabel("Window (years)")

    if SAVE_FIG:
        out_png = FIG_DIR / "heatmap_1col6rows_oneColorbar_physPalette.png"
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()

def main():
    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] FIG_DIR : {FIG_DIR}")
    plot_1col6rows_one_colorbar()

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# =======================
# Global style (Times New Roman)
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

# =======================
# Paths (Windows)
# =======================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR  = DATA_DIR / "fig_health_3dims_heatmap_grid_3x2_physCmap_physRange"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Config
# =======================
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}

SAMPLES = ["rural", "urban"]
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

SAVE_FIG = True
DRAW_STARS = True

# =======================
# Use Physical Health colormap for ALL panels
# =======================
PHYS_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
CMAP_ONE = mcolors.LinearSegmentedColormap.from_list("cmap_phys_global", PHYS_COLORS, N=256)


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def load_fe_csv(y_var: str, sample: str) -> pd.DataFrame:
    fp = DATA_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    df = pd.read_csv(fp)
    df = df[(df["Y_var"] == y_var) & (df["sample"] == sample)].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df


def build_matrices(df: pd.DataFrame):
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    return mat, pmat


def compute_phys_max_abs() -> float:
    """
    Color range is determined ONLY by Physical Health (health_phys),
    pooled over rural+urban, then applied to ALL panels.
    """
    vals_all = []
    for s in SAMPLES:
        df = load_fe_csv("health_phys", s)
        if df.empty:
            continue
        mat, _ = build_matrices(df)
        vals_all.append(mat.to_numpy(dtype=float).reshape(-1))

    if not vals_all:
        return 1.0

    arr = np.concatenate(vals_all)
    max_abs = np.nanmax(np.abs(arr))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    return float(max_abs)


def plot_grid_3x2_phys_cmap_phys_range():
    # ONE shared norm for all 6 panels (based on health_phys only)
    max_abs = compute_phys_max_abs()
    norm_one = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

    fig, axes = plt.subplots(
        nrows=3, ncols=2, figsize=(12.8, 10.5),
        sharex=True, sharey=True, constrained_layout=True
    )

    last_im = None

    for i, y_var in enumerate(Y_VARS):
        for j, sample in enumerate(SAMPLES):
            ax = axes[i, j]
            yname = Y_LABEL.get(y_var, y_var)
            sname = SAMPLE_LABEL.get(sample, sample)

            df = load_fe_csv(y_var, sample)
            if df.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
                ax.set_axis_off()
                continue

            mat, pmat = build_matrices(df)
            vals = mat.to_numpy(dtype=float)

            im = ax.imshow(vals, aspect="auto", cmap=CMAP_ONE, norm=norm_one, origin="upper")
            last_im = im

            ax.set_title(f"{yname} ( {sname} )")

            # Stars
            if DRAW_STARS:
                for rr, w in enumerate(mat.index):
                    for cc, t in enumerate(mat.columns):
                        p = pmat.loc[w, t]
                        st = stars(p)
                        if st:
                            ax.text(cc, rr, st, ha="center", va="center", fontsize=20)

            # Shared ticks; show labels on left/bottom only
            ax.set_xticks(range(len(T_LIST)))
            ax.set_yticks(range(len(WINDOW_LIST)))

            if i == 2:
                ax.set_xticklabels([str(t) for t in T_LIST])
            else:
                ax.set_xticklabels([])

            if j == 0:
                ax.set_yticklabels([str(w) for w in WINDOW_LIST])
            else:
                ax.set_yticklabels([])

    # One global colorbar (Physical Health colormap + Physical Health range)
    if last_im is not None:
        cbar = fig.colorbar(
            last_im,
            ax=axes.ravel().tolist(),
            shrink=0.92,
            pad=0.02
        )
        cbar.set_label("Estimate")

    fig.supxlabel("T (years)")
    fig.supylabel("Window (years)")

    if SAVE_FIG:
        out_png = FIG_DIR / "heatmap_grid_3x2_allPhysCmap_allPhysRange_oneColorbar.png"
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()


def main():
    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] FIG_DIR : {FIG_DIR}")
    plot_grid_3x2_phys_cmap_phys_range()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# =======================
# Global style
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 16,
    "axes.labelsize": 15,
    "axes.titlesize": 15,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
})

# =======================
# Paths (Windows)
# =======================
DATA_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
FIG_DIR  = DATA_DIR / "fig_health_3dims_heatmap_grid_3x2_physCmap_physRange"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# =======================
# Config
# =======================
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "Physical Health",
    "health_mental": "Mental Health",
    "health_social": "Social Adaptation",
}

SAMPLES = ["rural", "urban"]
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

SAVE_FIG = True
DRAW_STARS = True

SHOW_CBAR = True   # Original notebook comment normalized for the public code archive.
CBAR_LABEL = "Estimate"

# =============================================================================
CBAR_FONTFAMILY = "Times New Roman"
CBAR_LABEL_FONTSIZE = 18
CBAR_TICK_FONTSIZE  = 16
CBAR_LABEL_FONTWEIGHT = "normal"  # Original notebook comment normalized for the public code archive.
CBAR_TICK_FONTWEIGHT  = "normal"
# ====================================

# =======================
# Use Physical Health colormap for ALL panels
# =======================
PHYS_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
CMAP_ONE = mcolors.LinearSegmentedColormap.from_list("cmap_phys_global", PHYS_COLORS, N=256)


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def load_fe_csv(y_var: str, sample: str) -> pd.DataFrame:
    fp = DATA_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")

    df = pd.read_csv(fp)
    df = df[(df["Y_var"] == y_var) & (df["sample"] == sample)].copy()

    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")

    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            if c == "Pr(>|t|)":
                df[c] = np.nan

    df = df.dropna(subset=["T", "window", "Estimate"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df


def build_matrices(df: pd.DataFrame):
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    return mat, pmat


def compute_phys_max_abs() -> float:
    """
    Color range is determined ONLY by Physical Health (health_phys),
    pooled over rural+urban, then applied to ALL panels.
    """
    vals_all = []
    for s in SAMPLES:
        df = load_fe_csv("health_phys", s)
        if df.empty:
            continue
        mat, _ = build_matrices(df)
        vals_all.append(mat.to_numpy(dtype=float).reshape(-1))

    if not vals_all:
        return 1.0

    arr = np.concatenate(vals_all)
    max_abs = np.nanmax(np.abs(arr))
    if (not np.isfinite(max_abs)) or max_abs == 0:
        max_abs = 1.0
    return float(max_abs)


def plot_grid_3x2_phys_cmap_phys_range():
    max_abs = compute_phys_max_abs()
    norm_one = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

    fig, axes = plt.subplots(
        nrows=3, ncols=2, figsize=(12.8, 10.5),
        sharex=True, sharey=True, constrained_layout=True
    )

    last_im = None

    for i, y_var in enumerate(Y_VARS):
        for j, sample in enumerate(SAMPLES):
            ax = axes[i, j]
            yname = Y_LABEL.get(y_var, y_var)
            sname = SAMPLE_LABEL.get(sample, sample)

            df = load_fe_csv(y_var, sample)
            if df.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
                ax.set_axis_off()
                continue

            mat, pmat = build_matrices(df)
            vals = mat.to_numpy(dtype=float)

            im = ax.imshow(vals, aspect="auto", cmap=CMAP_ONE, norm=norm_one, origin="upper")
            last_im = im

            # Original notebook comment normalized for the public code archive.
            ax.set_title(f"{yname} ( {sname} )")

            if DRAW_STARS:
                for rr, w in enumerate(mat.index):
                    for cc, t in enumerate(mat.columns):
                        p = pmat.loc[w, t]
                        st = stars(p)
                        if st:
                            ax.text(cc, rr, st, ha="center", va="center", fontsize=20)

            ax.set_xticks(range(len(T_LIST)))
            ax.set_yticks(range(len(WINDOW_LIST)))

            if i == 2:
                ax.set_xticklabels([str(t) for t in T_LIST])
            else:
                ax.set_xticklabels([])

            ax.set_yticklabels([str(w) for w in WINDOW_LIST])
            ax.tick_params(axis="y", labelleft=True)

    # =============================================================================
    if SHOW_CBAR and last_im is not None:
        cbar = fig.colorbar(
            last_im,
            ax=axes.ravel().tolist(),
            shrink=0.92,
            pad=0.02,
        )

        # Original notebook comment normalized for the public code archive.
        cbar.set_label(
            CBAR_LABEL,
            fontsize=CBAR_LABEL_FONTSIZE,
            fontfamily=CBAR_FONTFAMILY,
            fontweight=CBAR_LABEL_FONTWEIGHT,
        )

        # Original notebook comment normalized for the public code archive.
        cbar.ax.tick_params(labelsize=CBAR_TICK_FONTSIZE)

        # Original notebook comment normalized for the public code archive.
        for t in (cbar.ax.get_xticklabels() + cbar.ax.get_yticklabels()):
            t.set_fontfamily(CBAR_FONTFAMILY)
            t.set_fontweight(CBAR_TICK_FONTWEIGHT)

        # Original notebook comment normalized for the public code archive.
        # cbar.set_ticks([-max_abs, 0, max_abs])
    # =======================================

    fig.supxlabel("Return period T")
    fig.supylabel("Window (years)")

    if SAVE_FIG:
        out_png = FIG_DIR / "heatmap_grid_3x2_allPhysCmap_allPhysRange_oneColorbar.png"
        fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0.02)

    plt.show()


def main():
    print(f"[INFO] DATA_DIR: {DATA_DIR}")
    print(f"[INFO] FIG_DIR : {FIG_DIR}")
    plot_grid_3x2_phys_cmap_phys_range()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# =============================================================================
OUT_PNG = Path("legend_horizontal.png")
OUT_PDF = Path("legend_horizontal.pdf")  # Original notebook comment normalized for the public code archive.

# =============================================================================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# =============================================================================
PHYS_COLORS = [
    "#762a83", "#af8dc3", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#7fbf7b", "#1b7837"
]
cmap = mcolors.LinearSegmentedColormap.from_list("cmap_phys_global", PHYS_COLORS, N=256)

# =============================================================================
max_abs = 1.0
norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)

# =============================================================================
sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # Original notebook comment normalized for the public code archive.

fig = plt.figure(figsize=(7.0, 1.2), dpi=300)
cax = fig.add_axes([0.10, 0.45, 0.80, 0.25])  # [left, bottom, width, height]
cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
cbar.set_label("Estimate")

# Original notebook comment normalized for the public code archive.
# cbar.set_ticks([-max_abs, 0, max_abs])

fig.savefig(OUT_PNG, bbox_inches="tight", pad_inches=0.02)
fig.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
