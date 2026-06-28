#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot multi-mechanism flood coefficients by return period T
from the aggregated results:
  fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv

Models:
2) Mechanism model M~F   : M ~ Flood + controls
3) Health+Mechanism H~F+M: health_z ~ Flood + M + controls

For each figure:
  - x-axis: return period T (2, 5, 10, 20, 50, 100)
  - y-axis: coefficient of Flood (already aggregated across time windows)
  - one line for each mechanism (group:M_var)
  - significance stars: p<0.1 -> "*"; p<0.05 -> "**"; p<0.001 -> "****"
  - For H~F+M, optionally overlay a dashed baseline line (H~F).

Figures are drawn separately for sample = all / rural / urban.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Global plotting style (Times New Roman) =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# ========= Paths =========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

# Column name constants
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_Y      = "Y_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Model labels (English)
SPEC_LABEL = {
    "M~F":   "Mechanism model: M ~ Flood",
    "H~F+M": "Health + mechanism model: Health ~ Flood + M",
}

# Return period order
T_ORDER = [2, 5, 10, 20, 50, 100]


# ========= Helper: significance stars by p-value =========
def stars_for_p(p: float) -> str:
    """
    Return significance stars based on p-value:
      p < 0.001 -> '****'
      p < 0.05  -> '**'
      p < 0.10  -> '*'
      otherwise -> ''
    """
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


# ========= Load aggregated results =========
def load_agg_results() -> pd.DataFrame:
    print(f"[READ] Aggregated results: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] shape  = {df.shape}")
    print(f"[INFO] spec   = {df[COL_SPEC].unique()}")
    print(f"[INFO] sample = {df[COL_SAMPLE].unique()}")
    print(f"[INFO] T      = {sorted(df[COL_T].unique())}")

    # Ensure numeric types
    df[COL_T]   = pd.to_numeric(df[COL_T], errors="coerce")
    df[COL_EST] = pd.to_numeric(df[COL_EST], errors="coerce")
    df[COL_P]   = pd.to_numeric(df[COL_P], errors="coerce")

    return df


# ========= Core plotting function =========
def plot_multimech_by_T(df: pd.DataFrame,
                        spec: str = "H~F+M",
                        sample: str = "all",
                        add_baseline: bool = True) -> None:
    """
    Plot multi-mechanism flood coefficients by return period T
    for a given model spec and sample.

    Parameters
    ----------
    df : DataFrame
        Aggregated results.
    spec : {"M~F", "H~F+M"}
        Model specification.
    sample : {"all", "urban", "rural"}
        Sample group.
    add_baseline : bool
        For H~F+M, whether to overlay baseline H~F as a dashed line.
        (Baseline spec is not plotted as a standalone figure.)
    """
    # Subset for current spec and sample
    sub = df[(df[COL_SPEC] == spec) & (df[COL_SAMPLE] == sample)].copy()
    if sub.empty:
        print(f"[WARN] spec={spec}, sample={sample} has no results. Skip plotting.")
        return

    # For Health-related models, keep only health_z (in M~F, Y_var is M_var)
    if spec in ["H~F", "H~F+M"]:
        sub = sub[sub[COL_Y] == "health_z"].copy()
        if sub.empty:
            print(f"[WARN] spec={spec}, sample={sample} has no health_z rows. Skip.")
            return

    # Baseline line (only for H~F+M plots, if required and if baseline exists)
    base_df = None
    if add_baseline and spec == "H~F+M":
        base_df = df[
            (df[COL_SPEC] == "H~F")
            & (df[COL_SAMPLE] == sample)
            & (df[COL_GROUP] == "baseline")
            & (df[COL_Y] == "health_z")
        ].copy()
        if base_df.empty:
            print(f"[WARN] No baseline H~F results for sample={sample}. No overlay.")
            base_df = None

    # ========= y-axis range =========
    y_vals = sub[COL_EST].copy()
    if base_df is not None:
        y_vals = pd.concat([y_vals, base_df[COL_EST]], ignore_index=True)

    y_min = y_vals.min()
    y_max = y_vals.max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -1.0, 1.0

    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.03 * y_range

    # ========= Start plotting =========
    plt.figure(figsize=(7, 5))

    # 1) Baseline line (if any)
    if base_df is not None and not base_df.empty:
        base_df = base_df.sort_values(COL_T)
        x = base_df[COL_T].values
        y = base_df[COL_EST].values
        p = base_df[COL_P].values

        plt.plot(x, y, linestyle="--", marker="o", label="Baseline (H~F)")
        for xi, yi, pi in zip(x, y, p):
            s = stars_for_p(pi)
            if s:
                plt.text(xi, yi + star_offset, s,
                         ha="center", va="bottom", fontsize=9)

    # 2) Lines for each mechanism: combinations of (group, M_var)
    combos = (
        sub[[COL_GROUP, COL_MVAR]]
        .drop_duplicates()
        .sort_values([COL_GROUP, COL_MVAR])
        .itertuples(index=False)
    )

    for comb in combos:
        g = getattr(comb, COL_GROUP)
        m = getattr(comb, COL_MVAR)

        sub_gm = sub[(sub[COL_GROUP] == g) & (sub[COL_MVAR] == m)].copy()
        if sub_gm.empty:
            continue

        sub_gm = sub_gm.sort_values(COL_T)
        x = sub_gm[COL_T].values
        y = sub_gm[COL_EST].values
        p = sub_gm[COL_P].values

        if spec == "H~F" and g == "baseline":
            label = "Baseline (H~F)"
        else:
            label = f"{g}: {m}"

        plt.plot(x, y, marker="o", label=label)

        # Add significance stars
        for xi, yi, pi in zip(x, y, p):
            s = stars_for_p(pi)
            if s:
                plt.text(xi, yi + star_offset,
                         s, ha="center", va="bottom", fontsize=9)

    # ========= Formatting =========
    plt.axhline(0, linestyle="--", linewidth=1)

    plt.xlabel("Return period T (years)")
    if spec in ["H~F", "H~F+M"]:
        plt.ylabel("Coefficient of Flood on Health (health_z, aggregated)")
    else:
        plt.ylabel("Coefficient of Flood on mechanism variable M (aggregated)")

    title_en = SPEC_LABEL.get(spec, spec)
    plt.title(f"Multi-mechanism flood coefficients ({title_en}, sample = {sample})")

    plt.xticks(T_ORDER)
    plt.ylim(y_lower, y_upper)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.show()


# ========= main: only two model specs (M~F and H~F+M) =========
def main():
    df = load_agg_results()

    # Only keep the last two models: M~F and H~F+M
    spec_list = ["M~F", "H~F+M"]
    sample_list = ["all", "rural", "urban"]

    for spec in spec_list:
        for sample in sample_list:
            # Only H~F+M overlays baseline; M~F does not
            add_base = (spec == "H~F+M")
            print(f"\n[PLOT] spec={spec}, sample={sample}, add_baseline={add_base}")
            plot_multimech_by_T(df, spec=spec, sample=sample, add_baseline=add_base)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
import pandas as pd

CSV_PATH = r"E:\impact_assessment_child_order\data\figure3\fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

df = pd.read_csv(CSV_PATH)

# Original notebook comment normalized for the public code archive.
df_mech = df[df["spec"] == "M~F"].copy()

print("[INFO] unique groups:")
print(df_mech["group"].unique())

print("\n[INFO] unique mechanism variables (M_var):")
print(df_mech["M_var"].unique())

print("[INFO] Notebook progress message.")
combos = (
    df_mech[["group", "M_var"]]
    .drop_duplicates()
    .sort_values(["group", "M_var"])
)
print(combos.to_string(index=False))


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism model only: M ~ Flood + controls

From:
    fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv

For each sample (all / rural / urban):
  - x-axis: return period T (2, 5, 10, 20, 50, 100)
  - y-axis: coefficient of Flood on mechanism variable M
  - one line per mechanism variable
  - legend uses intuitive English labels for mechanism variables
  - significance stars: p<0.1 -> "*"; p<0.05 -> "**"; p<0.001 -> "****"
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========= Global plotting style =========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# ========= Paths =========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

# Column names
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Return periods
T_ORDER = [2, 5, 10, 20, 50, 100]

# =============================================================================
M_VAR_LABELS = {
    # Out-of-pocket spending (individual level)
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",

    # Out-of-pocket spending (household level)
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",

    # Any use of care (binary)
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",

    # Utilization intensity
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",

    # Access: time to care
    "outpt_time_single_unc": "Travel time to last outpatient visit (min, uncapped)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min, uncapped)",
    "outpt_time_month_unc":  "Total travel time for outpatient visits, last month (min, uncapped)",

    # Access: distance to care
    "outpt_dist_single_unc": "Travel distance to last outpatient visit (km, uncapped)",
    "inp_dist_single_unc":   "Travel distance to last inpatient visit (km, uncapped)",

    # Access: transport mode
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

# Original notebook comment normalized for the public code archive.
GROUP_LABELS = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

SAMPLE_LABELS = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}


# ========= Helper: p-value to stars =========
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


# ========= Read aggregated results =========
def load_mech_results() -> pd.DataFrame:
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    # Original notebook comment normalized for the public code archive.
    df = df[df[COL_SPEC] == "M~F"].copy()
    if df.empty:
        raise RuntimeError("No rows with spec == 'M~F' found in the CSV.")

    # Original notebook comment normalized for the public code archive.
    df[COL_T]   = pd.to_numeric(df[COL_T], errors="coerce")
    df[COL_EST] = pd.to_numeric(df[COL_EST], errors="coerce")
    df[COL_P]   = pd.to_numeric(df[COL_P], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df[COL_T].isin(T_ORDER)].copy()

    print(f"[INFO] mechanism results shape = {df.shape}")
    print("[INFO] samples:", df[COL_SAMPLE].unique())
    print("[INFO] groups:", df[COL_GROUP].unique())

    return df


# ========= Core plotting function: mechanism model only =========
def plot_mechanism_by_T(df: pd.DataFrame, sample: str = "all") -> None:
    """
    Plot Flood coefficients for mechanism model (M~F) by T,
    for a given sample ("all", "rural", "urban").
    """
    sub = df[df[COL_SAMPLE] == sample].copy()
    if sub.empty:
        print(f"[WARN] No M~F rows for sample={sample}. Skip.")
        return

    # Original notebook comment normalized for the public code archive.
    sub[COL_T] = pd.Categorical(sub[COL_T], categories=T_ORDER, ordered=True)
    sub = sub.sort_values([COL_MVAR, COL_T])

    # Original notebook comment normalized for the public code archive.
    y_vals = sub[COL_EST]
    y_min, y_max = y_vals.min(), y_vals.max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    star_offset = 0.03 * (y_upper - y_lower)

    # Original notebook comment normalized for the public code archive.
    mvars = sorted(sub[COL_MVAR].dropna().unique())
    cmap = plt.get_cmap("tab20")
    color_map = {m: cmap(i % 20) for i, m in enumerate(mvars)}

    # =============================================================================
    plt.figure(figsize=(7.5, 5.0))

    # Original notebook comment normalized for the public code archive.
    for m in mvars:
        sub_m = sub[sub[COL_MVAR] == m].copy()
        sub_m = sub_m.sort_values(COL_T)

        x = sub_m[COL_T].astype(int).values
        y = sub_m[COL_EST].values
        p = sub_m[COL_P].values

        label = M_VAR_LABELS.get(m, m)  # Original notebook comment normalized for the public code archive.
        color = color_map[m]

        plt.plot(x, y, marker="o", label=label, color=color)

        # Original notebook comment normalized for the public code archive.
        for xi, yi, pi in zip(x, y, p):
            s = stars_for_p(pi)
            if s:
                plt.text(
                    xi,
                    yi + star_offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=color,
                )

    # Original notebook comment normalized for the public code archive.
    plt.axhline(0, color="grey", linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    plt.xlabel("Return period T (years)")
    plt.ylabel("Coefficient of Flood on mechanism M")

    sample_lab = SAMPLE_LABELS.get(sample, sample)
    plt.title(f"Mechanism model: M ~ Flood (sample = {sample_lab})")

    plt.xticks(T_ORDER)
    plt.ylim(y_lower, y_upper)

    # Original notebook comment normalized for the public code archive.
    plt.legend(
        fontsize=8,
        bbox_to_anchor=(1.02, 1.0),
        loc="upper left",
        borderaxespad=0.0,
    )

    plt.tight_layout()
    plt.show()


# ========= main =========
def main():
    df_mech = load_mech_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PLOT] Mechanism model, sample = {sample}")
        plot_mechanism_by_T(df_mech, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism models only (spec == "M~F"):
Grouped forest-style point plots of flood coefficients by return period T,
for 7 mechanism groups.

Input:
    E:\\impact_assessment_child_order\\data\\figure3\\
        fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv

For each mechanism group (7 groups) and sample (all / rural / urban):
    - x-axis: return period T (2, 5, 10, 20, 50, 100)
    - y-axis: coefficient of Flood (from mechanism model M ~ Flood + controls)
    - one series per mechanism variable (M_var) within that group
    - significance stars based on p-values:
        p < 0.001 -> "****"
        p < 0.05  -> "**"
        p < 0.10  -> "*"
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# If T is the return period, recommended order
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Plotting options ==========
# Whether to connect points with lines
CONNECT_POINTS = False  # default: show stand-alone points only

# Whether to show vertical error bars (requires a standard error column)
SHOW_ERRORBAR = False   # default: no error bars
ERR_COL = "Std. Error"  # change if your CSV uses a different column name

# Error bar scale factor (e.g. 1.96 for ~95% CI, 1.0 for ±1 SE)
ERR_SCALE = 1.96

# ========== More intuitive English labels ==========
# 7 mechanism group labels
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

# Mechanism variable labels
MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min, uncapped)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min, uncapped)",
    "outpt_time_month_unc":  "Total travel time for outpatient visits, last month (min, uncapped)",
    "outpt_dist_single_unc": "Travel distance to last outpatient visit (km, uncapped)",
    "inp_dist_single_unc":   "Travel distance to last inpatient visit (km, uncapped)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

# Sample labels
SAMPLE_LABEL = {
    "all":   "All",
    "rural": "Rural",
    "urban": "Urban",
}

# ========== Helper: significance stars ==========
def stars_for_p(p):
    """Return significance stars based on p-value."""
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


# ========== Read & filter: mechanism model only ==========
def load_mechanism_results():
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    # Keep only mechanism model: spec == "M~F"
    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    # Convert numeric columns
    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    # Drop invalid T or coefficients
    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])

    return df_mech


# ========== Plot for one mechanism group + sample ==========
def plot_one_group(df_mech, mech_group, sample="all"):
    """
    Plot one figure for a given mechanism group (mech_group) and sample:
      - x-axis: T
      - y-axis: Flood coefficient (Estimate)
      - one series per M_var in that group
      - markers only by default; optional lines and error bars controlled by
        CONNECT_POINTS and SHOW_ERRORBAR.
    """
    sub = df_mech[
        (df_mech[COL_GROUP] == mech_group) &
        (df_mech[COL_SAMPLE] == sample)
    ].copy()

    if sub.empty:
        print(f"[WARN] group={mech_group}, sample={sample} has no rows. Skip.")
        return

    # Keep and sort T
    sub = sub.dropna(subset=[COL_T, COL_EST])
    ts = sorted(sub[COL_T].unique())

    # y-axis range
    y_vals = sub[COL_EST]
    y_min = float(y_vals.min())
    y_max = float(y_vals.max())
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    # Color map across M_var within this group
    mvars = (
        sub[COL_MVAR]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    n_mvars = len(mvars)
    cmap = plt.cm.get_cmap("tab10", n_mvars)

    fig, ax = plt.subplots(figsize=(6.0, 4.0))

    for i, mvar in enumerate(mvars):
        sub_mv = sub[sub[COL_MVAR] == mvar].copy()
        if sub_mv.empty:
            continue

        sub_mv = sub_mv.sort_values(COL_T)
        x = sub_mv[COL_T].values
        y = sub_mv[COL_EST].values
        p = sub_mv[COL_P].values

        label = MVAR_LABEL.get(mvar, mvar)
        color = cmap(i)

        # Optional error bars
        yerr = None
        if SHOW_ERRORBAR and (ERR_COL in sub_mv.columns):
            se = pd.to_numeric(sub_mv[ERR_COL], errors="coerce").values
            # Handle all-NaN case gracefully
            if np.isfinite(se).any():
                yerr = ERR_SCALE * se

        # Marker / line choice
        if CONNECT_POINTS:
            if yerr is not None:
                ax.errorbar(
                    x, y, yerr=yerr,
                    fmt="o-", color=color, label=label,
                    capsize=3, linewidth=1
                )
            else:
                ax.plot(
                    x, y, marker="o",
                    color=color, label=label
                )
        else:
            if yerr is not None:
                ax.errorbar(
                    x, y, yerr=yerr,
                    fmt="o", linestyle="none",
                    color=color, label=label,
                    capsize=3
                )
            else:
                ax.scatter(
                    x, y,
                    color=color, label=label
                )

        # Significance stars
        for xi, yi, pi in zip(x, y, p):
            s = stars_for_p(pi)
            if s:
                ax.text(
                    xi, yi + star_offset,
                    s,
                    ha="center", va="bottom",
                    fontsize=9,
                    color=color,
                )

    # Horizontal zero line
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)

    # Axes and title
    ax.set_xlabel("Return period T (years)")
    ax.set_ylabel("Coefficient of Flood")

    group_title = GROUP_LABEL.get(mech_group, mech_group)
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"{group_title} (sample: {sample_title})")

    # x-axis ticks
    ax.set_xticks(ts)
    ax.set_xlim(min(ts) - 1, max(ts) + 1)

    ax.set_ylim(y_lower, y_upper)

    # Legend at bottom to avoid overlap with points
    ax.legend(
        fontsize=8,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.15),
        ncol=1,
        frameon=False
    )

    plt.tight_layout()

    # Save PNG + SVG
    fn_base = f"mech_MF_{sample}_{mech_group}.png"
    out_png = OUT_DIR / fn_base
    out_svg = OUT_DIR / fn_base.replace(".png", ".svg")

    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    # 7 mechanism groups (order can be adjusted)
    group_list = [
        "oop_individual",
        "oop_household",
        "util_any",
        "util_intensity",
        "access_time",
        "access_distance",
        "access_transport",
    ]

    # You can also restrict to ["all"] if needed
    sample_list = ["all", "rural", "urban"]

    for g in group_list:
        for s in sample_list:
            print(f"\n[PLOT] group={g}, sample={s}")
            plot_one_group(df_mech, mech_group=g, sample=s)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism models only (spec == "M~F"):
Grouped forest-style point plots of flood coefficients by return period T,
for 7 mechanism groups.

Input:
    E:\\impact_assessment_child_order\\data\\figure3\\
        fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv

For each mechanism group (7 groups) and sample (all / rural / urban):
    - x-axis: return period T (2, 5, 10, 20, 50, 100)
    - y-axis: coefficient of Flood (from mechanism model M ~ Flood + controls)
    - one series per mechanism variable (M_var) within that group
    - point style encodes significance:
        p > 0.10      : colored ring only (white inside)
        0.05 < p ≤0.10: large white core
        0.001<p ≤0.05 : medium white core
        p ≤ 0.001     : small white core (almost solid)
    - significance stars still shown above the markers.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# If T is the return period, recommended order
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Plotting options ==========
# Whether to connect points with thin lines
CONNECT_POINTS = False  # default: stand-alone markers only

# Whether to show vertical error bars (requires a standard error column)
SHOW_ERRORBAR = False   # default: no error bars
ERR_COL = "Std. Error"  # change if your CSV uses a different column name
ERR_SCALE = 1.96        # e.g. 1.96 for ~95% CI, 1.0 for ±1 SE

# Base marker size (area in points^2, used for outer colored circle)
BASE_MARKER_SIZE = 60.0

# ========== More intuitive English labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min, uncapped)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min, uncapped)",
    "outpt_time_month_unc":  "Total travel time for outpatient visits, last month (min, uncapped)",
    "outpt_dist_single_unc": "Travel distance to last outpatient visit (km, uncapped)",
    "inp_dist_single_unc":   "Travel distance to last inpatient visit (km, uncapped)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All",
    "rural": "Rural",
    "urban": "Urban",
}

# ========== Helper: significance stars ==========
def stars_for_p(p):
    """Return significance stars based on p-value."""
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


# ========== Helper: draw marker with colored ring + white core ==========
def draw_sig_marker(ax, x, y, p, color, base_size=BASE_MARKER_SIZE, zorder=3):
    """
    Draw a circular marker whose fill style depends on p-value.

    Rules:
        p > 0.10      : colored ring only (white inside)
        0.05 < p <=.10: large white core
        0.001< p <=.05: medium white core
        p <= 0.001    : small white core (almost solid)
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        p = np.nan

    # Non-significant: ring only (no fill)
    if not np.isfinite(p) or p > 0.10:
        ax.scatter(
            [x], [y],
            s=base_size,
            facecolors="none",
            edgecolors=color,
            linewidths=1.0,
            zorder=zorder,
        )
        return

    # Significant: colored disk + white core (size depends on p)
    ax.scatter(
        [x], [y],
        s=base_size,
        facecolors=color,
        edgecolors=color,
        linewidths=0.8,
        zorder=zorder,
    )

    # White core radius as a fraction of outer radius
    if p > 0.05:        # 0.05 < p <= 0.10  (weak significance)
        inner_scale = 0.75
    elif p > 0.001:     # 0.001 < p <= 0.05 (moderate)
        inner_scale = 0.50
    else:               # p <= 0.001       (strong)
        inner_scale = 0.25

    # Size ~ radius^2
    inner_size = base_size * (inner_scale ** 2)

    ax.scatter(
        [x], [y],
        s=inner_size,
        facecolors="white",
        edgecolors="white",
        linewidths=0.0,
        zorder=zorder + 1,
    )


# ========== Read & filter: mechanism model only ==========
def load_mechanism_results():
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    # Keep only mechanism model: spec == "M~F"
    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    # Convert numeric columns
    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    # Drop invalid T or coefficients
    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])

    return df_mech


# ========== Plot for one mechanism group + sample ==========
def plot_one_group(df_mech, mech_group, sample="all"):
    """
    Plot one figure for a given mechanism group (mech_group) and sample:
      - x-axis: T
      - y-axis: Flood coefficient (Estimate)
      - one series per M_var in that group
      - markers styled by significance (colored ring + white core).
    """
    sub = df_mech[
        (df_mech[COL_GROUP] == mech_group) &
        (df_mech[COL_SAMPLE] == sample)
    ].copy()

    if sub.empty:
        print(f"[WARN] group={mech_group}, sample={sample} has no rows. Skip.")
        return

    # Keep and sort T
    sub = sub.dropna(subset=[COL_T, COL_EST])
    ts = sorted(sub[COL_T].unique())

    # y-axis range
    y_vals = sub[COL_EST]
    y_min = float(y_vals.min())
    y_max = float(y_vals.max())
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower
    star_offset = 0.04 * y_range

    # Color map across M_var within this group
    mvars = (
        sub[COL_MVAR]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    n_mvars = len(mvars)
    cmap = plt.cm.get_cmap("tab10", n_mvars)

    fig, ax = plt.subplots(figsize=(6.0, 4.0))

    for i, mvar in enumerate(mvars):
        sub_mv = sub[sub[COL_MVAR] == mvar].copy()
        if sub_mv.empty:
            continue

        sub_mv = sub_mv.sort_values(COL_T)
        x_vals = sub_mv[COL_T].values
        y_vals = sub_mv[COL_EST].values
        p_vals = sub_mv[COL_P].values

        label = MVAR_LABEL.get(mvar, mvar)
        color = cmap(i)

        # For legend: one dummy handle per series
        if CONNECT_POINTS:
            ax.plot(
                x_vals, y_vals,
                color=color, linewidth=1.0, alpha=0.7,
                label=label
            )
        else:
            # dummy point for legend (no line)
            ax.plot(
                [], [],  # no data
                marker="o", linestyle="none",
                color=color, label=label
            )

        # Optional error bars (line only, markers drawn separately)
        if SHOW_ERRORBAR and (ERR_COL in sub_mv.columns):
            se = pd.to_numeric(sub_mv[ERR_COL], errors="coerce").values
            if np.isfinite(se).any():
                yerr = ERR_SCALE * se
                ax.errorbar(
                    x_vals, y_vals,
                    yerr=yerr,
                    fmt="none",
                    ecolor=color,
                    elinewidth=0.8,
                    capsize=3,
                    zorder=2,
                )

        # Draw markers + stars for each point
        for xi, yi, pi in zip(x_vals, y_vals, p_vals):
            # colored ring + white core depending on p
            draw_sig_marker(ax, xi, yi, pi, color, base_size=BASE_MARKER_SIZE)

            # significance stars above the marker
            s = stars_for_p(pi)
            if s:
                ax.text(
                    xi, yi + star_offset,
                    s,
                    ha="center", va="bottom",
                    fontsize=9,
                    color=color,
                )

    # Horizontal zero line
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)

    # Axes and title
    ax.set_xlabel("Return period T (years)")
    ax.set_ylabel("Coefficient of Flood")

    group_title = GROUP_LABEL.get(mech_group, mech_group)
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"{group_title} (sample: {sample_title})")

    # x-axis ticks
    ax.set_xticks(ts)
    ax.set_xlim(min(ts) - 1, max(ts) + 1)

    ax.set_ylim(y_lower, y_upper)

    # Legend at bottom
    ax.legend(
        fontsize=8,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.15),
        ncol=1,
        frameon=False
    )

    plt.tight_layout()

    # Save PNG + SVG
    fn_base = f"mech_MF_{sample}_{mech_group}.png"
    out_png = OUT_DIR / fn_base
    out_svg = OUT_DIR / fn_base.replace(".png", ".svg")

    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    group_list = [
        "oop_individual",
        "oop_household",
        "util_any",
        "util_intensity",
        "access_time",
        "access_distance",
        "access_transport",
    ]

    sample_list = ["all", "rural", "urban"]

    for g in group_list:
        for s in sample_list:
            print(f"\n[PLOT] group={g}, sample={s}")
            plot_one_group(df_mech, mech_group=g, sample=s)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# """
# Mechanism models only (spec == "M~F"):

# For each mechanism group (7 groups) and sample (all / rural / urban),
# Original notebook comment normalized for the public code archive.

#     - Y-axis: mechanism variables (M_var) within that group
#     - X-axis: coefficient of Flood (M ~ Flood + controls)
#     - One horizontal segment per mechanism:
#           segment range  = [min(Estimate across T), max(Estimate across T)]
#           central point  = mean(Estimate across T)

# The vertical order of mechanisms follows a fixed global ordering
# (from top to bottom, consistent across groups).

# Output:
#     all   -> E:\impact_assessment_child_order\data\figure3\mechanism_figures\all
#     rural -> E:\impact_assessment_child_order\data\figure3\mechanism_figures\rural
#     urban -> E:\impact_assessment_child_order\data\figure3\mechanism_figures\urban

# Group colors (GROUP_BASE_COLORS) are aligned with the
# Original notebook comment normalized for the public code archive.
# """

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# ========== Paths ==========
BASE_OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")

CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

# Original notebook comment normalized for the public code archive.
SAMPLE_OUT_DIRS = {
    "all":   BASE_OUT_DIR / "all",
    "rural": BASE_OUT_DIR / "rural",
    "urban": BASE_OUT_DIR / "urban",
}
for _p in SAMPLE_OUT_DIRS.values():
    _p.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Original notebook comment normalized for the public code archive.
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# Original notebook comment normalized for the public code archive.
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# =============================================================================
GROUP_BASE_COLORS = {
    "oop_individual":   "#a6cee3",  # light blue
    "oop_household":    "#1f78b4",  # blue
    "util_any":         "#b2df8a",  # light green
    "util_intensity":   "#33a02c",  # green
    "access_time":      "#fb9a99",  # light red
    "access_distance":  "#e31a1c",  # red
    "access_transport": "#fdbf6f",  # orange
}

# =============================================================================
MVAR_ORDER = [
    "inp_last_oop",          # Inpatient OOP, last admission (CNY)
    "inp_year_oop",          # Inpatient OOP, last year (CNY)
    "outpt_last_oop",        # Outpatient OOP, last visit (CNY)
    "outpt_month_oop",       # Outpatient OOP, last month (CNY)
    "self_treat_oop",        # Self-treatment OOP, last month (CNY)
    "hh_health_year",        # Household total health spending, last year (CNY)
    "hh_med_year",           # Household medical spending, last year (CNY)
    "has_outpt",             # Any outpatient visit, last month (0/1)
    "inp_any",               # Any inpatient admission, last year (0/1)
    "ed005_visits",          # Number of outpatient visits, last month
    "inp_last_total",        # Length of stay, last admission (days)
    "inp_year_total",        # Number of inpatient admissions, last year
    "self_treat_total",      # Number of self-treatments, last month
    "inp_time_single_unc",   # Travel time to last inpatient visit (min)
    "outpt_time_month_unc",  # Total travel time outpatient, last month (min)
    "outpt_time_single_unc", # Travel time to last outpatient visit (min)
    "inp_dist_single_unc",   # Distance to last inpatient visit (km)
    "outpt_dist_single_unc", # Distance to last outpatient visit (km)
    "inp_walk",              # Walked to last inpatient visit (0/1)
    "outpt_homevisit",       # Received outpatient home visit (0/1)
    "outpt_walk",            # Walked to last outpatient visit (0/1)
]
MVAR_ORDER_INDEX = {m: i for i, m in enumerate(MVAR_ORDER)}


# =============================================================================
def load_mechanism_results() -> pd.DataFrame:
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])
    df_mech = df_mech[df_mech[COL_T].isin(T_ORDER)].copy()

    return df_mech


# =============================================================================
def plot_group_horizontal(df_mech: pd.DataFrame, mech_group: str, sample: str) -> None:
    """
    For a given mechanism group and sample, draw a horizontal forest-style plot:
        each mechanism variable -> one horizontal bar (min..max) + center dot (mean),
        with vertical order determined by MVAR_ORDER (top to bottom).
    """
    sub = df_mech[
        (df_mech[COL_GROUP] == mech_group) &
        (df_mech[COL_SAMPLE] == sample)
    ].copy()

    if sub.empty:
        print(f"[WARN] group={mech_group}, sample={sample} has no rows. Skip.")
        return

    # =============================================================================
    stats = (
        sub.groupby(COL_MVAR)[COL_EST]
        .agg(mean="mean", min="min", max="max")
        .reset_index()
    )

    # Original notebook comment normalized for the public code archive.
    stats["order"] = stats[COL_MVAR].map(MVAR_ORDER_INDEX)
    stats = stats.dropna(subset=["order"]).sort_values("order")

    mvars = stats[COL_MVAR].tolist()
    n = len(mvars)
    if n == 0:
        print(f"[WARN] group={mech_group}, sample={sample} has no M_var in MVAR_ORDER. Skip.")
        return

    y_pos = np.arange(n)

    mean_vals = stats["mean"].values
    min_vals  = stats["min"].values
    max_vals  = stats["max"].values

    # Original notebook comment normalized for the public code archive.
    x_min = float(min(min_vals))
    x_max = float(max(max_vals))
    if not np.isfinite(x_min) or not np.isfinite(x_max):
        x_min, x_max = -0.5, 0.5
    pad = 0.15 * (x_max - x_min if x_max > x_min else 1.0)
    x_lower, x_upper = x_min - pad, x_max + pad

    color = GROUP_BASE_COLORS.get(mech_group, "#333333")

    fig_height = max(2.5, 0.4 * n)
    fig, ax = plt.subplots(figsize=(6.0, fig_height))

    # =============================================================================
    for i in range(n):
        y = y_pos[i]
        mn = min_vals[i]
        mx = max_vals[i]
        mu = mean_vals[i]

        ax.hlines(
            y,
            xmin=mn,
            xmax=mx,
            color=color,
            linewidth=2.0,
            zorder=2,
        )

        ax.scatter(
            [mu],
            [y],
            s=30,
            facecolors="white",
            edgecolors=color,
            linewidths=1.2,
            zorder=3,
        )

    # Original notebook comment normalized for the public code archive.
    ax.axvline(0.0, color="grey", linestyle="--", linewidth=1.0, zorder=1)

    # Original notebook comment normalized for the public code archive.
    y_labels = [MVAR_LABEL.get(m, m) for m in mvars]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.invert_yaxis()

    # Original notebook comment normalized for the public code archive.
    ax.set_xlim(x_lower, x_upper)
    ax.set_xlabel("Coefficient of Flood (M ~ Flood + controls)")

    group_title = GROUP_LABEL.get(mech_group, mech_group)
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"{group_title}  —  {sample_title}", fontsize=11)

    plt.tight_layout()

    out_dir = SAMPLE_OUT_DIRS.get(sample, BASE_OUT_DIR)
    fn_base = f"mech_MF_horizontal_{sample}_{mech_group}.png"
    out_png = out_dir / fn_base
    out_svg = out_dir / fn_base.replace(".png", ".svg")

    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    group_list = GROUP_ORDER
    sample_list = ["all", "rural", "urban"]

    for g in group_list:
        for s in sample_list:
            print(f"\n[PLOT] group={g}, sample={s}")
            plot_group_horizontal(df_mech, mech_group=g, sample=s)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism models only (spec == "M~F"):

Panel plots of flood coefficients by return period T,
for 7 mechanism groups stacked in one figure.

- X-axis: 6 return periods (2, 5, 10, 20, 50, 100), equally spaced as categories
- Y-axis: coefficient of Flood (M ~ Flood + controls), separate scale per row
- One series per mechanism variable (M_var) within each group
- Markers use "colored ring + white core" style to encode significance:
      p > 0.10      : colored ring only (white inside)
      0.05 < p ≤0.10: large white core
      0.001< p ≤0.05: medium white core
      p ≤ 0.001     : small white core (almost solid)
- Points are connected with lines (line width configurable)
- Within each group, colors are similar (different shades of one base color);
  across groups, base colors differ. In total up to 21 distinct colors.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Return periods as ordered categories (equally spaced on x-axis)
T_ORDER = [2, 5, 10, 20, 50, 100]
T_POSITIONS = {t: i for i, t in enumerate(T_ORDER)}  # map T -> 0..5

# ========== Plotting options ==========
# Points are connected with lines (you can set to False if needed)
CONNECT_POINTS = True

# Line width for connecting segments
LINE_WIDTH = 1.8

# Whether to show vertical error bars (requires a standard error column)
SHOW_ERRORBAR = False        # default off
ERR_COL = "Std. Error"       # change if your CSV uses a different column name
ERR_SCALE = 1.96             # e.g. 1.96 for ~95% CI, 1.0 for ±1 SE

# Base marker size (outer colored circle)
BASE_MARKER_SIZE = 40.0

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# Order of mechanism groups in the panel
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# Original notebook comment normalized for the public code archive.
GROUP_BASE_COLORS = [
    "#a6cee3",  # group 1
    "#1f78b4",  # group 2
    "#b2df8a",  # group 3
    "#33a02c",  # group 4
    "#fb9a99",  # group 5
    "#e31a1c",  # group 6
    "#fdbf6f",  # group 7
]


# ========== Color helper ==========
def vary_color_within_group(base_color: str, idx: int, n: int):
    """
    Within one group, generate similar but distinct colors for each M_var.

    Strategy: only DARKEN the base color by different strengths, so
    colors will never become too light (washed out).

    base_color: hex string for the group
    idx: index of the variable in this group (0..n-1)
    n: total number of variables in this group
    """
    base_rgb = np.array(mcolors.to_rgb(base_color))

    if n <= 1:
        return base_rgb

    # darkness factor from 0 (no darkening) to MAX_DARKEN
    MAX_DARKEN = 0.45  # Original notebook comment normalized for the public code archive.
    factors = np.linspace(0.0, MAX_DARKEN, n)
    alpha = factors[idx]

    # mix with black: darker = base * (1 - alpha)
    new_rgb = base_rgb * (1.0 - alpha)
    new_rgb = np.clip(new_rgb, 0.0, 1.0)

    return new_rgb

# ========== Marker style helper ==========
def draw_sig_marker(ax, x, y, p, color,
                    base_size=BASE_MARKER_SIZE,
                    zorder=3):
    """
    Draw a circular marker whose fill style depends on p-value.

        p > 0.10      : colored ring only (white inside)
        0.05 < p ≤0.10: large white core
        0.001< p ≤0.05: medium white core
        p ≤ 0.001     : small white core (almost solid)
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        p = np.nan

    # Non-significant: ring only
    if (not np.isfinite(p)) or (p > 0.10):
        ax.scatter(
            [x], [y],
            s=base_size,
            facecolors="none",
            edgecolors=color,
            linewidths=1.0,
            zorder=zorder,
        )
        return

    # Significant: colored disk
    ax.scatter(
        [x], [y],
        s=base_size,
        facecolors=color,
        edgecolors=color,
        linewidths=0.8,
        zorder=zorder,
    )

    # White core size
    if p > 0.05:        # 0.05 < p ≤ 0.10
        inner_scale = 0.75
    elif p > 0.001:     # 0.001 < p ≤ 0.05
        inner_scale = 0.50
    else:               # p ≤ 0.001
        inner_scale = 0.25

    inner_size = base_size * (inner_scale ** 2)

    ax.scatter(
        [x], [y],
        s=inner_size,
        facecolors="white",
        edgecolors="white",
        linewidths=0.0,
        zorder=zorder + 1,
    )


# ========== Read & filter: mechanism model only ==========
def load_mechanism_results():
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])

    # Original notebook comment normalized for the public code archive.
    df_mech = df_mech[df_mech[COL_T].isin(T_ORDER)].copy()

    return df_mech


# ========== Panel: 7 groups in one figure for a given sample ==========
def plot_all_groups_panel(df_mech: pd.DataFrame, sample: str = "all") -> None:
    """
    Create a single figure with 7 stacked subplots (one per mechanism group)
    for a given sample ("all", "rural", "urban").
    """
    sub_sample = df_mech[df_mech[COL_SAMPLE] == sample].copy()
    if sub_sample.empty:
        print(f"[WARN] sample={sample} has no rows. Skip panel.")
        return

    n_groups = len(GROUP_ORDER)
    fig, axes = plt.subplots(
        nrows=n_groups,
        ncols=1,
        sharex=True,
        figsize=(7.0, 2.0 * n_groups),
    )

    if n_groups == 1:
        axes = [axes]

    for idx, mech_group in enumerate(GROUP_ORDER):
        ax = axes[idx]

        sub = sub_sample[sub_sample[COL_GROUP] == mech_group].copy()
        if sub.empty:
            ax.set_visible(False)
            print(f"[WARN] group={mech_group}, sample={sample} has no rows.")
            continue

        # Map T to equally spaced positions
        sub = sub.dropna(subset=[COL_T, COL_EST])
        sub["T_pos"] = sub[COL_T].map(T_POSITIONS)

        # y-axis range per group
        y_vals = sub[COL_EST]
        y_min = float(y_vals.min())
        y_max = float(y_vals.max())
        if not np.isfinite(y_min) or not np.isfinite(y_max):
            y_min, y_max = -0.5, 0.5
        pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
        y_lower, y_upper = y_min - pad, y_max + pad

        # Color palette for this group
        mvars = (
            sub[COL_MVAR]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        n_mvars = len(mvars)
        base_color = GROUP_BASE_COLORS[idx % len(GROUP_BASE_COLORS)]

        for j, mvar in enumerate(mvars):
            sub_mv = sub[sub[COL_MVAR] == mvar].copy()
            if sub_mv.empty:
                continue

            sub_mv = sub_mv.sort_values("T_pos")
            x_vals = sub_mv["T_pos"].values
            y_vals = sub_mv[COL_EST].values
            p_vals = sub_mv[COL_P].values

            color = vary_color_within_group(base_color, j, n_mvars)
            label = MVAR_LABEL.get(mvar, mvar)

            # Original notebook comment normalized for the public code archive.
            if CONNECT_POINTS:
                ax.plot(
                    x_vals, y_vals,
                    color=color,
                    linewidth=LINE_WIDTH,
                    alpha=0.9,
                    label=label,
                    zorder=2,
                )
            else:
                # Original notebook comment normalized for the public code archive.
                ax.plot(
                    [], [],
                    marker="o",
                    linestyle="none",
                    color=color,
                    label=label,
                )

            # Optional error bars
            if SHOW_ERRORBAR and (ERR_COL in sub_mv.columns):
                se = pd.to_numeric(sub_mv[ERR_COL], errors="coerce").values
                if np.isfinite(se).any():
                    yerr = ERR_SCALE * se
                    ax.errorbar(
                        x_vals, y_vals,
                        yerr=yerr,
                        fmt="none",
                        ecolor=color,
                        elinewidth=0.6,
                        capsize=2,
                        zorder=2,
                    )

            # Original notebook comment normalized for the public code archive.
            for xi, yi, pi in zip(x_vals, y_vals, p_vals):
                draw_sig_marker(ax, xi, yi, pi, color)

        # Horizontal zero line
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)

        # Y label and group title
        ax.set_ylabel("Coef.", fontsize=8)
        group_title = GROUP_LABEL.get(mech_group, mech_group)
        ax.set_title(group_title, loc="left", fontsize=9)

        ax.set_ylim(y_lower, y_upper)

        # Legend per row
        ax.legend(
            fontsize=7,
            loc="upper right",
            frameon=False,
            ncol=1,
        )

        # Hide x tick labels except bottom row
        if idx < n_groups - 1:
            ax.tick_params(labelbottom=False)

    # Shared x-axis: equally spaced 0..5
    axes[-1].set_xlabel("Return period T (years)")
    axes[-1].set_xticks(range(len(T_ORDER)))
    axes[-1].set_xticklabels(T_ORDER)
    axes[-1].set_xlim(-0.5, len(T_ORDER) - 0.5)

    sample_title = SAMPLE_LABEL.get(sample, sample)
    fig.suptitle(
        f"Mechanism model: M ~ Flood  (sample: {sample_title})",
        fontsize=12,
        y=0.99,
    )

    plt.tight_layout(rect=[0.05, 0.03, 0.97, 0.96])

    out_png = OUT_DIR / f"panel_MF_{sample}_all_groups_equalX.png"
    out_svg = OUT_DIR / f"panel_MF_{sample}_all_groups_equalX.svg"

    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PANEL] sample={sample}")
        plot_all_groups_panel(df_mech, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism models only (spec == "M~F"):

Panel plots of flood coefficients by return period T,
for 7 mechanism groups stacked in one figure.

- X-axis: 6 return periods (2, 5, 10, 20, 50, 100), equally spaced as categories
- Y-axis: coefficient of Flood (M ~ Flood + controls), separate scale per row
- One series per mechanism variable (M_var) within each group
- Markers encode significance:
      p > 0.05      : hollow circle (colored edge, no fill)
      p ≤ 0.05      : solid circle (filled)
- Points are connected with lines (line width configurable)
- Within each group, colors are similar (different shades of one base color);
  across groups, base colors differ. In total up to 21 distinct colors.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Return periods as ordered categories (equally spaced on x-axis)
T_ORDER = [2, 5, 10, 20, 50, 100]
T_POSITIONS = {t: i for i, t in enumerate(T_ORDER)}  # map T -> 0..5

# ========== Plotting options ==========
CONNECT_POINTS = True          # whether to connect markers
LINE_WIDTH = 1.8               # line width

SHOW_ERRORBAR = False          # vertical error bars
ERR_COL = "Std. Error"
ERR_SCALE = 1.96

BASE_MARKER_SIZE = 40.0        # marker area

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# Order of mechanism groups in the panel
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# 7 base colors (one per group)
GROUP_BASE_COLORS = [
    "#a6cee3",  # group 1
    "#1f78b4",  # group 2
    "#b2df8a",  # group 3
    "#33a02c",  # group 4
    "#fb9a99",  # group 5
    "#e31a1c",  # group 6
    "#fdbf6f",  # group 7
]


# ========== Color helper ==========
def vary_color_within_group(base_color: str, idx: int, n: int):
    """
    Within one group, generate similar but distinct colors for each M_var.

    Strategy: only DARKEN the base color by different strengths, so
    colors will never become too light (washed out).
    """
    base_rgb = np.array(mcolors.to_rgb(base_color))

    if n <= 1:
        return base_rgb

    MAX_DARKEN = 0.45  # higher -> darker
    factors = np.linspace(0.0, MAX_DARKEN, n)
    alpha = factors[idx]

    new_rgb = base_rgb * (1.0 - alpha)  # mix with black
    new_rgb = np.clip(new_rgb, 0.0, 1.0)

    return new_rgb


# ========== Marker style helper ==========
def draw_sig_marker(ax, x, y, p, color,
                    base_size=BASE_MARKER_SIZE,
                    zorder=3):
    """
    Draw a circular marker whose fill style depends on p-value.

        p > 0.05      : hollow circle (colored edge, no fill)
        p ≤ 0.05      : solid circle (filled)
    """
    try:
        p = float(p)
    except (TypeError, ValueError):
        p = np.nan

    # Non-significant: hollow
    if (not np.isfinite(p)) or (p > 0.05):
        ax.scatter(
            [x], [y],
            s=base_size,
            facecolors="none",
            edgecolors=color,
            linewidths=1.0,
            zorder=zorder,
        )
        return

    # Significant: solid
    ax.scatter(
        [x], [y],
        s=base_size,
        facecolors=color,
        edgecolors=color,
        linewidths=0.8,
        zorder=zorder,
    )


# ========== Read & filter: mechanism model only ==========
def load_mechanism_results():
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])

    # keep only specified return periods
    df_mech = df_mech[df_mech[COL_T].isin(T_ORDER)].copy()

    return df_mech


# ========== Panel: 7 groups in one figure for a given sample ==========
def plot_all_groups_panel(df_mech: pd.DataFrame, sample: str = "all") -> None:
    """
    Create a single figure with 7 stacked subplots (one per mechanism group)
    for a given sample ("all", "rural", "urban").
    """
    sub_sample = df_mech[df_mech[COL_SAMPLE] == sample].copy()
    if sub_sample.empty:
        print(f"[WARN] sample={sample} has no rows. Skip panel.")
        return

    n_groups = len(GROUP_ORDER)
    fig, axes = plt.subplots(
        nrows=n_groups,
        ncols=1,
        sharex=True,
        figsize=(7.0, 2.0 * n_groups),
    )

    if n_groups == 1:
        axes = [axes]

    for idx, mech_group in enumerate(GROUP_ORDER):
        ax = axes[idx]

        sub = sub_sample[sub_sample[COL_GROUP] == mech_group].copy()
        if sub.empty:
            ax.set_visible(False)
            print(f"[WARN] group={mech_group}, sample={sample} has no rows.")
            continue

        # Map T to equally spaced positions
        sub = sub.dropna(subset=[COL_T, COL_EST])
        sub["T_pos"] = sub[COL_T].map(T_POSITIONS)

        # y-axis range per group (larger padding -> visually flatter curves)
        y_vals = sub[COL_EST]
        y_min = float(y_vals.min())
        y_max = float(y_vals.max())
        if not np.isfinite(y_min) or not np.isfinite(y_max):
            y_min, y_max = -0.5, 0.5
        pad = 0.3 * (y_max - y_min if y_max > y_min else 1.0)  # 0.3 instead of 0.1
        y_lower, y_upper = y_min - pad, y_max + pad

        # Color palette for this group
        mvars = (
            sub[COL_MVAR]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        n_mvars = len(mvars)
        base_color = GROUP_BASE_COLORS[idx % len(GROUP_BASE_COLORS)]

        for j, mvar in enumerate(mvars):
            sub_mv = sub[sub[COL_MVAR] == mvar].copy()
            if sub_mv.empty:
                continue

            sub_mv = sub_mv.sort_values("T_pos")
            x_vals = sub_mv["T_pos"].values
            y_vals = sub_mv[COL_EST].values
            p_vals = sub_mv[COL_P].values

            color = vary_color_within_group(base_color, j, n_mvars)
            # label = MVAR_LABEL.get(mvar, mvar)  # legend no longer shown

            # connect points
            if CONNECT_POINTS:
                ax.plot(
                    x_vals, y_vals,
                    color=color,
                    linewidth=LINE_WIDTH,
                    alpha=0.9,
                    zorder=2,
                )

            # Optional error bars
            if SHOW_ERRORBAR and (ERR_COL in sub_mv.columns):
                se = pd.to_numeric(sub_mv[ERR_COL], errors="coerce").values
                if np.isfinite(se).any():
                    yerr = ERR_SCALE * se
                    ax.errorbar(
                        x_vals, y_vals,
                        yerr=yerr,
                        fmt="none",
                        ecolor=color,
                        elinewidth=0.6,
                        capsize=2,
                        zorder=2,
                    )

            # markers with simplified significance encoding
            for xi, yi, pi in zip(x_vals, y_vals, p_vals):
                draw_sig_marker(ax, xi, yi, pi, color)

        # zero line
        ax.axhline(0, color="grey", linestyle="--", linewidth=0.8)

        # y-axis on the right
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.set_ylabel("Coef.", fontsize=8)

        ax.set_ylim(y_lower, y_upper)

        # no per-panel title, no legend
        # ax.legend(...) removed

        # hide x tick labels except bottom row
        if idx < n_groups - 1:
            ax.tick_params(labelbottom=False)

    # Shared x-axis: equally spaced 0..5
    axes[-1].set_xlabel("Return period T (years)")
    axes[-1].set_xticks(range(len(T_ORDER)))
    axes[-1].set_xticklabels(T_ORDER)
    axes[-1].set_xlim(-0.5, len(T_ORDER) - 0.5)

    # no suptitle
    # fig.suptitle(...) removed

    plt.tight_layout(rect=[0.07, 0.03, 0.97, 0.97])

    out_png = OUT_DIR / f"panel_MF_{sample}_all_groups_equalX.png"
    out_svg = OUT_DIR / f"panel_MF_{sample}_all_groups_equalX.svg"

    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PANEL] sample={sample}")
        plot_all_groups_panel(df_mech, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mechanism models only (spec == "M~F"):

For each sample (all / rural / urban), draw a panel with 7 stacked subplots
(one per mechanism group). In each subplot:

    - Y-axis: mechanism variables (M_var) within that group (categories, vertical list)
    - X-axis: coefficient of Flood (M ~ Flood + controls)
    - One horizontal bar per mechanism:
          bar center  = mean(Estimate across T = 2,5,10,20,50,100)
          error bar   = [min(Estimate), max(Estimate)] across T
            (i.e. xerr from min to max)
    - Bars in the same group share the same color; groups have different colors.

No titles, no legends.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"

# Original notebook comment normalized for the public code archive.
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# Original notebook comment normalized for the public code archive.
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# Original notebook comment normalized for the public code archive.
GROUP_BASE_COLORS = {
    "oop_individual":   "#a6cee3",
    "oop_household":    "#1f78b4",
    "util_any":         "#b2df8a",
    "util_intensity":   "#33a02c",
    "access_time":      "#fb9a99",
    "access_distance":  "#e31a1c",
    "access_transport": "#fdbf6f",
}


# =============================================================================
def load_mechanism_results() -> pd.DataFrame:
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique group = {df[COL_GROUP].unique()}")
    print(f"[INFO] unique sample= {df[COL_SAMPLE].unique()}")

    df_mech = df[df[COL_SPEC] == "M~F"].copy()
    print(f"[INFO] mechanism subset shape = {df_mech.shape}")

    df_mech[COL_T]   = pd.to_numeric(df_mech[COL_T], errors="coerce")
    df_mech[COL_EST] = pd.to_numeric(df_mech[COL_EST], errors="coerce")
    df_mech[COL_P]   = pd.to_numeric(df_mech[COL_P], errors="coerce")

    df_mech = df_mech.dropna(subset=[COL_T, COL_EST])

    # Original notebook comment normalized for the public code archive.
    df_mech = df_mech[df_mech[COL_T].isin(T_ORDER)].copy()

    return df_mech


# =============================================================================
def plot_barh_panel_for_sample(df_mech: pd.DataFrame, sample: str = "all") -> None:
    """Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub_sample = df_mech[df_mech[COL_SAMPLE] == sample].copy()
    if sub_sample.empty:
        print(f"[WARN] sample={sample} has no rows. Skip.")
        return

    n_groups = len(GROUP_ORDER)
    fig_height = 2.0 * n_groups
    fig, axes = plt.subplots(
        nrows=n_groups,
        ncols=1,
        figsize=(7.0, fig_height),
        sharex=True,    # Original notebook comment normalized for the public code archive.
    )

    if n_groups == 1:
        axes = [axes]

    for idx, g in enumerate(GROUP_ORDER):
        ax = axes[idx]
        sub_g = sub_sample[sub_sample[COL_GROUP] == g].copy()
        if sub_g.empty:
            ax.set_visible(False)
            print(f"[WARN] group={g}, sample={sample} has no rows.")
            continue

        # Original notebook comment normalized for the public code archive.
        stats = (
            sub_g.groupby(COL_MVAR)[COL_EST]
            .agg(["mean", "min", "max"])
            .reset_index()
        )

        # Original notebook comment normalized for the public code archive.
        stats = stats.sort_values(COL_MVAR)
        mvars = stats[COL_MVAR].tolist()
        n_mvars = len(mvars)

        y = np.arange(n_mvars)
        mean_vals = stats["mean"].values
        min_vals  = stats["min"].values
        max_vals  = stats["max"].values

        # Original notebook comment normalized for the public code archive.
        xerr_left  = mean_vals - min_vals
        xerr_right = max_vals - mean_vals
        xerr = np.vstack([xerr_left, xerr_right])

        # Original notebook comment normalized for the public code archive.
        x_min = float(min(min_vals))
        x_max = float(max(max_vals))
        if not np.isfinite(x_min) or not np.isfinite(x_max):
            x_min, x_max = -0.5, 0.5
        pad = 0.2 * (x_max - x_min if x_max > x_min else 1.0)
        ax.set_xlim(x_min - pad, x_max + pad)

        # Original notebook comment normalized for the public code archive.
        color = GROUP_BASE_COLORS.get(g, "#808080")

        # Original notebook comment normalized for the public code archive.
        bar_height = 0.6
        ax.barh(
            y,
            mean_vals,
            height=bar_height,
            color=color,
            edgecolor="black",
            linewidth=0.7,
            zorder=2,
        )

        ax.errorbar(
            mean_vals,
            y,
            xerr=xerr,
            fmt="none",
            ecolor="black",
            elinewidth=0.8,
            capsize=3,
            zorder=3,
        )

        # Original notebook comment normalized for the public code archive.
        y_labels = [MVAR_LABEL.get(m, m) for m in mvars]
        ax.set_yticks(y)
        ax.set_yticklabels(y_labels)

        # Original notebook comment normalized for the public code archive.
        ax.invert_yaxis()

        # Original notebook comment normalized for the public code archive.
        ax.axvline(0, color="grey", linestyle="--", linewidth=0.6, zorder=1)

        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        # ax.text(ax.get_xlim()[1], -0.5, GROUP_LABEL.get(g, g),
        #         ha="right", va="bottom", fontsize=8)

        # Original notebook comment normalized for the public code archive.
        if idx < n_groups - 1:
            ax.tick_params(labelbottom=False)

    # Original notebook comment normalized for the public code archive.
    axes[-1].set_xlabel("Coefficient of Flood (mechanism model M ~ Flood + controls)")

    # Original notebook comment normalized for the public code archive.
    plt.tight_layout(rect=[0.08, 0.03, 0.98, 0.98])

    out_png = OUT_DIR / f"panel_barh_MF_{sample}_groups.png"
    out_svg = OUT_DIR / f"panel_barh_MF_{sample}_groups.svg"
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df_mech = load_mechanism_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PANEL-BARH] sample={sample}")
        plot_barh_panel_for_sample(df_mech, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\health_mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"
COL_YVAR   = "Y_var"

# Return periods
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# 7 mechanism groups in desired order
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# base colors for the 7 groups (from your palette)
GROUP_BASE_COLORS = {
    "oop_individual":   "#a6cee3",
    "oop_household":    "#1f78b4",
    "util_any":         "#b2df8a",
    "util_intensity":   "#33a02c",
    "access_time":      "#fb9a99",
    "access_distance":  "#e31a1c",
    "access_transport": "#fdbf6f",
}

# ========== Color helpers ==========
def lighten_color(color, amount):
    """
    Lighten a color by mixing with white.

    amount=0.0 -> original color
    amount=1.0 -> white
    """
    rgb = np.array(mcolors.to_rgb(color))
    white = np.array([1.0, 1.0, 1.0])
    new_rgb = rgb + (white - rgb) * amount
    new_rgb = np.clip(new_rgb, 0.0, 1.0)
    return new_rgb


def palette_for_group(base_color: str):
    """
    For one group, generate a 6-color palette for T_ORDER:

        small T (2)  -> lighter
        large T (100)-> darker (close to base_color)

    We use lightening factors from 0.5 down to 0.
    """
    n = len(T_ORDER)
    amounts = np.linspace(0.5, 0.0, n)  # 2->0.5 (lightest), 100->0.0 (original)
    return [lighten_color(base_color, a) for a in amounts]


# ========== Data loader ==========
def load_health_mech_results() -> pd.DataFrame:
    """Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique Y_var = {df[COL_YVAR].unique()}")

    df = df[(df[COL_SPEC] == "H~F+M") & (df[COL_YVAR] == "health_z")].copy()
    print(f"[INFO] H~F+M health subset shape = {df.shape}")

    # Ensure numeric
    df[COL_T]   = pd.to_numeric(df[COL_T], errors="coerce")
    df[COL_EST] = pd.to_numeric(df[COL_EST], errors="coerce")
    df[COL_P]   = pd.to_numeric(df[COL_P], errors="coerce")

    df = df.dropna(subset=[COL_T, COL_EST])
    df = df[df[COL_T].isin(T_ORDER)].copy()

    return df


# ========== Plotter for one sample ==========
def plot_health_mech_bars(df: pd.DataFrame, sample: str = "all") -> None:
    """
    Horizontal bar plot for a given sample ("all", "rural", "urban"):

        y: 21 mechanisms grouped into 7 groups
        x: coefficient of Flood (H~F+M)
        within each mechanism: 6 bars for T=2,5,10,20,50,100
    """
    sub = df[df[COL_SAMPLE] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows. Skip.")
        return

    # Build ordered list of (group, M_var)
    mech_list = []
    for g in GROUP_ORDER:
        g_sub = sub[sub[COL_GROUP] == g]
        if g_sub.empty:
            continue
        mvars = (
            g_sub[COL_MVAR]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        for m in mvars:
            mech_list.append((g, m))

    if not mech_list:
        print(f"[WARN] no mechanisms found for sample={sample}.")
        return

    n_mech = len(mech_list)

    # vertical layout parameters
    cluster_gap = 1.0          # distance between mechanism centers
    offsets = np.linspace(-0.25, 0.25, len(T_ORDER))  # vertical offsets within a mechanism
    bar_height = 0.08          # bar thickness

    # assign y-center for each mechanism
    y_centers = {}
    curr_y = 0.0
    for g, m in mech_list:
        y_centers[(g, m)] = curr_y
        curr_y += cluster_gap

    # determine x-range (common for all mechanisms in this sample)
    x_vals = sub[COL_EST].values
    x_min = float(np.nanmin(x_vals))
    x_max = float(np.nanmax(x_vals))
    if not np.isfinite(x_min) or not np.isfinite(x_max):
        x_min, x_max = -0.5, 0.5
    # symmetric around 0 with some padding
    max_abs = max(abs(x_min), abs(x_max))
    max_abs = max_abs * 1.1 if max_abs > 0 else 1.0
    x_lower, x_upper = -max_abs, max_abs

    # figure size
    fig_height = max(5.0, 0.35 * n_mech)
    fig, ax = plt.subplots(figsize=(8.0, fig_height))

    # Draw bars
    for g_idx, g in enumerate(GROUP_ORDER):
        # palette for this group (6 colors for 6 T)
        base_color = GROUP_BASE_COLORS.get(g, "#808080")
        palette = palette_for_group(base_color)
        t_to_color = {t: palette[i] for i, t in enumerate(T_ORDER)}

        for m_idx, m in enumerate([m for gg, m in mech_list if gg == g]):
            y_center = y_centers[(g, m)]
            sub_gm = sub[(sub[COL_GROUP] == g) & (sub[COL_MVAR] == m)].copy()
            if sub_gm.empty:
                continue

            # we want T in fixed order
            for t_index, t in enumerate(T_ORDER):
                sub_t = sub_gm[sub_gm[COL_T] == t]
                if sub_t.empty:
                    continue
                coef = float(sub_t[COL_EST].iloc[0])
                color = t_to_color[t]

                y = y_center + offsets[t_index]
                left = min(0.0, coef)
                width = abs(coef)

                ax.barh(
                    y,
                    width,
                    height=bar_height,
                    left=left,
                    color=color,
                    edgecolor="none",
                )

    # y-axis ticks: one per mechanism (on the centers)
    y_ticks = [y_centers[(g, m)] for (g, m) in mech_list]
    y_labels = [MVAR_LABEL.get(m, m) for (g, m) in mech_list]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    # reverse y-axis so first mechanism at top
    ax.invert_yaxis()

    # vertical separators between groups
    # (thin grey lines between last mechanism of group and next group)
    for g_idx, g in enumerate(GROUP_ORDER[:-1]):
        # find last mechanism index of this group and first of next group
        indices_g = [i for i, (gg, _) in enumerate(mech_list) if gg == g]
        if not indices_g:
            continue
        last_idx_g = max(indices_g)
        # find next group with any mechanism
        for g_next in GROUP_ORDER[g_idx + 1:]:
            indices_next = [i for i, (gg, _) in enumerate(mech_list) if gg == g_next]
            if indices_next:
                first_idx_next = min(indices_next)
                break
        else:
            continue

        y_bottom_g = y_centers[mech_list[last_idx_g]]
        y_top_next = y_centers[mech_list[first_idx_next]]
        y_sep = (y_bottom_g + y_top_next) / 2.0
        ax.axhline(y_sep, color="lightgrey", linewidth=0.6)

    # reference line at 0
    ax.axvline(0.0, color="grey", linestyle="--", linewidth=1.0)

    # x-axis
    ax.set_xlim(x_lower, x_upper)
    ax.set_xlabel("Coefficient of Flood (health-mechanism model H~F+M)")

    # title + legend
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"Flood coefficients by mechanism and return period (sample: {sample_title})")

    # Legend for return periods (use palette of the first group)
    base_color_legend = GROUP_BASE_COLORS[GROUP_ORDER[0]]
    palette_legend = palette_for_group(base_color_legend)
    handles = [
        plt.Line2D(
            [0], [0],
            color=palette_legend[i],
            linewidth=6,
            marker=None,
        )
        for i in range(len(T_ORDER))
    ]
    labels = [f"T = {t} years" for t in T_ORDER]
    ax.legend(
        handles,
        labels,
        fontsize=8,
        title="Return period",
        loc="lower right",
        frameon=False,
    )

    plt.tight_layout()

    out_png = OUT_DIR / f"health_mech_HFplusM_{sample}.png"
    out_svg = OUT_DIR / f"health_mech_HFplusM_{sample}.svg"
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df = load_health_mech_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PLOT] sample={sample}")
        plot_health_mech_bars(df, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\health_mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"
COL_YVAR   = "Y_var"

# Return periods
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# 7 mechanism groups in desired order
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# base colors for the 7 groups
GROUP_BASE_COLORS = {
    "oop_individual":   "#a6cee3",
    "oop_household":    "#1f78b4",
    "util_any":         "#b2df8a",
    "util_intensity":   "#33a02c",
    "access_time":      "#fb9a99",
    "access_distance":  "#e31a1c",
    "access_transport": "#fdbf6f",
}

# ========== Color helpers ==========
def adjust_color(base_color: str, delta: float):
    """
    Adjust luminance of base_color.

    delta > 0: lighten by mixing with white (amount in [0,1])
    delta < 0: darken by mixing with black (amount in [0,1])
    """
    base = np.array(mcolors.to_rgb(base_color))

    if delta >= 0:
        white = np.array([1.0, 1.0, 1.0])
        new = base + (white - base) * delta
    else:
        black = np.array([0.0, 0.0, 0.0])
        new = base + (black - base) * (-delta)

    new = np.clip(new, 0.0, 1.0)
    return new


def palette_for_group(base_color: str):
    """Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    n = len(T_ORDER)
    deltas = np.linspace(0.10, -0.10, n)  # 0.25, 0.15, 0.05, -0.05, -0.15, -0.20
    return [adjust_color(base_color, d) for d in deltas]


# ========== Data loader ==========
def load_health_mech_results() -> pd.DataFrame:
    """Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique Y_var = {df[COL_YVAR].unique()}")

    df = df[(df[COL_SPEC] == "H~F+M") & (df[COL_YVAR] == "health_z")].copy()
    print(f"[INFO] H~F+M health subset shape = {df.shape}")

    # Ensure numeric
    df[COL_T]   = pd.to_numeric(df[COL_T], errors="coerce")
    df[COL_EST] = pd.to_numeric(df[COL_EST], errors="coerce")
    df[COL_P]   = pd.to_numeric(df[COL_P], errors="coerce")

    df = df.dropna(subset=[COL_T, COL_EST])
    df = df[df[COL_T].isin(T_ORDER)].copy()

    return df


# ========== Plotter for one sample ==========
def plot_health_mech_bars(df: pd.DataFrame, sample: str = "all") -> None:
    """
    Horizontal bar plot for a given sample ("all", "rural", "urban"):

        y: 21 mechanisms grouped into 7 groups
        x: coefficient of Flood (H~F+M)
        within each mechanism: 6 bars for T=2,5,10,20,50,100

    Edge style:
        p > 0.05 -> dashed border
        p <=0.05 -> solid border
    """
    sub = df[df[COL_SAMPLE] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows. Skip.")
        return

    # Build ordered list of (group, M_var)
    mech_list = []
    for g in GROUP_ORDER:
        g_sub = sub[sub[COL_GROUP] == g]
        if g_sub.empty:
            continue
        mvars = (
            g_sub[COL_MVAR]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        for m in mvars:
            mech_list.append((g, m))

    if not mech_list:
        print(f"[WARN] no mechanisms found for sample={sample}.")
        return

    n_mech = len(mech_list)

    # vertical layout parameters
    cluster_gap = 1.0          # distance between mechanism centers
    offsets = np.linspace(-0.25, 0.25, len(T_ORDER))  # vertical offsets within a mechanism
    bar_height = 0.08          # bar thickness

    # assign y-center for each mechanism
    y_centers = {}
    curr_y = 0.0
    for g, m in mech_list:
        y_centers[(g, m)] = curr_y
        curr_y += cluster_gap

    # determine x-range (common for all mechanisms in this sample)
    x_vals = sub[COL_EST].values
    x_min = float(np.nanmin(x_vals))
    x_max = float(np.nanmax(x_vals))
    if not np.isfinite(x_min) or not np.isfinite(x_max):
        x_min, x_max = -0.5, 0.5
    # symmetric around 0 with some padding
    max_abs = max(abs(x_min), abs(x_max))
    max_abs = max_abs * 1.1 if max_abs > 0 else 1.0
    x_lower, x_upper = -max_abs, max_abs

    # figure size
    fig_height = max(5.0, 0.35 * n_mech)
    fig, ax = plt.subplots(figsize=(8.0, fig_height))

    # Draw bars
    for g_idx, g in enumerate(GROUP_ORDER):
        # palette for this group (6 colors for 6 T)
        base_color = GROUP_BASE_COLORS.get(g, "#808080")
        palette = palette_for_group(base_color)
        t_to_color = {t: palette[i] for i, t in enumerate(T_ORDER)}

        # Original notebook comment normalized for the public code archive.
        m_in_group = [m for gg, m in mech_list if gg == g]

        for m_idx, m in enumerate(m_in_group):
            y_center = y_centers[(g, m)]
            sub_gm = sub[(sub[COL_GROUP] == g) & (sub[COL_MVAR] == m)].copy()
            if sub_gm.empty:
                continue

            # we want T in fixed order
            for t_index, t in enumerate(T_ORDER):
                sub_t = sub_gm[sub_gm[COL_T] == t]
                if sub_t.empty:
                    continue

                coef = float(sub_t[COL_EST].iloc[0])
                p_val = float(sub_t[COL_P].iloc[0]) if not pd.isna(sub_t[COL_P].iloc[0]) else np.nan

                color = t_to_color[t]
                y = y_center + offsets[t_index]
                left = min(0.0, coef)
                width = abs(coef)

                # edge style by significance
                if (not np.isnan(p_val)) and (p_val <= 0.05):
                    edge_ls = "-"   # solid
                else:
                    edge_ls = "--"  # dashed

                ax.barh(
                    y,
                    width,
                    height=bar_height,
                    left=left,
                    color=color,
                    edgecolor=color,
                    linewidth=1.0,
                    linestyle=edge_ls,
                )

    # y-axis ticks: one per mechanism (on the centers)
    y_ticks = [y_centers[(g, m)] for (g, m) in mech_list]
    y_labels = [MVAR_LABEL.get(m, m) for (g, m) in mech_list]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    # reverse y-axis so first mechanism at top
    ax.invert_yaxis()

    # separators between groups (light grey lines)
    for g_idx, g in enumerate(GROUP_ORDER[:-1]):
        indices_g = [i for i, (gg, _) in enumerate(mech_list) if gg == g]
        if not indices_g:
            continue
        last_idx_g = max(indices_g)

        # find next group with any mechanism
        next_idx = None
        for g_next in GROUP_ORDER[g_idx + 1:]:
            indices_next = [i for i, (gg, _) in enumerate(mech_list) if gg == g_next]
            if indices_next:
                next_idx = min(indices_next)
                break
        if next_idx is None:
            continue

        y_bottom_g = y_centers[mech_list[last_idx_g]]
        y_top_next = y_centers[mech_list[next_idx]]
        y_sep = (y_bottom_g + y_top_next) / 2.0
        ax.axhline(y_sep, color="lightgrey", linewidth=0.6)

    # reference line at 0
    ax.axvline(0.0, color="grey", linestyle="--", linewidth=1.0)

    # x-axis
    ax.set_xlim(x_lower, x_upper)
    ax.set_xlabel("Coefficient of Flood (health–mechanism model H~F+M)")

    # title + legend
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"Flood coefficients by mechanism and return period (sample: {sample_title})")

    # Legend for return periods (use palette of the first group)
    base_color_legend = GROUP_BASE_COLORS[GROUP_ORDER[0]]
    palette_legend = palette_for_group(base_color_legend)
    handles = [
        plt.Line2D(
            [0], [0],
            color=palette_legend[i],
            linewidth=6,
            marker=None,
        )
        for i in range(len(T_ORDER))
    ]
    labels = [f"T = {t} years" for t in T_ORDER]
    ax.legend(
        handles,
        labels,
        fontsize=8,
        title="Return period",
        loc="lower right",
        frameon=False,
    )

    plt.tight_layout()

    out_png = OUT_DIR / f"health_mech_HFplusM_{sample}.png"
    out_svg = OUT_DIR / f"health_mech_HFplusM_{sample}.svg"
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df = load_health_mech_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PLOT] sample={sample}")
        plot_health_mech_bars(df, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ========== Global style ==========
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# ========== Paths ==========
CSV_PATH = Path(
    r"E:\impact_assessment_child_order\data\figure3"
) / "fe_mechanism2_full_results_aggByT_mech2_pid_provYear_cityCluster.csv"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\figure3\health_mechanism_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Column constants ==========
COL_SPEC   = "spec"
COL_GROUP  = "group"
COL_MVAR   = "M_var"
COL_SAMPLE = "sample"
COL_T      = "T"
COL_EST    = "Estimate"
COL_P      = "Pr(>|t|)"
COL_YVAR   = "Y_var"

# Return periods
T_ORDER = [2, 5, 10, 20, 50, 100]

# ========== Labels ==========
GROUP_LABEL = {
    "oop_individual":   "Out-of-pocket spending (individual)",
    "oop_household":    "Out-of-pocket spending (household)",
    "util_any":         "Any use of care",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

MVAR_LABEL = {
    "outpt_month_oop":       "Outpatient OOP, last month (CNY)",
    "inp_year_oop":          "Inpatient OOP, last year (CNY)",
    "self_treat_oop":        "Self-treatment OOP, last month (CNY)",
    "outpt_last_oop":        "Outpatient OOP, last visit (CNY)",
    "inp_last_oop":          "Inpatient OOP, last admission (CNY)",
    "hh_med_year":           "Household medical spending, last year (CNY)",
    "hh_health_year":        "Household total health spending, last year (CNY)",
    "has_outpt":             "Any outpatient visit, last month (0/1)",
    "inp_any":               "Any inpatient admission, last year (0/1)",
    "ed005_visits":          "Number of outpatient visits, last month",
    "inp_year_total":        "Number of inpatient admissions, last year",
    "inp_last_total":        "Length of stay, last admission (days)",
    "self_treat_total":      "Number of self-treatments, last month",
    "outpt_time_single_unc": "Travel time to last outpatient visit (min)",
    "inp_time_single_unc":   "Travel time to last inpatient visit (min)",
    "outpt_time_month_unc":  "Total travel time outpatient, last month (min)",
    "outpt_dist_single_unc": "Distance to last outpatient visit (km)",
    "inp_dist_single_unc":   "Distance to last inpatient visit (km)",
    "outpt_walk":            "Walked to last outpatient visit (0/1)",
    "inp_walk":              "Walked to last inpatient visit (0/1)",
    "outpt_homevisit":       "Received outpatient home visit (0/1)",
}

SAMPLE_LABEL = {
    "all":   "All respondents",
    "rural": "Rural only",
    "urban": "Urban only",
}

# 7 mechanism groups in desired order
GROUP_ORDER = [
    "oop_individual",
    "oop_household",
    "util_any",
    "util_intensity",
    "access_time",
    "access_distance",
    "access_transport",
]

# base colors for the 7 groups
GROUP_BASE_COLORS = {
    "oop_individual":   "#a6cee3",
    "oop_household":    "#1f78b4",
    "util_any":         "#b2df8a",
    "util_intensity":   "#33a02c",
    "access_time":      "#fb9a99",
    "access_distance":  "#e31a1c",
    "access_transport": "#fdbf6f",
}

# ========== Color helpers ==========
def adjust_color(base_color: str, delta: float):
    """
    Adjust luminance of base_color.

    delta > 0: lighten by mixing with white (amount in [0,1])
    delta < 0: darken by mixing with black (amount in [0,1])
    """
    base = np.array(mcolors.to_rgb(base_color))

    if delta >= 0:
        white = np.array([1.0, 1.0, 1.0])
        new = base + (white - base) * delta
    else:
        black = np.array([0.0, 0.0, 0.0])
        new = base + (black - base) * (-delta)

    new = np.clip(new, 0.0, 1.0)
    return new


# def palette_for_group(base_color: str):
#     """
#     For one group, generate a 6-color palette for T_ORDER:

#         T = 2   -> lighter
#         ...
#         T = 100 -> slightly darker than base color

#     Deltas from +0.10 (lighten) down to -0.10 (darken).
#     """
#     n = len(T_ORDER)
#     deltas = np.linspace(0.10, -0.10, n)
#     return [adjust_color(base_color, d) for d in deltas]

# def palette_for_group(base_color: str):
#     """
#     For one group, generate a 6-color palette for T_ORDER:
#         T = 2   -> lighter
#         ...
#         T = 100 -> darker

#     Use a stronger contrast than before.
#     """

#     deltas = [0.25, 0.12, 0.02, -0.10, -0.24, -0.38]
#     return [adjust_color(base_color, d) for d in deltas]

def palette_for_group(base_color: str):
    n = len(T_ORDER)
    deltas = np.linspace(0.30, -0.30, n)
    return [adjust_color(base_color, d) for d in deltas]


# ========== Data loader ==========
def load_health_mech_results() -> pd.DataFrame:
    """Archived notebook note for 07_figure3_elderly_health.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"[INFO] raw shape    = {df.shape}")
    print(f"[INFO] unique spec  = {df[COL_SPEC].unique()}")
    print(f"[INFO] unique Y_var = {df[COL_YVAR].unique()}")

    df = df[(df[COL_SPEC] == "H~F+M") & (df[COL_YVAR] == "health_z")].copy()
    print(f"[INFO] H~F+M health subset shape = {df.shape}")

    # Ensure numeric
    df[COL_T]   = pd.to_numeric(df[COL_T], errors="coerce")
    df[COL_EST] = pd.to_numeric(df[COL_EST], errors="coerce")
    df[COL_P]   = pd.to_numeric(df[COL_P], errors="coerce")

    df = df.dropna(subset=[COL_T, COL_EST])
    df = df[df[COL_T].isin(T_ORDER)].copy()

    return df


# ========== Plotter for one sample ==========
def plot_health_mech_bars(df: pd.DataFrame, sample: str = "all") -> None:
    """
    Horizontal bar plot for a given sample ("all", "rural", "urban"):

        y: 21 mechanisms grouped into 7 groups
        x: coefficient of Flood (H~F+M)
        within each mechanism: 6 bars for T=2,5,10,20,50,100

    Significance encoding:
        p <= 0.05 -> solid filled bar
        p > 0.05  -> hollow bar (border only)
    """
    sub = df[df[COL_SAMPLE] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows. Skip.")
        return

    # Build ordered list of (group, M_var)
    mech_list = []
    for g in GROUP_ORDER:
        g_sub = sub[sub[COL_GROUP] == g]
        if g_sub.empty:
            continue
        mvars = (
            g_sub[COL_MVAR]
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        for m in mvars:
            mech_list.append((g, m))

    if not mech_list:
        print(f"[WARN] no mechanisms found for sample={sample}.")
        return

    n_mech = len(mech_list)

    # vertical layout parameters
    cluster_gap = 1.2          # distance between mechanism centers
    offsets = np.linspace(-0.45, 0.45, len(T_ORDER))  # vertical offsets within a mechanism
    bar_height = 0.18          # bar thickness

    # assign y-center for each mechanism
    y_centers = {}
    curr_y = 0.0
    for g, m in mech_list:
        y_centers[(g, m)] = curr_y
        curr_y += cluster_gap

    # determine x-range (common for all mechanisms in this sample)
    x_vals = sub[COL_EST].values
    x_min = float(np.nanmin(x_vals))
    x_max = float(np.nanmax(x_vals))
    if not np.isfinite(x_min) or not np.isfinite(x_max):
        x_min, x_max = -0.5, 0.5
    # symmetric around 0 with some padding
    max_abs = max(abs(x_min), abs(x_max))
    max_abs = max_abs * 1.1 if max_abs > 0 else 1.0
    x_lower, x_upper = -max_abs, max_abs

    # figure size
    fig_height = max(5.0, 0.35 * n_mech)
    fig, ax = plt.subplots(figsize=(8.0, fig_height))

    # Draw bars
    for g_idx, g in enumerate(GROUP_ORDER):
        # palette for this group (6 colors for 6 T)
        base_color = GROUP_BASE_COLORS.get(g, "#808080")
        palette = palette_for_group(base_color)
        t_to_color = {t: palette[i] for i, t in enumerate(T_ORDER)}

        # all mechanisms in this group (in mech_list order)
        m_in_group = [m for gg, m in mech_list if gg == g]

        for m_idx, m in enumerate(m_in_group):
            y_center = y_centers[(g, m)]
            sub_gm = sub[(sub[COL_GROUP] == g) & (sub[COL_MVAR] == m)].copy()
            if sub_gm.empty:
                continue

            # fixed order of T
            for t_index, t in enumerate(T_ORDER):
                sub_t = sub_gm[sub_gm[COL_T] == t]
                if sub_t.empty:
                    continue

                coef = float(sub_t[COL_EST].iloc[0])
                p_raw = sub_t[COL_P].iloc[0]
                p_val = float(p_raw) if not pd.isna(p_raw) else np.nan

                color = t_to_color[t]
                y = y_center + offsets[t_index]
                left = min(0.0, coef)
                width = abs(coef)

                # significance: filled vs hollow
                if (not np.isnan(p_val)) and (p_val <= 0.05):
                    facecolor = color       # solid
                    edgecolor = "none"
                    linewidth = 0.0
                else:
                    facecolor = "none"      # hollow
                    edgecolor = color
                    linewidth = 1.2

                ax.barh(
                    y,
                    width,
                    height=bar_height,
                    left=left,
                    color=facecolor,      # fill
                    edgecolor=edgecolor,  # border
                    linewidth=linewidth,
                )

    # y-axis ticks: one per mechanism (on the centers)
    # y_ticks = [y_centers[(g, m)] for (g, m) in mech_list]
    # y_labels = [MVAR_LABEL.get(m, m) for (g, m) in mech_list]
    # ax.set_yticks(y_ticks)
    # ax.set_yticklabels(y_labels)

    # # reverse y-axis so first mechanism at top
    # ax.invert_yaxis()

    # y-axis ticks: one per mechanism (on the centers)
    y_ticks = [y_centers[(g, m)] for (g, m) in mech_list]
    y_labels = [MVAR_LABEL.get(m, m) for (g, m) in mech_list]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    
    # Original notebook comment normalized for the public code archive.
    y_min_bar = min(y_ticks) + np.min(offsets) - bar_height / 2
    y_max_bar = max(y_ticks) + np.max(offsets) + bar_height / 2
    y_pad = 0.03
    ax.set_ylim(y_min_bar - y_pad, y_max_bar + y_pad)
    ax.margins(y=0.05)
    
    # reverse y-axis so first mechanism at top
    ax.invert_yaxis()

    # separators between groups (light grey lines)
    for g_idx, g in enumerate(GROUP_ORDER[:-1]):
        indices_g = [i for i, (gg, _) in enumerate(mech_list) if gg == g]
        if not indices_g:
            continue
        last_idx_g = max(indices_g)

        # find next group with any mechanism
        next_idx = None
        for g_next in GROUP_ORDER[g_idx + 1:]:
            indices_next = [i for i, (gg, _) in enumerate(mech_list) if gg == g_next]
            if indices_next:
                next_idx = min(indices_next)
                break
        if next_idx is None:
            continue

        y_bottom_g = y_centers[mech_list[last_idx_g]]
        y_top_next = y_centers[mech_list[next_idx]]
        y_sep = (y_bottom_g + y_top_next) / 2.0
        ax.axhline(y_sep, color="lightgrey", linewidth=0.6)

    # reference line at 0
    ax.axvline(0.0, color="grey", linestyle="--", linewidth=1.0)

    # x-axis
    ax.set_xlim(x_lower, x_upper)
    ax.set_xlabel("Coefficient of Flood (health–mechanism model H~F+M)")

    # title + legend
    sample_title = SAMPLE_LABEL.get(sample, sample)
    ax.set_title(f"Flood coefficients by mechanism and return period (sample: {sample_title})")

    # Legend for return periods (use palette of the first group)
    base_color_legend = GROUP_BASE_COLORS[GROUP_ORDER[0]]
    palette_legend = palette_for_group(base_color_legend)
    handles = [
        plt.Line2D(
            [0], [0],
            color=palette_legend[i],
            linewidth=6,
            marker=None,
        )
        for i in range(len(T_ORDER))
    ]
    labels = [f"T = {t} years" for t in T_ORDER]
    ax.legend(
        handles,
        labels,
        fontsize=8,
        title="Return period",
        loc="lower right",
        frameon=False,
    )

    plt.tight_layout()

    out_png = OUT_DIR / f"health_mech_HFplusM_{sample}.png"
    out_svg = OUT_DIR / f"health_mech_HFplusM_{sample}.svg"
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] {out_png}")
    print(f"[SAVE] {out_svg}")

    plt.close(fig)


# ========== main ==========
def main():
    df = load_health_mech_results()

    for sample in ["all", "rural", "urban"]:
        print(f"\n[PLOT] sample={sample}")
        plot_health_mech_bars(df, sample=sample)


if __name__ == "__main__":
    main()
