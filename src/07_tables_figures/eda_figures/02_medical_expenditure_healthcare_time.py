#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
mpl.rcParams.update({
    "font.family": "Times New Roman",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "axes.labelsize": 20,    # Original notebook comment normalized for the public code archive.
    "axes.titlesize": 13,    # Original notebook comment normalized for the public code archive.
    "xtick.labelsize": 19,   # Original notebook comment normalized for the public code archive.
    "ytick.labelsize": 19,   # Original notebook comment normalized for the public code archive.
    "legend.fontsize": 18,   # Original notebook comment normalized for the public code archive.
})

# =============================================================================
BASE = Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
PANEL = BASE / "charls_health_mechanism2_with_Tall_5_10_20_30y.parquet"

OUT_DIR = BASE / "eda_mechanism2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
MECH_GROUPS = {
    "oop_individual": [
        "outpt_month_oop", "inp_year_oop", "self_treat_oop",
        "outpt_last_oop", "inp_last_oop",
    ],
    "oop_household": [
        "hh_med_year", "hh_health_year",
    ],
    "util_any": [
        "has_outpt", "inp_any",
    ],
    "util_intensity": [
        "ed005_visits", "inp_year_total", "inp_last_total", "self_treat_total",
    ],
    "access_time": [
        "outpt_time_single_unc", "inp_time_single_unc", "outpt_time_month_unc",
    ],
    "access_distance": [
        "outpt_dist_single_unc", "inp_dist_single_unc",
    ],
    "access_transport": [
        "outpt_walk", "inp_walk", "outpt_homevisit",
    ],
}
ALL_VARS = [v for vs in MECH_GROUPS.values() for v in vs]

# =============================================================================
MONEY_VARS = MECH_GROUPS["oop_individual"] + MECH_GROUPS["oop_household"]

# =============================================================================
BINARY_VARS = {
    "has_outpt", "inp_any",
    "outpt_walk", "inp_walk", "outpt_homevisit",
}

# =============================================================================
URBAN_NBS_COL = "urban_nbs"

# =============================================================================
NEG_AS_NA_GROUPS = {
    "oop_individual",
    "oop_household",
    "util_intensity",
    "access_time",
    "access_distance",
}


def clean_neg_to_nan(df, cols):
    for c in cols:
        if c in df.columns:
            df.loc[df[c] < 0, c] = np.nan
    return df


def mean_se_ci(s):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s)
    s = pd.to_numeric(s, errors="coerce").dropna()
    n = len(s)
    if n == 0:
        return np.nan, np.nan, 0
    mean = s.mean()
    std = s.std(ddof=1)
    se = std / np.sqrt(n) if n > 1 else 0.0
    return mean, se, n


def prep_df():
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_parquet(PANEL)

    keep = ["year", URBAN_NBS_COL] + ALL_VARS
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    # Original notebook comment normalized for the public code archive.
    neg_cols = []
    for g, vs in MECH_GROUPS.items():
        if g in NEG_AS_NA_GROUPS:
            neg_cols.extend([v for v in vs if v in df.columns])
    df = clean_neg_to_nan(df, neg_cols)

    # Original notebook comment normalized for the public code archive.
    if URBAN_NBS_COL not in df.columns:
        raise KeyError("未找到 urban_nbs，无法进行波次口径城乡划分。")

    df["urban_group_wave"] = (
        pd.to_numeric(df[URBAN_NBS_COL], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df


# =============================================================================
MONEY_MODE = "k"  # raw | k | wan | log1p


def make_money_transform(mode):
    if mode == "raw":
        return None, "CNY"
    if mode == "k":
        return (lambda s: s / 1000.0), "thousand CNY"
    if mode == "wan":
        return (lambda s: s / 10000.0), "10k CNY"
    if mode == "log1p":
        return (lambda s: np.log1p(s.where(s >= 0))), "log1p(CNY)"
    raise ValueError(f"Unknown money transform mode: {mode}")


def apply_transform(series, fn):
    s = pd.to_numeric(series, errors="coerce")
    if fn is None:
        return s
    out = fn(s)
    if isinstance(out, np.ndarray):
        out = pd.Series(out, index=s.index)
    return out


def build_summary_diff_subset(
    df,
    vars_subset,
    group_col="urban_group_wave",
    scale=1.0,
    money_mode=None,
):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    vars_present = [v for v in vars_subset if v in df.columns]
    rows = []

    money_fn = None
    money_unit = None
    if money_mode is not None:
        money_fn, money_unit = make_money_transform(money_mode)

    for var in vars_present:
        sub0 = df[df[group_col] == 0][var]  # rural
        sub1 = df[df[group_col] == 1][var]  # urban

        # Original notebook comment normalized for the public code archive.
        if money_mode is not None and var in MONEY_VARS:
            sub0 = apply_transform(sub0, money_fn)
            sub1 = apply_transform(sub1, money_fn)

        m0, se0, n0 = mean_se_ci(sub0)
        m1, se1, n1 = mean_se_ci(sub1)

        diff = m1 - m0
        se_diff = np.sqrt(
            (se0 if np.isfinite(se0) else np.nan) ** 2 +
            (se1 if np.isfinite(se1) else np.nan) ** 2
        )

        ci_l = diff - 1.96 * se_diff if np.isfinite(se_diff) else np.nan
        ci_u = diff + 1.96 * se_diff if np.isfinite(se_diff) else np.nan

        rows.append({
            "var": var,
            "mean_rural": m0 * scale if np.isfinite(m0) else np.nan,
            "mean_urban": m1 * scale if np.isfinite(m1) else np.nan,
            "n_rural": n0,
            "n_urban": n1,
            "diff_u_minus_r": diff * scale if np.isfinite(diff) else np.nan,
            "se_diff": se_diff * scale if np.isfinite(se_diff) else np.nan,
            "ci_l": ci_l * scale if np.isfinite(ci_l) else np.nan,
            "ci_u": ci_u * scale if np.isfinite(ci_u) else np.nan,
            "money_mode": money_mode if (money_mode is not None and var in MONEY_VARS) else "na",
            "money_unit": money_unit if (money_mode is not None and var in MONEY_VARS) else "na",
            "scale": scale,
        })

    summ = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    order = [v for v in ALL_VARS if v in vars_present]
    if len(order) > 0 and not summ.empty:
        summ["var"] = pd.Categorical(summ["var"], categories=order, ordered=True)
        summ = summ.sort_values("var").reset_index(drop=True)

    return summ


def plot_forest_from_summary(summ, outfile: Path, title: str, xlabel: str):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if summ.empty:
        print("[WARN] empty summary -> skip:", outfile.name)
        return

    y = np.arange(len(summ))
    x = summ["diff_u_minus_r"].to_numpy()
    left = (summ["diff_u_minus_r"] - summ["ci_l"]).to_numpy()
    right = (summ["ci_u"] - summ["diff_u_minus_r"]).to_numpy()

    left = np.where(np.isfinite(left), left, 0.0)
    right = np.where(np.isfinite(right), right, 0.0)

    fig_h = max(4.5, 0.42 * len(summ) + 1.0)
    fig, ax = plt.subplots(figsize=(8.8, fig_h), constrained_layout=True)

    ax.errorbar(
        x, y,
        xerr=[left, right],
        fmt="o",
        capsize=3,
        linewidth=1,
    )
    ax.axvline(0, linewidth=1)

    ax.set_yticks(y)
    # Original notebook comment normalized for the public code archive.
    ax.set_yticklabels(summ["var"].astype(str), fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_title(title)

    # Original notebook comment normalized for the public code archive.
    x_min, x_max = ax.get_xlim()
    x_text = x_max + (x_max - x_min) * 0.02
    for i, (n0, n1) in enumerate(zip(summ["n_rural"], summ["n_urban"])):
        ax.text(
            x_text,
            i,
            f"nR={int(n0)}, nU={int(n1)}",
            va="center",
            fontsize=8,
        )
    ax.set_xlim(x_min, x_max + (x_max - x_min) * 0.18)

    # Original notebook comment normalized for the public code archive.
    fig.savefig(outfile, dpi=300)
    print("[SAVE]", outfile)
    plt.show()
    plt.close(fig)


# =============================================================================
def plot_money_only(df):
    vars_subset = [v for v in MONEY_VARS if v in df.columns]
    summ = build_summary_diff_subset(
        df, vars_subset,
        scale=1.0,
        money_mode=MONEY_MODE,
    )

    _, unit = make_money_transform(MONEY_MODE)
    out_fig = OUT_DIR / f"mech2_forest_diff_money_only_{MONEY_MODE}.png"
    out_csv = OUT_DIR / f"mech2_forest_diff_money_only_{MONEY_MODE}_summary.csv"

    title = f"Mechanism2: Spending (Urban vs Rural) [{unit}]"
    xlabel = f"Urban − Rural (mean difference with 95% CI; money vars in {unit})"

    plot_forest_from_summary(summ, out_fig, title, xlabel)
    summ.to_csv(out_csv, index=False)
    print("[SAVE]", out_csv)


def plot_util_intensity_only(df):
    vars_subset = [v for v in MECH_GROUPS["util_intensity"] if v in df.columns]
    summ = build_summary_diff_subset(df, vars_subset, scale=1.0)

    out_fig = OUT_DIR / "mech2_forest_diff_util_intensity_only.png"
    out_csv = OUT_DIR / "mech2_forest_diff_util_intensity_only_summary.csv"

    title = "Mechanism2: Utilization intensity (Urban vs Rural)"
    xlabel = "Urban − Rural (mean difference with 95% CI)"

    plot_forest_from_summary(summ, out_fig, title, xlabel)
    summ.to_csv(out_csv, index=False)
    print("[SAVE]", out_csv)


def plot_access_time_dist_only(df):
    vars_subset = (
        [v for v in MECH_GROUPS["access_time"] if v in df.columns] +
        [v for v in MECH_GROUPS["access_distance"] if v in df.columns]
    )
    summ = build_summary_diff_subset(df, vars_subset, scale=1.0)

    out_fig = OUT_DIR / "mech2_forest_diff_access_time_dist_only.png"
    out_csv = OUT_DIR / "mech2_forest_diff_access_time_dist_only_summary.csv"

    title = "Mechanism2: Access (time & distance) (Urban vs Rural)"
    xlabel = "Urban − Rural (mean difference with 95% CI)"

    plot_forest_from_summary(summ, out_fig, title, xlabel)
    summ.to_csv(out_csv, index=False)
    print("[SAVE]", out_csv)


def plot_binary_pp_only(df):
    vars_subset = [v for v in ALL_VARS if (v in BINARY_VARS and v in df.columns)]
    # Original notebook comment normalized for the public code archive.
    summ = build_summary_diff_subset(df, vars_subset, scale=100.0)

    out_fig = OUT_DIR / "mech2_forest_diff_binary_pp_only.png"
    out_csv = OUT_DIR / "mech2_forest_diff_binary_pp_only_summary.csv"

    title = "Mechanism2: Binary outcomes (percentage-point differences)"
    xlabel = "Urban − Rural (percentage-point difference with 95% CI)"

    plot_forest_from_summary(summ, out_fig, title, xlabel)
    summ.to_csv(out_csv, index=False)
    print("[SAVE]", out_csv)


def main():
    df = prep_df()
    found = [v for v in ALL_VARS if v in df.columns]
    print("[INFO] vars found:", found)

    # Original notebook comment normalized for the public code archive.
    plot_money_only(df)
    plot_util_intensity_only(df)
    plot_access_time_dist_only(df)
    plot_binary_pp_only(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =========================
# Original notebook comment normalized for the public code archive.
# =========================

PANEL = Path(
    r"E:\impact_assessment_child_order\data\supplement\EDA"
) / "charls_health_mechanism2_with_Tall_5_10_20_30y.parquet"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_XLSX = OUT_DIR / "mech2_UvsR_summary_table.xlsx"
OUT_CSV  = OUT_DIR / "mech2_UvsR_summary_table.csv"

URBAN_NBS_COL = "urban_nbs"
YEAR_COL = "year"

# =========================
# Original notebook comment normalized for the public code archive.
# =========================

rename_map = {
    "outpt_month_oop": "op_oop_m1",
    "inp_year_oop": "ip_oop_y1",
    "self_treat_oop": "st_oop_m1",
    "outpt_last_oop": "op_oop_last",
    "inp_last_oop": "ip_oop_last",
    "hh_med_year": "hh_med_y1",
    "hh_health_year": "hh_hlth_y1",
    "has_outpt": "op_any_m1",
    "inp_any": "ip_any_y1",
    "ed005_visits": "op_n_m1",
    "inp_year_total": "ip_tot_y1",
    "inp_last_total": "ip_tot_last",
    "self_treat_total": "st_tot_m1",
    "outpt_time_single_unc": "op_time_last_unc",
    "inp_time_single_unc": "ip_time_last_unc",
    "outpt_time_month_unc": "op_time_m1_unc",
    "outpt_dist_single_unc": "op_dist_last_unc",
    "inp_dist_single_unc": "ip_dist_last_unc",
    "outpt_walk": "op_walk_last",
    "inp_walk": "ip_walk_last",
    "outpt_homevisit": "op_home_last",
}

# =========================
# Original notebook comment normalized for the public code archive.
# =========================

MECH_GROUPS = {
    "oop_individual": [
        "op_oop_m1",
        "ip_oop_y1",
        "st_oop_m1",
        "op_oop_last",
        "ip_oop_last",
    ],
    "oop_household": [
        "hh_med_y1",
        "hh_hlth_y1",
    ],
    "util_any": [
        "op_any_m1",
        "ip_any_y1",
    ],
    "util_intensity": [
        "op_n_m1",
        "ip_tot_y1",
        "ip_tot_last",
        "st_tot_m1",
    ],
    "access_time": [
        "op_time_last_unc",
        "ip_time_last_unc",
        "op_time_m1_unc",
    ],
    "access_distance": [
        "op_dist_last_unc",
        "ip_dist_last_unc",
    ],
    "access_transport": [
        "op_walk_last",
        "ip_walk_last",
        "op_home_last",
    ],
}

# Original notebook comment normalized for the public code archive.
MECH_GROUP_LABELS = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

# Original notebook comment normalized for the public code archive.
ALL_VARS = [v for vs in MECH_GROUPS.values() for v in vs]

# Original notebook comment normalized for the public code archive.
NEG_AS_NA_GROUPS = {
    "oop_individual",
    "oop_household",
    "util_intensity",
    "access_time",
    "access_distance",
}

# Original notebook comment normalized for the public code archive.
VAR_LABELS = {
    # Original notebook comment normalized for the public code archive.
    "op_oop_m1":       "Outpatient OOP, last month (CNY)",
    "ip_oop_y1":       "Inpatient OOP, last year (CNY)",
    "st_oop_m1":       "Self-treatment OOP, last month (CNY)",
    "op_oop_last":     "Outpatient OOP, last visit (CNY)",
    "ip_oop_last":     "Inpatient OOP, last admission (CNY)",
    # Original notebook comment normalized for the public code archive.
    "hh_med_y1":       "Household medical spending, last year (CNY)",
    "hh_hlth_y1":      "Household total health spending, last year (CNY)",
    # any use
    "op_any_m1":       "Any outpatient visit, last month (0/1)",
    "ip_any_y1":       "Any inpatient admission, last year (0/1)",
    # intensity
    "op_n_m1":         "Number of outpatient visits, last month",
    "ip_tot_y1":       "Number of inpatient admissions, last year",
    "ip_tot_last":     "Length of stay, last admission (days)",
    "st_tot_m1":       "Number of self-treatments, last month",
    # access: time
    "op_time_last_unc": "Travel time to last outpatient visit (min, uncapped)",
    "ip_time_last_unc": "Travel time to last inpatient visit (min, uncapped)",
    "op_time_m1_unc":   "Total travel time for outpatient visits, last month (min, uncapped)",
    # access: distance
    "op_dist_last_unc": "Travel distance to last outpatient visit (km, uncapped)",
    "ip_dist_last_unc": "Travel distance to last inpatient visit (km, uncapped)",
    # access: transport
    "op_walk_last":    "Walked to last outpatient visit (0/1)",
    "ip_walk_last":    "Walked to last inpatient visit (0/1)",
    "op_home_last":    "Received outpatient home visit (0/1)",
}


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def mean_ci(series: pd.Series, alpha: float = 0.05):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = s.shape[0]
    if n == 0:
        return np.nan, np.nan, np.nan, 0

    mean = float(s.mean())
    sd = float(s.std(ddof=1)) if n > 1 else 0.0
    se = sd / np.sqrt(n) if n > 1 else 0.0
    z  = 1.96  # Original notebook comment normalized for the public code archive.
    ci_l = mean - z * se
    ci_u = mean + z * se
    return mean, ci_l, ci_u, int(n)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def prep_df() -> pd.DataFrame:
    print(f"[READ] {PANEL}")
    df = pd.read_parquet(PANEL)

    # Original notebook comment normalized for the public code archive.
    rename_actual = {old: new for old, new in rename_map.items() if old in df.columns}
    df = df.rename(columns=rename_actual)

    # Original notebook comment normalized for the public code archive.
    keep_cols = [YEAR_COL, URBAN_NBS_COL] + ALL_VARS
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()

    # Original notebook comment normalized for the public code archive.
    neg_cols = []
    for grp, vars_ in MECH_GROUPS.items():
        if grp in NEG_AS_NA_GROUPS:
            neg_cols.extend([v for v in vars_ if v in df.columns])

    for col in neg_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = np.nan

    # Original notebook comment normalized for the public code archive.
    if URBAN_NBS_COL not in df.columns:
        raise KeyError(f"'{URBAN_NBS_COL}' not found in data.")

    urban_numeric = pd.to_numeric(df[URBAN_NBS_COL].astype(str), errors="coerce")
    df["urban_group_wave"] = urban_numeric.fillna(0).astype(int)

    return df


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def build_display_table(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows_out = []

    for grp_id, var_list in MECH_GROUPS.items():
        grp_label = MECH_GROUP_LABELS.get(grp_id, grp_id)

        # Original notebook comment normalized for the public code archive.
        rows_out.append({
            "Variable_label": grp_label,
            "Rural_N":        "",
            "Rural_mean":     "",
            "Rural_CI":       "",
            "Urban_N":        "",
            "Urban_mean":     "",
            "Urban_CI":       "",
        })

        # Original notebook comment normalized for the public code archive.
        for var in var_list:
            if var not in df.columns:
                continue

            label = VAR_LABELS.get(var, var)

            s_rural = df.loc[df["urban_group_wave"] == 0, var]
            s_urban = df.loc[df["urban_group_wave"] == 1, var]

            mean_r, ci_l_r, ci_u_r, n_r = mean_ci(s_rural)
            mean_u, ci_l_u, ci_u_u, n_u = mean_ci(s_urban)

            # Original notebook comment normalized for the public code archive.
            def fmt3(x):
                return f"{x:.3f}" if (x is not None and np.isfinite(x)) else ""

            rural_mean_str = fmt3(mean_r)
            urban_mean_str = fmt3(mean_u)

            if np.isfinite(ci_l_r) and np.isfinite(ci_u_r):
                rural_ci_str = f"[{fmt3(ci_l_r)}, {fmt3(ci_u_r)}]"
            else:
                rural_ci_str = ""

            if np.isfinite(ci_l_u) and np.isfinite(ci_u_u):
                urban_ci_str = f"[{fmt3(ci_l_u)}, {fmt3(ci_u_u)}]"
            else:
                urban_ci_str = ""

            rows_out.append({
                "Variable_label": label,
                "Rural_N":        str(n_r) if n_r > 0 else "",
                "Rural_mean":     rural_mean_str,
                "Rural_CI":       rural_ci_str,
                "Urban_N":        str(n_u) if n_u > 0 else "",
                "Urban_mean":     urban_mean_str,
                "Urban_CI":       urban_ci_str,
            })

    table = pd.DataFrame(rows_out, columns=[
        "Variable_label",
        "Rural_N",
        "Rural_mean",
        "Rural_CI",
        "Urban_N",
        "Urban_mean",
        "Urban_CI",
    ])

    return table


# =========================
# main
# =========================

def main():
    df = prep_df()

    print("[INFO] Notebook progress message.")
    present = [v for v in ALL_VARS if v in df.columns]
    print(present)

    table = build_display_table(df)

    # Original notebook comment normalized for the public code archive.
    table.to_excel(OUT_XLSX, index=False)
    table.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[SAVE] Excel table: {OUT_XLSX}")
    print(f"[SAVE] CSV table  : {OUT_CSV}")
    print("\n[HEAD]")
    print(table.head(15))


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
mpl.rcParams.update({
    "font.family": "Times New Roman",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

# =============================================================================
PANEL = Path(
    r"E:\impact_assessment_child_order\data\supplement\EDA"
) / "charls_health_mechanism2_with_Tall_5_10_20_30y.parquet"

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIG = OUT_DIR / "mech2_std_diff_forest_UminusR_transparent.png"

URBAN_NBS_COL = "urban_nbs"
YEAR_COL = "year"

# =============================================================================
rename_map = {
    "outpt_month_oop": "op_oop_m1",
    "inp_year_oop": "ip_oop_y1",
    "self_treat_oop": "st_oop_m1",
    "outpt_last_oop": "op_oop_last",
    "inp_last_oop": "ip_oop_last",
    "hh_med_year": "hh_med_y1",
    "hh_health_year": "hh_hlth_y1",
    "has_outpt": "op_any_m1",
    "inp_any": "ip_any_y1",
    "ed005_visits": "op_n_m1",
    "inp_year_total": "ip_tot_y1",
    "inp_last_total": "ip_tot_last",
    "self_treat_total": "st_tot_m1",
    "outpt_time_single_unc": "op_time_last_unc",
    "inp_time_single_unc": "ip_time_last_unc",
    "outpt_time_month_unc": "op_time_m1_unc",
    "outpt_dist_single_unc": "op_dist_last_unc",
    "inp_dist_single_unc": "ip_dist_last_unc",
    "outpt_walk": "op_walk_last",
    "inp_walk": "ip_walk_last",
    "outpt_homevisit": "op_home_last",
}

# =============================================================================
MECH_GROUPS = {
    "oop_individual": [
        "op_oop_m1",
        "ip_oop_y1",
        "st_oop_m1",
        "op_oop_last",
        "ip_oop_last",
    ],
    "oop_household": [
        "hh_med_y1",
        "hh_hlth_y1",
    ],
    "util_any": [
        "op_any_m1",
        "ip_any_y1",
    ],
    "util_intensity": [
        "op_n_m1",
        "ip_tot_y1",
        "ip_tot_last",
        "st_tot_m1",
    ],
    "access_time": [
        "op_time_last_unc",
        "ip_time_last_unc",
        "op_time_m1_unc",
    ],
    "access_distance": [
        "op_dist_last_unc",
        "ip_dist_last_unc",
    ],
    "access_transport": [
        "op_walk_last",
        "ip_walk_last",
        "op_home_last",
    ],
}

MECH_GROUP_LABELS = {
    "oop_individual":   "Out-of-pocket spending (individual level)",
    "oop_household":    "Out-of-pocket spending (household level)",
    "util_any":         "Any use of care (binary)",
    "util_intensity":   "Utilization intensity",
    "access_time":      "Access: time to care",
    "access_distance":  "Access: distance to care",
    "access_transport": "Access: transport mode",
}

ALL_VARS = [v for vs in MECH_GROUPS.values() for v in vs]

# Original notebook comment normalized for the public code archive.
NEG_AS_NA_GROUPS = {
    "oop_individual",
    "oop_household",
    "util_intensity",
    "access_time",
    "access_distance",
}

# =============================================================================
def cohen_d_with_ci(s_rural: pd.Series, s_urban: pd.Series):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    r = pd.to_numeric(s_rural, errors="coerce").dropna()
    u = pd.to_numeric(s_urban, errors="coerce").dropna()

    n_r = r.shape[0]
    n_u = u.shape[0]
    if n_r < 2 or n_u < 2:
        return np.nan, np.nan, np.nan, n_r, n_u

    mean_r = float(r.mean())
    mean_u = float(u.mean())
    var_r = float(r.var(ddof=1))
    var_u = float(u.var(ddof=1))

    pooled_var = ((n_r - 1) * var_r + (n_u - 1) * var_u) / (n_r + n_u - 2)
    if pooled_var <= 0 or not np.isfinite(pooled_var):
        return np.nan, np.nan, np.nan, n_r, n_u

    pooled_sd = np.sqrt(pooled_var)
    d = (mean_u - mean_r) / pooled_sd

    se_d = np.sqrt((n_r + n_u) / (n_r * n_u) + d ** 2 / (2 * (n_r + n_u - 2)))
    if not np.isfinite(se_d) or se_d == 0:
        return d, np.nan, np.nan, n_r, n_u

    z = 1.96
    ci_l = d - z * se_d
    ci_u = d + z * se_d
    return d, ci_l, ci_u, n_r, n_u


# =============================================================================
def prep_df() -> pd.DataFrame:
    print(f"[READ] {PANEL}")
    df = pd.read_parquet(PANEL)

    # Original notebook comment normalized for the public code archive.
    rename_actual = {old: new for old, new in rename_map.items() if old in df.columns}
    df = df.rename(columns=rename_actual)

    keep_cols = [YEAR_COL, URBAN_NBS_COL] + ALL_VARS
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols].copy()

    # Original notebook comment normalized for the public code archive.
    neg_cols = []
    for grp, vars_ in MECH_GROUPS.items():
        if grp in NEG_AS_NA_GROUPS:
            neg_cols.extend([v for v in vars_ if v in df.columns])

    for col in neg_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = np.nan

    # Original notebook comment normalized for the public code archive.
    if URBAN_NBS_COL not in df.columns:
        raise KeyError(f"'{URBAN_NBS_COL}' not found in data.")

    urban_numeric = pd.to_numeric(df[URBAN_NBS_COL].astype(str), errors="coerce")
    df["urban_group_wave"] = urban_numeric.fillna(0).astype(int)

    return df


# =============================================================================
def build_effect_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grp_id, var_list in MECH_GROUPS.items():
        # Original notebook comment normalized for the public code archive.
        grp_label = MECH_GROUP_LABELS.get(grp_id, grp_id)
        rows.append({
            "is_group": True,
            "label": grp_label,
            "d": np.nan,
            "ci_l": np.nan,
            "ci_u": np.nan,
            "n_rural": np.nan,
            "n_urban": np.nan,
        })

        for var in var_list:
            if var not in df.columns:
                rows.append({
                    "is_group": False,
                    "label": var,
                    "d": np.nan,
                    "ci_l": np.nan,
                    "ci_u": np.nan,
                    "n_rural": np.nan,
                    "n_urban": np.nan,
                })
                continue

            s_rural = df.loc[df["urban_group_wave"] == 0, var]
            s_urban = df.loc[df["urban_group_wave"] == 1, var]

            d, ci_l, ci_u, n_r, n_u = cohen_d_with_ci(s_rural, s_urban)

            rows.append({
                "is_group": False,
                "label": var,
                "d": d,
                "ci_l": ci_l,
                "ci_u": ci_u,
                "n_rural": n_r,
                "n_urban": n_u,
            })

    eff = pd.DataFrame(rows)
    return eff


# =============================================================================
def plot_forest_std_diff(eff: pd.DataFrame, save_path: Path):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    eff = eff.reset_index(drop=True)
    n_rows = eff.shape[0]
    y_pos = np.arange(n_rows)[::-1]  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    mask_plot = (eff["is_group"] == False) & eff["d"].notna()
    if not mask_plot.any():
        raise RuntimeError("No finite standardized differences (all NaN).")

    d = eff.loc[mask_plot, "d"].to_numpy()
    ci_l = eff.loc[mask_plot, "ci_l"].to_numpy()
    ci_u = eff.loc[mask_plot, "ci_u"].to_numpy()
    y_plot = y_pos[mask_plot.to_numpy()]

    err_left = d - ci_l
    err_right = ci_u - d

    fig_h = max(6.0, 0.35 * n_rows)
    fig, ax = plt.subplots(figsize=(9, fig_h))

    # Original notebook comment normalized for the public code archive.
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    # Original notebook comment normalized for the public code archive.
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    ax.errorbar(
        d,
        y_plot,
        xerr=[err_left, err_right],
        fmt="o",
        color="black",
        ecolor="black",
        elinewidth=1.2,
        capsize=3,
    )

    # Original notebook comment normalized for the public code archive.
    ax.set_xlim(-0.1, 0.3)
    ax.set_ylim(-1, n_rows)

    ax.set_xlabel("Standardized urban − rural difference (Cohen's d)")
    ax.set_yticks([])
    ax.tick_params(axis="y", length=0)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"[SAVE] {save_path}")


# ========== main ==========
def main():
    df = prep_df()

    print("[INFO] Notebook progress message.")
    print([v for v in ALL_VARS if v in df.columns])

    eff = build_effect_table(df)
    print("\n[HEAD of effect table]")
    print(eff.head(15))

    plot_forest_std_diff(eff, OUT_FIG)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
PANEL = ROOT / "charls_health_mechanism2_with_Tall_5_10_20_30y.parquet"

OUT_DIR = ROOT / "figure"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_SVG = OUT_DIR / "mech2_forest_std_urban_rural_strip.svg"

URBAN_NBS_COL = "urban_nbs"

# Original notebook comment normalized for the public code archive.
FIG_W_MM = 57.573
FIG_H_MM = 163.607
FIG_W_IN = FIG_W_MM / 25.4
FIG_H_IN = FIG_H_MM / 25.4

# =============================================================================
var_order = [
    # Out-of-pocket spending (individual level)
    "outpt_month_oop",       # Outpatient OOP, last month (CNY)
    "inp_year_oop",          # Inpatient OOP, last year (CNY)
    "self_treat_oop",        # Self-treatment OOP, last month (CNY)
    "outpt_last_oop",        # Outpatient OOP, last visit (CNY)
    "inp_last_oop",          # Inpatient OOP, last admission (CNY)
    # Out-of-pocket spending (household level)
    "hh_med_year",           # Household medical spending, last year (CNY)
    "hh_health_year",        # Household total health spending, last year (CNY)
    # Any use of care (binary)
    "has_outpt",             # Any outpatient visit, last month (0/1)
    "inp_any",               # Any inpatient admission, last year (0/1)
    # Utilization intensity
    "ed005_visits",          # Number of outpatient visits, last month
    "inp_year_total",        # Number of inpatient admissions, last year
    "inp_last_total",        # Length of stay, last admission (days)
    "self_treat_total",      # Number of self-treatments, last month
    # Access: time to care
    "outpt_time_single_unc", # Travel time to last outpatient visit (min, uncapped)
    "inp_time_single_unc",   # Travel time to last inpatient visit (min, uncapped)
    "outpt_time_month_unc",  # Total travel time for outpatient visits, last month (min, uncapped)
    # Access: distance to care
    "outpt_dist_single_unc", # Travel distance to last outpatient visit (km, uncapped)
    "inp_dist_single_unc",   # Travel distance to last inpatient visit (km, uncapped)
    # Access: transport mode
    "outpt_walk",            # Walked to last outpatient visit (0/1)
    "inp_walk",              # Walked to last inpatient visit (0/1)
    "outpt_homevisit",       # Received outpatient home visit (0/1)
]

# Original notebook comment normalized for the public code archive.
NEG_AS_NA = {
    "outpt_month_oop",
    "inp_year_oop",
    "self_treat_oop",
    "outpt_last_oop",
    "inp_last_oop",
    "hh_med_year",
    "hh_health_year",
    "ed005_visits",
    "inp_year_total",
    "inp_last_total",
    "self_treat_total",
    "outpt_time_single_unc",
    "inp_time_single_unc",
    "outpt_time_month_unc",
    "outpt_dist_single_unc",
    "inp_dist_single_unc",
}

# =============================================================================
def mean_se(x: np.ndarray):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = x[np.isfinite(x)]
    n = x.size
    if n == 0:
        return np.nan, np.nan, 0
    m = x.mean()
    se = x.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
    return m, se, n

# =============================================================================
print(f"[READ] {PANEL}")
df = pd.read_parquet(PANEL)

# Original notebook comment normalized for the public code archive.
if URBAN_NBS_COL not in df.columns:
    raise KeyError(f"Column '{URBAN_NBS_COL}' not found in data.")

urban_wave = pd.to_numeric(df[URBAN_NBS_COL], errors="coerce").fillna(0)
df["urban_group_wave"] = urban_wave.astype(int)

# =============================================================================
rows = []

for var in var_order:
    if var not in df.columns:
        print(f"[WARN] {var} not in data, skip.")
        continue

    s_all = pd.to_numeric(df[var], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    if var in NEG_AS_NA:
        s_all = s_all.where(s_all >= 0)

    # overall SD
    x_all = s_all.to_numpy()
    x_all = x_all[np.isfinite(x_all)]
    if x_all.size < 2:
        print(f"[WARN] {var}: not enough non-missing values, skip.")
        continue
    sd_all = x_all.std(ddof=1)

    # Original notebook comment normalized for the public code archive.
    s_rural = s_all[df["urban_group_wave"] == 0].to_numpy()
    s_urban = s_all[df["urban_group_wave"] == 1].to_numpy()

    m_r, se_r, n_r = mean_se(s_rural)
    m_u, se_u, n_u = mean_se(s_urban)

    if not np.isfinite(sd_all) or sd_all == 0:
        print(f"[WARN] {var}: SD_all is 0 or NA, skip.")
        continue

    # Original notebook comment normalized for the public code archive.
    diff_raw = m_u - m_r
    se_diff_raw = np.sqrt(se_r**2 + se_u**2) if np.isfinite(se_r) and np.isfinite(se_u) else np.nan

    # Original notebook comment normalized for the public code archive.
    diff_std = diff_raw / sd_all
    if np.isfinite(se_diff_raw):
        se_diff_std = se_diff_raw / sd_all
        ci_l_std = diff_std - 1.96 * se_diff_std
        ci_u_std = diff_std + 1.96 * se_diff_std
    else:
        ci_l_std = np.nan
        ci_u_std = np.nan

    rows.append(
        {
            "var": var,
            "diff_std": diff_std,
            "ci_l_std": ci_l_std,
            "ci_u_std": ci_u_std,
            "n_rural": n_r,
            "n_urban": n_u,
        }
    )

stats = pd.DataFrame(rows)

# Original notebook comment normalized for the public code archive.
stats["var"] = pd.Categorical(stats["var"], categories=var_order, ordered=True)
stats = stats.sort_values("var").reset_index(drop=True)

print("[INFO] stats head:")
print(stats.head())

# =============================================================================
mpl.rcParams.update({
    "figure.dpi": 300,
    "axes.unicode_minus": False,
})

fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN))

y_positions = np.arange(len(stats))

# Original notebook comment normalized for the public code archive.
x = stats["diff_std"].to_numpy()
x_l = stats["diff_std"] - stats["ci_l_std"]
x_u = stats["ci_u_std"] - stats["diff_std"]

xerr = np.vstack([x_l.to_numpy(), x_u.to_numpy()])

# Original notebook comment normalized for the public code archive.
ax.errorbar(
    x,
    y_positions,
    xerr=xerr,
    fmt="o",
    markersize=2.0,
    linewidth=0.8,
    capsize=1.5,
    color="black",
    ecolor="black",
)

# Original notebook comment normalized for the public code archive.
ax.axvline(0.0, linestyle="--", linewidth=0.8, color="0.7")

# Original notebook comment normalized for the public code archive.
ax.set_xlim(-0.1, 0.3)
ax.set_ylim(-0.5, len(stats) - 0.5)

# Original notebook comment normalized for the public code archive.
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")

# Original notebook comment normalized for the public code archive.
for spine in ax.spines.values():
    spine.set_visible(False)

# Original notebook comment normalized for the public code archive.
fig.patch.set_alpha(0.0)
ax.set_facecolor((1, 1, 1, 0))

# Original notebook comment normalized for the public code archive.
plt.subplots_adjust(left=0.05, right=0.95, top=0.98, bottom=0.02)

# Original notebook comment normalized for the public code archive.
fig.savefig(OUT_SVG, format="svg", transparent=True)
plt.close(fig)

print(f"[SAVE] {OUT_SVG}")


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 22
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
ROOT = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result")
PANEL = ROOT / "charls_health_mechanism2_with_Tall_5_10_20_30y.parquet"

OUT_DIR = ROOT / "eda_mechanism2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_NUM_CSV = OUT_DIR / "mech2_urban_rural_table_numeric.csv"
OUT_FMT_CSV = OUT_DIR / "mech2_urban_rural_table_formatted.csv"
OUT_XLSX = OUT_DIR / "mech2_urban_rural_table.xlsx"

# =============================================================================
MECH_GROUPS = {
    "oop_individual": [
        "outpt_month_oop", "inp_year_oop", "self_treat_oop",
        "outpt_last_oop", "inp_last_oop",
    ],
    "oop_household": [
        "hh_med_year", "hh_health_year",
    ],
    "util_any": [
        "has_outpt", "inp_any",
    ],
    "util_intensity": [
        "ed005_visits", "inp_year_total", "inp_last_total", "self_treat_total",
    ],
    "access_time": [
        "outpt_time_single_unc", "inp_time_single_unc", "outpt_time_month_unc",
    ],
    "access_distance": [
        "outpt_dist_single_unc", "inp_dist_single_unc",
    ],
    "access_transport": [
        "outpt_walk", "inp_walk", "outpt_homevisit",
    ],
}
ALL_VARS = [v for vs in MECH_GROUPS.values() for v in vs]

# =============================================================================
URBAN_NBS_COL = "urban_nbs"

# =============================================================================
NEG_AS_NA_GROUPS = {
    "oop_individual",
    "oop_household",
    "util_intensity",
    "access_time",
    "access_distance",
}

# =============================================================================
MONEY_VARS = MECH_GROUPS["oop_individual"] + MECH_GROUPS["oop_household"]
BINARY_VARS = {
    "has_outpt", "inp_any",
    "outpt_walk", "inp_walk", "outpt_homevisit",
}

# =============================================================================
# raw | k | wan | log1p
MONEY_MODE = "k"

def clean_neg_to_nan(df, cols):
    for c in cols:
        if c in df.columns:
            df.loc[df[c] < 0, c] = np.nan
    return df

def mean_se_ci(s):
    s = pd.Series(s)
    s = pd.to_numeric(s, errors="coerce").dropna()
    n = len(s)
    if n == 0:
        return np.nan, np.nan, 0, np.nan, np.nan
    mean = s.mean()
    std = s.std(ddof=1)
    se = std / np.sqrt(n) if n > 1 else 0.0
    ci_l = mean - 1.96 * se if np.isfinite(se) else np.nan
    ci_u = mean + 1.96 * se if np.isfinite(se) else np.nan
    return mean, se, n, ci_l, ci_u

def prep_df():
    df = pd.read_parquet(PANEL)

    keep = ["year", URBAN_NBS_COL] + ALL_VARS
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    # Original notebook comment normalized for the public code archive.
    neg_cols = []
    for g, vs in MECH_GROUPS.items():
        if g in NEG_AS_NA_GROUPS:
            neg_cols.extend([v for v in vs if v in df.columns])
    df = clean_neg_to_nan(df, neg_cols)

    # Original notebook comment normalized for the public code archive.
    if URBAN_NBS_COL not in df.columns:
        raise KeyError("未找到 urban_nbs，无法进行波次口径城乡划分。")

    df["urban_group_wave"] = (
        pd.to_numeric(df[URBAN_NBS_COL], errors="coerce")
        .fillna(0).astype(int)
    )
    return df

def make_money_transform(mode):
    if mode == "raw":
        return None, "CNY"
    if mode == "k":
        return (lambda s: s / 1000.0), "thousand CNY"
    if mode == "wan":
        return (lambda s: s / 10000.0), "10k CNY"
    if mode == "log1p":
        return (lambda s: np.log1p(s.where(s >= 0))), "log1p(CNY)"
    raise ValueError(f"Unknown money mode: {mode}")

def apply_transform(series, fn):
    s = pd.to_numeric(series, errors="coerce")
    if fn is None:
        return s
    out = fn(s)
    if isinstance(out, np.ndarray):
        out = pd.Series(out, index=s.index)
    return out

def var_scale_and_unit(var):
    """Archived notebook note for 02_medical_expenditure_healthcare_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if var in BINARY_VARS:
        return 100.0, "percent", "binary"
    if var in MONEY_VARS:
        _, unit = make_money_transform(MONEY_MODE)
        return 1.0, unit, "money"
    return 1.0, "raw", "continuous"

def build_table(df, group_col="urban_group_wave"):
    money_fn, money_unit = make_money_transform(MONEY_MODE)

    vars_present = [v for v in ALL_VARS if v in df.columns]

    # Original notebook comment normalized for the public code archive.
    group_order = list(MECH_GROUPS.keys())
    var_order = []
    for g in group_order:
        var_order.extend([v for v in MECH_GROUPS[g] if v in vars_present])

    # Original notebook comment normalized for the public code archive.
    var2group = {}
    for g, vs in MECH_GROUPS.items():
        for v in vs:
            var2group[v] = g

    rows = []
    for var in var_order:
        scale, unit, vtype = var_scale_and_unit(var)

        s0 = df[df[group_col] == 0][var]  # rural
        s1 = df[df[group_col] == 1][var]  # urban

        # Original notebook comment normalized for the public code archive.
        if var in MONEY_VARS and money_fn is not None:
            s0 = apply_transform(s0, money_fn)
            s1 = apply_transform(s1, money_fn)

        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        m0, se0, n0, l0, u0 = mean_se_ci(s0)
        m1, se1, n1, l1, u1 = mean_se_ci(s1)

        diff = m1 - m0
        se_diff = np.sqrt(
            (se0 if np.isfinite(se0) else np.nan) ** 2 +
            (se1 if np.isfinite(se1) else np.nan) ** 2
        )
        dl = diff - 1.96 * se_diff if np.isfinite(se_diff) else np.nan
        du = diff + 1.96 * se_diff if np.isfinite(se_diff) else np.nan

        # Original notebook comment normalized for the public code archive.
        m0_s, l0_s, u0_s = m0 * scale, l0 * scale, u0 * scale
        m1_s, l1_s, u1_s = m1 * scale, l1 * scale, u1 * scale
        diff_s, dl_s, du_s = diff * scale, dl * scale, du * scale

        rows.append({
            "mech_group": var2group.get(var, None),
            "var": var,
            "type": vtype,
            "display_unit": unit,
            "scale": scale,

            "n_rural": n0,
            "mean_rural": m0_s, "ci_rural_l": l0_s, "ci_rural_u": u0_s,

            "n_urban": n1,
            "mean_urban": m1_s, "ci_urban_l": l1_s, "ci_urban_u": u1_s,

            "diff_u_minus_r": diff_s,
            "ci_diff_l": dl_s, "ci_diff_u": du_s,
        })

    num = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    num["mech_group"] = pd.Categorical(num["mech_group"], categories=group_order, ordered=True)
    num["var"] = pd.Categorical(num["var"], categories=var_order, ordered=True)
    num = num.sort_values(["mech_group", "var"]).reset_index(drop=True)

    return num

def format_ci(mean, l, u, digits=2):
    if not (np.isfinite(mean) and np.isfinite(l) and np.isfinite(u)):
        return ""
    fmt = f"{{:.{digits}f}}"
    return f"{fmt.format(mean)} [{fmt.format(l)}, {fmt.format(u)}]"

def build_formatted_table(num):
    # Original notebook comment normalized for the public code archive.
    def digits_for_type(t, unit):
        if t == "binary":
            return 1
        if t == "money":
            # Original notebook comment normalized for the public code archive.
            return 2
        return 2

    rows = []
    for _, r in num.iterrows():
        d = digits_for_type(r["type"], r["display_unit"])

        rural_str = format_ci(r["mean_rural"], r["ci_rural_l"], r["ci_rural_u"], digits=d)
        urban_str = format_ci(r["mean_urban"], r["ci_urban_l"], r["ci_urban_u"], digits=d)
        diff_str = format_ci(r["diff_u_minus_r"], r["ci_diff_l"], r["ci_diff_u"], digits=d)

        rows.append({
            "mech_group": r["mech_group"],
            "var": r["var"],
            "type": r["type"],
            "unit": r["display_unit"],

            "Rural mean [95% CI]": rural_str,
            "Urban mean [95% CI]": urban_str,
            "Urban − Rural [95% CI]": diff_str,

            "n_rural": int(r["n_rural"]) if pd.notna(r["n_rural"]) else "",
            "n_urban": int(r["n_urban"]) if pd.notna(r["n_urban"]) else "",
        })

    fmt = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    fmt["mech_group"] = num["mech_group"].values
    fmt["var"] = num["var"].values

    return fmt

def main():
    df = prep_df()
    print("[INFO] vars found:", [v for v in ALL_VARS if v in df.columns])

    num = build_table(df)
    fmt = build_formatted_table(num)

    # Original notebook comment normalized for the public code archive.
    num.to_csv(OUT_NUM_CSV, index=False)
    fmt.to_csv(OUT_FMT_CSV, index=False)

    # Excel output note.
    with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
        num.to_excel(writer, sheet_name="numeric", index=False)
        fmt.to_excel(writer, sheet_name="formatted", index=False)

    print("[SAVE]", OUT_NUM_CSV)
    print("[SAVE]", OUT_FMT_CSV)
    print("[SAVE]", OUT_XLSX)

if __name__ == "__main__":
    main()
