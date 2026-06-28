#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_figure3_child_education.

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

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ============== 0. Global style ==============

# Use Times New Roman for all text and numbers
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Basic paths & settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Order of mechanisms (in Chinese, matching dep_label in CSV)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
    "教育培训支出（有支出家庭，元）",
    "教育负债余额（有负债家庭，元）",
]
DEP_ORDER_MAP = {lab: i for i, lab in enumerate(DEP_ORDER_ZH)}

# Mapping to English labels for display
DEP_LABEL_EN = {
    "教育培训参与率（是否有支出）":
        "Participation in education training (any spending)",
    "是否有教育负债":
        "Having education debt",
    "教育培训支出（有支出家庭，元）":
        "Education training expenditure (spending households, Yuan)",
    "教育负债余额（有负债家庭，元）":
        "Outstanding education debt (indebted households, Yuan)",
}

SAMPLE_ORDER = ["all", "rural", "urban"]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """
    Classify dependent variable as:
      - 'binary': probability/participation (0/1)
      - 'amount': monetary amounts
    """
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    # Binary outcomes (probability / participation)
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    # Amount outcomes (monetary)
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    # Default: treat as amount
    return "amount"


def get_dep_label_en(row) -> str:
    """
    Get English display label for the mechanism:
      1) Try mapping from Chinese dep_label;
      2) If not found, fall back to dep_var (usually English);
      3) As a last resort, use the original dep_label.
    """
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_EN:
        return DEP_LABEL_EN[dep_label_zh]

    if dep_var:
        return dep_var

    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # Numeric type conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep k=1 only
    df = df[df["k_window"] == 1].copy()

    # Dependent variable type (binary / amount)
    df["dep_type"] = df.apply(classify_dep_type, axis=1)

    # Order index based on Chinese labels
    df["dep_order"] = df["dep_label"].map(DEP_ORDER_MAP)

    # English display label
    df["dep_label_en"] = df.apply(get_dep_label_en, axis=1)

    return df


# ============== 3. Heatmap plotting function ==============

def plot_heatmap_by_type(df: pd.DataFrame, dep_type: str = "binary"):
    """
    Plot heatmap for a given dep_type ("binary" or "amount").

    Rows: mechanism × sample
    Columns: return period T
    Color: Estimate
    """
    sub = df[df["dep_type"] == dep_type].copy()
    if sub.empty:
        print(f"[WARN] Heatmap: dep_type={dep_type} has no results.")
        return

    sub = sub.dropna(subset=["dep_label_en", "T", "Estimate"])
    sub["T_int"] = sub["T"].astype(int)

    # Row ranking: mechanism order × sample order
    def row_rank(r):
        d = DEP_ORDER_MAP.get(r["dep_label"], 999)
        s = SAMPLE_ORDER.index(r["sample"]) if r["sample"] in SAMPLE_ORDER else 999
        return d * 10 + s

    sub["row_rank"] = sub.apply(row_rank, axis=1)

    # Row label: English mechanism [sample]
    sub["row_label"] = (
        sub["dep_label_en"].astype(str)
        + " [" + sub["sample"].astype(str) + "]"
    )

    sub = sub.sort_values(["row_rank", "row_label", "T_int"])

    mat = sub.pivot_table(
        index="row_label",
        columns="T_int",
        values="Estimate",
        aggfunc="mean",
    )

    # Ensure columns are ordered by T
    mat = mat.reindex(sorted(mat.columns), axis=1)

    # Figure size: adapt height to number of rows
    fig, ax = plt.subplots(figsize=(7, max(4, 0.35 * mat.shape[0])))

    im = ax.imshow(mat.values, aspect="auto", cmap="bwr")

    # Tick labels (Times New Roman via rcParams)
    ax.set_yticks(np.arange(mat.shape[0]))
    ax.set_yticklabels(mat.index.tolist())
    ax.set_xticks(np.arange(mat.shape[1]))
    ax.set_xticklabels(mat.columns.tolist())

    ax.set_xlabel("Return period T (years)")
    if dep_type == "binary":
        ax.set_ylabel("Mechanism × sample (binary outcomes)")
        title_type = "Binary outcomes (probabilities)"
    else:
        ax.set_ylabel("Mechanism × sample (amount outcomes)")
        title_type = "Amount outcomes (Yuan)"

    ax.set_title(f"Flood coefficient heatmap: {title_type}")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()

    # Binary outcomes
    plot_heatmap_by_type(df_all, dep_type="binary")

    # Amount outcomes
    plot_heatmap_by_type(df_all, dep_type="amount")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Chinese labels in the CSV (only two binary mechanisms here)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]

# Short English labels shown in the figure
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
}

SAMPLE_ORDER = ["all", "rural", "urban"]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose heatmap ==============

def plot_semi_rose_heatmap(df: pd.DataFrame):
    """
    Semi-circular rose heatmap for two binary mechanisms:
      Train_part, Edu_debt_any
    and three samples: all, rural, urban.
    """

    # Keep only the two binary mechanisms we care about
    df_bin = df[df["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]
    if df_bin.empty:
        print("[WARN] No binary results for Train_part / Edu_debt_any.")
        return

    # Return periods (T) and their order
    T_order = sorted(df_bin["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # All combinations shown as sectors (left -> right)
    sector_combos = [
        ("Train_part",   "all"),
        ("Train_part",   "rural"),
        ("Train_part",   "urban"),
        ("Edu_debt_any", "all"),
        ("Edu_debt_any", "rural"),
        ("Edu_debt_any", "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Discrete color palette (8 levels) ---------
    color_list = [
        "#b35806",
        "#e08214",
        "#fdb863",
        "#fee0b6",
        "#d8daeb",
        "#b2abd2",
        "#8073ac",
        "#542788",
    ]
    cmap = ListedColormap(color_list)

    # global range for Estimate, symmetric
    max_abs = np.nanmax(np.abs(df_bin["Estimate"].values))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # radial settings: leave empty center
    r_inner = 2.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians

    # Draw colored bars for each sector × T
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping

        sub = df_bin[(df_bin["dep_label_short"] == mech) &
                     (df_bin["sample"] == sample)]

        # Build value list aligned with T_order
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            ax.bar(
                theta_center,
                dr,
                width=dtheta * 0.9,
                bottom=r0,
                color=color,
                edgecolor="white",
                linewidth=0.6,
                align="center",
            )

    # ---- Decorations: labels and guides (all English) ----

    # Original notebook comment normalized for the public code archive.
    for j, T in enumerate(T_order):
        ax.text(
            0.0,
            r_inner + (j + 0.5) * dr,
            str(T),
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.text(
        0.0,
        r_inner + nT * dr + 0.6,
        "Return period T",
        ha="left",
        va="center",
        fontsize=9,
    )

    # Sample labels roughly inside the empty center
    center_r = r_inner * 0.5
    ax.text(5 * np.pi / 6, center_r, "all",
            ha="center", va="center", fontsize=11)
    ax.text(np.pi / 2,     center_r, "rural",
            ha="center", va="center", fontsize=11)
    ax.text(np.pi / 6,     center_r, "urban",
            ha="center", va="center", fontsize=11)

    # Mechanism labels above the two groups of sectors
    theta_train = np.pi - 1.5 * dtheta              # Original notebook comment normalized for the public code archive.
    theta_edu   = np.pi - (3 + 1.5) * dtheta        # Original notebook comment normalized for the public code archive.
    outer_r = r_inner + nT * dr + 0.4

    ax.text(theta_train, outer_r, "Train_part",
            ha="center", va="center", fontsize=11)
    ax.text(theta_edu,   outer_r, "Edu_debt_any",
            ha="center", va="center", fontsize=11)

    # Title
    ax.set_title("Semi-circular rose heatmap of flood coefficients", pad=20)

    # Colorbar for the discrete palette
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # required for older matplotlib versions
    cbar = plt.colorbar(sm, ax=ax, pad=0.15, boundaries=bounds)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()
    plot_semi_rose_heatmap(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Chinese labels in the CSV (only two binary mechanisms here)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]

# Short English labels shown in the figure
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
}

SAMPLE_ORDER = ["all", "rural", "urban"]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose heatmap ==============

def plot_semi_rose_heatmap(df: pd.DataFrame):
    """
    Semi-circular rose heatmap for two binary mechanisms:
      Train_part, Edu_debt_any
    and three samples: all, rural, urban.
    """

    # Keep only the two binary mechanisms we care about
    df_bin = df[df["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]
    if df_bin.empty:
        print("[WARN] No binary results for Train_part / Edu_debt_any.")
        return

    # Return periods (T) and their order
    T_order = sorted(df_bin["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Interleaved sector order (left → right)
    sector_combos = [
        ("Train_part",   "all"),
        ("Edu_debt_any", "all"),
        ("Train_part",   "rural"),
        ("Edu_debt_any", "rural"),
        ("Train_part",   "urban"),
        ("Edu_debt_any", "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Discrete color palette (8 levels) ---------
    color_list = [
        "#b35806",
        "#e08214",
        "#fdb863",
        "#fee0b6",
        "#d8daeb",
        "#b2abd2",
        "#8073ac",
        "#542788",
    ]
    cmap = ListedColormap(color_list)

    # global range for Estimate, symmetric
    max_abs = np.nanmax(np.abs(df_bin["Estimate"].values))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # radial settings: leave empty center
    r_inner = 3.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians

    theta_centers = []  # store for labels later

    # Draw colored bars for each sector × T
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        sub = df_bin[(df_bin["dep_label_short"] == mech) &
                     (df_bin["sample"] == sample)]

        # Build value list aligned with T_order
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            ax.bar(
                theta_center,
                dr,
                width=dtheta * 0.9,
                bottom=r0,
                color=color,
                edgecolor="white",
                linewidth=0.6,
                align="center",
            )

    # ---- Decorations: labels and guides (all English) ----

    # T labels along the right-hand radial line (theta = 0), with r_inner offset
    for j, T in enumerate(T_order):
        ax.text(
            0.0,
            r_inner + (j + 0.5) * dr,
            str(T),
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.text(
        0.0,
        r_inner + nT * dr + 0.6,
        "Return period T",
        ha="left",
        va="center",
        fontsize=9,
    )

    # Compute average angle per sample for center labels
    theta_centers = np.array(theta_centers)
    combo_array = np.array(sector_combos, dtype=object)

    def mean_angle(mask):
        # Original notebook comment normalized for the public code archive.
        return float(theta_centers[mask].mean())

    theta_all = mean_angle(combo_array[:, 1] == "all")
    theta_rural = mean_angle(combo_array[:, 1] == "rural")
    theta_urban = mean_angle(combo_array[:, 1] == "urban")

    center_r = r_inner * 0.5
    ax.text(theta_all,   center_r, "all",
            ha="center", va="center", fontsize=11)
    ax.text(theta_rural, center_r, "rural",
            ha="center", va="center", fontsize=11)
    ax.text(theta_urban, center_r, "urban",
            ha="center", va="center", fontsize=11)

    # Mechanism labels: average angle over the 3 sectors of each mechanism
    theta_train = mean_angle(combo_array[:, 0] == "Train_part")
    theta_edu   = mean_angle(combo_array[:, 0] == "Edu_debt_any")
    outer_r = r_inner + nT * dr + 0.4

    ax.text(theta_train, outer_r, "Train_part",
            ha="center", va="center", fontsize=11)
    ax.text(theta_edu,   outer_r, "Edu_debt_any",
            ha="center", va="center", fontsize=11)

    # Title
    ax.set_title("Semi-circular rose heatmap of flood coefficients", pad=20)

    # Colorbar for the discrete palette
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # required for some matplotlib versions
    cbar = plt.colorbar(sm, ax=ax, pad=0.15, boundaries=bounds)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()
    plot_semi_rose_heatmap(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Chinese labels in the CSV (only two binary mechanisms here)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]

# Short English labels shown in the figure
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
}

SAMPLE_ORDER = ["all", "rural", "urban"]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose heatmap ==============

def plot_semi_rose_heatmap(df: pd.DataFrame):
    """
    Semi-circular rose heatmap for two binary mechanisms:
      Train_part, Edu_debt_any
    and three samples: all, rural, urban.
    """

    # Keep only the two binary mechanisms we care about
    df_bin = df[df["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]
    if df_bin.empty:
        print("[WARN] No binary results for Train_part / Edu_debt_any.")
        return

    # Return periods (T) and their order
    T_order = sorted(df_bin["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Interleaved sector order (left → right)
    sector_combos = [
        ("Train_part",   "all"),
        ("Edu_debt_any", "all"),
        ("Train_part",   "rural"),
        ("Edu_debt_any", "rural"),
        ("Train_part",   "urban"),
        ("Edu_debt_any", "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Discrete color palette (8 levels) ---------
    color_list = [
        "#b35806",
        "#e08214",
        "#fdb863",
        "#fee0b6",
        "#d8daeb",
        "#b2abd2",
        "#8073ac",
        "#542788",
    ]
    cmap = ListedColormap(color_list)

    # global range for Estimate, symmetric
    max_abs = np.nanmax(np.abs(df_bin["Estimate"].values))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # remove outer black border and grid
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # radial settings: leave empty center
    r_inner = 2.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians

    theta_centers = []  # store for labels later

    # Draw colored bars for each sector × T
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        sub = df_bin[(df_bin["dep_label_short"] == mech) &
                     (df_bin["sample"] == sample)]

        # Build value list aligned with T_order
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        # border style: Train_part no border, Edu_debt_any with border
        if mech == "Train_part":
            edgecolor = "none"
            lw = 0.0
        else:
            edgecolor = "black"
            lw = 0.6

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            ax.bar(
                theta_center,
                dr,
                width=dtheta * 0.9,
                bottom=r0,
                color=color,
                edgecolor=edgecolor,
                linewidth=lw,
                align="center",
            )

    # ---- Decorations: labels and guides (all English) ----

    # T labels along the right-hand radial line (theta = 0), with r_inner offset
    for j, T in enumerate(T_order):
        ax.text(
            0.0,
            r_inner + (j + 0.5) * dr,
            str(T),
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.text(
        0.0,
        r_inner + nT * dr + 0.6,
        "Return period T",
        ha="left",
        va="center",
        fontsize=9,
    )

    # Compute average angle per sample for center labels
    theta_centers = np.array(theta_centers)
    combo_array = np.array(sector_combos, dtype=object)

    def mean_angle(mask):
        # Original notebook comment normalized for the public code archive.
        return float(theta_centers[mask].mean())

    theta_all = mean_angle(combo_array[:, 1] == "all")
    theta_rural = mean_angle(combo_array[:, 1] == "rural")
    theta_urban = mean_angle(combo_array[:, 1] == "urban")

    center_r = r_inner * 0.5
    ax.text(theta_all,   center_r, "all",
            ha="center", va="center", fontsize=11)
    ax.text(theta_rural, center_r, "rural",
            ha="center", va="center", fontsize=11)
    ax.text(theta_urban, center_r, "urban",
            ha="center", va="center", fontsize=11)

    # Mechanism labels: average angle over the 3 sectors of each mechanism
    theta_train = mean_angle(combo_array[:, 0] == "Train_part")
    theta_edu   = mean_angle(combo_array[:, 0] == "Edu_debt_any")
    outer_r = r_inner + nT * dr + 0.4

    ax.text(theta_train, outer_r, "Train_part",
            ha="center", va="center", fontsize=11)
    ax.text(theta_edu,   outer_r, "Edu_debt_any",
            ha="center", va="center", fontsize=11)

    # Title
    ax.set_title("Semi-circular rose heatmap of flood coefficients", pad=20)

    # Colorbar for the discrete palette
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # required for some matplotlib versions
    cbar = plt.colorbar(sm, ax=ax, pad=0.15, boundaries=bounds)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()
    plot_semi_rose_heatmap(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Chinese labels in the CSV (only two binary mechanisms here)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]

# Short English labels shown in the figure
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
}

SAMPLE_ORDER = ["all", "rural", "urban"]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose heatmap ==============

def plot_semi_rose_heatmap(df: pd.DataFrame):
    """
    Semi-circular rose heatmap for two binary mechanisms:
      Train_part, Edu_debt_any
    and three samples: all, rural, urban.
    """

    # Keep only the two binary mechanisms we care about
    df_bin = df[df["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]
    if df_bin.empty:
        print("[WARN] No binary results for Train_part / Edu_debt_any.")
        return

    # Return periods (T) and their order
    T_order = sorted(df_bin["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Interleaved sector order (left → right)
    sector_combos = [
        ("Train_part",   "all"),
        ("Edu_debt_any", "all"),
        ("Train_part",   "rural"),
        ("Edu_debt_any", "rural"),
        ("Train_part",   "urban"),
        ("Edu_debt_any", "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Discrete color palette (8 levels) ---------
    color_list = [
        "#b35806",
        "#e08214",
        "#fdb863",
        "#fee0b6",
        "#d8daeb",
        "#b2abd2",
        "#8073ac",
        "#542788",
    ]
    cmap = ListedColormap(color_list)

    # global range for Estimate, symmetric
    max_abs = np.nanmax(np.abs(df_bin["Estimate"].values))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # remove outer black border and grid
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # radial settings: leave empty center
    r_inner = 3.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians

    theta_centers = []  # store for labels and big borders later

    # ---------- 3.1 draw filled small cells (NO internal borders) ----------
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        sub = df_bin[(df_bin["dep_label_short"] == mech) &
                     (df_bin["sample"] == sample)]

        # Build value list aligned with T_order
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            # Original notebook comment normalized for the public code archive.
            ax.bar(
                theta_center,
                dr,
                width=dtheta * 0.9,
                bottom=r0,
                color=color,
                edgecolor="none",
                linewidth=0.0,
                align="center",
            )

    # ---------- 3.2 draw BIG sector borders only for Edu_debt_any ----------
    theta_centers = np.array(theta_centers)
    combo_array = np.array(sector_combos, dtype=object)

    for (theta_center, (mech, sample)) in zip(theta_centers, sector_combos):
        if mech != "Edu_debt_any":
            continue  # Train_part sectors: no outer border

        ax.bar(
            theta_center,
            nT * dr,                # full radial span
            width=dtheta * 0.9,
            bottom=r_inner,
            facecolor="none",
            edgecolor="black",
            linewidth=0.8,
            align="center",
        )

    # ---- Decorations: labels and guides (all English) ----

    # T labels along the right-hand radial line (theta = 0), with r_inner offset
    for j, T in enumerate(T_order):
        ax.text(
            0.0,
            r_inner + (j + 0.5) * dr,
            str(T),
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.text(
        0.0,
        r_inner + nT * dr + 0.6,
        "Return period T",
        ha="left",
        va="center",
        fontsize=9,
    )

    # Compute average angle per sample for center labels
    def mean_angle(mask):
        return float(theta_centers[mask].mean())

    theta_all   = mean_angle(combo_array[:, 1] == "all")
    theta_rural = mean_angle(combo_array[:, 1] == "rural")
    theta_urban = mean_angle(combo_array[:, 1] == "urban")

    center_r = r_inner * 0.5
    ax.text(theta_all,   center_r, "all",
            ha="center", va="center", fontsize=11)
    ax.text(theta_rural, center_r, "rural",
            ha="center", va="center", fontsize=11)
    ax.text(theta_urban, center_r, "urban",
            ha="center", va="center", fontsize=11)

    # Mechanism labels: average angle over the 3 sectors of each mechanism
    theta_train = mean_angle(combo_array[:, 0] == "Train_part")
    theta_edu   = mean_angle(combo_array[:, 0] == "Edu_debt_any")
    outer_r = r_inner + nT * dr + 0.4

    ax.text(theta_train, outer_r, "Train_part",
            ha="center", va="center", fontsize=11)
    ax.text(theta_edu,   outer_r, "Edu_debt_any",
            ha="center", va="center", fontsize=11)

    # Title
    ax.set_title("Semi-circular rose heatmap of flood coefficients", pad=20)

    # Colorbar for the discrete palette
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # required for some matplotlib versions
    cbar = plt.colorbar(sm, ax=ax, pad=0.15, boundaries=bounds)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()
    plot_semi_rose_heatmap(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
import math
import pandas as pd
from pathlib import Path

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLS = 16_384

def parquet_to_xlsx(in_parquet: Path, out_xlsx: Path, sheet_prefix: str = "data") -> None:
    df = pd.read_parquet(in_parquet)

    # ---- Excel columns limit ----
    if df.shape[1] > EXCEL_MAX_COLS:
        raise ValueError(
            f"Too many columns for Excel: {df.shape[1]} > {EXCEL_MAX_COLS}. "
            f"Consider exporting to multiple files or CSV."
        )

    # ---- Handle timezone-aware datetimes (Excel cannot store tz-aware datetimes) ----
    tz_cols = df.select_dtypes(include=["datetimetz"]).columns
    for c in tz_cols:
        df[c] = df[c].dt.tz_localize(None)

    # ---- Optional: convert Period dtype to string (sometimes Excel writers struggle) ----
    period_cols = [c for c in df.columns if pd.api.types.is_period_dtype(df[c])]
    for c in period_cols:
        df[c] = df[c].astype(str)

    n = len(df)
    n_sheets = max(1, math.ceil(n / EXCEL_MAX_ROWS))

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        if n_sheets == 1:
            df.to_excel(writer, sheet_name=sheet_prefix, index=False)
        else:
            for i in range(n_sheets):
                start = i * EXCEL_MAX_ROWS
                end   = min((i + 1) * EXCEL_MAX_ROWS, n)
                sheet_name = f"{sheet_prefix}_{i+1}"
                df.iloc[start:end].to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Saved: {out_xlsx} (rows={n}, cols={df.shape[1]}, sheets={n_sheets})")

if __name__ == "__main__":
    in_parquet = Path(r"E:\impact_assessment_child_order\data\figure3\children\CHFS_panel_with_flood_BM_1to5y.parquet")
    out_xlsx   = Path(r"E:\impact_assessment_child_order\data\figure3\children\CHFS_panel_with_flood_BM_1to5y.xlsx")
    parquet_to_xlsx(in_parquet, out_xlsx, sheet_prefix="CHFS")


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Chinese labels in the CSV (4 mechanisms)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",       # binary
    "是否有教育负债",                   # binary
    "教育培训支出（有支出家庭，元）",   # amount
    "教育负债余额（有负债家庭，元）",   # amount
]

# Short English labels shown in the figures
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
    "教育培训支出（有支出家庭，元）": "Train_exp",
    "教育负债余额（有负债家庭，元）": "Edu_debt_bal",
}

SAMPLE_ORDER = ["all", "rural", "urban"]

# ====== Color palettes (8 levels) ======
# Binary side palette (unchanged)
COLOR_LIST_BINARY = [
    "#b35806",
    "#e08214",
    "#fdb863",
    "#fee0b6",
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#542788",
]

# Original notebook comment normalized for the public code archive.
COLOR_LIST_AMOUNT = [
    "#1b7837",
    "#5aae61",
    "#a6dba0",
    "#d9f0d3",
    "#e7d4e8",
    "#c2a5cf",
    "#9970ab",
    "#762a83",
]



# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    # binary outcomes
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    # amount outcomes
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Generic semi-circular rose plot for two mechanisms ==============

def plot_two_mech(df_sub: pd.DataFrame,
                  mech1: str,
                  mech2: str,
                  title_main: str,
                  use_quantile_bins: bool = False):
    """
    Draw a semi-circular rose heatmap for two mechanisms (mech1, mech2)
    and three samples (all / rural / urban).

    mech1: no border
    mech2: only a big sector border, no internal borders

    use_quantile_bins:
      - False: boundaries are equally spaced between vmin and vmax.
      - True : boundaries are based on |Estimate| quantiles (25/50/75%)
               and symmetric around 0. (recommended for amount outcomes)
    """
    if df_sub.empty:
        print(f"[WARN] No data for mechanisms {mech1} / {mech2}.")
        return

    # Return periods (T)
    T_order = sorted(df_sub["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Sector order (left → right), interleaved by sample
    # sector_combos = [
    #     (mech1, "all"),
    #     (mech2, "all"),
    #     (mech1, "rural"),
    #     (mech2, "rural"),
    #     (mech1, "urban"),
    #     (mech2, "urban"),
    # ]
    sector_combos = [
        (mech1, "all"),
        (mech1, "rural"),
        (mech1, "urban"),
        (mech2, "all"),
        (mech2, "rural"),
        (mech2, "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Choose color palette ---------
    if use_quantile_bins:
        color_list = COLOR_LIST_AMOUNT  # Original notebook comment normalized for the public code archive.
    else:
        color_list = COLOR_LIST_BINARY  # Original notebook comment normalized for the public code archive.

    cmap = ListedColormap(color_list)

    # global range for Estimate
    vals_all = df_sub["Estimate"].to_numpy()
    max_abs = np.nanmax(np.abs(vals_all))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    if use_quantile_bins:
        # use quantiles of |Estimate| (non-zero) for amount outcomes
        abs_nonzero = np.abs(vals_all[np.isfinite(vals_all) & (vals_all != 0)])
        if len(abs_nonzero) >= 4:
            q1, q2, q3 = np.quantile(abs_nonzero, [0.25, 0.5, 0.75])
            # make sure quantiles are strictly increasing and >0
            eps = 1e-9
            q1 = max(q1, eps)
            q2 = max(q2, q1 + eps)
            q3 = max(q3, q2 + eps)
            bounds = np.array([-max_abs, -q3, -q2, -q1, 0.0,
                               q1, q2, q3, max_abs])
        else:
            # fallback to equal spacing if data too few
            bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    else:
        # equal spacing (for binary outcomes)
        bounds = np.linspace(vmin, vmax, len(color_list) + 1)

    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # remove outer black border and grid
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # radial settings: leave empty center
    r_inner = 3.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians
    width_factor = 0.90         # < 1 : small gap between sectors

    theta_centers = []  # store for labels and big borders later

    # ---------- 3.1 draw filled small cells (NO internal borders) ----------
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        sub = df_sub[
            (df_sub["dep_label_short"] == mech)
            & (df_sub["sample"] == sample)
        ]

        # Build value list aligned with T_order
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            ax.bar(
                theta_center,
                dr,
                width=dtheta * width_factor,
                bottom=r0,
                color=color,
                edgecolor="none",
                linewidth=0.0,
                align="center",
            )

    # ---------- 3.2 draw BIG sector borders only for mech2 ----------
    theta_centers = np.array(theta_centers)
    combo_array = np.array(sector_combos, dtype=object)

    for theta_center, (mech, sample) in zip(theta_centers, sector_combos):
        if mech != mech2:
            continue  # mech1 sectors: no outer border

        ax.bar(
            theta_center,
            nT * dr,                # full radial span
            width=dtheta * width_factor,
            bottom=r_inner,
            facecolor="none",
            edgecolor="black",
            linewidth=0.8,
            align="center",
        )

    # ---- Decorations: labels and guides (all English) ----

    # T labels along the right-hand radial line (theta = 0), with r_inner offset
    for j, T in enumerate(T_order):
        ax.text(
            0.0,
            r_inner + (j + 0.5) * dr,
            str(T),
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.text(
        0.0,
        r_inner + nT * dr + 0.6,
        "Return period T",
        ha="left",
        va="center",
        fontsize=9,
    )

    # Compute average angle per sample for center labels
    def mean_angle(mask):
        return float(theta_centers[mask].mean())

    theta_all   = mean_angle(combo_array[:, 1] == "all")
    theta_rural = mean_angle(combo_array[:, 1] == "rural")
    theta_urban = mean_angle(combo_array[:, 1] == "urban")

    center_r = r_inner * 0.5
    ax.text(theta_all,   center_r, "all",
            ha="center", va="center", fontsize=11)
    ax.text(theta_rural, center_r, "rural",
            ha="center", va="center", fontsize=11)
    ax.text(theta_urban, center_r, "urban",
            ha="center", va="center", fontsize=11)

    # Mechanism labels: average angle over the 3 sectors of each mechanism
    theta_m1 = mean_angle(combo_array[:, 0] == mech1)
    theta_m2 = mean_angle(combo_array[:, 0] == mech2)
    outer_r = r_inner + nT * dr + 0.4

    ax.text(theta_m1, outer_r, mech1,
            ha="center", va="center", fontsize=11)
    ax.text(theta_m2, outer_r, mech2,
            ha="center", va="center", fontsize=11)

    # Title
    ax.set_title(title_main, pad=20)

    # Colorbar for the discrete palette
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.15, boundaries=bounds)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()

    # ---- 4.1 Binary-side figure (probability outcomes) ----
    df_bin = df_all[df_all["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]

    plot_two_mech(
        df_sub=df_bin,
        mech1="Train_part",         # no border
        mech2="Edu_debt_any",       # big sector border
        title_main="Semi-circular rose heatmap of flood coefficients (binary outcomes)",
        use_quantile_bins=False,    # Original notebook comment normalized for the public code archive.
    )

    # ---- 4.2 Amount-side figure (amount outcomes) ----
    df_amt = df_all[df_all["dep_type"] == "amount"].copy()
    df_amt = df_amt[df_amt["dep_label_short"].isin(["Train_exp", "Edu_debt_bal"])]

    plot_two_mech(
        df_sub=df_amt,
        mech1="Train_exp",          # no border
        mech2="Edu_debt_bal",       # big sector border
        title_main="Semi-circular rose heatmap of flood coefficients (amount outcomes)",
        use_quantile_bins=True,     # Original notebook comment normalized for the public code archive.
    )


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS education investment mechanisms (k=1)
→ Semi-circular rose heatmaps for flood coefficients (no labels)

Two figures saved as SVG (300 dpi, no labels/legend/title):
  1) Binary outcomes:   Train_part & Edu_debt_any
  2) Amount outcomes:   Train_exp & Edu_debt_bal
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Chinese labels in the CSV (4 mechanisms)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",       # binary
    "是否有教育负债",                   # binary
    "教育培训支出（有支出家庭，元）",   # amount
    "教育负债余额（有负债家庭，元）",   # amount
]

# Short English labels used internally
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
    "教育培训支出（有支出家庭，元）": "Train_exp",
    "教育负债余额（有负债家庭，元）": "Edu_debt_bal",
}

SAMPLE_ORDER = ["all", "rural", "urban"]

# ====== Color palettes (8 levels) ======
# Binary side palette
COLOR_LIST_BINARY = [
    "#b35806",
    "#e08214",
    "#fdb863",
    "#fee0b6",
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#542788",
]

# Original notebook comment normalized for the public code archive.
COLOR_LIST_AMOUNT = [
    "#1b7837",
    "#5aae61",
    "#a6dba0",
    "#d9f0d3",
    "#e7d4e8",
    "#c2a5cf",
    "#9970ab",
    "#762a83",
]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    # binary outcomes
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    # amount outcomes
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose plot and save ==============

def plot_two_mech_save(df_sub: pd.DataFrame,
                       mech1: str,
                       mech2: str,
                       out_path: Path,
                       use_quantile_bins: bool = False):
    """
    Draw a semi-circular rose heatmap for two mechanisms (mech1, mech2)
    and three samples (all / rural / urban), then save to out_path.

    - No labels, no title, no colorbar.
    - Leftmost sector touches 180°, rightmost sector touches 0°.
      Middle sectors keep gaps (width_factor).
    """

    if df_sub.empty:
        print(f"[WARN] No data for mechanisms {mech1} / {mech2}.")
        return

    # Return periods (T)
    T_order = sorted(df_sub["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Sector order (left → right), grouped by mechanism:
    # mech1: all, rural, urban | mech2: all, rural, urban
    sector_combos = [
        (mech1, "all"),
        (mech1, "rural"),
        (mech1, "urban"),
        (mech2, "all"),
        (mech2, "rural"),
        (mech2, "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Choose color palette ---------
    if use_quantile_bins:
        color_list = COLOR_LIST_AMOUNT  # amount side
    else:
        color_list = COLOR_LIST_BINARY  # binary side

    cmap = ListedColormap(color_list)

    # global range for Estimate
    vals_all = df_sub["Estimate"].to_numpy()
    max_abs = np.nanmax(np.abs(vals_all))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    if use_quantile_bins:
        # quantiles of |Estimate| (non-zero) for amount outcomes
        abs_nonzero = np.abs(vals_all[np.isfinite(vals_all) & (vals_all != 0)])
        if len(abs_nonzero) >= 4:
            q1, q2, q3 = np.quantile(abs_nonzero, [0.25, 0.5, 0.75])
            eps = 1e-9
            q1 = max(q1, eps)
            q2 = max(q2, q1 + eps)
            q3 = max(q3, q2 + eps)
            bounds = np.array([-max_abs, -q3, -q2, -q1, 0.0,
                               q1, q2, q3, max_abs])
        else:
            bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    else:
        bounds = np.linspace(vmin, vmax, len(color_list) + 1)

    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # remove outer black border and grid
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # radial settings: leave empty center
    r_inner = 3.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians
    width_factor = 0.90         # middle sectors shrink to create gaps

    theta_centers = []

    # ---------- 3.1 draw filled small cells ----------
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        # outermost sectors full width; middle sectors shrunk
        if i == 0 or i == n_sectors - 1:
            bar_width = dtheta
        else:
            bar_width = dtheta * width_factor

        sub = df_sub[
            (df_sub["dep_label_short"] == mech)
            & (df_sub["sample"] == sample)
        ]

        # values by T
        values = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
            values.append(val)

        for j, (T, val) in enumerate(zip(T_order, values)):
            r0 = r_inner + j * dr

            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            ax.bar(
                theta_center,
                dr,
                width=bar_width,
                bottom=r0,
                color=color,
                edgecolor="none",
                linewidth=0.0,
                align="center",
            )

    # ---------- 3.2 big sector borders only for mech2 ----------
    theta_centers = np.array(theta_centers)

    for i, (theta_center, (mech, sample)) in enumerate(
            zip(theta_centers, sector_combos)):

        if mech != mech2:
            continue  # mech1 sectors: no outer border

        if i == 0 or i == n_sectors - 1:
            border_width = dtheta
        else:
            border_width = dtheta * width_factor

        ax.bar(
            theta_center,
            nT * dr,                # full radial span
            width=border_width,
            bottom=r_inner,
            facecolor="none",
            edgecolor="black",
            linewidth=0.8,
            align="center",
        )

    # ---- No labels / title / legend ----
    ax.set_axis_off()

    # ---- Save figure ----
    fig.savefig(out_path, dpi=300, format="svg", bbox_inches="tight")
    plt.close(fig)


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()

    # ---- 4.1 Binary-side figure (probability outcomes) ----
    df_bin = df_all[df_all["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]

    out_bin = OUT_DIR / "CHFS_mechanism_rose_binary.svg"
    plot_two_mech_save(
        df_sub=df_bin,
        mech1="Train_part",       # left block
        mech2="Edu_debt_any",     # right block (with big border)
        out_path=out_bin,
        use_quantile_bins=False,  # equal spacing + binary palette
    )

    # ---- 4.2 Amount-side figure (amount outcomes) ----
    df_amt = df_all[df_all["dep_type"] == "amount"].copy()
    df_amt = df_amt[df_amt["dep_label_short"].isin(["Train_exp", "Edu_debt_bal"])]

    out_amt = OUT_DIR / "CHFS_mechanism_rose_amount.svg"
    plot_two_mech_save(
        df_sub=df_amt,
        mech1="Train_exp",        # left block
        mech2="Edu_debt_bal",     # right block (with big border)
        out_path=out_amt,
        use_quantile_bins=True,   # quantile-based bins + amount palette
    )


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS education investment mechanisms (k=1)
→ Semi-circular rose heatmaps for flood coefficients (no labels)

Two figures saved as SVG (300 dpi, no labels/legend/title, only significance stars):
  1) Binary outcomes:   Train_part & Edu_debt_any
  2) Amount outcomes:   Train_exp & Edu_debt_bal

Significance stars:
  - p > 0.10      : no star
  - 0.05 < p ≤ 0.10 : "*"
  - 0.01 < p ≤ 0.05 : "**"
  - p ≤ 0.01      : "***"
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Global style ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ============== 1. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Chinese labels in the CSV (4 mechanisms)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",       # binary
    "是否有教育负债",                   # binary
    "教育培训支出（有支出家庭，元）",   # amount
    "教育负债余额（有负债家庭，元）",   # amount
]

# Short English labels used internally
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
    "教育培训支出（有支出家庭，元）": "Train_exp",
    "教育负债余额（有负债家庭，元）": "Edu_debt_bal",
}

SAMPLE_ORDER = ["all", "rural", "urban"]

# ====== Color palettes (8 levels) ======
# Binary side palette
COLOR_LIST_BINARY = [
    "#b35806",
    "#e08214",
    "#fdb863",
    "#fee0b6",
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#542788",
]

# Original notebook comment normalized for the public code archive.
COLOR_LIST_AMOUNT = [
    "#1b7837",
    "#5aae61",
    "#a6dba0",
    "#d9f0d3",
    "#e7d4e8",
    "#c2a5cf",
    "#9970ab",
    "#762a83",
]


# ============== 2. Load & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    # binary outcomes
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    # amount outcomes
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"


def get_dep_label_short(row) -> str:
    """Return short English mechanism label."""
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))

    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    """Read CSV, keep k=1, and add classification fields."""
    df = pd.read_csv(RES_CSV)

    # numeric conversion
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep k=1
    df = df[df["k_window"] == 1].copy()

    # classify
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)

    # integer T
    df["T_int"] = df["T"].astype("Int64")

    return df


# ============== 3. Semi-circular rose plot and save ==============

def p_to_stars(pval: float) -> str:
    """Map p-value to significance stars."""
    if not np.isfinite(pval):
        return ""
    if pval <= 0.01:
        return "***"
    elif pval <= 0.05:
        return "**"
    elif pval <= 0.10:
        return "*"
    else:
        return ""


def plot_two_mech_save(df_sub: pd.DataFrame,
                       mech1: str,
                       mech2: str,
                       out_path: Path,
                       use_quantile_bins: bool = False):
    """
    Draw a semi-circular rose heatmap for two mechanisms (mech1, mech2)
    and three samples (all / rural / urban), then save to out_path.

    - No labels, no title, no colorbar.
    - Leftmost sector touches 180°, rightmost sector touches 0°.
      Middle sectors keep gaps (width_factor).
    - Significance stars according to p_to_stars().
    """

    if df_sub.empty:
        print(f"[WARN] No data for mechanisms {mech1} / {mech2}.")
        return

    # Return periods (T)
    T_order = sorted(df_sub["T_int"].dropna().unique().tolist())
    nT = len(T_order)
    if nT == 0:
        print("[WARN] No valid T values.")
        return

    # Sector order (left → right), grouped by mechanism:
    # mech1: all, rural, urban | mech2: all, rural, urban
    sector_combos = [
        (mech1, "all"),
        (mech1, "rural"),
        (mech1, "urban"),
        (mech2, "all"),
        (mech2, "rural"),
        (mech2, "urban"),
    ]
    n_sectors = len(sector_combos)

    # --------- Choose color palette ---------
    if use_quantile_bins:
        color_list = COLOR_LIST_AMOUNT  # amount side
    else:
        color_list = COLOR_LIST_BINARY  # binary side

    cmap = ListedColormap(color_list)

    # global range for Estimate
    vals_all = df_sub["Estimate"].to_numpy()
    max_abs = np.nanmax(np.abs(vals_all))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    # boundaries for 8 bins
    if use_quantile_bins:
        # quantiles of |Estimate| (non-zero) for amount outcomes
        abs_nonzero = np.abs(vals_all[np.isfinite(vals_all) & (vals_all != 0)])
        if len(abs_nonzero) >= 4:
            q1, q2, q3 = np.quantile(abs_nonzero, [0.25, 0.5, 0.75])
            eps = 1e-9
            q1 = max(q1, eps)
            q2 = max(q2, q1 + eps)
            q3 = max(q3, q2 + eps)
            bounds = np.array([-max_abs, -q3, -q2, -q1, 0.0,
                               q1, q2, q3, max_abs])
        else:
            bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    else:
        bounds = np.linspace(vmin, vmax, len(color_list) + 1)

    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 4.5))
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_xticks([])
    ax.set_yticks([])

    # remove outer black border and grid
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    # radial settings: leave empty center
    r_inner = 3.0           # inner empty radius
    dr = 1.0                # radial thickness per T band
    ax.set_ylim(0, r_inner + nT * dr)

    dtheta = np.pi / n_sectors  # sector width in radians
    width_factor = 0.90         # middle sectors shrink to create gaps

    theta_centers = []

    # ---------- 3.1 draw filled small cells + stars ----------
    for i, (mech, sample) in enumerate(sector_combos):
        theta_center = np.pi - (i + 0.5) * dtheta  # left→right mapping
        theta_centers.append(theta_center)

        # outermost sectors full width; middle sectors shrunk
        if i == 0 or i == n_sectors - 1:
            bar_width = dtheta
        else:
            bar_width = dtheta * width_factor

        sub = df_sub[
            (df_sub["dep_label_short"] == mech)
            & (df_sub["sample"] == sample)
        ]

        # values & p-values by T
        values = []
        pvals = []
        for T in T_order:
            row = sub[sub["T_int"] == T]
            if row.empty:
                val = np.nan
                pval = np.nan
            else:
                val = float(row["Estimate"].iloc[0])
                pval = float(row["PValue"].iloc[0])
            values.append(val)
            pvals.append(pval)

        for j, (T, val, pval) in enumerate(zip(T_order, values, pvals)):
            r0 = r_inner + j * dr
            r_center = r0 + dr / 2.0

            # color
            if np.isnan(val):
                color = "lightgrey"
            else:
                idx = np.digitize(val, bounds) - 1
                idx = max(0, min(idx, len(color_list) - 1))
                color = color_list[idx]

            # bar
            ax.bar(
                theta_center,
                dr,
                width=bar_width,
                bottom=r0,
                color=color,
                edgecolor="none",
                linewidth=0.0,
                align="center",
            )

            # significance star
            stars = p_to_stars(pval)
            if stars:
                ax.text(
                    theta_center,
                    r_center,
                    stars,
                    ha="center",
                    va="center",
                    fontsize=12,
                    color="black",
                )

    # ---------- 3.2 big sector borders only for mech2 ----------
    theta_centers = np.array(theta_centers)

    for i, (theta_center, (mech, sample)) in enumerate(
            zip(theta_centers, sector_combos)):

        if mech != mech2:
            continue  # mech1 sectors: no outer border

        if i == 0 or i == n_sectors - 1:
            border_width = dtheta
        else:
            border_width = dtheta * width_factor

        ax.bar(
            theta_center,
            nT * dr,                # full radial span
            width=border_width,
            bottom=r_inner,
            facecolor="none",
            edgecolor="black",
            linewidth=0.8,
            align="center",
        )

    # ---- No axes / labels / title / legend ----
    ax.set_axis_off()

    # ---- Save figure ----
    fig.savefig(out_path, dpi=300, format="svg", bbox_inches="tight")
    plt.close(fig)


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()

    # ---- 4.1 Binary-side figure (probability outcomes) ----
    df_bin = df_all[df_all["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]

    out_bin = OUT_DIR / "CHFS_mechanism_rose_binary.svg"
    plot_two_mech_save(
        df_sub=df_bin,
        mech1="Train_part",       # left block
        mech2="Edu_debt_any",     # right block (with big border)
        out_path=out_bin,
        use_quantile_bins=False,  # equal spacing + binary palette
    )

    # ---- 4.2 Amount-side figure (amount outcomes) ----
    df_amt = df_all[df_all["dep_type"] == "amount"].copy()
    df_amt = df_amt[df_amt["dep_label_short"].isin(["Train_exp", "Edu_debt_bal"])]

    out_amt = OUT_DIR / "CHFS_mechanism_rose_amount.svg"
    plot_two_mech_save(
        df_sub=df_amt,
        mech1="Train_exp",        # left block
        mech2="Edu_debt_bal",     # right block (with big border)
        out_path=out_amt,
        use_quantile_bins=True,   # quantile-based bins + amount palette
    )


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate standalone legends (colorbars) for CHFS mechanism rose plots.

Output:
  E:\impact_assessment_child_order\data\figure3\children\CHFS\
    CHFS_legend_binary.svg
    CHFS_legend_amount.svg
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

# ============== 0. Paths & basic settings ==============

RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ====== Color palettes (8 levels) ======
COLOR_LIST_BINARY = [
    "#b35806",
    "#e08214",
    "#fdb863",
    "#fee0b6",
    "#d8daeb",
    "#b2abd2",
    "#8073ac",
    "#542788",
]

COLOR_LIST_AMOUNT = [
    "#1b7837",
    "#5aae61",
    "#a6dba0",
    "#d9f0d3",
    "#e7d4e8",
    "#c2a5cf",
    "#9970ab",
    "#762a83",
]

# ============== 1. Load & classify ==============

DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
    "教育培训支出（有支出家庭，元）": "Train_exp",
    "教育负债余额（有负债家庭，元）": "Edu_debt_bal",
}

def classify_dep_type(row) -> str:
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"
    return "amount"


def get_dep_label_short(row) -> str:
    dep_label_zh = str(row.get("dep_label", ""))
    dep_var = str(row.get("dep_var", ""))
    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    if dep_var:
        return dep_var
    return dep_label_zh


def load_results() -> pd.DataFrame:
    df = pd.read_csv(RES_CSV)

    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["k_window"] == 1].copy()
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_label_short"] = df.apply(get_dep_label_short, axis=1)
    df["T_int"] = df["T"].astype("Int64")
    return df


# ============== 2. Helper: compute bounds ==============

def compute_bounds(vals: np.ndarray,
                   color_list,
                   use_quantile_bins: bool) -> np.ndarray:
    """Return bin boundaries for the given values."""
    vals = np.asarray(vals)
    max_abs = np.nanmax(np.abs(vals))
    if not np.isfinite(max_abs) or max_abs == 0:
        max_abs = 1.0
    vmin, vmax = -max_abs, max_abs

    if use_quantile_bins:
        abs_nonzero = np.abs(vals[np.isfinite(vals) & (vals != 0)])
        if len(abs_nonzero) >= 4:
            q1, q2, q3 = np.quantile(abs_nonzero, [0.25, 0.5, 0.75])
            eps = 1e-9
            q1 = max(q1, eps)
            q2 = max(q2, q1 + eps)
            q3 = max(q3, q2 + eps)
            bounds = np.array(
                [-max_abs, -q3, -q2, -q1, 0.0, q1, q2, q3, max_abs]
            )
        else:
            bounds = np.linspace(vmin, vmax, len(color_list) + 1)
    else:
        bounds = np.linspace(vmin, vmax, len(color_list) + 1)

    return bounds


# ============== 3. Helper: draw and save colorbar ==============

def save_colorbar(bounds: np.ndarray,
                  color_list,
                  out_path: Path,
                  label: str = "Estimate"):
    """Create a vertical discrete colorbar and save as SVG (two decimals)."""
    cmap = ListedColormap(color_list)
    norm = BoundaryNorm(bounds, cmap.N)

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(figsize=(1.2, 4.5))

    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(sm, cax=ax, boundaries=bounds)
    cbar.set_label(label)

    # Original notebook comment normalized for the public code archive.
    cbar.set_ticks(bounds)
    cbar.ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))

    fig.savefig(out_path, format="svg", dpi=300, bbox_inches="tight")
    plt.close(fig)


# ============== 4. Main ==============

if __name__ == "__main__":
    df_all = load_results()

    # ---- Binary side (Train_part / Edu_debt_any) ----
    df_bin = df_all[df_all["dep_type"] == "binary"].copy()
    df_bin = df_bin[df_bin["dep_label_short"].isin(["Train_part", "Edu_debt_any"])]

    bounds_bin = compute_bounds(
        vals=df_bin["Estimate"].to_numpy(),
        color_list=COLOR_LIST_BINARY,
        use_quantile_bins=False,
    )
    out_bin = OUT_DIR / "CHFS_legend_binary.svg"
    save_colorbar(bounds_bin, COLOR_LIST_BINARY, out_bin, label="Estimate")

    # ---- Amount side (Train_exp / Edu_debt_bal) ----
    df_amt = df_all[df_all["dep_type"] == "amount"].copy()
    df_amt = df_amt[df_amt["dep_label_short"].isin(["Train_exp", "Edu_debt_bal"])]

    bounds_amt = compute_bounds(
        vals=df_amt["Estimate"].to_numpy(),
        color_list=COLOR_LIST_AMOUNT,
        use_quantile_bins=True,
    )
    out_amt = OUT_DIR / "CHFS_legend_amount.svg"
    save_colorbar(bounds_amt, COLOR_LIST_AMOUNT, out_amt, label="Estimate")


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS education investment mechanisms (k=1)
Binary outcomes for all return periods T
Dot-and-whisker + bar plots, rural / urban plotted separately.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ============== 0. Global style & basic settings ==============

# Use Times New Roman everywhere
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Result file path (Windows)
RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Return periods to consider
T_LIST = [2, 5, 10, 20, 50, 100]

# Binary mechanisms (Chinese labels from CSV)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]
DEP_ORDER_MAP = {lab: i for i, lab in enumerate(DEP_ORDER_ZH)}

# Short English labels shown in the figures
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train_part",
    "是否有教育负债": "Edu_debt_any",
}

# Sample labels (for titles)
SAMPLE_LABEL_EN = {
    "rural": "rural sample",
    "urban": "urban sample",
    "all": "full sample",
}


# ============== 1. Load results & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))
    # binary outcomes
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"
    # amount outcomes
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"
    return "amount"


def get_dep_label_short(dep_label_zh: str) -> str:
    """Map Chinese mechanism label to short English label."""
    if dep_label_zh in DEP_LABEL_SHORT:
        return DEP_LABEL_SHORT[dep_label_zh]
    return dep_label_zh  # fallback, should not be shown anyway


def load_binary_results() -> pd.DataFrame:
    """Read CSV, keep k=1 and binary outcomes only."""
    df = pd.read_csv(RES_CSV)

    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # k = 1 only
    df = df[df["k_window"] == 1].copy()

    # classify and ordering
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_order"] = df["dep_label"].map(DEP_ORDER_MAP)

    # keep binary only
    df = df[df["dep_type"] == "binary"].copy()

    return df


# ============== 2. p-value -> stars ==============

def stars_for_p(p: float) -> str:
    """
    Map p-value to significance stars:
      p < 0.01        -> "***"
      0.01 <= p < 0.05 -> "**"
      0.05 <= p < 0.10 -> "*"
      p >= 0.10       -> ""
    """
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


# ============== 3. Dot-and-whisker: one sample, all T ==============

def plot_binary_dot_whisker_allT(df: pd.DataFrame, sample: str = "rural"):
    """
    For a fixed sample (rural / urban):
      - y-axis: mechanism × T combinations
      - x-axis: flood coefficient with 95% CI
    """
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] Dot-whisker: sample={sample} has no results.")
        return

    sub["T_int"] = sub["T"].astype(int)
    sub = sub.dropna(subset=["dep_label", "Estimate"])

    # sort: mechanism then T
    sub = sub.sort_values(["dep_order", "dep_label", "T_int"])

    # build y-axis labels using short English mechanism names
    sub["mech_short"] = sub["dep_label"].apply(get_dep_label_short)
    sub["y_label"] = sub.apply(
        lambda r: f"{r['mech_short']}, T={int(r['T_int'])}", axis=1
    )

    y_labels = sub["y_label"].tolist()
    y_pos = np.arange(len(y_labels))

    est = sub["Estimate"].to_numpy(float)

    # CI / SE
    if {"CI_low", "CI_high"}.issubset(sub.columns) and sub["CI_low"].notna().any():
        ci_low = sub["CI_low"].to_numpy(float)
        ci_high = sub["CI_high"].to_numpy(float)
        xerr = np.vstack([est - ci_low, ci_high - est])
    else:
        se = sub["StdError"].to_numpy(float)
        xerr = 1.96 * se

    # range for star offset
    x_min = np.nanmin(est - (xerr[0] if xerr.ndim == 2 else xerr))
    x_max = np.nanmax(est + (xerr[1] if xerr.ndim == 2 else xerr))
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_max <= x_min:
        x_min, x_max = -0.5, 0.5
    x_range = x_max - x_min
    star_offset = 0.03 * x_range if x_range > 0 else 0.05

    fig, ax = plt.subplots(figsize=(7, max(4, 0.35 * len(y_labels))))

    ax.errorbar(
        est,
        y_pos,
        xerr=xerr,
        fmt="o",
        linestyle="none",
        capsize=4,
        color="tab:blue",
    )

    # significance stars
    for xi, yi, (_, row) in zip(est, y_pos, sub.iterrows()):
        star = stars_for_p(row["PValue"])
        if star:
            ax.text(
                xi + star_offset,
                yi,
                star,
                va="center",
                ha="left",
                fontsize=9,
            )

    ax.axvline(0, linestyle="--", linewidth=1, color="gray")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=9)

    sample_en = SAMPLE_LABEL_EN.get(sample, sample)
    ax.set_xlabel("Flood coefficient (probability / participation rate)")
    ax.set_title(f"Binary mechanisms across return periods ({sample_en})")

    plt.tight_layout()
    plt.show()


# ============== 4. Bar plot: one sample, all T ==============

def plot_binary_bar_allT(df: pd.DataFrame, sample: str = "rural"):
    """
    For a fixed sample (rural / urban):
      - x-axis: return period T
      - at each T: grouped bars by mechanism.
    """
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] Bar: sample={sample} has no results.")
        return

    sub["T_int"] = sub["T"].astype(int)

    mechanisms_zh = [m for m in DEP_ORDER_ZH if m in sub["dep_label"].unique()]
    if not mechanisms_zh:
        print(f"[WARN] Bar: sample={sample} has no mechanisms.")
        return

    n_mech = len(mechanisms_zh)
    mech_colors = plt.cm.Set1(np.linspace(0, 1, n_mech))

    T_vals = [t for t in T_LIST if t in sub["T_int"].unique()]
    x_base = np.arange(len(T_vals))
    width = 0.8 / n_mech

    fig, ax = plt.subplots(figsize=(7, 4))

    for j, m_zh in enumerate(mechanisms_zh):
        tmp = sub[sub["dep_label"] == m_zh].set_index("T_int")
        mech_short = get_dep_label_short(m_zh)

        est_list = []
        yerr_low_list = []
        yerr_high_list = []

        for t in T_vals:
            if t in tmp.index:
                row = tmp.loc[t]
                est = float(row["Estimate"])
                if {"CI_low", "CI_high"}.issubset(tmp.columns) and pd.notna(row["CI_low"]):
                    yerr_low = est - float(row["CI_low"])
                    yerr_high = float(row["CI_high"]) - est
                else:
                    se = float(row["StdError"])
                    yerr_low = 1.96 * se
                    yerr_high = 1.96 * se
            else:
                est = 0.0
                yerr_low = 0.0
                yerr_high = 0.0

            est_list.append(est)
            yerr_low_list.append(yerr_low)
            yerr_high_list.append(yerr_high)

        est_arr = np.array(est_list)
        yerr = np.vstack([yerr_low_list, yerr_high_list])

        x_pos = x_base + (j - (n_mech - 1) / 2) * width

        # bars
        ax.bar(
            x_pos,
            est_arr,
            width,
            yerr=yerr,
            capsize=4,
            label=mech_short,
            color=mech_colors[j],
            alpha=0.9,
        )

        # significance stars on bar tops
        for k, (xi, yi, yl, yh) in enumerate(zip(x_pos, est_arr, yerr_low_list, yerr_high_list)):
            t_idx = T_vals[k]
            if t_idx not in tmp.index:
                continue
            row = tmp.loc[t_idx]
            star = stars_for_p(row["PValue"])
            if not star:
                continue
            offset = yh if yi >= 0 else -yl
            ax.text(
                xi,
                yi + offset,
                star,
                ha="center",
                va="bottom" if yi >= 0 else "top",
                fontsize=9,
            )

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")

    ax.set_xticks(x_base)
    ax.set_xticklabels([str(int(t)) for t in T_vals])

    sample_en = SAMPLE_LABEL_EN.get(sample, sample)
    ax.set_xlabel("Return period T (years)")
    ax.set_ylabel("Flood coefficient (probability / participation rate)")
    ax.set_title(f"Binary mechanisms: grouped bars over T ({sample_en})")
    ax.legend(title="Mechanism")

    plt.tight_layout()
    plt.show()


# ============== 5. main ==============

if __name__ == "__main__":
    df_bin = load_binary_results()

    # rural sample: dot-and-whisker + bar
    plot_binary_dot_whisker_allT(df_bin, sample="rural")
    plot_binary_bar_allT(df_bin, sample="rural")

    # urban sample: dot-and-whisker + bar
    plot_binary_dot_whisker_allT(df_bin, sample="urban")
    plot_binary_bar_allT(df_bin, sample="urban")


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS education investment mechanisms (k=1)
Grouped bar plots of binary mechanisms over return periods T.

For each sample (rural / urban):
  - x-axis: return period T
  - at each T: grouped bars for Train_part and Edu_debt_any
  - y-axis: flood coefficient (probability / participation rate)
  - error bars: 95% confidence interval
  - significance stars on top of each bar:
        p < 0.01        -> ***
        0.01 <= p < 0.05 -> **
        0.05 <= p < 0.10 -> *
        p >= 0.10       -> (no star)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ============== 0. Global style & basic settings ==============

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Original notebook comment normalized for the public code archive.
TITLE_FONTSIZE   = 12   # Original notebook comment normalized for the public code archive.
AXLABEL_FONTSIZE = 10   # Original notebook comment normalized for the public code archive.
TICK_FONTSIZE    = 8    # Original notebook comment normalized for the public code archive.
LEGEND_FONTSIZE  = 9    # Original notebook comment normalized for the public code archive.
STAR_FONTSIZE    = 9    # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_mechanism_margins_k1_results.csv"

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Return periods to consider (years)
T_LIST = [2, 5, 10, 20, 50, 100]

# Mechanisms (Chinese labels in CSV)
DEP_ORDER_ZH = [
    "教育培训参与率（是否有支出）",   # Train_part
    "是否有教育负债",               # Edu_debt_any
]
DEP_ORDER_MAP = {lab: i for i, lab in enumerate(DEP_ORDER_ZH)}

# Short English labels to show in legend
DEP_LABEL_SHORT = {
    "教育培训参与率（是否有支出）": "Train part",
    "是否有教育负债": "Edu debt",
}

# Sample labels for titles
SAMPLE_LABEL_EN = {
    "rural": "rural sample",
    "urban": "urban sample",
    "all": "full sample",
}


# ============== 1. Load results & classify ==============

def classify_dep_type(row) -> str:
    """Classify dependent variable: 'binary' or 'amount'."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))
    # binary outcomes
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"
    # amount outcomes
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"
    return "amount"


def get_dep_label_short(dep_label_zh: str) -> str:
    """Map Chinese mechanism label to short English label."""
    return DEP_LABEL_SHORT.get(dep_label_zh, dep_label_zh)


def load_binary_results() -> pd.DataFrame:
    """Read CSV, keep k=1 and binary outcomes only."""
    df = pd.read_csv(RES_CSV)

    # numeric columns
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # k = 1 only
    df = df[df["k_window"] == 1].copy()

    # classify and ordering
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_order"] = df["dep_label"].map(DEP_ORDER_MAP)

    # keep binary only
    df = df[df["dep_type"] == "binary"].copy()

    return df


# ============== 2. p-value -> stars ==============

def stars_for_p(p: float) -> str:
    """
    Map p-value to significance stars:
      p < 0.01        -> "***"
      0.01 <= p < 0.05 -> "**"
      0.05 <= p < 0.10 -> "*"
      p >= 0.10       -> ""
    """
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


# ============== 3. Grouped bar plot over T ==============

def plot_binary_bar_allT(df: pd.DataFrame, sample: str = "rural",
                         save_svg: bool = True):
    """
    Grouped bar plot for a fixed sample (rural / urban / all):
      - x-axis: return period T
      - at each T: grouped bars for each binary mechanism
    """
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] Bar: sample={sample} has no results.")
        return

    sub["T_int"] = sub["T"].astype(int)

    # mechanisms present in this sample, keep in defined order
    mechanisms_zh = [m for m in DEP_ORDER_ZH if m in sub["dep_label"].unique()]
    if not mechanisms_zh:
        print(f"[WARN] Bar: sample={sample} has no mechanisms.")
        return

    n_mech = len(mechanisms_zh)
    mech_colors = plt.cm.Set1(np.linspace(0, 1, n_mech))

    # T values that exist in data and in T_LIST
    T_vals = [t for t in T_LIST if t in sub["T_int"].unique()]
    if not T_vals:
        print(f"[WARN] Bar: sample={sample} has no valid T values.")
        return

    x_base = np.arange(len(T_vals))
    width = 0.8 / n_mech  # total width 0.8, split by mechanisms

    fig, ax = plt.subplots(figsize=(7, 4))

    for j, m_zh in enumerate(mechanisms_zh):
        tmp = sub[sub["dep_label"] == m_zh].set_index("T_int")
        mech_short = get_dep_label_short(m_zh)

        est_list = []
        yerr_low_list = []
        yerr_high_list = []

        for t in T_vals:
            if t in tmp.index:
                row = tmp.loc[t]
                est = float(row["Estimate"])
                if {"CI_low", "CI_high"}.issubset(tmp.columns) and pd.notna(row["CI_low"]):
                    yerr_low = est - float(row["CI_low"])
                    yerr_high = float(row["CI_high"]) - est
                else:
                    se = float(row["StdError"])
                    yerr_low = 1.96 * se
                    yerr_high = 1.96 * se
            else:
                est = 0.0
                yerr_low = 0.0
                yerr_high = 0.0

            est_list.append(est)
            yerr_low_list.append(yerr_low)
            yerr_high_list.append(yerr_high)

        est_arr = np.array(est_list)
        yerr = np.vstack([yerr_low_list, yerr_high_list])

        # x positions for this mechanism
        x_pos = x_base + (j - (n_mech - 1) / 2) * width

        # bars
        ax.bar(
            x_pos,
            est_arr,
            width,
            yerr=yerr,
            capsize=4,
            label=mech_short,
            color=mech_colors[j],
            alpha=0.9,
        )

        # significance stars on bar tops
        for k, (xi, yi, yl, yh) in enumerate(zip(x_pos, est_arr, yerr_low_list, yerr_high_list)):
            t_idx = T_vals[k]
            if t_idx not in tmp.index:
                continue
            row = tmp.loc[t_idx]
            star = stars_for_p(row["PValue"])
            if not star:
                continue
            offset = yh if yi >= 0 else -yl
            ax.text(
                xi,
                yi + offset,
                star,
                ha="center",
                va="bottom" if yi >= 0 else "top",
                fontsize=STAR_FONTSIZE,   # Original notebook comment normalized for the public code archive.
            )

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")

    ax.set_xticks(x_base)
    ax.set_xticklabels([str(int(t)) for t in T_vals])
    # Original notebook comment normalized for the public code archive.
    ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)

    sample_en = SAMPLE_LABEL_EN.get(sample, sample)
    ax.set_xlabel("Return period T (years)", fontsize=AXLABEL_FONTSIZE)
    ax.set_ylabel("Flood coefficient (probability / participation rate)",
                  fontsize=AXLABEL_FONTSIZE)
    ax.set_title(f"Binary mechanisms: grouped bars over T ({sample_en})",
                 fontsize=TITLE_FONTSIZE)

    # Original notebook comment normalized for the public code archive.
    leg = ax.legend(title="Mechanism", fontsize=LEGEND_FONTSIZE)
    if leg is not None and leg.get_title() is not None:
        leg.get_title().set_fontsize(LEGEND_FONTSIZE)

    plt.tight_layout()

    # =============================================================================
    if save_svg:
        out_fp = OUT_DIR / f"CHFS_binary_grouped_{sample}.svg"
        fig.savefig(out_fp, format="svg", dpi=300, bbox_inches="tight")
        print(f"[INFO] Saved SVG: {out_fp}")

    # Original notebook comment normalized for the public code archive.
    plt.show()
    plt.close(fig)


# ============== 4. main ==============

if __name__ == "__main__":
    df_bin = load_binary_results()

    # rural sample
    plot_binary_bar_allT(df_bin, sample="rural", save_svg=True)

    # urban sample
    plot_binary_bar_allT(df_bin, sample="urban", save_svg=True)

    # if you also want the full sample, uncomment:
    # plot_binary_bar_allT(df_bin, sample="all", save_svg=True)


# ------------------------------------------------------------------------------
# Notebook cell 22
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Original notebook comment normalized for the public code archive.
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

LEGEND_FONTSIZE = 9  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\children\CHFS")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def save_legend_only_svg(out_path: Path, ncol: int = 2):
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    handles = [
        Patch(facecolor="red", edgecolor="red", label="Spending amount"),
        Patch(facecolor="black", edgecolor="black", label="Education debt amount"),
    ]

    # Original notebook comment normalized for the public code archive.
    fig = plt.figure(figsize=(3.2, 0.8))
    ax = fig.add_subplot(111)
    ax.axis("off")

    # Original notebook comment normalized for the public code archive.
    ax.legend(
        handles=handles,
        loc="center",
        ncol=ncol,          # Original notebook comment normalized for the public code archive.
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
        handlelength=1.6,
        columnspacing=1.2,
        handletextpad=0.6,
    )

    fig.savefig(out_path, format="svg", dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"[INFO] Saved legend SVG: {out_path}")


if __name__ == "__main__":
    save_legend_only_svg(OUT_DIR / "legend_spending_edudebt.svg", ncol=2)


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CHFS micro-level amount mechanisms: scatter plots across return periods T
------------------------------------------------------------------

Data:
  E:\impact_assessment_child_order\data\figure3\children\
    CHFS_panel_with_flood_BM_1to5y.parquet

Function:
  1) Construct amount outcomes:
        edu_amount       = last-year education expenditure (CNY)
        edu_debt_balance = education debt balance (CNY)
  2) Keep only households with children aged ≤ 15 (has_child_u15 == 1),
     and split by sample = all / rural / urban;
  3) For each amount outcome, plot:
        - x: share_flood_ge_T{T}_1y (optionally partial residuals)
        - y: amount outcome (optionally partial residuals)
        - different T in different colors, no fitted regression lines.

  Figures are saved as PNG (300 dpi) to:
    E:\impact_assessment_child_order\data\figure3\children\CHFS
"""

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.formula.api as smf

# ========= 0. Paths and global config =========

# Font family
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# ---- Separate font sizes (you can adjust these) ----
TITLE_FONTSIZE   = 14  # Figure title
AXLABEL_FONTSIZE = 14  # Axis labels
TICK_FONTSIZE    = 14  # Tick labels
LEGEND_FONTSIZE  = 12  # Legend text

# ---- 2015 average exchange rate: CNY per US$1 ----
EXCHANGE_RATE_2015 = 6.2284

# Panel data path (Windows)
PANEL_PARQUET = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_panel_with_flood_BM_1to5y.parquet"

# Output directory for PNG figures
OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Return periods (consistent with mechanism regressions)
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # using share_flood_ge_T*_1y

# ======== Fixed colors you provided ========
COLOR_MAP = {
    2:   "#1f77b4",
    5:   "#2ca02c",
    10:  "#9467bd",
    20:  "#e377c2",
    50:  "#bcbd22",
    100: "#17becf",
}

# Controls (consistent with main mechanism regressions)
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# ========= 1. Construct amount variables =========

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add amount variables to the panel:
      edu_amount       : education expenditure (CNY, raw amount)
      edu_debt_balance : education debt balance (CNY, raw amount)

    If columns already exist, they are kept.
    """
    df = df.copy()

    # Education expenditure amount
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0.0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0.0)
        else:
            raise KeyError(
                "Cannot find column '去年教育培训支出（元）' or 'edu_train_total' "
                "to construct 'edu_amount'."
            )

    # Education debt balance
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0.0)
        else:
            # If this column is missing in some waves, keep NaN
            df["edu_debt_balance"] = np.nan

    return df


# ========= 2. Sample filtering & partial residuals =========

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """
    Restrict to a given sample = all / rural / urban, and
    keep only households with children aged ≤ 15 (has_child_u15 == 1).
    """
    df = df.copy()

    # Only households with children <= 15
    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    # Rural / urban split
    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]
    # sample == "all": no further restriction

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute partial residuals:
      y_res = dep_var - E(dep_var | controls)
      x_res = exp_var - E(exp_var | controls)

    Controls are specified in CONTROL_FML_RHS.
    All regression variables are cast to float64
    to avoid potential Int64Dtype issues.
    """
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    # Drop missing values
    df = df.dropna(subset=[dep_var, exp_var,
                           "log_income", "log_childnum",
                           "is_rural", "wave"])

    if df.empty:
        return np.array([]), np.array([])

    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# ========= 3. Amount outcomes: scatter plots across all T =========

def plot_amount_scatter_allT(df_all: pd.DataFrame,
                             dep_var: str = "edu_amount",
                             sample: str = "rural",
                             partial: bool = True,
                             save_png: bool = True) -> None:
    """
    For a given amount outcome dep_var (e.g., edu_amount / edu_debt_balance),
    and a given sample (all / rural / urban), draw a scatter plot for all T:

      - x: share_flood_ge_T{T}_1y (partial residuals or raw values)
      - y: dep_var (partial residuals or raw values)
      - each T in a different color; no regression line.
    """
    df = filter_sample(df_all, sample)

    # Cast controls to float64 (avoid Int64Dtype issues)
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    fig, ax = plt.subplots(figsize=(7, 5))
    any_plotted = False

    for T in T_LIST:
        exp_col = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_col not in df.columns:
            print(f"[WARN] Missing exposure column {exp_col}, skip T={T}")
            continue

        # Columns needed: dep_var + exposure + controls
        cols_needed = [dep_var, exp_col,
                       "log_income", "log_childnum",
                       "is_rural", "wave"]
        cols_existing = [c for c in cols_needed if c in df.columns]

        sub = df.dropna(subset=cols_existing).copy()
        if sub.empty:
            print(f"[WARN] dep_var={dep_var}, sample={sample}, T={T} has no valid rows.")
            continue

        if partial:
            x, y = partial_residuals(sub, dep_var=dep_var, exp_var=exp_col)
            if x.size == 0:
                print(f"[WARN] dep_var={dep_var}, sample={sample}, T={T} "
                      f"partial residuals are empty.")
                continue
        else:
            x = sub[exp_col].to_numpy(float)
            y = sub[dep_var].to_numpy(float)

        ax.scatter(
            x,
            y,
            s=8,
            alpha=0.3,
            color=COLOR_MAP[T],   # =============================================================================
            label=f"T = {int(T)} years",
        )
        any_plotted = True

    if not any_plotted:
        print(f"[WARN] dep_var={dep_var}, sample={sample} produced no points.")
        plt.close(fig)
        return

    # Reference lines
    if partial:
        ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)

    # ---- Axis labels & title (fixed English) ----
    ax.set_xlabel("Flood exposure share", fontsize=AXLABEL_FONTSIZE)

    # CHANGED: y-axis title from CNY to thousand US$
    ax.set_ylabel("Expenditure (10³ USD)", fontsize=AXLABEL_FONTSIZE)

    if sample == "rural":
        title_str = "Rural"
    elif sample == "urban":
        title_str = "Urban"
    else:
        title_str = "All"
    ax.set_title(title_str, fontsize=TITLE_FONTSIZE)

    ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)

    # CHANGED: display y-axis in thousand US$,
    # while underlying data remain raw CNY

    ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda y, _: f"{int(round(y / EXCHANGE_RATE_2015 / 1000))}")
    )

    # ---- Legend: only for rural sample ----

    # ---- Save as PNG (300 dpi) ----
    if save_png:
        suffix = "partial" if partial else "raw"
        out_fp = OUT_DIR / f"CHFS_amount_scatter_{dep_var}_{sample}_{suffix}.png"
        fig.savefig(out_fp, dpi=300, bbox_inches="tight")
        print(f"[INFO] Saved PNG: {out_fp}")

    plt.show()
    plt.close(fig)


# ========= 4. main: example calls =========

def main() -> None:
    print(f"[READ] Panel file: {PANEL_PARQUET}")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Construct amount variables
    df_panel = add_amount_vars(df_panel)

    # Expenditure, rural sample
    print("\n[EXAMPLE] Expenditure, sample=rural, all T scatter")
    plot_amount_scatter_allT(
        df_panel,
        dep_var="edu_amount",
        sample="rural",
        partial=True,
        save_png=True,
    )

    # Expenditure, urban sample
    print("\n[EXAMPLE] Expenditure, sample=urban, all T scatter")
    plot_amount_scatter_allT(
        df_panel,
        dep_var="edu_amount",
        sample="urban",
        partial=True,
        save_png=True,
    )

    # Debt balance example:
    # plot_amount_scatter_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    #     sample="rural",
    #     partial=True,
    #     save_png=True,
    # )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 32
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ========= 1. Global config =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

LEGEND_FONTSIZE = 12

# Original notebook comment normalized for the public code archive.
OUT_SVG = Path(r"E:\impact_assessment_child_order\data\figure3\children\CHFS") / "CHFS_legend_only.svg"
OUT_SVG.parent.mkdir(parents=True, exist_ok=True)

# =============================================================================
COLOR_MAP = {
    2:   "#1f77b4",
    5:   "#2ca02c",
    10:  "#9467bd",
    20:  "#e377c2",
    50:  "#bcbd22",
    100: "#17becf",
}

# =============================================================================
def save_legend_only_svg(
    out_svg: Path,
    marker_size: float = 6,
    alpha: float = 0.8,
    ncol: int = 1,
) -> None:
    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.axis("off")

    # Original notebook comment normalized for the public code archive.
    handles = [
        Line2D(
            [0], [0],
            marker="o",
            linestyle="None",
            markersize=marker_size,
            markerfacecolor=COLOR_MAP[T],
            markeredgecolor=COLOR_MAP[T],
            alpha=alpha,
            label=f"T = {T} years",
        )
        for T in [2, 5, 10, 20, 50, 100]
    ]

    legend = ax.legend(
        handles=handles,
        loc="center",
        frameon=False,
        fontsize=LEGEND_FONTSIZE,
        title="Return period",
        ncol=ncol,
        handletextpad=0.8,
        labelspacing=0.8,
        borderpad=0.2,
    )

    if legend.get_title() is not None:
        legend.get_title().set_fontsize(LEGEND_FONTSIZE)

    # Original notebook comment normalized for the public code archive.
    fig.canvas.draw()
    bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(out_svg, format="svg", bbox_inches=bbox)

    plt.close(fig)
    print(f"[INFO] Saved legend-only SVG: {out_svg}")

# ========= 4. main =========
if __name__ == "__main__":
    save_legend_only_svg(OUT_SVG)


# ------------------------------------------------------------------------------
# Notebook cell 36
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# =============================================================================

PANEL_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_windows_1to5/CHFS_panel_with_flood_BM_1to5y.parquet"
)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# =============================================================================

def stars_for_p(p: float) -> str:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


# =============================================================================

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0)
        else:
            raise KeyError(
                "找不到『去年教育培训支出（元）』或 'edu_train_total'，无法生成 edu_amount。"
            )

    # Original notebook comment normalized for the public code archive.
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df["edu_debt_balance"] = np.nan

    return df


# =============================================================================

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> tuple[np.ndarray, np.ndarray]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=[
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ])
    if df.empty:
        return np.array([]), np.array([])

    # dep_var ~ controls
    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    # exp_var ~ controls
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# =============================================================================

def get_line_for_T(df: pd.DataFrame,
                   dep_var: str,
                   exp_var: str) -> tuple[np.ndarray, np.ndarray, float] | tuple[None, None, float]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=cols_for_reg)
    if df.shape[0] < 200:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    # Original notebook comment normalized for the public code archive.
    fml = f"{dep_var} ~ {exp_var} + {CONTROL_FML_RHS}"
    try:
        fit = smf.ols(fml, data=df).fit()
    except Exception as e:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    if exp_var not in fit.params.index:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    beta = float(fit.params[exp_var])
    pval = float(fit.pvalues.get(exp_var, np.nan))

    # Original notebook comment normalized for the public code archive.
    x_res, y_res = partial_residuals(df, dep_var=dep_var, exp_var=exp_var)
    if x_res.size == 0:
        print("[INFO] Notebook progress message.")
        return None, None, pval

    # Original notebook comment normalized for the public code archive.
    x_min = np.quantile(x_res, 0.05)
    x_max = np.quantile(x_res, 0.95)
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min == x_max:
        print("[INFO] Notebook progress message.")
        return None, None, pval

    x_grid = np.linspace(x_min, x_max, 50)
    # Original notebook comment normalized for the public code archive.
    y_grid = beta * x_grid

    return x_grid, y_grid, pval


# =============================================================================

def plot_amount_lines_allT(df_all: pd.DataFrame,
                           dep_var: str = "edu_amount",
                           dep_label: str = "教育金额（元）",
                           sample: str = "rural"):
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = filter_sample(df_all, sample)

    # Original notebook comment normalized for the public code archive.
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    colors = plt.cm.tab10(np.linspace(0, 1, len(T_LIST)))

    fig, ax = plt.subplots(figsize=(7, 5))

    x_all = []
    y_all = []
    any_line = False

    for idx, T in enumerate(T_LIST):
        exp_var = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_var not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        x_grid, y_grid, pval = get_line_for_T(df, dep_var=dep_var, exp_var=exp_var)
        if x_grid is None:
            continue

        # Original notebook comment normalized for the public code archive.
        star = stars_for_p(pval)
        if pval < 0.05:
            linestyle = "-"
            alpha = 1.0
        elif pval < 0.10:
            linestyle = "--"
            alpha = 0.9
        else:
            linestyle = ":"
            alpha = 0.6

        label = f"T = {int(T)} 年{(' ' + star) if star else ''}"

        ax.plot(
            x_grid,
            y_grid,
            color=colors[idx],
            linewidth=2,
            linestyle=linestyle,
            alpha=alpha,
            label=label,
        )

        x_all.append(x_grid)
        y_all.append(y_grid)
        any_line = True

        print(f"[INFO] sample={sample}, dep={dep_var}, T={T}: "
              f"beta={y_grid[-1]/x_grid[-1]:.3f}, p={pval:.4f}, stars='{star}'")

    if not any_line:
        print("[INFO] Notebook progress message.")
        return

    x_all = np.concatenate(x_all)
    y_all = np.concatenate(y_all)

    # Original notebook comment normalized for the public code archive.
    x_min, x_max = np.nanmin(x_all), np.nanmax(x_all)
    y_min, y_max = np.nanmin(y_all), np.nanmax(y_all)

    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min == x_max:
        x_min, x_max = -0.1, 0.1
    if not np.isfinite(y_min) or not np.isfinite(y_max) or y_min == y_max:
        y_min, y_max = -1.0, 1.0

    x_pad = 0.05 * (x_max - x_min if x_max > x_min else 0.1)
    y_pad = 0.08 * (y_max - y_min if y_max > y_min else 0.2)

    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    ax.set_xlabel("share_flood_ge_T_1y（控制后残差）")
    ax.set_ylabel(f"{dep_label}（控制后残差）")
    ax.set_title(
        f"{dep_label} × 洪水暴露：多返回期 T 回归线\n"
        f"sample = {sample}（已控制收入、儿童数、城乡、波次；线型反映显著性）"
    )
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.show()


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Original notebook comment normalized for the public code archive.
    df_panel = add_amount_vars(df_panel)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="rural",
    )

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="urban",
    )

    # Original notebook comment normalized for the public code archive.
    # plot_amount_lines_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    # Original notebook comment normalized for the public code archive.
    #     sample="rural",
    # )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 38
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""


from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# ========= 0. Paths and global config =========

# Global font
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Font sizes (adjust if needed)
TITLE_FONTSIZE   = 20
AXLABEL_FONTSIZE = 20
TICK_FONTSIZE    = 18
LEGEND_FONTSIZE  = 18

# Panel data path (Windows)
PANEL_PARQUET = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_panel_with_flood_BM_1to5y.parquet"

# Output directory for SVG figures
OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Return periods (consistent with mechanism regressions)
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # using share_flood_ge_T*_1y

# Controls (consistent with main mechanism regressions)
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# ========= Helper: p-value -> stars =========

def stars_for_p(p: float) -> str:
    """Map p-value to significance stars."""
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


# ========= 1. Construct amount variables =========

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add amount variables to the panel:
      edu_amount       : education expenditure (CNY, raw amount)
      edu_debt_balance : education debt balance (CNY, raw amount)

    If columns already exist, they are kept.
    """
    df = df.copy()

    # Education expenditure amount
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0)
        else:
            raise KeyError(
                "Cannot find column '去年教育培训支出（元）' or 'edu_train_total' "
                "to construct 'edu_amount'."
            )

    # Education debt balance
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0)
        else:
            # If this column is missing in some waves, keep NaN
            df["edu_debt_balance"] = np.nan

    return df


# ========= 2. Sample filtering & partial residuals =========

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """
    Restrict to a given sample = all / rural / urban,
    and keep only households with children aged ≤ 15 (has_child_u15 == 1).
    """
    df = df.copy()

    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> Tuple[np.ndarray, np.ndarray]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=[
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ])
    if df.empty:
        return np.array([]), np.array([])

    # dep_var ~ controls
    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    # exp_var ~ controls
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# ========= 3. For a single T: build regression line in residual space =========

def get_line_for_T(df: pd.DataFrame,
                   dep_var: str,
                   exp_var: str
                   ) -> tuple[np.ndarray | None, np.ndarray | None, float]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=cols_for_reg)
    if df.shape[0] < 200:
        print(f"[SKIP] {exp_var}: valid sample size < 200, N={df.shape[0]}")
        return None, None, np.nan

    # Main regression: dep_var ~ exp_var + controls
    fml = f"{dep_var} ~ {exp_var} + {CONTROL_FML_RHS}"
    try:
        fit = smf.ols(fml, data=df).fit()
    except Exception as e:
        print(f"[WARN] Regression failed for {exp_var}: {e}")
        return None, None, np.nan

    if exp_var not in fit.params.index:
        print(f"[WARN] No coefficient for {exp_var} in regression results.")
        return None, None, np.nan

    beta = float(fit.params[exp_var])
    pval = float(fit.pvalues.get(exp_var, np.nan))

    # Partial residuals
    x_res, y_res = partial_residuals(df, dep_var=dep_var, exp_var=exp_var)
    if x_res.size == 0:
        print(f"[WARN] {exp_var}: partial residuals are empty.")
        return None, None, pval

    # Original notebook comment normalized for the public code archive.
    x_min = np.quantile(x_res, 0.05)
    x_max = np.quantile(x_res, 0.95)
    if (not np.isfinite(x_min)) or (not np.isfinite(x_max)) or x_min == x_max:
        print(f"[WARN] {exp_var}: abnormal x_res range, x_min={x_min}, x_max={x_max}")
        return None, None, pval

    x_grid = np.linspace(x_min, x_max, 50)
    y_grid = beta * x_grid

    return x_grid, y_grid, pval


# ========= 4. Plot regression lines over all T =========

def plot_amount_lines_allT(df_all: pd.DataFrame,
                           dep_var: str = "edu_amount",
                           sample: str = "rural",
                           save_svg: bool = True) -> None:
    """
    For a given amount outcome dep_var and sample ∈ {all, rural, urban}:

      - For each T in T_LIST, construct a regression line in residual space:
          x-axis: exposure residual
          y-axis: outcome residual
      - Line style and legend stars reflect significance.

    Axis labels (fixed):
      x-axis: "Flood exposure share (residual)"
      y-axis: "Expenditure (residual)"

    Title:
      "Rural", "Urban", or "All"

    Legend is shown only for the rural sample.
    """
    df = filter_sample(df_all, sample)

    # Cast controls to float64
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    colors = plt.cm.tab10(np.linspace(0, 1, len(T_LIST)))

    # Create figure/axes with transparent background
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_alpha(0.0)     # figure background transparent
    ax.set_facecolor("none")     # axes background transparent

    x_all = []
    y_all = []
    any_line = False

    for idx, T in enumerate(T_LIST):
        exp_var = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_var not in df.columns:
            print(f"[WARN] Missing exposure column {exp_var}, skip T={T}")
            continue

        x_grid, y_grid, pval = get_line_for_T(df, dep_var=dep_var, exp_var=exp_var)
        if x_grid is None:
            continue

        star = stars_for_p(pval)

        # Line style by significance: p <= 0.05 -> solid; p > 0.05 -> dashed
        if pval <= 0.05:
            linestyle = "-"
        else:
            linestyle = "--"

        alpha = 1.0

        label = f"T = {int(T)} years{(' ' + star) if star else ''}"

        ax.plot(
            x_grid,
            y_grid,
            color=colors[idx],
            linewidth=3,
            linestyle=linestyle,
            alpha=alpha,
            label=label,
        )

        x_all.append(x_grid)
        y_all.append(y_grid)
        any_line = True

        print(
            f"[INFO] sample={sample}, dep={dep_var}, T={T}: "
            f"beta={y_grid[-1]/x_grid[-1]:.3f}, p={pval:.4f}, stars='{star}'"
        )

    if not any_line:
        print(f"[WARN] dep_var={dep_var}, sample={sample}: no regression lines drawn.")
        plt.close(fig)
        return

    x_all_concat = np.concatenate(x_all)
    y_all_concat = np.concatenate(y_all)

    # Axis ranges with small padding
    x_min, x_max = np.nanmin(x_all_concat), np.nanmax(x_all_concat)
    y_min, y_max = np.nanmin(y_all_concat), np.nanmax(y_all_concat)

    if (not np.isfinite(x_min)) or (not np.isfinite(x_max)) or x_min == x_max:
        x_min, x_max = -0.1, 0.1
    if (not np.isfinite(y_min)) or (not np.isfinite(y_max)) or y_min == y_max:
        y_min, y_max = -1.0, 1.0

    x_pad = 0.05 * (x_max - x_min if x_max > x_min else 0.1)
    y_pad = 0.08 * (y_max - y_min if y_max > y_min else 0.2)

    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Fixed English labels
    ax.set_xlabel("Flood exposure share", fontsize=AXLABEL_FONTSIZE)
    ax.set_ylabel("Expenditure", fontsize=AXLABEL_FONTSIZE)

    if sample == "rural":
        title_str = "Rural"
    elif sample == "urban":
        title_str = "Urban"
    else:
        title_str = "All"
    ax.set_title(title_str, fontsize=TITLE_FONTSIZE)

    ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)

    # Legend only for rural sample
    # if sample == "rural":
    #     leg = ax.legend(fontsize=LEGEND_FONTSIZE, title="Return period")
    #     if leg is not None and leg.get_title() is not None:
    #         leg.get_title().set_fontsize(LEGEND_FONTSIZE)

    plt.tight_layout()

    # Save as SVG (300 dpi, transparent)
    if save_svg:
        out_fp = OUT_DIR / f"CHFS_amount_reglines_{dep_var}_{sample}.svg"
        fig.savefig(
            out_fp,
            format="svg",
            dpi=300,
            bbox_inches="tight",
            transparent=True,
        )
        print(f"[INFO] Saved SVG (transparent): {out_fp}")

    plt.show()
    plt.close(fig)


# ========= 5. main: example calls =========

def main() -> None:
    print(f"[READ] Panel file: {PANEL_PARQUET}")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Construct amount variables
    df_panel = add_amount_vars(df_panel)

    # Example 1: education expenditure, rural sample
    print("\n[EXAMPLE] Expenditure, sample=rural, regression lines over T")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        sample="rural",
        save_svg=True,
    )

    # Example 2: education expenditure, urban sample
    print("\n[EXAMPLE] Expenditure, sample=urban, regression lines over T")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        sample="urban",
        save_svg=True,
    )

    # If you want debt balance as well, call similarly:
    # plot_amount_lines_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    #     sample="rural",
    #     save_svg=True,
    # )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 39
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""


from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# ========= 0. Paths and global config =========

# Global font
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Font sizes (adjust if needed)
TITLE_FONTSIZE   = 18
AXLABEL_FONTSIZE = 18
TICK_FONTSIZE    = 16
LEGEND_FONTSIZE  = 16  # currently unused (no legend)

# Panel data path (Windows)
PANEL_PARQUET = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "CHFS_panel_with_flood_BM_1to5y.parquet"

# Output directory for PNG figures
OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Return periods (consistent with mechanism regressions)
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # using share_flood_ge_T*_1y

# Controls (consistent with main mechanism regressions)
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# ========= Helper: p-value -> stars (still used in print info) =========

def stars_for_p(p: float) -> str:
    """Map p-value to significance stars."""
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


# ========= 1. Construct amount variables =========

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add amount variables to the panel:
      edu_amount       : education expenditure (CNY, raw amount)
      edu_debt_balance : education debt balance (CNY, raw amount)

    If columns already exist, they are kept.
    """
    df = df.copy()

    # Education expenditure amount
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0)
        else:
            raise KeyError(
                "Cannot find column '去年教育培训支出（元）' or 'edu_train_total' "
                "to construct 'edu_amount'."
            )

    # Education debt balance
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0)
        else:
            # If this column is missing in some waves, keep NaN
            df["edu_debt_balance"] = np.nan

    return df


# ========= 2. Sample filtering & partial residuals =========

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """
    Restrict to a given sample = all / rural / urban,
    and keep only households with children aged ≤ 15 (has_child_u15 == 1).
    """
    df = df.copy()

    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> Tuple[np.ndarray, np.ndarray]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=[
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ])
    if df.empty:
        return np.array([]), np.array([])

    # dep_var ~ controls
    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    # exp_var ~ controls
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# ========= 3. For a single T: build regression line in residual space =========

def get_line_for_T(df: pd.DataFrame,
                   dep_var: str,
                   exp_var: str
                   ) -> tuple[np.ndarray | None, np.ndarray | None, float]:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=cols_for_reg)
    if df.shape[0] < 200:
        print(f"[SKIP] {exp_var}: valid sample size < 200, N={df.shape[0]}")
        return None, None, np.nan

    # Main regression: dep_var ~ exp_var + controls
    fml = f"{dep_var} ~ {exp_var} + {CONTROL_FML_RHS}"
    try:
        fit = smf.ols(fml, data=df).fit()
    except Exception as e:
        print(f"[WARN] Regression failed for {exp_var}: {e}")
        return None, None, np.nan

    if exp_var not in fit.params.index:
        print(f"[WARN] No coefficient for {exp_var} in regression results.")
        return None, None, np.nan

    beta = float(fit.params[exp_var])
    pval = float(fit.pvalues.get(exp_var, np.nan))

    # Partial residuals
    x_res, y_res = partial_residuals(df, dep_var=dep_var, exp_var=exp_var)
    if x_res.size == 0:
        print(f"[WARN] {exp_var}: partial residuals are empty.")
        return None, None, pval

    # Original notebook comment normalized for the public code archive.
    x_min = np.quantile(x_res, 0.05)
    x_max = np.quantile(x_res, 0.95)
    if (not np.isfinite(x_min)) or (not np.isfinite(x_max)) or x_min == x_max:
        print(f"[WARN] {exp_var}: abnormal x_res range, x_min={x_min}, x_max={x_max}")
        return None, None, pval

    x_grid = np.linspace(x_min, x_max, 50)
    y_grid = beta * x_grid

    return x_grid, y_grid, pval


# ========= 4. Plot regression lines over all T =========

def plot_amount_lines_allT(df_all: pd.DataFrame,
                           dep_var: str = "edu_amount",
                           sample: str = "rural",
                           save_png: bool = True) -> None:
    """
    For a given amount outcome dep_var and sample ∈ {all, rural, urban}:

      - For each T in T_LIST, construct a regression line in residual space:
          x-axis: exposure residual
          y-axis: outcome residual
      - Line style encodes significance:
          p <= 0.05 -> solid
          p > 0.05  -> dashed

    Axis labels (fixed):
      x-axis: "Flood exposure share"
      y-axis: "Expenditure"

    Title:
      "Rural", "Urban", or "All"

    Legend is disabled (no legend).
    """
    df = filter_sample(df_all, sample)

    # Cast controls to float64
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    colors = plt.cm.tab10(np.linspace(0, 1, len(T_LIST)))

    # Create figure/axes with transparent background
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_alpha(0.0)     # figure background transparent
    ax.set_facecolor("none")     # axes background transparent

    x_all = []
    y_all = []
    any_line = False

    for idx, T in enumerate(T_LIST):
        exp_var = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_var not in df.columns:
            print(f"[WARN] Missing exposure column {exp_var}, skip T={T}")
            continue

        x_grid, y_grid, pval = get_line_for_T(df, dep_var=dep_var, exp_var=exp_var)
        if x_grid is None:
            continue

        star = stars_for_p(pval)

        # Line style by significance: p <= 0.05 -> solid; p > 0.05 -> dashed
        if pval <= 0.05:
            linestyle = "-"
        else:
            linestyle = "--"

        ax.plot(
            x_grid,
            y_grid,
            color=colors[idx],
            linewidth=3,
            linestyle=linestyle,
            alpha=1.0,
            # label kept in case you re-enable legend later
            label=f"T = {int(T)} years{(' ' + star) if star else ''}",
        )

        x_all.append(x_grid)
        y_all.append(y_grid)
        any_line = True

        print(
            f"[INFO] sample={sample}, dep={dep_var}, T={T}: "
            f"beta={y_grid[-1]/x_grid[-1]:.3f}, p={pval:.4f}, stars='{star}'"
        )

    if not any_line:
        print(f"[WARN] dep_var={dep_var}, sample={sample}: no regression lines drawn.")
        plt.close(fig)
        return

    x_all_concat = np.concatenate(x_all)
    y_all_concat = np.concatenate(y_all)

    # Axis ranges with small padding
    x_min, x_max = np.nanmin(x_all_concat), np.nanmax(x_all_concat)
    y_min, y_max = np.nanmin(y_all_concat), np.nanmax(y_all_concat)

    if (not np.isfinite(x_min)) or (not np.isfinite(x_max)) or x_min == x_max:
        x_min, x_max = -0.1, 0.1
    if (not np.isfinite(y_min)) or (not np.isfinite(y_max)) or y_min == y_max:
        y_min, y_max = -1.0, 1.0

    x_pad = 0.05 * (x_max - x_min if x_max > x_min else 0.1)
    y_pad = 0.08 * (y_max - y_min if y_max > y_min else 0.2)

    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    # Fixed English labels
    ax.set_xlabel("Flood exposure share", fontsize=AXLABEL_FONTSIZE)
    ax.set_ylabel("Expenditure", fontsize=AXLABEL_FONTSIZE)

    if sample == "rural":
        title_str = "Rural"
    elif sample == "urban":
        title_str = "Urban"
    else:
        title_str = "All"
    ax.set_title(title_str, fontsize=TITLE_FONTSIZE)

    ax.tick_params(axis="both", labelsize=TICK_FONTSIZE)

    # Ensure no legend (even if label exists)
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()

    plt.tight_layout()

    # Save as PNG (300 dpi, transparent)
    if save_png:
        out_fp = OUT_DIR / f"CHFS_amount_reglines_{dep_var}_{sample}.png"
        fig.savefig(
            out_fp,
            format="png",
            dpi=300,
            bbox_inches="tight",
            transparent=True,
        )
        print(f"[INFO] Saved PNG (transparent): {out_fp}")

    plt.show()
    plt.close(fig)


# ========= 5. main: example calls =========

def main() -> None:
    print(f"[READ] Panel file: {PANEL_PARQUET}")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Construct amount variables
    df_panel = add_amount_vars(df_panel)

    # Example 1: education expenditure, rural sample
    print("\n[EXAMPLE] Expenditure, sample=rural, regression lines over T")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        sample="rural",
        save_png=True,
    )

    # Example 2: education expenditure, urban sample
    print("\n[EXAMPLE] Expenditure, sample=urban, regression lines over T")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        sample="urban",
        save_png=True,
    )

    # If you want debt balance as well, call similarly:
    # plot_amount_lines_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    #     sample="rural",
    #     save_png=True,
    # )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 43
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
School flooding mechanisms (joint exposure): dot-and-whisker plot
-----------------------------------------------------------------

Data:
  E:\impact_assessment_child_order\data\figure3\children\
    school_mechanism_FE_results.csv

Filters:
  - Y_var == "edu_years"
  - f_var == "F_school_joint"
  - sample in {"rural", "urban"}
  - Term in SCHOOL_EXPO_VARS:

    SCHOOL_EXPO_VARS = [
        "F_school_mean_share",
        "F_school_any_exposed_ge1m",
        "F_school_mean_days_ge1m",
        "F_school_n_years",
    ]

Output:
  Dot-and-whisker plot (rural & urban in the same panel):
    E:\impact_assessment_child_order\data\figure3\children\CHFS\
      school_mechanism_FE_joint_dotwhisker.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Paths & global style =========

# Input regression results (Windows path)
RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "school_mechanism_FE_results.csv"

# Output directory and file for dot-whisker figure
OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_DOT = OUT_DIR / "school_mechanism_FE_joint_dotwhisker.png"

Y_VAR_TARGET = "edu_years"
F_VAR_SET_NAME = "F_school_joint"

# School exposure variables (the jointly included regressors)
SCHOOL_EXPO_VARS = [
    "F_school_mean_share",
    "F_school_any_exposed_ge1m",
    "F_school_mean_days_ge1m",
    "F_school_n_years",
]

# === Short English labels for y-axis ===
TERM_LABELS = {
    "F_school_mean_share":       "Mean flooded share",
    "F_school_any_exposed_ge1m": "Any ≥1 m flood",
    "F_school_mean_days_ge1m":   "Mean days ≥1 m",
    "F_school_n_years":          "Observed years",
}

# Samples and colors: rural / urban only
SAMPLES = ["rural", "urban"]
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}
SAMPLE_COLOR = {
    "rural": "#2ca02c",  # green
    "urban": "#d62728",  # red
}

# Global font and sizes
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

TITLE_FONTSIZE          = 24
AXLABEL_FONTSIZE        = 22
TICK_FONTSIZE           = 20
LEGEND_FONTSIZE         = 20
LEGEND_TITLE_FONTSIZE   = 20

# ---- Dot / error bar style (easy to tune here) ----
DOT_SIZE         = 9    # marker size
MARKER_EDGEWIDTH = 2.5  # marker edge width
ERR_LINEWIDTH    = 3.0  # error bar line width
CAPSIZE          = 8    # cap length for error bars

# ---- Star position (vertical offset above the point) ----
STAR_Y_OFFSET = 0.25    # in "y" units (category spacing is 1.0)


# ========= Helpers =========

def stars_for_p(p: float) -> str:
    """
    Return significance stars based on p-value.

      p > 0.10            -> ""
      0.05 < p <= 0.10    -> "*"
      0.01 < p <= 0.05    -> "**"
      p <= 0.01           -> "***"
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p <= 0.01:
        return "***"
    elif p <= 0.05:
        return "**"
    elif p <= 0.10:
        return "*"
    else:
        return ""


def load_joint_results() -> pd.DataFrame:
    """
    Read and filter the joint regression results, keeping:
      - Y_var = "edu_years"
      - f_var = "F_school_joint"
      - sample ∈ {rural, urban}
      - Term ∈ SCHOOL_EXPO_VARS

    Also compute 95% confidence intervals and significance stars.
    """
    print(f"[STEP] Reading regression results: {RES_CSV}")
    df = pd.read_csv(RES_CSV)
    print(f"[INFO] Raw results shape: {df.shape}")

    sub = df[
        (df["Y_var"] == Y_VAR_TARGET)
        & (df["f_var"] == F_VAR_SET_NAME)
        & (df["sample"].isin(SAMPLES))
        & (df["Term"].isin(SCHOOL_EXPO_VARS))
    ].copy()

    if sub.empty:
        raise RuntimeError(
            "Filtered results are empty. Please check that the regression script "
            "outputs the joint-specification results as expected."
        )

    # Enforce Term order
    sub["Term"] = pd.Categorical(sub["Term"], categories=SCHOOL_EXPO_VARS, ordered=True)
    sub = sub.sort_values(["sample", "Term"])

    # 95% CI
    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]

    # Significance stars
    sub["sig"] = sub["PValue"].apply(stars_for_p)

    print("[INFO] Filtered joint-spec results (head):")
    print(
        sub[
            ["sample", "Term", "Estimate", "StdError", "PValue", "CI_low", "CI_high", "sig"]
        ].head()
    )

    return sub


# ========= Dot-and-whisker: rural & urban in one figure =========

def plot_dot_whisker_joint(sub: pd.DataFrame, save_path: Path = OUT_DOT) -> None:
    """
    Dot-and-whisker plot:

      - y-axis: school exposure variables (in SCHOOL_EXPO_VARS order)
      - x-axis: coefficient estimate
      - rural & urban shown in the same panel with different colors
      - significance stars printed above each point (on top of the error bar)
    """
    # Determine which terms actually appear
    terms_here = [t for t in SCHOOL_EXPO_VARS if t in sub["Term"].unique()]
    if not terms_here:
        print("[WARN] Dot-whisker: no SCHOOL_EXPO_VARS found in results.")
        return

    term_to_y = {t: i for i, t in enumerate(terms_here)}
    y_base = np.array([term_to_y[t] for t in terms_here])

    # Keep only needed samples and terms
    sub = sub[sub["Term"].isin(terms_here) & sub["sample"].isin(SAMPLES)].copy()

    # y-axis tick labels (English)
    yticklabels = [TERM_LABELS.get(t, t) for t in terms_here]

    # (We still compute x-range in case you later want horizontal offsets.)
    est_min = sub["Estimate"].min()
    est_max = sub["Estimate"].max()
    if not np.isfinite(est_min) or not np.isfinite(est_max) or est_max <= est_min:
        est_min, est_max = -0.5, 0.5
    x_range = est_max - est_min
    # Currently not used, but kept for flexibility
    x_star_offset = 0.0 if x_range > 0 else 0.0

    # Determine vertical offsets for rural / urban
    samples_here = [s for s in SAMPLES if s in sub["sample"].unique()]
    n_s = len(samples_here)
    if n_s == 0:
        print("[WARN] Dot-whisker: no rural/urban results found.")
        return
    if n_s == 1:
        offsets = {samples_here[0]: 0.0}
    else:
        offset_vals = np.linspace(-0.15, 0.15, n_s)
        offsets = dict(zip(samples_here, offset_vals))

    fig, ax = plt.subplots(figsize=(8, 5))

    for s in samples_here:
        tmp = sub[sub["sample"] == s].copy()
        if tmp.empty:
            continue
        tmp = tmp.sort_values("Term")

        est = tmp["Estimate"].to_numpy(float)
        ci_low = tmp["CI_low"].to_numpy(float)
        ci_high = tmp["CI_high"].to_numpy(float)
        xerr = np.vstack([est - ci_low, ci_high - est])

        y = np.array([term_to_y[t] for t in tmp["Term"]]) + offsets[s]

        ax.errorbar(
            est,
            y,
            xerr=xerr,
            fmt="o",
            markersize=DOT_SIZE,
            markeredgewidth=MARKER_EDGEWIDTH,
            linestyle="none",
            capsize=CAPSIZE,
            elinewidth=ERR_LINEWIDTH,
            capthick=ERR_LINEWIDTH,
            label=SAMPLE_LABEL.get(s, s),
            color=SAMPLE_COLOR.get(s, None),
        )

        # Significance stars: above the point / error bar
        for xi, yi, (_, row) in zip(est, y, tmp.iterrows()):
            star = row["sig"]
            if star:
                ax.text(
                    xi + x_star_offset,
                    yi + STAR_Y_OFFSET,
                    star,
                    va="bottom",
                    ha="center",
                    fontsize=20,
                    color=SAMPLE_COLOR.get(s, "black"),
                )

    # Zero line
    ax.axvline(0.0, linestyle="--", linewidth=2, color="gray")

    ax.set_yticks(y_base)
    ax.set_yticklabels(yticklabels, fontsize=TICK_FONTSIZE)

    ax.set_xlabel(
        "Marginal effect on years of schooling",
        fontsize=AXLABEL_FONTSIZE,
    )
    ax.set_title(
        "School flooding mechanisms",
        fontsize=TITLE_FONTSIZE,
    )

    ax.tick_params(axis="x", labelsize=TICK_FONTSIZE)

    # Legend
    leg = ax.legend(title="Sample", fontsize=LEGEND_FONTSIZE)
    if leg is not None and leg.get_title() is not None:
        leg.get_title().set_fontsize(LEGEND_TITLE_FONTSIZE)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"[DONE] Dot-and-whisker figure saved: {save_path}")


# ========= Main =========

def main():
    sub = load_joint_results()
    plot_dot_whisker_joint(sub, save_path=OUT_DOT)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 44
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd

# =============================================================================
CSV_PATH = (
    Path(r"E:\impact_assessment_child_order\data\figure3\children")
    / "school_mechanism_FE_results.csv"
)

Y_VAR_TARGET = "edu_years"
F_VAR_SET_NAME = "F_school_joint"

SCHOOL_EXPO_VARS = [
    "F_school_mean_share",
    "F_school_any_exposed_ge1m",
    "F_school_mean_days_ge1m",
    "F_school_n_years",
]

# =============================================================================
print(f"[STEP] Read CSV: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)
print(f"[INFO] Raw shape: {df.shape}")

sub = df[
    (df["Y_var"] == Y_VAR_TARGET)
    & (df["f_var"] == F_VAR_SET_NAME)
    & (df["sample"].isin(["rural", "urban"]))
    & (df["Term"].isin(SCHOOL_EXPO_VARS))
].copy()

# Original notebook comment normalized for the public code archive.
sub["Term"] = pd.Categorical(sub["Term"], categories=SCHOOL_EXPO_VARS, ordered=True)
sub = sub.sort_values(["Term", "sample"])

# =============================================================================
print("\n[INFO] Joint-spec rows (rural + urban):")
print(
    sub[["sample", "Term", "Estimate", "StdError", "PValue"]]
)

# =============================================================================
print("\n[INFO] Wide view of estimates (rows = Term, cols = sample):")
wide_est = sub.pivot(index="Term", columns="sample", values="Estimate")
print(wide_est)

print("\n[INFO] Wide view of p-values (rows = Term, cols = sample):")
wide_p = sub.pivot(index="Term", columns="sample", values="PValue")
print(wide_p)

# =============================================================================
print("\n[CHECK] Coefficients for F_school_mean_days_ge1m (Mean days ≥1 m):")
days = sub[sub["Term"] == "F_school_mean_days_ge1m"][
    ["sample", "Estimate", "StdError", "PValue"]
]
print(days.to_string(index=False))


# ------------------------------------------------------------------------------
# Notebook cell 45
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
School flooding mechanism (Mean days ≥1 m only): dot-and-whisker plot
---------------------------------------------------------------------

Data:
  E:\impact_assessment_child_order\data\figure3\children\
    school_mechanism_FE_results.csv

Filter:
  - Y_var  == "edu_years"
  - f_var  == "F_school_joint"
  - Term   == "F_school_mean_days_ge1m"
  - sample in {"rural", "urban"}

Output:
  PNG + SVG in:
  E:\impact_assessment_child_order\data\figure3\children\CHFS\
    school_mechanism_FE_joint_mean_days_ge1m.png
    school_mechanism_FE_joint_mean_days_ge1m.svg
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Paths =========
RES_CSV = Path(
    r"E:\impact_assessment_child_order\data\figure3\children"
) / "school_mechanism_FE_results.csv"

OUT_DIR = Path(
    r"E:\impact_assessment_child_order\data\figure3\children\CHFS"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_DIR / "school_mechanism_FE_joint_mean_days_ge1m.png"
OUT_SVG = OUT_DIR / "school_mechanism_FE_joint_mean_days_ge1m.svg"

# ========= Filters =========
Y_VAR_TARGET      = "edu_years"
F_VAR_SET_NAME    = "F_school_joint"
TERM_TARGET       = "F_school_mean_days_ge1m"
TERM_LABEL_EN     = "Mean days ≥1 m"

SAMPLES      = ["rural", "urban"]
SAMPLE_LABEL = {"rural": "Rural", "urban": "Urban"}
SAMPLE_COLOR = {"rural": "#2ca02c", "urban": "#d62728"}

# ========= Global style =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

TITLE_FONTSIZE        = 20
AXLABEL_FONTSIZE      = 40
TICK_FONTSIZE         = 40
LEGEND_FONTSIZE       = 18
LEGEND_TITLE_FONTSIZE = 18

DOT_SIZE         = 9
MARKER_EDGEWIDTH = 2.5
ERR_LINEWIDTH    = 3.0
CAPSIZE          = 8

STAR_Y_OFFSET    = 0.15


def stars_for_p(p: float) -> str:
    """Significance stars."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p <= 0.01:
        return "***"
    elif p <= 0.05:
        return "**"
    elif p <= 0.10:
        return "*"
    else:
        return ""


def load_single_term() -> pd.DataFrame:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[STEP] Reading regression results: {RES_CSV}")
    df = pd.read_csv(RES_CSV)
    print(f"[INFO] Raw results shape: {df.shape}")

    sub = df[
        (df["Y_var"] == Y_VAR_TARGET)
        & (df["f_var"] == F_VAR_SET_NAME)
        & (df["Term"] == TERM_TARGET)
        & (df["sample"].isin(SAMPLES))
    ].copy()

    if sub.empty:
        raise RuntimeError(
            "No rows found for Mean days ≥1 m (F_school_mean_days_ge1m) "
            "with the requested filters."
        )

    sub["sample"] = pd.Categorical(sub["sample"], categories=SAMPLES, ordered=True)
    sub = sub.sort_values("sample")

    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]
    sub["sig"] = sub["PValue"].apply(stars_for_p)

    print("[INFO] Single-term results (Mean days ≥1 m):")
    print(sub[["sample", "Term", "Estimate", "StdError",
               "PValue", "CI_low", "CI_high", "sig"]])

    return sub


def plot_single_term(sub: pd.DataFrame) -> None:
    """Archived notebook note for 06_figure3_child_education.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    base_y = 0.0
    offsets = {"rural": -0.08, "urban": 0.08}

    x_min = float(sub["CI_low"].min())
    x_max = float(sub["CI_high"].max())
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_max <= x_min:
        x_min, x_max = -0.5, 0.5
    x_range = x_max - x_min
    x_pad = 0.25 * x_range
    x_lim = (x_min - x_pad, x_max + x_pad)

    fig, ax = plt.subplots(figsize=(7.5, 4))

    for s in SAMPLES:
        tmp = sub[sub["sample"] == s]
        if tmp.empty:
            continue

        est = float(tmp["Estimate"].iloc[0])
        ci_low = float(tmp["CI_low"].iloc[0])
        ci_high = float(tmp["CI_high"].iloc[0])
        star = tmp["sig"].iloc[0]

        y = base_y + offsets[s]
        xerr = np.array([[est - ci_low], [ci_high - est]])

        ax.errorbar(
            est,
            y,
            xerr=xerr,
            fmt="o",
            markersize=DOT_SIZE,
            markeredgewidth=MARKER_EDGEWIDTH,
            linestyle="none",
            capsize=CAPSIZE,
            elinewidth=ERR_LINEWIDTH,
            capthick=ERR_LINEWIDTH,
            label=SAMPLE_LABEL.get(s, s),
            color=SAMPLE_COLOR.get(s, None),
        )

        if star:
            ax.text(
                est,
                y + STAR_Y_OFFSET,
                star,
                va="bottom",
                ha="center",
                fontsize=18,
                color=SAMPLE_COLOR.get(s, "black"),
            )

    # Original notebook comment normalized for the public code archive.
    ax.axvline(0.0, linestyle="--", linewidth=2, color="gray")

    # Original notebook comment normalized for the public code archive.
    ax.set_yticks([])
    ax.set_yticklabels([])

    # Original notebook comment normalized for the public code archive.
    ax.set_ylim(base_y - 0.5, base_y + 0.5)

    ax.set_xlim(x_lim)
    # Original notebook comment normalized for the public code archive.
    # ax.set_xlabel("Marginal effect on years of schooling", fontsize=AXLABEL_FONTSIZE)
    # ax.set_title("School flooding mechanism: Mean days ≥1 m", fontsize=TITLE_FONTSIZE)

    ax.tick_params(axis="x", labelsize=35)

    # Original notebook comment normalized for the public code archive.
    # leg = ax.legend(title="Sample", fontsize=LEGEND_FONTSIZE, loc="upper right")
    # if leg is not None and leg.get_title() is not None:
    #     leg.get_title().set_fontsize(LEGEND_TITLE_FONTSIZE)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.savefig(OUT_SVG, format="svg", bbox_inches="tight")
    plt.show()
    print(f"[DONE] Single-term figure saved: {OUT_PNG}")
    print(f"[DONE] Single-term figure saved: {OUT_SVG}")


def main():
    sub = load_single_term()
    plot_single_term(sub)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 51
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
School flooding “count mechanisms”: grouped bar chart with error bars
+ linear trend lines (Rural & Urban)
--------------------------------------------------------------------

Input (count mechanism results):
  E:\\impact_assessment_child_order\\data\\figure3\\children\\
      school_mechanism_FE_n_floodyears.csv

Trend regression results (linear trend in number of flooded years):
  Either of the following (the script will try both):
  1) E:\\impact_assessment_child_order\\data\\figure3\\children\\
       school_mechanism_trend_FE_results.csv
  2) E:\\impact_assessment_child_order\\data\\figure3\\children\\CHFS\\
       school_mechanism_trend_FE_results.csv

Expected columns in count-mechanism CSV:
  sample, k_flood, Term, Estimate, StdError, PValue, nobs

Expected columns in trend CSV:
  sample, Term == "F_school_n_flood_years", Estimate, StdError, PValue, nobs

We keep:
  sample ∈ {"rural", "urban"}

Output (PNG, 300 dpi):
  E:\\impact_assessment_child_order\\data\\figure3\\children\\CHFS\\
      school_mechanism_FE_n_floodyears_bar.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Paths =========
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\children")

RES_CSV = BASE_DIR / "school_mechanism_FE_n_floodyears.csv"

# trend CSV: try both base folder and CHFS subfolder
TREND_CSV_CANDIDATES = [
    BASE_DIR / "school_mechanism_trend_FE_results.csv",
    BASE_DIR / "CHFS" / "school_mechanism_trend_FE_results.csv",
]

OUT_DIR = BASE_DIR / "CHFS"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_BAR = OUT_DIR / "school_mechanism_FE_n_floodyears_bar.png"

# ========= Global style =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

TITLE_FONTSIZE   = 18
AXLABEL_FONTSIZE = 16
TICK_FONTSIZE    = 14
LEGEND_FONTSIZE  = 14


def sig_label(p: float) -> str:
    """
    Significance stars:
      p > 0.10        → ""
      0.05 < p ≤ 0.10 → "*"
      0.01 < p ≤ 0.05 → "**"
      p ≤ 0.01        → "***"
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""

    if p > 0.10:
        return ""
    elif p > 0.05:
        return "*"
    elif p > 0.01:
        return "**"
    else:
        return "***"


def p_text(p: float) -> str:
    """
    Pretty-print p-value for slope text.
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "P = NA"

    if p <= 0.001:
        return "P < 0.001"
    elif p <= 0.01:
        return "P < 0.01"
    elif p <= 0.05:
        return "P < 0.05"
    else:
        return f"P = {p:.2f}"


def prepare_count_data() -> pd.DataFrame:
    """Read count-mechanism results, keep rural/urban, add CI and stars."""
    print(f"[STEP] Reading count-mechanism results: {RES_CSV}")
    df = pd.read_csv(RES_CSV)
    print(f"[INFO] Raw table shape: {df.shape}")

    # Keep only rural / urban
    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("No rural/urban rows found in the count-mechanism file.")

    # Ensure k_flood is integer
    df["k_flood"] = pd.to_numeric(df["k_flood"], errors="coerce").astype(int)

    # 95% CI
    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]

    # Significance stars
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Example rows after filtering (count):")
    print(df.head())

    return df


def load_trend_results():
    """
    Read trend-regression results and return a dict:
        trend_info[sample] = {"slope": ..., "p": ...}
    If no candidate CSV is found, return {} and skip trend lines.
    """
    csv_path = None
    for cand in TREND_CSV_CANDIDATES:
        if cand.exists():
            csv_path = cand
            break

    if csv_path is None:
        print("[WARN] Trend CSV not found in any candidate path. "
              "Trend lines will NOT be drawn.")
        for cand in TREND_CSV_CANDIDATES:
            print(f"  tried: {cand}")
        return {}

    print(f"[STEP] Reading trend results: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[INFO] Raw trend table shape: {df.shape}")

    df = df[(df["Term"] == "F_school_n_flood_years") &
            (df["sample"].isin(["rural", "urban"]))].copy()

    if df.empty:
        print("[WARN] No rural/urban trend rows found. Trend lines will NOT be drawn.")
        return {}

    info = {}
    for _, row in df.iterrows():
        s = str(row["sample"])
        info[s] = {
            "slope": float(row["Estimate"]),
            "p": float(row["PValue"]),
        }

    print("[INFO] Trend info:")
    print(info)
    return info


def plot_grouped_bar(df: pd.DataFrame, trend_info: dict) -> None:
    """
    Grouped bar chart with error bars and optional trend lines.
    """
    ks = sorted(df["k_flood"].unique())
    samples = ["rural", "urban"]
    sample_label = {"rural": "Rural", "urban": "Urban"}
    sample_color = {"rural": "tab:green", "urban": "tab:red"}

    x_base = np.array(ks, dtype=float)  # actual k as x

    n_s = len(samples)
    width = 0.8 / n_s

    # y limits based on CI range
    y_min = np.nanmin(df["CI_low"])
    y_max = np.nanmax(df["CI_high"])
    if not np.isfinite(y_min) or not np.isfinite(y_max) or y_max <= y_min:
        y_min, y_max = -0.5, 0.5
    y_span = y_max - y_min
    y_pad = 0.15 * y_span
    y_lim = (y_min - y_pad, y_max + y_pad)

    fig, ax = plt.subplots(figsize=(8, 5))

    z = 1.96

    # ----- Bars + error bars + stars -----
    for i, s in enumerate(samples):
        sub = df[df["sample"] == s].copy()
        if sub.empty:
            continue

        sub = sub.set_index("k_flood").reindex(ks)

        est_arr     = sub["Estimate"].to_numpy(float)
        se_arr      = sub["StdError"].to_numpy(float)
        ci_high_arr = sub["CI_high"].to_numpy(float)

        yerr = z * se_arr
        x_pos = x_base + (i - (n_s - 1) / 2) * width

        ax.bar(
            x_pos,
            est_arr,
            width,
            yerr=yerr,
            capsize=4,
            linewidth=0,
            label=sample_label.get(s, s),
            color=sample_color.get(s, None),
            alpha=0.9,
        )

        for xi, ci_high, (_, row) in zip(x_pos, ci_high_arr, sub.iterrows()):
            star = row.get("sig", "")
            if not star:
                continue
            ax.text(
                xi,
                ci_high + 0.06 * y_span,
                star,
                ha="center",
                va="bottom",
                fontsize=12,
                color=sample_color.get(s, "black"),
            )

    # ----- Trend lines -----
    for s in samples:
        if s not in trend_info:
            continue
        sub = df[df["sample"] == s].copy()
        if sub.empty:
            continue

        k_vals = sub["k_flood"].to_numpy(float)
        b_vals = sub["Estimate"].to_numpy(float)

        slope = trend_info[s]["slope"]

        # Anchor line at mean (k_mean, beta_mean)
        k_mean = np.nanmean(k_vals)
        b_mean = np.nanmean(b_vals)
        intercept = b_mean - slope * k_mean

        x_line = np.linspace(k_vals.min(), k_vals.max(), 100)
        y_line = intercept + slope * x_line

        ax.plot(
            x_line,
            y_line,
            color=sample_color.get(s, "black"),
            linewidth=2.0,
            alpha=0.9,
        )

    # ----- Axes & labels -----
    ax.axhline(0.0, linestyle="--", color="gray", linewidth=1.2)

    xticklabels = [str(k) if k < 9 else "9+" for k in ks]
    ax.set_xticks(x_base)
    ax.set_xticklabels(xticklabels, fontsize=TICK_FONTSIZE)

    ax.set_ylim(y_lim)

    ax.set_xlabel("Number of flooded school years", fontsize=AXLABEL_FONTSIZE)
    ax.set_ylabel(
        "Marginal effect on years of schooling (years)",
        fontsize=AXLABEL_FONTSIZE,
    )
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)

    leg = ax.legend(fontsize=LEGEND_FONTSIZE)
    if leg is not None and leg.get_title() is not None:
        leg.get_title().set_fontsize(LEGEND_FONTSIZE)

    ax.set_title(
        "School flooding mechanisms (count): Rural vs Urban",
        fontsize=TITLE_FONTSIZE,
    )

    # ----- Slope & p text -----
    for s in samples:
        if s not in trend_info:
            continue
        slope = trend_info[s]["slope"]
        pval  = trend_info[s]["p"]
        txt = f"{sample_label[s]} slope = {slope:.3f}, {p_text(pval)}"

        if s == "rural":
            # top-left corner
            ax.text(
                0.02,
                0.96,
                txt,
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=13,
                color=sample_color.get(s, "black"),
            )
        else:
            # top-right corner
            ax.text(
                0.98,
                0.96,
                txt,
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=13,
                color=sample_color.get(s, "black"),
            )

    plt.tight_layout()
    plt.savefig(OUT_BAR, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"[DONE] Grouped bar + trend-line figure saved: {OUT_BAR}")


def main():
    df = prepare_count_data()
    trend_info = load_trend_results()
    plot_grouped_bar(df, trend_info)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 52
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
School flooding “count mechanisms”: grouped bar chart with error bars
+ linear trend lines (Rural & Urban)
--------------------------------------------------------------------
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Paths =========
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\children")

RES_CSV = BASE_DIR / "school_mechanism_FE_n_floodyears.csv"

TREND_CSV_CANDIDATES = [
    BASE_DIR / "school_mechanism_trend_FE_results.csv",
    BASE_DIR / "CHFS" / "school_mechanism_trend_FE_results.csv",
]

OUT_DIR = BASE_DIR / "CHFS"
OUT_DIR.mkdir(parents=True, exist_ok=True)

#OUT_BAR = OUT_DIR / "school_mechanism_FE_n_floodyears_bar.png"
OUT_BAR = OUT_DIR / "school_mechanism_FE_n_floodyears_bar.svg"


# ========= Global style =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

TITLE_FONTSIZE   = 18
AXLABEL_FONTSIZE = 16
TICK_FONTSIZE    = 14
LEGEND_FONTSIZE  = 14


def sig_label(p: float) -> str:
    """Significance stars."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p > 0.10:
        return ""
    elif p > 0.05:
        return "*"
    elif p > 0.01:
        return "**"
    else:
        return "***"


def p_text(p: float) -> str:
    """Pretty p-value text for trend line."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "P = NA"
    if p <= 0.001:
        return "P < 0.001"
    elif p <= 0.01:
        return "P < 0.01"
    elif p <= 0.05:
        return "P < 0.05"
    else:
        return f"P = {p:.2f}"


def prepare_count_data() -> pd.DataFrame:
    """Read count-mechanism results, keep rural/urban, add CI and stars."""
    print(f"[STEP] Reading count-mechanism results: {RES_CSV}")
    df = pd.read_csv(RES_CSV)
    print(f"[INFO] Raw table shape: {df.shape}")

    df = df[df["sample"].isin(["rural", "urban"])].copy()
    if df.empty:
        raise RuntimeError("No rural/urban rows found in the count-mechanism file.")

    df["k_flood"] = pd.to_numeric(df["k_flood"], errors="coerce").astype(int)

    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]

    df["PValue"] = pd.to_numeric(df["PValue"], errors="coerce")
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Example rows after filtering (count):")
    print(df.head())
    print("[INFO] Check stars:")
    print(df[["sample", "k_flood", "Estimate", "PValue", "sig"]])

    return df


def load_trend_results():
    """Load trend regression results."""
    csv_path = None
    for cand in TREND_CSV_CANDIDATES:
        if cand.exists():
            csv_path = cand
            break

    if csv_path is None:
        print("[WARN] Trend CSV not found in any candidate path. Trend lines will NOT be drawn.")
        for cand in TREND_CSV_CANDIDATES:
            print(f"  tried: {cand}")
        return {}

    print(f"[STEP] Reading trend results: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[INFO] Raw trend table shape: {df.shape}")

    df = df[(df["Term"] == "F_school_n_flood_years") &
            (df["sample"].isin(["rural", "urban"]))].copy()

    if df.empty:
        print("[WARN] No rural/urban trend rows found. Trend lines will NOT be drawn.")
        return {}

    info = {}
    for _, row in df.iterrows():
        s = str(row["sample"])
        info[s] = {
            "slope": float(row["Estimate"]),
            "p": float(row["PValue"]),
        }

    print("[INFO] Trend info:", info)
    return info


def plot_grouped_bar(df: pd.DataFrame, trend_info: dict) -> None:
    """Grouped bar chart with error bars and trend lines."""
    ks = sorted(df["k_flood"].unique())
    samples = ["rural", "urban"]
    sample_label = {"rural": "Rural", "urban": "Urban"}
    sample_color = {"rural": "tab:green", "urban": "tab:red"}

    x_base = np.array(ks, dtype=float)
    n_s = len(samples)
    width = 0.8 / n_s

    y_min = np.nanmin(df["CI_low"])
    y_max = np.nanmax(df["CI_high"])
    if not np.isfinite(y_min) or not np.isfinite(y_max) or y_max <= y_min:
        y_min, y_max = -0.5, 0.5
    y_span = y_max - y_min
    y_pad = 0.15 * y_span
    y_lim = (y_min - y_pad, y_max + y_pad)

    fig, ax = plt.subplots(figsize=(8, 5))
    z = 1.96

    # ----- Bars + error bars + stars -----
    for i, s in enumerate(samples):
        sub = df[df["sample"] == s].copy()
        if sub.empty:
            continue

        sub = sub.set_index("k_flood").reindex(ks)

        est_arr     = sub["Estimate"].to_numpy(float)
        se_arr      = sub["StdError"].to_numpy(float)
        ci_high_arr = sub["CI_high"].to_numpy(float)

        yerr = z * se_arr
        x_pos = x_base + (i - (n_s - 1) / 2) * width

        ax.bar(
            x_pos,
            est_arr,
            width,
            yerr=yerr,
            capsize=4,
            linewidth=0,
            label=sample_label.get(s, s),
            color=sample_color.get(s, None),
            alpha=0.9,
        )

        # Original notebook comment normalized for the public code archive.
        for xi, ci_high, est, (_, row) in zip(
            x_pos, ci_high_arr, est_arr, sub.iterrows()
        ):
            star = row.get("sig", "")
            if not isinstance(star, str) or star == "":
                continue
            # Original notebook comment normalized for the public code archive.
            base_y = max(ci_high, 0.0)
            ax.text(
                xi,
                base_y + 0.04 * y_span,
                star,
                ha="center",
                va="bottom",
                fontsize=12,
                color="black",  # Original notebook comment normalized for the public code archive.
            )

    # ----- Trend lines -----
    for s in samples:
        if s not in trend_info:
            continue
        sub = df[df["sample"] == s].copy()
        if sub.empty:
            continue

        k_vals = sub["k_flood"].to_numpy(float)
        b_vals = sub["Estimate"].to_numpy(float)

        slope = trend_info[s]["slope"]
        k_mean = np.nanmean(k_vals)
        b_mean = np.nanmean(b_vals)
        intercept = b_mean - slope * k_mean

        x_line = np.linspace(k_vals.min(), k_vals.max(), 100)
        y_line = intercept + slope * x_line

        ax.plot(
            x_line,
            y_line,
            color=sample_color.get(s, "black"),
            linewidth=2.0,
            alpha=0.9,
        )

    # ----- Axes & labels -----
    ax.axhline(0.0, linestyle="--", color="gray", linewidth=1.2)

    xticklabels = [str(k) if k < 9 else "9+" for k in ks]
    ax.set_xticks(x_base)
    ax.set_xticklabels(xticklabels, fontsize=TICK_FONTSIZE)

    ax.set_ylim(y_lim)
    ax.set_xlabel("Number of flooded school years", fontsize=AXLABEL_FONTSIZE)
    ax.set_ylabel(
        "Marginal effect on years of schooling",
        fontsize=AXLABEL_FONTSIZE,
    )
    ax.tick_params(axis="y", labelsize=TICK_FONTSIZE)

    leg = ax.legend(fontsize=LEGEND_FONTSIZE)
    if leg is not None and leg.get_title() is not None:
        leg.get_title().set_fontsize(LEGEND_FONTSIZE)

    ax.set_title(
        "School flooding mechanisms",
        fontsize=TITLE_FONTSIZE,
    )

    # ----- Slope & p text -----
    for s in samples:
        if s not in trend_info:
            continue
        slope = trend_info[s]["slope"]
        pval  = trend_info[s]["p"]
        txt = f"{sample_label[s]} slope = {slope:.3f}, {p_text(pval)}"
        if s == "rural":
            ax.text(
                0.02, 0.96, txt,
                transform=ax.transAxes,
                ha="left", va="top",
                fontsize=13,
                color=sample_color.get(s, "black"),
            )
        else:
            ax.text(
                0.98, 0.96, txt,
                transform=ax.transAxes,
                ha="right", va="top",
                fontsize=13,
                color=sample_color.get(s, "black"),
            )

    plt.tight_layout()
    plt.savefig(OUT_BAR, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"[DONE] Grouped bar + trend-line figure saved: {OUT_BAR}")


def main():
    df = prepare_count_data()
    trend_info = load_trend_results()
    plot_grouped_bar(df, trend_info)


if __name__ == "__main__":
    main()
